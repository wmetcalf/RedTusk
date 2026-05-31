"""JobStore protocol — contract every backend implements."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from redtusk.types import JobRecord, JobState


@runtime_checkable
class JobStore(Protocol):
    """Persists JobRecords across the lifecycle queued -> running -> succeeded|failed.

    Every method is async; even the in-memory backend uses an asyncio.Lock
    so the contract stays uniform.

    Note: ``@runtime_checkable`` enables ``isinstance(obj, JobStore)`` checks
    but only verifies method *names*, not signatures. Use mypy (strict mode) to
    catch signature mismatches in backend implementations.
    """

    async def connect(self) -> None:
        """Initialize the backend (open db, run migrations). Idempotent."""
        ...

    async def close(self) -> None:
        """Release backend resources. Idempotent."""
        ...

    async def create(self, record: JobRecord) -> None:
        """Persist a new record. Raises ``StorageError`` if the id already exists."""
        ...

    async def get(self, job_id: str) -> JobRecord | None:
        """Fetch a record by id, or return None if no such job exists."""
        ...

    async def update(self, record: JobRecord) -> None:
        """Replace the record for ``record.id``. Raises ``JobNotFoundError`` if missing."""
        ...

    async def claim_next_queued(self) -> JobRecord | None:
        """Atomically find the oldest QUEUED job, transition it to RUNNING, and return it.

        Returns None if no QUEUED jobs exist. The returned record reflects the
        post-transition state (state=RUNNING, started_at set to now).
        """
        ...

    async def list_recent(self, limit: int = 50, offset: int = 0,
                          state: str | None = None) -> list[JobRecord]:
        """Return up to ``limit`` most-recently-submitted jobs, newest first.

        Optional ``state`` filters to a single JobState value
        ("queued" / "running" / "succeeded" / "failed"). ``offset`` skips
        the first N matching jobs for pagination.
        """
        ...

    async def state_counts(self) -> dict[str, int]:
        """Returns total job count per state. Used by the UI to drive
        state-filter pills so users can navigate large queues."""
        ...

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        """Full-text search against job ID, filename, sha256, content-type, QR URLs.

        Matches are case-insensitive substring matches against the serialised
        job payload JSON.  Newest-first, capped at ``limit``.
        """
        ...

    async def list_recent_payloads(
        self, limit: int = 50, offset: int = 0, state: str | None = None,
    ) -> list[dict[str, Any]]:
        """Same shape as ``list_recent`` but returns raw payload dicts (skipping
        the ``JobRecord.from_dict`` reconstruction). Used by the list-jobs API
        path where Pydantic-style typing is wasted: the result tree is parsed
        out of jsonb just to be thrown away by ``_summary_from_payload`` and the
        full-payload deserialization dominates wall time on heavy results."""
        ...

    async def search_payloads(
        self, query: str, limit: int = 50, offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Same as ``search`` but returns raw payload dicts — see
        ``list_recent_payloads`` for the rationale."""
        ...

    async def delete(self, job_id: str) -> bool:
        """Safe-delete: removes the record only if state is terminal.

        Returns True if deleted, False if the record was non-terminal (caller
        should treat as 409). Raises ``JobNotFoundError`` if the id is unknown.
        """
        ...

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        """Delete every terminal job whose completed_at is older than ``now - ttl_seconds``.

        Returns the count of deleted records. Non-terminal jobs are never
        affected by retention.
        """
        ...

    async def count_by_state(self, state: JobState) -> int:
        """Return the count of jobs in the given state."""
        ...
