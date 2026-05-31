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
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.types import JobRecord, JobState

# Postgres identifier whitelist for the schema name. The schema is interpolated
# into DDL/DML via f-strings (it cannot be a bound parameter), so it must match
# a strict identifier pattern. This is defense-in-depth: the schema is not
# user-reachable today, but validating here means a future caller can't smuggle
# a `"` to break out of the quoted identifier. Postgres caps identifiers at 63
# bytes, hence the {0,62} upper bound after the leading char.
_VALID_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _serialize(record: JobRecord) -> str:
    """Serialize a JobRecord to JSON, stripping U+0000 which Postgres JSONB rejects.

    PostgreSQL's jsonb type rejects the NUL code point even though it's valid
    JSON. Strip NULs from string values BEFORE json.dumps so the encoder produces
    valid JSON with no escaped \\u0000.

    The previous implementation did the strip on the json.dumps OUTPUT via
    `.replace("\\u0000", "")` — which CORRUPTED any string containing the
    literal six characters `\\u0000` (e.g. extracted JS files with escape
    literals: `Kr=/\\u0000|.../` → json.dumps → `\\\\u0000|...` → replace
    matches at position 1, strips 6 chars → `\\|...` → INVALID JSON → PG
    rejects with "Escape sequence \"\\|\" is invalid."). Stripping at the
    Python-value layer can't corrupt escape sequences because there are none
    yet.
    """
    return json.dumps(_strip_nuls(record.to_dict()))


def _strip_nuls(obj: Any) -> Any:
    """Recursively strip raw NUL bytes from every string value in obj.

    Walks dicts and lists in place-equivalent (returns new structures to keep
    the caller's `record.to_dict()` immutable). Non-string scalars pass through
    unchanged. NUL bytes are removed silently — they have no meaningful place
    in extracted-text payloads and PG jsonb won't store them regardless.
    """
    if isinstance(obj, str):
        return obj.replace("\x00", "") if "\x00" in obj else obj
    if isinstance(obj, dict):
        return {k: _strip_nuls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_nuls(v) for v in obj]
    return obj

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

-- entry_hashes: per-entry perceptual + cryptographic hashes for similarity
-- search across the job corpus. Populated by index_entries() after each
-- successful job. phash is a signed int64 (Hamming-distance friendly);
-- colorhash is 14-hex (txn-distance friendly); sha256 is 64-hex (exact-only).
CREATE TABLE IF NOT EXISTS entry_hashes (
    job_id TEXT NOT NULL,
    entry_path TEXT NOT NULL,
    phash INTEGER,
    colorhash TEXT,
    sha256 TEXT,
    filename TEXT,
    content_type TEXT,
    indexed_at TEXT NOT NULL,
    PRIMARY KEY (job_id, entry_path)
);
CREATE INDEX IF NOT EXISTS entry_hashes_phash_idx ON entry_hashes(phash);
CREATE INDEX IF NOT EXISTS entry_hashes_colorhash_idx ON entry_hashes(colorhash);
CREATE INDEX IF NOT EXISTS entry_hashes_sha256_idx ON entry_hashes(sha256);
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

CREATE TABLE IF NOT EXISTS {schema}.entry_hashes (
    job_id TEXT NOT NULL REFERENCES {schema}.jobs(id) ON DELETE CASCADE,
    entry_path TEXT NOT NULL,
    phash BIGINT,
    colorhash TEXT,
    sha256 TEXT,
    filename TEXT,
    content_type TEXT,
    indexed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (job_id, entry_path)
);
CREATE INDEX IF NOT EXISTS entry_hashes_phash_idx
    ON {schema}.entry_hashes(phash);
CREATE INDEX IF NOT EXISTS entry_hashes_colorhash_idx
    ON {schema}.entry_hashes(colorhash);
CREATE INDEX IF NOT EXISTS entry_hashes_sha256_idx
    ON {schema}.entry_hashes(sha256);
"""


class SqlJobStore:
    """JobStore backed by sqlite or postgres.

    Pass a URL like ``sqlite:///./jobs.db`` or
    ``postgresql://user:pass@host/db`` to the constructor. The ``schema``
    argument is postgres-only and lets tests isolate themselves.
    """

    def __init__(self, url: str, *, schema: str = "public") -> None:
        if not _VALID_SCHEMA_RE.match(schema):
            raise ValueError(
                f"invalid postgres schema name {schema!r}: must match "
                f"{_VALID_SCHEMA_RE.pattern} (letters, digits, underscores; "
                f"max 63 chars; cannot start with a digit)"
            )
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

    async def list_recent(self, limit: int = 50, offset: int = 0,
                          state: str | None = None) -> list[JobRecord]:
        if self._dialect == "sqlite":
            if state:
                async with self._aiosqlite_conn.execute(
                    "SELECT payload FROM jobs WHERE state = ? "
                    "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                    (state, limit, offset),
                ) as cur:
                    rows = await cur.fetchall()
            else:
                async with self._aiosqlite_conn.execute(
                    "SELECT payload FROM jobs ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ) as cur:
                    rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    if state:
                        await cur.execute(
                            f'SELECT payload FROM "{self._schema}".jobs '
                            "WHERE state = %s "
                            "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                            (state, limit, offset),
                        )
                    else:
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

    @staticmethod
    def _rows_to_payloads(rows: list[Any]) -> list[dict[str, Any]]:
        """Parse the SQL ``payload`` column out of each row into a dict, with
        no further reconstruction. Postgres returns jsonb as a dict already,
        SQLite returns it as TEXT — both paths end up as ``dict[str, Any]``.
        Used by the ``*_payloads`` variants to skip ``JobRecord.from_dict``,
        which dominates wall time on heavy results in the list-jobs API."""
        out: list[dict[str, Any]] = []
        for row in rows:
            cell = row[0]
            if isinstance(cell, str):
                out.append(json.loads(cell))
            elif isinstance(cell, dict):
                out.append(cell)
            else:
                out.append(json.loads(json.dumps(cell)))
        return out

    async def list_recent_payloads(
        self, limit: int = 50, offset: int = 0, state: str | None = None,
    ) -> list[dict[str, Any]]:
        """Raw-payload variant of ``list_recent`` — see base.JobStore."""
        if self._dialect == "sqlite":
            if state:
                async with self._aiosqlite_conn.execute(
                    "SELECT payload FROM jobs WHERE state = ? "
                    "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                    (state, limit, offset),
                ) as cur:
                    rows = await cur.fetchall()
            else:
                async with self._aiosqlite_conn.execute(
                    "SELECT payload FROM jobs ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ) as cur:
                    rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    if state:
                        await cur.execute(
                            f'SELECT payload FROM "{self._schema}".jobs '
                            "WHERE state = %s "
                            "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                            (state, limit, offset),
                        )
                    else:
                        await cur.execute(
                            f'SELECT payload FROM "{self._schema}".jobs '
                            "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                            (limit, offset),
                        )
                    rows = await cur.fetchall()
        return self._rows_to_payloads(rows)

    async def search_payloads(
        self, query: str, limit: int = 50, offset: int = 0,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        """Raw-payload variant of ``search`` — see base.JobStore.

        ``state`` (when given) is applied in SQL so LIMIT/OFFSET paginate the
        state-filtered set rather than a post-filtered page."""
        q = f"%{query}%"
        if self._dialect == "sqlite":
            state_clause = "AND state = ? " if state is not None else ""
            params: tuple[Any, ...] = (
                (q, q, q, state, limit, offset)
                if state is not None
                else (q, q, q, limit, offset)
            )
            async with self._aiosqlite_conn.execute(
                "SELECT payload FROM jobs "
                "WHERE (id LIKE ? "
                "OR json_extract(payload, '$.filename_hint') LIKE ? "
                "OR json_extract(payload, '$.input_sha256') LIKE ?) "
                f"{state_clause}"
                "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                params,
            ) as cur:
                rows = await cur.fetchall()
        else:
            state_clause = "AND state = %s " if state is not None else ""
            params = (
                (q, q, q, state, limit, offset)
                if state is not None
                else (q, q, q, limit, offset)
            )
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs '
                        "WHERE (id ILIKE %s "
                        "OR payload->>'filename_hint' ILIKE %s "
                        "OR payload->>'input_sha256' ILIKE %s) "
                        f"{state_clause}"
                        "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                        params,
                    )
                    rows = await cur.fetchall()
        return self._rows_to_payloads(rows)

    async def state_counts(self) -> dict[str, int]:
        """Returns the count of jobs per state. Used by the UI to surface
        a summary banner so users can navigate large queues by state."""
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT state, COUNT(*) FROM jobs GROUP BY state"
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT state, COUNT(*) FROM "{self._schema}".jobs '
                        "GROUP BY state"
                    )
                    rows = await cur.fetchall()
        return {state: int(count) for state, count in rows}

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        q = f"%{query}%"
        if self._dialect == "sqlite":
            # Match on id + filename_hint + input_sha256 only — no full
            # payload scan (see Postgres branch below for the rationale).
            async with self._aiosqlite_conn.execute(
                "SELECT payload FROM jobs "
                "WHERE id LIKE ? "
                "OR json_extract(payload, '$.filename_hint') LIKE ? "
                "OR json_extract(payload, '$.input_sha256') LIKE ? "
                "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (q, q, q, limit, offset),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    # Match on id + filename_hint + input_sha256. The earlier
                    # `OR payload::text ILIKE %s` clause forced a seq scan
                    # with a text cast on every row's jsonb — 37s @ 3.9 k
                    # rows in prod (UI fetch times out → "failed to fetch").
                    # These three scalar fields cover the common search use
                    # cases; full-payload search (QR URLs, OCR text) would
                    # need a pg_trgm GIN index — add when actually required.
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs '
                        "WHERE id ILIKE %s "
                        "OR payload->>'filename_hint' ILIKE %s "
                        "OR payload->>'input_sha256' ILIKE %s "
                        "ORDER BY submitted_at DESC LIMIT %s OFFSET %s",
                        (q, q, q, limit, offset),
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

    # ── similarity index ─────────────────────────────────────────────────────

    @staticmethod
    def _phash_hex_to_int8(hex_str: str) -> int:
        """Signed int64 cast for a 16-char hex pHash. Mirrors the
        clippyshot conversion so the same hex string maps to the same
        int8 across the two projects."""
        val = int(hex_str, 16)
        if val >= 1 << 63:
            val -= 1 << 64
        return val

    @staticmethod
    def _int8_to_phash_hex(v: int) -> str:
        return f"{v & ((1 << 64) - 1):016x}"

    async def index_entries(self, record: JobRecord) -> int:
        """Populate entry_hashes for a succeeded job. Idempotent — repeat
        calls upsert. Returns the number of rows indexed."""
        if record.result is None:
            return 0
        rows = []
        now = datetime.now(UTC).isoformat() if self._dialect == "sqlite" \
            else datetime.now(UTC)
        for entry in record.result.extraction.entries:
            ph_hex = entry.phash
            ch = entry.colorhash
            sha = entry.sha256
            if not (ph_hex or ch or sha):
                continue
            try:
                ph_int = self._phash_hex_to_int8(ph_hex) if ph_hex else None
            except ValueError:
                ph_int = None
            rows.append({
                "job_id": record.id,
                "entry_path": entry.path,
                "phash": ph_int,
                "colorhash": ch,
                "sha256": sha,
                "filename": record.filename_hint,
                "content_type": entry.content_type,
                "indexed_at": now,
            })
        if not rows:
            return 0
        if self._dialect == "sqlite":
            await self._aiosqlite_conn.executemany(
                "INSERT INTO entry_hashes "
                "(job_id, entry_path, phash, colorhash, sha256, "
                " filename, content_type, indexed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(job_id, entry_path) DO UPDATE SET "
                "phash=excluded.phash, colorhash=excluded.colorhash, "
                "sha256=excluded.sha256, filename=excluded.filename, "
                "content_type=excluded.content_type, indexed_at=excluded.indexed_at",
                [tuple(r[k] for k in (
                    "job_id", "entry_path", "phash", "colorhash", "sha256",
                    "filename", "content_type", "indexed_at"
                )) for r in rows],
            )
            await self._aiosqlite_conn.commit()
        else:
            async with self._psycopg_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(
                        f'INSERT INTO "{self._schema}".entry_hashes '
                        "(job_id, entry_path, phash, colorhash, sha256, "
                        " filename, content_type, indexed_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (job_id, entry_path) DO UPDATE SET "
                        "phash=EXCLUDED.phash, colorhash=EXCLUDED.colorhash, "
                        "sha256=EXCLUDED.sha256, filename=EXCLUDED.filename, "
                        "content_type=EXCLUDED.content_type, "
                        "indexed_at=EXCLUDED.indexed_at",
                        [tuple(r[k] for k in (
                            "job_id", "entry_path", "phash", "colorhash", "sha256",
                            "filename", "content_type", "indexed_at"
                        )) for r in rows],
                    )
                await conn.commit()
        return len(rows)

    async def find_similar_phash(
        self, target_int8: int, max_distance: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return rows whose phash is within ``max_distance`` Hamming bits of
        target. On Postgres uses bit_count for fast distance computation;
        on SQLite falls back to in-memory popcount over the full table."""
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT job_id, entry_path, phash, colorhash, sha256, "
                "filename, content_type FROM entry_hashes WHERE phash IS NOT NULL"
            ) as cur:
                rows = await cur.fetchall()
            out = []
            for r in rows:
                ph = r[2]
                if ph is None:
                    continue
                dist = bin((ph ^ target_int8) & ((1 << 64) - 1)).count("1")
                if dist <= max_distance:
                    out.append({
                        "job_id": r[0], "entry_path": r[1],
                        "phash": ph, "colorhash": r[3], "sha256": r[4],
                        "filename": r[5], "content_type": r[6],
                        "distance": dist,
                    })
            out.sort(key=lambda x: (x["distance"], x["job_id"], x["entry_path"]))
            return out[:limit]
        # Postgres
        async with self._psycopg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f'SELECT job_id, entry_path, phash, colorhash, sha256, '
                    f'filename, content_type, '
                    f"bit_count((phash # %s::int8)::bit(64)) AS distance "
                    f'FROM "{self._schema}".entry_hashes '
                    f"WHERE phash IS NOT NULL "
                    f"AND bit_count((phash # %s::int8)::bit(64)) <= %s "
                    f"ORDER BY distance, job_id, entry_path LIMIT %s",
                    (target_int8, target_int8, max_distance, limit),
                )
                cols = [d.name for d in cur.description]
                rows = [dict(zip(cols, row, strict=False)) for row in await cur.fetchall()]
        return rows

    async def find_by_colorhash(
        self, colorhash: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Exact-match colorhash lookup."""
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT job_id, entry_path, phash, colorhash, sha256, "
                "filename, content_type FROM entry_hashes "
                "WHERE colorhash = ? ORDER BY job_id, entry_path LIMIT ?",
                (colorhash, limit),
            ) as cur:
                rows = await cur.fetchall()
            keys = ("job_id", "entry_path", "phash", "colorhash", "sha256",
                    "filename", "content_type")
            return [dict(zip(keys, r, strict=False)) for r in rows]
        async with self._psycopg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f'SELECT job_id, entry_path, phash, colorhash, sha256, '
                    f'filename, content_type FROM "{self._schema}".entry_hashes '
                    f"WHERE colorhash = %s ORDER BY job_id, entry_path LIMIT %s",
                    (colorhash, limit),
                )
                cols = [d.name for d in cur.description]
                return [dict(zip(cols, row, strict=False)) for row in await cur.fetchall()]

    async def find_by_sha256(
        self, sha256: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Exact-match SHA-256 lookup."""
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(
                "SELECT job_id, entry_path, phash, colorhash, sha256, "
                "filename, content_type FROM entry_hashes "
                "WHERE sha256 = ? ORDER BY job_id, entry_path LIMIT ?",
                (sha256, limit),
            ) as cur:
                rows = await cur.fetchall()
            keys = ("job_id", "entry_path", "phash", "colorhash", "sha256",
                    "filename", "content_type")
            return [dict(zip(keys, r, strict=False)) for r in rows]
        async with self._psycopg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f'SELECT job_id, entry_path, phash, colorhash, sha256, '
                    f'filename, content_type FROM "{self._schema}".entry_hashes '
                    f"WHERE sha256 = %s ORDER BY job_id, entry_path LIMIT %s",
                    (sha256, limit),
                )
                cols = [d.name for d in cur.description]
                return [dict(zip(cols, row, strict=False)) for row in await cur.fetchall()]
