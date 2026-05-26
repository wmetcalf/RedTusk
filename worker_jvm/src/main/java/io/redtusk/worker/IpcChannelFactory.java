package io.redtusk.worker;

import java.io.File;
import java.util.logging.Logger;

/**
 * Picks an {@link IpcChannel} implementation based on the {@code REDTUSK_WORKER_IPC}
 * environment variable.
 *
 * <ul>
 *   <li>Unset, empty, or {@code "file"}: {@link FileIpcChannel} — the historical
 *       bind-mount file-based IPC. Default for compatibility with all existing
 *       worker profiles ({@code default}, {@code high-density}, the initial
 *       {@code kata} config).</li>
 *   <li>{@code "vsock"}: reserved for the future microvm profile;
 *       Phase 1 throws a clear error if requested.</li>
 * </ul>
 *
 * <p>This factory exists so {@link Main} can pick the channel once per
 * invocation without scattering env-var lookups across the worker. Callers
 * pass the same scratch dir as before; the file impl uses it directly and
 * the vsock impl will ignore it.
 */
public final class IpcChannelFactory {
    private static final Logger LOG = Logger.getLogger(IpcChannelFactory.class.getName());

    private IpcChannelFactory() {}

    public static IpcChannel forScratchDir(File scratchDir) {
        String requested = System.getenv("REDTUSK_WORKER_IPC");
        String kind = (requested == null || requested.isEmpty()) ? "file" : requested.toLowerCase();
        switch (kind) {
            case "file":
                return new FileIpcChannel(scratchDir);
            case "vsock":
                return buildVsockChannel();
            default:
                LOG.warning("Unknown REDTUSK_WORKER_IPC=" + requested + "; falling back to file");
                return new FileIpcChannel(scratchDir);
        }
    }

    private static IpcChannel buildVsockChannel() {
        String portRaw = System.getenv("REDTUSK_VSOCK_PORT");
        if (portRaw == null || portRaw.isEmpty()) {
            throw new IllegalStateException(
                "REDTUSK_WORKER_IPC=vsock requires REDTUSK_VSOCK_PORT to be set " +
                "(must match the port the dispatcher binds)");
        }
        int port = Integer.parseInt(portRaw.trim());
        int hostCid = VsockIpcChannel.DEFAULT_HOST_CID;
        String cidRaw = System.getenv("REDTUSK_VSOCK_HOST_CID");
        if (cidRaw != null && !cidRaw.isEmpty()) {
            hostCid = Integer.parseInt(cidRaw.trim());
        }
        String unixPath = System.getenv("REDTUSK_VSOCK_UNIX_PATH");
        return new VsockIpcChannel(hostCid, port, unixPath);
    }
}
