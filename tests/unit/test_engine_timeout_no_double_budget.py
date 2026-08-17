"""A warm-path TIMEOUT must not be re-run on the cold path.

Observed on the fleet: `ransomeware-guide.pdf` (8.4 MB, 151 embedded entries, ~84s of parse)
against the guest's 120s budget produced three different outcomes for the SAME input — sometimes
done, sometimes `engine_error: ... timed out after 120.0 seconds`, sometimes reaped as
"warm worker abandoned: owning dispatcher gone".

The abandoned case is the expensive one: the job is FAILED terminally (a warm orphan is never
requeued, deliberately — re-detonating untrusted input in a second sandbox is worse), and it holds
a slot the whole time. The cause was a silent doubling: the warm timeout raised RuntimeError,
which the enclosing `except Exception` caught and answered by re-running the same document on a
fresh cold JVM with a FULL fresh `timeout`. Total budget 2 x timeout, which is what pushed a
boundary document past the host's warm-stale cutoff (worker_timeout_s + requeue_grace_s).

Both directions matter, so both are pinned here:
  * TIMEOUT  -> no cold retry (the cold path has the same parser and the same budget)
  * CRASH    -> cold retry WITH a full budget (fail-closed; a broken warm tier must still serve)
"""
from __future__ import annotations

import subprocess
import types

import pytest

from redtusk import engine as engine_mod
from redtusk.engine import EngineTimeout, RedTuskEngine


class _FakeProc:
    """Stands in for the warm JVM subprocess."""

    def __init__(self, *, timeout: bool, returncode: int = 0) -> None:
        self._timeout = timeout
        self.returncode = returncode
        self.killed = False

    def poll(self):
        # ALIVE at the pre-flight check. Returning the exit code here instead would send
        # _produce_rmeta down its "warm handle is already dead" branch at the top, which never
        # enters the try block at all -- an earlier version of this fake did exactly that, and the
        # crash test passed while proving nothing (mutation-checked: broadening the EngineTimeout
        # clause to `except Exception` survived).
        return None

    def communicate(self, timeout=None):
        if self._timeout and timeout is not None:
            raise subprocess.TimeoutExpired(cmd="java", timeout=timeout)
        return (b"", b"boom")

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return self.returncode


def _engine_with_warm(tmp_path, proc):
    eng = RedTuskEngine()
    scratch = tmp_path / "slot"
    (scratch / "in").mkdir(parents=True)
    (scratch / "control").mkdir(parents=True)
    eng._warm = engine_mod._WarmWorker(
        proc=proc,
        scratch=scratch,
        in_dir=scratch / "in",
        control_dir=scratch / "control",
        tmp=types.SimpleNamespace(cleanup=lambda: None),
    )
    return eng


def test_warm_timeout_does_not_rerun_on_the_cold_path(tmp_path, monkeypatch):
    """MUTATION: remove the `except EngineTimeout: raise` clause -> _run_worker is called with a
    second full budget, and this test fails on both assertions."""
    calls: list[float] = []
    monkeypatch.setattr(engine_mod, "_run_worker",
                        lambda inp, out, timeout: calls.append(timeout))

    src = tmp_path / "slow.pdf"
    src.write_bytes(b"%PDF-1.4 slow")
    eng = _engine_with_warm(tmp_path, _FakeProc(timeout=True))

    with pytest.raises(EngineTimeout):
        eng._produce_rmeta(src, tmp_path / "out", timeout=120.0)

    assert calls == [], (
        f"a warm TIMEOUT was re-run on the cold path with budget(s) {calls}: total guest budget "
        f"becomes {120.0 + sum(calls)}s instead of 120.0s"
    )


def test_warm_crash_still_fails_closed_to_cold_with_a_full_budget(tmp_path, monkeypatch):
    """The other direction: a warm JVM that DIED must still get a working cold run.

    MUTATION: broaden the EngineTimeout clause to `except Exception: raise` -> a crashed warm JVM
    stops falling back, and a transiently broken warm tier fails every job instead of degrading.
    """
    calls: list[float] = []
    monkeypatch.setattr(engine_mod, "_run_worker",
                        lambda inp, out, timeout: calls.append(timeout))

    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4 ok")
    eng = _engine_with_warm(tmp_path, _FakeProc(timeout=False, returncode=134))

    eng._produce_rmeta(src, tmp_path / "out", timeout=120.0)

    assert calls == [120.0], (
        f"a warm CRASH must fall back to cold with the FULL budget, got {calls}"
    )


def test_engine_timeout_is_not_swallowed_by_the_generic_handler():
    """EngineTimeout must remain distinguishable from a generic engine fault.

    It is a RuntimeError subclass, so ordering of the except clauses is the only thing keeping it
    out of the cold-retry path — assert the type relationship the ordering depends on.
    """
    assert issubclass(EngineTimeout, RuntimeError)
    assert EngineTimeout is not RuntimeError
