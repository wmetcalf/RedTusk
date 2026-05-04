"""Tests for the building-block value types in redtusk.types."""
from __future__ import annotations

import dataclasses

import pytest

from redtusk.types import (
    EmbeddedEntry,
    JobState,
    OcrResult,
    QrCode,
    QrResult,
    SkipReason,
    TruncationInfo,
    TruncationReason,
    WarningEntry,
)


def test_job_state_string_values() -> None:
    assert JobState.QUEUED.value == "queued"
    assert JobState.RUNNING.value == "running"
    assert JobState.SUCCEEDED.value == "succeeded"
    assert JobState.FAILED.value == "failed"


def test_job_state_terminal_predicate() -> None:
    assert JobState.SUCCEEDED.is_terminal()
    assert JobState.FAILED.is_terminal()
    assert not JobState.QUEUED.is_terminal()
    assert not JobState.RUNNING.is_terminal()


def test_skip_reason_string_values() -> None:
    """SkipReason vocabulary is the same for QR and OCR."""
    assert SkipReason.NO_IMAGES.value == "no_images"
    assert SkipReason.TIMEOUT_BUDGET.value == "timeout_budget"
    assert SkipReason.ERROR.value == "error"
    assert SkipReason.DISABLED.value == "disabled"


def test_truncation_reason_string_values() -> None:
    assert TruncationReason.MAX_EMBEDDED_ENTRIES.value == "max_embedded_entries"
    assert TruncationReason.MAX_RECURSION_DEPTH.value == "max_recursion_depth"
    assert TruncationReason.MAX_EXTRACTED_BYTES.value == "max_extracted_bytes"


def test_qr_code_is_frozen() -> None:
    code = QrCode(data="hello", format="QR_CODE")
    with pytest.raises(dataclasses.FrozenInstanceError):
        code.data = "changed"  # type: ignore[misc]


def test_qr_code_round_trip() -> None:
    code = QrCode(data="https://example.com", format="QR_CODE")
    d = code.to_dict()
    assert d == {
        "data": "https://example.com",
        "format": "QR_CODE",
        "raw_bytes": None,
        "position": None,
    }
    assert QrCode.from_dict(d) == code


def test_qr_result_default_empty() -> None:
    r = QrResult()
    assert r.codes == []
    assert r.skipped is None


def test_qr_result_round_trip() -> None:
    r = QrResult(
        codes=[QrCode(data="x", format="QR_CODE")],
        skipped=None,
    )
    d = r.to_dict()
    assert d == {
        "codes": [{"data": "x", "format": "QR_CODE", "raw_bytes": None, "position": None}],
        "skipped": None,
    }
    assert QrResult.from_dict(d) == r


def test_qr_result_round_trip_skipped() -> None:
    r = QrResult(codes=[], skipped=SkipReason.DISABLED)
    d = r.to_dict()
    assert d == {"codes": [], "skipped": "disabled"}
    assert QrResult.from_dict(d) == r


def test_ocr_result_default_empty() -> None:
    r = OcrResult()
    assert r.text == ""
    assert r.language is None
    assert r.duration_ms == 0
    assert r.skipped is None


def test_ocr_result_round_trip() -> None:
    r = OcrResult(text="hello", language="eng", duration_ms=412, skipped=None)
    d = r.to_dict()
    assert d == {
        "text": "hello",
        "language": "eng",
        "duration_ms": 412,
        "skipped": None,
    }
    assert OcrResult.from_dict(d) == r


def test_ocr_result_round_trip_skipped() -> None:
    r = OcrResult(skipped=SkipReason.TIMEOUT_BUDGET)
    d = r.to_dict()
    assert d == {
        "text": "",
        "language": None,
        "duration_ms": 0,
        "skipped": "timeout_budget",
    }
    assert OcrResult.from_dict(d) == r


def test_warning_entry_round_trip() -> None:
    w = WarningEntry(
        code="ocr_scan_error", detail="tesseract crashed", entry_path="/embedded/img1.png"
    )
    d = w.to_dict()
    assert d == {
        "code": "ocr_scan_error",
        "detail": "tesseract crashed",
        "entry_path": "/embedded/img1.png",
    }
    assert WarningEntry.from_dict(d) == w


def test_warning_entry_optional_path() -> None:
    w = WarningEntry(code="x", detail="y")
    d = w.to_dict()
    assert d == {"code": "x", "detail": "y", "entry_path": None}


def test_truncation_info_round_trip() -> None:
    t = TruncationInfo(
        reason=TruncationReason.MAX_EMBEDDED_ENTRIES, limit=5000, observed=6234
    )
    d = t.to_dict()
    assert d == {"reason": "max_embedded_entries", "limit": 5000, "observed": 6234}
    assert TruncationInfo.from_dict(d) == t


def test_embedded_entry_round_trip_full() -> None:
    e = EmbeddedEntry(
        path="/embedded/image1.png",
        parent_path="/",
        depth=1,
        content_type="image/png",
        size_bytes=1024,
        sha256="9f3d" + "0" * 60,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
        metadata={"Image-Width": "200"},
        text="",
        language=None,
        qr=QrResult(
            codes=[QrCode(data="x", format="QR_CODE")],
            skipped=None,
        ),
        ocr=OcrResult(text="hi", language="eng", duration_ms=100),
        error=None,
    )
    d = e.to_dict()
    assert EmbeddedEntry.from_dict(d) == e


def test_embedded_entry_root_no_parent() -> None:
    e = EmbeddedEntry(
        path="/",
        parent_path=None,
        depth=0,
        content_type="application/pdf",
        size_bytes=1000,
        sha256="ae1c" + "0" * 60,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
        metadata={},
        text="hello",
        language="en",
        qr=QrResult(),
        ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
        error=None,
    )
    assert e.parent_path is None
    assert e.depth == 0
    d = e.to_dict()
    assert d["parent_path"] is None
    assert EmbeddedEntry.from_dict(d) == e
