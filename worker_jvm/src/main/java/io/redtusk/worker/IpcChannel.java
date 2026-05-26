package io.redtusk.worker;

import java.io.Closeable;
import java.io.IOException;

/**
 * Worker ↔ dispatcher IPC abstraction.
 *
 * <p>Worker processes go through this channel for control-plane signaling
 * (ready / go) and to obtain the per-job descriptor that names the input file
 * and output directory. The two current implementations are:
 *
 * <ul>
 *   <li>{@link FileIpcChannel} — file-based on a bind-mounted scratch directory.
 *       Used by every profile that supports virtio-fs / 9p host-share IPC:
 *       {@code default} (gVisor), {@code high-density} (runc + CRaC), and the
 *       initial {@code kata} configuration. This is the historical RedTusk
 *       contract and the only one most deployments need.</li>
 *
 *   <li>{@code VsockIpcChannel} — vsock-based, used by the {@code microvm}
 *       profile that runs the worker inside a Kata microVM with no shared
 *       host filesystem (a prerequisite for Kata's VM templating + Firecracker
 *       snapshots). Not implemented in this Phase 1 refactor; the interface
 *       is shaped to accept it without further changes here.</li>
 * </ul>
 *
 * <p>The {@code microvm} path will also need a way to stream input bytes and
 * receive output bytes (since there's no bind-mount), but that lives outside
 * this signaling interface — likely a separate {@code BlobTransport} or
 * extended {@link JobDescriptor} fields. Phase 1 deliberately keeps that
 * surface OUT of this interface so the FileIpcChannel refactor is a strict
 * no-behavior-change move.
 */
public interface IpcChannel extends Closeable {

    /**
     * Signal to the dispatcher that this worker process is ready to receive
     * a job. For FileIpcChannel this creates {@code control/control.ready};
     * for VsockIpcChannel this will send a READY frame on the vsock socket.
     *
     * <p>May be called more than once on the same instance — specifically,
     * the CRaC restore path calls this once at checkpoint time (captured in
     * the snapshot) and again post-restore (because the dispatcher's
     * bind-mount overlays the build-time ready file). Implementations MUST
     * be idempotent.
     */
    void announceReady() throws IOException;

    /**
     * Block until the dispatcher signals that a job is queued and ready to be
     * picked up. For FileIpcChannel this polls for {@code control/control.go};
     * for VsockIpcChannel this will block on a GO frame from the socket.
     *
     * <p>Returns a short status token ("go") that the historical FifoLoop API
     * surfaces; callers compare or ignore it.
     */
    String awaitGoSignal() throws IOException;

    /**
     * Default no-op close. File-based has no socket to release; vsock will
     * shut down its socket here.
     */
    @Override
    default void close() throws IOException {}
}
