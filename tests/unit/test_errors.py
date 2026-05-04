"""Tests for the redtusk.errors exception hierarchy."""
from __future__ import annotations

import pytest

from redtusk.errors import (
    ConfigurationError,
    DispatchError,
    ExtractionError,
    JobNotFoundError,
    JobNotTerminalError,
    PoolExhaustedError,
    RedTuskError,
    SchemaValidationError,
    StorageError,
    WorkerError,
)


def test_all_errors_inherit_from_base() -> None:
    """Every RedTusk exception must inherit from RedTuskError so callers
    can catch the whole family with one except clause."""
    subclasses = [
        ConfigurationError,
        DispatchError,
        ExtractionError,
        JobNotFoundError,
        JobNotTerminalError,
        PoolExhaustedError,
        SchemaValidationError,
        StorageError,
        WorkerError,
    ]
    for cls in subclasses:
        assert issubclass(cls, RedTuskError), f"{cls.__name__} must inherit from RedTuskError"


def test_base_inherits_from_exception() -> None:
    assert issubclass(RedTuskError, Exception)


def test_job_not_found_carries_job_id() -> None:
    exc = JobNotFoundError("abc-123")
    assert exc.job_id == "abc-123"
    assert "abc-123" in str(exc)


def test_job_not_terminal_carries_state() -> None:
    exc = JobNotTerminalError("abc-123", "running")
    assert exc.job_id == "abc-123"
    assert exc.state == "running"
    assert "abc-123" in str(exc)
    assert "running" in str(exc)


def test_pool_exhausted_carries_timeout() -> None:
    exc = PoolExhaustedError(timeout_s=30.0)
    assert exc.timeout_s == 30.0
    assert "30" in str(exc)


def test_schema_validation_carries_path() -> None:
    exc = SchemaValidationError(path="entries[0].sha256", reason="not a hex string")
    assert exc.path == "entries[0].sha256"
    assert exc.reason == "not a hex string"
    assert "entries[0].sha256" in str(exc)


def test_can_catch_all_with_base() -> None:
    """A caller using `except RedTuskError` should catch every subclass."""
    for raise_cls in [
        ConfigurationError("x"),
        DispatchError("x"),
        ExtractionError("x"),
        JobNotFoundError("x"),
        JobNotTerminalError("x", "queued"),
        PoolExhaustedError(timeout_s=1.0),
        SchemaValidationError(path="x", reason="x"),
        StorageError("x"),
        WorkerError("x"),
    ]:
        with pytest.raises(RedTuskError):
            raise raise_cls
