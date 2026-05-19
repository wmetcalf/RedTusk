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
    assert limits.pool_size == 10
    assert limits.pool_burst_size == 5
    assert limits.pool_burst_trigger_s == 3
    assert limits.pool_burst_drain_s == 60
    assert limits.pool_max_size == 32
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
        limits.pool_size = 99  # type: ignore[misc]


def test_from_env_with_no_env_returns_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        limits = Limits.from_env()
    assert limits == Limits()


def test_from_env_reads_int_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "20"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_size == 20


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
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "20"}, clear=True):
        limits = Limits.from_env(pool_size=99)
    assert limits.pool_size == 99


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
