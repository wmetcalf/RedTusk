"""Tests for redtusk.limits.Limits and Limits.from_env()."""
from __future__ import annotations

import dataclasses
import os
from unittest.mock import patch

import pytest

from redtusk.errors import ConfigurationError
from redtusk.limits import Limits


def test_defaults_are_sensible() -> None:
    """Defaults should match the design spec's documented values."""
    limits = Limits()

    # Worker / extraction
    assert limits.max_input == 100 * 1024 * 1024
    assert limits.job_timeout_s == 60
    assert limits.max_recursion_depth == 10
    assert limits.max_embedded_entries == 5000
    assert limits.max_extracted_bytes == 500 * 1024 * 1024
    assert limits.max_metadata_bytes == 64 * 1024 * 1024

    # OCR/QR
    assert limits.enable_qr is True
    assert limits.enable_ocr is False
    assert limits.ocr_lang == "eng"
    assert limits.ocr_psm == 3
    assert limits.ocr_timeout_s == 15
    assert limits.ocr_per_call_timeout_s == 30
    assert limits.ocr_all is False

    # Pool
    expected_warm = max(2, (os.cpu_count() or 4) // 2)
    expected_concurrent = max(8, os.cpu_count() or 8)
    assert limits.pool_warm_size == expected_warm
    assert limits.pool_size == expected_warm                # legacy alias
    assert limits.pool_burst_size == 5
    assert limits.pool_burst_trigger_s == 3
    assert limits.pool_burst_drain_s == 60
    assert limits.pool_concurrent_size == expected_concurrent
    assert limits.pool_max_size == expected_concurrent       # legacy alias
    assert limits.pool_spawn_rate_limit == 4.0
    assert limits.pool_spawn_retry_max == 5

    # Worker boot
    assert limits.worker_warmup_timeout_s == 15
    assert limits.sync_queue_timeout_s == 30

    # Profile
    assert limits.profile == "default"
    assert limits.worker_seccomp_profile == ""
    assert limits.worker_apparmor_profile == ""
    assert limits.max_artifact_bytes == 1024 * 1024 * 1024
    assert limits.max_infected_zip_source_bytes == 1024 * 1024 * 1024

    # Job retention
    assert limits.job_retention_seconds == 86400

    # Database
    assert limits.database_url == "sqlite:///./redtusk-jobs.db"

    # Disable knobs
    assert limits.disable_ksm is False


def test_is_frozen() -> None:
    limits = Limits()
    with pytest.raises(dataclasses.FrozenInstanceError):
        limits.pool_warm_size = 99  # type: ignore[misc]


def test_from_env_with_no_env_returns_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        limits = Limits.from_env()
    assert limits == Limits()


def test_from_env_reads_int_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_WARM_SIZE": "20"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_warm_size == 20


def test_from_env_reads_float_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SPAWN_RATE_LIMIT": "8.5"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_spawn_rate_limit == 8.5


def test_from_env_reads_str_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_OCR_LANG": "deu"}, clear=True):
        limits = Limits.from_env()
    assert limits.ocr_lang == "deu"


def test_from_env_reads_bool_truthy() -> None:
    for truthy in ["1", "true", "True", "TRUE", "yes", "on"]:
        with patch.dict(os.environ, {"REDTUSK_ENABLE_OCR": truthy}, clear=True):
            limits = Limits.from_env()
        assert limits.enable_ocr is True, f"{truthy!r} should be truthy"


def test_from_env_reads_bool_falsy() -> None:
    for falsy in ["0", "false", "False", "FALSE", "no", "off", ""]:
        with patch.dict(os.environ, {"REDTUSK_ENABLE_QR": falsy}, clear=True):
            limits = Limits.from_env()
        assert limits.enable_qr is False, f"{falsy!r} should be falsy"


def test_from_env_explicit_overrides_take_precedence() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_WARM_SIZE": "20"}, clear=True):
        limits = Limits.from_env(pool_warm_size=99)
    assert limits.pool_warm_size == 99


def test_from_env_legacy_pool_size_alias() -> None:
    """REDTUSK_POOL_SIZE is the old name for REDTUSK_POOL_WARM_SIZE — must still work."""
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "33"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_warm_size == 33
    assert limits.pool_size == 33  # property alias


def test_from_env_legacy_and_new_pool_size_conflict() -> None:
    from redtusk.errors import ConfigurationError
    with patch.dict(
        os.environ,
        {"REDTUSK_POOL_SIZE": "20", "REDTUSK_POOL_WARM_SIZE": "30"},
        clear=True,
    ), pytest.raises(ConfigurationError, match="deprecated alias"):
        Limits.from_env()


def test_from_env_invalid_int_raises_configuration_error() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "not-a-number"}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_POOL_SIZE" in str(ei.value)


def test_from_env_invalid_float_raises_configuration_error() -> None:
    with patch.dict(
        os.environ, {"REDTUSK_POOL_SPAWN_RATE_LIMIT": "abc"}, clear=True
    ):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_POOL_SPAWN_RATE_LIMIT" in str(ei.value)


def test_from_env_unknown_override_raises() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env(no_such_field=123)
    assert "no_such_field" in str(ei.value)


def test_from_env_invalid_profile_raises() -> None:
    with patch.dict(os.environ, {"REDTUSK_PROFILE": "garbage"}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_PROFILE" in str(ei.value)
    assert "garbage" in str(ei.value)


def test_from_env_valid_profiles() -> None:
    for profile in ["default", "high-density"]:
        with patch.dict(os.environ, {"REDTUSK_PROFILE": profile}, clear=True):
            limits = Limits.from_env()
        assert limits.profile == profile


def test_from_env_rejects_both_legacy_and_new_kwarg() -> None:
    """Regression for GPT-5.5 review G2: passing both pool_size (legacy
    alias) and pool_warm_size (new name) to from_env used to silently
    keep the new name. Now both-set raises ConfigurationError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError, match="deprecated alias"):
            Limits.from_env(pool_size=1, pool_warm_size=2)
        with pytest.raises(ConfigurationError, match="deprecated alias"):
            Limits.from_env(pool_max_size=10, pool_concurrent_size=20)


def test_from_env_rejects_fc_outdisk_exceeding_max_extracted() -> None:
    """Regression for GPT-5.5 review G3 + G3': a fc_outdisk_mib far larger
    than max_extracted_bytes creates a pre-extraction DoS window (host
    rdumps the whole image before the cap fires). from_env rejects — but
    only when worker_runtime is explicitly "firecracker"; non-FC deploy-
    ments shouldn't have to tune an unused FC setting (G3')."""
    with patch.dict(os.environ, {}, clear=True):
        # FC mode: 2 GiB disk vs 500 MiB cap is well past the 128 MiB slack
        with pytest.raises(ConfigurationError, match="fc_outdisk_mib"):
            Limits.from_env(worker_runtime="firecracker", fc_outdisk_mib=2048)
        # Non-FC mode (worker_runtime="" auto, or "runsc"): same value is
        # accepted — the FC setting is unused.
        ok = Limits.from_env(fc_outdisk_mib=2048)
        assert ok.fc_outdisk_mib == 2048
        ok = Limits.from_env(worker_runtime="runsc", fc_outdisk_mib=2048)
        assert ok.fc_outdisk_mib == 2048


def test_worker_runtime_accepts_all_valid_values() -> None:
    """"" (auto), runc, runsc, kata (Docker backend) and firecracker (FC
    backend) are all valid at config time. (finding 2)"""
    for rt in ("", "runc", "runsc", "kata", "firecracker"):
        with patch.dict(
            os.environ, {"REDTUSK_WORKER_RUNTIME": rt}, clear=True
        ):
            limits = Limits.from_env()
        assert limits.worker_runtime == rt


def test_worker_runtime_rejects_typo_via_env() -> None:
    """A typo'd runtime (e.g. "firercracker") must be rejected centrally at
    config time with a clear ConfigurationError, not silently accepted and
    then blow up per-spawn inside build_run_argv. (finding 2)"""
    with patch.dict(
        os.environ, {"REDTUSK_WORKER_RUNTIME": "firercracker"}, clear=True
    ):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_WORKER_RUNTIME" in str(ei.value)


def test_worker_runtime_rejects_unknown_via_override() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            Limits.from_env(worker_runtime="podman")


def test_fc_vcpu_count_must_be_one_under_firecracker():
    """fc_vcpu_count != 1 is a hard correctness invariant under the FC runtime
    (>1 vCPU corrupts large vsock transfers ~44% of the time). It must raise for
    firecracker and be ignored for non-FC runtimes."""
    from redtusk.errors import ConfigurationError

    Limits.from_env(worker_runtime="firecracker", fc_vcpu_count=1)  # ok
    with pytest.raises(ConfigurationError, match="fc_vcpu_count must be 1"):
        Limits.from_env(worker_runtime="firecracker", fc_vcpu_count=2)
    # Non-FC runtimes don't use fc_vcpu_count, so it isn't enforced.
    Limits.from_env(worker_runtime="", fc_vcpu_count=2)
