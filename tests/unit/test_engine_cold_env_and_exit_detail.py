"""Two narrow guarantees on the cold path and the warm-death diagnostic.

1. The cold path must NEVER prewarm. `REDTUSK_PREWARM` is the warm JVM's knob -- `warmup()`
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


class _PipeHeldOpenByAChild:
    """stderr whose read() never returns -- a surviving grandchild still holds the write end."""

    def __init__(self) -> None:
        self.entered = threading.Event()

    def read(self, *a):
        self.entered.set()
        threading.Event().wait()        # blocks forever, exactly like a real read() at no-EOF


def test_warm_exit_detail_cannot_hang_the_dispatcher():
    """MUTATION: restore the unbounded `warm.proc.stderr.read()` -> this test times out instead
    of returning, which is precisely what it does to a dispatcher thread in production."""
    pipe = _PipeHeldOpenByAChild()
    warm = types.SimpleNamespace(proc=types.SimpleNamespace(stderr=pipe))

    result: list[str] = []
    t = threading.Thread(target=lambda: result.append(engine_mod.RedTuskEngine._warm_exit_detail(warm)),
                         daemon=True)
    t.start()
    t.join(timeout=10.0)

    assert pipe.entered.is_set(), "the test did not actually exercise the read path"
    assert not t.is_alive(), "_warm_exit_detail blocked on a pipe a live child still holds open"
    assert result and isinstance(result[0], str) and result[0], "it must still return a reason"


def test_warm_exit_detail_still_reports_the_last_line():
    """The bound must not cost the diagnostic it exists to provide."""
    class _P:
        def read(self, *a):
            return b"banner line\nCaused by: go-signal timeout rc=2\n"

    warm = types.SimpleNamespace(proc=types.SimpleNamespace(stderr=_P()))
    assert "go-signal timeout rc=2" in engine_mod.RedTuskEngine._warm_exit_detail(warm)
