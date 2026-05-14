"""Dispatcher — drives queued jobs through the warm pool."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from redtusk.errors import PoolExhaustedError, SchemaValidationError, WorkerError
from redtusk.jobs.base import JobStore
from redtusk.jobs.retention import prune_orphaned_artifacts
from redtusk.limits import Limits
from redtusk.observability.logging import get_logger
from redtusk.observability.metrics import (
    record_extraction_total,
    record_jobs_in_flight,
)
from redtusk.pool import Pool
from redtusk.schema import validate_rmeta
from redtusk.types import ExtractResult, JobRecord, JobState, Slot
from redtusk.worker_runtime import WorkerRuntime

_logger = get_logger(__name__)


class Dispatcher:
    def __init__(
        self,
        pool: Pool,
        store: JobStore,
        worker_runtime: WorkerRuntime,
        limits: Limits,
    ) -> None:
        self._pool = pool
        self._store = store
        self._runtime = worker_runtime
        self._limits = limits
        self._tasks: list[asyncio.Task[None]] = []
        self._dispatch_tasks: set[asyncio.Task[None]] = set()
        self._in_flight: set[str] = set()  # job IDs currently being dispatched

    async def start(self) -> None:
        sync_dir = Path(self._limits.scratch_root) / "_sync"
        try:
            shutil.rmtree(sync_dir, ignore_errors=True)
        except Exception as exc:
            _logger.warning("dispatcher.cleanup_sync_error", error=str(exc))

        await self._pool.start()
        self._tasks.append(asyncio.create_task(self._claim_loop()))
        self._tasks.append(asyncio.create_task(self._cleanup_loop()))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        for t in list(self._dispatch_tasks):
            t.cancel()
        await asyncio.gather(*self._dispatch_tasks, return_exceptions=True)
        await self._pool.stop()

    def is_healthy(self) -> bool:
        return self._pool.is_healthy()

    async def _claim_loop(self) -> None:
        """Continuously claim queued jobs and dispatch them.

        Backpressure: never hold more in-flight dispatches than the pool's
        max capacity (pool_size + pool_burst_size).  Without this cap the
        claim loop drains the entire queue in seconds, all dispatch coroutines
        pile up waiting for a slot, and the majority time out before they are
        served.
        """
        max_in_flight = self._limits.pool_size + self._limits.pool_burst_size
        while True:
            try:
                if len(self._in_flight) >= max_in_flight:
                    await asyncio.sleep(0.1)
                    continue
                job = await self._store.claim_next_queued()
                if job is None or job.id in self._in_flight:
                    await asyncio.sleep(0.1)
                    continue
                self._in_flight.add(job.id)
                task = asyncio.create_task(self._dispatch(job))
                self._dispatch_tasks.add(task)
                task.add_done_callback(self._dispatch_tasks.discard)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.warning("dispatcher.claim_loop_error", error=str(exc))
                await asyncio.sleep(1.0)

    async def _cleanup_loop(self) -> None:
        """Periodically delete terminal jobs older than job_retention_seconds."""
        while True:
            try:
                await asyncio.sleep(60)
                deleted = await self._store.delete_expired(
                    datetime.now(UTC), self._limits.job_retention_seconds
                )
                pruned = await prune_orphaned_artifacts(
                    self._store, self._limits.artifact_root
                )
                if deleted:
                    _logger.info("dispatcher.cleanup", deleted=deleted)
                if pruned:
                    _logger.info("dispatcher.artifact_cleanup", deleted=pruned)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.warning("dispatcher.cleanup_error", error=str(exc))

    async def _dispatch(self, job: JobRecord) -> None:
        """Run one job end-to-end. Does not raise — failures are recorded in the store."""
        _logger.info("dispatcher.dispatch_start", job_id=job.id)
        record_jobs_in_flight(len(self._in_flight))
        slot: Slot | None = None
        slot_released = False

        async def release_slot(success: bool) -> None:
            nonlocal slot_released
            if slot is not None and not slot_released:
                slot_released = True
                await self._pool.release(slot, success=success)

        try:
            try:
                slot = await self._pool.claim(timeout=float(self._limits.job_timeout_s))
            except PoolExhaustedError:
                await self._fail_job(
                    job, code="pool_exhausted", detail="no idle slot within timeout"
                )
                return

            slot.assigned_job_id = job.id
            filename = job.filename_hint or "input"
            dest = Path(slot.scratch_dir) / "in" / filename  # type: ignore[arg-type]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if job.input_path:
                _hardlink_or_copy(job.input_path, str(dest))

            await self._runtime.signal_job(slot, job, self._limits)
            exit_code = await self._runtime.wait(
                slot, timeout=float(self._limits.job_timeout_s)
            )

            if exit_code == 0:
                await self._ingest_result(slot, job)
                await release_slot(success=True)
            else:
                code = "timeout" if exit_code == 137 else "worker_crash"
                await self._fail_job(
                    job, code=code, detail=f"worker exited {exit_code}"
                )
                await release_slot(success=False)

        except asyncio.CancelledError:
            await release_slot(success=False)
            raise
        except Exception as exc:
            _logger.error("dispatcher.dispatch_error", job_id=job.id, error=str(exc))
            await self._fail_job(job, code="internal_error", detail=str(exc))
            await release_slot(success=False)
        finally:
            self._in_flight.discard(job.id)
            record_jobs_in_flight(len(self._in_flight))

    async def _ingest_result(self, slot: Slot, job: JobRecord) -> None:
        """Read, validate, and persist the worker's output."""
        out_dir = Path(slot.scratch_dir) / "out"  # type: ignore[arg-type]
        metadata_path = out_dir / "metadata.json"

        # 1. Read metadata.json with size cap
        try:
            raw = _read_capped(metadata_path, self._limits.max_metadata_bytes)
        except (FileNotFoundError, OSError) as exc:
            await self._fail_job(job, code="metadata_missing", detail=str(exc))
            return

        # 2. Parse JSON
        try:
            doc: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            await self._fail_job(
                job, code="metadata_invalid", detail=f"JSON parse error: {exc}"
            )
            return

        # 3. Schema validate
        try:
            validate_rmeta(doc)
        except SchemaValidationError as exc:
            await self._fail_job(job, code="metadata_invalid", detail=str(exc))
            return

        # 4. SHA-256 verify root entry
        root_sha256 = doc.get("input", {}).get("sha256", "")
        if root_sha256 != job.input_sha256:
            await self._fail_job(
                job,
                code="metadata_invalid",
                detail=f"SHA-256 mismatch: expected {job.input_sha256}, got {root_sha256}",
            )
            return

        # 5. Parse into ExtractResult
        result = ExtractResult.from_dict(doc)

        # 6. Copy artifacts to persistent tree
        adir = artifact_dir(self._limits.artifact_root, job.id)
        _copy_artifacts(out_dir, adir, max_bytes=self._limits.max_artifact_bytes)

        # 7. Update job record
        job.state = JobState.SUCCEEDED
        job.completed_at = datetime.now(UTC)
        job.result = result
        await self._store.update(job)
        _logger.info("dispatcher.job_succeeded", job_id=job.id)
        fmt = doc.get("extraction", {}).get("root_content_type", "unknown")
        record_extraction_total(outcome="succeeded", fmt=fmt)

    async def _fail_job(self, job: JobRecord, *, code: str, detail: str = "") -> None:
        job.state = JobState.FAILED
        job.completed_at = datetime.now(UTC)
        job.error_code = code
        job.error_detail = detail
        try:
            await self._store.update(job)
        except Exception as exc:
            _logger.error(
                "dispatcher.fail_job_store_error", job_id=job.id, error=str(exc)
            )
        _logger.warning(
            "dispatcher.job_failed", job_id=job.id, code=code, detail=detail
        )
        record_extraction_total(outcome="failed", fmt="unknown")

    async def submit_sync(
        self,
        body: bytes,
        filename: str,
        limits: Limits,
    ) -> ExtractResult:
        """Process a document synchronously (used by tika-compat endpoints).

        Returns ExtractResult or raises PoolExhaustedError (-> 503) or WorkerError (-> 502).
        """
        # Write body to a temp file in scratch_root
        tmp_dir = Path(limits.scratch_root) / "_sync"
        _mkdir_p(tmp_dir)
        tmp_path: str | None = None
        with tempfile.NamedTemporaryFile(
            dir=tmp_dir, delete=False, suffix=f"_{filename}"
        ) as f:
            f.write(body)
            tmp_path = f.name

        # Build ephemeral job record (not persisted)
        sha256 = hashlib.sha256(body).hexdigest()
        job = JobRecord(
            id=f"sync-{sha256[:16]}",
            state=JobState.RUNNING,
            submitted_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            completed_at=None,
            input_sha256=sha256,
            input_size_bytes=len(body),
            filename_hint=filename,
            input_path=tmp_path,
            result=None,
            error_code=None,
            error_detail=None,
        )

        slot: Slot | None = None
        success = False
        try:
            try:
                slot = await self._pool.claim(
                    timeout=float(limits.sync_queue_timeout_s)
                )
            except PoolExhaustedError:
                raise  # caller handles as 503

            # Hardlink/copy to scratch
            dest = Path(slot.scratch_dir) / "in" / filename  # type: ignore[arg-type]
            dest.parent.mkdir(parents=True, exist_ok=True)
            _hardlink_or_copy(tmp_path, str(dest))

            await self._runtime.signal_job(slot, job, limits)
            exit_code = await self._runtime.wait(
                slot, timeout=float(limits.job_timeout_s)
            )

            if exit_code != 0:
                code = "timeout" if exit_code == 137 else "worker_crash"
                raise WorkerError(f"worker exited {exit_code} ({code})")

            # Read + validate result (reuse ingest logic but return result directly)
            out_dir = Path(slot.scratch_dir) / "out"  # type: ignore[arg-type]
            metadata_path = out_dir / "metadata.json"
            raw = _read_capped(metadata_path, limits.max_metadata_bytes)
            doc = json.loads(raw)
            validate_rmeta(doc)
            root_sha256 = doc.get("input", {}).get("sha256", "")
            if root_sha256 != sha256:
                raise WorkerError(
                    f"SHA-256 mismatch: expected {sha256}, got {root_sha256}"
                )
            result = ExtractResult.from_dict(doc)
            success = True
            return result

        finally:
            if slot is not None:
                await self._pool.release(slot, success=success)
            if tmp_path is not None:
                _rm_ignore(tmp_path)


def artifact_dir(artifact_root: str, job_id: str) -> Path:
    return Path(artifact_root) / job_id[:2] / job_id


def _hardlink_or_copy(src: str, dst: str) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _read_capped(path: Path, max_bytes: int) -> bytes:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"metadata.json too large: {size} > {max_bytes}")
    return path.read_bytes()


def _copy_artifacts(src_dir: Path, dst_dir: Path, *, max_bytes: int) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src_path in src_dir.rglob("*"):
        if not src_path.is_file() or src_path.is_symlink():
            continue
        size = src_path.stat().st_size
        if copied + size > max_bytes:
            raise ValueError(f"artifacts too large: {copied + size} > {max_bytes}")
        rel = src_path.relative_to(src_dir)
        dst_path = dst_dir / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        copied += size


def _mkdir_p(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _rm_ignore(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
