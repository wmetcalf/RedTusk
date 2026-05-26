package io.redtusk.worker;

import org.newsclub.net.unix.AFSocket;
import org.newsclub.net.unix.AFSocketCapability;
import org.newsclub.net.unix.AFUNIXSocketAddress;
import org.newsclub.net.unix.AFVSOCKSocketAddress;
import org.newsclub.net.unix.vsock.AFVSOCKSocket;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
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

    private final int hostCid;
    private final int port;
    private final String unixPathOverride;
    private Socket socket;
    private BufferedReader reader;
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
            reader = new BufferedReader(
                new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
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
        if (reader == null) {
            throw new IOException("awaitGoSignal called before announceReady");
        }
        long deadline = System.currentTimeMillis() + GO_TIMEOUT_MS;
        socket.setSoTimeout((int) Math.min(GO_TIMEOUT_MS, Integer.MAX_VALUE));
        String line;
        while ((line = reader.readLine()) != null) {
            String trimmed = line.trim();
            if (trimmed.equalsIgnoreCase("GO")) {
                LOG.info("VsockIpcChannel: received GO from " + describePeer());
                return "go";
            }
            // Tolerate unrecognized lines (e.g. future protocol additions);
            // keep reading until GO or EOF.
            LOG.warning("VsockIpcChannel: ignoring unexpected line: " + trimmed);
            if (System.currentTimeMillis() > deadline) {
                break;
            }
        }
        throw new IOException("VsockIpcChannel: connection closed before GO arrived");
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
