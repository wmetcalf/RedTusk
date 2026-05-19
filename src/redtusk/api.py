"""RedTusk FastAPI application."""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import io
import os
import tempfile
import re
import unicodedata
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pyzipper
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

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
        docs_url=None,
        redoc_url=None,
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
        form = await request.form()
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

    def flag(name: str) -> bool | None:
        v = p.get(name)
        return None if v is None else v.lower() not in ("0", "false", "no")

    def clamp_int(name: str, lo: int, hi: int) -> int | None:
        v = p.get(name)
        if v is None:
            return None
        try:
            return max(lo, min(hi, int(v)))
        except ValueError:
            return None

    for fname in ("enable_qr", "enable_ocr", "enable_thumbnails"):
        val = flag(fname)
        if val is not None:
            overrides[fname] = val

    depth = clamp_int("max_recursion_depth", 1, 50)
    if depth is not None:
        overrides["max_recursion_depth"] = depth

    entries = clamp_int("max_embedded_entries", 1, 10000)
    if entries is not None:
        overrides["max_embedded_entries"] = entries

    return dataclasses.replace(limits, **overrides) if overrides else limits


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
        _logger.warning("api.sync_error", error=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
        request: Request, limit: int = 50, offset: int = 0, q: str = ""
    ) -> JSONResponse:
        store: JobStore = request.app.state.store
        capped_limit = min(limit, 200)
        if q.strip():
            records = await store.search(q.strip(), limit=capped_limit, offset=offset)
        else:
            records = await store.list_recent(limit=capped_limit, offset=offset)
        has_more = len(records) == capped_limit
        return JSONResponse({"jobs": [_job_summary(r) for r in records], "has_more": has_more})

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
        return JSONResponse({"status": "degraded"}, status_code=503)

    @app.get("/metrics")
    async def metrics_endpoint() -> Response:
        body, content_type = render_for_endpoint()
        return Response(content=body, media_type=content_type)

    _SECURITY_HEADERS = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "style-src 'unsafe-inline'; "
            "script-src 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        ),
        "Referrer-Policy": "no-referrer",
    }

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        is_static = request.url.path.startswith("/static/")
        for k, v in _SECURITY_HEADERS.items():
            # Allow caching for immutable static assets (logo, favicon)
            if is_static and k == "Cache-Control":
                response.headers.setdefault(k, "public, max-age=86400, immutable")
            else:
                response.headers.setdefault(k, v)
        return response

    @app.get("/")
    async def ui() -> HTMLResponse:
        return HTMLResponse(
            content=await asyncio.to_thread(_load_ui),
        )
