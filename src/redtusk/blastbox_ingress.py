"""RedTusk product routes for the shared blastbox ingress.

Mounts RedTusk's canonical *rmeta* artifact route on top of the generic
blastbox ingress (submit/status/list/artifacts/result/similar/auth/health/
metrics) via the ``IngressExtension`` seam, resolved by
``BLASTBOX_INGRESS_EXTENSION=redtusk.blastbox_ingress:make_extension``.

The one RedTusk-specific data route the generic core can't already serve is the
**rmeta document** — the full recursive extraction tree the JVM/Tika worker
writes.  The engine embeds it in the sealed envelope as the ``redtusk_rmeta``
field rather than declaring it as a ``DeclaredArtifact``, because its
``metadata.json`` collided by name with the envelope's own at the zip root.

This route therefore reads the ENVELOPE, via
``request.app.state.load_result_metadata`` — the core helper that owns the
DONE-gate, the job-id validation, and the BlobStore read (never the local job
dir, which may already be purged on this node).

It used to ask ``serve_artifact_file`` for ``rmeta/metadata.json``, which cannot
work and had stopped working in production: that helper requires the path to be
a DECLARED artifact, and the engine deliberately stopped declaring this one. The
result was a 404 on every completed job while the document sat in the envelope,
intact.  A job produced BEFORE that change still has the declared artifact, so
this falls back to it rather than losing history.  These routers add NO security
logic of their own and inherit the app's auth middleware.

Everything else RedTusk's bespoke ``api.py`` exposed is either already provided
by the generic core (job lifecycle, per-entry artifacts via the artifacts route,
``/v1/similar``, the encrypted ``/result`` that replaces ``/infected-zip``) or is
deliberately NOT ported:

  * The **synchronous Tika-compat endpoints** (``/tika``, ``/rmeta``, ``/meta``,
    ``/detect``, ``/unpack`` …) need a JVM in the API tier and are incompatible
    with the host's submit→dispatch→poll split — the async ``/v1/jobs`` flow is
    their replacement.  If strict Tika-REST API-compat becomes a hard product
    requirement they can be re-added later as submit+poll wrappers.
  * The packaged **web UI** is wired here via ``StaticUI`` (the seam), but full
    UI parity is a follow-on: the front-end must be adapted to consume the
    blastbox envelope (the engine should embed the rmeta into the envelope, as
    ClippyShot does with its ``clippyshot_metadata`` field) and the flat
    ``static/`` assets restructured under an ``assets/`` subdir.  Set
    ``REDTUSK_SERVE_UI=0`` to skip mounting it until that lands.
"""

from __future__ import annotations

import os
from pathlib import Path as _FsPath

from blastbox.host.ingress.extension import IngressExtension, StaticUI
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

router = APIRouter()

# RedTusk's packaged web UI (served at GET / + /assets via the StaticUI seam).
_STATIC_DIR = _FsPath(__file__).resolve().parent / "static"

# Relative path of the rmeta document as jobs produced BEFORE the envelope move
# carry it — kept in sync with engine.py's ``rmeta`` subdir. Newer jobs do not
# declare it; see ``_RMETA_FIELD``.
_RMETA_REL = "rmeta/metadata.json"

# Envelope field the engine embeds the rmeta document into
# (``payload.metadata.fields.redtusk_rmeta``), as a JSON *string*.
_RMETA_FIELD = "redtusk_rmeta"


def _rmeta_from_envelope(envelope: object) -> str | None:
    """The embedded rmeta document, or None when this job predates the move.

    Read defensively: the envelope is a sealed document produced by another
    process, so a missing or unexpectedly-shaped branch means "not here", never
    an exception on a route whose job is to serve what IS here.
    """
    node: object = envelope
    for key in ("payload", "metadata", "fields", _RMETA_FIELD):
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node if isinstance(node, str) and node else None


@router.get("/v1/jobs/{job_id}/rmeta")
def get_rmeta(job_id: str, request: Request) -> Response:
    """Serve the canonical rmeta document (full recursive extraction tree).

    From the envelope, where the engine embeds it. Falling back to the declared
    artifact for jobs produced before that move, so history stays readable.
    """
    envelope = request.app.state.load_result_metadata(job_id)
    doc = _rmeta_from_envelope(envelope)
    if doc is not None:
        return Response(
            content=doc,
            media_type="application/json",
            headers={
                "content-disposition": f'attachment; filename="{job_id}.rmeta.json"'
            },
        )
    # Pre-move job: the document is a declared artifact on those.
    resp: Response = request.app.state.serve_artifact_file(
        job_id,
        _RMETA_REL,
        media_type="application/json",
        filename=f"{job_id}.rmeta.json",
    )
    return resp


@router.get("/jobs/{job_id}")
def spa_deeplink(job_id: str) -> FileResponse:
    """Serve the SPA shell for client-routed deep-links (``/jobs/<id>``) so a hard
    refresh / bookmark / share of a job-detail URL works — the front-end then routes
    on ``window.location.pathname``. Distinct from ``/v1/jobs/{id}`` (the JSON API);
    the StaticUI seam only registers ``GET /`` + ``/assets``, so without this a
    refresh on a detail URL 404s. 404 when the UI isn't packaged (REDTUSK_SERVE_UI=0)."""
    index = _STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(str(index), media_type="text/html")


def make_extension() -> IngressExtension:
    """Factory resolved by ``BLASTBOX_INGRESS_EXTENSION``.

    Returns an :class:`IngressExtension` carrying RedTusk's rmeta route and
    (unless ``REDTUSK_SERVE_UI=0``) its packaged web UI, mounted on the shared
    blastbox ingress by ``build_app``.
    """
    serve_ui = os.environ.get("REDTUSK_SERVE_UI", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    static_ui = (
        StaticUI(directory=str(_STATIC_DIR))
        if serve_ui and (_STATIC_DIR / "index.html").is_file()
        else None
    )
    return IngressExtension(routers=(router,), static_ui=static_ui)
