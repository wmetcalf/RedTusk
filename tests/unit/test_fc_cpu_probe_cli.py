"""Tests for scripts/fc_cpu_probe.py classify (the host-side probe CLI).

Pure classification, kept in sync with blastbox.host.runtime.cpu_probe. The live
FC boot is exercised by the blastbox unit tests; here we just lock the
mismatch/compatible/inconclusive decision the build script branches on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import fc_cpu_probe as p  # noqa: E402  (path injected above)

_REAL_MISMATCH = (
    "[    0.412][crac] Restore failed due to incompatible or missing CPU "
    "features, try using -XX:CPUFeatures=0x102100055bbd7,0x1c8 on checkpoint.\n"
    "Error: Could not create the Java Virtual Machine.\n"
)
# A successful restore prints "warp: Restore successful!" (confirmed live on toolz2).
_COMPATIBLE = "init: bound vsock\n0.539615: warp: Restore successful!\n"
_NO_CRAC = "[    0.10] Kernel panic - not syncing: VFS: Unable to mount root\n"


def test_classify_mismatch():
    status, value = p.classify(_REAL_MISMATCH)
    assert status == p.MISMATCH
    assert value == "0x102100055bbd7,0x1c8"


def test_classify_compatible_on_success_marker():
    assert p.classify(_COMPATIBLE) == (p.COMPATIBLE, None)


def test_classify_inconclusive_without_success_or_mismatch():
    assert p.classify(_NO_CRAC)[0] == p.INCONCLUSIVE
    assert p.classify("")[0] == p.INCONCLUSIVE
    # [crac] alone (the old, wrong heuristic) must NOT read as COMPATIBLE.
    assert p.classify("[crac] restoring\n")[0] == p.INCONCLUSIVE


def test_classify_custom_ok_marker():
    assert p.classify("worker is up\n", restore_ok_marker="worker is up")[0] == p.COMPATIBLE


def test_exit_codes_distinct():
    assert {p._EXIT[p.COMPATIBLE], p._EXIT[p.MISMATCH], p._EXIT[p.INCONCLUSIVE]} == {0, 10, 20}


def test_main_rejects_invalid_marker():
    argv = ["--fc-bin", "fc", "--kernel", "/k", "--rootfs", "/r", "--restore-ok-marker", "(bad"]
    with pytest.raises(SystemExit):
        p.main(argv)
