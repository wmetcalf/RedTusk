"""Tests for tika-server compatible endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from redtusk.errors import PoolExhaustedError, WorkerError
from tests.http.conftest import minimal_extract_result


def test_put_tika_returns_text(client, mock_dispatcher):
    mock_dispatcher.submit_sync = AsyncMock(
        return_value=minimal_extract_result(text="extracted text here")
    )
    resp = client.put(
        "/tika",
        content=b"dummy file content",
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "extracted text here" in resp.text


def test_put_rmeta_returns_list(client, mock_dispatcher):
    resp = client.put(
        "/rmeta",
        content=b"dummy",
        headers={"Content-Type": "application/pdf"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "Content-Type" in data[0]


def test_put_meta_returns_dict(client, mock_dispatcher):
    resp = client.put("/meta", content=b"dummy")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Content-Type" in data


def test_put_detect_returns_content_type(client, mock_dispatcher):
    mock_dispatcher.submit_sync = AsyncMock(
        return_value=minimal_extract_result(content_type="application/pdf")
    )
    resp = client.put("/detect/stream", content=b"dummy")
    assert resp.status_code == 200
    assert "application/pdf" in resp.text


def test_put_language_returns_string(client, mock_dispatcher):
    resp = client.put("/language/stream", content=b"dummy")
    assert resp.status_code == 200
    assert isinstance(resp.text, str)


def test_put_unpack_returns_tar(client):
    resp = client.put("/unpack", content=b"dummy")
    assert resp.status_code == 200
    assert "x-tar" in resp.headers.get("content-type", "")
    assert "Warning" in resp.headers


def test_get_version_contains_tika(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert "Apache Tika" in resp.text


def test_get_mime_types_returns_dict(client):
    resp = client.get("/mime-types")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_parsers_returns_json(client):
    resp = client.get("/parsers")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data


def test_pool_exhausted_returns_503(client, mock_dispatcher):
    mock_dispatcher.submit_sync = AsyncMock(side_effect=PoolExhaustedError(30.0))
    resp = client.put("/tika", content=b"dummy")
    assert resp.status_code == 503
    assert "Retry-After" in resp.headers


def test_worker_error_returns_502(client, mock_dispatcher):
    mock_dispatcher.submit_sync = AsyncMock(side_effect=WorkerError("worker crashed"))
    resp = client.put("/tika", content=b"dummy")
    assert resp.status_code == 502


def test_body_too_large_returns_413(tmp_path):
    from fastapi.testclient import TestClient

    from redtusk.api import create_app
    from redtusk.limits import Limits

    small_limits = Limits(max_input=10, artifact_root=str(tmp_path))
    mock_d = MagicMock()
    mock_d.start = AsyncMock()
    mock_d.stop = AsyncMock()
    mock_d.is_healthy.return_value = True
    mock_s = MagicMock()
    mock_s.create = AsyncMock()
    mock_s.list_recent = AsyncMock(return_value=[])
    mock_s.count_by_state = AsyncMock(return_value=0)
    app = create_app(dispatcher=mock_d, store=mock_s, limits=small_limits)
    with TestClient(app) as c:
        resp = c.put("/tika", content=b"x" * 100)
    assert resp.status_code == 413
