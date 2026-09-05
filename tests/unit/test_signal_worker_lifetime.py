"""The cold-path signal thread must not outlive the scratch dir it writes into.

`_signal_worker` polls for `control.ready` up to the job timeout, then writes job.json and
control.go "regardless". The JVM is launched inside a `tempfile.TemporaryDirectory`, and the
main thread only does `t.join(timeout=5)` -- which returns whether or not the thread finished.
So a worker that exits quickly (a fast failure, a timeout) left the signal thread polling; the
scratch dir was then removed, and the thread later wrote into a deleted path:

    FileNotFoundError: '/tmp/tmpXXXX/slot/control/job.json'   in Thread-1 (_signal_worker)

A daemon thread's exception goes nowhere -- pytest's threadexception hook is the only reason
this was ever seen (RedTusk #53). These tests drive the real module function.
"""

from __future__ import annotations

import shutil
import threading
import time


def _run_signal_thread(tmp_path, *, timeout: float, exit_after_s: float,
                       remove_scratch: bool) -> list[BaseException]:
    """Drive the real `_signal_worker` shape: start it, 'run' a worker, tear the dir down."""
    from redtusk import engine

    control_dir = tmp_path / "control"
    control_dir.mkdir(parents=True)
    caught: list[BaseException] = []

    def _hook(args):  # threading.excepthook
        caught.append(args.exc_value)

    old_hook = threading.excepthook
    threading.excepthook = _hook
    try:
        # The module builds the thread inside _cold_worker; exercise the same code by calling
        # the helper the way that function does, through the module's own globals.
        stop = threading.Event()
        job = {"input_path": "x", "output_dir": "y"}
        t = threading.Thread(
            target=engine._signal_worker_loop,
            args=(control_dir, job, timeout, stop),
            daemon=True,
        )
        t.start()
        time.sleep(exit_after_s)          # the JVM exits here
        stop.set()
        t.join(timeout=5)
        if remove_scratch:
            shutil.rmtree(tmp_path, ignore_errors=True)
        time.sleep(0.5)                   # give a still-live thread time to misbehave
        assert not t.is_alive(), "the signal thread outlived the worker it was signalling"
    finally:
        threading.excepthook = old_hook
    return caught


def test_the_signal_thread_ends_when_the_worker_exits(tmp_path):
    """control.ready never appears and the worker dies early: the thread must stop at once,
    not run to its own (much longer) deadline."""
    started = time.monotonic()
    caught = _run_signal_thread(tmp_path, timeout=30.0, exit_after_s=0.2, remove_scratch=False)
    elapsed = time.monotonic() - started

    assert not caught, f"the signal thread raised: {caught}"
    assert elapsed < 5.0, (
        f"took {elapsed:.1f}s: the thread ran toward its own deadline instead of stopping "
        "when the worker exited"
    )


def test_a_scratch_dir_removed_under_the_thread_raises_nothing(tmp_path):
    """Even if teardown wins the race, the thread must not die with an unhandled OSError."""
    caught = _run_signal_thread(tmp_path, timeout=2.0, exit_after_s=0.1, remove_scratch=True)

    assert not caught, f"the signal thread raised into the void: {caught}"


def test_the_go_signal_is_still_written_for_a_worker_that_is_alive(tmp_path):
    """The control: this thread exists to hand the worker its job, and must still do that."""
    from redtusk import engine

    control_dir = tmp_path / "control"
    control_dir.mkdir(parents=True)
    (control_dir / "control.ready").touch()      # the worker is up and waiting
    stop = threading.Event()

    t = threading.Thread(
        target=engine._signal_worker_loop,
        args=(control_dir, {"input_path": "x"}, 5.0, stop),
        daemon=True,
    )
    t.start()
    t.join(timeout=5)

    assert not t.is_alive()
    assert (control_dir / "job.json").exists(), "the worker was never handed its job"
    assert (control_dir / "control.go").exists(), "the worker was never released"


def test_a_control_dir_it_cannot_write_does_not_kill_the_thread(tmp_path):
    """The worker IS up (control.ready present) so the loop proceeds to the write -- and the
    write fails. That is the surviving race: teardown can win between the break and the write.

    Made deterministic with a read-only dir rather than by racing rmtree, so the guard is
    actually falsifiable: without it this thread dies with an unhandled PermissionError that
    nothing anywhere would report.
    """
    from redtusk import engine

    control_dir = tmp_path / "control"
    control_dir.mkdir(parents=True)
    (control_dir / "control.ready").touch()
    control_dir.chmod(0o500)                    # readable + traversable, NOT writable

    caught: list[BaseException] = []
    old_hook = threading.excepthook
    threading.excepthook = lambda args: caught.append(args.exc_value)
    try:
        t = threading.Thread(
            target=engine._signal_worker_loop,
            args=(control_dir, {"input_path": "x"}, 5.0, threading.Event()),
            daemon=True,
        )
        t.start()
        t.join(timeout=5)
    finally:
        threading.excepthook = old_hook
        control_dir.chmod(0o700)                # so tmp_path cleanup works

    assert not t.is_alive()
    assert not caught, f"the signal thread died with an unhandled error: {caught}"
