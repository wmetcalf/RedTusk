#!/usr/bin/env python3
"""Probe a Firecracker guest for its CRaC-compatible CPU feature value.

Self-contained host-side build tool for scripts/setup_firecracker_host.sh: boots
a one-shot probe microVM from a built rootfs and reports whether the baked CRaC
checkpoint will restore in that guest. Output (one line on stdout):

    COMPATIBLE            the checkpoint restores in the guest; ship as-is
    MISMATCH <value>      the guest needs -XX:CPUFeatures=<value>; rebuild pinned
    INCONCLUSIVE          the VM never reached the restore (bad kernel/rootfs/timeout)

Exit code mirrors the line: 0 COMPATIBLE, 10 MISMATCH, 20 INCONCLUSIVE, 2 error.

Stdlib-only on purpose — setup_firecracker_host.sh brings a *bare* host up, so
this must run without a blastbox/redtusk install. The canonical, unit-tested
implementation lives in blastbox.host.runtime.cpu_probe; keep the regex + the
classify logic in sync with it.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Matches the warp restore error that names the compatible value, e.g.
#   "... incompatible or missing CPU features, try using
#    -XX:CPUFeatures=0x102100055bbd7,0x1c8 on checkpoint."
_MISMATCH_RE = re.compile(
    r"incompatible or missing CPU features.*?-XX:CPUFeatures=([0-9a-fx,]+)",
    re.IGNORECASE | re.DOTALL,
)
# A successful warp restore prints "warp: Restore successful!" on the guest console
# (confirmed live on toolz2). That positive marker — NOT "[crac]", which shows up
# on the *failure* path — is what proves the checkpoint restored in this guest.
_DEFAULT_OK_MARKER = r"(?i)Restore successful"

COMPATIBLE, MISMATCH, INCONCLUSIVE = "COMPATIBLE", "MISMATCH", "INCONCLUSIVE"
_EXIT = {COMPATIBLE: 0, MISMATCH: 10, INCONCLUSIVE: 20}


def parse_cpu_mismatch(console: str) -> str | None:
    if not console:
        return None
    m = _MISMATCH_RE.search(console)
    return m.group(1) if m else None


def classify(
    console: str,
    *,
    restore_ok_marker: str = _DEFAULT_OK_MARKER,
) -> tuple[str, str | None]:
    """Pure classification of a captured guest console. Returns (status, value).

    A CPU-feature mismatch wins (names the value to pin); otherwise COMPATIBLE
    only if the success marker appeared — anything else is INCONCLUSIVE, never a
    silent COMPATIBLE.
    """
    value = parse_cpu_mismatch(console)
    if value is not None:
        return MISMATCH, value
    if re.search(restore_ok_marker, console):
        return COMPATIBLE, None
    return INCONCLUSIVE, None


def _build_config(kernel: str, rootfs: str, boot_args: str, mem_mib: int, vcpu: int) -> dict:
    return {
        "boot-source": {"kernel_image_path": kernel, "boot_args": boot_args},
        "drives": [
            {
                "drive_id": "rootfs",
                "path_on_host": rootfs,
                "is_root_device": True,
                "is_read_only": True,
            }
        ],
        "machine-config": {"vcpu_count": vcpu, "mem_size_mib": mem_mib, "smt": False},
    }


def _terminal(console: str, restore_ok_marker: str) -> bool:
    if parse_cpu_mismatch(console) is not None:
        return True
    if re.search(restore_ok_marker, console):
        return True
    return False


def probe(args: argparse.Namespace) -> tuple[str, str | None]:
    for label, p in (("kernel", args.kernel), ("rootfs", args.rootfs)):
        if not Path(p).is_file():
            print(f"fc_cpu_probe: {label} not found: {p}", file=sys.stderr)
            sys.exit(2)

    work = Path(tempfile.mkdtemp(prefix="fc-cpu-probe-"))
    try:
        cfg_path = work / "probe-fc-config.json"
        config = _build_config(args.kernel, args.rootfs, args.boot_args, args.mem_mib, args.vcpu)
        cfg_path.write_text(json.dumps(config), encoding="utf-8")
        log_path = work / "probe-fc.log"
        argv = [args.fc_bin, "--no-api", "--config-file", str(cfg_path)]

        deadline = time.monotonic() + args.timeout
        with open(log_path, "w") as log_fh:
            try:
                proc = subprocess.Popen(argv, stdout=log_fh, stderr=subprocess.STDOUT)
            except OSError as exc:
                print(f"fc_cpu_probe: failed to launch {args.fc_bin}: {exc}", file=sys.stderr)
                sys.exit(2)
            try:
                while True:
                    console = _read(log_path)
                    if _terminal(console, args.restore_ok_marker):
                        break
                    if proc.poll() is not None:
                        break
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.25)
            finally:
                _kill(proc)

        console = _read(log_path)
        status, value = classify(console, restore_ok_marker=args.restore_ok_marker)
        if status == INCONCLUSIVE:
            # Preserve the diagnostic before we delete the work dir: an
            # INCONCLUSIVE result usually means the VM never reached the restore.
            sys.stderr.write("fc_cpu_probe: INCONCLUSIVE — guest console tail:\n")
            sys.stderr.write(console[-1500:] + "\n")
        return status, value
    finally:
        # Don't leak the root-owned temp dir (FC config + guest console) per run.
        shutil.rmtree(work, ignore_errors=True)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _kill(proc: subprocess.Popen) -> None:
    try:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
    except Exception:  # best-effort teardown of a throwaway VM
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fc-bin", required=True)
    ap.add_argument("--kernel", required=True)
    ap.add_argument("--rootfs", required=True)
    ap.add_argument(
        "--boot-args",
        default="console=ttyS0 reboot=k panic=1 pci=off init=/init ro redtusk.vsock_port=10001",
    )
    ap.add_argument("--mem-mib", type=int, default=1024)
    ap.add_argument("--vcpu", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--restore-ok-marker", default=_DEFAULT_OK_MARKER)
    args = ap.parse_args(argv)

    try:
        re.compile(args.restore_ok_marker)
    except re.error as exc:
        ap.error(f"--restore-ok-marker is not a valid regex: {exc}")

    status, value = probe(args)
    print(f"{status} {value}" if value else status)
    return _EXIT[status]


if __name__ == "__main__":
    sys.exit(main())
