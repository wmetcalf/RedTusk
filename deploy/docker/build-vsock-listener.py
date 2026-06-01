#!/usr/bin/env python3
"""Build-time vsock-shim AF_UNIX listener.

Used by Dockerfile.crac to satisfy the worker's vsock connect during the
CRaC checkpoint step. Accepts a single connection, logs whatever the worker
writes (typically just "READY\\n"), holds the connection open until the
worker side closes (which happens when VsockIpcChannel.beforeCheckpoint
fires inside Core.checkpointRestore()).

The Dockerfile starts this in the background, points the worker at the
unix socket via REDTUSK_VSOCK_UNIX_PATH, then runs the --checkpoint JVM.
"""
import os
import socket
import sys

SOCK_PATH = os.environ.get("BUILD_VSOCK_SOCK", "/tmp/build-vsock.sock")

if os.path.exists(SOCK_PATH):
    os.unlink(SOCK_PATH)

srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCK_PATH)
srv.listen(1)
print(f"build-vsock: listening on {SOCK_PATH}", flush=True)

# Accept multiple connections — at build time the worker connects twice:
#   1. announceReady (before Core.checkpointRestore)
#   2. VsockIpcChannel.afterRestore re-issuing announceReady on the
#      synthetic "continue" path that warp takes at build time.
# Without accepting the second connection the worker would block in
# connectWithRetry for 30s × backoff retries and the build hangs.
import select
try:
    # Loop until parent kills us OR we've handled the two expected connections.
    expected_conns = 2
    handled = 0
    srv.settimeout(60.0)
    while handled < expected_conns:
        try:
            conn, _ = srv.accept()
        except socket.timeout:
            print(f"build-vsock: timed out after {handled} connections", flush=True)
            break
        print(f"build-vsock: accepted connection #{handled+1}", flush=True)
        handled += 1
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    print(f"build-vsock: connection #{handled} closed by peer", flush=True)
                    break
                sys.stdout.write(data.decode("utf-8", "replace"))
                sys.stdout.flush()
        except Exception as e:
            print(f"build-vsock: connection #{handled} recv error: {e}", flush=True)
        finally:
            conn.close()
    print(f"build-vsock: exiting after {handled} connections", flush=True)
finally:
    srv.close()
    try:
        os.unlink(SOCK_PATH)
    except OSError:
        pass
