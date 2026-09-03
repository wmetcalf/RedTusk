"""The /rmeta route must serve the document from where it actually lives.

It asked `serve_artifact_file` for `rmeta/metadata.json`, which cannot work:
that helper requires the path to be a DECLARED artifact and the engine
deliberately stopped declaring this one — its name collided with the envelope's
own `metadata.json` at the zip root — embedding it in the envelope instead.

Measured on toolz2 before the fix: 80/80 jobs done, 0/9 sampled rmeta reads
returning 200, and the envelope holding a 28KB `redtusk_rmeta` field the whole
time.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from redtusk.blastbox_ingress import _rmeta_from_envelope, router

# A real job id shape. The route itself does not validate ids -- that belongs to
# blastbox's `load_result_metadata`, which rejects a non-UUID before any store or
# filesystem access and is tested there. A realistic id keeps this fixture from
# implying the route would accept something production rejects.
_JOB = "95e5c8eb-8df4-49e7-bce7-dbccb6e6c9b4"

_DOC = json.dumps({"extraction": {"entries": [{"path": "/", "depth": 0}]}})


def _envelope(field: str | None = _DOC) -> dict[str, Any]:
    fields: dict[str, Any] = {} if field is None else {"redtusk_rmeta": field}
    return {"status": "ok", "payload": {"metadata": {"fields": fields}}}


def _client(envelope: object, artifact: object = None) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def load_result_metadata(job_id: str) -> object:
        return envelope

    def serve_artifact_file(job_id: str, rel: str, **kw: Any) -> Any:
        if artifact is None:
            from fastapi import HTTPException

            raise HTTPException(404, "artifact file not found")
        from fastapi.responses import Response

        return Response(content=artifact, media_type="application/json")

    app.state.load_result_metadata = load_result_metadata
    app.state.serve_artifact_file = serve_artifact_file
    return TestClient(app)


def test_the_document_is_served_from_the_envelope() -> None:
    r = _client(_envelope()).get(f"/v1/jobs/{_JOB}/rmeta")
    assert r.status_code == 200, r.text
    assert r.json()["extraction"]["entries"][0]["depth"] == 0
    assert r.headers["content-type"].startswith("application/json")


def test_the_download_filename_is_preserved() -> None:
    """The route was a download before; callers may rely on the filename."""
    r = _client(_envelope()).get(f"/v1/jobs/{_JOB}/rmeta")
    assert f'filename="{_JOB}.rmeta.json"' in r.headers.get("content-disposition", "")


def test_a_pre_move_job_still_reads_from_its_declared_artifact() -> None:
    """Jobs produced before the envelope move have the artifact; keep them readable."""
    r = _client(_envelope(field=None), artifact=_DOC).get(f"/v1/jobs/{_JOB}/rmeta")
    assert r.status_code == 200, r.text
    assert r.json()["extraction"]["entries"][0]["depth"] == 0


def test_neither_present_is_a_404_not_a_crash() -> None:
    assert _client(_envelope(field=None)).get(f"/v1/jobs/{_JOB}/rmeta").status_code == 404


@pytest.mark.parametrize(
    "envelope",
    [
        {},                                              # empty
        {"payload": None},                               # null branch
        {"payload": {"metadata": {}}},                   # no fields
        {"payload": {"metadata": {"fields": {"redtusk_rmeta": ""}}}},   # empty string
        {"payload": {"metadata": {"fields": {"redtusk_rmeta": 42}}}},   # wrong type
        {"payload": [{"metadata": {}}]},                 # wrong container
    ],
)
def test_a_malformed_envelope_reads_as_absent_not_an_exception(envelope: object) -> None:
    """The envelope is produced by another process; a surprise shape is 'not here'.

    Raising instead would turn a readable-but-odd job into a 500 on a route
    whose entire purpose is to serve what IS present.
    """
    assert _rmeta_from_envelope(envelope) is None


def test_a_well_formed_envelope_yields_the_document() -> None:
    assert _rmeta_from_envelope(_envelope()) == _DOC
