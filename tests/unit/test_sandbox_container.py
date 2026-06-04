"""Unit tests for redtusk.sandbox.container.build_run_argv."""
from __future__ import annotations

from pathlib import Path

import pytest

from redtusk.limits import Limits
from redtusk.sandbox.container import build_run_argv

IMAGE = "redtusk-worker:latest"


def _argv(
    runtime: str = "runc",
    profile: str = "default",
    image: str = IMAGE,
    limits: Limits | None = None,
    scratch_dir: Path | None = None,
    container_name: str = "name123",
    tmp_path: Path | None = None,
) -> list[str]:
    if limits is None:
        limits = Limits()
    if scratch_dir is None:
        scratch_dir = tmp_path if tmp_path is not None else Path("/tmp/scratch")
    return build_run_argv(
        runtime=runtime,
        profile=profile,
        image=image,
        limits=limits,
        scratch_dir=scratch_dir,
        container_name=container_name,
    )


# ---------------------------------------------------------------------------
# 1. runc + default: required flags, no --cap-add, no --runtime
# ---------------------------------------------------------------------------

def test_runc_default_contains_required_flags(tmp_path: Path) -> None:
    argv = _argv(runtime="runc", profile="default", tmp_path=tmp_path)
    assert "docker" == argv[0]
    assert "run" == argv[1]
    assert "--name" in argv
    assert "name123" in argv
    assert "--detach" in argv
    assert "--rm" not in argv  # removed: --rm races with docker wait
    assert "--read-only" in argv
    idx = argv.index("--security-opt")
    assert argv[idx + 1] == "no-new-privileges"
    idx = argv.index("--cap-drop")
    assert argv[idx + 1] == "ALL"
    idx = argv.index("--memory")
    assert argv[idx + 1] == "1024m"
    idx = argv.index("--pids-limit")
    assert argv[idx + 1] == "256"
    idx = argv.index("--cpus")
    assert argv[idx + 1] == "1.0"
    idx = argv.index("--network")
    assert argv[idx + 1] == "none"
    idx = argv.index("--user")
    assert argv[idx + 1] == "10001:10001"
    assert IMAGE in argv


def test_runc_default_no_cap_add(tmp_path: Path) -> None:
    argv = _argv(runtime="runc", profile="default", tmp_path=tmp_path)
    assert "--cap-add" not in argv


def test_runc_default_no_runtime_flag(tmp_path: Path) -> None:
    argv = _argv(runtime="runc", profile="default", tmp_path=tmp_path)
    assert "--runtime" not in argv


# ---------------------------------------------------------------------------
# 2. runsc + default: --runtime runsc present
# ---------------------------------------------------------------------------

def test_runsc_default_has_runtime_flag(tmp_path: Path) -> None:
    argv = _argv(runtime="runsc", profile="default", tmp_path=tmp_path)
    assert "--runtime" in argv
    idx = argv.index("--runtime")
    assert argv[idx + 1] == "runsc"


def test_runsc_default_no_cap_add(tmp_path: Path) -> None:
    argv = _argv(runtime="runsc", profile="default", tmp_path=tmp_path)
    assert "--cap-add" not in argv


def test_runc_uses_optional_seccomp_and_apparmor(tmp_path: Path) -> None:
    limits = Limits(
        worker_seccomp_profile="/etc/redtusk/seccomp.json",
        worker_apparmor_profile="redtusk-worker",
    )
    argv = _argv(runtime="runc", profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert "seccomp=/etc/redtusk/seccomp.json" in secopts
    assert "apparmor=redtusk-worker" in secopts


def test_runsc_skips_optional_seccomp_and_apparmor(tmp_path: Path) -> None:
    limits = Limits(
        worker_seccomp_profile="/etc/redtusk/seccomp.json",
        worker_apparmor_profile="redtusk-worker",
    )
    argv = _argv(runtime="runsc", profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert "seccomp=/etc/redtusk/seccomp.json" not in secopts
    assert "apparmor=redtusk-worker" not in secopts


# ---------------------------------------------------------------------------
# 3. runc + high-density: --cap-add CHECKPOINT_RESTORE, no --runtime
# ---------------------------------------------------------------------------

def test_runc_high_density_has_cap_add(tmp_path: Path) -> None:
    argv = _argv(runtime="runc", profile="high-density", tmp_path=tmp_path)
    cap_adds = [argv[i + 1] for i, v in enumerate(argv) if v == "--cap-add"]
    assert cap_adds == ["CHECKPOINT_RESTORE", "SETPCAP"]


def test_runc_high_density_no_runtime_flag(tmp_path: Path) -> None:
    argv = _argv(runtime="runc", profile="high-density", tmp_path=tmp_path)
    assert "--runtime" not in argv


# ---------------------------------------------------------------------------
# 4. runsc + high-density: both --runtime runsc and --cap-add CHECKPOINT_RESTORE
# ---------------------------------------------------------------------------

def test_runsc_high_density_has_both(tmp_path: Path) -> None:
    argv = _argv(runtime="runsc", profile="high-density", tmp_path=tmp_path)
    assert "--runtime" in argv
    assert argv[argv.index("--runtime") + 1] == "runsc"
    cap_adds = [argv[i + 1] for i, v in enumerate(argv) if v == "--cap-add"]
    assert cap_adds == ["CHECKPOINT_RESTORE", "SETPCAP"]


# ---------------------------------------------------------------------------
# 5. Always-present security flags
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "runtime,profile",
    [
        ("runc", "default"),
        ("runsc", "default"),
        ("runc", "high-density"),
        ("runsc", "high-density"),
    ],
)
def test_always_present_security_flags(
    runtime: str, profile: str, tmp_path: Path
) -> None:
    argv = _argv(runtime=runtime, profile=profile, tmp_path=tmp_path)
    assert "--network" in argv
    assert argv[argv.index("--network") + 1] == "none"
    assert "--read-only" in argv
    assert "--security-opt" in argv
    assert "no-new-privileges" in argv
    assert "--cap-drop" in argv
    assert "ALL" in argv


# ---------------------------------------------------------------------------
# 6. Mount flags reference scratch_dir correctly
# ---------------------------------------------------------------------------

def test_mount_flags_reference_scratch_dir(tmp_path: Path) -> None:
    scratch = tmp_path / "slot-abc"
    argv = _argv(runtime="runc", scratch_dir=scratch, tmp_path=tmp_path)
    mounts = [argv[i + 1] for i, v in enumerate(argv) if v == "--mount"]
    in_mount = f"type=bind,source={scratch}/in,target=/in,readonly"
    out_mount = f"type=bind,source={scratch}/out,target=/out"
    assert in_mount in mounts
    assert out_mount in mounts


# ---------------------------------------------------------------------------
# 7. Resource limit flags use Limits defaults
# ---------------------------------------------------------------------------

def test_default_memory_flag(tmp_path: Path) -> None:
    argv = _argv(tmp_path=tmp_path)
    assert "--memory" in argv
    assert argv[argv.index("--memory") + 1] == "1024m"


def test_default_pids_limit_flag(tmp_path: Path) -> None:
    argv = _argv(tmp_path=tmp_path)
    assert "--pids-limit" in argv
    assert argv[argv.index("--pids-limit") + 1] == "256"


def test_default_cpus_flag(tmp_path: Path) -> None:
    argv = _argv(tmp_path=tmp_path)
    assert "--cpus" in argv
    assert argv[argv.index("--cpus") + 1] == "1.0"


def test_custom_resource_limits(tmp_path: Path) -> None:
    limits = Limits(worker_memory_mb=2048, worker_pids_limit=512, worker_cpus=2.5)
    argv = _argv(limits=limits, tmp_path=tmp_path)
    assert argv[argv.index("--memory") + 1] == "2048m"
    assert argv[argv.index("--pids-limit") + 1] == "512"
    assert argv[argv.index("--cpus") + 1] == "2.5"


# ---------------------------------------------------------------------------
# 8. Invalid input validation
# ---------------------------------------------------------------------------

def test_invalid_runtime_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="runtime must be one of"):
        _argv(runtime="podman", profile="default", tmp_path=tmp_path)


def test_invalid_profile_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="profile must be one of"):
        _argv(runtime="runc", profile="ultra", tmp_path=tmp_path)


# ---------------------------------------------------------------------------
# 9. runc seccomp FAIL-CLOSED (finding 1)
# ---------------------------------------------------------------------------

def test_runc_without_seccomp_and_without_escape_hatch_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """runc with no resolvable seccomp profile and no escape hatch must refuse
    to build the argv (fail closed) — never silently fall back to Docker's
    default seccomp."""
    import redtusk.sandbox.container as container

    # No baked default, no per-container profile, no escape hatch.
    monkeypatch.setattr(container, "_DEFAULT_RUNC_SECCOMP", "")
    monkeypatch.delenv("REDTUSK_ALLOW_INSECURE_RUNC", raising=False)
    limits = Limits(worker_seccomp_profile="")
    with pytest.raises(ValueError, match="runc runtime requires a seccomp profile"):
        _argv(runtime="runc", profile="default", limits=limits, tmp_path=tmp_path)


def test_runc_without_seccomp_with_escape_hatch_builds_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The explicit REDTUSK_ALLOW_INSECURE_RUNC=1 escape hatch lets an operator
    knowingly run runc with Docker's default seccomp (no --security-opt seccomp)."""
    import redtusk.sandbox.container as container

    monkeypatch.setattr(container, "_DEFAULT_RUNC_SECCOMP", "")
    monkeypatch.setenv("REDTUSK_ALLOW_INSECURE_RUNC", "1")
    limits = Limits(worker_seccomp_profile="")
    argv = _argv(runtime="runc", profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert not any(s.startswith("seccomp=") for s in secopts)
    # Still a valid runc argv with the other security flags intact.
    assert "no-new-privileges" in secopts


def test_runc_with_explicit_profile_includes_security_opt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A resolved seccomp profile (via worker_seccomp_profile) is passed through
    as --security-opt seccomp=<path> and no escape hatch is needed."""
    import redtusk.sandbox.container as container

    monkeypatch.setattr(container, "_DEFAULT_RUNC_SECCOMP", "")
    monkeypatch.delenv("REDTUSK_ALLOW_INSECURE_RUNC", raising=False)
    limits = Limits(worker_seccomp_profile="/etc/redtusk/seccomp.json")
    argv = _argv(runtime="runc", profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert "seccomp=/etc/redtusk/seccomp.json" in secopts


def test_runc_uses_baked_default_seccomp_when_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When _DEFAULT_RUNC_SECCOMP is the baked in-image path, runc resolves it
    without an explicit per-container profile and without the escape hatch."""
    import redtusk.sandbox.container as container

    monkeypatch.setattr(
        container, "_DEFAULT_RUNC_SECCOMP", "/opt/redtusk/seccomp/redtusk.seccomp.json"
    )
    monkeypatch.delenv("REDTUSK_ALLOW_INSECURE_RUNC", raising=False)
    limits = Limits(worker_seccomp_profile="")
    argv = _argv(runtime="runc", profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert "seccomp=/opt/redtusk/seccomp/redtusk.seccomp.json" in secopts


@pytest.mark.parametrize("runtime", ["runsc", "kata"])
def test_non_runc_runtimes_unaffected_by_seccomp_fail_closed(
    runtime: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gVisor/runsc and kata do their own syscall interception and must NOT be
    forced through the runc seccomp fail-closed gate (no profile, no escape
    hatch -> still builds a valid argv with no seccomp flag)."""
    import redtusk.sandbox.container as container

    monkeypatch.setattr(container, "_DEFAULT_RUNC_SECCOMP", "")
    monkeypatch.delenv("REDTUSK_ALLOW_INSECURE_RUNC", raising=False)
    limits = Limits(worker_seccomp_profile="")
    argv = _argv(runtime=runtime, profile="default", limits=limits, tmp_path=tmp_path)
    secopts = [argv[i + 1] for i, v in enumerate(argv) if v == "--security-opt"]
    assert not any(s.startswith("seccomp=") for s in secopts)
    assert argv[argv.index("--runtime") + 1] == runtime
