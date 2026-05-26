package io.redtusk.worker;

import java.io.File;
import java.io.IOException;

/**
 * File-based IPC over a bind-mounted scratch directory.
 *
 * <p>Wraps the historical {@link FifoLoop} static API in the {@link IpcChannel}
 * interface so callers don't have to choose between channel implementations at
 * call sites. Behavior is byte-identical to calling {@link FifoLoop} directly:
 *
 * <ul>
 *   <li>{@link #announceReady()} creates {@code <scratch>/control/control.ready}</li>
 *   <li>{@link #awaitGoSignal()} polls for {@code <scratch>/control/control.go}
 *       at 100 ms intervals, returns "go" on success, throws on the 10-minute
 *       FifoLoop timeout.</li>
 * </ul>
 *
 * <p>Used by every worker profile that supports virtio-fs / 9p shared mounts:
 * {@code default}, {@code high-density}, and the current {@code kata} setup.
 */
public final class FileIpcChannel implements IpcChannel {
    private final File scratchDir;

    public FileIpcChannel(File scratchDir) {
        this.scratchDir = scratchDir;
    }

    /** Idempotent — repeated calls re-touch the ready file. Safe for the
     *  CRaC pre-checkpoint + post-restore double-announce pattern. */
    @Override
    public void announceReady() throws IOException {
        scratchDir.mkdirs();
        FifoLoop.createFifo(scratchDir);
    }

    @Override
    public String awaitGoSignal() throws IOException {
        return FifoLoop.waitForSignal(scratchDir);
    }
}
