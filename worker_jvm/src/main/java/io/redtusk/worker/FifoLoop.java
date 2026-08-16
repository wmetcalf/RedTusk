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
    // WAIT FOREVER by default. A worker that has not been handed a job yet is not
    // "stuck" -- there is nothing for it to be stuck on. It is idle on purpose, which
    // is the entire point of a warm pool, so self-terminating is never the right answer
    // and no finite value is either: any bound is just a cliff the tier falls off once
    // the fleet is quiet for that long, and it fails SILENTLY (the JVM exits rc=2 and the
    // engine falls back to a cold per-job JVM, so the tier only gets slower).
    //
    // Slot lifetime belongs to the HOST, which already owns it: the pool health-checks,
    // evicts and SIGKILLs slots, and run_guest.py states the contract outright -- the
    // guest "blocks until the host SIGKILLs the slot. So slot lifetime is entirely
    // host-reaper-controlled". A guest-side deadline contradicts that and can only
    // disagree with the host about whether a slot is alive.
    //
    // Every caller already has an outer bound, so unbounded here cannot hang anything:
    // the cold path runs the JVM under a subprocess timeout, warmup() kills it if READY
    // never arrives, and pooled slots are reaped by the host.
    //
    // A positive REDTUSK_JOB_SIGNAL_TIMEOUT_MS restores a bound for callers that want one
    // (tests, one-shot runs outside a pool). Unset or <= 0 means wait indefinitely.
    private static final long JOB_SIGNAL_TIMEOUT_MS = timeoutMsFromEnv();

    private static long timeoutMsFromEnv() {
        return parseTimeoutMs(System.getenv("REDTUSK_JOB_SIGNAL_TIMEOUT_MS"));
    }

    /**
     * Package-private so the default can be asserted (System.getenv is not settable in-process).
     *
     * @return positive bound in ms, or 0 meaning "wait indefinitely" — the default, and the
     *     value every unset/blank/garbage/non-positive input must map to. A parse slip that
     *     silently produced a finite bound would reintroduce the self-terminating warm slot.
     */
    static long parseTimeoutMs(String raw) {
        if (raw != null && !raw.isBlank()) {
            try {
                return Math.max(0L, Long.parseLong(raw.trim()));
            } catch (NumberFormatException e) {
                LOG.warning("Bad REDTUSK_JOB_SIGNAL_TIMEOUT_MS=" + raw + "; waiting indefinitely");
            }
        }
        return 0L;
    }

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
     *
     * Waits indefinitely by default — see {@link #JOB_SIGNAL_TIMEOUT_MS}. Returns "go" when
     * the signal file appears; only throws on timeout if a bound was explicitly configured.
     */
    public static String waitForSignal(File scratchDir) throws IOException {
        File goFile = new File(controlDir(scratchDir), GO_FILE);
        final boolean bounded = JOB_SIGNAL_TIMEOUT_MS > 0L;
        LOG.info("Waiting for go-signal at " + goFile.getAbsolutePath()
                + (bounded ? " (bounded: " + JOB_SIGNAL_TIMEOUT_MS + " ms)" : " (indefinitely)"));
        // MONOTONIC, not wall clock, for the bounded case: on a warm tier this JVM is parked
        // in this very loop when the host snapshots it, and each slot resumes that image later.
        // currentTimeMillis() would count the suspended time and fire the instant a slot
        // resumes; nanoTime does not advance across the suspend. Same hazard blastbox handles
        // on the Python side with _RestoreAwareDeadline.
        long deadlineNanos = System.nanoTime() + JOB_SIGNAL_TIMEOUT_MS * 1_000_000L;
        while (!bounded || System.nanoTime() - deadlineNanos < 0) {
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
        // Unreachable unless a bound was explicitly configured; the default loop never exits.
        throw new IOException("Timed out waiting for go-signal after " + JOB_SIGNAL_TIMEOUT_MS
                + " ms (explicit REDTUSK_JOB_SIGNAL_TIMEOUT_MS; the default is to wait "
                + "indefinitely and let the host reap the slot)");
    }
}
