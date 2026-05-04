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
        File readyFile = scratchDir.resolve("control.ready").toFile();
        assertFalse(readyFile.exists());

        ExecutorService exec = Executors.newSingleThreadExecutor();
        Future<Void> task = exec.submit(() -> {
            FifoLoop.createFifo(scratchDir.toFile());
            return null;
        });
        task.get(5, TimeUnit.SECONDS);
        assertTrue(readyFile.exists(), "control.ready must exist after createFifo()");
        exec.shutdownNow();
    }

    @Test
    void waitForSignalReceivesGoLine(@TempDir Path scratchDir) throws Exception {
        FifoLoop.createFifo(scratchDir.toFile());
        File goFile = scratchDir.resolve("control.go").toFile();

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
}
