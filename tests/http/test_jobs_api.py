"""Tests for /v1/jobs endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from redtusk.errors import JobNotFoundError
from redtusk.types import JobState
from tests.http.conftest import minimal_extract_result, minimal_job_record


def test_post_job_returns_202(client, mock_store):
    resp = client.post("/v1/jobs", content=b"file content",
                       headers={"Content-Disposition": 'attachment; filename="test.txt"'})
    assert resp.status_code == 202
    data = resp.json()
    assert "id" in data
    assert data["state"] == "queued"
    assert "input_sha256" in data
    assert data["filename_hint"] == "test.txt"
    assert "submitted_at" in data
    assert mock_store.create.called
    from redtusk.types import JobState
    created_record = mock_store.create.call_args[0][0]
    assert created_record.state == JobState.QUEUED
    assert created_record.input_sha256  # non-empty sha256


def test_get_job_found(client, mock_store):
    job = minimal_job_record(job_id="abc123")
    mock_store.get = AsyncMock(return_value=job)
    resp = client.get("/v1/jobs/abc123")
    assert resp.status_code == 200
    assert resp.json()["id"] == "abc123"


def test_get_job_not_found(client, mock_store):
    mock_store.get = AsyncMock(return_value=None)
    resp = client.get("/v1/jobs/nonexistent")
    assert resp.status_code == 404


def test_delete_terminal_job_returns_204(client, mock_store):
    mock_store.delete = AsyncMock(return_value=True)
    resp = client.delete("/v1/jobs/abc123")
    assert resp.status_code == 204


def test_delete_running_job_returns_409(client, mock_store):
    mock_store.delete = AsyncMock(return_value=False)
    resp = client.delete("/v1/jobs/abc123")
    assert resp.status_code == 409


def test_delete_nonexistent_job_returns_404(client, mock_store):
    mock_store.delete = AsyncMock(side_effect=JobNotFoundError("abc123"))
    resp = client.delete("/v1/jobs/abc123")
    assert resp.status_code == 404


def test_list_jobs_returns_jobs_key(client, mock_store):
    # The endpoint reads raw payload dicts via list_recent_payloads (see
    # _summary_from_payload), not JobRecord objects via list_recent.
    payloads = [minimal_job_record().to_dict(), minimal_job_record().to_dict()]
    mock_store.list_recent_payloads = AsyncMock(return_value=payloads)
    resp = client.get("/v1/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert len(data["jobs"]) == 2


def test_list_jobs_negative_params_clamped(client, mock_store):
    """Negative limit/offset must not be passed through to the store —
    list_jobs clamps to limit>=1, offset>=0 (regression for the clamp fix)."""
    captured = {}

    async def fake_list(*, limit, offset, state=None):
        captured["limit"] = limit
        captured["offset"] = offset
        return []

    mock_store.list_recent_payloads = AsyncMock(side_effect=fake_list)
    resp = client.get("/v1/jobs?limit=-1&offset=-5")
    assert resp.status_code == 200
    assert captured["limit"] >= 1
    assert captured["offset"] >= 0


def test_get_artifact_succeeds(tmp_path):
    """Artifact serving with real file on disk."""
    from redtusk.api import create_app
    from redtusk.dispatcher import artifact_dir
    from redtusk.limits import Limits

    job_id = str(uuid4())
    result = minimal_extract_result()
    job = minimal_job_record(job_id=job_id, state=JobState.SUCCEEDED, result=result)

    store = MagicMock()
    store.get = AsyncMock(return_value=job)
    store.create = AsyncMock()
    store.list_recent = AsyncMock(return_value=[])
    store.count_by_state = AsyncMock(return_value=0)

    test_limits = Limits(artifact_root=str(tmp_path))
    art_dir = artifact_dir(str(tmp_path), job_id)
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "metadata.json").write_text('{"test": true}')

    mock_d = MagicMock()
    mock_d.start = AsyncMock()
    mock_d.stop = AsyncMock()
    mock_d.is_healthy.return_value = True

    app = create_app(dispatcher=mock_d, store=store, limits=test_limits)
    with TestClient(app) as c:
        resp = c.get(f"/v1/jobs/{job_id}/artifacts/metadata.json")
    assert resp.status_code == 200
    assert b"test" in resp.content


def test_get_artifact_path_traversal_blocked(client, mock_store):
    """Path traversal in artifact name returns 404."""
    job = minimal_job_record(
        job_id="abc123",
        state=JobState.SUCCEEDED,
        result=minimal_extract_result(),
    )
    mock_store.get = AsyncMock(return_value=job)
    resp = client.get("/v1/jobs/abc123/artifacts/../../etc/passwd")
    assert resp.status_code == 404


def test_infected_zip_rejects_oversized_artifacts(tmp_path):
    from redtusk.api import create_app
    from redtusk.dispatcher import artifact_dir
    from redtusk.limits import Limits

    job_id = str(uuid4())
    result = minimal_extract_result()
    job = minimal_job_record(job_id=job_id, state=JobState.SUCCEEDED, result=result)

    store = MagicMock()
    store.get = AsyncMock(return_value=job)
    store.create = AsyncMock()
    store.list_recent = AsyncMock(return_value=[])
    store.count_by_state = AsyncMock(return_value=0)

    test_limits = Limits(
        artifact_root=str(tmp_path),
        max_infected_zip_source_bytes=3,
    )
    art_dir = artifact_dir(str(tmp_path), job_id)
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "metadata.json").write_bytes(b"abcd")

    mock_d = MagicMock()
    mock_d.start = AsyncMock()
    mock_d.stop = AsyncMock()
    mock_d.is_healthy.return_value = True

    app = create_app(dispatcher=mock_d, store=store, limits=test_limits)
    with TestClient(app) as c:
        resp = c.get(f"/v1/jobs/{job_id}/infected-zip")

    assert resp.status_code == 413
