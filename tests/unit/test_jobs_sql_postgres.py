"""Tests for SqlJobStore against a real postgres backend.

Skipped unless REDTUSK_TEST_POSTGRES_URL is set in the environment.
Each test uses a fresh schema (store fixture) so they don't collide.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.sql_store import SqlJobStore
from redtusk.types import JobRecord, JobState

pytestmark = pytest.mark.postgres

_TEST_URL = os.environ.get("REDTUSK_TEST_POSTGRES_URL")


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
async def store():
    if not _TEST_URL:
        pytest.skip("REDTUSK_TEST_POSTGRES_URL not set")
    schema = f"redtusk_test_{uuid.uuid4().hex[:8]}"
    s = SqlJobStore(_TEST_URL, schema=schema)
    await s.connect()
    yield s
    await s.drop_schema()
    await s.close()


async def test_create_and_get(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    assert (await store.get("a")) == r


async def test_create_duplicate_raises(store: SqlJobStore) -> None:
    await store.create(_record("a"))
    with pytest.raises(StorageError):
        await store.create(_record("a"))


async def test_claim_next_queued_returns_oldest(store: SqlJobStore) -> None:
    await store.create(_record("c", submitted_at=_now(2)))
    await store.create(_record("a", submitted_at=_now(0)))
    await store.create(_record("b", submitted_at=_now(1)))
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING


async def test_claim_next_queued_is_atomic_under_concurrency(store: SqlJobStore) -> None:
    """Two concurrent claims against the same QUEUED set must each get a different job."""
    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    results = await asyncio.gather(*[store.claim_next_queued() for _ in range(5)])
    ids = [r.id for r in results if r is not None]
    assert len(ids) == 5
    assert len(set(ids)) == 5  # all distinct, none claimed twice


async def test_delete_non_terminal_returns_false(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False


async def test_delete_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: SqlJobStore) -> None:
    await store.create(
        _record("old-success", state=JobState.SUCCEEDED, completed_at=_now(-3600))
    )
    await store.create(_record("old-running", state=JobState.RUNNING, started_at=_now(-3600)))
    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 1
    assert (await store.get("old-success")) is None
    assert (await store.get("old-running")) is not None
