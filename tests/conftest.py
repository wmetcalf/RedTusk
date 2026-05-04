"""Shared pytest fixtures for the RedTusk test suite."""
from __future__ import annotations

import pytest


@pytest.fixture
def fixed_now() -> str:
    """A deterministic ISO-8601 timestamp used by tests that need a fake 'now'."""
    return "2026-05-04T18:23:11+00:00"
