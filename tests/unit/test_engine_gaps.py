"""Engine-side gaps that blastbox-engine.toml used to record, now closed in code.

Each test drives the condition the gap described and asserts the evidence reaches the typed
result (or a warning says why it could not), rather than living only inside the
``redtusk_rmeta`` JSON string, the worker log, or a stale directory.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from blastbox.limits import Limits

from redtusk import engine as eng_mod
from redtusk.engine import (
    RedTuskEngine,
    _embedded_disk_relpath,
    _infer_artifact_kind,
    _reconstruct_rmeta_artifact_paths,
)
from tests.engine_contract import conform
from tests.unit.test_engine_envelope import _RMETA_FIXTURE, _entry


def _rmeta(**over: Any) -> dict[str, Any]:
    doc = copy.deepcopy(_RMETA_FIXTURE)
    doc.update(over)
    return doc


def _detonate_with(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, doc: dict[str, Any],
                   files: dict[str, bytes] | None = None) -> Any:
    def produce(self: Any, input: Path, rmeta_dir: Path, timeout: float) -> None:
        rmeta_dir.mkdir(parents=True, exist_ok=True)
        (rmeta_dir / "metadata.json").write_text(json.dumps(doc))
        for rel, data in (files or {}).items():
            (rmeta_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (rmeta_dir / rel).write_bytes(data)

    monkeypatch.setattr(RedTuskEngine, "_produce_rmeta", produce)
    inp = tmp_path / "x.xlsx"
    inp.write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir()
    res = RedTuskEngine().detonate(inp, out, Limits(timeout_s=10))
    conform(res, out)
    return res


# --- qr-only-in-rmeta-string --------------------------------------------------------------------

def test_qr_ocr_parent_and_thumbnail_state_reach_the_typed_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = _rmeta()
    entries = doc["extraction"]["entries"]
    entries[1]["qr"] = {"codes": [{"data": "https://phish.example/x", "format": "QR_CODE",
                                   "raw_bytes": None, "position": "1,2"}], "skipped": None}
    entries[1]["ocr"] = {"text": "Sign in to Micros0ft", "language": "eng",
                         "duration_ms": 7, "skipped": None}
    entries[1]["has_thumbnail"] = True
    entries.append(_entry("/blank.png", "/", 1, "image/png", "ef" * 32,
                          has_thumbnail=False, thumbnail_skipped="pass1_buffer_cap",
                          qr={"codes": [], "skipped": "blank_image"}))
    res = _detonate_with(tmp_path, monkeypatch, doc)

    img, blank = (c for c in res.payload.children if getattr(c, "embedded_path", None))
    f = img.metadata.fields
    assert f["redtusk:parent_path"] == "/"
    assert f["redtusk:has_thumbnail"] is True
    qr = f["redtusk:qr"].fields
    assert qr["data"] == ["https://phish.example/x"]
    assert qr["format"] == ["QR_CODE"]
    assert qr["position"] == ["1,2"]
    ocr = f["redtusk:ocr"].fields
    assert ocr["text"] == "Sign in to Micros0ft"
    assert ocr["language"] == "eng"

    b = blank.metadata.fields
    assert b["redtusk:thumbnail_skipped"] == "pass1_buffer_cap"
    assert b["redtusk:qr"].fields["skipped"] == "blank_image"
    assert "redtusk:ocr" not in b  # nothing to say: no text, no skip reason


def test_engine_fields_win_over_a_colliding_tika_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = _rmeta()
    doc["extraction"]["entries"][1]["metadata"] = {"redtusk:parent_path": "/spoofed"}
    res = _detonate_with(tmp_path, monkeypatch, doc)
    node = res.payload.children[0]
    assert node.metadata.fields["redtusk:parent_path"] == "/"


# --- truncated-warning-unstructured / rmeta warning entry_path ----------------------------------

def test_truncation_is_structured_on_the_root(tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    doc = _rmeta(truncated={"reason": "max_embedded_entries", "limit": 5000, "observed": 5001})
    res = _detonate_with(tmp_path, monkeypatch, doc)
    tr = res.payload.metadata.fields["redtusk:truncated"].fields
    assert tr == {"reason": "max_embedded_entries", "limit": 5000, "observed": 5001}
    (w,) = [w for w in res.warnings if w.code == "truncated"]
    assert w.context == "max_embedded_entries"


def test_rmeta_warning_entry_path_is_kept_as_context(tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    doc = _rmeta(warnings=[{"code": "partial_extraction", "detail": "boom",
                            "entry_path": "/word/document.xml"}])
    res = _detonate_with(tmp_path, monkeypatch, doc)
    (w,) = [w for w in res.warnings if w.code == "partial_extraction"]
    assert w.context == "/word/document.xml"


# --- silent-size-caps (the Python half: Record key cap) -----------------------------------------

def test_metadata_key_cap_is_warned_not_silent(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    doc = _rmeta()
    doc["extraction"]["entries"][1]["metadata"] = {f"k{i}": "v" for i in range(4100)}
    res = _detonate_with(tmp_path, monkeypatch, doc)
    (w,) = [w for w in res.warnings if w.code == "metadata_keys_capped"]
    assert w.context == "/image3.jpeg"
    assert "4100" in w.message


# --- kind-from-filename -------------------------------------------------------------------------

def test_kind_follows_the_path_role_not_the_file_name() -> None:
    assert _infer_artifact_kind("rmeta/embedded/photo.jpg") == "embedded_file"
    assert _infer_artifact_kind("rmeta/embedded/notes.txt") == "embedded_file"
    assert _infer_artifact_kind("rmeta/embedded/a/b.bin") == "embedded_file"
    assert _infer_artifact_kind("rmeta/embedded/thumbnails/photo.jpg.jpg") == "thumbnail"
    assert _infer_artifact_kind("rmeta/thumbnail.jpg") == "thumbnail"


def test_a_real_entry_under_thumbnails_dir_is_an_embedded_file() -> None:
    # An archive member literally named thumbnails/x.jpg lands at the same prefix as a thumbnail;
    # the rmeta entries say which it is.
    known = frozenset({"rmeta/embedded/thumbnails/x.jpg"})
    assert _infer_artifact_kind("rmeta/embedded/thumbnails/x.jpg", known) == "embedded_file"


def test_detonate_declares_embedded_images_as_embedded_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    res = _detonate_with(tmp_path, monkeypatch, _rmeta(), {
        "embedded/image3.jpeg": b"\xff\xd8jpeg",
        "embedded/thumbnails/image3.jpeg.jpg": b"\xff\xd8thumb",
    })
    kinds = {a.path: a.kind for a in res.artifacts}
    assert kinds["rmeta/embedded/image3.jpeg"] == "embedded_file"
    assert kinds["rmeta/embedded/thumbnails/image3.jpeg.jpg"] == "thumbnail"


# --- cr-tier-drops-thumbnails -------------------------------------------------------------------

def test_stale_view_reconstruction_declares_thumbnails(tmp_path: Path) -> None:
    rmeta = tmp_path / "rmeta"
    lossy = "/sub/évil*.png"
    for rel in ("metadata.json", "thumbnail.jpg", "embedded/image1.png",
                "embedded/thumbnails/image1.png.jpg",
                f"embedded/{_embedded_disk_relpath(lossy)}",
                f"embedded/thumbnails/{_embedded_disk_relpath(lossy)}.jpg"):
        (rmeta / rel).parent.mkdir(parents=True, exist_ok=True)
        (rmeta / rel).write_bytes(b"x")
    entries = [
        {"path": "/", "has_thumbnail": True},
        {"path": "/image1.png", "has_thumbnail": True},
        {"path": lossy, "has_thumbnail": True},
        {"path": "/nothumb.png", "has_thumbnail": True},   # claimed, but not on disk
    ]
    got = _reconstruct_rmeta_artifact_paths(tmp_path, rmeta, entries)
    assert "rmeta/thumbnail.jpg" in got
    assert "rmeta/embedded/thumbnails/image1.png.jpg" in got
    assert f"rmeta/embedded/thumbnails/{_embedded_disk_relpath(lossy)}.jpg" in got
    assert not any("nothumb" in p for p in got)


# --- fallback-reuses-rmeta-dir ------------------------------------------------------------------

def test_crac_fallback_starts_cold_from_a_clean_rmeta_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rmeta_dir = tmp_path / "rmeta"

    def failed_crac(inp: Path, rmeta: Path, **_: Any) -> None:
        (rmeta / "embedded").mkdir(parents=True, exist_ok=True)
        (rmeta / "embedded" / "half-written.bin").write_bytes(b"partial")
        (rmeta / ".metadata.json.draft.tmp").write_text("{}")
        raise RuntimeError("restore failed mid-job")

    seen: list[list[str]] = []

    def cold(inp: Path, rmeta: Path, *, timeout: float) -> None:
        seen.append(sorted(p.name for p in rmeta.rglob("*")) if rmeta.exists() else [])

    monkeypatch.setattr(eng_mod, "_crac_restore_worker", failed_crac)
    monkeypatch.setattr(eng_mod, "_run_worker", cold)
    monkeypatch.setenv("REDTUSK_CRAC_CHECKPOINT", "/ckpt")
    RedTuskEngine()._produce_rmeta(Path("in"), rmeta_dir, 10.0)
    assert seen == [[]], f"cold fallback saw the failed attempt's files: {seen}"


def test_a_draft_tmp_is_never_declared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    res = _detonate_with(tmp_path, monkeypatch, _rmeta(),
                         {".metadata.json.draft.tmp": b"{}"})
    assert ".metadata.json.draft.tmp" not in " ".join(a.path for a in res.artifacts)


def test_warm_crash_fallback_starts_cold_from_a_clean_rmeta_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.unit.test_warm_timeout_discriminator import _engine_with_warm, _FakeProc

    rmeta_dir = tmp_path / "out" / "rmeta"

    class _CrashingWarm(_FakeProc):
        def communicate(self, timeout: float | None = None) -> tuple[bytes | None, bytes | None]:
            (rmeta_dir / "embedded").mkdir(parents=True, exist_ok=True)
            (rmeta_dir / "embedded" / "half-written.bin").write_bytes(b"partial")
            return (b"", b"boom")

    seen: list[list[str]] = []
    monkeypatch.setattr(
        eng_mod, "_run_worker",
        lambda i, r, timeout: seen.append(
            sorted(p.name for p in r.rglob("*")) if r.exists() else []),
    )
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    eng = _engine_with_warm(tmp_path, _CrashingWarm(timeout=False, returncode=1), started=True)
    eng._produce_rmeta(src, rmeta_dir, timeout=30.0)
    assert seen == [[]], f"cold fallback saw the crashed warm JVM's files: {seen}"
