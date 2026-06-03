"""Tests for the Firecracker CRaC CPU-feature-mismatch detector.

Two layers:
- The vendored parser (redtusk.fc_cpu_features.parse_cpu_mismatch) — kept in sync
  with the canonical blastbox.host.runtime.cpu_features.
- The FirecrackerWorkerRuntime wiring: on a warmup timeout, it reads the slot's
  captured guest console (fc.log) and converts the otherwise-opaque timeout into
  an actionable FcCpuFeatureMismatchError naming the -XX:CPUFeatures value to rebuild
  with — while staying silent (generic timeout) on a clean console or no log.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from redtusk.errors import FcCpuFeatureMismatchError
from redtusk.fc_cpu_features import CpuFeatureMismatch, parse_cpu_mismatch
from redtusk.limits import Limits
from redtusk.observability import metrics
from redtusk.types import Slot, SlotState
from redtusk.worker_runtime import FirecrackerWorkerRuntime

# The actual guest serial console from the 2026-06-02 incident (commit 8838962).
_REAL_MISMATCH = """\
[    0.412][crac] Restore failed due to incompatible or missing CPU features, \
try using -XX:CPUFeatures=0x102100055bbd7,0x1c8 on checkpoint.
[    0.413][crac] Failed to restore from /app/checkpoint
Error: Could not create the Java Virtual Machine.
"""

_CLEAN_BOOT = "[    0.401] redtusk-worker READY\n"


# ---------------------------------------------------------------------------
# Vendored parser (sync with blastbox canonical)
# ---------------------------------------------------------------------------


def test_parses_real_mismatch_value():
    mm = parse_cpu_mismatch(_REAL_MISMATCH)
    assert isinstance(mm, CpuFeatureMismatch)
    assert mm.needed == "0x102100055bbd7,0x1c8"
    assert "checkpoint" not in mm.needed and " " not in mm.needed


def test_clean_or_empty_returns_none():
    assert parse_cpu_mismatch(_CLEAN_BOOT) is None
    assert parse_cpu_mismatch("") is None
    assert parse_cpu_mismatch(None) is None  # type: ignore[arg-type]


def test_unrelated_jvm_error_not_misread():
    other = "Error: Could not create the Java Virtual Machine.\nOOM killed.\n"
    assert parse_cpu_mismatch(other) is None


# ---------------------------------------------------------------------------
# FirecrackerWorkerRuntime wiring
# ---------------------------------------------------------------------------


def _runtime(tmp_path: Path) -> FirecrackerWorkerRuntime:
    return FirecrackerWorkerRuntime(limits=Limits(scratch_root=str(tmp_path)))


def _slot(scratch_dir: Path) -> Slot:
    return Slot(
        id=uuid4(),
        state=SlotState.WARMING,
        container_id="fc-1",
        scratch_dir=scratch_dir,
        assigned_job_id=None,
        assigned_at=datetime.now(tz=UTC),
        spawn_attempts=0,
        is_burst=False,
    )


@pytest.mark.asyncio
async def test_diagnose_raises_and_counts_on_mismatch(tmp_path: Path):
    (tmp_path / "fc.log").write_text(_REAL_MISMATCH)
    rt, slot = _runtime(tmp_path), _slot(tmp_path)

    before = metrics.fc_cpu_feature_mismatch_total._value.get()
    with pytest.raises(FcCpuFeatureMismatchError) as ei:
        await rt._raise_if_cpu_feature_mismatch(slot)
    assert ei.value.needed == "0x102100055bbd7,0x1c8"
    assert "-XX:CPUFeatures=0x102100055bbd7,0x1c8" in str(ei.value)
    assert metrics.fc_cpu_feature_mismatch_total._value.get() == before + 1


@pytest.mark.asyncio
async def test_diagnose_silent_on_clean_console(tmp_path: Path):
    (tmp_path / "fc.log").write_text(_CLEAN_BOOT)
    rt, slot = _runtime(tmp_path), _slot(tmp_path)
    await rt._raise_if_cpu_feature_mismatch(slot)  # must not raise


@pytest.mark.asyncio
async def test_diagnose_silent_when_no_log(tmp_path: Path):
    rt, slot = _runtime(tmp_path), _slot(tmp_path)  # no fc.log written
    await rt._raise_if_cpu_feature_mismatch(slot)  # must not raise


@pytest.mark.asyncio
async def test_diagnose_silent_when_no_scratch_dir(tmp_path: Path):
    rt = _runtime(tmp_path)
    slot = _slot(tmp_path)
    slot.scratch_dir = None
    await rt._raise_if_cpu_feature_mismatch(slot)  # must not raise


class _TimeoutServer:
    """Stands in for VsockSlotServer whose accept_ready never signals READY."""

    def accept_ready(self) -> None:
        raise TimeoutError


@pytest.mark.asyncio
async def test_poll_fifo_raises_on_cpu_mismatch_after_timeout(tmp_path: Path):
    (tmp_path / "fc.log").write_text(_REAL_MISMATCH)
    rt, slot = _runtime(tmp_path), _slot(tmp_path)
    rt._vsock_servers[slot.id] = _TimeoutServer()  # type: ignore[assignment]
    with pytest.raises(FcCpuFeatureMismatchError):
        await rt.poll_fifo(slot, timeout=0.05)


@pytest.mark.asyncio
async def test_poll_fifo_returns_false_on_generic_timeout(tmp_path: Path):
    # Timeout with no CPU-feature signature → unchanged generic behavior.
    (tmp_path / "fc.log").write_text(_CLEAN_BOOT)
    rt, slot = _runtime(tmp_path), _slot(tmp_path)
    rt._vsock_servers[slot.id] = _TimeoutServer()  # type: ignore[assignment]
    assert await rt.poll_fifo(slot, timeout=0.05) is False
