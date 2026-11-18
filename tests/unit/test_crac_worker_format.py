"""A CRaC checkpoint is restored only when its worker writes the output format this engine reads.

A restore resumes the JVM (and the worker jar) that was checkpointed at image-build time, so
an image baked before the engine output contract (#64) restores a worker that writes the old
rmeta layout while this engine parses the new one. The checkpoint image therefore records
the format its own jar writes (``redtusk-worker --worker-format``), and the engine refuses a
checkpoint whose record is missing or differs, falling back to a cold JVM.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from redtusk import engine as eng

REPO = Path(__file__).resolve().parents[2]
DOCKER = REPO / "deploy" / "docker"
JAVA_FORMAT = REPO / "worker_jvm/src/main/java/io/redtusk/worker/WorkerFormat.java"


def _checkpoint(tmp_path: Path, fmt: str | None) -> Path:
    ckpt = tmp_path / "ckpt"
    ckpt.mkdir()
    (ckpt / "core.img").write_bytes(b"x")
    (ckpt / eng._CRAC_BASE64_OFF_MARKER).touch()
    if fmt is not None:
        (ckpt / eng._CRAC_WORKER_FORMAT_MARKER).write_text(fmt)
    return ckpt


def test_java_and_python_agree_on_the_worker_format() -> None:
    m = re.search(r"static final int VERSION\s*=\s*(\d+)\s*;", JAVA_FORMAT.read_text())
    assert m, "WorkerFormat.VERSION not found"
    assert int(m.group(1)) == eng._WORKER_FORMAT


@pytest.mark.parametrize("fmt", [None, "", "1", "garbage", str(eng._WORKER_FORMAT + 1)])
def test_restore_refuses_a_checkpoint_from_another_worker_format(
    fmt: str | None, tmp_path: Path
) -> None:
    ckpt = _checkpoint(tmp_path, fmt)
    scratch = tmp_path / "scr"
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    with pytest.raises(RuntimeError, match=eng._CRAC_WORKER_FORMAT_MARKER):
        eng._crac_restore_worker(
            inp, tmp_path / "rmeta", checkpoint_dir=str(ckpt), scratch_dir=str(scratch),
            timeout=5,
        )
    assert not scratch.exists(), "nothing may be staged for a refused checkpoint"


def test_restore_accepts_the_current_worker_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ckpt = _checkpoint(tmp_path, f"{eng._WORKER_FORMAT}\n")
    launched: list[object] = []

    class _LaunchedError(Exception):
        pass

    def fake_run(*a: object, **_k: object) -> None:
        launched.append(a)
        raise _LaunchedError

    monkeypatch.setattr(subprocess, "run", fake_run)
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    with pytest.raises(_LaunchedError):
        eng._crac_restore_worker(
            inp, tmp_path / "rmeta", checkpoint_dir=str(ckpt),
            scratch_dir=str(tmp_path / "scr"), timeout=5,
        )
    assert launched


def test_stale_format_checkpoint_falls_back_to_a_cold_jvm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ckpt = _checkpoint(tmp_path, None)  # a pre-#64 image: Base64 marker, no format record
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    calls: list[str] = []
    restores: list[object] = []
    monkeypatch.setenv("REDTUSK_CRAC_CHECKPOINT", str(ckpt))
    monkeypatch.setenv("REDTUSK_CRAC_SCRATCH", str(tmp_path / "scr"))
    monkeypatch.setattr(eng, "_run_worker", lambda i, r, *, timeout: calls.append("cold"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: restores.append(a))
    eng.RedTuskEngine()._produce_rmeta(inp, tmp_path / "rmeta", 5.0)
    assert restores == [], "a checkpoint from another worker format must never be restored"
    assert calls == ["cold"]


def test_crac_worker_image_records_the_format_of_the_jar_it_checkpointed() -> None:
    text = (DOCKER / "Dockerfile.crac-worker").read_text()
    run = next(
        block for block in re.split(r"\n(?=[A-Z]+ )", text)
        if block.startswith("RUN ") and "CRaCCheckpointTo" in block
    )
    marker = f"/app/checkpoint/{eng._CRAC_WORKER_FORMAT_MARKER}"
    assert marker in run
    # written by the checkpointed jar itself, and only once the checkpoint exists
    jar_writes_marker = r"-jar /app/redtusk-worker\.jar --worker-format\s*>\s*" + re.escape(marker)
    assert re.search(jar_writes_marker, run)
    assert run.index("test -s /app/checkpoint/core.img") < run.index(marker)
