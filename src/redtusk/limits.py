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

    # Pool sizing — two-dimensional:
    #
    #   pool_warm_size:        how many slots to keep IDLE and ready.
    #                          Sized to amortize spawn cost; default ½ cores.
    #                          (Legacy name: pool_size — still accepted.)
    #
    #   pool_concurrent_size:  hard ceiling on TOTAL in-flight slots
    #                          (idle + assigned + warming). Bigger than
    #                          pool_warm_size so bursts can spawn cold
    #                          slots beyond the warm reserve.
    #                          (Legacy name: pool_max_size — still accepted.)
    #
    # Bursting: when the queue grows for pool_burst_trigger_s, pool_warm_size
    # is temporarily lifted by pool_burst_size; after pool_burst_drain_s of
    # quiet, it relaxes back. The pool_concurrent_size cap is never exceeded
    # regardless of burst.
    pool_warm_size: int = field(
        default_factory=lambda: max(2, (os.cpu_count() or 4) // 2))
    pool_burst_size: int = 5
    pool_burst_trigger_s: int = 3
    pool_burst_drain_s: int = 60
    pool_concurrent_size: int = field(
        default_factory=lambda: max(8, os.cpu_count() or 8))
    pool_spawn_rate_limit: float = 4.0
    pool_spawn_retry_max: int = 5

    @property
    def pool_size(self) -> int:
        """Legacy alias for :attr:`pool_warm_size` (renamed for clarity)."""
        return self.pool_warm_size

    @property
    def pool_max_size(self) -> int:
        """Legacy alias for :attr:`pool_concurrent_size` (renamed for clarity)."""
        return self.pool_concurrent_size

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

    # Firecracker microVM runtime config — used only when worker_runtime="firecracker".
    # See deploy/firecracker/README.md for how to populate fc_kernel + fc_rootfs.
    fc_bin:        str = "/opt/kata/bin/firecracker"
    fc_kernel:     str = "/var/lib/redtusk/firecracker/vmlinux"
    fc_rootfs:     str = "/var/lib/redtusk/firecracker/rootfs-vsock.ext4"
    # MUST stay 1: with >1 vCPU the guest's virtio-vsock driver races the JVM's
    # socket writes across CPUs, and under concurrent host load that corrupts
    # large RESULT/ARTIFACT transfers on the wire (extra bytes → frame desync →
    # metadata_missing). Empirically vcpu=2 gave ~44% failures on artifact-heavy
    # files at concurrency 8; vcpu=1 drops corruption to ~0. Tika parse is
    # effectively single-threaded so the throughput cost is negligible.
    fc_vcpu_count: int = 1
    fc_mem_mib:    int = 1024
    # AF_VSOCK port the worker connects to on the host gateway. Must match
    # the redtusk.vsock_port=<N> kernel cmdline arg in init-vsock.
    fc_vsock_port: int = 10001
    # Retries when the vsock RESULT/ARTIFACT stream desyncs (a transport-level
    # corruption the guest virtio-vsock layer can still produce under heavy
    # host CPU contention even at fc_vcpu_count=1). Each retry re-runs the job
    # on a fresh microVM. Corruption is detected (frame desync), so this is a
    # bounded, deterministic retry — not a blind loop.
    fc_vsock_retries: int = 2
    # Per-slot output disk (virtio-blk ext4) size in MiB. The worker writes
    # metadata.json + artifacts here instead of streaming them over vsock;
    # the host reads it back after the VM exits. Sparse — only actual output
    # consumes host disk. Must exceed a job's max output (metadata + artifacts).
    fc_outdisk_mib: int = 1024

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
        # Legacy aliases (pool_size / pool_max_size) are allowed and
        # remapped further down.
        _legacy_kwarg_aliases = {"pool_size", "pool_max_size"}
        for key in overrides:
            if key in _legacy_kwarg_aliases:
                continue
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

        # Backward-compat: REDTUSK_POOL_SIZE / REDTUSK_POOL_MAX_SIZE were
        # renamed to REDTUSK_POOL_WARM_SIZE / REDTUSK_POOL_CONCURRENT_SIZE.
        # Translate legacy names if the new ones aren't set; error if both
        # are present so a .env mistake doesn't silently win.
        legacy_aliases = [
            ("POOL_SIZE", "pool_warm_size"),
            ("POOL_MAX_SIZE", "pool_concurrent_size"),
        ]
        for env_suffix, new_field in legacy_aliases:
            env_name = f"REDTUSK_{env_suffix}"
            if env_name in os.environ:
                new_env = f"REDTUSK_{new_field.upper()}"
                if new_field in kwargs or new_env in os.environ:
                    raise ConfigurationError(
                        f"both {env_name} and {new_env} are set; "
                        f"{env_name} is a deprecated alias — pick one"
                    )
                try:
                    kwargs[new_field] = int(os.environ[env_name])
                except ValueError as e:
                    raise ConfigurationError(
                        f"{env_name}={os.environ[env_name]!r} is not a valid int"
                    ) from e

        # Same backward-compat at the kwarg level (for tests that pass
        # pool_size=99 directly to from_env).
        for old_kw, new_kw in [("pool_size", "pool_warm_size"),
                               ("pool_max_size", "pool_concurrent_size")]:
            if old_kw in overrides:
                if new_kw in kwargs:
                    raise ConfigurationError(
                        f"both {old_kw} and {new_kw} were passed; "
                        f"{old_kw} is a deprecated alias — pick one"
                    )
                kwargs[new_kw] = overrides.pop(old_kw)

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
