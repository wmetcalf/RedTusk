"""The warm JVM's stdio must not be a pipe nobody reads until job time.

`warmup()` starts the JVM and nothing reads its output until `communicate()` at the FIRST JOB.
Everything the JVM emits before that -- boot, Tika class loading, and (with REDTUSK_PREWARM=1)
a whole parser-tree build -- accumulates in a 64 KiB kernel pipe buffer. Fill it and the JVM
BLOCKS ON WRITE, never signals ready, and the tier degrades to cold with nothing in the log but
"did not signal ready". The images bake REDTUSK_LOG_LEVEL=INFO, so the volume is not
hypothetical.

Files do not block. Sending the warm JVM's stdout/stderr to files in its own scratch dir
removes the deadlock by construction, and makes the death diagnostic a plain read of a file
rather than a race against a pipe a surviving child may still hold open.
"""
from __future__ import annotations

from pathlib import Path

import subprocess
import threading
import types

from redtusk import engine as engine_mod


def test_warmup_does_not_hand_the_jvm_an_unread_pipe(tmp_path, monkeypatch):
    """MUTATION: restore stdout=PIPE/stderr=PIPE -> a JVM that emits >64 KiB before ready
    deadlocks, and this fails."""
    seen = {}

    class _P:
        """Announces control.ready immediately, so warmup() returns instead of spending the
        full _WARMUP_READY_TIMEOUT poll (60s) in a test that only cares about the stdio kwargs."""

        def __init__(self, *a, **kw):
            seen.update(kw)
            self.returncode = None
            for f in ("stdout", "stderr"):
                h = kw.get(f)
                if hasattr(h, "name"):
                    ready = Path(h.name).parent / "control" / "control.ready"
                    ready.parent.mkdir(parents=True, exist_ok=True)
                    ready.touch()

        def poll(self):
            return None

        def kill(self):
            pass

        def wait(self, timeout=None):
            return 0

        def communicate(self, timeout=None):
            return (None, None)

    monkeypatch.setattr(engine_mod.subprocess, "Popen", _P)
    monkeypatch.setattr(engine_mod, "_java_worker_argv", lambda scratch: ["java", "-jar", "x"])

    eng = engine_mod.RedTuskEngine()
    try:
        eng.warmup()
    except Exception:
        pass          # readiness handshake is not what this asserts

    assert seen.get("stdout") is not subprocess.PIPE, "warm stdout is an unread PIPE"
    assert seen.get("stderr") is not subprocess.PIPE, "warm stderr is an unread PIPE"


def test_exit_detail_reads_the_file_and_needs_no_pipe(tmp_path):
    """The diagnostic survives the move -- and now cannot block at all, because a file read
    always terminates whatever else still holds the descriptor.

    MUTATION: read proc.stderr instead of the file -> nothing to read, and the reason is lost
    exactly when it is needed.
    """
    scratch = tmp_path / "slot"
    (scratch / "control").mkdir(parents=True)
    (scratch / engine_mod._WARM_STDERR_LOG).write_bytes(
        b"banner\nCaused by: go-signal timeout rc=2\n")

    class _HostilePipe:
        """If the diagnostic touches proc.stderr at all, this blocks -- exactly the production
        failure (a surviving ZXingReader/tesseract still holding the write end)."""
        def read(self, *a):
            threading.Event().wait()

    warm = types.SimpleNamespace(
        proc=types.SimpleNamespace(stderr=_HostilePipe()),
        scratch=scratch,
    )
    # On a THREAD with a join timeout, so a regression FAILS this test instead of hanging the
    # run. Learned the hard way: the first version asserted directly, and a mutation that
    # reintroduced the pipe read parked the whole suite forever -- a test that proves a hang by
    # hanging tells CI nothing except that CI is stuck.
    box: list[str] = []
    t = threading.Thread(
        target=lambda: box.append(engine_mod.RedTuskEngine._warm_exit_detail(warm)), daemon=True)
    t.start()
    t.join(timeout=10.0)
    assert not t.is_alive(), "_warm_exit_detail touched proc.stderr and blocked on it"
    assert box and "go-signal timeout rc=2" in box[0]


def test_exit_detail_is_graceful_when_there_is_no_log(tmp_path):
    scratch = tmp_path / "slot"
    scratch.mkdir(parents=True)
    warm = types.SimpleNamespace(proc=types.SimpleNamespace(stderr=None), scratch=scratch)
    assert engine_mod.RedTuskEngine._warm_exit_detail(warm)      # a reason, not an exception
