"""WorkerRuntime protocol — contract for spawning/signaling/reaping worker containers."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import UUID

from redtusk._version import __version__
from redtusk.errors import WorkerError
from redtusk.sandbox.container import _vsock_port_for_slot
from redtusk.sandbox.vsock_server import VsockSlotServer
from redtusk.observability.logging import get_logger
from redtusk.runtime.docker_runtime import DockerRuntime

if TYPE_CHECKING:
    from redtusk.limits import Limits
    from redtusk.types import JobRecord, Slot

_logger = get_logger(__name__)

TIMEOUT_EXIT_CODE: int = 137


@runtime_checkable
class WorkerRuntime(Protocol):
    """Interface for spawning, signaling, and reaping one-shot worker containers.

    DockerWorkerRuntime (in this same module) is the concrete implementation.
    Tests use AsyncMock.
    """

    async def create_scratch(self, slot_id: UUID) -> Path:
        """Create scratch_dir/{slot_id}/in and /out. Return scratch_dir/{slot_id}."""
        ...

    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        """Spawn a worker container. Return container_id."""
        ...

    async def poll_fifo(self, slot: Slot, timeout: float) -> bool:  # noqa: ASYNC109
        """Poll for control.fifo until timeout. Return True if found."""
        ...

    async def signal_job(self, slot: Slot, job: JobRecord, limits: Limits) -> None:
        """Write job.json and send 'go\\n' to the FIFO."""
        ...

    async def receive_result(self, slot: Slot) -> None:
        """microvm profile only: drain RESULT + ARTIFACT frames from the
        slot's vsock socket into ``<scratch>/out``. No-op for file-IPC
        profiles (artifacts already on bind-mounted /out). Must be called
        BEFORE :meth:`wait` because the worker closes its socket after
        sending DONE and only THEN exits."""
        ...

    async def wait(self, slot: Slot, timeout: float) -> int:  # noqa: ASYNC109
        """Wait for container exit. Return exit code. 137 means killed."""
        ...

    async def reap(self, slot: Slot) -> None:
        """docker rm + remove scratch dir."""
        ...

    async def is_container_running(self, slot: Slot) -> bool:
        """Return True iff the slot's container is still in the running state."""
        ...


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _rmtree(p: Path) -> None:
    import shutil
    shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------------------
# DockerWorkerRuntime
# ---------------------------------------------------------------------------


@dataclass
class DockerWorkerRuntime:
    """Concrete WorkerRuntime backed by Docker CLI and filesystem."""

    docker: DockerRuntime
    limits: Limits
    image: str                        # worker Docker image name
    _scratch_root: Path = field(init=False)
    _effective_runtime_by_slot: dict[UUID, str] = field(default_factory=dict, init=False)
    # microvm profile: per-slot host-side vsock listener. Keyed by slot UUID;
    # populated in spawn() and torn down in reap(). For file-IPC profiles this
    # dict stays empty and the existing scratch-dir code path runs unchanged.
    _vsock_servers: dict[UUID, "VsockSlotServer"] = field(default_factory=dict, init=False)
    # Tracks which profile each slot was spawned with so subsequent methods
    # (poll_fifo, signal_job, reap) can branch correctly without re-deriving
    # from limits (which may have changed).
    _profile_by_slot: dict[UUID, str] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._scratch_root = Path(self.limits.scratch_root)

    async def create_scratch(self, slot_id: UUID) -> Path:
        slot_dir = self._scratch_root / str(slot_id)
        await asyncio.to_thread(_mkdir, slot_dir / "in")
        await asyncio.to_thread(_mkdir, slot_dir / "out")
        await asyncio.to_thread(_mkdir, slot_dir / "control")
        # chmod 0o777 so container UID 10001 can write to out/
        await asyncio.to_thread(os.chmod, slot_dir, 0o777)
        await asyncio.to_thread(os.chmod, slot_dir / "in", 0o777)
        await asyncio.to_thread(os.chmod, slot_dir / "out", 0o777)
        await asyncio.to_thread(os.chmod, slot_dir / "control", 0o777)
        return slot_dir

    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        from redtusk.sandbox.container import build_run_argv
        # Limits.worker_runtime overrides auto-detected runtime (useful when runsc/gVisor
        # is available but its 9p filesystem cannot propagate FIFOs to the host).
        effective_runtime = limits.worker_runtime or self.docker.runtime
        self._effective_runtime_by_slot[slot.id] = effective_runtime
        self._profile_by_slot[slot.id] = profile

        # microvm profile: bind a per-slot vsock listener BEFORE the worker
        # starts, so the worker's VsockIpcChannel.connect-with-retry has a
        # listener to dial into. The server stays bound through this slot's
        # entire lifecycle; cleanup happens in reap().
        if profile == "microvm":
            port = _vsock_port_for_slot(str(slot.id))
            server = VsockSlotServer(port=port,
                                     ready_timeout_s=float(limits.worker_warmup_timeout_s),
                                     recv_timeout_s=float(limits.job_timeout_s))
            await asyncio.to_thread(server.bind)
            self._vsock_servers[slot.id] = server

        argv = build_run_argv(
            runtime=effective_runtime,
            profile=profile,
            image=self.image,
            limits=limits,
            scratch_dir=slot.scratch_dir,
            container_name=str(slot.id),
        )
        return await self.docker.run(argv)

    async def poll_fifo(self, slot: Slot, timeout: float) -> bool:  # noqa: ASYNC109
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")

        # microvm profile: "ready" means "worker connected to vsock + sent READY".
        # accept_ready blocks synchronously; run it in a thread so the event
        # loop stays responsive. Treat a socket timeout as a polling failure
        # (returns False) so the pool can retry as usual.
        server = self._vsock_servers.get(slot.id)
        if server is not None:
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(server.accept_ready),
                    timeout=timeout,
                )
                return True
            except (TimeoutError, OSError):
                return False

        # File-IPC profiles: poll for control.ready (regular file). Works with
        # gVisor/9p unlike named pipes. Java creates this file after warmup.
        ready_path = Path(slot.scratch_dir) / "control" / "control.ready"
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            exists = await asyncio.to_thread(ready_path.exists)
            if exists:
                return True
            await asyncio.sleep(0.25)
        return False

    async def signal_job(self, slot: Slot, job: JobRecord, limits: Limits) -> None:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        scratch_dir = Path(slot.scratch_dir)
        effective_runtime = (
            limits.worker_runtime
            or self._effective_runtime_by_slot.get(slot.id)
            or self.docker.runtime
        )

        # 1. Write job.json
        job_dict = {
            "input_path": f"/in/{job.filename_hint or 'input'}",
            "output_dir": "/out",
            "sha256": job.input_sha256,
            "filename_hint": job.filename_hint,
            "limits": {
                "max_recursion_depth": limits.max_recursion_depth,
                "max_embedded_entries": limits.max_embedded_entries,
                "max_extracted_bytes": limits.max_extracted_bytes,
                "ocr_timeout_s": limits.ocr_timeout_s,
            },
            "enable_qr": limits.enable_qr,
            "enable_ocr": limits.enable_ocr,
            "enable_thumbnails": limits.enable_thumbnails,
            "ocr_lang": limits.ocr_lang,
            "ocr_psm": limits.ocr_psm,
            "sandbox_profile": limits.profile,
            "sandbox_runtime": effective_runtime,
            # The image uses JDK 25's AOT cache (the successor to AppCDS) —
            # see deploy/docker/Dockerfile.default for the dump/runtime args.
            # We report this as appcds=True for UI label compatibility; both
            # mechanisms produce the same class-data pre-loading effect.
            "appcds": True,
            "ksm": not limits.disable_ksm,
            "crac": limits.profile == "high-density",
            "redtusk_version": __version__,
            "zxing_path":      "/usr/local/bin/ZXingReader",
            "tesseract_path":  "tesseract",
            "ocr_max_image_dim": limits.ocr_max_image_dim,
            "ocr_skip_blank":    limits.ocr_skip_blank,
        }
        # microvm profile: ship the descriptor + input bytes over the
        # already-connected vsock socket instead of writing files. The worker's
        # VsockIpcChannel.receiveJob reads JOB+INPUT and gives Main.processJob
        # a descriptor with locally-resolved tmpfs paths. No host-side
        # filesystem touch from this dispatcher → no virtio-fs needed.
        server = self._vsock_servers.get(slot.id)
        if server is not None:
            input_path = job.input_path
            if input_path is None:
                raise WorkerError(
                    f"microvm slot {slot.id}: job has no input_path on host"
                )
            input_bytes = await asyncio.to_thread(Path(input_path).read_bytes)
            await asyncio.to_thread(server.send_go)
            await asyncio.to_thread(server.send_job, job_dict, input_bytes)
            return

        job_json = json.dumps(job_dict, ensure_ascii=False).encode()
        # job.json goes in scratch root (mapped to /scratch/job.json in container)
        job_path = scratch_dir / "control" / "job.json"
        await asyncio.to_thread(job_path.write_bytes, job_json)

        # 2. Signal the worker by creating control.go (regular file).
        # Java polls for this file at 100 ms intervals — works with gVisor/9p, no FIFO needed.
        go_path = scratch_dir / "control" / "control.go"
        await asyncio.to_thread(go_path.touch)

    async def receive_result(self, slot: Slot) -> None:
        """For microvm profile: drain the vsock stream into the slot's scratch
        ``out`` directory so the dispatcher's existing _ingest_result code
        (which reads metadata.json + artifacts from {scratch_dir}/out/) works
        unchanged. For file-IPC profiles this is a no-op — outputs are
        already on the bind-mounted /out.

        Must be called BEFORE :meth:`wait` because the worker sends DONE
        and only THEN closes the socket and exits. Calling it after the
        worker exits would block forever (or fail) on a dead connection.
        """
        server = self._vsock_servers.get(slot.id)
        if server is None:
            return  # file-IPC profile — output already on disk
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir for artifacts")
        out_dir = Path(slot.scratch_dir) / "out"
        result = await asyncio.to_thread(server.receive_result, out_dir)
        # The worker wrote metadata.json bytes as the RESULT frame; persist
        # them at the canonical path the file-IPC ingest path expects.
        metadata_path = out_dir / "metadata.json"
        await asyncio.to_thread(metadata_path.write_bytes, result["metadata"])

    async def wait(self, slot: Slot, timeout: float) -> int:  # noqa: ASYNC109
        container_id = slot.container_id
        assert container_id is not None
        try:
            return await asyncio.wait_for(
                self.docker.wait(container_id),
                timeout=timeout,
            )
        except TimeoutError:
            await self.docker.kill(container_id)
            return TIMEOUT_EXIT_CODE

    async def reap(self, slot: Slot) -> None:
        if slot.container_id:
            await self.docker.rm(slot.container_id)
        # Tear down the per-slot vsock listener (if any) before deleting the
        # scratch dir. Order matters: the server's recv socket holds a fd
        # we want closed first.
        server = self._vsock_servers.pop(slot.id, None)
        if server is not None:
            await asyncio.to_thread(server.close)
        if slot.scratch_dir:
            await asyncio.to_thread(_rmtree, slot.scratch_dir)
        self._effective_runtime_by_slot.pop(slot.id, None)
        self._profile_by_slot.pop(slot.id, None)

    async def is_container_running(self, slot: Slot) -> bool:
        if not slot.container_id:
            return False
        return await self.docker.is_running(slot.container_id)
