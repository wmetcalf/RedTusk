"""Dispatcher-side vsock server for the microvm worker profile.

Each worker slot owns a :class:`VsockSlotServer` that binds an AF_VSOCK
listener on a unique port (or an AF_UNIX socket for tests).

Two flavors of worker use this server, with different output paths:

* **Docker-microvm (kata) profile** — full streaming, both directions::

      worker → host:   "READY\\n"
      host   → worker: "GO\\n"
      host   → worker: "JOB <N>\\n" + N bytes UTF-8 JobDescriptor JSON
                       "INPUT <M>\\n" + M bytes input-file payload
      worker → host:   "RESULT <K>\\n" + K bytes metadata.json
                       "ARTIFACT <relPath> <L>\\n" + L bytes per file (0+)
                       "DONE\\n"

* **Firecracker profile** — control plane only over vsock; OUTPUT (metadata
  + artifacts) goes to a per-slot virtio-blk ext4 disk the guest mounts at
  ``/tmp/redtusk-out`` and the host reads back via ``debugfs rdump`` after
  the VM powers off. The worker's ``VsockIpcChannel.sendResult`` /
  ``sendArtifact`` are no-ops in this mode. The host's
  :meth:`receive_result` is correspondingly a no-op; ``wait()`` reads the
  disk and FC-process-exit is the "done" signal (do NOT await a vsock
  DONE frame — the worker closes the socket on exit, which would look
  like protocol corruption). Output is OFF vsock because the guest
  virtio-vsock layer corrupts large transfers under concurrent host load.

The server is intentionally **synchronous in its socket I/O** — the
dispatcher invokes it via :func:`asyncio.to_thread` so the asyncio
event loop stays responsive while the worker is doing CPU-bound parse
work. This keeps the protocol code simple (no asyncio socket adapter)
and aligns with the file-IPC dispatcher's polling pattern.

For unit testing on hosts without /dev/vsock the server transparently
binds AF_UNIX when ``unix_path`` is set instead of ``cid+port``.
"""
from __future__ import annotations

import json
import logging
import os
import socket
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

# Generous default per-frame ceiling: 64 MiB — beyond what we'd ever
# expect for a single artifact. Caps RAM consumption against a misbehaving
# or malicious worker that lies about a payload's length. The dispatcher
# can override per-slot via :class:`VsockSlotServer.max_frame_bytes`.
DEFAULT_MAX_FRAME_BYTES = 64 * 1024 * 1024


class VsockProtocolError(Exception):
    """Raised when the worker's framing doesn't conform to the protocol."""


class VsockSlotServer:
    """Per-slot listener that drives one worker through its full lifecycle.

    Lifecycle:
      1. :meth:`bind` — open the listening socket.
      2. :meth:`accept_ready` — block until the worker connects + sends READY.
      3. :meth:`send_go` — release the worker to start the job.
      4. :meth:`send_job` — push descriptor JSON + input bytes.
      5. :meth:`receive_result(artifacts_dir)` — collect metadata.json
         and all ARTIFACT frames until DONE; write artifacts under
         ``artifacts_dir`` preserving worker-side relative paths.
      6. :meth:`close` — release the socket(s).

    All step methods raise :class:`VsockProtocolError` on framing
    violations and :class:`OSError`/:class:`socket.timeout` on transport
    issues; the dispatcher should treat either as a worker failure.
    """

    def __init__(
        self,
        *,
        port: int | None = None,
        cid: int = -1,  # VMADDR_CID_ANY
        unix_path: str | None = None,
        max_frame_bytes: int = DEFAULT_MAX_FRAME_BYTES,
        ready_timeout_s: float = 120.0,
        recv_timeout_s: float = 600.0,
    ) -> None:
        if (port is None) == (unix_path is None):
            raise ValueError("provide exactly one of port= or unix_path=")
        self.port = port
        self.cid = cid
        self.unix_path = unix_path
        self.max_frame_bytes = max_frame_bytes
        self.ready_timeout_s = ready_timeout_s
        self.recv_timeout_s = recv_timeout_s
        self._listen: socket.socket | None = None
        self._conn: socket.socket | None = None

    def bind(self) -> None:
        if self._listen is not None:
            raise RuntimeError("already bound")
        if self.unix_path is not None:
            try:
                os.unlink(self.unix_path)
            except FileNotFoundError:
                pass
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(self.unix_path)
        else:
            if not hasattr(socket, "AF_VSOCK"):
                raise OSError("Python build has no AF_VSOCK (Linux + py3.7+ needed)")
            s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
            s.bind((self.cid, self.port))
        s.listen(1)
        self._listen = s
        _logger.info(
            "vsock_server.bind",
            extra={"port": self.port, "cid": self.cid, "unix_path": self.unix_path},
        )

    def accept_ready(self) -> None:
        if self._listen is None:
            raise RuntimeError("bind() not called")
        self._listen.settimeout(self.ready_timeout_s)
        conn, peer = self._listen.accept()
        conn.settimeout(self.recv_timeout_s)
        self._conn = conn
        _logger.info("vsock_server.accept", extra={"peer": repr(peer)})
        line = self._read_line()
        if line.strip().upper() != "READY":
            raise VsockProtocolError(f"expected READY, got {line!r}")

    def send_go(self) -> None:
        self._send_line("GO")

    def send_job(self, descriptor: dict[str, Any], input_bytes: bytes) -> None:
        """Send the JOB+INPUT frame pair. Descriptor is JSON-encoded; input
        bytes are sent verbatim."""
        if self._conn is None:
            raise RuntimeError("not connected")
        json_bytes = json.dumps(descriptor).encode("utf-8")
        self._conn.sendall(f"JOB {len(json_bytes)}\n".encode())
        self._conn.sendall(json_bytes)
        self._conn.sendall(f"INPUT {len(input_bytes)}\n".encode())
        self._conn.sendall(input_bytes)

    def receive_result(
        self, artifacts_dir: Path, max_extracted_bytes: int | None = None
    ) -> dict[str, Any]:
        """Read RESULT then zero or more ARTIFACT frames then DONE.

        :param artifacts_dir: Host directory where ARTIFACT payloads are
            written. The worker-side relative path is preserved so e.g.
            ``embedded/0001.bin`` lands at ``artifacts_dir/embedded/0001.bin``.
        :param max_extracted_bytes: Host-side cumulative cap on total extracted bytes
            (metadata + all artifacts combined).

        Returns a dict with::

            {
                "metadata": <bytes of metadata.json>,
                "artifacts": [<relative paths actually written>, ...]
            }
        """
        if self._conn is None:
            raise RuntimeError("not connected")
        artifacts_dir = Path(artifacts_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        metadata: bytes | None = None
        artifacts: list[str] = []
        total_bytes = 0

        while True:
            line = self._read_line()
            header = line.strip()
            if not header:
                continue
            parts = header.split(" ")
            tag = parts[0].upper()
            if tag == "RESULT":
                if len(parts) != 2:
                    raise VsockProtocolError(f"malformed RESULT header: {header}")
                length = int(parts[1])
                if length < 0:
                    raise VsockProtocolError(f"negative RESULT length: {length}")
                if max_extracted_bytes is not None and total_bytes + length > max_extracted_bytes:
                    import shutil
                    shutil.rmtree(artifacts_dir, ignore_errors=True)
                    artifacts_dir.mkdir(parents=True, exist_ok=True)
                    raise VsockProtocolError(
                        f"extracted output exceeds cap: >{max_extracted_bytes} bytes"
                    )
                metadata = self._read_blob(length)
                total_bytes += length
            elif tag == "ARTIFACT":
                if len(parts) < 3:
                    raise VsockProtocolError(f"malformed ARTIFACT header: {header}")
                # Path may contain spaces; the LAST token is the length.
                length = int(parts[-1])
                if length < 0:
                    raise VsockProtocolError(f"negative ARTIFACT length: {length}")
                if max_extracted_bytes is not None and total_bytes + length > max_extracted_bytes:
                    import shutil
                    shutil.rmtree(artifacts_dir, ignore_errors=True)
                    artifacts_dir.mkdir(parents=True, exist_ok=True)
                    raise VsockProtocolError(
                        f"extracted output exceeds cap: >{max_extracted_bytes} bytes"
                    )
                rel_path = " ".join(parts[1:-1])
                # Reject path-traversal: relative path with no .. components,
                # no absolute paths.
                if rel_path.startswith("/") or ".." in Path(rel_path).parts:
                    raise VsockProtocolError(f"unsafe artifact path: {rel_path!r}")
                dest = artifacts_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    self._stream_blob_to_file(length, f)
                artifacts.append(rel_path)
                total_bytes += length
            elif tag == "READY":
                # CRaC restore can re-announce READY: afterRestore() reopens
                # the socket and re-sends READY, and announceReady() is
                # idempotent, so a second READY can trail the one consumed by
                # accept_ready(). VsockIpcChannel.java documents that the
                # dispatcher must tolerate duplicate READY frames — skip them.
                continue
            elif tag == "DONE":
                break
            else:
                raise VsockProtocolError(f"unknown frame tag: {tag!r}")

        if metadata is None:
            raise VsockProtocolError("DONE without prior RESULT frame")
        return {"metadata": metadata, "artifacts": artifacts}

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None
        if self._listen is not None:
            try:
                self._listen.close()
            except OSError:
                pass
            self._listen = None
        if self.unix_path is not None:
            try:
                os.unlink(self.unix_path)
            except FileNotFoundError:
                pass

    # ── internals ─────────────────────────────────────────────────────────

    def _read_line(self) -> str:
        """Read a single line terminated by \\n from the connection."""
        assert self._conn is not None
        buf = bytearray()
        while True:
            b = self._conn.recv(1)
            if not b:
                if not buf:
                    raise VsockProtocolError("connection closed mid-line")
                return buf.decode("utf-8", errors="replace")
            if b == b"\n":
                return buf.decode("utf-8", errors="replace")
            if b == b"\r":
                continue
            buf.extend(b)
            if len(buf) > 4096:
                # A control line this long means the byte stream desynced (a
                # blob length didn't match the bytes on the wire). Log a prefix
                # to aid diagnosis; see fc_vcpu_count note in limits.py.
                _logger.warning(
                    "vsock_server.control_line_overflow",
                    extra={"prefix": repr(bytes(buf[:48]))},
                )
                raise VsockProtocolError("control line exceeds 4 KiB")

    def _read_blob(self, length: int) -> bytes:
        assert self._conn is not None
        if length < 0 or length > self.max_frame_bytes:
            raise VsockProtocolError(
                f"blob length {length} out of range (cap {self.max_frame_bytes})"
            )
        chunks: list[bytes] = []
        remaining = length
        while remaining > 0:
            chunk = self._conn.recv(min(64 * 1024, remaining))
            if not chunk:
                raise VsockProtocolError(
                    f"EOF mid-blob at {length - remaining}/{length}"
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _stream_blob_to_file(self, length: int, fobj: Any) -> None:
        """Same as _read_blob but streams to file to avoid holding huge
        payloads in memory."""
        assert self._conn is not None
        if length < 0 or length > self.max_frame_bytes:
            raise VsockProtocolError(
                f"blob length {length} out of range (cap {self.max_frame_bytes})"
            )
        remaining = length
        while remaining > 0:
            chunk = self._conn.recv(min(64 * 1024, remaining))
            if not chunk:
                raise VsockProtocolError(
                    f"EOF mid-blob at {length - remaining}/{length}"
                )
            fobj.write(chunk)
            remaining -= len(chunk)

    def _send_line(self, text: str) -> None:
        if self._conn is None:
            raise RuntimeError("not connected")
        self._conn.sendall((text + "\n").encode("utf-8"))
