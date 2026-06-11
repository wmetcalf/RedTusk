"""Warm-JVM path: warmup() pre-boots a JVM; detonate() feeds the already-warm one.

The blastbox FC warm-snapshot tier calls engine.warmup() before taking the VM
snapshot, so the JVM-boot cost is paid once (captured in the snapshot) and each
restored slot's detonate() reuses the warm JVM. This test exercises that path
in-process (no FC) and asserts:
  - warmup() produces a warm JVM,
  - the warm detonation is correct (status ok),
  - warm output is equivalent to the cold path (same detection + tree shape),
  - the warm tier is fail-closed (a broken warmup still detonates via cold).

Mark: ``integration`` (needs java + the worker jar).
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from blastbox.limits import Limits

from redtusk.engine import _DEFAULT_WORKER_JAR, RedTuskEngine

_ROOT = Path(__file__).resolve().parents[2]
_DOCX = _ROOT / "deploy" / "docker" / "appcds-warmup-corpus" / "qr_fixture.docx"


def _worker_jar() -> str:
    return os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)


def _skip() -> str | None:
    if shutil.which("java") is None:
        return "java not on PATH"
    if not Path(_worker_jar()).is_file():
        return f"worker jar {_worker_jar()!r} not present"
    if not _DOCX.is_file():
        return f"fixture missing: {_DOCX}"
    return None


_SKIP = _skip()
pytestmark = pytest.mark.integration


def _detonate(engine: RedTuskEngine) -> object:
    with tempfile.TemporaryDirectory() as td:
        return engine.detonate(_DOCX, Path(td), Limits.from_env())


@pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")
def test_warm_detonation_matches_cold():
    cold = _detonate(RedTuskEngine())

    warm_engine = RedTuskEngine()
    warm_engine.warmup()
    assert warm_engine._warm is not None, "warmup() did not produce a warm JVM"
    warm = _detonate(warm_engine)
    # the warm JVM is one-shot — consumed after the job
    assert warm_engine._warm is None

    assert cold.status == "ok"
    assert warm.status == "ok"
    assert warm.detected.mime == cold.detected.mime
    # same recursive tree shape + same declared-artifact count
    assert _tree_size(warm.payload) == _tree_size(cold.payload)
    assert len(warm.artifacts) == len(cold.artifacts)


@pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")
def test_warm_tier_fails_closed_to_cold():
    """A broken warmup must NOT break detonation — it falls back to the cold JVM."""
    engine = RedTuskEngine()
    # Point warmup at a non-existent jar so it can't boot a warm JVM.
    prev = os.environ.get("REDTUSK_WORKER_JAR")
    try:
        os.environ["REDTUSK_WORKER_JAR"] = "/nonexistent/redtusk-worker.jar"
        engine.warmup()
        assert engine._warm is None, "warmup should fail-soft with no warm JVM"
    finally:
        if prev is not None:
            os.environ["REDTUSK_WORKER_JAR"] = prev
        else:
            os.environ.pop("REDTUSK_WORKER_JAR", None)
    # With a valid jar restored, detonate falls back to a fresh cold JVM and works.
    res = _detonate(engine)
    assert res.status == "ok"


def _tree_size(node: object) -> int:
    if not hasattr(node, "children"):
        return 1
    return 1 + sum(_tree_size(c) for c in getattr(node, "children", []) or [])
