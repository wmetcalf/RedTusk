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
from redtusk.observability.logging import get_logger
from redtusk.runtime.docker_runtime import DockerRuntime
from redtusk.sandbox.container import _vsock_port_for_slot
from redtusk.sandbox.vsock_server import VsockSlotServer

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


def _make_ext4_sync(path: Path, size_mib: int) -> None:
    """Create a sparse ext4 image (no root needed). Used as the FC per-slot
    output disk: the worker writes metadata.json + artifacts onto it, the host
    reads them back after the VM exits — keeping large output OFF the vsock
    stream (which corrupts large transfers under concurrency)."""
    import subprocess
    with open(path, "wb") as f:
        f.truncate(size_mib * 1024 * 1024)
    # no journal + 0 reserved blocks: faster mkfs, more usable space, and the
    # disk is single-use (written once in-guest, read once on the host).
    subprocess.run(
        ["mkfs.ext4", "-q", "-F", "-O", "^has_journal", "-m", "0", str(path)],
        check=True, capture_output=True,
    )


def _rdump_ext4_sync(image: Path, dest: Path, max_bytes: int) -> list[str]:
    """Extract an ext4 image's root contents to ``dest`` WITHOUT mounting
    (no root) via debugfs rdump. Returns the top-level names written.

    Defense-in-depth against a malicious worker (compromised JVM) producing
    an attacker-crafted ext4 image:
      * Refuse if ``dest`` contains whitespace — debugfs's `-R` request is
        space-tokenized and would misparse, dropping output into the wrong
        path. ``dest`` derives from ``scratch_root``/<UUID>/out so this only
        bites a misconfigured operator, but reject early either way.
      * Sanity-check the ext4 superblock magic before invoking debugfs.
        Catches obviously-corrupt images; gives a smaller surface for
        e2fsprogs CVEs to chew on (debugfs still runs as the unprivileged
        FC dispatcher user, so blast radius is bounded).
      * Cap total extracted size at ``max_bytes`` — a runaway worker could
        otherwise fill the slot dir up to the size of the output disk.
    """
    import subprocess
    dest_str = str(dest)
    if any(c.isspace() for c in dest_str):
        raise ValueError(f"rdump dest path must not contain whitespace: {dest_str!r}")
    # ext4 superblock magic 0xEF53 lives at offset 0x438 (1080) of the image.
    try:
        with open(image, "rb") as f:
            f.seek(0x438)
            magic = f.read(2)
    except OSError as exc:
        raise ValueError(f"cannot read ext4 image {image}: {exc}") from exc
    if magic != b"\x53\xef":
        raise ValueError(
            f"ext4 magic check failed on {image} (got {magic!r}); refusing to invoke debugfs"
        )

    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["debugfs", "-R", f"rdump / {dest_str}", str(image)],
        check=True, capture_output=True,
    )
    # debugfs rdump always recreates lost+found; drop it so it isn't mistaken
    # for an artifact.
    import shutil
    lf = dest / "lost+found"
    if lf.exists():
        shutil.rmtree(lf, ignore_errors=True)
    # Enforce the host-side extracted-size cap. A compromised worker that
    # ignored max_extracted_bytes guest-side could otherwise dump up to
    # fc_outdisk_mib bytes into the slot dir.
    total = 0
    for p in dest.rglob("*"):
        if p.is_file() and not p.is_symlink():
            total += p.stat().st_size
            if total > max_bytes:
                shutil.rmtree(dest, ignore_errors=True)
                dest.mkdir(parents=True, exist_ok=True)
                raise ValueError(
                    f"extracted output exceeds cap: >{max_bytes} bytes"
                )
    return [p.name for p in dest.iterdir()]


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
    _vsock_servers: dict[UUID, VsockSlotServer] = field(default_factory=dict, init=False)
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
        result = await asyncio.to_thread(
            server.receive_result, out_dir, self.limits.max_extracted_bytes
        )
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


# ---------------------------------------------------------------------------
# FirecrackerWorkerRuntime
# ---------------------------------------------------------------------------


@dataclass
class FirecrackerWorkerRuntime:
    """Concrete WorkerRuntime that runs each worker in a fresh Firecracker
    microVM, talking AF_VSOCK to a host-side :class:`VsockSlotServer`.

    Unlike :class:`DockerWorkerRuntime` this backend bypasses Docker entirely:
    each slot is a Firecracker subprocess. Per-slot lifecycle:

      1. ``create_scratch`` makes a tiny per-slot dir (just for FC config +
         vsock UDS, ~1 KiB). No /in or /out bind-mounts.
      2. ``spawn`` binds the host listener at ``<slot_dir>/vsock.sock_<port>``
         (Firecracker convention), writes the per-slot FC config JSON, and
         launches FC as a subprocess. The container_id is the PID.
      3. ``poll_fifo`` blocks until the worker connects + sends READY.
      4. ``signal_job`` sends ``GO`` + ``JOB`` + ``INPUT`` over vsock.
      5. ``receive_result`` drains ``RESULT`` + ``ARTIFACT`` frames into
         ``<slot_dir>/out`` so the dispatcher's _ingest_result is unchanged.
      6. ``wait`` waits for the FC process to exit (worker did poweroff).
      7. ``reap`` kills FC if still alive, tears down the vsock listener,
         removes the slot dir.

    Profile is ignored — FC always uses vsock IPC. The worker image
    must be the ``redtusk-worker:crac-vsock`` flavor whose CRaC
    checkpoint was taken in vsock IPC mode.
    """

    limits: Limits

    _scratch_root: Path = field(init=False)
    _vsock_servers: dict[UUID, VsockSlotServer] = field(default_factory=dict, init=False)
    _fc_procs: dict[UUID, asyncio.subprocess.Process] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._scratch_root = Path(self.limits.scratch_root)

    async def create_scratch(self, slot_id: UUID) -> Path:
        # vsock carries the control handshake + job descriptor + input bytes.
        # OUTPUT (metadata.json + artifacts) goes over a per-slot virtio-blk
        # ext4 disk instead — large vsock transfers corrupt under concurrency
        # (see fc_vcpu_count note in limits.py). /out is where the host
        # rdumps the disk into, for the dispatcher's _ingest_result.
        slot_dir = self._scratch_root / str(slot_id)
        await asyncio.to_thread(_mkdir, slot_dir / "out")
        await asyncio.to_thread(os.chmod, slot_dir, 0o777)
        await asyncio.to_thread(os.chmod, slot_dir / "out", 0o777)
        await asyncio.to_thread(
            _make_ext4_sync, slot_dir / "outdisk.ext4", self.limits.fc_outdisk_mib
        )
        return slot_dir

    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        slot_dir = Path(slot.scratch_dir)
        port = limits.fc_vsock_port

        # Bind the host listener BEFORE launching FC so the worker's
        # afterRestore-driven connect succeeds on first try.
        vsock_uds = slot_dir / "vsock.sock"          # FC owns this path
        listener_path = f"{vsock_uds}_{port}"        # we own this one
        server = VsockSlotServer(
            unix_path=listener_path,
            ready_timeout_s=float(limits.worker_warmup_timeout_s),
            recv_timeout_s=float(limits.job_timeout_s),
        )
        await asyncio.to_thread(server.bind)
        self._vsock_servers[slot.id] = server

        # FC config JSON
        fc_config = {
            "boot-source": {
                "kernel_image_path": limits.fc_kernel,
                "boot_args": (
                    "console=ttyS0 reboot=k panic=1 pci=off init=/init ro "
                    f"redtusk.vsock_port={port}"
                ),
            },
            "drives": [
                {
                    "drive_id": "rootfs",
                    "path_on_host": limits.fc_rootfs,
                    "is_root_device": True,
                    "is_read_only": True,
                },
                {
                    # Output disk (vdb): guest mounts it at /tmp/redtusk-out,
                    # worker writes results here, host rdumps it after exit.
                    "drive_id": "outdisk",
                    "path_on_host": str(slot_dir / "outdisk.ext4"),
                    "is_root_device": False,
                    "is_read_only": False,
                },
            ],
            "machine-config": {
                "vcpu_count": limits.fc_vcpu_count,
                "mem_size_mib": limits.fc_mem_mib,
                "smt": False,
            },
            "vsock": {"guest_cid": 3, "uds_path": str(vsock_uds)},
        }
        config_path = slot_dir / "fc-config.json"
        await asyncio.to_thread(
            config_path.write_text,
            json.dumps(fc_config, indent=2),
        )
        log_path = slot_dir / "fc.log"

        # Launch FC. `sudo` is needed to set up KVM unless the redtusk user
        # is in the kvm group. We document the latter and don't shell out
        # to sudo here (avoids password prompts in the dispatcher).
        proc = await asyncio.create_subprocess_exec(
            limits.fc_bin,
            "--no-api",
            "--config-file", str(config_path),
            stdout=await asyncio.to_thread(open, log_path, "w"),
            stderr=asyncio.subprocess.STDOUT,
        )
        self._fc_procs[slot.id] = proc
        return str(proc.pid)

    async def poll_fifo(self, slot: Slot, timeout: float) -> bool:  # noqa: ASYNC109
        server = self._vsock_servers.get(slot.id)
        if server is None:
            return False
        try:
            await asyncio.wait_for(
                asyncio.to_thread(server.accept_ready),
                timeout=timeout,
            )
            return True
        except (TimeoutError, OSError):
            return False

    async def signal_job(self, slot: Slot, job: JobRecord, limits: Limits) -> None:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        server = self._vsock_servers.get(slot.id)
        if server is None:
            raise WorkerError(f"slot {slot.id} has no vsock server")
        if job.input_path is None:
            raise WorkerError(f"FC slot {slot.id}: job has no input_path on host")

        # Same descriptor schema as DockerWorkerRuntime.signal_job so the
        # Java worker can't tell them apart. input_path/output_dir below are
        # PLACEHOLDERS — VsockIpcChannel.receiveJob unconditionally rewrites
        # them to /tmp/redtusk-{in,out} inside the guest. (output_dir
        # specifically backs onto the virtio-blk output disk; see init-vsock.)
        # input_path/output_dir below are placeholders; the worker rewrites them.
        job_dict = {
            "input_path": f"/in/{job.filename_hint or 'input'}",
            "output_dir": "/out",
            "sha256": job.input_sha256,
            "filename_hint": job.filename_hint,
            "limits": {
                "max_recursion_depth":  limits.max_recursion_depth,
                "max_embedded_entries": limits.max_embedded_entries,
                "max_extracted_bytes":  limits.max_extracted_bytes,
                "ocr_timeout_s":        limits.ocr_timeout_s,
            },
            "enable_qr":            limits.enable_qr,
            "enable_ocr":           limits.enable_ocr,
            "enable_thumbnails":    limits.enable_thumbnails,
            "ocr_lang":             limits.ocr_lang,
            "ocr_psm":              limits.ocr_psm,
            "sandbox_profile":      limits.profile,
            "sandbox_runtime":      "firecracker",
            "appcds":               True,
            "ksm":                  not limits.disable_ksm,
            "crac":                 True,
            "redtusk_version":      __version__,
            "zxing_path":           "/usr/local/bin/ZXingReader",
            "tesseract_path":       "tesseract",
            "ocr_max_image_dim":    limits.ocr_max_image_dim,
            "ocr_skip_blank":       limits.ocr_skip_blank,
        }
        input_bytes = await asyncio.to_thread(Path(job.input_path).read_bytes)
        await asyncio.to_thread(server.send_go)
        await asyncio.to_thread(server.send_job, job_dict, input_bytes)

    async def receive_result(self, slot: Slot) -> None:
        # Disk-output mode: nothing to receive over vsock. The worker writes
        # results to the virtio-blk disk; the DONE signal is the FC process
        # exiting (the guest powers off after the worker finishes). We read
        # the disk in wait() once the VM has exited and the guest has flushed
        # + unmounted it. Do NOT read the vsock here: the worker closes it on
        # exit, and a premature close would look like corruption and trigger a
        # spurious retry even though the output is already safe on the disk.
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} not in receivable state")

    async def wait(self, slot: Slot, timeout: float) -> int:  # noqa: ASYNC109
        proc = self._fc_procs.get(slot.id)
        if proc is None:
            return TIMEOUT_EXIT_CODE
        rc = TIMEOUT_EXIT_CODE
        try:
            rc = await asyncio.wait_for(proc.wait(), timeout=timeout)
        except TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
            rc = TIMEOUT_EXIT_CODE
        # FC has exited → the guest synced + unmounted the output disk on
        # poweroff, so the ext4 image is consistent. Read it into /out for
        # _ingest_result (and partial-salvage on non-zero exit). Best-effort.
        await self._read_outdisk(slot)
        return rc

    async def _read_outdisk(self, slot: Slot) -> None:
        if slot.scratch_dir is None:
            return
        image = Path(slot.scratch_dir) / "outdisk.ext4"
        out_dir = Path(slot.scratch_dir) / "out"
        if not image.exists():
            return
        try:
            names = await asyncio.to_thread(
                _rdump_ext4_sync, image, out_dir, self.limits.max_extracted_bytes
            )
            _logger.info("fc.outdisk_read", slot=str(slot.id), entries=len(names))
        except Exception as exc:
            _logger.warning("fc.outdisk_read_error", slot=str(slot.id), error=str(exc))

    async def reap(self, slot: Slot) -> None:
        proc = self._fc_procs.pop(slot.id, None)
        if proc is not None and proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
        server = self._vsock_servers.pop(slot.id, None)
        if server is not None:
            await asyncio.to_thread(server.close)
        if slot.scratch_dir:
            await asyncio.to_thread(_rmtree, slot.scratch_dir)

    async def is_container_running(self, slot: Slot) -> bool:
        proc = self._fc_procs.get(slot.id)
        return proc is not None and proc.returncode is None
