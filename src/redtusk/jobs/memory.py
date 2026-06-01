"""In-process JobStore backend.

Used for unit tests, single-process dev runs, and as a reference
implementation. Asyncio-safe via a single Lock since it backs every
method onto plain dict operations.
"""
from __future__ import annotations

import asyncio
import copy
from datetime import UTC, datetime, timedelta

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.types import JobRecord, JobState


class MemoryJobStore:
    """In-memory JobStore. All state lives in a process-local dict."""

    def __init__(self) -> None:
        self._records: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def create(self, record: JobRecord) -> None:
        async with self._lock:
            if record.id in self._records:
                raise StorageError(f"job already exists: {record.id}")
            self._records[record.id] = copy.deepcopy(record)

    async def get(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            r = self._records.get(job_id)
            return copy.deepcopy(r) if r is not None else None

    async def update(self, record: JobRecord) -> None:
        async with self._lock:
            if record.id not in self._records:
                raise JobNotFoundError(record.id)
            self._records[record.id] = copy.deepcopy(record)

    async def claim_next_queued(self) -> JobRecord | None:
        async with self._lock:
            queued = [r for r in self._records.values() if r.state == JobState.QUEUED]
            if not queued:
                return None
            queued.sort(key=lambda r: r.submitted_at)
            chosen = queued[0]
            now = _utcnow()
            updated = JobRecord(
                id=chosen.id,
                state=JobState.RUNNING,
                submitted_at=chosen.submitted_at,
                started_at=now,
                completed_at=chosen.completed_at,
                input_sha256=chosen.input_sha256,
                input_size_bytes=chosen.input_size_bytes,
                filename_hint=chosen.filename_hint,
                input_path=chosen.input_path,
                result=chosen.result,
                error_code=chosen.error_code,
                error_detail=chosen.error_detail,
            )
            self._records[chosen.id] = updated
            return copy.deepcopy(updated)

    async def list_recent(self, limit: int = 50, offset: int = 0,
                          state: str | None = None) -> list[JobRecord]:
        async with self._lock:
            records: list[JobRecord] = list(self._records.values())
            if state:
                records = [r for r in records if r.state.value == state]
            ordered = sorted(
                records, key=lambda r: r.submitted_at, reverse=True
            )
            return [copy.deepcopy(r) for r in ordered[offset:offset + limit]]

    async def state_counts(self) -> dict[str, int]:
        async with self._lock:
            out: dict[str, int] = {}
            for r in self._records.values():
                out[r.state.value] = out.get(r.state.value, 0) + 1
            return out

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        q = query.lower()
        async with self._lock:
            matches = [
                r for r in self._records.values()
                if q in (r.filename_hint or "").lower()
            ]
            ordered = sorted(matches, key=lambda r: r.submitted_at, reverse=True)
            return [copy.deepcopy(r) for r in ordered[offset:offset + limit]]

    # ── *_payloads variants ─────────────────────────────────────────────
    # Memory store keeps JobRecord objects directly — there's no jsonb-roundtrip
    # overhead to skip, so we just reuse the typed variants and call .to_dict().
    # (Tests use the memory store; the sql_store implementations are what
    # actually matter for the prod hot path.)

    async def list_recent_payloads(
        self, limit: int = 50, offset: int = 0, state: str | None = None,
    ) -> list[dict]:
        records = await self.list_recent(limit=limit, offset=offset, state=state)
        return [r.to_dict() for r in records]

    async def search_payloads(
        self, query: str, limit: int = 50, offset: int = 0,
    ) -> list[dict]:
        records = await self.search(query, limit=limit, offset=offset)
        return [r.to_dict() for r in records]

    async def delete(self, job_id: str) -> bool:
        async with self._lock:
            r = self._records.get(job_id)
            if r is None:
                raise JobNotFoundError(job_id)
            if not r.state.is_terminal():
                return False
            del self._records[job_id]
            return True

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        cutoff = now - timedelta(seconds=ttl_seconds)
        async with self._lock:
            doomed = [
                r.id
                for r in self._records.values()
                if r.state.is_terminal()
                and r.completed_at is not None
                and r.completed_at < cutoff
            ]
            for job_id in doomed:
                del self._records[job_id]
            return len(doomed)

    async def count_by_state(self, state: JobState) -> int:
        async with self._lock:
            return sum(1 for r in self._records.values() if r.state == state)


def _utcnow() -> datetime:
    """Indirection so tests can monkeypatch if needed; production uses real UTC."""
    return datetime.now(tz=UTC)
