"""JSON Schema for the canonical rmeta document.

The dispatcher validates every worker-produced metadata.json against
this schema before trusting the worker's output. The schema enforces
shape, types, and the small set of value vocabularies (skip reasons,
truncation reasons, profile names) that have closed enumerations.
"""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from redtusk.errors import SchemaValidationError

_SHA256_PATTERN = "^[a-f0-9]{64}$"
_SKIP_REASONS = ["no_images", "timeout_budget", "error", "disabled", "blank_image"]
_TRUNCATION_REASONS = ["max_embedded_entries", "max_recursion_depth", "max_extracted_bytes"]
_PROFILES = ["default", "high-density"]

_QR_CODE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["data", "format"],
    "properties": {
        "data":      {"type": "string"},
        "format":    {"type": "string"},
        "raw_bytes": {"type": ["string", "null"]},
        "position":  {"type": ["string", "null"]},
    },
}

_QR_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["codes", "skipped"],
    "properties": {
        "codes": {"type": "array", "items": _QR_CODE_SCHEMA},
        "skipped": {"type": ["string", "null"], "enum": [*_SKIP_REASONS, None]},
    },
}

_OCR_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text", "language", "duration_ms", "skipped"],
    "properties": {
        "text": {"type": "string"},
        "language": {"type": ["string", "null"]},
        "duration_ms": {"type": "integer", "minimum": 0},
        "skipped": {"type": ["string", "null"], "enum": [*_SKIP_REASONS, None]},
    },
}

_ENTRY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "path",
        "parent_path",
        "depth",
        "content_type",
        "size_bytes",
        "sha256",
        "metadata",
        "text",
        "language",
        "qr",
        "ocr",
        "error",
    ],
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "parent_path": {"type": ["string", "null"]},
        "depth": {"type": "integer", "minimum": 0},
        "content_type": {"type": "string", "minLength": 1},
        "size_bytes": {"type": "integer", "minimum": 0},
        # null for depth>0 entries until DigestingParser provides real byte hashes;
        # pattern not enforced here — dispatcher cross-checks root sha256 separately
        "sha256":         {"type": ["string", "null"]},
        "md5":            {"type": ["string", "null"]},
        "sha1":           {"type": ["string", "null"]},
        "has_thumbnail":  {"type": "boolean"},
        "phash":     {"type": ["string", "null"]},
        "colorhash": {"type": ["string", "null"]},
        "metadata": {"type": "object"},
        "text": {"type": "string"},
        "language": {"type": ["string", "null"]},
        "qr": _QR_RESULT_SCHEMA,
        "ocr": _OCR_RESULT_SCHEMA,
        "error": {"type": ["string", "null"]},
    },
}

_ROOT_ENTRY_SCHEMA = {
    "allOf": [
        _ENTRY_SCHEMA,
        {
            "type": "object",
            "properties": {
                "path": {"const": "/"},
                "depth": {"const": 0},
                "parent_path": {"const": None},
            },
        },
    ]
}

RMETA_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "redtusk_version",
        "input",
        "extraction",
        "limits",
        "truncated",
        "warnings",
        "sandbox",
    ],
    "properties": {
        "redtusk_version": {"type": "string", "minLength": 1},
        "input": {
            "type": "object",
            "additionalProperties": False,
            "required": ["sha256", "size_bytes", "filename_hint", "submitted_at"],
            "properties": {
                "sha256": {"type": "string", "pattern": _SHA256_PATTERN},
                "size_bytes": {"type": "integer", "minimum": 0},
                "filename_hint": {"type": ["string", "null"]},
                "submitted_at": {"type": "string", "format": "date-time"},
            },
        },
        "extraction": {
            "type": "object",
            "additionalProperties": False,
            "required": ["root_content_type", "root_language", "duration_ms", "entries"],
            "properties": {
                "root_content_type": {"type": "string", "minLength": 1},
                "root_language": {"type": ["string", "null"]},
                "duration_ms": {"type": "integer", "minimum": 0},
                "entries": {
                    "type": "array",
                    "minItems": 1,
                    "items": _ENTRY_SCHEMA,
                    "prefixItems": [_ROOT_ENTRY_SCHEMA],
                },
            },
        },
        "limits": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "max_recursion_depth",
                "max_embedded_entries",
                "max_extracted_bytes",
                "ocr_timeout_s",
            ],
            "properties": {
                "max_recursion_depth": {"type": "integer", "minimum": 0},
                "max_embedded_entries": {"type": "integer", "minimum": 0},
                "max_extracted_bytes": {"type": "integer", "minimum": 0},
                "ocr_timeout_s": {"type": "integer", "minimum": 0},
            },
        },
        "truncated": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reason", "limit", "observed"],
                    "properties": {
                        "reason": {"enum": _TRUNCATION_REASONS},
                        "limit": {"type": "integer", "minimum": 0},
                        "observed": {"type": "integer", "minimum": 0},
                    },
                },
            ]
        },
        "warnings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "detail", "entry_path"],
                "properties": {
                    "code": {"type": "string", "minLength": 1},
                    "detail": {"type": "string"},
                    "entry_path": {"type": ["string", "null"]},
                },
            },
        },
        "sandbox": {
            "type": "object",
            "additionalProperties": False,
            "required": ["profile", "runtime", "appcds", "ksm", "crac"],
            "properties": {
                "profile": {"enum": _PROFILES},
                "runtime": {"type": "string", "minLength": 1},
                "appcds": {"type": "boolean"},
                "ksm": {"type": "boolean"},
                "crac": {"type": "boolean"},
            },
        },
    },
}

_VALIDATOR = Draft202012Validator(RMETA_SCHEMA, format_checker=FormatChecker())


def validate_rmeta(doc: dict[str, Any]) -> None:
    """Validate ``doc`` against RMETA_SCHEMA.

    Raises ``SchemaValidationError`` (with a JSON-pointer-ish path) on any
    violation. The first error is reported; we intentionally don't aggregate
    every error since the dispatcher rejects on first failure anyway.
    """
    try:
        _VALIDATOR.validate(doc)
    except ValidationError as e:
        path = ".".join(str(p) for p in e.absolute_path) or "<root>"
        raise SchemaValidationError(path=path, reason=e.message) from e
