"""Integration test: RedTuskEngine → detonator harness → host trust.

Validates the full cross-language seam:

    RedTuskEngine.detonate()
        → run_detonation(RedTuskEngine(), ...) writes detonator metadata.json
        → validate_worker_output(...)          re-seals + enforces caps
        → Envelope with status="ok"

Requires:
  - Docker daemon running
  - ``redtusk-worker:default`` image present

Mark: ``integration`` (skip in CI unless the worker image is available).
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from detonator.contract import EmbeddedResource, ExtractedText, find_by_type
from detonator.errors import OutputTrustError
from detonator.host.trust import validate_worker_output
from detonator.limits import Limits
from detonator.worker.harness import run_detonation

from redtusk.engine import IMAGE, RedTuskEngine, _build_tree

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _image_available() -> bool:
    import subprocess
    r = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        capture_output=True,
    )
    return r.returncode == 0


def _docker_running() -> bool:
    import subprocess
    r = subprocess.run(["docker", "info"], capture_output=True)
    return r.returncode == 0


_SKIP_LIVE = not (_docker_running() and _image_available())
_SKIP_REASON = (
    f"Docker not running or image {IMAGE!r} not present — live worker unavailable"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def simple_txt(tmp_path_factory) -> Path:
    """A small plain-text file used as the detonation input."""
    d = tmp_path_factory.mktemp("input")
    p = d / "hello.txt"
    p.write_text(
        "RedTusk detonator round-trip test.\n"
        "The quick brown fox jumps over the lazy dog.\n",
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Live worker tests (require Docker + image)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_SKIP_LIVE, reason=_SKIP_REASON)
def test_run_detonation_exits_zero(simple_txt, tmp_path):
    """run_detonation returns 0 and produces metadata.json."""
    engine = RedTuskEngine()
    outdir = tmp_path / "out"

    rc = run_detonation(
        engine,
        input_path=simple_txt,
        output_dir=outdir,
        limits=Limits(),
    )

    assert rc == 0, "harness must return 0"
    meta = outdir / "metadata.json"
    assert meta.is_file(), "metadata.json must exist"
    envelope = json.loads(meta.read_text())
    assert envelope["engine"] == "redtusk"
    assert envelope["status"] == "ok"


@pytest.mark.skipif(_SKIP_LIVE, reason=_SKIP_REASON)
def test_validate_worker_output_accepts_ok(simple_txt, tmp_path):
    """Host trust validation accepts a well-formed detonation."""
    engine = RedTuskEngine()
    outdir = tmp_path / "out"
    input_sha256 = _sha256(simple_txt.read_bytes())

    rc = run_detonation(
        engine,
        input_path=simple_txt,
        output_dir=outdir,
        limits=Limits(),
    )
    assert rc == 0

    env = validate_worker_output(
        output_dir=outdir,
        input_sha256=input_sha256,
        engine="redtusk",
        limits=Limits(),
    )

    assert env.status == "ok"
    assert env.engine == "redtusk"


@pytest.mark.skipif(_SKIP_LIVE, reason=_SKIP_REASON)
def test_validate_worker_output_finds_embedded_resource(simple_txt, tmp_path):
    """Payload must contain at least one EmbeddedResource (the root entry)."""
    engine = RedTuskEngine()
    outdir = tmp_path / "out"
    input_sha256 = _sha256(simple_txt.read_bytes())

    run_detonation(engine, input_path=simple_txt, output_dir=outdir, limits=Limits())
    env = validate_worker_output(
        output_dir=outdir,
        input_sha256=input_sha256,
        engine="redtusk",
        limits=Limits(),
    )

    resources = find_by_type(env.payload, EmbeddedResource)
    assert len(resources) >= 1, (
        f"Expected ≥1 EmbeddedResource; payload type={type(env.payload).__name__}"
    )
    root = resources[0]
    assert root.depth == 0
    assert root.embedded_path == "/"


@pytest.mark.skipif(_SKIP_LIVE, reason=_SKIP_REASON)
def test_validate_worker_output_finds_extracted_text(simple_txt, tmp_path):
    """ExtractedText node must be present and contain the doc's text."""
    engine = RedTuskEngine()
    outdir = tmp_path / "out"
    input_sha256 = _sha256(simple_txt.read_bytes())

    run_detonation(engine, input_path=simple_txt, output_dir=outdir, limits=Limits())
    env = validate_worker_output(
        output_dir=outdir,
        input_sha256=input_sha256,
        engine="redtusk",
        limits=Limits(),
    )

    texts = find_by_type(env.payload, ExtractedText)
    assert len(texts) >= 1, "Expected ≥1 ExtractedText node"
    combined = " ".join(t.text for t in texts)
    assert "RedTusk" in combined or "fox" in combined, (
        f"Expected document text in ExtractedText nodes; got: {combined[:200]!r}"
    )


@pytest.mark.skipif(_SKIP_LIVE, reason=_SKIP_REASON)
def test_validate_worker_output_rejects_wrong_sha(simple_txt, tmp_path):
    """validate_worker_output must raise OutputTrustError on sha256 mismatch."""
    engine = RedTuskEngine()
    outdir = tmp_path / "out"

    run_detonation(engine, input_path=simple_txt, output_dir=outdir, limits=Limits())

    wrong_sha = "a" * 64
    with pytest.raises(OutputTrustError):
        validate_worker_output(
            output_dir=outdir,
            input_sha256=wrong_sha,
            engine="redtusk",
            limits=Limits(),
        )


# ---------------------------------------------------------------------------
# Unit tests: rmeta → EmbeddedResource tree mapping (no Docker required)
# ---------------------------------------------------------------------------
# These run unconditionally and test the mapping logic against a hand-crafted
# rmeta structure — so even if the live worker is unavailable, the adapter
# contract is still exercised.


_SAMPLE_RMETA: dict = {
    "redtusk_version": "0.1.0",
    "input": {
        "sha256": "a" * 64,
        "size_bytes": 100,
        "filename_hint": "test.docx",
        "submitted_at": "2026-01-01T00:00:00+00:00",
    },
    "extraction": {
        "root_content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "root_language": "en",
        "duration_ms": 420,
        "entries": [
            {
                "path": "/",
                "parent_path": None,
                "depth": 0,
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size_bytes": 9500,
                "sha256": "b" * 64,
                "md5": None,
                "sha1": None,
                "has_thumbnail": False,
                "thumbnail_skipped": None,
                "phash": None,
                "colorhash": None,
                "metadata": {"dc:creator": "Alice", "dc:title": "Test Document"},
                "text": "Hello from the root document.",
                "language": "en",
                "qr": {"codes": [], "skipped": None},
                "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": "disabled"},
                "error": None,
            },
            {
                "path": "/embedded/image1.png",
                "parent_path": "/",
                "depth": 1,
                "content_type": "image/png",
                "size_bytes": 2048,
                "sha256": "c" * 64,
                "md5": None,
                "sha1": None,
                "has_thumbnail": False,
                "thumbnail_skipped": None,
                "phash": None,
                "colorhash": None,
                "metadata": {"width": 640, "height": 480},
                "text": "",
                "language": None,
                "qr": {"codes": [], "skipped": None},
                "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": "no_images"},
                "error": None,
            },
            {
                "path": "/embedded/doc.docx",
                "parent_path": "/",
                "depth": 1,
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size_bytes": 3200,
                "sha256": "d" * 64,
                "md5": None,
                "sha1": None,
                "has_thumbnail": False,
                "thumbnail_skipped": None,
                "phash": None,
                "colorhash": None,
                "metadata": {},
                "text": "Nested document text.",
                "language": "en",
                "qr": {"codes": [], "skipped": None},
                "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": "disabled"},
                "error": None,
            },
            {
                "path": "/embedded/doc.docx/image2.jpg",
                "parent_path": "/embedded/doc.docx",
                "depth": 2,
                "content_type": "image/jpeg",
                "size_bytes": 1024,
                "sha256": "e" * 64,
                "md5": None,
                "sha1": None,
                "has_thumbnail": False,
                "thumbnail_skipped": None,
                "phash": None,
                "colorhash": None,
                "metadata": {},
                "text": "",
                "language": None,
                "qr": {"codes": [], "skipped": None},
                "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": "disabled"},
                "error": None,
            },
        ],
    },
    "limits": {
        "max_recursion_depth": 10,
        "max_embedded_entries": 5000,
        "max_extracted_bytes": 524288000,
        "ocr_timeout_s": 30,
    },
    "truncated": None,
    "warnings": [],
    "sandbox": {
        "profile": "default",
        "runtime": "runc",
        "appcds": True,
        "ksm": False,
        "crac": False,
    },
}


def test_build_tree_root_is_embedded_resource():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    assert isinstance(root, EmbeddedResource)
    assert root.embedded_path == "/"
    assert root.depth == 0
    assert "application/vnd.openxmlformats" in root.content_type


def test_build_tree_text_becomes_child():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    # Root has text → ExtractedText child
    texts = [c for c in root.children if isinstance(c, ExtractedText)]
    assert len(texts) == 1
    assert "Hello" in texts[0].text


def test_build_tree_depth1_children_attached_to_root():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    er_children = [c for c in root.children if isinstance(c, EmbeddedResource)]
    assert len(er_children) == 2, (
        f"Expected 2 depth-1 EmbeddedResource children; got {er_children}"
    )
    paths = {c.embedded_path for c in er_children}
    assert "/embedded/image1.png" in paths
    assert "/embedded/doc.docx" in paths


def test_build_tree_depth2_nested_correctly():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    # Find the nested doc
    nested_doc = next(
        c for c in root.children
        if isinstance(c, EmbeddedResource) and c.embedded_path == "/embedded/doc.docx"
    )
    # It has text + one image child
    er_children = [c for c in nested_doc.children if isinstance(c, EmbeddedResource)]
    assert len(er_children) == 1
    assert er_children[0].embedded_path == "/embedded/doc.docx/image2.jpg"
    assert er_children[0].depth == 2


def test_build_tree_metadata_preserved():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    assert root.metadata is not None
    assert root.metadata.fields.get("dc:creator") == "Alice"


def test_build_tree_find_by_type_counts():
    entries = _SAMPLE_RMETA["extraction"]["entries"]
    root = _build_tree(entries)
    all_er = find_by_type(root, EmbeddedResource)
    assert len(all_er) == 4, f"Expected 4 EmbeddedResource nodes; got {len(all_er)}"
    all_text = find_by_type(root, ExtractedText)
    # Entries with non-empty text: root ("/") and "/embedded/doc.docx"
    assert len(all_text) == 2


def test_build_tree_single_entry():
    """A single root entry produces a valid root with no EmbeddedResource children."""
    entries = [_SAMPLE_RMETA["extraction"]["entries"][0]]
    root = _build_tree(entries)
    assert isinstance(root, EmbeddedResource)
    assert root.embedded_path == "/"
    er_children = [c for c in root.children if isinstance(c, EmbeddedResource)]
    assert len(er_children) == 0


def test_build_tree_empty_entries():
    """Empty entry list synthesises a minimal root node."""
    root = _build_tree([])
    assert isinstance(root, EmbeddedResource)
    assert root.depth == 0
    assert root.children == []
