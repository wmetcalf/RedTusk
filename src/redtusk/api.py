"""RedTusk FastAPI application."""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import os
import re
import tempfile
import unicodedata
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pyzipper  # type: ignore[import-untyped]
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.formparsers import MultiPartException

from redtusk._version import __version__
from redtusk.dispatcher import Dispatcher, artifact_dir
from redtusk.errors import (
    JobNotFoundError,
    PoolExhaustedError,
    SchemaValidationError,
    WorkerError,
)
from redtusk.jobs.base import JobStore
from redtusk.limits import Limits
from redtusk.observability.logging import get_logger
from redtusk.observability.metrics import render_for_endpoint
from redtusk.translation import (
    to_detect_text,
    to_language_text,
    to_meta_json,
    to_rmeta_json,
    to_tika_text,
    to_unpack_tar,
)
from redtusk.types import ExtractResult, JobRecord, JobState

if TYPE_CHECKING:
    pass

_logger = get_logger(__name__)
_STATIC = Path(__file__).parent / "static"
_BAD_FILENAME_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f\xad]")

# Bounds concurrent infected-zip builds. Each build AES-encrypts up to ~1 GiB
# of artifacts (CPU + disk heavy); without a cap an unauthenticated burst could
# exhaust the box. Mirrors the similarity endpoint's concurrency gate.
_INFECTED_ZIP_SEMAPHORE = asyncio.Semaphore(2)


def _load_ui() -> str:
    return (_STATIC / "index.html").read_text(encoding="utf-8")


# ── Static stubs ──────────────────────────────────────────────────────────────

MIME_TYPES_STUB: dict[str, Any] = {
    "application/pdf": {"alias": [], "supertype": "application/octet-stream"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "alias": ["application/x-docx"],
        "supertype": "application/zip",
    },
    "text/plain": {"alias": ["text/x-plain"], "supertype": "text/plain"},
    "image/jpeg": {"alias": ["image/jpg"], "supertype": "image/jpeg"},
    "image/png": {"alias": [], "supertype": "image/png"},
    "application/zip": {
        "alias": ["application/x-zip"],
        "supertype": "application/octet-stream",
    },
    "application/vnd.ms-excel": {"alias": [], "supertype": "application/octet-stream"},
    "application/vnd.ms-powerpoint": {
        "alias": [],
        "supertype": "application/octet-stream",
    },
    "text/html": {"alias": ["text/x-html"], "supertype": "text/plain"},
    "message/rfc822": {"alias": [], "supertype": "application/octet-stream"},
}

PARSERS_STUB: dict[str, Any] = {
    "name": "org.apache.tika.parser.AutoDetectParser",
    "composite": True,
    "children": [
        {
            "name": "org.apache.tika.parser.pdf.PDFParser",
            "composite": False,
            "children": [],
        },
        {
            "name": "org.apache.tika.parser.microsoft.OfficeParser",
            "composite": False,
            "children": [],
        },
        {
            "name": "org.apache.tika.parser.odf.OpenDocumentParser",
            "composite": False,
            "children": [],
        },
        {
            "name": "org.apache.tika.parser.image.ImageParser",
            "composite": False,
            "children": [],
        },
        {
            "name": "org.apache.tika.parser.txt.TXTParser",
            "composite": False,
            "children": [],
        },
    ],
}


# ── Application factory ───────────────────────────────────────────────────────


def create_app(
    dispatcher: Dispatcher,
    store: JobStore,
    limits: Limits,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        await app.state.dispatcher.start()
        yield
        await app.state.dispatcher.stop()

    app = FastAPI(
        title="RedTusk",
        version=__version__,
        # Swagger/ReDoc and the OpenAPI schema are withheld unless explicitly
        # enabled (REDTUSK_EXPOSE_DOCS=true) — a malware-processing service
        # shouldn't publish its API surface by default. When off, /openapi.json
        # is suppressed too (previously it leaked even with the UIs disabled).
        docs_url="/docs" if limits.expose_docs else None,
        redoc_url="/redoc" if limits.expose_docs else None,
        openapi_url="/openapi.json" if limits.expose_docs else None,
        lifespan=lifespan,
    )
    app.state.dispatcher = dispatcher
    app.state.store = store
    app.state.limits = limits
    _register_routes(app)
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
    return app


# ── Upload helper ─────────────────────────────────────────────────────────────


def _sanitize_filename(raw_name: str | None) -> str:
    raw = raw_name or "upload"
    # Normalize unicode (NFC) and strip combining/invisible/private-use categories
    raw = unicodedata.normalize("NFC", raw)
    raw = "".join(
        c for c in raw if unicodedata.category(c) not in {"Cc", "Cf", "Co", "Cn"}
    )
    filename = Path(raw.replace("\\", "/")).name or "upload"
    filename = _BAD_FILENAME_CHARS.sub("", filename).strip()[:200]
    if filename in {"", ".", ".."}:
        return "upload"
    return filename


async def _read_upload(request: Request) -> tuple[bytes, str]:
    """Read request body. Return (body_bytes, filename_hint).

    Handles both raw binary bodies (Tika-compat PUT endpoints) and
    multipart/form-data (curl -F, browser form) — the latter carries the
    real filename in the part headers, not the top-level HTTP headers.

    Raises HTTPException(413) if body exceeds limits.max_input.
    """
    limits: Limits = request.app.state.limits
    ct = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > limits.max_input:
                raise HTTPException(status_code=413, detail="Request body too large")
        except ValueError:
            pass

    if ct.startswith("multipart/form-data"):
        # Bound the bytes buffered by the form parser so a client cannot force
        # us to read an unbounded body into memory before the size check below.
        # A missing/invalid Content-Length means the early check above was
        # skipped, so this streaming cap is the only guard — always apply it.
        try:
            form = await request.form(max_part_size=limits.max_input + 1)
        except MultiPartException as exc:
            raise HTTPException(
                status_code=413, detail="Request body too large"
            ) from exc
        # Try common field names; fall back to first field present
        file_field = None
        for name in ("file", "upload", "data", "document"):
            if name in form:
                file_field = form[name]
                break
        if file_field is None:
            vals = list(form.values())
            file_field = vals[0] if vals else None
        if file_field is None:
            raise HTTPException(status_code=400, detail="No file in multipart form")
        body = await file_field.read()  # type: ignore[union-attr]
        if len(body) > limits.max_input:
            raise HTTPException(status_code=413, detail="Request body too large")
        raw_name = getattr(file_field, "filename", None) or "upload"
        filename = _sanitize_filename(raw_name)
        return body, filename

    # Raw binary body (Tika-compat PUT or direct POST with Content-Disposition)
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limits.max_input:
            raise HTTPException(status_code=413, detail="Request body too large")
        chunks.append(chunk)
    body = b"".join(chunks)

    cd = request.headers.get("content-disposition", "")
    filename = "upload"
    if "filename=" in cd:
        part = cd.split("filename=", 1)[1].strip().strip('"').strip("'")
        filename = part.split(";")[0].strip() or "upload"
    filename = _sanitize_filename(filename)
    return body, filename


# ── Sync runner helper ────────────────────────────────────────────────────────


def _apply_per_request_limits(limits: Limits, request: Request) -> Limits:
    """Return a Limits copy with per-request overrides from query params."""
    overrides: dict[str, object] = {}
    p = request.query_params

    truthy = ("1", "true", "yes", "on")
    falsey = ("0", "false", "no", "off")

    def flag(name: str) -> bool | None:
        v = p.get(name)
        if v is None:
            return None
        normalized = v.strip().lower()
        if normalized in truthy:
            return True
        if normalized in falsey:
            return False
        # Reject malformed values rather than silently coercing them to True.
        raise HTTPException(
            status_code=400,
            detail=f"invalid boolean value for query parameter '{name}'",
        )

    def clamp_int(name: str, lo: int, hi: int) -> int | None:
        v = p.get(name)
        if v is None:
            return None
        try:
            parsed = int(v)
        except (TypeError, ValueError) as exc:
            # Reject malformed values rather than silently ignoring them.
            raise HTTPException(
                status_code=400,
                detail=f"invalid integer value for query parameter '{name}'",
            ) from exc
        return max(lo, min(hi, parsed))

    for fname in ("enable_qr", "enable_ocr", "enable_thumbnails"):
        val = flag(fname)
        if val is not None:
            overrides[fname] = val

    depth = clamp_int("max_recursion_depth", 1, 50)
    if depth is not None:
        overrides["max_recursion_depth"] = depth

    # Cap the client override at the operator's configured ceiling (not a
    # hardcoded 10000, which let a client raise it to 2x the operator default and
    # defeat that knob). 10000 stays as an absolute upper bound.
    entries = clamp_int("max_embedded_entries", 1, min(limits.max_embedded_entries, 10000))
    if entries is not None:
        overrides["max_embedded_entries"] = entries

    return dataclasses.replace(limits, **overrides) if overrides else limits  # type: ignore[arg-type]


async def _run_sync(request: Request) -> ExtractResult:
    """Read upload, dispatch synchronously, return ExtractResult.

    Maps errors to HTTP responses.
    """
    dispatcher: Dispatcher = request.app.state.dispatcher
    limits: Limits = _apply_per_request_limits(request.app.state.limits, request)
    body, filename = await _read_upload(request)
    try:
        return await dispatcher.submit_sync(body, filename, limits)
    except PoolExhaustedError as exc:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily overloaded",
            headers={"Retry-After": "5"},
        ) from exc
    except (WorkerError, SchemaValidationError) as exc:
        # Log the full error server-side, but return a generic detail to the
        # client — schema pointers, exit codes and SHA-256 internals must not
        # leak to unauthenticated callers.
        _logger.warning("api.sync_error", error=str(exc))
        raise HTTPException(status_code=502, detail="extraction failed") from exc


# ── List-view summary ─────────────────────────────────────────────────────────


def _job_summary(record: JobRecord) -> dict[str, Any]:
    """Return a lightweight job dict for the list view.

    The full result (extraction entries, OCR text, etc.) is omitted — it can
    be 100s of KB per job, making 200-job list responses far too large for the
    browser to parse. Callers that need the full result fetch individual jobs.
    Computed summary counters (qr_count, entry_count, has_ocr) are added so
    the table can still show useful badges without the full payload.
    """
    qr_count = 0
    entry_count = 0
    has_ocr = False
    if record.result:
        entries = record.result.extraction.entries
        entry_count = len(entries)
        for e in entries:
            qr_count += len(e.qr.codes)
            if e.ocr.text:
                has_ocr = True
    d = record.to_dict()
    d.pop("input_path", None)  # internal host path, not for API consumers
    d["result"] = None  # strip heavy payload
    d["qr_count"] = qr_count
    d["entry_count"] = entry_count
    d["has_ocr"] = has_ocr
    # queue_ms and processing_ms are already computed in to_dict(); keep them.
    return d


def _summary_from_payload(d: dict[str, Any]) -> dict[str, Any]:
    """Lightweight list-view summary built directly from a raw payload dict —
    skips the ``JobRecord.from_dict`` reconstruction that dominates wall time
    on heavy results (200 large xml/docx payloads = 20+ s of attr-by-attr
    rebuild we throw away when we set result=None).

    Same output shape as ``_job_summary`` — kept in lockstep so the UI doesn't
    care which path produced it.
    """
    qr_count = 0
    entry_count = 0
    has_ocr = False
    result = d.get("result")
    if result:
        entries = (result.get("extraction") or {}).get("entries") or []
        entry_count = len(entries)
        for e in entries:
            qr_count += len((e.get("qr") or {}).get("codes") or [])
            if (e.get("ocr") or {}).get("text"):
                has_ocr = True

    # Derived timing metrics — same formulae as JobRecord.to_dict(), recomputed
    # from the ISO-8601 strings. fromisoformat is fast (~µs); the round-trip
    # via JobRecord would also have parsed datetimes here, just with all the
    # nested-result reconstruction tacked on for no reason in the list view.
    def _parse(ts: str | None) -> datetime | None:
        if not ts:
            return None
        from datetime import datetime
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            # A corrupted/legacy row with a malformed timestamp must not 500
            # the whole list endpoint — treat it as missing.
            return None

    submitted = _parse(d.get("submitted_at"))
    started = _parse(d.get("started_at"))
    worker_started = _parse(d.get("worker_started_at"))
    completed = _parse(d.get("completed_at"))

    queue_ms = pool_wait_ms = processing_ms = parse_ms = None
    if submitted and started:
        queue_ms = int((started - submitted).total_seconds() * 1000)
    if started and worker_started:
        pool_wait_ms = int((worker_started - started).total_seconds() * 1000)
    if completed:
        anchor = worker_started or started
        if anchor:
            processing_ms = int((completed - anchor).total_seconds() * 1000)
    if result:
        try:
            parse_ms = int(result["extraction"]["duration_ms"])
        except (KeyError, TypeError, ValueError):
            parse_ms = None

    return {
        "id": d.get("id"),
        "state": d.get("state"),
        "submitted_at": d.get("submitted_at"),
        "started_at": d.get("started_at"),
        "worker_started_at": d.get("worker_started_at"),
        "completed_at": d.get("completed_at"),
        "queue_ms": queue_ms,
        "pool_wait_ms": pool_wait_ms,
        "processing_ms": processing_ms,
        "parse_ms": parse_ms,
        "input_sha256": d.get("input_sha256"),
        "input_size_bytes": d.get("input_size_bytes"),
        "filename_hint": d.get("filename_hint"),
        "result": None,  # heavy payload stripped — fetch per-job for details
        "error_code": d.get("error_code"),
        "error_detail": d.get("error_detail"),
        "qr_count": qr_count,
        "entry_count": entry_count,
        "has_ocr": has_ocr,
    }


# ── Route registration ────────────────────────────────────────────────────────


def _register_routes(app: FastAPI) -> None:
    # ── Tika-compat ──────────────────────────────────────────────

    @app.put("/tika")
    async def put_tika(request: Request) -> PlainTextResponse:
        return PlainTextResponse(to_tika_text(await _run_sync(request)))

    @app.put("/tika/form")
    async def put_tika_form(request: Request) -> PlainTextResponse:
        return PlainTextResponse(to_tika_text(await _run_sync(request)))

    @app.put("/rmeta")
    async def put_rmeta(request: Request) -> JSONResponse:
        return JSONResponse(to_rmeta_json(await _run_sync(request)))

    @app.put("/rmeta/text")
    async def put_rmeta_text(request: Request) -> JSONResponse:
        return JSONResponse(to_rmeta_json(await _run_sync(request)))

    @app.put("/rmeta/html")
    async def put_rmeta_html(request: Request) -> JSONResponse:
        return JSONResponse(to_rmeta_json(await _run_sync(request)))

    @app.put("/rmeta/xml")
    async def put_rmeta_xml(request: Request) -> JSONResponse:
        return JSONResponse(to_rmeta_json(await _run_sync(request)))

    @app.put("/meta")
    async def put_meta(request: Request) -> JSONResponse:
        return JSONResponse(to_meta_json(await _run_sync(request)))

    @app.put("/detect/stream")
    async def put_detect(request: Request) -> PlainTextResponse:
        return PlainTextResponse(to_detect_text(await _run_sync(request)))

    @app.put("/language/stream")
    async def put_language(request: Request) -> PlainTextResponse:
        return PlainTextResponse(to_language_text(await _run_sync(request)))

    @app.put("/unpack")
    async def put_unpack(request: Request) -> Response:
        result = await _run_sync(request)
        tar_bytes = to_unpack_tar(result, include_root=False)
        return Response(
            content=tar_bytes,
            media_type="application/x-tar",
            headers={"Warning": '299 - "unpack-bytes-unavailable"'},
        )

    @app.put("/unpack/all")
    async def put_unpack_all(request: Request) -> Response:
        result = await _run_sync(request)
        tar_bytes = to_unpack_tar(result, include_root=True)
        return Response(
            content=tar_bytes,
            media_type="application/x-tar",
            headers={"Warning": '299 - "unpack-bytes-unavailable"'},
        )

    @app.get("/version")
    async def get_version() -> PlainTextResponse:
        return PlainTextResponse(f"Apache Tika - RedTusk {__version__}")

    @app.get("/mime-types")
    async def get_mime_types() -> JSONResponse:
        return JSONResponse(MIME_TYPES_STUB)

    @app.get("/parsers")
    async def get_parsers() -> JSONResponse:
        return JSONResponse(PARSERS_STUB)

    @app.get("/parsers/details")
    async def get_parsers_details() -> JSONResponse:
        return JSONResponse(PARSERS_STUB)

    # ── /v1/convert (sync, native result) ────────────────────────

    @app.post("/v1/convert")
    async def convert_sync(request: Request) -> JSONResponse:
        """Synchronous extraction: block until done, return full ExtractResult JSON.

        Query params: enable_qr=true/false, enable_ocr=true/false
        """
        result = await _run_sync(request)
        return JSONResponse(result.to_dict())

    # ── /v1/jobs ──────────────────────────────────────────────────

    @app.post("/v1/jobs", status_code=202)
    async def create_job(request: Request) -> JSONResponse:
        store: JobStore = request.app.state.store
        limits: Limits = request.app.state.limits
        body, filename = await _read_upload(request)
        sha256 = hashlib.sha256(body).hexdigest()
        job_id = str(uuid4())

        # Stage input to artifact_root/{job_id}/pending/{filename}
        pending_dir = Path(limits.artifact_root) / job_id[:2] / job_id / "pending"
        await asyncio.to_thread(pending_dir.mkdir, parents=True, exist_ok=True)
        input_path = pending_dir / filename
        await asyncio.to_thread(input_path.write_bytes, body)

        record = JobRecord(
            id=job_id,
            state=JobState.QUEUED,
            submitted_at=datetime.now(UTC),
            started_at=None,
            completed_at=None,
            input_sha256=sha256,
            input_size_bytes=len(body),
            filename_hint=filename,
            result=None,
            error_code=None,
            error_detail=None,
            input_path=str(input_path),
        )
        await store.create(record)
        return JSONResponse(record.to_dict(), status_code=202)

    @app.get("/v1/jobs/counts")
    async def job_counts(request: Request) -> JSONResponse:
        """Counts of jobs per state. Backs the UI's state-filter pills so
        users can navigate large queues without scrolling through hundreds
        of queued rows. Registered BEFORE /v1/jobs/{job_id} so the literal
        path wins over the path-param route."""
        store: JobStore = request.app.state.store
        method = getattr(store, "state_counts", None)
        if method is None:
            return JSONResponse({"counts": {}})
        counts = await method()
        return JSONResponse({"counts": counts})

    @app.get("/v1/jobs/{job_id}")
    async def get_job(job_id: str, request: Request) -> JSONResponse:
        store: JobStore = request.app.state.store
        record = await store.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Job not found")
        d = record.to_dict()
        d.pop("input_path", None)
        return JSONResponse(d)

    @app.delete("/v1/jobs/{job_id}", status_code=204)
    async def delete_job(job_id: str, request: Request) -> Response:
        store: JobStore = request.app.state.store
        limits: Limits = request.app.state.limits
        try:
            deleted = await store.delete(job_id)
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        if not deleted:
            raise HTTPException(status_code=409, detail="Job is not in terminal state")

        import shutil

        art_dir = artifact_dir(limits.artifact_root, job_id)
        await asyncio.to_thread(shutil.rmtree, art_dir, ignore_errors=True)
        return Response(status_code=204)

    @app.get("/v1/jobs")
    async def list_jobs(
        request: Request, limit: int = 50, offset: int = 0, q: str = "",
        state: str = ""
    ) -> JSONResponse:
        store: JobStore = request.app.state.store
        capped_limit = max(1, min(limit, 200))
        offset = max(0, offset)
        state_filter = state.strip().lower() if state else None
        if state_filter and state_filter not in (
                "queued", "running", "succeeded", "failed"):
            raise HTTPException(400, "state must be one of: queued, running, succeeded, failed")
        # Use the raw-payload variants — see _summary_from_payload for the
        # rationale (skipping JobRecord.from_dict shaves ~20 s off 200-row
        # responses when the rows have heavy extraction trees).
        if q.strip():
            payloads = await store.search_payloads(
                q.strip(), limit=capped_limit, offset=offset, state=state_filter)
        else:
            payloads = await store.list_recent_payloads(
                limit=capped_limit, offset=offset, state=state_filter)
        has_more = len(payloads) == capped_limit
        return JSONResponse({
            "jobs": [_summary_from_payload(p) for p in payloads],
            "has_more": has_more,
        })


    # Similarity gate — same idea as clippyshot. Fuzzy phash queries with
    # large max_hamming can sequentially scan entry_hashes; cap concurrency
    # so an unauthenticated burst can't pin Postgres.
    _similar_gate = asyncio.Semaphore(3)

    @app.get("/v1/similar")
    async def find_similar(
        request: Request,
        phash: str | None = None,
        colorhash: str | None = None,
        sha256: str | None = None,
        max_hamming: int = 5,
        limit: int = 50,
    ) -> JSONResponse:
        """Find entries with similar perceptual/cryptographic hashes.

        - phash: 16-char hex. Returns entries within ``max_hamming`` Hamming
          bits (0-64; default 5).
        - colorhash: 14-char hex; exact match.
        - sha256: 64-char hex; exact match.

        Exactly one of phash / colorhash / sha256 must be provided.
        """
        provided = [p for p in (phash, colorhash, sha256) if p]
        if len(provided) != 1:
            raise HTTPException(400, "provide exactly one of phash, colorhash, sha256")
        if limit < 1 or limit > 500:
            raise HTTPException(400, "limit must be in [1, 500]")
        store: JobStore = request.app.state.store
        if phash:
            if not re.fullmatch(r"[0-9a-fA-F]{16}", phash):
                raise HTTPException(400, "phash must be 16 hex chars")
            if not (0 <= max_hamming <= 64):
                raise HTTPException(400, "max_hamming must be in [0, 64]")
            method = getattr(store, "find_similar_phash", None)
            if method is None:
                raise HTTPException(
                    501, "current store does not support similarity search"
                )
            # Local helper — mirrors SqlJobStore._phash_hex_to_int8.
            val = int(phash, 16)
            target_int8 = val - (1 << 64) if val >= (1 << 63) else val
            async with _similar_gate:
                rows = await method(target_int8, max_hamming, limit=limit)
        elif colorhash:
            if not re.fullmatch(r"[0-9a-fA-F]{14}", colorhash):
                raise HTTPException(400, "colorhash must be 14 hex chars")
            method = getattr(store, "find_by_colorhash", None)
            if method is None:
                raise HTTPException(
                    501, "current store does not support colorhash lookup"
                )
            async with _similar_gate:
                rows = await method(colorhash, limit=limit)
        else:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256 or ""):
                raise HTTPException(400, "sha256 must be 64 hex chars")
            method = getattr(store, "find_by_sha256", None)
            if method is None:
                raise HTTPException(
                    501, "current store does not support sha256 lookup"
                )
            async with _similar_gate:
                rows = await method(sha256, limit=limit)
        # Normalise phash int8 -> hex for the response so clients see the
        # same string they queried with.
        out = []
        for r in rows:
            ph = r.get("phash")
            r_out = dict(r)
            if isinstance(ph, int):
                r_out["phash"] = f"{ph & ((1 << 64) - 1):016x}"
            out.append(r_out)
        return JSONResponse({"matches": out, "count": len(out)})

    @app.get("/v1/jobs/{job_id}/artifacts/{artifact_name:path}")
    async def get_artifact(
        job_id: str, artifact_name: str, request: Request
    ) -> Response:
        store: JobStore = request.app.state.store
        limits: Limits = request.app.state.limits
        record = await store.get(job_id)
        if record is None or record.state != JobState.SUCCEEDED:
            raise HTTPException(status_code=404, detail="Artifact not found")
        art_dir = artifact_dir(limits.artifact_root, job_id)
        art_path = (art_dir / artifact_name).resolve()
        # Path traversal guard
        try:
            art_path.relative_to(art_dir.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found") from exc
        if not art_path.exists() or not art_path.is_file():
            raise HTTPException(status_code=404, detail="Artifact not found")
        content = await asyncio.to_thread(art_path.read_bytes)
        return Response(content=content, media_type="application/octet-stream")

    @app.get("/v1/jobs/{job_id}/infected-zip")
    async def download_infected_zip(job_id: str, request: Request) -> Response:
        """Return a password-protected zip of all job artifacts.

        Password is the standard threat-intel convention: ``infected``.
        The zip contains metadata.json plus any extracted embedded files.
        """
        store: JobStore = request.app.state.store
        limits: Limits = request.app.state.limits
        record = await store.get(job_id)
        if record is None or record.state != JobState.SUCCEEDED:
            raise HTTPException(
                status_code=404, detail="Job not found or not succeeded"
            )

        art_dir = artifact_dir(limits.artifact_root, job_id)

        def _build_zip(tmp_path: str) -> None:
            source_bytes = 0
            with pyzipper.AESZipFile(
                tmp_path,
                "w",
                compression=pyzipper.ZIP_DEFLATED,
                encryption=pyzipper.WZ_AES,
            ) as zf:
                zf.setpassword(b"infected")
                for p in sorted(art_dir.rglob("*")):
                    if p.is_file() and "pending" not in p.parts:
                        source_bytes += p.stat().st_size
                        if source_bytes > limits.max_infected_zip_source_bytes:
                            raise ValueError(
                                "infected zip source artifacts too large: "
                                f"{source_bytes} > {limits.max_infected_zip_source_bytes}"
                            )
                        arcname = p.relative_to(art_dir)
                        zf.write(p, arcname)

        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp_path = tmp.name
            import asyncio
            async with _INFECTED_ZIP_SEMAPHORE:
                await asyncio.to_thread(_build_zip, tmp_path)
        except ValueError as exc:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except Exception as exc:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise HTTPException(status_code=500, detail="Failed to build zip") from exc

        filename = f"redtusk-{job_id[:8]}.zip"
        
        def _cleanup() -> None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return FileResponse(
            path=tmp_path,
            media_type="application/zip",
            filename=filename,
            background=BackgroundTask(_cleanup)
        )

    # ── Ops ───────────────────────────────────────────────────────

    @app.get("/v1/readyz")
    async def readyz(request: Request) -> JSONResponse:
        dispatcher: Dispatcher = request.app.state.dispatcher
        if dispatcher.is_healthy():
            return JSONResponse({"status": "ok"})
        body: dict[str, str] = {"status": "degraded"}
        fatal = dispatcher.fatal_spawn_error
        if fatal:
            # Surface the actionable remediation (e.g. the -XX:CPUFeatures value to
            # rebuild with) as the dominant signal rather than a bare "degraded".
            body["detail"] = fatal
        return JSONResponse(body, status_code=503)

    @app.get("/metrics")
    async def metrics_endpoint() -> Response:
        body, content_type = render_for_endpoint()
        return Response(content=body, media_type=content_type)

    security_headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": (
            # script-src drops 'unsafe-inline': all JS is served from the
            # external /static/app.js bundle and inline on* handlers have been
            # replaced by delegated listeners. style-src keeps 'unsafe-inline'
            # for the remaining inline style="" attributes (style injection is
            # far lower risk than script execution); the bundle is /static/app.css.
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        ),
        "Referrer-Policy": "no-referrer",
    }

    # Swagger UI / ReDoc load their JS+CSS bundle and an inline init script from
    # jsdelivr; the strict app CSP (script-src 'self') blanks the page. Relax the
    # CSP for the opt-in, internal /docs + /redoc routes only — same-origin
    # /openapi.json fetch stays covered by connect-src 'self'.
    docs_csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "worker-src 'self' blob:; "
        "connect-src 'self'"
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        path = request.url.path
        is_static = path.startswith("/static/")
        is_docs = path in ("/docs", "/redoc")
        for k, v in security_headers.items():
            if k == "Content-Security-Policy" and is_docs:
                response.headers.setdefault(k, docs_csp)
            elif is_static and k == "Cache-Control":
                # Non-versioned code bundles (app.js/app.css) must revalidate so a
                # deploy propagates without a hard refresh — the ETag StaticFiles
                # sets makes this a cheap conditional 304 when unchanged. Other
                # assets (logo, favicon, fonts) are content-stable → cache a day.
                if path.endswith((".js", ".css")):
                    response.headers.setdefault(k, "no-cache")
                else:
                    response.headers.setdefault(k, "public, max-age=86400")
            else:
                response.headers.setdefault(k, v)
        return response

    @app.get("/")
    async def ui() -> HTMLResponse:
        return HTMLResponse(
            content=await asyncio.to_thread(_load_ui),
        )

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    async def ui_job_detail(job_id: str) -> HTMLResponse:
        """SPA route — serves the same index.html as ``/``; client-side JS
        reads ``window.location.pathname`` and dispatches to the dedicated
        job-detail view. Lets users deep-link / share / bookmark a specific
        job without the synthetic-row-in-the-list gymnastics the old
        ``?job=<id>`` deep link required."""
        # Validate the path param looks like a UUID-ish id; reject anything
        # else with 404 so we don't quietly serve the UI for typos that the
        # JS would then 404 on the API anyway.
        if not all(c.isalnum() or c == "-" for c in job_id) or len(job_id) > 64:
            raise HTTPException(status_code=404, detail="Not found")
        return HTMLResponse(
            content=await asyncio.to_thread(_load_ui),
        )
