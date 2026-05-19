"""Shared fixtures for HTTP tests."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from redtusk.api import create_app
from redtusk.limits import Limits
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


def minimal_extract_result(
    sha256: str = "a" * 64,
    content_type: str = "text/plain",
    text: str = "hello world",
) -> ExtractResult:
    """Build a minimal valid ExtractResult for testing."""
    entry = EmbeddedEntry(
        path="/",
        parent_path=None,
        depth=0,
        content_type=content_type,
        size_bytes=len(text.encode()),
        sha256=sha256,
        md5=None,
        sha1=None,
        has_thumbnail=False,
        phash=None,
        colorhash=None,
        metadata={"Author": "Test"},
        text=text,
        language="en",
        qr=QrResult(codes=[], skipped=None),
        ocr=OcrResult(text="", language=None, duration_ms=0, skipped=SkipReason.NO_IMAGES),
        error=None,
    )
    return ExtractResult(
        redtusk_version="0.1.0",
        input=InputInfo(
            sha256=sha256,
            size_bytes=len(text.encode()),
            filename_hint="test.txt",
            submitted_at=datetime.now(UTC),
        ),
        extraction=ExtractionInfo(
            root_content_type=content_type,
            root_language="en",
            duration_ms=10,
            entries=[entry],
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
            runtime="runc",
            appcds=True,
            ksm=False,
            crac=False,
        ),
    )


def minimal_job_record(
    job_id: str | None = None,
    state: JobState = JobState.QUEUED,
    result: ExtractResult | None = None,
) -> JobRecord:
    return JobRecord(
        id=job_id or str(uuid4()),
        state=state,
        submitted_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
        input_sha256="a" * 64,
        input_size_bytes=100,
        filename_hint="test.txt",
        result=result,
        error_code=None,
        error_detail=None,
        input_path=None,
    )


@pytest.fixture
def mock_dispatcher():
    d = MagicMock()
    d.is_healthy.return_value = True
    d.submit_sync = AsyncMock(return_value=minimal_extract_result())
    d.start = AsyncMock()
    d.stop = AsyncMock()
    return d


@pytest.fixture
def mock_store():
    s = MagicMock()
    s.create = AsyncMock()
    s.get = AsyncMock(return_value=None)
    s.update = AsyncMock()
    s.delete = AsyncMock(return_value=True)
    s.list_recent = AsyncMock(return_value=[])
    s.count_by_state = AsyncMock(return_value=0)
    return s


@pytest.fixture
def limits(tmp_path):
    return Limits(artifact_root=str(tmp_path))


@pytest.fixture
def client(mock_dispatcher, mock_store, limits):
    app = create_app(dispatcher=mock_dispatcher, store=mock_store, limits=limits)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
