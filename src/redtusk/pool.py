"""Warm-pool manager for RedTusk worker containers.

Pool maintains a configurable number of pre-spawned worker containers
(IDLE slots) so that incoming extraction jobs can be dispatched without
paying the container cold-start penalty on the critical path.

State machine:
    spawn() -> WARMING -> IDLE -> ASSIGNED -> DRAINING -> (gone)
                     |                                        ^
                     +-> SPAWN_FAILED ───────────────────────+
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from redtusk.errors import PoolExhaustedError, WorkerError
from redtusk.jobs.base import JobStore
from redtusk.limits import Limits
from redtusk.observability.logging import get_logger
from redtusk.observability.metrics import (
    record_pool_assigned,
    record_pool_idle,
    record_pool_target,
    record_pool_warming,
    record_spawn_duration,
    record_spawn_outcome,
)
from redtusk.types import JobState, Slot, SlotState
from redtusk.worker_runtime import WorkerRuntime

_logger = get_logger(__name__)


class Pool:
    """Manages a warm pool of pre-spawned worker containers."""

    def __init__(
        self,
        limits: Limits,
        worker_runtime: WorkerRuntime,
        store: JobStore,
        profile: str,
    ) -> None:
        self._limits = limits
        self._runtime = worker_runtime
        self._store = store
        self._profile = profile
        self._slots: dict[UUID, Slot] = {}
        self._lock = asyncio.Lock()
        self._idle_event = asyncio.Event()   # set when a slot becomes IDLE
        self._tasks: list[asyncio.Task[None]] = []
        self._target_size: int = limits.pool_size
        self._spawn_semaphore = asyncio.Semaphore(int(limits.pool_spawn_rate_limit))
        self._consecutive_spawn_failures: int = 0
        self._last_idle_at: datetime | None = None
        self._started_at: datetime | None = None
        self._burst_active: bool = False
        self._burst_last_claimed_at: datetime | None = None

    async def start(self) -> None:
        """Begin the spawn and burst management background tasks."""
        self._started_at = datetime.now(UTC)
        self._tasks.append(asyncio.create_task(self._spawn_loop()))
        self._tasks.append(asyncio.create_task(self._burst_loop()))
        self._tasks.append(asyncio.create_task(self._health_check_loop()))

    async def stop(self) -> None:
        """Cancel background tasks and drain."""
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def claim(self, timeout: float) -> Slot:  # noqa: ASYNC109
        """Wait up to ``timeout`` seconds for an IDLE slot. Return it as ASSIGNED.

        Raises PoolExhaustedError on timeout.
        """
        deadline = asyncio.get_running_loop().time() + timeout
        async with self._lock:
            while True:
                for slot in self._slots.values():
                    if slot.state == SlotState.IDLE:
                        slot.state = SlotState.ASSIGNED
                        slot.assigned_at = datetime.now(UTC)
                        self._burst_last_claimed_at = datetime.now(UTC)
                        self._idle_event.clear()
                        self._update_metrics()
                        return slot
                # No IDLE slot — wait for idle_event
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise PoolExhaustedError(timeout)
                # Release lock while waiting
                self._lock.release()
                try:
                    await asyncio.wait_for(
                        self._idle_event.wait(),
                        timeout=remaining,
                    )
                except TimeoutError:
                    await self._lock.acquire()
                    raise PoolExhaustedError(timeout) from None
                except BaseException:
                    await self._lock.acquire()
                    raise
                await self._lock.acquire()

    async def release(self, slot: Slot, *, success: bool) -> None:
        """Transition ASSIGNED -> DRAINING. Fire-and-forget replacement spawn."""
        async with self._lock:
            slot.state = SlotState.DRAINING
            slot.assigned_job_id = None
            self._update_metrics()
        asyncio.create_task(self._reap_and_replace(slot, success=success))

    def idle_count(self) -> int:
        return sum(1 for s in self._slots.values() if s.state == SlotState.IDLE)

    def assigned_count(self) -> int:
        return sum(1 for s in self._slots.values() if s.state == SlotState.ASSIGNED)

    def warming_count(self) -> int:
        return sum(1 for s in self._slots.values() if s.state == SlotState.WARMING)

    def is_healthy(self) -> bool:
        """True if pool has >=1 IDLE slot, or was idle recently, or is still warming up."""
        if self.idle_count() > 0:
            return True
        if self._last_idle_at is not None:
            elapsed = (datetime.now(UTC) - self._last_idle_at).total_seconds()
            if elapsed < 30:
                return True
        # Still within warmup window
        if self._started_at is not None:
            elapsed = (datetime.now(UTC) - self._started_at).total_seconds()
            if elapsed < self._limits.worker_warmup_timeout_s:
                return True
        return False

    # ------------------------------------------------------------------
    # Internal background loops
    # ------------------------------------------------------------------

    async def _spawn_loop(self) -> None:
        """Maintain target_size slots. Runs as background task."""
        while True:
            async with self._lock:
                current = len(
                    [
                        s
                        for s in self._slots.values()
                        if s.state
                        in (SlotState.WARMING, SlotState.IDLE, SlotState.ASSIGNED)
                    ]
                )
                deficit = min(
                    self._target_size - current,
                    self._limits.pool_max_size - len(self._slots),
                )
                deficit = max(0, deficit)
            for _ in range(deficit):
                asyncio.create_task(self._spawn_one(is_burst=False))
            await asyncio.sleep(0.5)

    async def _spawn_one(self, *, is_burst: bool) -> None:
        """Spawn a single slot. Uses semaphore for rate-limiting."""
        slot = Slot(
            id=uuid4(),
            state=SlotState.WARMING,
            container_id=None,
            scratch_dir=None,
            assigned_job_id=None,
            assigned_at=None,
            spawn_attempts=0,
            is_burst=is_burst,
        )
        async with self._lock:
            self._slots[slot.id] = slot
            self._update_metrics()

        t_start = asyncio.get_running_loop().time()
        async with self._spawn_semaphore:
            try:
                # Create scratch dir
                slot.scratch_dir = await self._runtime.create_scratch(slot.id)
                # Spawn container
                container_id = await self._runtime.spawn(slot, self._limits, self._profile)
                slot.container_id = container_id
                # Wait for fifo
                found = await self._runtime.poll_fifo(
                    slot, timeout=float(self._limits.worker_warmup_timeout_s)
                )
                if not found:
                    raise WorkerError(f"slot {slot.id}: fifo not found within warmup timeout")
                # Mark IDLE
                async with self._lock:
                    slot.state = SlotState.IDLE
                    self._last_idle_at = datetime.now(UTC)
                    self._consecutive_spawn_failures = 0
                    self._idle_event.set()
                    self._update_metrics()
                duration = asyncio.get_running_loop().time() - t_start
                record_spawn_outcome("success")
                record_spawn_duration(duration)
            except Exception as exc:
                record_spawn_outcome("failed")
                await self._handle_spawn_failure(slot, exc)

    async def _handle_spawn_failure(self, slot: Slot, exc: Exception) -> None:
        _logger.warning("pool.spawn_failed", slot_id=str(slot.id), error=str(exc))
        backoff_delays = [0.25, 0.5, 1.0, 2.0, 5.0]
        async with self._lock:
            self._consecutive_spawn_failures += 1
            slot.state = SlotState.SPAWN_FAILED
            slot.spawn_attempts += 1
            failures = self._consecutive_spawn_failures
        await self._runtime.reap(slot)
        async with self._lock:
            del self._slots[slot.id]
        if failures > self._limits.pool_spawn_retry_max:
            async with self._lock:
                if self._target_size > 1:
                    self._target_size -= 1
                    _logger.critical(
                        "pool.shrinking_target", new_target=self._target_size
                    )
        else:
            delay_idx = min(slot.spawn_attempts - 1, len(backoff_delays) - 1)
            await asyncio.sleep(backoff_delays[delay_idx])
            asyncio.create_task(self._spawn_one(is_burst=slot.is_burst))

    async def _reap_and_replace(self, slot: Slot, *, success: bool) -> None:
        await self._runtime.reap(slot)
        async with self._lock:
            del self._slots[slot.id]
            self._update_metrics()
        # Immediately spawn replacement (unless pool target is being met already)
        if not slot.is_burst or self._burst_active:
            asyncio.create_task(self._spawn_one(is_burst=slot.is_burst))

    # ------------------------------------------------------------------
    # Burst management
    # ------------------------------------------------------------------

    async def _burst_loop(self) -> None:
        """Monitor queue depth; spawn burst slots when sustained load detected."""
        sustained_since: datetime | None = None
        while True:
            await asyncio.sleep(1.0)
            queued = await self._store.count_by_state(JobState.QUEUED)
            now = datetime.now(UTC)
            if queued > 0:
                if sustained_since is None:
                    sustained_since = now
                elapsed = (now - sustained_since).total_seconds()
                if elapsed >= self._limits.pool_burst_trigger_s and not self._burst_active:
                    # Trigger burst
                    async with self._lock:
                        current = len(self._slots)
                        burst_slots = min(
                            self._limits.pool_burst_size,
                            self._limits.pool_max_size - current,
                        )
                        self._burst_active = True
                    if burst_slots > 0:
                        _logger.info("pool.burst_triggered", extra_slots=burst_slots)
                        for _ in range(burst_slots):
                            asyncio.create_task(self._spawn_one(is_burst=True))
            else:
                sustained_since = None
                # Drain burst slots if idle for too long
                if self._burst_active and self._burst_last_claimed_at is not None:
                    idle_time = (now - self._burst_last_claimed_at).total_seconds()
                    if idle_time >= self._limits.pool_burst_drain_s:
                        await self._drain_burst_slots()

    async def _drain_burst_slots(self) -> None:
        """Remove idle burst slots."""
        async with self._lock:
            to_drain = [
                s
                for s in self._slots.values()
                if s.is_burst and s.state == SlotState.IDLE
            ]
            for slot in to_drain:
                slot.state = SlotState.DRAINING
        for slot in to_drain:
            asyncio.create_task(self._reap_without_replace(slot))
        async with self._lock:
            self._burst_active = False

    async def _reap_without_replace(self, slot: Slot) -> None:
        await self._runtime.reap(slot)
        async with self._lock:
            del self._slots[slot.id]
            self._update_metrics()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def _health_check_loop(self) -> None:
        """Every 2 s verify that every IDLE slot's container is still running.

        Slots whose containers have exited (e.g. killed by OOM, SIGKILL on a
        previous stack restart, or the worker's self-timeout firing while
        idle) are evicted and replaced so they don't silently absorb jobs
        and fail immediately with exit-2.
        """
        while True:
            await asyncio.sleep(2)
            try:
                await self._check_idle_slots()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.warning("pool.health_check_error", error=str(exc))

    async def _check_idle_slots(self) -> None:
        async with self._lock:
            idle_slots = [s for s in self._slots.values() if s.state == SlotState.IDLE]

        dead: list[Slot] = []
        # Check containers concurrently — one docker inspect per slot.
        results = await asyncio.gather(
            *(self._runtime.is_container_running(s) for s in idle_slots),
            return_exceptions=True,
        )
        for slot, running in zip(idle_slots, results, strict=False):
            if isinstance(running, Exception) or not running:
                dead.append(slot)

        if not dead:
            return

        _logger.warning("pool.stale_slots_evicted", count=len(dead),
                        ids=[str(s.id) for s in dead])
        async with self._lock:
            for slot in dead:
                # Only evict if still IDLE — a concurrent claim could have
                # taken it between the check and now.
                if slot.id in self._slots and self._slots[slot.id].state == SlotState.IDLE:
                    slot.state = SlotState.DRAINING
                    self._update_metrics()

        for slot in dead:
            asyncio.create_task(self._reap_and_replace(slot, success=False))

    # ------------------------------------------------------------------
    # Metrics helper
    # ------------------------------------------------------------------

    def _update_metrics(self) -> None:
        """Called inside lock. Update Prometheus gauges."""
        record_pool_idle(self.idle_count())
        record_pool_assigned(self.assigned_count())
        record_pool_warming(self.warming_count())
        record_pool_target(self._target_size)
