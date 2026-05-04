"""Tests for the structlog-based logging configuration."""
from __future__ import annotations

import io
import json
import logging

import pytest
import structlog

from redtusk.observability.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def reset_structlog():
    """Each test starts from a clean structlog config."""
    structlog.reset_defaults()
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    yield
    structlog.reset_defaults()
    root.handlers = saved_handlers
    root.level = saved_level


def test_configure_logging_writes_json_to_stream() -> None:
    stream = io.StringIO()
    configure_logging(level="INFO", stream=stream)
    log = get_logger("test")
    log.info("hello", foo="bar", n=42)
    line = stream.getvalue().strip()
    assert line, "logger should have written something"
    record = json.loads(line)
    assert record["event"] == "hello"
    assert record["foo"] == "bar"
    assert record["n"] == 42
    assert record["logger"] == "test"
    assert record["level"] == "info"
    assert "timestamp" in record


def test_log_level_filters_below_threshold() -> None:
    stream = io.StringIO()
    configure_logging(level="WARNING", stream=stream)
    log = get_logger("test")
    log.info("should-not-appear")
    log.warning("should-appear")
    output = stream.getvalue()
    assert "should-not-appear" not in output
    assert "should-appear" in output


def test_get_logger_includes_name() -> None:
    stream = io.StringIO()
    configure_logging(level="DEBUG", stream=stream)
    log = get_logger("redtusk.test.something")
    log.info("x")
    record = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert record["logger"] == "redtusk.test.something"


def test_bind_carries_context() -> None:
    stream = io.StringIO()
    configure_logging(level="INFO", stream=stream)
    log = get_logger("test").bind(job_id="abc-123")
    log.info("processing")
    record = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert record["job_id"] == "abc-123"
