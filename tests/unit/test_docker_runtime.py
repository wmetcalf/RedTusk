"""Unit tests for redtusk.runtime.docker_runtime.DockerRuntime."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from redtusk.errors import DispatchError
from redtusk.runtime.docker_runtime import DockerRuntime

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> AsyncMock:
    """Return a mock subprocess process object."""
    mock_proc = AsyncMock()
    mock_proc.returncode = returncode
    mock_proc.communicate.return_value = (stdout, stderr)
    return mock_proc


# ---------------------------------------------------------------------------
# 1. detect() → "runsc" when docker info output contains {"runsc": {...}}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_returns_runsc_when_present() -> None:
    runtimes_json = json.dumps(
        {"runsc": {"path": "/usr/bin/runsc"}, "runc": {"path": "/usr/bin/runc"}}
    )
    mock_proc = _make_proc(stdout=runtimes_json.encode())

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await DockerRuntime.detect()

    assert result.runtime == "runsc"


# ---------------------------------------------------------------------------
# 2. detect() → "runc" when docker info output does not contain "runsc"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_returns_runc_when_runsc_absent() -> None:
    runtimes_json = json.dumps({"runc": {"path": "/usr/bin/runc"}})
    mock_proc = _make_proc(stdout=runtimes_json.encode())

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await DockerRuntime.detect()

    assert result.runtime == "runc"


# ---------------------------------------------------------------------------
# 3. detect() raises DispatchError when docker binary not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_raises_dispatch_error_when_docker_not_found() -> None:
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("docker not found")):
        with pytest.raises(DispatchError, match="docker not found"):
            await DockerRuntime.detect()


# ---------------------------------------------------------------------------
# 4. run() returns stripped container ID from stdout on success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_returns_stripped_container_id() -> None:
    container_id = "container-id-abc"
    mock_proc = _make_proc(stdout=f"{container_id}\n".encode())

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        result = await rt.run(["docker", "run", "--rm", "some-image"])

    assert result == container_id


# ---------------------------------------------------------------------------
# 5. run() raises DispatchError on non-zero return code
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_raises_dispatch_error_on_nonzero_exit() -> None:
    mock_proc = _make_proc(returncode=1, stderr=b"container failed to start")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        with pytest.raises(DispatchError, match="docker run failed"):
            await rt.run(["docker", "run", "--rm", "some-image"])


# ---------------------------------------------------------------------------
# 6. kill() does not raise when docker kill returns non-zero
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_kill_does_not_raise_on_nonzero_exit() -> None:
    mock_proc = _make_proc(returncode=1, stderr=b"No such container: abc123")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        # Must not raise
        await rt.kill("abc123")


# ---------------------------------------------------------------------------
# 7. rm() does not raise on any non-zero exit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rm_does_not_raise_on_nonzero_exit() -> None:
    mock_proc = _make_proc(returncode=1, stderr=b"No such container: abc123")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        # Must not raise
        await rt.rm("abc123")


# ---------------------------------------------------------------------------
# 8. wait() returns the integer exit code parsed from stdout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wait_returns_integer_exit_code() -> None:
    mock_proc = _make_proc(stdout=b"42\n")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        exit_code = await rt.wait("abc123")

    assert exit_code == 42


# ---------------------------------------------------------------------------
# 9. wait() raises DispatchError on empty output
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wait_raises_on_empty_output() -> None:
    mock_proc = _make_proc(stdout=b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        rt = DockerRuntime(runtime="runc")
        with pytest.raises(DispatchError, match="docker wait returned empty output"):
            await rt.wait("abc123")


# ---------------------------------------------------------------------------
# 10. detect() raises DispatchError with distinct message when daemon unreachable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_raises_dispatch_error_when_daemon_unreachable() -> None:
    mock_proc = _make_proc(returncode=1, stderr=b"Cannot connect to the Docker daemon")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(DispatchError, match="docker daemon unreachable"):
            await DockerRuntime.detect()
