package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.*;
import java.nio.file.Path;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

class FifoLoopTest {

    @Test
    void fifoCreatedAtExpectedPath(@TempDir Path scratchDir) throws Exception {
        File readyFile = scratchDir.resolve("control/control.ready").toFile();
        assertFalse(readyFile.exists());

        ExecutorService exec = Executors.newSingleThreadExecutor();
        Future<Void> task = exec.submit(() -> {
            FifoLoop.createFifo(scratchDir.toFile());
            return null;
        });
        task.get(5, TimeUnit.SECONDS);
        assertTrue(readyFile.exists(), "control/control.ready must exist after createFifo()");
        exec.shutdownNow();
    }

    @Test
    void waitForSignalReceivesGoLine(@TempDir Path scratchDir) throws Exception {
        FifoLoop.createFifo(scratchDir.toFile());
        File goFile = scratchDir.resolve("control/control.go").toFile();

        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try {
                Thread.sleep(50);
                goFile.createNewFile();
            } catch (Exception ignored) {}
            return null;
        });

        String line = FifoLoop.waitForSignal(scratchDir.toFile());
        assertEquals("go", line.trim());
        exec.shutdownNow();
    }

    @Test
    void ksmHelperDoesNotThrow() {
        assertDoesNotThrow(KsmHelper::markHeapMergeable);
    }

    @Test
    void capDropperFailsClosedWhenNativeLibraryIsUnavailable() {
        IllegalStateException ex = assertThrows(
            IllegalStateException.class,
            CapDropper::dropCheckpointRestoreCapability
        );
        assertTrue(ex.getMessage().contains("capability dropper native library unavailable"));
    }

    /**
     * A warm slot that has not been handed a job is idle ON PURPOSE -- that is the whole
     * point of a warm pool -- so it must never self-terminate. Slot lifetime belongs to the
     * host reaper. Any finite default is just a cliff the tier falls off once the fleet is
     * quiet that long, and it fails silently (JVM exits rc=2, engine reverts to a cold
     * per-job JVM). 0 means wait indefinitely.
     */
    @Test
    void goSignalWaitIsUnboundedUnlessExplicitlyConfigured() {
        assertEquals(0L, FifoLoop.parseTimeoutMs(null), "unset must wait indefinitely");
        assertEquals(0L, FifoLoop.parseTimeoutMs(""), "blank must wait indefinitely");
        assertEquals(0L, FifoLoop.parseTimeoutMs("   "), "whitespace must wait indefinitely");
        assertEquals(0L, FifoLoop.parseTimeoutMs("banana"), "garbage must wait indefinitely");
        assertEquals(0L, FifoLoop.parseTimeoutMs("-1"), "negative must wait indefinitely");
        assertEquals(0L, FifoLoop.parseTimeoutMs("0"), "zero must wait indefinitely");
    }

    @Test
    void explicitPositiveTimeoutIsHonoured() {
        assertEquals(5000L, FifoLoop.parseTimeoutMs("5000"));
        assertEquals(5000L, FifoLoop.parseTimeoutMs("  5000  "));
    }

    @Test
    void hugeTimeoutIsClampedInsteadOfOverflowingIntoThePast() {
        // System.nanoTime() + ms * 1_000_000L wraps negative past ~9.2e12 ms, putting the
        // deadline BEHIND now -- so a value an operator writes to mean "effectively forever"
        // would fire instantly and self-terminate the slot, which is the failure this class was
        // changed to remove. Clamp instead of honouring it literally.
        assertEquals(FifoLoop.MAX_TIMEOUT_MS, FifoLoop.parseTimeoutMs("99999999999999"));
        assertEquals(FifoLoop.MAX_TIMEOUT_MS, FifoLoop.parseTimeoutMs(Long.toString(Long.MAX_VALUE)));

        // ...and the clamped value must actually produce a FUTURE deadline.
        long deadline = System.nanoTime() + FifoLoop.parseTimeoutMs("99999999999999") * 1_000_000L;
        assertTrue(System.nanoTime() - deadline < 0,
                "clamped deadline must still be in the future");
    }

    @Test
    void ordinaryValuesAreUnaffectedByTheClamp() {
        assertEquals(0L, FifoLoop.parseTimeoutMs(null));
        assertEquals(0L, FifoLoop.parseTimeoutMs(""));
        assertEquals(0L, FifoLoop.parseTimeoutMs("nonsense"));
        assertEquals(120_000L, FifoLoop.parseTimeoutMs("120000"));
    }
}
