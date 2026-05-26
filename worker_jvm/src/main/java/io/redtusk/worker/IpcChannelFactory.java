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
                throw new UnsupportedOperationException(
                    "REDTUSK_WORKER_IPC=vsock is reserved for the microvm profile " +
                    "and not yet implemented (Phase 2). Use 'file' or unset the variable.");
            default:
                LOG.warning("Unknown REDTUSK_WORKER_IPC=" + requested + "; falling back to file");
                return new FileIpcChannel(scratchDir);
        }
    }
}
