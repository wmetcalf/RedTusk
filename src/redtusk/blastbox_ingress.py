"""RedTusk product routes for the shared blastbox ingress.

Mounts RedTusk's canonical *rmeta* artifact route on top of the generic
blastbox ingress (submit/status/list/artifacts/result/similar/auth/health/
metrics) via the ``IngressExtension`` seam, resolved by
``BLASTBOX_INGRESS_EXTENSION=redtusk.blastbox_ingress:make_extension``.

The one RedTusk-specific data route the generic core can't already serve is the
**rmeta document** (``rmeta/metadata.json`` — the full recursive extraction tree
the JVM/Tika worker writes).  The engine deliberately does NOT declare it as a
``DeclaredArtifact`` (so it never collides with the blastbox envelope), so the
generic ``/v1/jobs/{id}/artifacts/{id}`` route (keyed by artifact id) can't reach
it.  This route serves it by fixed relative path through
``request.app.state.serve_artifact_file`` — the core helper that owns the
DONE-gate, ``resolve()+relative_to()`` containment, and no-symlink-follow.  These
routers add NO security logic of their own and inherit the app's auth middleware.

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
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

router = APIRouter()

# RedTusk's packaged web UI (served at GET / + /assets via the StaticUI seam).
_STATIC_DIR = _FsPath(__file__).resolve().parent / "static"

# Relative path (under the job output dir) of the rmeta document the engine's
# RedTuskEngine.detonate writes — kept in sync with engine.py's ``rmeta`` subdir.
_RMETA_REL = "rmeta/metadata.json"


@router.get("/v1/jobs/{job_id}/rmeta")
def get_rmeta(job_id: str, request: Request) -> FileResponse:
    """Stream the canonical rmeta document (full recursive extraction tree)."""
    # app.state.serve_artifact_file is untyped (Any); launder through a typed
    # local so strict mypy keeps the FileResponse return type.
    resp: FileResponse = request.app.state.serve_artifact_file(
        job_id,
        _RMETA_REL,
        media_type="application/json",
        filename=f"{job_id}.rmeta.json",
    )
    return resp


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
