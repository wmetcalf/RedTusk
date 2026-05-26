package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.nio.file.Path;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

class IpcChannelTest {

    @Test
    void fileChannelAnnounceReadyCreatesControlReady(@TempDir Path scratchDir) throws Exception {
        IpcChannel ipc = new FileIpcChannel(scratchDir.toFile());
        ipc.announceReady();
        assertTrue(scratchDir.resolve("control/control.ready").toFile().exists(),
            "FileIpcChannel.announceReady must create control/control.ready");
    }

    @Test
    void fileChannelAnnounceReadyIsIdempotent(@TempDir Path scratchDir) throws Exception {
        IpcChannel ipc = new FileIpcChannel(scratchDir.toFile());
        ipc.announceReady();
        // Second call must not throw — CRaC pre-checkpoint + post-restore path
        // calls announceReady twice on the same channel.
        ipc.announceReady();
        assertTrue(scratchDir.resolve("control/control.ready").toFile().exists());
    }

    @Test
    void fileChannelAwaitGoSignalReceivesGo(@TempDir Path scratchDir) throws Exception {
        IpcChannel ipc = new FileIpcChannel(scratchDir.toFile());
        ipc.announceReady();
        File goFile = scratchDir.resolve("control/control.go").toFile();

        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try {
                Thread.sleep(50);
                goFile.createNewFile();
            } catch (Exception ignored) {}
            return null;
        });

        String line = ipc.awaitGoSignal();
        assertEquals("go", line.trim());
        exec.shutdownNow();
    }

    @Test
    void factoryDefaultsToFileChannel(@TempDir Path scratchDir) {
        // When REDTUSK_WORKER_IPC is unset, the factory must return FileIpcChannel.
        // We can't easily un-set env vars in a JVM test, so this assumes the test
        // process has no REDTUSK_WORKER_IPC set (which is true under maven test).
        IpcChannel ipc = IpcChannelFactory.forScratchDir(scratchDir.toFile());
        assertInstanceOf(FileIpcChannel.class, ipc,
            "default factory output must be FileIpcChannel");
    }
}
