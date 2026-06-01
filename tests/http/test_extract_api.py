"""Tests for /v1/convert (sync extract) hardening:

- generic client-facing error detail on worker/schema failure (no leak)
- multipart upload size cap enforced without unbounded buffering
- strict query-param coercion (malformed -> HTTP 400)

These build their own app via a local helper (no shared fixtures) so the
dispatcher/store behaviour is fully controlled per-test.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from redtusk.api import create_app
from redtusk.errors import SchemaValidationError, WorkerError
from redtusk.limits import Limits
from redtusk.types import ExtractResult


def _make_app(*, max_input: int = 536870912, side=None):
    dispatcher = MagicMock()
    dispatcher.start = AsyncMock()
    dispatcher.stop = AsyncMock()
    dispatcher.is_healthy = MagicMock(return_value=True)
    if side is not None:
        dispatcher.submit_sync = AsyncMock(side_effect=side)
    else:
        result = MagicMock(spec=ExtractResult)
        result.to_dict = MagicMock(return_value={"ok": True})
        dispatcher.submit_sync = AsyncMock(return_value=result)

    store = MagicMock()
    store.create = AsyncMock()
    store.get = AsyncMock()
    store.list_recent_payloads = AsyncMock(return_value=[])
    store.search_payloads = AsyncMock(return_value=[])
    store.state_counts = AsyncMock(return_value={})

    app = create_app(
        dispatcher=dispatcher, store=store, limits=Limits(max_input=max_input)
    )
    return app, dispatcher


# ── Finding 2: verbose internal error disclosure ─────────────────────────────


def test_worker_error_detail_is_generic():
    app, dispatcher = _make_app(side=WorkerError("boom internal exit=9"))
    with TestClient(app) as client:
        resp = client.post("/v1/convert", content=b"data")
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    # Internal worker details (exit codes, etc.) must not leak to clients.
    assert detail == "extraction failed"
    assert "boom" not in detail
    assert "exit=9" not in detail


def test_schema_error_detail_is_generic():
    app, dispatcher = _make_app(
        side=SchemaValidationError("/a/b", "ptr-internal-detail")
    )
    with TestClient(app) as client:
        resp = client.post("/v1/convert", content=b"data")
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    # Schema pointers / internal validation details must not leak to clients.
    assert detail == "extraction failed"
    assert "ptr=/a/b" not in detail


# ── Finding 3: multipart upload size cap ─────────────────────────────────────


def test_oversized_multipart_upload_returns_413():
    app, dispatcher = _make_app(max_input=16)
    with TestClient(app) as client:
        files = {"file": ("big.bin", b"x" * 1024, "application/octet-stream")}
        resp = client.post("/v1/convert", files=files)
    assert resp.status_code == 413
    # The worker must never be reached for an oversized upload.
    assert not dispatcher.submit_sync.called


def test_normal_multipart_upload_succeeds():
    app, dispatcher = _make_app(max_input=4096)
    with TestClient(app) as client:
        files = {"file": ("small.bin", b"hello world", "application/octet-stream")}
        resp = client.post("/v1/convert", files=files)
    assert resp.status_code == 200
    assert dispatcher.submit_sync.called


# ── Finding 5: strict query-param coercion ───────────────────────────────────


def test_malformed_int_query_param_returns_400():
    app, dispatcher = _make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/convert?max_recursion_depth=abc", content=b"x")
    assert resp.status_code == 400
    # Rejected before the worker runs.
    assert not dispatcher.submit_sync.called


def test_malformed_bool_query_param_returns_400():
    app, dispatcher = _make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/convert?enable_ocr=banana", content=b"x")
    assert resp.status_code == 400
    assert not dispatcher.submit_sync.called


def test_valid_bool_query_param_accepted():
    app, dispatcher = _make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/convert?enable_ocr=false", content=b"x")
    assert resp.status_code == 200
