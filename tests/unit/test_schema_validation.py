"""Tests for the canonical rmeta JSON schema validator."""
from __future__ import annotations

import pytest

from redtusk.errors import SchemaValidationError
from redtusk.schema import RMETA_SCHEMA, validate_rmeta


def _good_rmeta() -> dict:
    return {
        "redtusk_version": "0.1.0",
        "tika_version": "3.0.0",
        "input": {
            "sha256": "ae" + "0" * 62,
            "size_bytes": 10,
            "filename_hint": "x.pdf",
            "submitted_at": "2026-05-04T18:23:11+00:00",
        },
        "extraction": {
            "root_content_type": "text/plain",
            "root_language": "en",
            "duration_ms": 10,
            "entries": [
                {
                    "path": "/",
                    "parent_path": None,
                    "depth": 0,
                    "content_type": "text/plain",
                    "size_bytes": 10,
                    "sha256": "ae" + "0" * 62,
                    "metadata": {},
                    "text": "hi",
                    "language": "en",
                    "qr": {"codes": [], "skipped": None},
                    "ocr": {
                        "text": "",
                        "language": None,
                        "duration_ms": 0,
                        "skipped": "no_images",
                    },
                    "error": None,
                }
            ],
        },
        "limits": {
            "max_recursion_depth": 10,
            "max_embedded_entries": 5000,
            "max_extracted_bytes": 524288000,
            "ocr_timeout_s": 60,
        },
        "truncated": None,
        "warnings": [],
        "sandbox": {
            "profile": "default",
            "runtime": "runsc",
            "appcds": True,
            "ksm": True,
            "crac": False,
        },
    }


def test_schema_is_dict() -> None:
    assert isinstance(RMETA_SCHEMA, dict)
    assert RMETA_SCHEMA["$schema"].startswith("http")
    assert RMETA_SCHEMA["type"] == "object"


def test_minimal_good_doc_passes() -> None:
    validate_rmeta(_good_rmeta())  # raises on failure


def test_truncated_object_passes() -> None:
    doc = _good_rmeta()
    doc["truncated"] = {
        "reason": "max_embedded_entries",
        "limit": 5000,
        "observed": 6234,
    }
    validate_rmeta(doc)


def test_warnings_populated_passes() -> None:
    doc = _good_rmeta()
    doc["warnings"] = [
        {
            "code": "ocr_scan_error",
            "detail": "tesseract crashed",
            "entry_path": "/embedded/img1.png",
        },
        {"code": "qr_scan_error", "detail": "zbar segfault", "entry_path": None},
    ]
    validate_rmeta(doc)


def test_missing_top_level_key_fails() -> None:
    doc = _good_rmeta()
    del doc["sandbox"]
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "sandbox" in str(ei.value)


def test_extra_top_level_key_fails() -> None:
    doc = _good_rmeta()
    doc["unexpected_field"] = "garbage"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "unexpected_field" in str(ei.value)


def test_invalid_state_in_truncation_reason_fails() -> None:
    doc = _good_rmeta()
    doc["truncated"] = {"reason": "garbage", "limit": 1, "observed": 2}
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_invalid_skipped_value_fails() -> None:
    doc = _good_rmeta()
    doc["extraction"]["entries"][0]["qr"]["skipped"] = "garbage"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_negative_size_bytes_fails() -> None:
    doc = _good_rmeta()
    doc["input"]["size_bytes"] = -1
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_sha256_must_be_64_hex() -> None:
    doc = _good_rmeta()
    doc["input"]["sha256"] = "tooshort"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_root_entry_must_have_path_slash() -> None:
    """The dispatcher relies on entries[0].path == '/'.

    The schema enforces it via const on the first entry's path.
    """
    doc = _good_rmeta()
    doc["extraction"]["entries"][0]["path"] = "/not-root"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "path" in str(ei.value)


def test_entries_must_not_be_empty() -> None:
    doc = _good_rmeta()
    doc["extraction"]["entries"] = []
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_qr_field_required_on_every_entry() -> None:
    doc = _good_rmeta()
    del doc["extraction"]["entries"][0]["qr"]
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_ocr_field_required_on_every_entry() -> None:
    doc = _good_rmeta()
    del doc["extraction"]["entries"][0]["ocr"]
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_invalid_profile_fails() -> None:
    doc = _good_rmeta()
    doc["sandbox"]["profile"] = "garbage"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_validation_error_includes_path() -> None:
    """SchemaValidationError.path should point at the offending field."""
    doc = _good_rmeta()
    doc["input"]["size_bytes"] = "not-a-number"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "input" in ei.value.path
    assert "size_bytes" in ei.value.path


def test_invalid_submitted_at_date_format_fails() -> None:
    """The format: date-time constraint must be enforced, not just structural."""
    doc = _good_rmeta()
    doc["input"]["submitted_at"] = "NOT-A-DATE-AT-ALL-PWNED"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)
