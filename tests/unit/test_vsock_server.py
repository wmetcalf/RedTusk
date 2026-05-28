"""Unit tests for the dispatcher-side vsock server.

Vsock-specific kernel paths can't be exercised on every CI host (need
vhost_vsock or vsock_loopback modules), so these tests run over AF_UNIX
sockets — protocol code is identical, only the address family differs.
The Java VsockIpcChannel tests cover the equivalent client side over
AF_UNIX too, so the two halves are validated against each other in
all but the address-family-specific bytes.
"""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from pathlib import Path

import pytest

from redtusk.sandbox.vsock_server import VsockProtocolError, VsockSlotServer


def _send_line(sock: socket.socket, text: str) -> None:
    sock.sendall((text + "\n").encode("utf-8"))


def _send_blob(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(payload)


def _read_line(sock: socket.socket) -> bytes:
    buf = bytearray()
    while not buf.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def _run_worker(unix_path: str, *, send_result: bytes,
                send_artifacts: list[tuple[str, bytes]] | None = None) -> dict:
    """Tiny in-test worker simulator. Connects to the server, runs the
    client side of the protocol, returns the JOB+INPUT it received."""
    # Wait briefly for the server to bind.
    for _ in range(50):
        if os.path.exists(unix_path):
            break
        time.sleep(0.01)
    cli = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    cli.connect(unix_path)
    received: dict = {}
    try:
        _send_line(cli, "READY")
        # Read GO
        go = _read_line(cli)
        assert go == b"GO\n", f"expected GO, got {go!r}"

        # Read JOB header
        hdr_buf = bytearray()
        while not hdr_buf.endswith(b"\n"):
            hdr_buf.extend(cli.recv(1))
        job_hdr = hdr_buf.decode("utf-8").strip()
        assert job_hdr.startswith("JOB "), f"expected JOB, got {job_hdr!r}"
        job_len = int(job_hdr.split(" ")[1])
        job_buf = b""
        while len(job_buf) < job_len:
            job_buf += cli.recv(job_len - len(job_buf))
        received["job"] = json.loads(job_buf)

        # Read INPUT header + payload
        hdr_buf.clear()
        while not hdr_buf.endswith(b"\n"):
            hdr_buf.extend(cli.recv(1))
        input_hdr = hdr_buf.decode("utf-8").strip()
        assert input_hdr.startswith("INPUT "), f"expected INPUT, got {input_hdr!r}"
        input_len = int(input_hdr.split(" ")[1])
        input_buf = b""
        while len(input_buf) < input_len:
            input_buf += cli.recv(input_len - len(input_buf))
        received["input"] = input_buf

        # Send RESULT
        _send_line(cli, f"RESULT {len(send_result)}")
        _send_blob(cli, send_result)
        # Send any artifacts
        for rel, payload in (send_artifacts or []):
            _send_line(cli, f"ARTIFACT {rel} {len(payload)}")
            _send_blob(cli, payload)
        # DONE
        _send_line(cli, "DONE")
    finally:
        cli.close()
    return received


def test_full_handshake_round_trip(tmp_path: Path) -> None:
    sock_path = str(tmp_path / "ipc.sock")
    artifacts_dir = tmp_path / "artifacts"

    server = VsockSlotServer(unix_path=sock_path, ready_timeout_s=5,
                             recv_timeout_s=5)
    server.bind()

    descriptor = {"input_path": "/tmp/in", "output_dir": "/tmp/out",
                  "sha256": "a" * 64, "filename_hint": "test.lnk"}
    input_bytes = b"the input file contents"
    expected_metadata = b'{"hello":"world"}'
    expected_artifacts = [("embedded/0.bin", b"\x00\x01\x02"),
                          ("text/entry.txt", b"hello text")]

    received_box: dict = {}
    t = threading.Thread(target=lambda: received_box.update(
        _run_worker(sock_path, send_result=expected_metadata,
                    send_artifacts=expected_artifacts)))
    t.start()

    try:
        server.accept_ready()
        server.send_go()
        server.send_job(descriptor, input_bytes)
        result = server.receive_result(artifacts_dir)
    finally:
        t.join(timeout=5)
        server.close()

    assert received_box["job"] == descriptor
    assert received_box["input"] == input_bytes
    assert result["metadata"] == expected_metadata
    assert set(result["artifacts"]) == {"embedded/0.bin", "text/entry.txt"}
    assert (artifacts_dir / "embedded/0.bin").read_bytes() == b"\x00\x01\x02"
    assert (artifacts_dir / "text/entry.txt").read_bytes() == b"hello text"


def test_rejects_path_traversal_artifact(tmp_path: Path) -> None:
    sock_path = str(tmp_path / "ipc.sock")
    artifacts_dir = tmp_path / "out"
    server = VsockSlotServer(unix_path=sock_path, ready_timeout_s=5,
                             recv_timeout_s=5)
    server.bind()

    def bad_worker():
        for _ in range(50):
            if os.path.exists(sock_path):
                break
            time.sleep(0.01)
        cli = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cli.connect(sock_path)
        try:
            _send_line(cli, "READY")
            _read_line(cli)  # consume GO
            # Read+discard JOB
            buf = bytearray()
            while not buf.endswith(b"\n"):
                buf.extend(cli.recv(1))
            jl = int(buf.decode("utf-8").strip().split(" ")[1])
            while jl > 0:
                jl -= len(cli.recv(jl))
            # Read+discard INPUT
            buf.clear()
            while not buf.endswith(b"\n"):
                buf.extend(cli.recv(1))
            il = int(buf.decode("utf-8").strip().split(" ")[1])
            while il > 0:
                il -= len(cli.recv(il))
            # Send RESULT then a malicious ARTIFACT path
            _send_line(cli, "RESULT 2")
            _send_blob(cli, b"{}")
            _send_line(cli, "ARTIFACT ../../../etc/passwd 4")
            _send_blob(cli, b"AAAA")
            _send_line(cli, "DONE")
        finally:
            cli.close()

    t = threading.Thread(target=bad_worker)
    t.start()
    try:
        server.accept_ready()
        server.send_go()
        server.send_job({"x": 1}, b"input")
        with pytest.raises(VsockProtocolError, match="unsafe artifact path"):
            server.receive_result(artifacts_dir)
    finally:
        t.join(timeout=5)
        server.close()


def test_bind_requires_either_port_or_unix() -> None:
    with pytest.raises(ValueError):
        VsockSlotServer()
    with pytest.raises(ValueError):
        VsockSlotServer(port=12345, unix_path="/tmp/x")


def test_oversized_blob_rejected(tmp_path: Path) -> None:
    sock_path = str(tmp_path / "ipc.sock")
    server = VsockSlotServer(unix_path=sock_path, max_frame_bytes=128,
                             ready_timeout_s=5, recv_timeout_s=5)
    server.bind()

    def malicious_worker():
        for _ in range(50):
            if os.path.exists(sock_path):
                break
            time.sleep(0.01)
        cli = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cli.connect(sock_path)
        try:
            _send_line(cli, "READY")
            _read_line(cli)
            buf = bytearray()
            while not buf.endswith(b"\n"):
                buf.extend(cli.recv(1))
            jl = int(buf.decode("utf-8").strip().split(" ")[1])
            while jl > 0:
                jl -= len(cli.recv(jl))
            buf.clear()
            while not buf.endswith(b"\n"):
                buf.extend(cli.recv(1))
            il = int(buf.decode("utf-8").strip().split(" ")[1])
            while il > 0:
                il -= len(cli.recv(il))
            # Send a RESULT frame claiming to be way over the cap
            _send_line(cli, "RESULT 999999999")
        finally:
            cli.close()

    t = threading.Thread(target=malicious_worker)
    t.start()
    try:
        server.accept_ready()
        server.send_go()
        server.send_job({"x": 1}, b"in")
        with pytest.raises(VsockProtocolError, match="out of range"):
            server.receive_result(tmp_path / "out")
    finally:
        t.join(timeout=5)
        server.close()
