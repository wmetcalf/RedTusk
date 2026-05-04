"""Tests for the RetentionSweeper background task."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from redtusk.jobs.memory import MemoryJobStore
from redtusk.jobs.retention import RetentionSweeper
from redtusk.types import JobRecord, JobState


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=UTC) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState, completed_offset_s: int) -> JobRecord:
    return JobRecord(
        id=job_id,
        state=state,
        submitted_at=_now(-completed_offset_s),
        started_at=_now(-completed_offset_s),
        completed_at=_now(-completed_offset_s) if state.is_terminal() else None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )


async def test_sweeper_runs_one_pass_and_deletes() -> None:
    store = MemoryJobStore()
    await store.connect()
    await store.create(_record("old", JobState.SUCCEEDED, completed_offset_s=3600))
    await store.create(_record("recent", JobState.SUCCEEDED, completed_offset_s=10))

    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=0.05,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    await asyncio.sleep(0.15)  # let it run several iterations
    await sweeper.stop()
    await store.close()

    assert await store.get("old") is None
    assert await store.get("recent") is not None


async def test_sweeper_stop_is_idempotent() -> None:
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=10,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    await sweeper.stop()
    await sweeper.stop()  # second call must not raise


async def test_sweeper_start_twice_raises() -> None:
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=10,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    with pytest.raises(RuntimeError):
        await sweeper.start()
    await sweeper.stop()


async def test_sweeper_stops_promptly() -> None:
    """Even with a long interval, stop() should return within a small fraction of it."""
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=300,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    start = asyncio.get_event_loop().time()
    await sweeper.stop()
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed < 1.0, f"stop() took {elapsed:.2f}s, expected < 1s"
