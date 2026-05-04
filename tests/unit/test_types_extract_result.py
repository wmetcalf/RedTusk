"""Tests for ExtractResult and its composing wrapper types."""
from __future__ import annotations

from datetime import UTC, datetime

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
    TruncationInfo,
    TruncationReason,
    WarningEntry,
)


def _root_entry() -> EmbeddedEntry:
    return EmbeddedEntry(
        path="/",
        parent_path=None,
        depth=0,
        content_type="application/pdf",
        size_bytes=1024,
        sha256="ae1c" + "0" * 60,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
        metadata={"Author": "test"},
        text="hello",
        language="en",
        qr=QrResult(),
        ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
        error=None,
    )


def _result(**overrides) -> ExtractResult:
    base = ExtractResult(
        redtusk_version="0.1.0",
        tika_version="3.0.0",
        input=InputInfo(
            sha256="ae1c" + "0" * 60,
            size_bytes=1024,
            filename_hint="test.pdf",
            submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=UTC),
        ),
        extraction=ExtractionInfo(
            root_content_type="application/pdf",
            root_language="en",
            duration_ms=412,
            entries=[_root_entry()],
        ),
        limits=LimitsInfo(
            max_recursion_depth=10,
            max_embedded_entries=5000,
            max_extracted_bytes=524288000,
            ocr_timeout_s=60,
        ),
        truncated=None,
        warnings=[],
        sandbox=SandboxInfo(
            profile="default",
            runtime="runsc",
            appcds=True,
            ksm=True,
            crac=False,
        ),
    )
    if overrides:
        from dataclasses import replace
        return replace(base, **overrides)
    return base


def test_input_info_round_trip() -> None:
    info = InputInfo(
        sha256="abc",
        size_bytes=10,
        filename_hint="x.pdf",
        submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=UTC),
    )
    d = info.to_dict()
    assert d == {
        "sha256": "abc",
        "size_bytes": 10,
        "filename_hint": "x.pdf",
        "submitted_at": "2026-05-04T18:23:11+00:00",
    }
    assert InputInfo.from_dict(d) == info


def test_input_info_no_filename_hint() -> None:
    info = InputInfo(
        sha256="abc",
        size_bytes=10,
        filename_hint=None,
        submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=UTC),
    )
    d = info.to_dict()
    assert d["filename_hint"] is None
    assert InputInfo.from_dict(d) == info


def test_extraction_info_round_trip() -> None:
    info = ExtractionInfo(
        root_content_type="application/pdf",
        root_language="en",
        duration_ms=100,
        entries=[_root_entry()],
    )
    d = info.to_dict()
    assert d["root_content_type"] == "application/pdf"
    assert d["root_language"] == "en"
    assert d["duration_ms"] == 100
    assert len(d["entries"]) == 1
    assert ExtractionInfo.from_dict(d) == info


def test_extraction_info_no_root_language() -> None:
    info = ExtractionInfo(
        root_content_type="application/octet-stream",
        root_language=None,
        duration_ms=0,
        entries=[_root_entry()],
    )
    d = info.to_dict()
    assert d["root_language"] is None
    assert ExtractionInfo.from_dict(d) == info


def test_limits_info_round_trip() -> None:
    info = LimitsInfo(
        max_recursion_depth=10,
        max_embedded_entries=5000,
        max_extracted_bytes=524288000,
        ocr_timeout_s=60,
    )
    d = info.to_dict()
    assert d == {
        "max_recursion_depth": 10,
        "max_embedded_entries": 5000,
        "max_extracted_bytes": 524288000,
        "ocr_timeout_s": 60,
    }
    assert LimitsInfo.from_dict(d) == info


def test_sandbox_info_round_trip() -> None:
    s = SandboxInfo(profile="high-density", runtime="runc", appcds=True, ksm=True, crac=True)
    d = s.to_dict()
    assert d == {
        "profile": "high-density",
        "runtime": "runc",
        "appcds": True,
        "ksm": True,
        "crac": True,
    }
    assert SandboxInfo.from_dict(d) == s


def test_extract_result_round_trip_full() -> None:
    r = _result()
    d = r.to_dict()
    parsed = ExtractResult.from_dict(d)
    assert parsed == r


def test_extract_result_with_truncation() -> None:
    r = _result(
        truncated=TruncationInfo(
            reason=TruncationReason.MAX_EMBEDDED_ENTRIES, limit=5000, observed=6000
        )
    )
    d = r.to_dict()
    assert d["truncated"] == {
        "reason": "max_embedded_entries",
        "limit": 5000,
        "observed": 6000,
    }
    assert ExtractResult.from_dict(d) == r


def test_extract_result_with_warnings() -> None:
    r = _result(warnings=[WarningEntry(code="ocr_scan_error", detail="crash")])
    d = r.to_dict()
    assert d["warnings"] == [
        {"code": "ocr_scan_error", "detail": "crash", "entry_path": None}
    ]
    assert ExtractResult.from_dict(d) == r


def test_extract_result_top_level_keys_match_spec() -> None:
    """The top-level shape is part of the public API contract; pin it explicitly."""
    d = _result().to_dict()
    assert set(d.keys()) == {
        "redtusk_version",
        "tika_version",
        "input",
        "extraction",
        "limits",
        "truncated",
        "warnings",
        "sandbox",
    }
