"""Tests for MemoryJobStore."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.memory import MemoryJobStore
from redtusk.types import JobRecord, JobState


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=UTC) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState = JobState.QUEUED, **overrides) -> JobRecord:
    base = dict(
        id=job_id,
        state=state,
        submitted_at=_now(),
        started_at=None,
        completed_at=None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    base.update(overrides)
    return JobRecord(**base)


@pytest.fixture
async def store() -> MemoryJobStore:
    s = MemoryJobStore()
    await s.connect()
    yield s
    await s.close()


async def test_create_and_get(store: MemoryJobStore) -> None:
    r = _record("a")
    await store.create(r)
    fetched = await store.get("a")
    assert fetched == r


async def test_get_unknown_returns_none(store: MemoryJobStore) -> None:
    assert await store.get("does-not-exist") is None


async def test_create_duplicate_raises(store: MemoryJobStore) -> None:
    r = _record("a")
    await store.create(r)
    with pytest.raises(StorageError):
        await store.create(r)


async def test_update_replaces(store: MemoryJobStore) -> None:
    r = _record("a", state=JobState.QUEUED)
    await store.create(r)
    updated = _record("a", state=JobState.RUNNING, started_at=_now(1))
    await store.update(updated)
    assert (await store.get("a")) == updated


async def test_update_unknown_raises(store: MemoryJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.update(_record("nope"))


async def test_claim_next_queued_returns_oldest(store: MemoryJobStore) -> None:
    a = _record("a", submitted_at=_now(0))
    b = _record("b", submitted_at=_now(1))
    c = _record("c", submitted_at=_now(2))
    # Insert out of order to make sure ordering is by submitted_at, not insert order.
    await store.create(c)
    await store.create(a)
    await store.create(b)

    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING
    assert claimed.started_at is not None


async def test_claim_next_queued_skips_non_queued(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    await store.create(_record("b", state=JobState.SUCCEEDED))
    await store.create(_record("c", state=JobState.QUEUED))
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "c"


async def test_claim_next_queued_returns_none_when_empty(store: MemoryJobStore) -> None:
    assert await store.claim_next_queued() is None


async def test_claim_next_queued_returns_none_when_no_queued_remain(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    await store.create(_record("b", state=JobState.SUCCEEDED, completed_at=_now(1)))
    await store.create(_record("c", state=JobState.FAILED, completed_at=_now(2)))
    assert await store.claim_next_queued() is None


async def test_claim_next_queued_persists_state_change(store: MemoryJobStore) -> None:
    await store.create(_record("a"))
    await store.claim_next_queued()
    fetched = await store.get("a")
    assert fetched is not None
    assert fetched.state == JobState.RUNNING


async def test_list_recent_returns_newest_first(store: MemoryJobStore) -> None:
    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent(limit=3)
    assert [r.id for r in recent] == ["job-4", "job-3", "job-2"]


async def test_list_recent_default_limit(store: MemoryJobStore) -> None:
    for i in range(60):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent()
    assert len(recent) == 50


async def test_delete_terminal_returns_true(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.SUCCEEDED, completed_at=_now(1)))
    assert (await store.delete("a")) is True
    assert (await store.get("a")) is None


async def test_delete_non_terminal_returns_false(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False
    assert (await store.get("a")) is not None  # still there


async def test_delete_unknown_raises(store: MemoryJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: MemoryJobStore) -> None:
    # 1h ago, succeeded, eligible
    await store.create(
        _record(
            "old-success",
            state=JobState.SUCCEEDED,
            completed_at=_now(-3600),
        )
    )
    # 1h ago, failed, eligible
    await store.create(
        _record(
            "old-failed",
            state=JobState.FAILED,
            completed_at=_now(-3600),
        )
    )
    # 1h ago, still queued (no completed_at), NOT eligible
    await store.create(_record("old-queued", state=JobState.QUEUED, submitted_at=_now(-3600)))
    # 1h ago, still running (no completed_at), NOT eligible
    await store.create(
        _record("old-running", state=JobState.RUNNING, started_at=_now(-3600))
    )
    # 1m ago, succeeded, NOT eligible (too recent)
    await store.create(
        _record(
            "recent-success",
            state=JobState.SUCCEEDED,
            completed_at=_now(-60),
        )
    )

    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 2
    assert (await store.get("old-success")) is None
    assert (await store.get("old-failed")) is None
    assert (await store.get("old-queued")) is not None
    assert (await store.get("old-running")) is not None
    assert (await store.get("recent-success")) is not None


async def test_implements_protocol() -> None:
    """MemoryJobStore must satisfy isinstance check against JobStore protocol."""
    from redtusk.jobs.base import JobStore

    s = MemoryJobStore()
    assert isinstance(s, JobStore)
