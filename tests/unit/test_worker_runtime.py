"""Unit tests for DockerWorkerRuntime."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from redtusk.limits import Limits
from redtusk.runtime.docker_runtime import DockerRuntime
from redtusk.types import JobRecord, JobState, Slot, SlotState
from redtusk.worker_runtime import DockerWorkerRuntime

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_docker() -> DockerRuntime:
    docker = MagicMock(spec=DockerRuntime)
    docker.runtime = "runc"
    docker.run = AsyncMock(return_value="container-abc")
    docker.wait = AsyncMock(return_value=0)
    docker.kill = AsyncMock()
    docker.rm = AsyncMock()
    return docker  # type: ignore[return-value]


@pytest.fixture
def limits(tmp_path: Path) -> Limits:
    return Limits(scratch_root=str(tmp_path))


def make_slot(scratch_dir: Path, container_id: str = "container-abc") -> Slot:
    return Slot(
        id=uuid4(),
        state=SlotState.ASSIGNED,
        container_id=container_id,
        scratch_dir=scratch_dir,
        assigned_job_id="job-1",
        assigned_at=datetime.now(tz=UTC),
        spawn_attempts=0,
        is_burst=False,
    )


def make_job(filename_hint: str = "test.docx", input_sha256: str = "abc123") -> JobRecord:
    return JobRecord(
        id="job-1",
        state=JobState.RUNNING,
        submitted_at=datetime.now(tz=UTC),
        started_at=datetime.now(tz=UTC),
        completed_at=None,
        input_sha256=input_sha256,
        input_size_bytes=1024,
        filename_hint=filename_hint,
        result=None,
        error_code=None,
        error_detail=None,
    )


# ---------------------------------------------------------------------------
# 1. create_scratch creates slot_id/in and slot_id/out
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_scratch_creates_directories(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot_id = uuid4()
    result = await rt.create_scratch(slot_id)

    assert result == tmp_path / str(slot_id)
    assert (tmp_path / str(slot_id) / "in").is_dir()
    assert (tmp_path / str(slot_id) / "out").is_dir()


# ---------------------------------------------------------------------------
# 2. spawn calls docker.run with --detach (no --rm: docker wait needs the container to linger)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_spawn_calls_docker_run(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot = make_slot(tmp_path)
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)
    (tmp_path / "out").mkdir(parents=True, exist_ok=True)

    container_id = await rt.spawn(slot, limits, "default")

    assert container_id == "container-abc"
    mock_docker.run.assert_awaited_once()  # type: ignore[attr-defined]
    called_argv = mock_docker.run.call_args[0][0]  # type: ignore[attr-defined]
    assert called_argv[0] == "docker"
    assert "--detach" in called_argv
    assert "--rm" not in called_argv  # removed: auto-remove races with docker wait


# ---------------------------------------------------------------------------
# 3. poll_fifo returns True when fifo file exists within timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_fifo_returns_true_when_fifo_exists(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)
    (tmp_path / "control").mkdir(parents=True, exist_ok=True)
    # Java creates control.ready (regular file) — works through gVisor 9p unlike named pipes
    ready = tmp_path / "control" / "control.ready"
    ready.write_bytes(b"")

    slot = make_slot(tmp_path)
    result = await rt.poll_fifo(slot, timeout=2.0)

    assert result is True


# ---------------------------------------------------------------------------
# 4. poll_fifo returns False when timeout elapses without fifo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_fifo_returns_false_on_timeout(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)
    # No FIFO created

    slot = make_slot(tmp_path)
    result = await rt.poll_fifo(slot, timeout=0.3)

    assert result is False


# ---------------------------------------------------------------------------
# 5. signal_job writes job.json and creates control.go (file-based IPC, gVisor-compatible)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signal_job_writes_job_json(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot = make_slot(tmp_path)
    job = make_job(filename_hint="test.docx", input_sha256="deadbeef")
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)

    (tmp_path / "control").mkdir(parents=True, exist_ok=True)
    await rt.signal_job(slot, job, limits)

    # control.go is created (file-based signal, no FIFO)
    assert (tmp_path / "control" / "control.go").exists()

    job_json = json.loads((tmp_path / "control" / "job.json").read_bytes())  # job.json at scratch root
    assert job_json["sha256"] == "deadbeef"
    assert job_json["limits"]["max_recursion_depth"] == limits.max_recursion_depth
    assert job_json["limits"]["max_embedded_entries"] == limits.max_embedded_entries
    assert job_json["limits"]["max_extracted_bytes"] == limits.max_extracted_bytes
    assert job_json["limits"]["ocr_timeout_s"] == limits.ocr_timeout_s
    assert "input_path" in job_json
    assert job_json["input_path"] == "/in/test.docx"
    assert job_json["output_dir"] == "/out"
    assert job_json["filename_hint"] == "test.docx"
    assert job_json["enable_qr"] == limits.enable_qr
    assert job_json["enable_ocr"] == limits.enable_ocr
    assert job_json["ocr_lang"] == limits.ocr_lang
    assert job_json["ocr_psm"] == limits.ocr_psm
    assert job_json["sandbox_profile"] == limits.profile
    assert job_json["sandbox_runtime"] == "runc"
    # AppCDS is intentionally disabled in Dockerfile.default — JDK 25
    # rejects the shared archive on a flag-value mismatch we can't fix
    # at dump time. See the Dockerfile comment for full root cause.
    assert job_json["appcds"] is False
    assert "redtusk_version" in job_json


@pytest.mark.asyncio
async def test_signal_job_reports_effective_runtime_override(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    overridden_limits = Limits(scratch_root=str(tmp_path), worker_runtime="runsc")
    rt = DockerWorkerRuntime(docker=mock_docker, limits=overridden_limits, image="redtusk:dev")
    slot = make_slot(tmp_path)
    job = make_job(filename_hint="test.docx", input_sha256="deadbeef")
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)

    (tmp_path / "control").mkdir(parents=True, exist_ok=True)
    await rt.signal_job(slot, job, overridden_limits)

    job_json = json.loads((tmp_path / "control" / "job.json").read_bytes())
    assert job_json["sandbox_runtime"] == "runsc"


# ---------------------------------------------------------------------------
# 6. wait returns exit code from docker.wait
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wait_returns_exit_code(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    mock_docker.wait = AsyncMock(return_value=42)  # type: ignore[attr-defined]
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot = make_slot(tmp_path, container_id="container-xyz")

    exit_code = await rt.wait(slot, timeout=30.0)

    assert exit_code == 42
    mock_docker.wait.assert_awaited_once_with("container-xyz")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 7. wait calls docker.kill and returns 137 on timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wait_kills_and_returns_137_on_timeout(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    import asyncio

    async def _slow_wait(container_id: str) -> int:
        await asyncio.Event().wait()  # never fires
        return 0

    mock_docker.wait = AsyncMock(side_effect=_slow_wait)  # type: ignore[attr-defined]
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot = make_slot(tmp_path, container_id="container-timeout")

    exit_code = await rt.wait(slot, timeout=0.05)

    assert exit_code == 137
    mock_docker.kill.assert_awaited_once_with("container-timeout")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 8. reap calls docker.rm and removes scratch directory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reap_removes_container_and_scratch(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    slot = make_slot(scratch, container_id="container-rm")

    await rt.reap(slot)

    mock_docker.rm.assert_awaited_once_with("container-rm")  # type: ignore[attr-defined]
    assert not scratch.exists()


# ---------------------------------------------------------------------------
# 9. signal_job creates control.go file to trigger worker (file-based IPC)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signal_job_creates_control_go(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot = make_slot(tmp_path)
    job = make_job(filename_hint="test.docx", input_sha256="deadbeef")
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)
    (tmp_path / "control").mkdir(parents=True, exist_ok=True)

    assert not (tmp_path / "control" / "control.go").exists()
    await rt.signal_job(slot, job, limits)
    # control.go must exist so Java's polling loop detects it
    assert (tmp_path / "control" / "control.go").exists()
