package io.redtusk.worker;

import java.io.Closeable;
import java.io.IOException;

/**
 * Worker ↔ dispatcher IPC abstraction.
 *
 * <p>Worker processes go through this channel for control-plane signaling
 * (ready / go), the per-job JobDescriptor + input bytes, and the resulting
 * metadata + artifacts. Two implementations:
 *
 * <ul>
 *   <li>{@link FileIpcChannel} — file-based on a bind-mounted scratch dir.
 *       Used by every profile that has virtio-fs / 9p host-share IPC:
 *       {@code default} (gVisor), {@code high-density} (runc + CRaC), and
 *       the initial {@code kata} configuration. Existing RedTusk contract.</li>
 *
 *   <li>{@link VsockIpcChannel} — AF_VSOCK stream, used by the {@code microvm}
 *       profile that runs the worker inside a Kata microVM with no shared
 *       host filesystem (prerequisite for Kata VM templating + Firecracker
 *       snapshots).</li>
 * </ul>
 *
 * <h2>Wire protocol (vsock)</h2>
 *
 * <p>Line-based, length-prefixed for binary blobs. All non-blob frames are
 * one line of ASCII text. The sequence for one job:
 *
 * <pre>
 *   worker → host:  "READY\n"                        (announceReady)
 *   host   → worker: "GO\n"                          (awaitGoSignal returns "go")
 *   host   → worker: "JOB &lt;N&gt;\n" + N bytes of UTF-8 JobDescriptor JSON
 *   host   → worker: "INPUT &lt;M&gt;\n" + M bytes of input file
 *   worker (processes the job locally)
 *   worker → host:  "RESULT &lt;K&gt;\n" + K bytes of metadata.json
 *   (zero or more)  "ARTIFACT &lt;path&gt; &lt;L&gt;\n" + L bytes of artifact data
 *   worker → host:  "DONE\n"
 * </pre>
 *
 * <p>FileIpcChannel implements the same logical operations against the
 * scratch directory and the {@link JobDescriptor#inputPath()} /
 * {@link JobDescriptor#outputDir()} fields the descriptor carries. This way
 * Main.java doesn't have to branch on transport — it just calls the
 * abstract operations and the channel does the right thing.
 */
public interface IpcChannel extends Closeable {

    /**
     * Signal to the dispatcher that this worker process is ready to receive
     * a job. Implementations MUST be idempotent — the CRaC restore path
     * calls this once at checkpoint time (captured in the snapshot) and
     * again post-restore.
     */
    void announceReady() throws IOException;

    /**
     * Block until the dispatcher signals that a job is queued and ready
     * to be picked up. Returns a short status token ("go") for parity
     * with the historical FifoLoop return value.
     */
    String awaitGoSignal() throws IOException;

    /**
     * Receive the job descriptor for the job to process.
     *
     * <p>For FileIpcChannel this reads {@code <scratchDir>/control/job.json}.
     * For VsockIpcChannel this reads a "JOB &lt;N&gt;\n" framed JSON blob
     * over the open socket AND ALSO writes the input bytes to a local
     * temporary file (returned via the descriptor's {@code inputPath}).
     *
     * <p>The returned descriptor's {@code inputPath} and {@code outputDir}
     * are valid filesystem paths the worker should read input from and
     * write output to, regardless of underlying transport. For vsock,
     * the channel has already written the input bytes locally.
     *
     * @return parsed JobDescriptor with valid local paths
     */
    JobDescriptor receiveJob() throws IOException;

    /**
     * Send the parser's primary output (metadata.json bytes) back to the
     * dispatcher.
     *
     * <p>For FileIpcChannel this is a no-op — the worker has already
     * written the file to {@link JobDescriptor#outputDir()} on a
     * bind-mounted /out, which the dispatcher reads directly from the
     * host filesystem.
     *
     * <p>For VsockIpcChannel this sends a "RESULT &lt;K&gt;\n" frame
     * followed by K bytes of payload over the socket.
     */
    void sendResult(byte[] metadataJson) throws IOException;

    /**
     * Send one artifact (thumbnail, embedded file, per-entry text, etc.)
     * back to the dispatcher. Path is relative to the worker's output
     * directory.
     *
     * <p>FileIpcChannel: no-op (already on disk).
     * VsockIpcChannel: "ARTIFACT &lt;relPath&gt; &lt;L&gt;\n" + L bytes.
     */
    void sendArtifact(String relPath, byte[] payload) throws IOException;

    /**
     * Signal that the worker is done with this job. After this call the
     * channel may be closed.
     *
     * <p>FileIpcChannel: no-op. VsockIpcChannel: sends "DONE\n".
     */
    void signalDone() throws IOException;

    /**
     * Close any underlying resources (sockets). File-based has nothing
     * to release; vsock will close its socket.
     */
    @Override
    default void close() throws IOException {}

    /**
     * Whether {@link #sendResult(byte[])} and {@link #sendArtifact} actually
     * ship bytes over the channel. When false, the worker has already placed
     * output where the dispatcher will read it (a bind-mounted /out, or a
     * virtio-blk disk in FC's disk-output mode), and {@link Main} can skip
     * the {@code Files.readAllBytes} that would otherwise be discarded by a
     * no-op send. Defaults to true so legacy/streaming channels keep working
     * unchanged.
     */
    default boolean outputsOverIpc() { return true; }
}
