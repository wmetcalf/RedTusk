"""Unit tests for DockerWorkerRuntime."""
from __future__ import annotations

import json
import os
import stat
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

    # job.json under control/
    job_bytes = (tmp_path / "control" / "job.json").read_bytes()
    job_json = json.loads(job_bytes)
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
    # The worker image uses JDK 25's AOT cache (AppCDS successor); both
    # mechanisms are surfaced under the same appcds=True flag for UI parity.
    assert job_json["appcds"] is True
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


# ---------------------------------------------------------------------------
# 10. create_scratch dirs are 0o770, NOT world-writable (finding 3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_scratch_dirs_are_not_world_writable(
    tmp_path: Path, mock_docker: DockerRuntime, limits: Limits
) -> None:
    rt = DockerWorkerRuntime(docker=mock_docker, limits=limits, image="redtusk:dev")
    slot_id = uuid4()
    result = await rt.create_scratch(slot_id)
    for sub in (result, result / "in", result / "out", result / "control"):
        mode = stat.S_IMODE(os.stat(sub).st_mode)
        assert mode == 0o770, f"{sub} has mode {oct(mode)}, expected 0o770"
        # Explicitly: no world (other) bits set.
        assert not (mode & 0o007), f"{sub} is world-accessible: {oct(mode)}"


# ---------------------------------------------------------------------------
# 11. spawn rejects worker_runtime='firecracker' on the Docker backend (finding 2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_spawn_rejects_firecracker_runtime_on_docker_backend(
    tmp_path: Path, mock_docker: DockerRuntime
) -> None:
    """worker_runtime='firecracker' must not reach the Docker argv builder —
    it routes to FirecrackerWorkerRuntime. If it leaks to DockerWorkerRuntime
    (deployment wiring bug), spawn raises a clear WorkerError instead of a
    generic per-spawn ValueError from build_run_argv."""
    from redtusk.errors import WorkerError

    fc_limits = Limits(scratch_root=str(tmp_path), worker_runtime="firecracker")
    rt = DockerWorkerRuntime(docker=mock_docker, limits=fc_limits, image="redtusk:dev")
    slot = make_slot(tmp_path)
    (tmp_path / "in").mkdir(parents=True, exist_ok=True)
    (tmp_path / "out").mkdir(parents=True, exist_ok=True)

    with pytest.raises(WorkerError, match="firecracker"):
        await rt.spawn(slot, fc_limits, "default")
    mock_docker.run.assert_not_awaited()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# FC argv seccomp invariant — the VMM's confinement in compose mode is
# firecracker's *built-in* seccomp filter, which is on unless we disable it.
# Lock in that we never do. (See _fc_base_argv's docstring + the privsep doc.)
# ---------------------------------------------------------------------------


def test_fc_argv_seccomp() -> None:
    from redtusk.worker_runtime import _fc_base_argv

    argv = _fc_base_argv("/opt/kata/bin/firecracker", "/scratch/0/fc-config.json")

    assert argv[0] == "/opt/kata/bin/firecracker"
    assert "--no-api" in argv
    assert argv[argv.index("--config-file") + 1] == "/scratch/0/fc-config.json"
    # The built-in BPF filter must never be turned off or swapped out.
    for forbidden in ("--no-seccomp", "--seccomp-filter", "--seccomp-level"):
        assert forbidden not in argv, f"{forbidden} disables firecracker's built-in seccomp"


# ---------------------------------------------------------------------------
# Jailer (bare-metal Mode B) — pure builders. The full job round-trip is
# operator-validated on an FC host; here we lock the wiring: chroot-relative
# config, jailer argv shape, chroot path convention, seccomp invariant carried.
# ---------------------------------------------------------------------------


def test_build_fc_config_bare_uses_absolute_paths() -> None:
    from redtusk.worker_runtime import _build_fc_config

    cfg = _build_fc_config(
        "/var/lib/redtusk/firecracker/vmlinux",
        "/var/lib/redtusk/firecracker/rootfs-vsock.ext4",
        "/scratch/0/outdisk.ext4",
        "/scratch/0/vsock.sock",
        10001, 1, 1024,
    )
    assert cfg["boot-source"]["kernel_image_path"] == "/var/lib/redtusk/firecracker/vmlinux"
    assert cfg["drives"][0]["path_on_host"].endswith("rootfs-vsock.ext4")
    assert cfg["drives"][0]["is_root_device"] is True
    assert cfg["drives"][1]["path_on_host"] == "/scratch/0/outdisk.ext4"
    assert cfg["vsock"]["uds_path"] == "/scratch/0/vsock.sock"
    assert cfg["machine-config"] == {"vcpu_count": 1, "mem_size_mib": 1024, "smt": False}
    assert "redtusk.vsock_port=10001" in cfg["boot-source"]["boot_args"]


def test_build_fc_config_jail_uses_chroot_relative_paths() -> None:
    from redtusk.worker_runtime import (
        _JAIL_KERNEL,
        _JAIL_OUTDISK,
        _JAIL_ROOTFS,
        _JAIL_VSOCK,
        _build_fc_config,
    )

    cfg = _build_fc_config(
        _JAIL_KERNEL, _JAIL_ROOTFS, _JAIL_OUTDISK, _JAIL_VSOCK, 10001, 1, 1024,
    )
    # Inside the chroot firecracker sees plain top-level paths.
    assert cfg["boot-source"]["kernel_image_path"] == "/vmlinux"
    assert cfg["drives"][0]["path_on_host"] == "/rootfs.ext4"
    assert cfg["drives"][1]["path_on_host"] == "/outdisk.ext4"
    assert cfg["vsock"]["uds_path"] == "/vsock.sock"


def test_jail_root_matches_jailer_convention() -> None:
    from redtusk.worker_runtime import _jail_base, _jail_root

    slot_dir = Path("/scratch/abc")
    # jailer lays the chroot at <chroot_base>/<exec_basename>/<id>/root.
    assert _jail_base(slot_dir) == Path("/scratch/abc/jail")
    assert _jail_root(slot_dir, "sid-1") == Path("/scratch/abc/jail/firecracker/sid-1/root")


def test_jailer_argv_shape_and_seccomp_invariant() -> None:
    from redtusk.worker_runtime import _jailer_argv

    argv = _jailer_argv(
        "/opt/kata/bin/jailer", "/opt/kata/bin/firecracker", "sid-1",
        Path("/scratch/abc/jail"), 10001, 10001,
    )
    assert argv[0] == "/opt/kata/bin/jailer"
    # required jailer args
    for flag, val in (("--id", "sid-1"), ("--uid", "10001"), ("--gid", "10001"),
                      ("--exec-file", "/opt/kata/bin/firecracker"),
                      ("--chroot-base-dir", "/scratch/abc/jail"),
                      ("--cgroup-version", "2")):
        assert argv[argv.index(flag) + 1] == val
    # everything after `--` is the firecracker argv (chroot-relative config)
    sep = argv.index("--")
    fc_args = argv[sep + 1:]
    assert fc_args == ["--no-api", "--config-file", "/fc.json"]
    # the seccomp invariant must hold in the jailed path too
    for forbidden in ("--no-seccomp", "--seccomp-filter", "--seccomp-level"):
        assert forbidden not in argv
