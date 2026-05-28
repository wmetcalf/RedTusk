package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.crac.Context;
import org.crac.Core;
import org.crac.Resource;
import org.newsclub.net.unix.AFSocket;
import org.newsclub.net.unix.AFSocketCapability;
import org.newsclub.net.unix.AFUNIXSocketAddress;
import org.newsclub.net.unix.AFVSOCKSocketAddress;
import org.newsclub.net.unix.vsock.AFVSOCKSocket;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.logging.Logger;

/**
 * AF_VSOCK-based IPC for the {@code microvm} worker profile.
 *
 * <p>The worker (inside a Kata microVM, or any guest with /dev/vsock) opens a
 * stream socket to the host CID + port configured via env vars and exchanges
 * a tiny line-based protocol with the dispatcher:
 *
 * <pre>
 *   worker → host:  READY\n            (after announceReady)
 *   host   → worker: GO\n               (returned by awaitGoSignal)
 *   ... later phases will extend with JOB, RESULT, ERROR messages ...
 * </pre>
 *
 * <p>Configuration:
 * <ul>
 *   <li>{@code REDTUSK_VSOCK_HOST_CID} — the CID to connect to. Defaults to 2
 *       (VMADDR_CID_HOST). In Kata's hybrid-vsock mode this is the host-side
 *       Unix socket that the kata-shim relays to AF_VSOCK in the guest.</li>
 *   <li>{@code REDTUSK_VSOCK_PORT} — the port to connect to. Must match what
 *       the dispatcher binds. No default — set explicitly so the dispatcher
 *       and worker agree.</li>
 *   <li>{@code REDTUSK_VSOCK_UNIX_PATH} — test-only override. When set,
 *       VsockIpcChannel uses AF_UNIX on this socket path instead of AF_VSOCK.
 *       Used by tests on hosts without /dev/vsock; identical protocol.</li>
 * </ul>
 *
 * <p>Connect attempts retry with exponential backoff up to {@code CONNECT_TIMEOUT_MS}
 * because the dispatcher may not have its vsock listener bound when the
 * worker spawns. Once connected, the socket stays open until {@link #close()}.
 */
public final class VsockIpcChannel implements IpcChannel, Resource {
    private static final Logger LOG = Logger.getLogger(VsockIpcChannel.class.getName());

    static final int DEFAULT_HOST_CID = 2;
    static final long CONNECT_TIMEOUT_MS = 30_000L;
    static final long INITIAL_RETRY_MS = 50L;
    static final long MAX_RETRY_MS = 2_000L;
    static final long GO_TIMEOUT_MS = 600_000L;

    private static final ObjectMapper OM = new ObjectMapper();
    /** Where the worker stages input bytes received over vsock. The microvm
     *  guest's rootfs has /tmp as a writable tmpfs (see Dockerfile.microvm).
     *  Each job gets a fresh subdirectory; cleanup is implicit on container exit. */
    static final String WORKER_INPUT_DIR = "/tmp/redtusk-in";
    /** Where the worker writes its output before streaming it back over vsock. */
    static final String WORKER_OUTPUT_DIR = "/tmp/redtusk-out";

    private int hostCid;
    private int port;
    // NOT final: re-read from env on afterRestore so a checkpoint taken with
    // REDTUSK_VSOCK_UNIX_PATH=/build/sock can be restored in an environment
    // where the env var is unset (→ fall back to AF_VSOCK at hostCid/port).
    private String unixPathOverride;
    private Socket socket;
    /** Use a binary input stream — we need to read framed binary payloads
     *  (JobDescriptor JSON, then arbitrary input bytes) intermixed with
     *  ASCII control lines. BufferedReader would consume too aggressively. */
    private DataInputStream din;
    private OutputStream writer;

    /** Constructed via {@link IpcChannelFactory}; package-private for tests. */
    VsockIpcChannel(int hostCid, int port, String unixPathOverride) {
        this.hostCid = hostCid;
        this.port = port;
        this.unixPathOverride = unixPathOverride;
        registerForCheckpointRestore();
    }

    /**
     * Register this channel for CRaC checkpoint/restore.
     *
     * <p>We register with BOTH the org.crac shim AND (reflectively) with
     * jdk.crac if available. The shim's register() on some CRaC builds does
     * not forward to jdk.crac, so registering only with the shim leaves
     * beforeCheckpoint un-called and the open vsock fd trips warp's
     * CheckpointOpenSocketException check. Registering with jdk.crac directly
     * is reflection-based so we don't take a hard compile dep on it (the
     * codebase still has to compile on non-CRaC JDKs in tests).
     */
    private void registerForCheckpointRestore() {
        try {
            Core.getGlobalContext().register(this);
        } catch (Throwable t) {
            LOG.fine("org.crac register failed: " + t);
        }
        try {
            Class<?> jdkCore = Class.forName("jdk.crac.Core");
            Object ctx = jdkCore.getMethod("getGlobalContext").invoke(null);
            // Build a jdk.crac.Resource proxy that forwards to our org.crac.Resource methods.
            Class<?> jdkResourceCls = Class.forName("jdk.crac.Resource");
            Object proxy = java.lang.reflect.Proxy.newProxyInstance(
                jdkResourceCls.getClassLoader(),
                new Class<?>[]{ jdkResourceCls },
                (p, method, args) -> {
                    String name = method.getName();
                    if ("beforeCheckpoint".equals(name)) {
                        this.beforeCheckpoint(null);
                        return null;
                    }
                    if ("afterRestore".equals(name)) {
                        this.afterRestore(null);
                        return null;
                    }
                    // Object methods (toString/hashCode/equals)
                    return method.invoke(this, args);
                }
            );
            ctx.getClass().getMethod("register", jdkResourceCls).invoke(ctx, proxy);
            LOG.info("VsockIpcChannel: registered with jdk.crac.Core");
        } catch (ClassNotFoundException e) {
            LOG.fine("jdk.crac not available (non-CRaC JDK)");
        } catch (Throwable t) {
            LOG.warning("Failed to register with jdk.crac directly: " + t);
        }
    }

    // ── CRaC Resource hooks ─────────────────────────────────────────────────
    //
    // Lifecycle around a checkpoint+restore cycle:
    //   1. announceReady() opens the socket, sends READY, leaves it connected.
    //   2. Caller invokes Core.checkpointRestore().
    //   3. → beforeCheckpoint(): we close the socket. The JVM dumps process
    //      state with no live fd, so the snapshot is portable across restores.
    //   4. JVM resumes (possibly hours later, on a different host).
    //   5. → afterRestore(): we reopen the socket and resend READY so the
    //      dispatcher knows this slot is ready. The next call to
    //      awaitGoSignal/receiveJob reads from the new this.din/socket fields.
    //
    // The Resource contract requires that we are NOT blocked in a read at
    // checkpoint time. Main.runCheckpoint puts Core.checkpointRestore()
    // strictly between announceReady() and processJob(), so we are guaranteed
    // to be idle (not inside socket.read()) when this fires.

    @Override
    public void beforeCheckpoint(Context<? extends Resource> context) throws IOException {
        if (socket != null && !socket.isClosed()) {
            LOG.info("VsockIpcChannel.beforeCheckpoint: closing socket to " + describePeer());
            try { socket.close(); } catch (IOException ignored) {}
        }
        socket = null;
        din = null;
        writer = null;
    }

    @Override
    public void afterRestore(Context<? extends Resource> context) throws IOException {
        // CRaC restores all fields verbatim from the checkpoint snapshot,
        // including unixPathOverride which we may have set at BUILD time
        // (REDTUSK_VSOCK_UNIX_PATH pointing at a build listener) but which
        // is irrelevant in the restore environment (e.g. inside an FC
        // microVM, we want AF_VSOCK to host CID 2 instead). Re-read the env
        // here so the post-restore peer is decided fresh.
        // CRITICAL: System.getenv() returns env cached at JVM-start —
        // unchanged across CRaC restore. We read /proc/self/environ directly
        // so the restored worker sees the FC init's actual environment.
        String envUnix = getEnvFromProc("REDTUSK_VSOCK_UNIX_PATH");
        this.unixPathOverride = (envUnix != null && !envUnix.isEmpty()) ? envUnix : null;
        String portRaw = getEnvFromProc("REDTUSK_VSOCK_PORT");
        if (portRaw != null && !portRaw.isEmpty()) {
            try { this.port = Integer.parseInt(portRaw.trim()); } catch (NumberFormatException ignore) {}
        }
        String cidRaw = getEnvFromProc("REDTUSK_VSOCK_HOST_CID");
        if (cidRaw != null && !cidRaw.isEmpty()) {
            try { this.hostCid = Integer.parseInt(cidRaw.trim()); } catch (NumberFormatException ignore) {}
        }
        LOG.info("VsockIpcChannel.afterRestore: reconnecting to " + describePeer());
        announceReady();
    }

    /** Read a single env var from /proc/self/environ (current process's
     *  actual environment, NOT the cached System.getenv() snapshot). */
    private static String getEnvFromProc(String name) {
        try {
            byte[] data = java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/proc/self/environ"));
            String prefix = name + "=";
            int start = 0;
            for (int i = 0; i <= data.length; i++) {
                if (i == data.length || data[i] == 0) {
                    if (i > start) {
                        String entry = new String(data, start, i - start, StandardCharsets.UTF_8);
                        if (entry.startsWith(prefix)) {
                            return entry.substring(prefix.length());
                        }
                    }
                    start = i + 1;
                }
            }
        } catch (IOException ignore) {}
        return null;
    }

    /** Connect to the host (with retry) and send the READY line. */
    @Override
    public void announceReady() throws IOException {
        if (socket == null) {
            socket = connectWithRetry();
            din = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
            writer = socket.getOutputStream();
        }
        // Idempotent: if announceReady is called twice (CRaC restore pattern),
        // we re-send READY on the existing socket. The dispatcher should
        // tolerate duplicate READY frames.
        writer.write("READY\n".getBytes(StandardCharsets.UTF_8));
        writer.flush();
        LOG.info("VsockIpcChannel: sent READY to " + describePeer());
    }

    /** Block reading until the dispatcher sends GO (or any equivalent token). */
    @Override
    public String awaitGoSignal() throws IOException {
        if (din == null) {
            throw new IOException("awaitGoSignal called before announceReady");
        }
        long deadline = System.currentTimeMillis() + GO_TIMEOUT_MS;
        socket.setSoTimeout((int) Math.min(GO_TIMEOUT_MS, Integer.MAX_VALUE));
        while (System.currentTimeMillis() <= deadline) {
            String line = readLine();
            if (line == null) {
                break;
            }
            String trimmed = line.trim();
            if (trimmed.equalsIgnoreCase("GO")) {
                LOG.info("VsockIpcChannel: received GO from " + describePeer());
                return "go";
            }
            // Tolerate unrecognized lines (e.g. future protocol additions);
            // keep reading until GO or EOF.
            LOG.warning("VsockIpcChannel: ignoring unexpected line: " + trimmed);
        }
        throw new IOException("VsockIpcChannel: connection closed before GO arrived");
    }

    @Override
    public JobDescriptor receiveJob() throws IOException {
        if (din == null) {
            throw new IOException("receiveJob called before announceReady");
        }
        // Expect: "JOB <N>\n" + N bytes JSON, then "INPUT <M>\n" + M bytes
        String jobHdr = expectFrameHeader("JOB");
        int jsonLen = parseLength(jobHdr);
        byte[] jsonBytes = readFully(jsonLen);

        // Parse with the input path REWRITTEN to a local tmpfs location.
        // The serialized inputPath might be a host-side path that doesn't
        // resolve inside the microVM, so we override before returning the
        // descriptor to Main.java.
        JobDescriptor incoming = OM.readValue(jsonBytes, JobDescriptor.class);

        // Read input bytes
        String inputHdr = expectFrameHeader("INPUT");
        int inputLen = parseLength(inputHdr);
        Path inDir = Path.of(WORKER_INPUT_DIR);
        Files.createDirectories(inDir);
        String filename = incoming.filenameHint() != null ? incoming.filenameHint() : "input";
        // Strip any path components from filenameHint to keep us in inDir.
        filename = new File(filename).getName();
        Path localInput = inDir.resolve(filename);
        try (FileOutputStream out = new FileOutputStream(localInput.toFile())) {
            copyStreamN(din, out, inputLen);
        }
        // Same for output dir.
        Path outDir = Path.of(WORKER_OUTPUT_DIR);
        Files.createDirectories(outDir);

        // Reconstruct the descriptor with rewritten paths. JobDescriptor is
        // a record-like immutable bean; we use the existing copy semantics.
        return incoming.withPaths(localInput.toString(), outDir.toString());
    }

    @Override
    public void sendResult(byte[] metadataJson) throws IOException {
        // No-op. Output (metadata.json + artifacts) is written to
        // WORKER_OUTPUT_DIR (/tmp/redtusk-out), which is a virtio-blk ext4
        // disk the host reads back after the VM powers off. Streaming large
        // payloads over vsock corrupts them under concurrent host load
        // (guest virtio-vsock race), so output bypasses vsock entirely; only
        // the control handshake + job descriptor + input + DONE use vsock.
        LOG.fine("VsockIpcChannel.sendResult: no-op (output on virtio-blk disk)");
    }

    @Override
    public void sendArtifact(String relPath, byte[] payload) throws IOException {
        // No-op — see sendResult. The artifact is already on the output disk.
    }

    @Override
    public void signalDone() throws IOException {
        if (writer == null) return;
        writer.write("DONE\n".getBytes(StandardCharsets.UTF_8));
        writer.flush();
        LOG.info("VsockIpcChannel: sent DONE");
    }

    // ── private framing helpers ──────────────────────────────────────────────

    private void sendBlobFrame(String tag, String path, byte[] payload) throws IOException {
        if (writer == null) {
            throw new IOException("send before announceReady");
        }
        StringBuilder hdr = new StringBuilder(tag);
        if (path != null) {
            hdr.append(' ').append(path);
        }
        hdr.append(' ').append(payload.length).append('\n');
        writer.write(hdr.toString().getBytes(StandardCharsets.UTF_8));
        writer.write(payload);
        writer.flush();
    }

    /** Read a single text line terminated by \n. Returns null on EOF.
     *  We do this manually instead of BufferedReader.readLine() because the
     *  underlying stream also carries framed binary payloads — line-buffered
     *  reads would consume past the \n. */
    private String readLine() throws IOException {
        StringBuilder sb = new StringBuilder();
        int b;
        while ((b = din.read()) != -1) {
            if (b == '\n') return sb.toString();
            if (b == '\r') continue;
            sb.append((char) b);
        }
        return sb.length() == 0 ? null : sb.toString();
    }

    private String expectFrameHeader(String expectedTag) throws IOException {
        String line = readLine();
        if (line == null) {
            throw new IOException("EOF while expecting " + expectedTag + " frame");
        }
        if (!line.startsWith(expectedTag + " ")) {
            throw new IOException("Expected " + expectedTag + " header, got: " + line);
        }
        return line;
    }

    private int parseLength(String header) throws IOException {
        // Header format: "TAG <length>" or "TAG <path> <length>" — we always
        // want the LAST space-separated token as the length.
        int sp = header.lastIndexOf(' ');
        if (sp < 0) throw new IOException("Malformed frame header: " + header);
        try {
            int n = Integer.parseInt(header.substring(sp + 1));
            if (n < 0) throw new IOException("Negative length in: " + header);
            return n;
        } catch (NumberFormatException e) {
            throw new IOException("Bad length in: " + header, e);
        }
    }

    private byte[] readFully(int len) throws IOException {
        byte[] buf = new byte[len];
        int read = 0;
        while (read < len) {
            int n = din.read(buf, read, len - read);
            if (n < 0) throw new IOException("EOF mid-payload at " + read + "/" + len);
            read += n;
        }
        return buf;
    }

    private void copyStreamN(java.io.InputStream in, OutputStream out, int n) throws IOException {
        byte[] buf = new byte[64 * 1024];
        int remaining = n;
        while (remaining > 0) {
            int got = in.read(buf, 0, Math.min(buf.length, remaining));
            if (got < 0) throw new IOException("EOF mid-stream at " + (n - remaining) + "/" + n);
            out.write(buf, 0, got);
            remaining -= got;
        }
    }

    @Override
    public void close() throws IOException {
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
    }

    private Socket connectWithRetry() throws IOException {
        long deadline = System.currentTimeMillis() + CONNECT_TIMEOUT_MS;
        long delay = INITIAL_RETRY_MS;
        IOException last = null;
        while (System.currentTimeMillis() < deadline) {
            try {
                return openSocket();
            } catch (IOException e) {
                last = e;
                try {
                    Thread.sleep(delay);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new IOException("interrupted while connecting to " + describePeer(), ie);
                }
                delay = Math.min(delay * 2, MAX_RETRY_MS);
            }
        }
        throw new IOException("VsockIpcChannel: failed to connect to " + describePeer()
            + " within " + CONNECT_TIMEOUT_MS + " ms", last);
    }

    private Socket openSocket() throws IOException {
        if (unixPathOverride != null && !unixPathOverride.isEmpty()) {
            // Test/portability mode: AF_UNIX socket at the given path. Same
            // line-based protocol; lets unit tests run on hosts without
            // /dev/vsock.
            AFUNIXSocketAddress addr = AFUNIXSocketAddress.of(new java.io.File(unixPathOverride));
            return org.newsclub.net.unix.AFUNIXSocket.connectTo(addr);
        }
        // NOTE: skip AFSocket.supports(CAPABILITY_VSOCK). The check caches
        // its result on first call; if first call is during CRaC checkpoint
        // build (where /dev/vsock doesn't exist), the cached "false" persists
        // into the restored process even when /dev/vsock IS available in the
        // FC microVM. We let the actual socket() / connect() syscall surface
        // the real error if vsock truly isn't there.
        AFVSOCKSocketAddress addr = AFVSOCKSocketAddress.ofPortAndCID(port, hostCid);
        AFVSOCKSocket s = AFVSOCKSocket.newInstance();
        s.connect(addr);
        return s;
    }

    private String describePeer() {
        if (unixPathOverride != null && !unixPathOverride.isEmpty()) {
            return "unix:" + unixPathOverride;
        }
        return "vsock:cid=" + hostCid + ",port=" + port;
    }
}
