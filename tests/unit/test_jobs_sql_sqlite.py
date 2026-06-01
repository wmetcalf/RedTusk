"""Tests for SqlJobStore against a sqlite backend."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.sql_store import SqlJobStore
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
async def store(tmp_path) -> SqlJobStore:
    db_path = tmp_path / "test.db"
    s = SqlJobStore(f"sqlite:///{db_path}")
    await s.connect()
    yield s
    await s.close()


async def test_connect_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    s = SqlJobStore(f"sqlite:///{db_path}")
    await s.connect()
    # If we can create + get without error, the schema exists.
    await s.create(_record("a"))
    assert (await s.get("a")) is not None
    await s.close()


async def test_create_and_get(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    fetched = await store.get("a")
    assert fetched == r


async def test_get_unknown_returns_none(store: SqlJobStore) -> None:
    assert await store.get("does-not-exist") is None


async def test_create_duplicate_raises(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    with pytest.raises(StorageError):
        await store.create(r)


async def test_update_replaces(store: SqlJobStore) -> None:
    r = _record("a", state=JobState.QUEUED)
    await store.create(r)
    updated = _record("a", state=JobState.RUNNING, started_at=_now(1))
    await store.update(updated)
    assert (await store.get("a")) == updated


async def test_update_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.update(_record("nope"))


async def test_claim_next_queued_returns_oldest(store: SqlJobStore) -> None:
    a = _record("a", submitted_at=_now(0))
    b = _record("b", submitted_at=_now(1))
    c = _record("c", submitted_at=_now(2))
    await store.create(c)
    await store.create(a)
    await store.create(b)
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING
    assert claimed.started_at is not None


async def test_claim_next_queued_returns_none_when_empty(store: SqlJobStore) -> None:
    assert await store.claim_next_queued() is None


async def test_claim_next_queued_skips_non_queued(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    await store.create(_record("b", state=JobState.SUCCEEDED, completed_at=_now(1)))
    await store.create(_record("c", state=JobState.QUEUED))
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "c"


async def test_list_recent_newest_first(store: SqlJobStore) -> None:
    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent(limit=3)
    assert [r.id for r in recent] == ["job-4", "job-3", "job-2"]


async def test_list_recent_default_limit(store: SqlJobStore) -> None:
    for i in range(60):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent()
    assert len(recent) == 50


async def test_delete_terminal_returns_true(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.SUCCEEDED, completed_at=_now(1)))
    assert (await store.delete("a")) is True
    assert (await store.get("a")) is None


async def test_delete_non_terminal_returns_false(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False
    assert (await store.get("a")) is not None


async def test_delete_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: SqlJobStore) -> None:
    await store.create(
        _record("old-success", state=JobState.SUCCEEDED, completed_at=_now(-3600))
    )
    await store.create(
        _record("old-failed", state=JobState.FAILED, completed_at=_now(-3600))
    )
    await store.create(_record("old-queued", state=JobState.QUEUED, submitted_at=_now(-3600)))
    await store.create(_record("old-running", state=JobState.RUNNING, started_at=_now(-3600)))
    await store.create(
        _record("recent-success", state=JobState.SUCCEEDED, completed_at=_now(-60))
    )
    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 2
    assert (await store.get("old-success")) is None
    assert (await store.get("old-failed")) is None
    assert (await store.get("old-queued")) is not None
    assert (await store.get("old-running")) is not None
    assert (await store.get("recent-success")) is not None


async def test_implements_protocol(tmp_path) -> None:
    from redtusk.jobs.base import JobStore

    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    assert isinstance(s, JobStore)


async def test_close_is_idempotent(tmp_path) -> None:
    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    await s.connect()
    await s.close()
    await s.close()  # second call must not raise


async def test_connect_is_idempotent(tmp_path) -> None:
    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    await s.connect()
    await s.connect()  # second call must not raise
    await s.create(_record("a"))
    assert (await s.get("a")) is not None
    await s.close()
