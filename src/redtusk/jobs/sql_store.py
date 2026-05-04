"""SQL-backed JobStore.

A single class handles both sqlite (via aiosqlite) and postgres (via psycopg
async). The URL scheme determines the dialect; the schema is one ``jobs``
table with a JSON ``payload`` column plus indexed columns for the queries
that have to be fast (state, submitted_at, completed_at).

The atomic ``claim_next_queued`` uses ``SELECT ... FOR UPDATE SKIP LOCKED``
on postgres for safe concurrent claims; sqlite is single-writer so a
``BEGIN IMMEDIATE`` transaction is sufficient.
"""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any


def _serialize(record: "JobRecord") -> str:
    """Serialize a JobRecord to JSON, stripping U+0000 which Postgres JSONB rejects.

    json.dumps encodes Python null bytes as the 6-char JSON escape \\u0000; Postgres
    JSONB rejects both the raw null byte and the escape sequence. Strip both forms.
    """
    return json.dumps(record.to_dict()).replace("\\u0000", "").replace("\x00", "")

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.types import JobRecord, JobState

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    completed_at TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_state_submitted_idx
    ON jobs(state, submitted_at);
CREATE INDEX IF NOT EXISTS jobs_completed_at_idx
    ON jobs(completed_at);
"""

_SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS {schema}.jobs (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_state_submitted_idx
    ON {schema}.jobs(state, submitted_at);
CREATE INDEX IF NOT EXISTS jobs_completed_at_idx
    ON {schema}.jobs(completed_at);
"""


class SqlJobStore:
    """JobStore backed by sqlite or postgres.

    Pass a URL like ``sqlite:///./jobs.db`` or
    ``postgresql://user:pass@host/db`` to the constructor. The ``schema``
    argument is postgres-only and lets tests isolate themselves.
    """

    def __init__(self, url: str, *, schema: str = "public") -> None:
        self._url = url
        self._schema = schema
        self._connected = False
        self._lock = asyncio.Lock()
        if url.startswith("sqlite:///"):
            self._dialect = "sqlite"
            self._sqlite_path = url.removeprefix("sqlite:///")
            self._aiosqlite_conn: Any = None
        elif url.startswith(("postgresql://", "postgres://")):
            self._dialect = "postgres"
            self._psycopg_pool: Any = None
        else:
            raise StorageError(f"unsupported database URL scheme: {url!r}")

    async def connect(self) -> None:
        async with self._lock:
            if self._connected:
                return
            if self._dialect == "sqlite":
                import aiosqlite

                self._aiosqlite_conn = await aiosqlite.connect(self._sqlite_path)
                await self._aiosqlite_conn.executescript(_SCHEMA_SQLITE)
                await self._aiosqlite_conn.commit()
            else:
                from psycopg_pool import AsyncConnectionPool

                self._psycopg_pool = AsyncConnectionPool(
                    self._url, min_size=1, max_size=10, open=False
                )
                await self._psycopg_pool.open()
                async with self._psycopg_pool.connection() as conn:
                    if self._schema != "public":
                        await conn.execute(
                            f'CREATE SCHEMA IF NOT EXISTS "{self._schema}"'
                        )
                    await conn.execute(
                        _SCHEMA_POSTGRES.format(schema=f'"{self._schema}"')
                    )
                    await conn.commit()
            self._connected = True

    async def close(self) -> None:
        async with self._lock:
            if not self._connected:
                return
            if self._dialect == "sqlite" and self._aiosqlite_conn is not None:
                await self._aiosqlite_conn.close()
                self._aiosqlite_conn = None
            elif self._dialect == "postgres" and self._psycopg_pool is not None:
                await self._psycopg_pool.close()
                self._psycopg_pool = None
            self._connected = False

    async def drop_schema(self) -> None:
        """Postgres-only test helper: drop the schema this store created."""
        if self._dialect != "postgres":
            return
        async with self._psycopg_pool.connection() as conn:
            await conn.execute(f'DROP SCHEMA IF EXISTS "{self._schema}" CASCADE')
            await conn.commit()

    async def create(self, record: JobRecord) -> None:
        payload = _serialize(record)
        if self._dialect == "sqlite":
            try:
                await self._aiosqlite_conn.execute(
                    "INSERT INTO jobs(id, state, submitted_at, completed_at, payload) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        record.id,
                        record.state.value,
                        record.submitted_at.isoformat(),
                        record.completed_at.isoformat() if record.completed_at else None,
                        payload,
                    ),
                )
                await self._aiosqlite_conn.commit()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise StorageError(f"job already exists: {record.id}") from e
                raise StorageError(str(e)) from e
        else:
            async with self._psycopg_pool.connection() as conn:
                try:
                    await conn.execute(
                        f'INSERT INTO "{self._schema}".jobs'
                        "(id, state, submitted_at, completed_at, payload) "
                        "VALUES (%s, %s, %s, %s, %s::jsonb)",
                        (
                            record.id,
                            record.state.value,
                            record.submitted_at,
                            record.completed_at,
                            payload,
                        ),
                    )
                    await conn.commit()
                except Exception as e:
                    type_name = type(e).__name__
                    if type_name == "UniqueViolation" or "duplicate key" in str(e):
                        raise StorageError(f"job already exists: {record.id}") from e
                    raise StorageError(str(e)) from e

    async def get(self, job_id: str) -> JobRecord | None:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT payload FROM jobs WHERE id = ?", (job_id,)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs WHERE id = %s',
                        (job_id,),
                    )
                    row = await cur.fetchone()
        if row is None:
            return None
        payload = row[0] if isinstance(row[0], str) else json.dumps(row[0])
        return JobRecord.from_dict(json.loads(payload))

    async def update(self, record: JobRecord) -> None:
        payload = _serialize(record)
        if self._dialect == "sqlite":
            cur = await self._aiosqlite_conn.execute(
                "UPDATE jobs SET state=?, submitted_at=?, completed_at=?, payload=? "
                "WHERE id=?",
                (
                    record.state.value,
                    record.submitted_at.isoformat(),
                    record.completed_at.isoformat() if record.completed_at else None,
                    payload,
                    record.id,
                ),
            )
            if cur.rowcount == 0:
                raise JobNotFoundError(record.id)
            await self._aiosqlite_conn.commit()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'UPDATE "{self._schema}".jobs '
                        "SET state=%s, submitted_at=%s, completed_at=%s, payload=%s::jsonb "
                        "WHERE id=%s",
                        (
                            record.state.value,
                            record.submitted_at,
                            record.completed_at,
                            payload,
                            record.id,
                        ),
                    )
                    if cur.rowcount == 0:
                        raise JobNotFoundError(record.id)
                await conn.commit()

    async def claim_next_queued(self) -> JobRecord | None:
        now = datetime.now(tz=UTC)
        if self._dialect == "sqlite":
            async with self._lock:
                await self._aiosqlite_conn.execute("BEGIN IMMEDIATE")
                async with self._aiosqlite_conn.execute(
                    "SELECT id, payload FROM jobs WHERE state = ? "
                    "ORDER BY submitted_at ASC LIMIT 1",
                    (JobState.QUEUED.value,),
                ) as cur:
                    row = await cur.fetchone()
                if row is None:
                    await self._aiosqlite_conn.commit()
                    return None
                job_id, payload = row[0], row[1]
                record = JobRecord.from_dict(json.loads(payload))
                updated = JobRecord(
                    id=record.id,
                    state=JobState.RUNNING,
                    submitted_at=record.submitted_at,
                    started_at=now,
                    completed_at=record.completed_at,
                    input_sha256=record.input_sha256,
                    input_size_bytes=record.input_size_bytes,
                    filename_hint=record.filename_hint,
                    input_path=record.input_path,
                    result=record.result,
                    error_code=record.error_code,
                    error_detail=record.error_detail,
                )
                await self._aiosqlite_conn.execute(
                    "UPDATE jobs SET state=?, payload=? WHERE id=?",
                    (JobState.RUNNING.value, _serialize(updated), job_id),
                )
                await self._aiosqlite_conn.commit()
                return updated
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT id, payload FROM "{self._schema}".jobs '
                        "WHERE state = %s ORDER BY submitted_at ASC LIMIT 1 "
                        "FOR UPDATE SKIP LOCKED",
                        (JobState.QUEUED.value,),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        await conn.commit()
                        return None
                    job_id = row[0]
                    payload = row[1] if isinstance(row[1], str) else json.dumps(row[1])
                    record = JobRecord.from_dict(json.loads(payload))
                    updated = JobRecord(
                        id=record.id,
                        state=JobState.RUNNING,
                        submitted_at=record.submitted_at,
                        started_at=now,
                        completed_at=record.completed_at,
                        input_sha256=record.input_sha256,
                        input_size_bytes=record.input_size_bytes,
                        filename_hint=record.filename_hint,
                        input_path=record.input_path,
                        result=record.result,
                        error_code=record.error_code,
                        error_detail=record.error_detail,
                    )
                    await cur.execute(
                        f'UPDATE "{self._schema}".jobs '
                        "SET state=%s, payload=%s::jsonb WHERE id=%s",
                        (JobState.RUNNING.value, _serialize(updated), job_id),
                    )
                await conn.commit()
                return updated

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT payload FROM jobs ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs '
                        "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                        (limit, offset),
                    )
                    rows = await cur.fetchall()
        out: list[JobRecord] = []
        for row in rows:
            payload = row[0] if isinstance(row[0], str) else json.dumps(row[0])
            out.append(JobRecord.from_dict(json.loads(payload)))
        return out

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        q = f"%{query}%"
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT payload FROM jobs "
                "WHERE id LIKE ? OR payload LIKE ? "
                "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (q, q, limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    # Check top-level scalar fields directly, then fall back
                    # to full payload text scan for content (QR URLs, OCR text)
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs '
                        "WHERE id ILIKE %s "
                        "OR payload->>'filename_hint' ILIKE %s "
                        "OR payload->>'input_sha256' ILIKE %s "
                        "OR payload::text ILIKE %s "
                        "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                        (q, q, q, q, limit, offset),
                    )
                    rows = await cur.fetchall()
        out: list[JobRecord] = []
        for row in rows:
            payload = row[0] if isinstance(row[0], str) else json.dumps(row[0])
            out.append(JobRecord.from_dict(json.loads(payload)))
        return out

    async def delete(self, job_id: str) -> bool:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT state FROM jobs WHERE id = ?", (job_id,)
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            state = JobState(row[0])
            if not state.is_terminal():
                return False
            await self._aiosqlite_conn.execute(
                "DELETE FROM jobs WHERE id = ?", (job_id,)
            )
            await self._aiosqlite_conn.commit()
            return True
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT state FROM "{self._schema}".jobs WHERE id = %s',
                        (job_id,),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise JobNotFoundError(job_id)
                    state = JobState(row[0])
                    if not state.is_terminal():
                        return False
                    await cur.execute(
                        f'DELETE FROM "{self._schema}".jobs WHERE id = %s', (job_id,)
                    )
                await conn.commit()
                return True

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        cutoff = now - timedelta(seconds=ttl_seconds)
        terminal_states = (JobState.SUCCEEDED.value, JobState.FAILED.value)
        if self._dialect == "sqlite":
            cur = await self._aiosqlite_conn.execute(
                "DELETE FROM jobs WHERE state IN (?, ?) "
                "AND completed_at IS NOT NULL AND completed_at < ?",
                (terminal_states[0], terminal_states[1], cutoff.isoformat()),
            )
            await self._aiosqlite_conn.commit()
            return cur.rowcount or 0
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'DELETE FROM "{self._schema}".jobs '
                        "WHERE state = ANY(%s) AND completed_at IS NOT NULL "
                        "AND completed_at < %s",
                        (list(terminal_states), cutoff),
                    )
                    deleted = cur.rowcount or 0
                await conn.commit()
                return deleted

    async def count_by_state(self, state: JobState) -> int:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE state = ?",
                (state.value,),
            ) as cur:
                row = await cur.fetchone()
            return row[0] if row is not None else 0
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT COUNT(*) FROM "{self._schema}".jobs WHERE state = %s',
                        (state.value,),
                    )
                    row = await cur.fetchone()
            return row[0] if row is not None else 0
