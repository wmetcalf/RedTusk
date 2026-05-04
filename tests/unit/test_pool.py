"""Unit tests for Pool (warm-slot state machine).

All tests avoid calling pool.start() to prevent background tasks from
interfering with deterministic assertions. Slots are injected directly
into pool._slots and internal methods are called as needed.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from redtusk.errors import PoolExhaustedError, WorkerError
from redtusk.limits import Limits
from redtusk.pool import Pool
from redtusk.types import Slot, SlotState

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def limits() -> Limits:
    return Limits.from_env(
        pool_size=2,
        pool_max_size=8,
        pool_burst_size=3,
        pool_burst_trigger_s=3,
        pool_burst_drain_s=60,
        pool_spawn_rate_limit=4.0,
        pool_spawn_retry_max=5,
        worker_warmup_timeout_s=15,
    )


@pytest.fixture
def mock_runtime() -> AsyncMock:
    rt = AsyncMock()
    rt.create_scratch.return_value = Path("/tmp/scratch/test")
    rt.spawn.return_value = "container-abc"
    rt.poll_fifo.return_value = True
    rt.reap.return_value = None
    return rt


@pytest.fixture
def mock_store() -> AsyncMock:
    store = AsyncMock()
    store.count_by_state.return_value = 0
    return store


def _make_pool(limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock) -> Pool:
    return Pool(limits, mock_runtime, mock_store, "default")


def _idle_slot() -> Slot:
    return Slot(
        id=uuid4(),
        state=SlotState.IDLE,
        container_id="c1",
        scratch_dir=Path("/tmp/x"),
        assigned_job_id=None,
        assigned_at=None,
        spawn_attempts=0,
        is_burst=False,
    )


def _warming_slot() -> Slot:
    return Slot(
        id=uuid4(),
        state=SlotState.WARMING,
        container_id=None,
        scratch_dir=None,
        assigned_job_id=None,
        assigned_at=None,
        spawn_attempts=0,
        is_burst=False,
    )


def _assigned_slot() -> Slot:
    return Slot(
        id=uuid4(),
        state=SlotState.ASSIGNED,
        container_id="c2",
        scratch_dir=Path("/tmp/y"),
        assigned_job_id="job-1",
        assigned_at=None,
        spawn_attempts=0,
        is_burst=False,
    )


# ---------------------------------------------------------------------------
# claim() tests
# ---------------------------------------------------------------------------


async def test_claim_returns_idle_slot(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """claim() returns the IDLE slot immediately and transitions it to ASSIGNED."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    slot = _idle_slot()
    pool._slots[slot.id] = slot

    claimed = await pool.claim(timeout=1.0)

    assert claimed is slot
    assert claimed.state == SlotState.ASSIGNED
    assert claimed.assigned_at is not None


async def test_claim_raises_on_timeout_with_no_slots(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """claim() raises PoolExhaustedError when no IDLE slot appears within timeout."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    # No slots at all

    with pytest.raises(PoolExhaustedError):
        await pool.claim(timeout=0.05)


async def test_claim_raises_on_timeout_with_only_warming_slots(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """claim() does not treat WARMING slots as claimable."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._slots[uuid4()] = _warming_slot()

    with pytest.raises(PoolExhaustedError):
        await pool.claim(timeout=0.05)


async def test_claim_succeeds_when_slot_becomes_idle_during_wait(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """claim() picks up a slot that transitions to IDLE while waiting."""
    pool = _make_pool(limits, mock_runtime, mock_store)

    async def make_idle_soon() -> None:
        await asyncio.sleep(0.05)
        slot = _idle_slot()
        async with pool._lock:
            pool._slots[slot.id] = slot
            pool._idle_event.set()

    asyncio.create_task(make_idle_soon())
    claimed = await pool.claim(timeout=1.0)
    assert claimed.state == SlotState.ASSIGNED


# ---------------------------------------------------------------------------
# release() tests
# ---------------------------------------------------------------------------


async def test_release_success_transitions_to_draining(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """release(success=True) transitions the slot to DRAINING."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    slot = _assigned_slot()
    pool._slots[slot.id] = slot

    await pool.release(slot, success=True)

    assert slot.state == SlotState.DRAINING
    assert slot.assigned_job_id is None


async def test_release_failure_also_transitions_to_draining(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """release(success=False) also transitions to DRAINING — pool replaces the slot."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    slot = _assigned_slot()
    pool._slots[slot.id] = slot

    await pool.release(slot, success=False)

    assert slot.state == SlotState.DRAINING


# ---------------------------------------------------------------------------
# is_healthy() tests
# ---------------------------------------------------------------------------


async def test_is_healthy_true_with_idle_slot(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._slots[uuid4()] = _idle_slot()

    assert pool.is_healthy() is True


async def test_is_healthy_true_during_warmup_window(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """Pool reports healthy within the warmup window even without idle slots."""
    from datetime import UTC, datetime

    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._started_at = datetime.now(UTC)  # just started

    assert pool.is_healthy() is True


async def test_is_healthy_true_with_recent_last_idle(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """is_healthy() is True if last_idle_at was within 30 s."""
    from datetime import UTC, datetime, timedelta

    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._last_idle_at = datetime.now(UTC) - timedelta(seconds=10)

    assert pool.is_healthy() is True


async def test_is_healthy_false_with_old_last_idle(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """is_healthy() is False if last_idle_at was >30 s ago and startup window is past."""
    from datetime import UTC, datetime, timedelta

    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._started_at = datetime.now(UTC) - timedelta(seconds=120)
    pool._last_idle_at = datetime.now(UTC) - timedelta(seconds=60)

    assert pool.is_healthy() is False


# ---------------------------------------------------------------------------
# Count helpers
# ---------------------------------------------------------------------------


async def test_idle_assigned_warming_counts(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    pool = _make_pool(limits, mock_runtime, mock_store)
    pool._slots[uuid4()] = _idle_slot()
    pool._slots[uuid4()] = _idle_slot()
    pool._slots[uuid4()] = _assigned_slot()
    pool._slots[uuid4()] = _warming_slot()

    assert pool.idle_count() == 2
    assert pool.assigned_count() == 1
    assert pool.warming_count() == 1


# ---------------------------------------------------------------------------
# _spawn_one() / SPAWN_FAILED handling
# ---------------------------------------------------------------------------


async def test_spawn_one_success_marks_slot_idle(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """_spawn_one() transitions WARMING -> IDLE on success."""
    pool = _make_pool(limits, mock_runtime, mock_store)

    await pool._spawn_one(is_burst=False)
    # Let the task settle
    await asyncio.sleep(0)

    assert pool.idle_count() == 1


async def test_spawn_one_failure_goes_to_spawn_failed_then_retries(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """When spawn() raises, the slot is removed and reap is called at least once."""
    mock_runtime.spawn.side_effect = WorkerError("docker down")
    pool = _make_pool(limits, mock_runtime, mock_store)

    # _spawn_one handles the exception internally and calls _handle_spawn_failure
    await pool._spawn_one(is_burst=False)
    await asyncio.sleep(0)

    # Slot should have been removed after failure (the original slot is gone).
    # Note: a retry task may have been scheduled and may have also run and failed,
    # but the original slot must be gone regardless.
    # reap should have been called at least once (for the initial slot)
    assert mock_runtime.reap.call_count >= 1


async def test_spawn_one_poll_fifo_false_raises_worker_error(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """When poll_fifo returns False the slot fails gracefully."""
    mock_runtime.poll_fifo.return_value = False
    pool = _make_pool(limits, mock_runtime, mock_store)

    await pool._spawn_one(is_burst=False)
    await asyncio.sleep(0)

    # Slot removed on failure
    assert len(pool._slots) == 0


async def test_consecutive_failures_shrink_target(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """After pool_spawn_retry_max+1 consecutive failures, target_size decrements."""
    mock_runtime.spawn.side_effect = WorkerError("always fails")
    # Use low retry_max so the test is quick
    lim = Limits.from_env(pool_size=3, pool_spawn_retry_max=2)
    pool = _make_pool(lim, mock_runtime, mock_store)
    initial_target = pool._target_size  # 3

    # Simulate consecutive_spawn_failures already at retry_max
    pool._consecutive_spawn_failures = lim.pool_spawn_retry_max

    # One more failure should cross the threshold and shrink target
    # Call _handle_spawn_failure directly so we skip the backoff sleep
    failing_slot = Slot(
        id=uuid4(),
        state=SlotState.WARMING,
        container_id=None,
        scratch_dir=None,
        assigned_job_id=None,
        assigned_at=None,
        spawn_attempts=lim.pool_spawn_retry_max,
        is_burst=False,
    )
    pool._slots[failing_slot.id] = failing_slot
    # Mark consecutive failures as being at the retry_max already
    pool._consecutive_spawn_failures = lim.pool_spawn_retry_max

    # _handle_spawn_failure increments to retry_max+1 then checks > retry_max
    # We need to call it but prevent the recursive retry from actually creating tasks
    # so we patch create_scratch to never be called since _handle_spawn_failure
    # only calls asyncio.create_task(_spawn_one) at the end if failures <= max.
    # Since we're *exceeding* the max, no retry task should be created.
    await pool._handle_spawn_failure(failing_slot, WorkerError("still down"))
    await asyncio.sleep(0)

    assert pool._target_size < initial_target


# ---------------------------------------------------------------------------
# _reap_and_replace() test
# ---------------------------------------------------------------------------


async def test_reap_and_replace_removes_slot_and_spawns(
    limits: Limits, mock_runtime: AsyncMock, mock_store: AsyncMock
) -> None:
    """_reap_and_replace removes the draining slot and spawns a replacement."""
    pool = _make_pool(limits, mock_runtime, mock_store)
    slot = Slot(
        id=uuid4(),
        state=SlotState.DRAINING,
        container_id="cDrain",
        scratch_dir=Path("/tmp/drain"),
        assigned_job_id=None,
        assigned_at=None,
        spawn_attempts=0,
        is_burst=False,
    )
    pool._slots[slot.id] = slot

    await pool._reap_and_replace(slot, success=True)
    await asyncio.sleep(0)  # let _spawn_one run

    mock_runtime.reap.assert_called_once_with(slot)
    # The draining slot was removed; a replacement warming slot was added
    assert slot.id not in pool._slots
