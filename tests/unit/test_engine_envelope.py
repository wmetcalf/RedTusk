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

import pytest

from redtusk.engine import RedTuskEngine, _env_param_overrides


def _entry(path, parent, depth, ct, sha, **extra):
    """A schema-valid extraction entry (all required fields present)."""
    e = {
        "path": path, "parent_path": parent, "depth": depth, "content_type": ct,
        "size_bytes": 10, "sha256": sha, "metadata": {}, "text": "", "language": None,
        "qr": {"codes": [], "skipped": None},
        "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": None},
        "error": None,
    }
    e.update(extra)
    return e


# A schema-conformant rmeta (detonate now validates it via the restored trust gate).
_RMETA_FIXTURE = {
    "redtusk_version": "test",
    "input": {
        "filename_hint": "x.xlsx", "size_bytes": 10, "sha256": "ab" * 32,
        "submitted_at": "2026-01-01T00:00:00+00:00",
    },
    "extraction": {
        "root_content_type": "application/vnd.ms-excel",
        "root_language": "en",
        "duration_ms": 5,
        "entries": [
            _entry("/", None, 0, "application/vnd.ms-excel", "ab" * 32),
            _entry("/image3.jpeg", "/", 1, "image/jpeg", "cd" * 32, has_thumbnail=True),
        ],
    },
    "limits": {
        "max_recursion_depth": 10, "max_embedded_entries": 5000,
        "max_extracted_bytes": 524_288_000, "ocr_timeout_s": 30,
    },
    "truncated": None,
    "warnings": [],
    "sandbox": {
        "profile": "default", "runtime": "runc", "appcds": True, "ksm": False, "crac": False,
    },
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


def test_detonate_fails_closed_on_malformed_rmeta(tmp_path, monkeypatch):
    """Trust gate: a worker rmeta that violates the schema fails the job (raises),
    not flows unvalidated to the UI."""
    from redtusk.schema import SchemaValidationError

    bad = {"redtusk_version": "x"}  # missing required input/extraction/...

    def fake_produce(self, input, rmeta_dir, timeout):
        (rmeta_dir / "embedded").mkdir(parents=True, exist_ok=True)
        (rmeta_dir / "metadata.json").write_text(json.dumps(bad))

    monkeypatch.setattr(RedTuskEngine, "_produce_rmeta", fake_produce)
    inp = tmp_path / "x"
    inp.write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(SchemaValidationError):
        RedTuskEngine().detonate(inp, out, types.SimpleNamespace(timeout_s=10.0))


def test_thumbnails_default_on_for_warm_tiers():
    """Warm guests (FC/gVisor) can't receive the per-job REDTUSK_ENABLE_THUMBNAILS
    (snapshot env is frozen), so the JVM job descriptor default must be ON or warm
    tiers silently produce no thumbnails."""
    from redtusk.engine import _DEFAULT_JOB

    assert _DEFAULT_JOB["enable_thumbnails"] is True


def test_env_param_overrides_can_disable_thumbnails_on_cold(monkeypatch):
    """Cold still honors an explicit per-job off (the override beats the default)."""
    monkeypatch.setenv("REDTUSK_ENABLE_THUMBNAILS", "false")
    assert _env_param_overrides()["enable_thumbnails"] is False


def test_env_param_overrides_absent_is_empty(monkeypatch):
    for v in (
        "REDTUSK_ENABLE_QR", "REDTUSK_ENABLE_OCR", "REDTUSK_ENABLE_THUMBNAILS",
        "REDTUSK_MAX_RECURSION_DEPTH", "REDTUSK_MAX_EMBEDDED_ENTRIES",
    ):
        monkeypatch.delenv(v, raising=False)
    assert _env_param_overrides() == {}
