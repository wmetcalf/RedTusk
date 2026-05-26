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

from redtusk.errors import (
    DispatchError,
    PoolExhaustedError,
    SchemaValidationError,
    WorkerError,
)
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
        self._preflight_state_dirs()

        sync_dir = Path(self._limits.scratch_root) / "_sync"
        try:
            shutil.rmtree(sync_dir, ignore_errors=True)
        except Exception as exc:
            _logger.warning("dispatcher.cleanup_sync_error", error=str(exc))

        await self._recover_orphaned_running_jobs()

        await self._pool.start()
        self._tasks.append(asyncio.create_task(self._claim_loop()))
        self._tasks.append(asyncio.create_task(self._cleanup_loop()))

    def _preflight_state_dirs(self) -> None:
        """Verify scratch_root and artifact_root exist + are writable.

        Fails fast with a clear, actionable error message instead of letting
        every pool slot fail with "Permission denied" in a tight retry loop
        until the queue drains by timeout. The bind-mount setup in compose
        mode requires that the host dir referenced by REDTUSK_STATE_DIR be
        owned by (or writable by) UID 10001 — the redtusk user inside the
        api container. A common failure mode is the dir being root-owned
        because it was created with sudo during initial host setup.
        """
        for label, p in (
            ("scratch_root", self._limits.scratch_root),
            ("artifact_root", self._limits.artifact_root),
        ):
            path = Path(p)
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError as exc:
                msg = (
                    f"{label}={p!r} cannot be created: {exc}. "
                    f"In compose deployments the api container runs as UID "
                    f"10001. Run `chown -R 10001:10001 {p}` on the host."
                )
                _logger.error("dispatcher.preflight_failed", error=msg)
                raise DispatchError(msg) from exc
            # Write probe — even if mkdir succeeded, the parent may be
            # writable but the dir itself a remnant with different perms.
            probe = path / ".redtusk.write_probe"
            try:
                probe.write_bytes(b"")
                probe.unlink()
            except OSError as exc:
                msg = (
                    f"{label}={p!r} exists but is not writable: {exc}. "
                    f"Inside the api container the uid is 10001; on the "
                    f"host run `chown -R 10001:10001 {p}`."
                )
                _logger.error("dispatcher.preflight_failed", error=msg)
                raise DispatchError(msg) from exc

    async def _recover_orphaned_running_jobs(self) -> None:
        """Mark RUNNING jobs as failed on dispatcher startup.

        A RUNNING row in the store corresponds to an in-flight worker
        container. When the dispatcher process restarts (deploy, OOM,
        SIGKILL, host reboot), its worker containers are torn down with
        it — but the DB row keeps state=RUNNING forever, because nothing
        else updates that field. The job then occupies the pool's
        accounting and shows up in `state=running` API queries indefinitely.
        Sweep them on startup and mark failed with a distinctive
        error_code so consumers can distinguish "your job was running
        when the dispatcher restarted" from a real worker crash.
        """
        try:
            stuck = await self._store.list_recent(
                limit=10000, state=JobState.RUNNING.value
            )
        except Exception as exc:
            _logger.warning(
                "dispatcher.orphan_recovery_list_error", error=str(exc)
            )
            return
        if not stuck:
            return
        now = datetime.now(UTC)
        recovered = 0
        for job in stuck:
            job.state = JobState.FAILED
            job.completed_at = now
            job.error_code = "dispatcher_restart"
            job.error_detail = (
                "Job was in RUNNING state when the dispatcher started; "
                "its worker container did not survive the restart and no "
                "result was recorded."
            )
            try:
                await self._store.update(job)
                recovered += 1
            except Exception as exc:
                _logger.warning(
                    "dispatcher.orphan_recovery_update_error",
                    job_id=job.id, error=str(exc),
                )
        _logger.info("dispatcher.orphan_recovery", recovered=recovered)

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

            # Record the moment the worker actually starts processing — this is
            # the boundary between "pool wait" and "real worker time" that the
            # job's `pool_wait_ms` / `processing_ms` calculations key off.
            job.worker_started_at = datetime.now(UTC)
            await self._store.update(job)
            await self._runtime.signal_job(slot, job, self._limits)

            # For microvm profile: drain the vsock stream into the slot's
            # scratch /out dir BEFORE we wait for the container to exit.
            # The worker sends DONE then closes its socket then exits;
            # we have to receive BEFORE the connection dies, otherwise we
            # block forever. File-IPC profile: this is a no-op (artifacts
            # were written directly to the bind-mounted /out).
            try:
                await asyncio.wait_for(
                    self._runtime.receive_result(slot),
                    timeout=float(self._limits.job_timeout_s),
                )
            except (TimeoutError, Exception) as exc:
                # Don't fail the whole dispatch yet — the wait() below will
                # surface the worker exit code. Log so the cause is visible.
                _logger.warning("dispatcher.receive_result_error",
                                job_id=job.id, error=str(exc))

            exit_code = await self._runtime.wait(
                slot, timeout=float(self._limits.job_timeout_s)
            )

            if exit_code == 0:
                await self._ingest_result(slot, job)
                await release_slot(success=True)
            else:
                code = "timeout" if exit_code == 137 else "worker_crash"
                # Worker may have left a mid-parse metadata.json snapshot
                # (DraftSnapshotWriter writes after each entry). If so, promote
                # it to a partial success rather than discarding the work.
                if await self._try_salvage_partial(slot, job, fail_code=code):
                    await release_slot(success=True)
                else:
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

        # 8. Index entry hashes for similarity search (best-effort; never
        #    fails the job). Stores phash/colorhash/sha256 from each entry
        #    in a queryable table so the UI can pivot on "find pages that
        #    look like this one" across the corpus.
        index_method = getattr(self._store, "index_entries", None)
        if index_method is not None:
            try:
                await index_method(job)
            except Exception as exc:
                _logger.warning(
                    "dispatcher.index_entries_failed",
                    job_id=job.id, error=str(exc),
                )
        _logger.info("dispatcher.job_succeeded", job_id=job.id)
        fmt = doc.get("extraction", {}).get("root_content_type", "unknown")
        record_extraction_total(outcome="succeeded", fmt=fmt)

    async def _try_salvage_partial(
        self, slot: Slot, job: JobRecord, *, fail_code: str
    ) -> bool:
        """If the worker left a draft metadata.json from DraftSnapshotWriter,
        promote it to a partial result. Returns True iff the salvage succeeded
        and the job is now in SUCCEEDED state.

        A draft is identified by ``truncated.reason == "in_progress"`` —
        DraftSnapshotWriter sets that sentinel on every snapshot. We rewrite it
        to ``"job_timeout"`` so downstream consumers can tell complete from
        partial results.

        Only ``timeout`` (SIGKILLed past job_timeout_s, exit 137) salvages. A
        ``worker_crash`` (segfault, OOM, JVM exit) may have produced corrupt
        bytes mid-flush — failing the job is safer than ingesting a partial we
        can't trust. Failures here (no file, schema invalid, sha mismatch) are
        non-fatal — the caller falls back to ``_fail_job``.
        """
        if fail_code != "timeout":
            return False
        out_dir = Path(slot.scratch_dir) / "out"  # type: ignore[arg-type]
        metadata_path = out_dir / "metadata.json"
        try:
            raw = _read_capped(metadata_path, self._limits.max_metadata_bytes)
        except (FileNotFoundError, OSError):
            return False
        try:
            doc: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return False

        truncated = doc.get("truncated") or {}
        if truncated.get("reason") != "in_progress":
            # No draft sentinel — this isn't a salvageable partial. (A complete
            # metadata.json reaches this path only if the worker wrote it and
            # then exited non-zero anyway, which would be a real worker_crash.)
            return False

        # Promote sentinel to a real truncation reason callers can act on.
        truncated["reason"] = "job_timeout"
        doc["truncated"] = truncated

        # Validate FIRST so a schema-invalid draft cannot leave a half-rewritten
        # file on disk. Only after validation succeeds do we commit the rewrite.
        try:
            validate_rmeta(doc)
        except SchemaValidationError as exc:
            _logger.warning(
                "dispatcher.salvage_schema_invalid",
                job_id=job.id, error=str(exc),
            )
            return False

        # Atomic-replace via os.replace + tmp file. Plain write_text could leave
        # a truncated file on disk if interrupted mid-write, breaking the next
        # read in _ingest_result.
        try:
            tmp_path = metadata_path.with_suffix(".json.salvage.tmp")
            tmp_path.write_text(json.dumps(doc, indent=2))
            os.replace(tmp_path, metadata_path)
        except OSError as exc:
            _logger.warning(
                "dispatcher.salvage_write_failed", job_id=job.id, error=str(exc)
            )
            return False

        # Reuse _ingest_result so artifact copy + indexing + state update all go
        # through the same code path as a normal success.
        try:
            await self._ingest_result(slot, job)
        except Exception as exc:
            _logger.warning(
                "dispatcher.salvage_ingest_failed", job_id=job.id, error=str(exc)
            )
            return False

        if job.state == JobState.SUCCEEDED:
            _logger.info(
                "dispatcher.job_salvaged",
                job_id=job.id, fail_code=fail_code,
                entries=len((doc.get("extraction") or {}).get("entries") or []),
            )
            return True
        return False

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
        now = datetime.now(UTC)
        job = JobRecord(
            id=f"sync-{sha256[:16]}",
            state=JobState.RUNNING,
            submitted_at=now,
            started_at=now,
            worker_started_at=None,  # set after pool.claim() below
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

            job.worker_started_at = datetime.now(UTC)
            await self._runtime.signal_job(slot, job, limits)
            # Drain vsock result BEFORE the container exits (microvm only;
            # no-op for file-IPC). Mirrors the async dispatch path so both
            # the queued and the sync submission flows handle microvm.
            try:
                await asyncio.wait_for(
                    self._runtime.receive_result(slot),
                    timeout=float(limits.job_timeout_s),
                )
            except (TimeoutError, Exception) as exc:
                _logger.warning("dispatcher.sync_receive_result_error",
                                job_id=job.id, error=str(exc))
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
        # Skip worker draft-snapshot scratch files. DraftSnapshotWriter writes
        # to .metadata.json.draft.tmp and atomically renames onto metadata.json;
        # if SIGKILL hits mid-write, the orphan .tmp shouldn't surface in the
        # artifact tree where the UI would list it.
        if src_path.name == ".metadata.json.draft.tmp":
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
