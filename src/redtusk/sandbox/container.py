"""Docker run argv builder for RedTusk worker containers."""
from __future__ import annotations

from pathlib import Path

from redtusk.limits import _VALID_PROFILES, Limits

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
        if limits.worker_seccomp_profile:
            argv += ["--security-opt", f"seccomp={limits.worker_seccomp_profile}"]
        if limits.worker_apparmor_profile:
            argv += ["--security-opt", f"apparmor={limits.worker_apparmor_profile}"]

    argv += [
        "--network", "none",
        "--memory", f"{limits.worker_memory_mb}m",
        "--pids-limit", str(limits.worker_pids_limit),
        "--cpus", str(limits.worker_cpus),
        "--tmpfs", "/tmp:rw,exec,nosuid,size=512m",
        "--tmpfs", "/var/lib/redtusk:rw,nosuid,size=64m,uid=10001,gid=10001",
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

    argv += [
        "--user", "10001:10001",
        image,
        # Override the image's default CMD; tells Main.java to use /scratch for
        # control.fifo and job.json, with /in and /out for input/output.
        "--run", "/scratch",
    ]

    return argv
