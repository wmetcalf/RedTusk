"""The cold path must never inherit the warm tier's prewarm knob. `REDTUSK_PREWARM` is the warm JVM's knob -- `warmup()`
   sets it deliberately -- but `_run_worker` inherits the whole environment, so an operator who
   enables it on the container turns on a ~1.2s parser prewarm for every COLD job and every
   warm->cold fallback. That is pure added latency for a one-shot process that then parses
   exactly once, and it contradicts what Main.prewarmParsers' javadoc promises ("set only by
   the Python engine's warmup()").

2. `_warm_exit_detail` must not be able to hang. It read the dead JVM's stderr to EOF on the
   claim that "the process has already exited, so this cannot block". EOF needs every WRITER to
   close, not just the JVM: Tika forks external scanners (ZXingReader, tesseract) that inherit
   stderr, so one surviving child holds the pipe open and an unbounded read() parks a dispatcher
   thread inside a LOGGING HELPER -- ahead of the cold fallback that was supposed to keep the
   tier serving.
"""
from __future__ import annotations

import subprocess
import threading
import types

from redtusk import engine as engine_mod


def test_cold_worker_never_inherits_prewarm(tmp_path, monkeypatch):
    """MUTATION: drop the REDTUSK_PREWARM pin from _run_worker's env -> the operator's warm-tier
    setting leaks into every cold job and this fails."""
    seen = {}

    def _fake_run(cmd, **kw):
        seen.update(kw.get("env") or {})
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setenv("REDTUSK_PREWARM", "1")          # operator enabled it for the warm tier
    monkeypatch.setattr(engine_mod.subprocess, "run", _fake_run)
    monkeypatch.setattr(engine_mod, "_java_worker_argv", lambda scratch: ["java", "-jar", "x"])

    src = tmp_path / "in.doc"; src.write_bytes(b"x")
    out = tmp_path / "out"; out.mkdir()
    try:
        engine_mod._run_worker(src, out, timeout=5.0)
    except Exception:
        pass                                            # output validation is not what we assert

    assert seen.get("REDTUSK_PREWARM") == "0", (
        f"the cold path forwarded REDTUSK_PREWARM={seen.get('REDTUSK_PREWARM')!r}; every cold "
        f"job and every warm->cold fallback would pay the prewarm parse"
    )


# NOTE: the two tests that used to live here pinned `_warm_exit_detail`'s PIPE behaviour (that
# an unbounded read could hang, and that a bounded one still reported the last line). The warm
# JVM's stderr is a FILE now, so the hazard is gone by construction rather than by a timeout,
# and their replacements live in tests/unit/test_warm_stdio_cannot_deadlock.py -- including one
# that hands the function a deliberately hostile blocking pipe to prove it is never touched.
