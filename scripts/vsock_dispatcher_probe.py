#!/usr/bin/env python3
"""Host-side reference implementation of the worker↔dispatcher vsock protocol.

This is a STAND-ALONE harness for validating that a VsockIpcChannel worker
talks correctly to a dispatcher-side listener. It is NOT the production
dispatcher integration (that lives in Phase 3 — once landed, this script
should become a regression-fixture rather than a primary tool).

Usage — vsock mode (host machine, requires `modprobe vhost_vsock`):
    python3 scripts/vsock_dispatcher_probe.py --port 50000

Usage — unix-socket mode (no kernel module needed; matches Java test fixtures):
    python3 scripts/vsock_dispatcher_probe.py --unix /tmp/redtusk-ipc.sock

The harness:
  1. Binds the requested socket (AF_VSOCK or AF_UNIX).
  2. Waits for ONE worker connection.
  3. Expects a "READY\\n" line from the worker.
  4. Sends "GO\\n" back.
  5. Exits 0 on success or non-zero with a clear error.

Exit codes:
  0 — handshake completed cleanly
  1 — worker connected but the READY frame never arrived (timeout or wrong protocol)
  2 — operational error (bind failed, AF_VSOCK unsupported, etc.)
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
import time


def serve_vsock(port: int, accept_timeout_s: int = 30) -> int:
    if not hasattr(socket, "AF_VSOCK"):
        print("error: Python build has no AF_VSOCK (need Linux + Python 3.7+)",
              file=sys.stderr)
        return 2
    try:
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        # VMADDR_CID_ANY = -1 (kernel picks); CID_HOST = 2 (the value workers
        # in Kata's hybrid-vsock mode dial to reach the host).
        s.bind((socket.VMADDR_CID_ANY, port))
        s.listen(1)
    except OSError as e:
        print(f"error: AF_VSOCK bind failed (need vhost_vsock kernel module?): {e}",
              file=sys.stderr)
        return 2
    print(f"vsock dispatcher probe listening on cid=ANY port={port}", flush=True)
    return _accept_one(s, accept_timeout_s)


def serve_unix(path: str, accept_timeout_s: int = 30) -> int:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(path)
    s.listen(1)
    print(f"unix dispatcher probe listening on {path}", flush=True)
    return _accept_one(s, accept_timeout_s)


def _accept_one(s: socket.socket, accept_timeout_s: int) -> int:
    s.settimeout(accept_timeout_s)
    try:
        conn, peer = s.accept()
    except socket.timeout:
        print(f"error: no worker connection within {accept_timeout_s}s",
              file=sys.stderr)
        return 2
    print(f"worker connected from {peer!r}", flush=True)
    conn.settimeout(accept_timeout_s)

    # Read until we see "READY" or hit a newline that's not READY.
    buf = b""
    deadline = time.time() + accept_timeout_s
    while time.time() < deadline:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
        if b"\n" in buf:
            break

    line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    if line.upper() != "READY":
        print(f"error: expected READY, got {line!r}", file=sys.stderr)
        return 1
    print("got READY; sending GO", flush=True)
    conn.sendall(b"GO\n")
    conn.close()
    print("handshake OK", flush=True)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--port", type=int, help="AF_VSOCK port to listen on")
    g.add_argument("--unix", help="AF_UNIX socket path (test mode)")
    ap.add_argument("--accept-timeout", type=int, default=30,
                    help="seconds to wait for a worker connection")
    args = ap.parse_args(argv)

    if args.unix:
        return serve_unix(args.unix, args.accept_timeout)
    return serve_vsock(args.port, args.accept_timeout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
