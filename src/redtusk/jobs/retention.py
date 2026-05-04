"""Periodic JobStore retention sweeper.

A long-running asyncio task that wakes every ``interval_seconds``,
calls ``store.delete_expired(now, ttl_seconds)``.
``start()`` / ``stop()`` give the dispatcher tight lifecycle control.
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from redtusk.jobs.base import JobStore

_log = logging.getLogger(__name__)


class RetentionSweeper:
    """Background task that periodically deletes expired terminal jobs."""

    def __init__(
        self,
        *,
        store: JobStore,
        ttl_seconds: int,
        interval_seconds: float = 60.0,
        clock: Callable[[], datetime] | None = None,
        artifact_root: str | None = None,
    ) -> None:
        self._store = store
        self._ttl_seconds = ttl_seconds
        self._interval_seconds = interval_seconds
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._artifact_root = artifact_root
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("RetentionSweeper already started")
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="redtusk-retention-sweeper")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=2.0)
        except (TimeoutError, asyncio.CancelledError):
            self._task.cancel()
        self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._store.delete_expired(
                    now=self._clock(), ttl_seconds=self._ttl_seconds
                )
                if self._artifact_root:
                    await prune_orphaned_artifacts(self._store, self._artifact_root)
            except Exception as e:
                _log.warning("delete_expired failed: %s", e)
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._interval_seconds
                )
            except TimeoutError:
                continue


async def prune_orphaned_artifacts(
    store: JobStore, artifact_root: str, *, min_age_seconds: float = 300.0
) -> int:
    """Remove artifact directories whose job record no longer exists."""
    root = Path(artifact_root)
    if not root.exists():  # noqa: ASYNC240
        return 0

    cutoff = time.time() - min_age_seconds
    removed = 0
    for shard in root.iterdir():  # noqa: ASYNC240
        if not shard.is_dir():  # noqa: ASYNC240
            continue
        for job_dir in shard.iterdir():  # noqa: ASYNC240
            if not job_dir.is_dir():  # noqa: ASYNC240
                continue
            if job_dir.stat().st_mtime > cutoff:  # noqa: ASYNC240
                continue
            if await store.get(job_dir.name) is not None:
                continue
            shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1
    return removed
