"""structlog setup for RedTusk.

Configures structlog to emit JSON one event per line to stdout (or any stream
the test passes in). Standard-library ``logging`` is also routed through the
same processor chain so dependencies that use stdlib logging show up in the
same stream.
"""
from __future__ import annotations

import logging
import sys
from typing import IO, Any, cast

import structlog


def configure_logging(level: str = "INFO", stream: IO[str] | None = None) -> None:
    """Configure structlog + stdlib logging to emit JSON.

    ``level`` is a logging level name (DEBUG/INFO/WARNING/ERROR/CRITICAL).
    ``stream`` defaults to sys.stdout; tests pass io.StringIO to capture.
    """
    target_stream = stream if stream is not None else sys.stdout
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level!r}")

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    pre_chain: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    # Configure structlog to use stdlib LoggerFactory
    # The ProcessorFormatter on the handler will apply JSONRenderer
    structlog.configure(
        processors=[
            *pre_chain,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging through structlog so library logs go to the same stream.
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(target_stream)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=pre_chain,
        processor=structlog.processors.JSONRenderer(),
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(numeric_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to ``name``.

    ``name`` shows up in the JSON output's ``logger`` field; pass the module
    name (e.g. ``__name__``) for traceability.
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
