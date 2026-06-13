"""Static guards for the packaged web UI ↔ blastbox.host contract.

The UI is plain JS with no build step, so these are string/structure assertions
(same approach as the rest of the repo's UI checks). They lock the regressions the
blastbox cutover surfaced — the UI was written against RedTusk's bespoke API and
silently drifted from the host contract:

  * it must NOT call routes the host doesn't expose (`/v1/convert`, `/v1/jobs/counts`,
    `/infected-zip`);
  * submit must be multipart (`file` + `engine` + repeated `params`), not a raw body;
  * forwarded params must use UPPERCASE `REDTUSK_*` keys (the dispatcher drops the rest);
  * the detail view must read the embedded `redtusk_rmeta` and resolve thumbnails via
    the declared-artifact id map;
  * the assets must be packaged (pyproject package-data) and referenced under /assets/.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_STATIC = _ROOT / "src" / "redtusk" / "static"
_APP_JS = (_STATIC / "assets" / "app.js").read_text()
_INDEX = (_STATIC / "index.html").read_text()


def _strip_js_comments(s: str) -> str:
    """Drop block + line comments so route checks scan CODE, not prose. Line-comment
    match requires line-start/whitespace before `//` so it can't eat `https://`."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"(?m)(^|\s)//[^\n]*", r"\1", s)
    return s


_APP_JS_CODE = _strip_js_comments(_APP_JS)


# ── dead routes the host does NOT serve ────────────────────────────────────
def test_ui_does_not_call_unported_routes():
    for dead in ("/v1/convert", "/v1/jobs/counts", "/infected-zip"):
        assert dead not in _APP_JS_CODE, f"UI still calls unported route {dead}"


# ── submit shape: multipart file + engine + params ─────────────────────────
def test_upload_uses_multipart_form():
    assert "new FormData()" in _APP_JS
    assert "fd.append('file'" in _APP_JS
    assert "fd.append('engine', 'redtusk')" in _APP_JS
    assert "fd.append('params'" in _APP_JS
    # the old raw-body + query-string submit must be gone
    assert "optParams()" not in _APP_JS


def test_forwarded_params_are_uppercase_redtusk_keys():
    # dispatcher drops anything not ^[A-Z][A-Z0-9_]*$ before the allowlist
    for key in (
        "REDTUSK_ENABLE_THUMBNAILS", "REDTUSK_ENABLE_QR", "REDTUSK_ENABLE_OCR",
        "REDTUSK_MAX_RECURSION_DEPTH", "REDTUSK_MAX_EMBEDDED_ENTRIES",
    ):
        assert key in _APP_JS, f"UI no longer sends {key}"
    assert "enable_thumbnails=" not in _APP_JS  # the lowercase form that never forwarded


# ── envelope-shaped data layer ─────────────────────────────────────────────
def test_detail_reads_embedded_rmeta_and_normalizes_host_jobs():
    assert "redtusk_rmeta" in _APP_JS                 # reads the embedded rmeta
    assert "/metadata" in _APP_JS                     # from the envelope endpoint
    assert "function normalizeJob" in _APP_JS         # host job-shape adapter
    assert "job_id" in _APP_JS and "filename" in _APP_JS


# ── thumbnails resolved via the declared-artifact id map ───────────────────
def test_thumbnails_resolved_via_artifact_map():
    assert "_curArtMap" in _APP_JS
    assert "_entryThumbPath" in _APP_JS
    assert "rmeta/embedded/thumbnails/" in _APP_JS
    # never by raw path against the id-keyed artifacts route
    assert "/artifacts/thumbnail.jpg" not in _APP_JS


# ── assets under /assets/ (the StaticUI seam serves / + /assets only) ──────
def test_index_references_assets_subdir_not_static():
    assert "/static/" not in _INDEX
    assert "/assets/app.js" in _INDEX
    assert "/assets/app.css" in _INDEX


# ── packaging: static/ must ship in the wheel (the 404 root-cause) ─────────
def test_pyproject_packages_static_assets():
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text())
    pkg_data = data["tool"]["setuptools"]["package-data"]["redtusk"]
    assert "static/index.html" in pkg_data
    assert any("static/assets/" in p for p in pkg_data)


def test_static_assets_present_on_disk():
    assert (_STATIC / "index.html").is_file()
    assert (_STATIC / "assets" / "app.js").is_file()
    assert (_STATIC / "assets" / "app.css").is_file()
