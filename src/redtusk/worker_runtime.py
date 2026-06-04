"""WorkerRuntime protocol — contract for spawning/signaling/reaping worker containers."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

from redtusk._version import __version__
from redtusk.errors import FcCpuFeatureMismatchError, WorkerError
from redtusk.fc_cpu_features import parse_cpu_mismatch
from redtusk.observability.logging import get_logger
from redtusk.observability.metrics import record_cpu_feature_mismatch
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


# The worker container runs as UID:GID 10001:10001 (see build_run_argv's
# --user). Scratch dirs are bind-mounted into the container and must be
# writable by that UID without being world-writable.
_WORKER_UID = 10001
_WORKER_GID = 10001


def _fc_base_argv(fc_bin: str, config_path: str) -> list[str]:
    """The firecracker argv shared by the bare-spawn and jailer paths.

    SECURITY INVARIANT — we deliberately never pass ``--no-seccomp`` (or a
    custom ``--seccomp-filter``): firecracker's **built-in** seccomp BPF filter
    is on by default and is the VMM's syscall confinement. In compose mode that
    filter — together with the dispatcher container's ``cap_drop ALL`` + non-root
    uid 10001 + read-only rootfs + no egress — IS the VMM's jail; the firecracker
    ``jailer`` (chroot/namespaces/uid-drop) is reserved for the **bare-metal**
    Mode B dispatcher, where there is no outer container to provide that
    isolation. Adding the jailer to the hardened container would require
    re-privileging it (root + CAP_SYS_ADMIN/MKNOD/CHROOT/SETUID) for no net gain.
    See ``docs/design/privsep-split-and-jailer.md``. ``test_fc_argv_seccomp``
    guards that this argv never disables the built-in filter.
    """
    return [fc_bin, "--no-api", "--config-file", config_path]


def _build_fc_config(
    kernel_path: str,
    rootfs_path: str,
    outdisk_path: str,
    vsock_uds: str,
    port: int,
    vcpu_count: int,
    mem_mib: int,
) -> dict[str, Any]:
    """The firecracker config JSON, shared by the bare-spawn and jailer paths.

    Paths are **absolute** for the bare spawn and **chroot-relative** for the
    jailer (where firecracker is chrooted into ``<jail>/root`` and sees
    ``/vmlinux`` etc.). Keeping one builder means the two paths can't drift in
    boot args / drive layout / vsock wiring.
    """
    return {
        "boot-source": {
            "kernel_image_path": kernel_path,
            "boot_args": (
                "console=ttyS0 reboot=k panic=1 pci=off init=/init ro "
                f"redtusk.vsock_port={port}"
            ),
        },
        "drives": [
            {
                "drive_id": "rootfs",
                "path_on_host": rootfs_path,
                "is_root_device": True,
                "is_read_only": True,
            },
            {
                "drive_id": "outdisk",
                "path_on_host": outdisk_path,
                "is_root_device": False,
                "is_read_only": False,
            },
        ],
        "machine-config": {
            "vcpu_count": vcpu_count,
            "mem_size_mib": mem_mib,
            "smt": False,
        },
        "vsock": {"guest_cid": 3, "uds_path": vsock_uds},
    }


# Firecracker jailer chroot layout. The jailer creates
# ``<chroot_base>/firecracker/<id>/root`` (exec basename is "firecracker"),
# chroots the VMM into it, and uid-drops. We anchor the chroot base under the
# slot's scratch dir so reap()'s rmtree(scratch_dir) cleans the whole jail
# (removing a hardlink leaves the shared rootfs/kernel inode intact). These are
# the paths firecracker sees *after* chroot — toolz2-validated: a CRaC restore
# inside this jail reaches a state byte-identical to the bare boot.
_JAIL_KERNEL = "/vmlinux"
_JAIL_ROOTFS = "/rootfs.ext4"
_JAIL_OUTDISK = "/outdisk.ext4"
_JAIL_VSOCK = "/vsock.sock"
_JAIL_CONFIG = "/fc.json"


def _jail_base(slot_dir: Path) -> Path:
    return slot_dir / "jail"


def _jail_root(slot_dir: Path, slot_id: object) -> Path:
    # MUST match the jailer's <chroot_base>/<exec_basename>/<id>/root convention.
    return _jail_base(slot_dir) / "firecracker" / str(slot_id) / "root"


def _jailer_argv(
    jailer_bin: str,
    fc_bin: str,
    slot_id: object,
    jail_base: Path,
    uid: int,
    gid: int,
) -> list[str]:
    """jailer argv that confines the VMM (chroot + cgroup v2 + uid-drop) then
    execs firecracker inside the chroot.

    **Bare-metal Mode B only** — the jailer must start as root with
    CAP_SYS_CHROOT/MKNOD/SETUID, so it is never used inside the hardened,
    non-root compose dispatcher (whose VMM confinement is firecracker's built-in
    seccomp + the container's cap-drop/uid/read-only; see ``_fc_base_argv``).
    """
    # Reuse the seccomp-safe base argv so the jailed path also never disables
    # firecracker's built-in filter; the jailer supplies the exec-file itself,
    # so we pass only the args after the binary token.
    fc_args = _fc_base_argv(fc_bin, _JAIL_CONFIG)
    return [
        jailer_bin,
        "--id", str(slot_id),
        "--exec-file", fc_bin,
        "--uid", str(uid),
        "--gid", str(gid),
        "--cgroup-version", "2",
        "--chroot-base-dir", str(jail_base),
        "--",
        *fc_args[1:],
    ]


def _link_or_copy(src: Path, dst: Path) -> None:
    """Hardlink src→dst (instant, no extra space) when same-fs; copy across
    filesystems. Keeps the jailer chroot portable regardless of where the FC
    assets vs. the scratch dir live."""
    import shutil

    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _populate_jail_chroot(
    jail_root: Path, kernel: str, rootfs: str, outdisk: Path
) -> None:
    """Lay out the jailer chroot: hardlink-or-copy the kernel + rootfs in, and
    hardlink the *already-prepared* per-slot output disk in so the guest's writes
    land on the same inode wait()'s _read_outdisk reads back via the slot-dir
    path. Kernel/rootfs stay world-readable (0644) so the uid-dropped firecracker
    can read them without us chowning — and mutating — the shared source inode."""
    jail_root.mkdir(parents=True, exist_ok=True)
    _link_or_copy(Path(kernel), jail_root / "vmlinux")
    _link_or_copy(Path(rootfs), jail_root / "rootfs.ext4")
    _link_or_copy(outdisk, jail_root / "outdisk.ext4")


def _chown_jail_writables(jail_root: Path) -> None:
    """chown only the *writable* chroot bits to the worker uid so the uid-dropped
    firecracker can create the vsock UDS (in jail_root) + write the output disk.
    No-op when not root (dev/test). Deliberately not recursive: chowning the
    kernel/rootfs hardlinks would mutate the shared source inode."""
    if not (hasattr(os, "geteuid") and os.geteuid() == 0):
        return
    for p in (jail_root, jail_root / "outdisk.ext4"):
        try:
            os.chown(p, _WORKER_UID, _WORKER_GID)
        except OSError:
            pass


def _remove_jail_cgroup(slot_id: object) -> None:
    """Best-effort rmdir of the empty cgroup v2 dir the jailer creates at
    ``/sys/fs/cgroup/firecracker/<id>`` (left behind after FC exits). Harmless
    no-op if the path differs or we're not root; an empty cgroup is low-severity
    so we don't fail reap over it."""
    if not (hasattr(os, "geteuid") and os.geteuid() == 0):
        return
    try:
        (Path("/sys/fs/cgroup/firecracker") / str(slot_id)).rmdir()
    except OSError:
        pass


def _secure_scratch_perms(p: Path) -> None:
    """chmod a scratch dir to 0o770 and (best-effort) chown it to the worker
    UID/GID so container UID 10001 can write but the world cannot.

    Replaces the old 0o777. The chown only runs when we're root (the common
    container/prod case); in local dev/tests where geteuid() != 0 we can't
    chown to an arbitrary uid, so we skip it and rely on the current user
    already owning the dir (0o770 keeps it writable for the owner). Any
    PermissionError/OSError from chown is swallowed for the same reason.
    """
    os.chmod(p, 0o770)
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        try:
            os.chown(p, _WORKER_UID, _WORKER_GID)
        except (PermissionError, OSError):
            pass


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
    #
    # NOTE: debugfs rdump extracts the WHOLE ext4 tree before this cap is checked,
    # so the transient host-disk footprint is bounded by fc_outdisk_mib (not
    # max_bytes) PER SLOT. Size the scratch filesystem accordingly:
    #   scratch_free >= fc_outdisk_mib * pool_concurrent_size.
    # The window is bounded (the enforced fc_outdisk_mib <= max_extracted_bytes
    # + 128 MiB invariant keeps it near ~600 MiB/slot) and rglob does not follow
    # symlinks, so this is a bounded host-scratch DoS only — no escape/poisoning.
    # A future tightening could add an entry-COUNT ceiling alongside the byte cap.
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
        # 0o770 + chown to worker UID 10001 (when root) so container UID 10001
        # can write but the world cannot. Was 0o777 (world-writable).
        await asyncio.to_thread(_secure_scratch_perms, slot_dir)
        await asyncio.to_thread(_secure_scratch_perms, slot_dir / "in")
        await asyncio.to_thread(_secure_scratch_perms, slot_dir / "out")
        await asyncio.to_thread(_secure_scratch_perms, slot_dir / "control")
        return slot_dir

    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        from redtusk.sandbox.container import build_run_argv
        # Limits.worker_runtime overrides auto-detected runtime (useful when runsc/gVisor
        # is available but its 9p filesystem cannot propagate FIFOs to the host).
        effective_runtime = limits.worker_runtime or self.docker.runtime
        # "firecracker" is not a Docker runtime — it selects FirecrackerWorkerRuntime
        # in cli.py. If it reaches here, the deployment is misconfigured (FC value
        # but Docker backend); fail with a clear message rather than letting
        # build_run_argv raise a generic "runtime must be one of ..." per spawn.
        if effective_runtime == "firecracker":
            raise WorkerError(
                "worker_runtime='firecracker' requires the Firecracker backend, "
                "not DockerWorkerRuntime. This is a deployment wiring bug: the FC "
                "value reached the Docker spawn path."
            )
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
        # 0o770 + chown to worker UID 10001 (when root); was 0o777.
        await asyncio.to_thread(_secure_scratch_perms, slot_dir)
        await asyncio.to_thread(_secure_scratch_perms, slot_dir / "out")
        await asyncio.to_thread(
            _make_ext4_sync, slot_dir / "outdisk.ext4", self.limits.fc_outdisk_mib
        )
        return slot_dir

    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        if slot.scratch_dir is None:
            raise WorkerError(f"slot {slot.id} has no scratch_dir")
        slot_dir = Path(slot.scratch_dir)
        port = limits.fc_vsock_port

        # Lay out the config + chroot (jailer) or plain config (bare), and learn
        # where FC's host-side vsock UDS will be — bare-metal Mode B wraps the VMM
        # in the firecracker jailer; compose uses the hardened bare spawn.
        if limits.fc_use_jailer:
            argv, listener_path = await self._prepare_jail(slot, slot_dir, limits, port)
        else:
            argv, listener_path = await self._prepare_bare(slot_dir, limits, port)

        # Bind the host listener BEFORE launching FC so the worker's
        # afterRestore-driven connect succeeds on first try.
        server = VsockSlotServer(
            unix_path=listener_path,
            ready_timeout_s=float(limits.worker_warmup_timeout_s),
            recv_timeout_s=float(limits.job_timeout_s),
        )
        await asyncio.to_thread(server.bind)
        self._vsock_servers[slot.id] = server

        log_path = slot_dir / "fc.log"
        # Launch FC (or the jailer, which execs FC after chroot+uid-drop). KVM
        # access needs the redtusk user in the kvm group (bare) or the jailer's
        # chroot /dev/kvm owned by the dropped uid (jailer); we don't shell out
        # to sudo here (avoids password prompts in the dispatcher).
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=await asyncio.to_thread(open, log_path, "w"),
            stderr=asyncio.subprocess.STDOUT,
        )
        self._fc_procs[slot.id] = proc
        return str(proc.pid)

    async def _prepare_bare(
        self, slot_dir: Path, limits: Limits, port: int
    ) -> tuple[list[str], str]:
        """Plain `firecracker --no-api` spawn (compose default). Absolute paths;
        the VMM's confinement is its built-in seccomp + the container hardening."""
        vsock_uds = slot_dir / "vsock.sock"          # FC owns this path
        listener_path = f"{vsock_uds}_{port}"        # we own this one
        fc_config = _build_fc_config(
            limits.fc_kernel,
            limits.fc_rootfs,
            str(slot_dir / "outdisk.ext4"),
            str(vsock_uds),
            port,
            limits.fc_vcpu_count,
            limits.fc_mem_mib,
        )
        config_path = slot_dir / "fc-config.json"
        await asyncio.to_thread(config_path.write_text, json.dumps(fc_config, indent=2))
        return _fc_base_argv(limits.fc_bin, str(config_path)), listener_path

    async def _prepare_jail(
        self, slot: Slot, slot_dir: Path, limits: Limits, port: int
    ) -> tuple[list[str], str]:
        """Bare-metal Mode B: stage the jailer chroot + a chroot-relative config,
        and return the jailer argv. The chroot lives under slot_dir so reap()'s
        rmtree cleans it. toolz2-validated: the CRaC restore inside this jail is
        byte-identical to the bare boot."""
        jail_base = _jail_base(slot_dir)
        jail_root = _jail_root(slot_dir, slot.id)
        await asyncio.to_thread(
            _populate_jail_chroot,
            jail_root,
            limits.fc_kernel,
            limits.fc_rootfs,
            slot_dir / "outdisk.ext4",
        )
        fc_config = _build_fc_config(
            _JAIL_KERNEL,
            _JAIL_ROOTFS,
            _JAIL_OUTDISK,
            _JAIL_VSOCK,
            port,
            limits.fc_vcpu_count,
            limits.fc_mem_mib,
        )
        await asyncio.to_thread(
            (jail_root / "fc.json").write_text, json.dumps(fc_config, indent=2)
        )
        await asyncio.to_thread(_chown_jail_writables, jail_root)
        # FC (chrooted) creates <jail_root>/vsock.sock; the guest dialing host
        # port P makes FC connect to <jail_root>/vsock.sock_P, so we listen there.
        listener_path = f"{jail_root / 'vsock.sock'}_{port}"
        argv = _jailer_argv(
            limits.fc_jailer_bin, limits.fc_bin, slot.id, jail_base,
            _WORKER_UID, _WORKER_GID,
        )
        return argv, listener_path

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
            # The slot never signalled READY. Before surfacing this as an opaque
            # warmup timeout, check the guest console for the one failure that
            # never self-resolves: a CRaC restore aborting on incompatible CPU
            # features. If that's what happened, raise a clear, actionable error
            # naming the exact -XX:CPUFeatures value to rebuild with.
            await self._raise_if_cpu_feature_mismatch(slot)
            return False

    async def _raise_if_cpu_feature_mismatch(self, slot: Slot) -> None:
        """Inspect ``<slot.scratch_dir>/fc.log`` (the captured guest serial
        console). If it shows a warp CRaC CPU-feature mismatch, record a metric,
        log the remediation, and raise :class:`FcCpuFeatureMismatchError`. Otherwise
        return quietly so the caller falls back to the generic timeout path.

        Diagnosis is best-effort: a missing/unreadable log is not itself an
        error here, so any OSError just yields the generic timeout.
        """
        if slot.scratch_dir is None:
            return
        log_path = Path(slot.scratch_dir) / "fc.log"
        try:
            console = await asyncio.to_thread(log_path.read_text, errors="replace")
        except OSError:
            return
        mismatch = parse_cpu_mismatch(console)
        if mismatch is None:
            return
        record_cpu_feature_mismatch()
        _logger.error(
            "fc.cpu_feature_mismatch",
            slot_id=str(slot.id),
            needed=mismatch.needed,
            remediation=(
                "rebuild the FC rootfs/checkpoint with "
                f"-XX:CPUFeatures={mismatch.needed} on AOT-create and checkpoint"
            ),
        )
        raise FcCpuFeatureMismatchError(mismatch.needed, detail=mismatch.raw_line)

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
            # Past job_timeout_s. We run --no-api with no control socket and the
            # guest may be wedged, so we cannot ask it to flush/poweroff cleanly;
            # SIGKILL the VMM. The guest's umount+sync (init-vsock) therefore never
            # runs, so the ext4 read below is best-effort PARTIAL SALVAGE of a
            # possibly-torn image — never a trusted complete result.
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
            rc = TIMEOUT_EXIT_CODE
        # Read the output disk into /out for _ingest_result. On a CLEAN exit the
        # guest powered off after umount+sync so the ext4 is consistent; on a
        # SIGKILL timeout it may be torn (see above). Either way the read is
        # best-effort and the result is schema-validated + hashed before it is
        # trusted, so a torn/partial image fails closed rather than poisoning.
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
        # rmtree(scratch_dir) already removes the jailer chroot (hardlinks — the
        # shared rootfs/kernel inode survives). The jailer also leaves an *empty*
        # cgroup behind after FC exits; best-effort rmdir it (jailer + root only).
        if self.limits.fc_use_jailer:
            await asyncio.to_thread(_remove_jail_cgroup, slot.id)

    async def is_container_running(self, slot: Slot) -> bool:
        proc = self._fc_procs.get(slot.id)
        return proc is not None and proc.returncode is None
