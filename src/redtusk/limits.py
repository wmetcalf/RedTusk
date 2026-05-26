"""Configuration for RedTusk.

A single ``Limits`` frozen dataclass holds every tunable. Both the CLI
and the HTTP API read from ``Limits.from_env()`` so they cannot drift.
Each field maps to the env var ``REDTUSK_<UPPERCASE_FIELD_NAME>``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Any

from redtusk.errors import ConfigurationError

# Recognized deployment profiles.
#   default      — bind-mount file IPC. Works under runc, runsc, kata-with-virtio-fs.
#                  Per-job worker container shares state via /scratch, /in, /out.
#   high-density — runc + CRaC checkpoint/restore. Same file IPC as default.
#   microvm      — vsock IPC. Kata + Firecracker snapshots / VM templating
#                  compatible. No bind mounts; worker gets job + input over
#                  AF_VSOCK, streams metadata + artifacts back over the same
#                  socket. Strongest sandbox + fastest spawn (when templating
#                  is on); pre-requisite for the Phase 3 Kata config that
#                  removes virtio-fs.
_VALID_PROFILES = {"default", "high-density", "microvm"}
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


@dataclass(frozen=True)
class Limits:
    # Worker / extraction
    max_input: int = 100 * 1024 * 1024
    job_timeout_s: int = 60
    max_recursion_depth: int = 10
    max_embedded_entries: int = 5000
    max_extracted_bytes: int = 500 * 1024 * 1024
    max_metadata_bytes: int = 64 * 1024 * 1024

    # Extraction options
    enable_thumbnails: bool = True

    # OCR / QR scanners
    enable_qr: bool = True
    enable_ocr: bool = False
    ocr_lang: str = "eng"
    ocr_psm: int = 3
    ocr_timeout_s: int = 15
    ocr_per_call_timeout_s: int = 30
    ocr_all: bool = False
    # Downscale images to at most this many pixels on the longest edge before
    # passing to Tesseract. 0 = disabled. Default 2000 gives ~300 DPI for A4.
    ocr_max_image_dim: int = 2000
    # Skip OCR on blank/uniform images detected via phash + colorhash.
    ocr_skip_blank: bool = True

    # Pool. Default is half of available logical cores (min 2) — sized to
    # keep half the host free for everything else. Override with the
    # REDTUSK_POOL_SIZE env var or an explicit constructor argument.
    pool_size: int = field(
        default_factory=lambda: max(2, (os.cpu_count() or 4) // 2))
    pool_burst_size: int = 5
    pool_burst_trigger_s: int = 3
    pool_burst_drain_s: int = 60
    # Default cap = full host (cpu_count). Lifted from the old hardcoded 32
    # so big-iron hosts can scale up without surgery. Bursting still respects
    # pool_burst_size on top of pool_size.
    pool_max_size: int = field(
        default_factory=lambda: max(8, os.cpu_count() or 8))
    pool_spawn_rate_limit: float = 4.0
    pool_spawn_retry_max: int = 5

    # Worker boot
    worker_warmup_timeout_s: int = 15
    sync_queue_timeout_s: int = 30

    # Container resources
    worker_memory_mb: int = 1024
    worker_pids_limit: int = 256
    worker_cpus: float = 1.0
    artifact_root: str = "/var/lib/redtusk/artifacts"
    scratch_root: str = "/var/lib/redtusk/scratch"   # REDTUSK_SCRATCH_ROOT

    # Deployment profile
    profile: str = "default"
    # Worker container runtime override. Empty = auto-detect (prefer runsc).
    # Recognized values: "" (auto), "runc", "runsc", "kata".
    #   runc  - Linux namespaces + seccomp + cap-drop; shared host kernel.
    #   runsc - gVisor userspace kernel; default when available; required when
    #           Docker's 9p propagation isn't an issue for the slot's FIFO IPC.
    #   kata  - Kata Containers microVM (Firecracker/QEMU under KVM);
    #           hardware-enforced boundary. Requires /dev/kvm — works on
    #           bare-metal hosts and on AWS C8i/M8i/R8i with the
    #           NestedVirtualization=true API parameter. Strongest sandbox.
    worker_runtime: str = ""
    # Optional runc-only host profiles. Leave empty for portability; runsc/gVisor
    # uses its own sandbox and should not be combined with these Docker options.
    worker_seccomp_profile: str = ""
    worker_apparmor_profile: str = ""

    # Artifact persistence/download caps. The worker has per-file embedded caps;
    # these bound aggregate host-side copy and zip creation.
    max_artifact_bytes: int = 1024 * 1024 * 1024
    max_infected_zip_source_bytes: int = 1024 * 1024 * 1024

    # Job retention (TTL)
    job_retention_seconds: int = 86400

    # JobStore
    database_url: str = "sqlite:///./redtusk-jobs.db"

    # Operator opt-outs
    disable_ksm: bool = False

    @classmethod
    def from_env(cls, **overrides: Any) -> Limits:
        """Construct a Limits from environment variables, then apply explicit overrides.

        Each field maps to ``REDTUSK_<FIELD_NAME_UPPER>`` (e.g. ``pool_size`` ->
        ``REDTUSK_POOL_SIZE``). Bools accept ``1/true/yes/on`` (case-insensitive)
        as truthy; ``0/false/no/off/""`` as falsy. Anything else raises
        ``ConfigurationError``.

        Explicit ``overrides`` are validated against known fields and replace
        anything from the environment.
        """
        field_map = {f.name: f for f in fields(cls)}

        # Validate overrides reference real fields before anything else.
        for key in overrides:
            if key not in field_map:
                raise ConfigurationError(
                    f"unknown Limits field in override: {key!r}"
                )

        kwargs: dict[str, Any] = {}
        for name, field in field_map.items():
            env_name = f"REDTUSK_{name.upper()}"
            if env_name not in os.environ:
                continue
            raw = os.environ[env_name]
            try:
                kwargs[name] = _coerce(field.type, raw, env_name)
            except ValueError as e:
                raise ConfigurationError(str(e)) from e

        kwargs.update(overrides)

        instance = cls(**kwargs)
        if instance.profile not in _VALID_PROFILES:
            raise ConfigurationError(
                f"REDTUSK_PROFILE must be one of {sorted(_VALID_PROFILES)}, "
                f"got {instance.profile!r}"
            )
        return instance


def _coerce(type_str: str | type, raw: str, env_name: str) -> Any:
    """Parse the env-var string for a given dataclass field type.

    The type comes in as a string (e.g. "int") because ``from __future__ import
    annotations`` defers evaluation. We resolve the few primitives we use.
    """
    target = type_str if isinstance(type_str, str) else type_str.__name__
    if target == "int":
        try:
            return int(raw)
        except ValueError as e:
            raise ValueError(
                f"{env_name}={raw!r} is not a valid int"
            ) from e
    if target == "float":
        try:
            return float(raw)
        except ValueError as e:
            raise ValueError(
                f"{env_name}={raw!r} is not a valid float"
            ) from e
    if target == "bool":
        lowered = raw.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
        raise ValueError(
            f"{env_name}={raw!r} is not a valid bool "
            f"(expected one of {sorted(_TRUTHY | _FALSY)})"
        )
    if target == "str":
        return raw
    raise ValueError(f"unsupported Limits field type: {target!r}")
