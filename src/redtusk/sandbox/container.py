"""Docker run argv builder for RedTusk worker containers."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from redtusk.limits import _VALID_PROFILES, Limits

_logger = logging.getLogger(__name__)

# Optional host-side path to a shipped default seccomp profile, auto-applied
# to runc containers when REDTUSK_WORKER_SECCOMP_PROFILE is unset. Use this
# in deployments where you can't easily set REDTUSK_WORKER_SECCOMP_PROFILE
# per-container but want runc-mode workers to have something stricter than
# Docker's default seccomp. Empty/unset = no auto-apply (warning logged).
_DEFAULT_RUNC_SECCOMP = os.environ.get("REDTUSK_DEFAULT_RUNC_SECCOMP", "")

# Track whether we've already warned about runc-without-seccomp this run, so
# the log doesn't get spammed once per spawn.
_warned_runc_no_seccomp = False

# Recognized OCI runtime names. The dispatcher delegates to the Docker daemon
# which must have the runtime registered (visible in `docker info | grep Runtimes`).
#   runc   — Linux namespaces + seccomp + cap-drop. Shared host kernel.
#   runsc  — gVisor: userspace kernel intercepts syscalls. Stronger than runc;
#            weaker than microVM. Default when available.
#   kata   — Kata Containers: each container gets its own microVM (Firecracker
#            or QEMU), hardware-enforced boundary via KVM. Requires KVM access
#            (bare metal, or AWS C8i/M8i/R8i with NestedVirtualization=true,
#            or any Linux host with /dev/kvm). Strongest of the three; opt-in
#            via REDTUSK_WORKER_RUNTIME=kata (auto-detect prefers runsc to
#            keep behavior unchanged for existing deployments).
_VALID_RUNTIMES = {"runsc", "runc", "kata"}


def build_run_argv(
    *,
    runtime: str,
    profile: str,
    image: str,
    limits: Limits,
    scratch_dir: Path,
    container_name: str,
) -> list[str]:
    """Return a complete ``docker run`` argv list for a RedTusk worker container.

    Args:
        runtime: Container runtime — ``"runsc"`` (gVisor) or ``"runc"`` (default).
        profile: Deployment profile — ``"default"`` or ``"high-density"``.
        image: Worker Docker image name.
        limits: Resolved :class:`~redtusk.limits.Limits` instance.
        scratch_dir: Host path to the per-slot scratch directory.
        container_name: Unique container name (slot UUID as string).

    Returns:
        List of strings suitable for passing to ``subprocess.run`` / ``exec``.
    """
    if runtime not in _VALID_RUNTIMES:
        raise ValueError(
            f"runtime must be one of {sorted(_VALID_RUNTIMES)!r}, got {runtime!r}"
        )
    if profile not in _VALID_PROFILES:
        raise ValueError(
            f"profile must be one of {sorted(_VALID_PROFILES)!r}, got {profile!r}"
        )

    argv: list[str] = [
        "docker", "run",
        "--detach",           # return container ID immediately; worker runs in background
        "--name", container_name,
        # No --rm: reap() calls docker rm after docker wait captures the exit code.
        # With --rm, the container auto-removes before docker wait can read the exit code.
        "--read-only",
        "--security-opt", "no-new-privileges",
        "--cap-drop", "ALL",
    ]

    if profile == "high-density":
        # SETPCAP is needed only long enough for the restored JVM to drop
        # CHECKPOINT_RESTORE and SETPCAP from its bounding/current sets.
        argv += ["--cap-add", "CHECKPOINT_RESTORE", "--cap-add", "SETPCAP"]

    if runtime == "runc":
        # Under runc the worker shares the host kernel — local kernel CVEs
        # (e.g. CVE-2026-31431 "CopyFail" in algif_aead) are reachable from
        # the container unless seccomp blocks the relevant entry point.
        # Our shipped deploy/seccomp/redtusk.seccomp.json is default-deny
        # and does not allow `socket()` at all, which closes AF_ALG along
        # with every other network family the worker doesn't need. To use
        # it, point REDTUSK_WORKER_SECCOMP_PROFILE at the host-side path,
        # OR set REDTUSK_DEFAULT_RUNC_SECCOMP to apply it whenever runc is
        # selected. When neither is set, the worker ships with Docker's
        # default seccomp — which DOES NOT BLOCK AF_ALG and is therefore
        # exposed to CopyFail-class kernel bugs. Warn loudly so the
        # deployment posture is visible in the logs.
        seccomp_path = limits.worker_seccomp_profile or _DEFAULT_RUNC_SECCOMP
        if seccomp_path:
            argv += ["--security-opt", f"seccomp={seccomp_path}"]
        else:
            global _warned_runc_no_seccomp
            if not _warned_runc_no_seccomp:
                _logger.warning(
                    "container.runc_default_seccomp",
                    extra={"action": "consider setting REDTUSK_WORKER_SECCOMP_PROFILE",
                           "risk": "Docker default seccomp permits socket(AF_ALG, ...) — "
                                   "container is reachable from CopyFail-class kernel CVEs"},
                )
                _warned_runc_no_seccomp = True
        if limits.worker_apparmor_profile:
            argv += ["--security-opt", f"apparmor={limits.worker_apparmor_profile}"]

    argv += [
        "--network", "none",
        "--memory", f"{limits.worker_memory_mb}m",
        "--pids-limit", str(limits.worker_pids_limit),
        "--cpus", str(limits.worker_cpus),
        "--tmpfs", "/tmp:rw,exec,nosuid,size=512m",
        "--tmpfs", "/var/lib/redtusk:rw,nosuid,size=64m,uid=10001,gid=10001",
    ]

    if profile == "microvm":
        # Vsock IPC mode: no host bind-mounts. Job descriptor + input bytes
        # flow over AF_VSOCK from the dispatcher's per-slot VsockSlotServer
        # to the worker's VsockIpcChannel; metadata + artifacts stream back
        # the same way. This is what unblocks Kata VM templating + Firecracker
        # snapshots, which are incompatible with virtio-fs.
        #
        # Configuration is passed via env vars (REDTUSK_WORKER_IPC=vsock,
        # REDTUSK_VSOCK_PORT=<slot's port>). The CMD just runs the worker
        # JAR — no `--run /scratch` arg, since there's no scratch directory.
        port_for_slot = _vsock_port_for_slot(container_name)
        argv += [
            "--env", "REDTUSK_WORKER_IPC=vsock",
            "--env", f"REDTUSK_VSOCK_PORT={port_for_slot}",
            "--env", f"REDTUSK_VSOCK_HOST_CID=2",
        ]
    else:
        # File-IPC profiles (default, high-density): bind-mount the per-slot
        # scratch dir so the worker's FileIpcChannel can read job.json and
        # write metadata.json + artifacts.
        argv += [
            # /scratch: rw bind mount for control.fifo + job.json (visible on host)
            "--mount", f"type=bind,source={scratch_dir},target=/scratch",
            # /in: readonly bind mount for input files (referenced by job.json input_path)
            "--mount", f"type=bind,source={scratch_dir}/in,target=/in,readonly",
            # /out: writable bind mount for worker output (metadata.json, per-entry text)
            "--mount", f"type=bind,source={scratch_dir}/out,target=/out",
        ]

    # runc is Docker's default; passing --runtime=runc is a no-op but harmless.
    # For runsc and kata, the runtime must be registered with the Docker daemon
    # and the host must satisfy its requirements (gVisor binaries for runsc;
    # /dev/kvm + kata-containers packages for kata).
    if runtime in ("runsc", "kata"):
        argv += ["--runtime", runtime]

    argv += ["--user", "10001:10001", image]

    if profile == "microvm":
        # Microvm worker has no scratch dir; it gets the job over vsock.
        # The image's ENTRYPOINT runs the worker JAR in "vsock-listening"
        # mode (Main.java picks up REDTUSK_WORKER_IPC=vsock and routes
        # all IPC through VsockIpcChannel). No CMD args needed — the
        # worker doesn't take a scratch path.
        pass
    else:
        # File-IPC profiles: override the image's default CMD with `--run
        # /scratch`. Main.java parses this and runs the worker against
        # the bind-mounted scratch dir.
        argv += ["--run", "/scratch"]

    return argv


def _vsock_port_for_slot(slot_name: str) -> int:
    """Deterministic per-slot vsock port derivation.

    Uses a low-collision hash on the slot UUID string clamped into the
    user range [49152, 65535) so we don't collide with privileged ports
    or common service ports. Per-slot ports keep concurrent workers
    isolated even when the dispatcher binds AF_VSOCK with CID_ANY.
    """
    h = 0
    for c in slot_name:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return 49152 + (h % (65535 - 49152))
