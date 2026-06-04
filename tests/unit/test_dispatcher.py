"""Unit tests for the Dispatcher class."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from redtusk.dispatcher import Dispatcher
from redtusk.errors import PoolExhaustedError, WorkerError
from redtusk.limits import Limits
from redtusk.types import ExtractResult, JobRecord, JobState, Slot, SlotState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SHA256 = "a" * 64


def make_metadata(sha256: str, job_id: str = "test-job") -> dict:
    return {
        "redtusk_version": "0.1.0",
        "input": {
            "sha256": sha256,
            "size_bytes": 100,
            "filename_hint": "test.txt",
            "submitted_at": "2026-05-05T00:00:00Z",
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
                    "size_bytes": 100,
                    "sha256": sha256,
                    "metadata": {},
                    "text": "hello",
                    "language": "en",
                    "qr": {"codes": [], "skipped": None},
                    "ocr": {"text": "", "language": None, "duration_ms": 0, "skipped": "no_images"},
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
            "runtime": "runc",
            "appcds": True,
            "ksm": False,
            "crac": False,
        },
    }


def make_job(sha256: str = _SHA256, input_path: str | None = None) -> JobRecord:
    return JobRecord(
        id="test-job",
        state=JobState.RUNNING,
        submitted_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        completed_at=None,
        input_sha256=sha256,
        input_size_bytes=100,
        filename_hint="test.txt",
        input_path=input_path,
        result=None,
        error_code=None,
        error_detail=None,
    )


def make_slot(tmp_path: Path) -> Slot:
    slot_dir = tmp_path / "slot"
    (slot_dir / "in").mkdir(parents=True)
    (slot_dir / "out").mkdir(parents=True)
    return Slot(
        id=uuid4(),
        state=SlotState.ASSIGNED,
        container_id="ctr-123",
        scratch_dir=slot_dir,
        assigned_job_id="test-job",
        assigned_at=datetime.now(UTC),
        spawn_attempts=0,
        is_burst=False,
    )


def make_dispatcher(pool: MagicMock, store: MagicMock, runtime: MagicMock) -> Dispatcher:
    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts",
        scratch_root="/tmp/scratch",
        max_metadata_bytes=64 * 1024 * 1024,
        max_artifact_bytes=1024 * 1024,
    )
    return Dispatcher(pool=pool, store=store, worker_runtime=runtime, limits=limits)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path(tmp_path: Path) -> None:
    """Happy path: dispatch succeeds, job state transitions to SUCCEEDED."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job()

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    pool.is_healthy = MagicMock(return_value=True)
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)

    # Write metadata.json into out/
    metadata = make_metadata(_SHA256)
    (tmp_path / "slot" / "out" / "metadata.json").write_text(json.dumps(metadata))

    dispatcher = make_dispatcher(pool, store, runtime)

    with patch("redtusk.dispatcher._copy_artifacts"):
        await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.SUCCEEDED
    assert updated_job.result is not None
    pool.release.assert_called_once_with(slot, success=True)


@pytest.mark.asyncio
async def test_worker_crash(tmp_path: Path) -> None:
    """Worker exits with code 1 -> job state FAILED, error_code='worker_crash'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job()

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=1)

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "worker_crash"
    pool.release.assert_called_once_with(slot, success=False)


@pytest.mark.asyncio
async def test_worker_timeout(tmp_path: Path) -> None:
    """Worker exits with code 137 -> error_code='timeout'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job()

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=137)

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "timeout"
    pool.release.assert_called_once_with(slot, success=False)


@pytest.mark.asyncio
async def test_pool_exhausted() -> None:
    """Pool raises PoolExhaustedError -> job state FAILED, error_code='pool_exhausted'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    job = make_job()
    pool.claim = AsyncMock(side_effect=PoolExhaustedError(10.0))
    pool.release = AsyncMock()

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    store.update.assert_called_once()
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "pool_exhausted"
    pool.release.assert_not_called()


@pytest.mark.asyncio
async def test_metadata_missing(tmp_path: Path) -> None:
    """Worker exits 0 but no metadata.json -> error_code='metadata_missing'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job()

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)
    # Do NOT write metadata.json

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "metadata_missing"
    pool.release.assert_called_once_with(slot, success=True)


@pytest.mark.asyncio
async def test_sha256_mismatch(tmp_path: Path) -> None:
    """metadata.json has different sha256 than job -> error_code='metadata_invalid'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job(sha256=_SHA256)

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)

    # Write metadata.json with a different sha256
    wrong_sha256 = "b" * 64
    metadata = make_metadata(wrong_sha256)
    (tmp_path / "slot" / "out" / "metadata.json").write_text(json.dumps(metadata))

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "metadata_invalid"
    assert "SHA-256 mismatch" in (updated_job.error_detail or "")
    pool.release.assert_called_once_with(slot, success=True)


@pytest.mark.asyncio
async def test_schema_validation_failure(tmp_path: Path) -> None:
    """metadata.json fails schema validation -> error_code='metadata_invalid'."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    job = make_job(sha256=_SHA256)

    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)

    # Write metadata.json that is structurally invalid (missing required fields)
    bad_metadata = {"redtusk_version": "0.1.0"}
    (tmp_path / "slot" / "out" / "metadata.json").write_text(json.dumps(bad_metadata))

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._dispatch(job)

    assert store.update.call_count == 2
    updated_job: JobRecord = store.update.call_args[0][0]
    assert updated_job.state == JobState.FAILED
    assert updated_job.error_code == "metadata_invalid"
    pool.release.assert_called_once_with(slot, success=True)


def test_is_healthy() -> None:
    """is_healthy() delegates to pool.is_healthy()."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    pool.is_healthy = MagicMock(return_value=True)
    dispatcher = make_dispatcher(pool, store, runtime)
    assert dispatcher.is_healthy() is True

    pool.is_healthy.return_value = False
    assert dispatcher.is_healthy() is False


def test_copy_artifacts_enforces_total_size_cap(tmp_path: Path) -> None:
    from redtusk.dispatcher import _copy_artifacts

    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "metadata.json").write_bytes(b"abcd")
    (src / "embedded.bin").write_bytes(b"efgh")

    with pytest.raises(ValueError, match="artifacts too large"):
        _copy_artifacts(src, dst, max_bytes=7)


# ---------------------------------------------------------------------------
# submit_sync tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_sync_happy_path(tmp_path: Path) -> None:
    """submit_sync returns ExtractResult when worker exits 0 and metadata is valid."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    body = b"hello world"
    filename = "test.txt"
    sha256 = hashlib.sha256(body).hexdigest()

    slot = make_slot(tmp_path)
    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)

    # Write a valid metadata.json into the slot's out/ dir
    metadata = make_metadata(sha256)
    (tmp_path / "slot" / "out" / "metadata.json").write_text(json.dumps(metadata))

    dispatcher = make_dispatcher(pool, store, runtime)
    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts",
        scratch_root=str(tmp_path / "scratch"),
        max_metadata_bytes=64 * 1024 * 1024,
    )

    result = await dispatcher.submit_sync(body, filename, limits)

    assert isinstance(result, ExtractResult)
    pool.release.assert_called_once_with(slot, success=True)


@pytest.mark.asyncio
async def test_submit_sync_pool_exhausted(tmp_path: Path) -> None:
    """submit_sync propagates PoolExhaustedError when pool is full."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    pool.claim = AsyncMock(side_effect=PoolExhaustedError(5.0))
    pool.release = AsyncMock()

    dispatcher = make_dispatcher(pool, store, runtime)
    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts",
        scratch_root=str(tmp_path / "scratch"),
        max_metadata_bytes=64 * 1024 * 1024,
    )

    with pytest.raises(PoolExhaustedError):
        await dispatcher.submit_sync(b"data", "doc.txt", limits)

    pool.release.assert_not_called()


@pytest.mark.asyncio
async def test_submit_sync_sha256_mismatch(tmp_path: Path) -> None:
    """submit_sync raises WorkerError when metadata sha256 doesn't match body sha256."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    body = b"hello world"
    filename = "test.txt"
    wrong_sha256 = "b" * 64

    slot = make_slot(tmp_path)
    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=0)

    # Write metadata with wrong sha256
    metadata = make_metadata(wrong_sha256)
    (tmp_path / "slot" / "out" / "metadata.json").write_text(json.dumps(metadata))

    dispatcher = make_dispatcher(pool, store, runtime)
    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts",
        scratch_root=str(tmp_path / "scratch"),
        max_metadata_bytes=64 * 1024 * 1024,
    )

    with pytest.raises(WorkerError, match="SHA-256 mismatch"):
        await dispatcher.submit_sync(body, filename, limits)

    pool.release.assert_called_once_with(slot, success=False)


@pytest.mark.asyncio
async def test_submit_sync_worker_crash(tmp_path: Path) -> None:
    """submit_sync raises WorkerError and releases slot with success=False on worker crash."""
    pool = MagicMock()
    store = AsyncMock()
    runtime = AsyncMock()

    slot = make_slot(tmp_path)
    pool.claim = AsyncMock(return_value=slot)
    pool.release = AsyncMock()
    runtime.signal_job = AsyncMock()
    runtime.wait = AsyncMock(return_value=1)

    dispatcher = make_dispatcher(pool, store, runtime)
    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts",
        scratch_root=str(tmp_path / "scratch"),
        max_metadata_bytes=64 * 1024 * 1024,
    )

    with pytest.raises(WorkerError, match="worker exited 1"):
        await dispatcher.submit_sync(b"data", "doc.txt", limits)

    pool.release.assert_called_once_with(slot, success=False)


@pytest.mark.asyncio
async def test_recover_orphaned_running_jobs() -> None:
    """Dispatcher.start() marks every RUNNING job as failed before the claim loop starts.

    RUNNING rows whose worker container did not survive a dispatcher restart
    would otherwise block forever — list endpoints would keep returning them
    and the pool would mis-account capacity.
    """
    pool = MagicMock()
    pool.start = AsyncMock()
    pool.stop = AsyncMock()
    runtime = MagicMock()

    stuck1 = JobRecord(
        id="stuck-1",
        submitted_at=datetime.now(UTC),
        state=JobState.RUNNING,
        input_sha256=_SHA256,
        input_size_bytes=10,
        filename_hint="a.xls",
        started_at=datetime.now(UTC),
    )
    stuck2 = JobRecord(
        id="stuck-2",
        submitted_at=datetime.now(UTC),
        state=JobState.RUNNING,
        input_sha256=_SHA256,
        input_size_bytes=10,
        filename_hint="b.xls",
        started_at=datetime.now(UTC),
    )

    store = AsyncMock()
    store.list_recent = AsyncMock(return_value=[stuck1, stuck2])
    store.update = AsyncMock()

    dispatcher = make_dispatcher(pool, store, runtime)
    try:
        await dispatcher._recover_orphaned_running_jobs()
    finally:
        # No claim loop / pool was started — just exercising the helper.
        pass

    # Both jobs were re-stamped as FAILED with the canonical code.
    store.list_recent.assert_awaited_once_with(limit=10000, state="running")
    assert store.update.await_count == 2
    for job in (stuck1, stuck2):
        assert job.state == JobState.FAILED
        assert job.error_code == "dispatcher_restart"
        assert job.error_detail and "restart" in job.error_detail
        assert job.completed_at is not None


@pytest.mark.asyncio
async def test_recover_orphaned_running_jobs_no_stuck() -> None:
    """No RUNNING rows means no store.update calls — fast, quiet, idempotent."""
    pool = MagicMock()
    runtime = MagicMock()
    store = AsyncMock()
    store.list_recent = AsyncMock(return_value=[])
    store.update = AsyncMock()

    dispatcher = make_dispatcher(pool, store, runtime)
    await dispatcher._recover_orphaned_running_jobs()

    store.list_recent.assert_awaited_once_with(limit=10000, state="running")
    store.update.assert_not_called()


@pytest.mark.asyncio
async def test_preflight_state_dirs_creates_and_passes(tmp_path: Path) -> None:
    """Pre-flight succeeds when scratch/artifact roots are writable."""
    pool = MagicMock()
    runtime = MagicMock()
    store = AsyncMock()

    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root=str(tmp_path / "art"),
        scratch_root=str(tmp_path / "scr"),
        max_metadata_bytes=64 * 1024 * 1024,
    )
    dispatcher = Dispatcher(pool=pool, store=store, worker_runtime=runtime, limits=limits)

    # Should be a clean no-op + mkdir; no exception.
    dispatcher._preflight_state_dirs()
    assert (tmp_path / "art").is_dir()
    assert (tmp_path / "scr").is_dir()


@pytest.mark.asyncio
async def test_preflight_state_dirs_unwritable_raises(tmp_path: Path) -> None:
    """Pre-flight raises a clear DispatchError when a state dir isn't writable."""
    import os
    pool = MagicMock()
    runtime = MagicMock()
    store = AsyncMock()

    # Lock down the artifact root so we can't write to it.
    locked = tmp_path / "locked"
    locked.mkdir()
    # Drop write bits for owner/group/other. mkdir() inside still succeeds
    # (because exist_ok=True on an existing dir is a no-op), but the
    # write-probe will fail. 0o555 = read+execute, no write.
    os.chmod(locked, 0o555)

    limits = Limits(
        job_timeout_s=10,
        sync_queue_timeout_s=5,
        artifact_root=str(locked),
        scratch_root=str(tmp_path / "scr"),
        max_metadata_bytes=64 * 1024 * 1024,
    )
    dispatcher = Dispatcher(pool=pool, store=store, worker_runtime=runtime, limits=limits)

    from redtusk.errors import DispatchError
    # Running as root in CI defeats chmod-based denial — only assert the
    # rejection when we are NOT root.
    if os.geteuid() != 0:
        with pytest.raises(DispatchError, match="not writable"):
            dispatcher._preflight_state_dirs()

    os.chmod(locked, 0o755)  # restore so tmp cleanup works


def test_sanitize_error_detail_strips_host_paths():
    from redtusk.dispatcher import _sanitize_error_detail

    s = _sanitize_error_detail(
        "[Errno 2] No such file: /var/lib/redtusk/scratch/abc-123/out/metadata.json"
    )
    assert "/var/lib/redtusk" not in s
    assert "<path>" in s
    # Path-free details and 'and/or' are left intact.
    assert _sanitize_error_detail("worker exited 137") == "worker exited 137"
    assert _sanitize_error_detail("use this and/or that") == "use this and/or that"


@pytest.mark.asyncio
async def test_api_role_has_no_pool_and_starts_cleanly():
    """api role: no pool/claim-loop (no /dev/kvm). start() is a no-op, readyz is
    healthy, and there's no pool fatal-error to surface."""
    store = AsyncMock()
    limits = Limits(
        job_timeout_s=10, sync_queue_timeout_s=5,
        artifact_root="/tmp/artifacts", scratch_root="/tmp/scratch",
        max_metadata_bytes=64 * 1024 * 1024, max_artifact_bytes=1024 * 1024,
    )
    d = Dispatcher(pool=None, store=store, worker_runtime=None, limits=limits, role="api")
    await d.start()  # must not spawn / touch a pool
    assert d.is_healthy() is True
    assert d.fatal_spawn_error is None
    await d.stop()  # must not touch a None pool
