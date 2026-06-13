"""Engine→envelope contract guards for the blastbox.host UI port.

These lock the three things that broke (and were fixed) during the cutover:

  * the rmeta document is EMBEDDED in the envelope as the ``redtusk_rmeta`` field
    and ``rmeta/metadata.json`` is NOT declared as an artifact — so ``/result``
    carries a single ``metadata.json`` (the envelope), not two;
  * thumbnails the JVM writes under ``rmeta/embedded/thumbnails/`` are declared as
    artifacts (the host serves them by id; the UI resolves them via the manifest);
  * UI-forwarded params are read ONLY from the UPPERCASE ``REDTUSK_*`` env names
    (the dispatcher drops lowercase keys before any allowlist).
"""

from __future__ import annotations

import json
import types
from pathlib import Path

from redtusk.engine import RedTuskEngine, _env_param_overrides

_RMETA_FIXTURE = {
    "redtusk_version": "test",
    "input": {"filename_hint": "x.xlsx", "size_bytes": 10, "sha256": "ab" * 32},
    "extraction": {
        "root_content_type": "application/vnd.ms-excel",
        "root_language": "en",
        "duration_ms": 5,
        "entries": [
            {"path": "/", "content_type": "application/vnd.ms-excel", "depth": 0,
             "metadata": {}},
            {"path": "/image3.jpeg", "content_type": "image/jpeg", "depth": 1,
             "metadata": {}, "has_thumbnail": True, "sha256": "cd" * 32},
        ],
    },
    "limits": {},
    "truncated": None,
    "warnings": [],
    "sandbox": {"profile": "default", "runtime": "runc"},
}


def _write_fixture_rmeta(rmeta_dir: Path) -> None:
    """Mimic what the JVM worker writes into outdir/rmeta/ (no JVM needed)."""
    (rmeta_dir / "embedded" / "thumbnails").mkdir(parents=True, exist_ok=True)
    (rmeta_dir / "metadata.json").write_text(json.dumps(_RMETA_FIXTURE))
    (rmeta_dir / "embedded" / "image3.jpeg").write_bytes(b"\xff\xd8jpeg")
    (rmeta_dir / "embedded" / "thumbnails" / "image3.jpeg.jpg").write_bytes(b"\xff\xd8thumb")


def _detonate(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        RedTuskEngine, "_produce_rmeta",
        lambda self, input, rmeta_dir, timeout: _write_fixture_rmeta(rmeta_dir),
    )
    inp = tmp_path / "x.xlsx"
    inp.write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir()
    return RedTuskEngine().detonate(inp, out, types.SimpleNamespace(timeout_s=10.0))


def test_detonate_embeds_rmeta_and_drops_metadata_json(tmp_path, monkeypatch):
    res = _detonate(tmp_path, monkeypatch)
    paths = [a.path for a in res.artifacts]
    # The wart: rmeta/metadata.json must NOT be a declared artifact (no second
    # metadata.json in the sealed /result zip).
    assert "rmeta/metadata.json" not in paths
    # Its content is embedded in the envelope instead.
    fields = res.payload.metadata.fields
    assert "redtusk_rmeta" in fields, "rmeta not embedded in the envelope"
    embedded = json.loads(fields["redtusk_rmeta"])
    assert embedded["extraction"]["entries"][1]["path"] == "/image3.jpeg"


def test_detonate_declares_thumbnail_artifacts_servable_by_id(tmp_path, monkeypatch):
    res = _detonate(tmp_path, monkeypatch)
    paths = [a.path for a in res.artifacts]
    assert "rmeta/embedded/image3.jpeg" in paths                      # the embedded image
    assert "rmeta/embedded/thumbnails/image3.jpeg.jpg" in paths       # its thumbnail
    ids = [a.id for a in res.artifacts]
    assert len(ids) == len(set(ids)), "artifact ids must be unique (host serves by id)"


def test_env_param_overrides_uppercase_only(monkeypatch):
    monkeypatch.setenv("REDTUSK_ENABLE_THUMBNAILS", "true")
    monkeypatch.setenv("REDTUSK_ENABLE_QR", "false")
    monkeypatch.setenv("REDTUSK_MAX_RECURSION_DEPTH", "20")
    monkeypatch.setenv("enable_thumbnails", "true")  # lowercase — read path must ignore it
    out = _env_param_overrides()
    assert out["enable_thumbnails"] is True
    assert out["enable_qr"] is False
    assert out["limits"]["max_recursion_depth"] == 20


def test_env_param_overrides_absent_is_empty(monkeypatch):
    for v in (
        "REDTUSK_ENABLE_QR", "REDTUSK_ENABLE_OCR", "REDTUSK_ENABLE_THUMBNAILS",
        "REDTUSK_MAX_RECURSION_DEPTH", "REDTUSK_MAX_EMBEDDED_ENTRIES",
    ):
        monkeypatch.delenv(v, raising=False)
    assert _env_param_overrides() == {}
