"""DockerRuntime: async wrapper around the Docker CLI for RedTusk dispatcher."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

from redtusk.errors import DispatchError
from redtusk.observability.logging import get_logger

_logger = get_logger(__name__)


@dataclass
class DockerRuntime:
    """Thin async wrapper around the ``docker`` CLI.

    Attributes:
        runtime: The OCI runtime to use — ``"runsc"`` (gVisor) or ``"runc"``.
    """

    runtime: str

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    async def detect(cls) -> DockerRuntime:
        """Probe Docker for runsc support, fall back to runc.

        Runs ``docker info --format '{{json .Runtimes}}'`` and inspects the
        JSON object returned.  If ``"runsc"`` is a key in that object the
        gVisor runtime is available; otherwise ``"runc"`` is used.

        Raises:
            DispatchError: If ``docker`` is not found on PATH or exits
                non-zero (i.e. Docker daemon is not reachable).
        """
        cmd = ["docker", "info", "--format", "{{json .Runtimes}}"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise DispatchError("docker not found") from exc

        stdout, stderr = await proc.communicate()
        stderr_text = stderr.decode(errors="replace").strip()
        if stderr_text:
            _logger.debug("docker.stderr", stderr=stderr_text, cmd=cmd[0])

        if proc.returncode != 0:
            raise DispatchError("docker daemon unreachable")

        try:
            runtimes: dict[str, object] = json.loads(stdout.decode())
        except (json.JSONDecodeError, ValueError):
            runtimes = {}

        chosen = "runsc" if "runsc" in runtimes else "runc"
        return cls(runtime=chosen)

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    async def run(self, argv: list[str]) -> str:
        """Run *argv* (a complete ``docker run`` command). Return the container ID.

        Args:
            argv: Full command list; ``argv[0]`` must be ``"docker"``.

        Returns:
            Stripped container ID string from stdout.

        Raises:
            DispatchError: On non-zero exit code.
        """
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        stderr_text = stderr.decode(errors="replace").strip()
        if stderr_text:
            _logger.debug("docker.stderr", stderr=stderr_text, cmd=argv[0])

        if proc.returncode != 0:
            raise DispatchError(
                f"docker run failed (exit {proc.returncode}): {stderr_text}"
            )

        return stdout.decode().strip()

    async def kill(self, container_id: str, signal: str = "SIGKILL") -> None:
        """Send *signal* to *container_id* via ``docker kill``.

        Non-zero exits are silently ignored (the container may already be dead).
        """
        argv = ["docker", "kill", f"--signal={signal}", container_id]
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            stderr_text = stderr.decode(errors="replace").strip()
            if stderr_text:
                _logger.debug("docker.stderr", stderr=stderr_text, cmd=argv[0])
        except Exception as exc:  # noqa: BLE001
            _logger.debug("docker.kill_ignored", error=str(exc), container_id=container_id)

    async def rm(self, container_id: str) -> None:
        """Force-remove *container_id* via ``docker rm -f``.

        All non-zero exits (including "No such container") are silently ignored.
        """
        argv = ["docker", "rm", "-f", container_id]
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            stderr_text = stderr.decode(errors="replace").strip()
            if stderr_text:
                _logger.debug("docker.stderr", stderr=stderr_text, cmd=argv[0])
        except Exception as exc:  # noqa: BLE001
            _logger.debug("docker.rm_ignored", error=str(exc), container_id=container_id)

    async def is_running(self, container_id: str) -> bool:
        """Return True iff *container_id* exists and is in the running state."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "inspect", "--format", "{{.State.Running}}", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip() == "true"
        except Exception:  # noqa: BLE001
            return False

    async def wait(self, container_id: str) -> int:
        """Block until *container_id* exits and return its exit code.

        Parses the first line of ``docker wait`` stdout as an integer.
        """
        argv = ["docker", "wait", container_id]
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        stderr_text = stderr.decode(errors="replace").strip()
        if stderr_text:
            _logger.debug("docker.stderr", stderr=stderr_text, cmd=argv[0])

        lines = stdout.decode().splitlines()
        if not lines:
            raise DispatchError("docker wait returned empty output")
        try:
            return int(lines[0].strip())
        except ValueError as exc:
            raise DispatchError(f"docker wait returned non-integer: {lines[0]!r}") from exc
