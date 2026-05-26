package io.redtusk.worker;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;

/**
 * File-based IPC over a bind-mounted scratch directory.
 *
 * <p>Wraps the historical {@link FifoLoop} static API in the {@link IpcChannel}
 * interface so callers don't have to choose between channel implementations at
 * call sites. Behavior is byte-identical to the pre-refactor direct calls:
 *
 * <ul>
 *   <li>{@link #announceReady()} → {@code FifoLoop.createFifo(scratchDir)}</li>
 *   <li>{@link #awaitGoSignal()} → {@code FifoLoop.waitForSignal(scratchDir)}</li>
 *   <li>{@link #receiveJob()} → reads {@code <scratchDir>/control/job.json}
 *       and returns the parsed descriptor unchanged (inputPath/outputDir
 *       still point at the bind-mounted /in and /out)</li>
 *   <li>{@link #sendResult(byte[])} / {@link #sendArtifact} / {@link #signalDone()}
 *       — no-ops, since outputs have already been written to the
 *       bind-mounted /out directory and the dispatcher reads them
 *       directly from the host filesystem</li>
 * </ul>
 *
 * <p>Used by every worker profile with virtio-fs / 9p shared mounts:
 * {@code default}, {@code high-density}, and the current {@code kata} setup.
 */
public final class FileIpcChannel implements IpcChannel {
    private static final ObjectMapper OM = new ObjectMapper();

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

    @Override
    public JobDescriptor receiveJob() throws IOException {
        File jobFile = new File(new File(scratchDir, FifoLoop.CONTROL_DIR), "job.json");
        if (!jobFile.exists()) {
            throw new IOException("job.json not found at: " + jobFile);
        }
        return OM.readValue(jobFile, JobDescriptor.class);
    }

    /** Output is on the bind-mounted /out — no transport step needed. The
     *  dispatcher reads it directly from the host filesystem. */
    @Override
    public void sendResult(byte[] metadataJson) {
        // intentionally empty
    }

    @Override
    public void sendArtifact(String relPath, byte[] payload) {
        // intentionally empty — artifacts already on disk in outputDir
    }

    @Override
    public void signalDone() {
        // intentionally empty — process exit signals completion in the
        // file-IPC contract.
    }
}
