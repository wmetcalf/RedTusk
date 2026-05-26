package io.redtusk.worker;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.newsclub.net.unix.AFUNIXServerSocket;
import org.newsclub.net.unix.AFUNIXSocketAddress;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests the VsockIpcChannel protocol layer over AF_UNIX. AF_VSOCK on Linux
 * is byte-identical to AF_UNIX from the application's perspective once
 * connected — we use AF_UNIX here as a portable stand-in because /dev/vsock
 * isn't always available on CI / dev hosts, and the kernel's vsock_loopback
 * module needs to be modprobed before AF_VSOCK can talk to itself.
 *
 * Vsock-specific paths (connection retry, address resolution) are exercised
 * indirectly via the same protocol code path; the only thing this test
 * doesn't cover is "does the kernel module accept our specific AF_VSOCK
 * arg combo" which is verified end-to-end in the dispatcher integration
 * tests once Phase 3 lands.
 */
class VsockIpcChannelTest {

    @Test
    void unixSocketHandshakeCompletes(@TempDir Path tmp) throws Exception {
        Path sockPath = tmp.resolve("ipc.sock");
        AFUNIXServerSocket server = AFUNIXServerSocket.newInstance();
        server.bind(AFUNIXSocketAddress.of(sockPath.toFile()));

        ExecutorService exec = Executors.newSingleThreadExecutor();
        Future<String> readyFromWorker = exec.submit(() -> {
            try (Socket client = server.accept();
                 BufferedReader r = new BufferedReader(
                     new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8));
                 OutputStream w = client.getOutputStream()) {
                String first = r.readLine();
                // Simulate dispatcher sending GO after seeing READY.
                w.write("GO\n".getBytes(StandardCharsets.UTF_8));
                w.flush();
                return first;
            }
        });

        // Worker side: the channel under test. AF_UNIX override path bypasses
        // the AF_VSOCK capability check.
        VsockIpcChannel ipc = new VsockIpcChannel(
            VsockIpcChannel.DEFAULT_HOST_CID, /*port*/ 0, sockPath.toString());
        try {
            ipc.announceReady();
            String go = ipc.awaitGoSignal();
            assertEquals("go", go);
            assertEquals("READY", readyFromWorker.get(5, TimeUnit.SECONDS));
        } finally {
            ipc.close();
            server.close();
            exec.shutdownNow();
        }
    }

    @Test
    void connectRetriesUntilServerBinds(@TempDir Path tmp) throws Exception {
        Path sockPath = tmp.resolve("late.sock");

        ExecutorService exec = Executors.newCachedThreadPool();
        // Bring the server up only after a delay so the channel has to retry.
        Future<?> serverFuture = exec.submit(() -> {
            try {
                Thread.sleep(150);
                AFUNIXServerSocket server = AFUNIXServerSocket.newInstance();
                server.bind(AFUNIXSocketAddress.of(sockPath.toFile()));
                try (Socket client = server.accept();
                     OutputStream w = client.getOutputStream();
                     BufferedReader r = new BufferedReader(
                         new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8))) {
                    r.readLine();
                    w.write("GO\n".getBytes(StandardCharsets.UTF_8));
                    w.flush();
                } finally {
                    server.close();
                }
            } catch (Exception e) { throw new RuntimeException(e); }
            return null;
        });

        VsockIpcChannel ipc = new VsockIpcChannel(
            VsockIpcChannel.DEFAULT_HOST_CID, 0, sockPath.toString());
        try {
            ipc.announceReady();
            assertEquals("go", ipc.awaitGoSignal());
        } finally {
            ipc.close();
            serverFuture.get(5, TimeUnit.SECONDS);
            exec.shutdownNow();
        }
    }

    @Test
    void awaitGoSignalIgnoresUnknownLinesUntilGo(@TempDir Path tmp) throws Exception {
        Path sockPath = tmp.resolve("noisy.sock");
        AFUNIXServerSocket server = AFUNIXServerSocket.newInstance();
        server.bind(AFUNIXSocketAddress.of(sockPath.toFile()));

        ExecutorService exec = Executors.newSingleThreadExecutor();
        exec.submit(() -> {
            try (Socket client = server.accept();
                 BufferedReader r = new BufferedReader(
                     new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8));
                 OutputStream w = client.getOutputStream()) {
                r.readLine();
                w.write("HELLO\n".getBytes(StandardCharsets.UTF_8));
                w.write("STATS hello=1\n".getBytes(StandardCharsets.UTF_8));
                w.write("GO\n".getBytes(StandardCharsets.UTF_8));
                w.flush();
            }
            return null;
        });

        VsockIpcChannel ipc = new VsockIpcChannel(
            VsockIpcChannel.DEFAULT_HOST_CID, 0, sockPath.toString());
        try {
            ipc.announceReady();
            assertEquals("go", ipc.awaitGoSignal());
        } finally {
            ipc.close();
            server.close();
            exec.shutdownNow();
        }
    }
}
