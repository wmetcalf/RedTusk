package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;
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
public final class VsockIpcChannel implements IpcChannel {
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

    private final int hostCid;
    private final int port;
    private final String unixPathOverride;
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
        sendBlobFrame("RESULT", null, metadataJson);
    }

    @Override
    public void sendArtifact(String relPath, byte[] payload) throws IOException {
        sendBlobFrame("ARTIFACT", relPath, payload);
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
        if (!AFSocket.supports(AFSocketCapability.CAPABILITY_VSOCK)) {
            throw new IOException("AF_VSOCK is not supported on this host "
                + "(no /dev/vsock kernel module loaded?)");
        }
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
