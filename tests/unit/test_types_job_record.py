"""Tests for JobRecord and its lifecycle helpers."""
from __future__ import annotations

import uuid
from datetime import datetime

from redtusk.types import (
    EmbeddedEntry,
    ExtractionInfo,
    ExtractResult,
    InputInfo,
    JobRecord,
    JobState,
    LimitsInfo,
    OcrResult,
    QrResult,
    SandboxInfo,
    SkipReason,
)


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _result() -> ExtractResult:
    return ExtractResult(
        redtusk_version="0.1.0",
        input=InputInfo(
            sha256="ae1c" + "0" * 60,
            size_bytes=10,
            filename_hint=None,
            submitted_at=_ts("2026-05-04T18:23:11+00:00"),
        ),
        extraction=ExtractionInfo(
            root_content_type="text/plain",
            root_language="en",
            duration_ms=10,
            entries=[
                EmbeddedEntry(
                    path="/",
                    parent_path=None,
                    depth=0,
                    content_type="text/plain",
                    size_bytes=10,
                    sha256="ae1c" + "0" * 60,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
                    metadata={},
                    text="hi",
                    language="en",
                    qr=QrResult(),
                    ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
                )
            ],
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
            profile="default", runtime="runsc", appcds=True, ksm=True, crac=False
        ),
    )


def test_new_job_defaults() -> None:
    """A newly-created job is queued, no started/completed/result, no error."""
    job_id = str(uuid.uuid4())
    submitted = _ts("2026-05-04T18:23:11+00:00")
    job = JobRecord(
        id=job_id,
        state=JobState.QUEUED,
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    assert job.id == job_id
    assert job.state == JobState.QUEUED
    assert job.submitted_at == submitted
    assert job.started_at is None
    assert job.completed_at is None
    assert job.result is None
    assert job.error_code is None


def test_to_dict_round_trip_queued() -> None:
    submitted = _ts("2026-05-04T18:23:11+00:00")
    job = JobRecord(
        id="abc-123",
        state=JobState.QUEUED,
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint="x.pdf",
        result=None,
        error_code=None,
        error_detail=None,
    )
    d = job.to_dict()
    assert d["id"] == "abc-123"
    assert d["state"] == "queued"
    assert d["submitted_at"] == "2026-05-04T18:23:11+00:00"
    assert d["started_at"] is None
    assert d["completed_at"] is None
    assert d["filename_hint"] == "x.pdf"
    assert d["result"] is None
    assert JobRecord.from_dict(d) == job


def test_to_dict_round_trip_succeeded() -> None:
    submitted = _ts("2026-05-04T18:23:11+00:00")
    started = _ts("2026-05-04T18:23:12+00:00")
    completed = _ts("2026-05-04T18:23:13+00:00")
    job = JobRecord(
        id="abc-123",
        state=JobState.SUCCEEDED,
        submitted_at=submitted,
        started_at=started,
        completed_at=completed,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=_result(),
        error_code=None,
        error_detail=None,
    )
    d = job.to_dict()
    assert d["state"] == "succeeded"
    assert d["started_at"] == "2026-05-04T18:23:12+00:00"
    assert d["completed_at"] == "2026-05-04T18:23:13+00:00"
    assert d["result"]["redtusk_version"] == "0.1.0"
    assert JobRecord.from_dict(d) == job


def test_to_dict_round_trip_failed() -> None:
    job = JobRecord(
        id="abc-123",
        state=JobState.FAILED,
        submitted_at=_ts("2026-05-04T18:23:11+00:00"),
        started_at=_ts("2026-05-04T18:23:12+00:00"),
        completed_at=_ts("2026-05-04T18:23:13+00:00"),
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code="worker_crash",
        error_detail="container exited 139",
    )
    d = job.to_dict()
    assert d["state"] == "failed"
    assert d["error_code"] == "worker_crash"
    assert d["error_detail"] == "container exited 139"
    assert JobRecord.from_dict(d) == job


def test_is_terminal_via_state() -> None:
    """Convenience: job.state.is_terminal() is what callers use; sanity-check it from JobRecord."""
    submitted = _ts("2026-05-04T18:23:11+00:00")
    base = dict(
        id="x",
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    assert not JobRecord(state=JobState.QUEUED, **base).state.is_terminal()
    assert not JobRecord(state=JobState.RUNNING, **base).state.is_terminal()
    assert JobRecord(state=JobState.SUCCEEDED, **base).state.is_terminal()
    assert JobRecord(state=JobState.FAILED, **base).state.is_terminal()
