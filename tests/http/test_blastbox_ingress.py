"""Tests for RedTusk's blastbox ingress extension (the rmeta artifact route).

Builds the shared blastbox ingress with RedTusk's ``IngressExtension`` mounted and
asserts the product route ``GET /v1/jobs/{id}/rmeta`` serves the canonical rmeta
document (``rmeta/metadata.json``) from a DONE job's output dir — reusing the
core's confinement via ``app.state.serve_artifact_file`` (DONE-gate, containment,
no-symlink-follow).

Self-contained: builds its own app via ``build_app`` and does not use the
bespoke-api fixtures in ``tests/http/conftest.py`` (which go away with api.py in
the cutover). Output lives under ``<job_root>/<id>/output`` — this test passes
``job_root=tmp_path/"jobs"``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("blastbox.host.ingress.app")

from blastbox.host.ingress.app import build_app
from blastbox.host.jobs.base import Job, JobStatus
from blastbox.host.jobs.memory import InMemoryJobStore

from redtusk.blastbox_ingress import make_extension

_RMETA_BYTES = (
    b'{"extraction":{"root_content_type":"text/plain","entries":'
    b'[{"path":"/","content_type":"text/plain","depth":0,"text":"hello"}]}}'
)


def _make_client(tmp_path: Path) -> tuple[TestClient, InMemoryJobStore]:
    store = InMemoryJobStore()
    app = build_app(
        job_store=store,
        job_root=tmp_path / "jobs",
        allowed_engines={"redtusk"},
        extension=make_extension(),
    )
    return TestClient(app, raise_server_exceptions=False), store


def _make_done_job(tmp_path: Path, store: InMemoryJobStore, *, write_rmeta: bool = True) -> Job:
    """Create a DONE redtusk job with rmeta/metadata.json under its output dir."""
    job = Job.new(engine="redtusk", filename="test.docx")
    output_dir = tmp_path / "jobs" / job.job_id / "output"
    (output_dir / "rmeta").mkdir(parents=True)
    if write_rmeta:
        (output_dir / "rmeta" / "metadata.json").write_bytes(_RMETA_BYTES)

    # Dispatcher-sealed envelope manifest. The engine (M-4) declares rmeta/metadata.json
    # as an artifact so it goes through the trust gate; blastbox's fixed-filename /rmeta
    # route (H-1, blastbox>=0.1.8) serves ONLY paths declared here, so the manifest must
    # list it — otherwise an undeclared file would be served as un-re-hashed worker bytes.
    (output_dir / "metadata.json").write_text(
        json.dumps({"artifacts": [{"path": "rmeta/metadata.json"}]})
    )

    job.result_dir = str(output_dir)
    job.input_sha256 = "a" * 64
    job.status = JobStatus.DONE
    job.finished_at = time.time()
    store.create(job)
    return job


def test_rmeta_route_served(tmp_path):
    client, store = _make_client(tmp_path)
    job = _make_done_job(tmp_path, store)
    resp = client.get(f"/v1/jobs/{job.job_id}/rmeta")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.content == _RMETA_BYTES


def test_rmeta_missing_returns_404(tmp_path):
    client, store = _make_client(tmp_path)
    job = _make_done_job(tmp_path, store, write_rmeta=False)
    resp = client.get(f"/v1/jobs/{job.job_id}/rmeta")
    assert resp.status_code == 404


def test_rmeta_409_when_not_done(tmp_path):
    """The core DONE-gate (via serve_artifact_file) applies to the product route."""
    client, store = _make_client(tmp_path)
    job = Job.new(engine="redtusk", filename="test.docx")
    store.create(job)  # QUEUED
    resp = client.get(f"/v1/jobs/{job.job_id}/rmeta")
    assert resp.status_code == 409


def test_rmeta_404_for_unknown_job(tmp_path):
    client, _ = _make_client(tmp_path)
    resp = client.get("/v1/jobs/00000000-0000-0000-0000-000000000000/rmeta")
    assert resp.status_code == 404


def test_make_extension_wires_rmeta_route():
    ext = make_extension()
    paths = {r.path for router in ext.routers for r in router.routes}
    assert "/v1/jobs/{job_id}/rmeta" in paths


def test_serve_ui_toggle(monkeypatch):
    monkeypatch.setenv("REDTUSK_SERVE_UI", "0")
    assert make_extension().static_ui is None
    monkeypatch.setenv("REDTUSK_SERVE_UI", "1")
    # static_ui is present iff the packaged index.html ships in the wheel.
    ext = make_extension()
    from redtusk.blastbox_ingress import _STATIC_DIR

    if (_STATIC_DIR / "index.html").is_file():
        assert ext.static_ui is not None
    else:  # pragma: no cover - depends on packaging
        assert ext.static_ui is None
