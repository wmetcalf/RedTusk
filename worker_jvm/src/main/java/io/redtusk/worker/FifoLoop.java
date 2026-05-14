package io.redtusk.worker;

import java.io.*;
import java.util.logging.Logger;

/**
 * File-based dispatcher/worker handshake — compatible with gVisor (runsc) whose
 * 9p filesystem layer (disable_fifo_open) cannot propagate named pipes to the host.
 *
 * Protocol:
 *   1. Worker creates control/control.ready  → dispatcher sees it, transitions slot to IDLE.
 *   2. Dispatcher writes control/job.json, then creates control/control.go  → worker sees it, starts job.
 *
 * All signal files live in the control/ subdirectory of the scratch dir.
 * Polling at 100 ms intervals; up to JOB_SIGNAL_TIMEOUT_MS before giving up.
 */
public final class FifoLoop {

    private static final Logger LOG = Logger.getLogger(FifoLoop.class.getName());

    static final String CONTROL_DIR = "control";
    static final String READY_FILE  = "control.ready";
    static final String GO_FILE     = "control.go";

    private static final long POLL_INTERVAL_MS      = 100L;
    private static final long JOB_SIGNAL_TIMEOUT_MS = 120_000L; // 2 min max wait

    private FifoLoop() {}

    private static File controlDir(File scratchDir) {
        File dir = new File(scratchDir, CONTROL_DIR);
        dir.mkdirs();
        return dir;
    }

    /**
     * Signal readiness to the dispatcher by creating control/control.ready.
     * Replaces the old mkfifo call; works on any filesystem including gVisor 9p.
     */
    public static void createFifo(File scratchDir) throws IOException {
        File ready = new File(controlDir(scratchDir), READY_FILE);
        if (!ready.createNewFile() && !ready.exists()) {
            throw new IOException("Failed to create " + ready.getAbsolutePath());
        }
        LOG.info("Readiness signal written: " + ready.getAbsolutePath());
    }

    /**
     * Block until the dispatcher creates control/control.go (polling at 100 ms intervals).
     * Returns "go" when the signal file appears, or throws IOException on timeout.
     */
    public static String waitForSignal(File scratchDir) throws IOException {
        File goFile = new File(controlDir(scratchDir), GO_FILE);
        LOG.info("Waiting for go-signal at " + goFile.getAbsolutePath());
        long deadline = System.currentTimeMillis() + JOB_SIGNAL_TIMEOUT_MS;
        while (System.currentTimeMillis() < deadline) {
            if (goFile.exists()) {
                LOG.info("Go-signal received");
                return "go";
            }
            try {
                Thread.sleep(POLL_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IOException("Interrupted while waiting for go-signal", e);
            }
        }
        throw new IOException("Timed out waiting for go-signal after " + JOB_SIGNAL_TIMEOUT_MS + " ms");
    }
}
