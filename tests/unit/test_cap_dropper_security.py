"""Security regression tests for high-density capability dropping."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_native_cap_dropper_clears_current_capability_sets() -> None:
    src = (ROOT / "worker_jvm/native/cap_dropper.c").read_text()

    assert "SYS_capget" in src
    assert "SYS_capset" in src
    assert "CAP_TO_MASK(cap)" in src
    assert "data[idx].effective &= ~mask" in src
    assert "data[idx].permitted &= ~mask" in src
    assert "data[idx].inheritable &= ~mask" in src
    assert "clear_capability(data, CAP_CHECKPOINT_RESTORE)" in src
    assert "clear_capability(data, CAP_SETPCAP)" in src
    assert "PR_CAPBSET_DROP, CAP_CHECKPOINT_RESTORE" in src
    assert "PR_CAPBSET_DROP, CAP_SETPCAP" in src


def test_java_cap_dropper_fails_closed_when_native_library_missing() -> None:
    src = (ROOT / "worker_jvm/src/main/java/io/redtusk/worker/CapDropper.java").read_text()

    assert "IllegalStateException" in src
    assert "capability dropper native library unavailable" in src
    assert "nativeDropCheckpointRestore()" in src
