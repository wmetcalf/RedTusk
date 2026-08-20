"""A warm TIMEOUT means two very different things, and the host must tell them apart.

Both look identical at `communicate(timeout=...)`:

  the JVM TOOK the job and ran out of budget   -> a slow document. The cold path has the same
                                                  parser and the same budget, so re-running it
                                                  there spends the budget twice for the same
                                                  answer -- which is what pushed a boundary PDF
                                                  past the host's warm-stale cutoff and got it
                                                  reaped as "warm worker abandoned".
  the JVM NEVER GOT the job                    -> infrastructure: the control dir not visible
                                                  after a restore, a wedged process, a full
                                                  stdio pipe. Nothing about the DOCUMENT is
                                                  implicated, so failing it terminally with no
                                                  fallback burns a job for a host-side fault.

Treating every timeout as the first case (which is what shipping only the EngineTimeoutError change
did) removes the fallback from the second. The JVM now writes `control/control.started` the
instant it takes the go-signal, so the host can ask instead of guess.
"""
from __future__ import annotations

import subprocess
import types
from pathlib import Path
from typing import Any, cast

import pytest

from redtusk import engine as engine_mod
from redtusk.engine import EngineTimeoutError, RedTuskEngine


class _FakeProc:
    def __init__(self, *, timeout: bool, returncode: int = 0) -> None:
        self._timeout = timeout
        self.returncode = returncode
        self.killed = False

    def poll(self) -> int | None:
        return None                      # ALIVE at the pre-flight check

    def communicate(self, timeout: float | None = None) -> tuple[bytes | None, bytes | None]:
        if self._timeout and timeout is not None:
            raise subprocess.TimeoutExpired(cmd="java", timeout=timeout)
        return (b"", b"boom")

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


def _engine_with_warm(tmp_path: Path, proc: Any, *, started: bool) -> RedTuskEngine:
    eng = RedTuskEngine()
    scratch = tmp_path / "slot"
    (scratch / "in").mkdir(parents=True)
    control = scratch / "control"
    control.mkdir(parents=True)
    if started:
        (control / "control.started").touch()
    eng._warm = engine_mod._WarmWorker(
        proc=proc, scratch=scratch, in_dir=scratch / "in", control_dir=control,
        tmp=cast(Any, types.SimpleNamespace(cleanup=lambda: None)),
    )
    return eng


def test_a_timeout_after_the_job_started_is_not_re_run(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """MUTATION: ignore control.started and always raise EngineTimeoutError -> unchanged here, but
    the next test fails. Both directions are needed; neither alone pins the discriminator."""
    calls: list[float] = []
    monkeypatch.setattr(engine_mod, "_run_worker", lambda i, o, timeout: calls.append(timeout))

    src = tmp_path / "slow.pdf"
    src.write_bytes(b"%PDF-1.4 slow")
    eng = _engine_with_warm(tmp_path, _FakeProc(timeout=True), started=True)

    with pytest.raises(EngineTimeoutError):
        eng._produce_rmeta(src, tmp_path / "out", timeout=120.0)
    assert calls == [], (
        f"the JVM demonstrably started this document; re-running it cold spends the budget "
        f"twice for the same answer (got {calls})"
    )


def test_a_timeout_before_the_job_started_falls_back_to_cold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MUTATION: raise EngineTimeoutError unconditionally (i.e. drop the marker check) -> a JVM that
    never picked the job up fails the job terminally with no fallback, and this fails."""
    calls: list[float] = []
    monkeypatch.setattr(engine_mod, "_run_worker", lambda i, o, timeout: calls.append(timeout))

    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4 ok")
    eng = _engine_with_warm(tmp_path, _FakeProc(timeout=True), started=False)

    eng._produce_rmeta(src, tmp_path / "out", timeout=120.0)      # must NOT raise
    assert calls == [120.0], (
        f"a warm JVM that never took the job is an infrastructure fault, not a slow document; "
        f"it must still get a full cold run (got {calls})"
    )


def test_the_warm_jvm_is_still_killed_either_way(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """Whichever branch is taken, the slot's process must not be left running."""
    monkeypatch.setattr(engine_mod, "_run_worker", lambda i, o, timeout: None)
    src = tmp_path / "d.pdf"
    src.write_bytes(b"%PDF")

    for started in (True, False):
        proc = _FakeProc(timeout=True)
        eng = _engine_with_warm(tmp_path / f"s{started}", proc, started=started)
        try:
            eng._produce_rmeta(src, tmp_path / f"o{started}", timeout=5.0)
        except EngineTimeoutError:
            pass
        assert proc.killed, f"warm JVM left alive on the started={started} path"
