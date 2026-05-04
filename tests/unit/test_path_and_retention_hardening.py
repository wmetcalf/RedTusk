"""Regression tests for file/path hardening."""
from __future__ import annotations

import tarfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest

from redtusk.api import _sanitize_filename
from redtusk.dispatcher import artifact_dir
from redtusk.jobs.memory import MemoryJobStore
from redtusk.jobs.retention import prune_orphaned_artifacts
from redtusk.translation import to_unpack_tar
from redtusk.types import (
    EmbeddedEntry,
    ExtractionInfo,
    ExtractResult,
    InputInfo,
    LimitsInfo,
    OcrResult,
    QrResult,
    SandboxInfo,
    SkipReason,
)


def test_sanitize_filename_rejects_empty_dot_and_traversal_names() -> None:
    assert _sanitize_filename("\x00\x1f") == "upload"
    assert _sanitize_filename(".") == "upload"
    assert _sanitize_filename("..") == "upload"
    assert _sanitize_filename("../evil.txt") == "evil.txt"
    assert _sanitize_filename(r"..\\evil.txt") == "evil.txt"


def test_unpack_tar_sanitizes_windows_traversal_names() -> None:
    entry = EmbeddedEntry(
        path=r"..\\evil.txt",
        parent_path="/",
        depth=1,
        content_type="text/plain",
        size_bytes=4,
        sha256=None,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
        metadata={},
        text="evil",
        language=None,
        qr=QrResult(codes=[], skipped=SkipReason.NO_IMAGES),
        ocr=OcrResult(text="", language=None, duration_ms=0, skipped=SkipReason.NO_IMAGES),
        error=None,
    )
    result = ExtractResult(
        redtusk_version="0.1.0",
        tika_version="4.0.0",
        input=InputInfo("a" * 64, 4, "x.txt", datetime.now(UTC)),
        extraction=ExtractionInfo("text/plain", None, 1, [entry]),
        limits=LimitsInfo(10, 5000, 100, 60),
        truncated=None,
        warnings=[],
        sandbox=SandboxInfo("default", "runc", True, False, False),
    )

    with tarfile.open(fileobj=BytesIO(to_unpack_tar(result, include_root=True))) as tar:
        names = tar.getnames()

    assert names == ["unsafe_path_.._evil.txt"]


@pytest.mark.asyncio
async def test_prune_orphaned_artifacts_removes_dirs_without_store_records(tmp_path: Path) -> None:
    store = MemoryJobStore()
    await store.connect()
    orphan_id = "12f2b03b-5b77-4ea1-a168-5a7ce6f08f94"
    orphan_dir = artifact_dir(str(tmp_path), orphan_id)
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "metadata.json").write_text("{}")

    removed = await prune_orphaned_artifacts(store, str(tmp_path), min_age_seconds=0)

    assert removed == 1
    assert not orphan_dir.exists()


@pytest.mark.asyncio
async def test_prune_orphaned_artifacts_skips_recent_dirs(tmp_path: Path) -> None:
    store = MemoryJobStore()
    await store.connect()
    recent_id = "12f2b03b-5b77-4ea1-a168-5a7ce6f08f94"
    recent_dir = artifact_dir(str(tmp_path), recent_id)
    recent_dir.mkdir(parents=True)

    removed = await prune_orphaned_artifacts(store, str(tmp_path), min_age_seconds=300)

    assert removed == 0
    assert recent_dir.exists()
