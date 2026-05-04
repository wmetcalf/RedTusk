"""Observability scaffolding: structured logging + Prometheus metrics."""
from __future__ import annotations

from redtusk.observability import metrics
from redtusk.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger", "metrics"]
