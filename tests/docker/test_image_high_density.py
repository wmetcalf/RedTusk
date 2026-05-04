"""Docker tests for the high-density (CRaC) worker image.

Build requirements (elevated capabilities needed for CRIU checkpoint):
    docker build \\
        --security-opt seccomp=unconfined \\
        --cap-add SYS_PTRACE \\
        --cap-add CHECKPOINT_RESTORE \\
        -f deploy/docker/Dockerfile.high-density \\
        -t redtusk:high-density-test .

Set REDTUSK_TEST_HIGHDENSITY_IMAGE=redtusk:high-density-test to enable these tests.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time

import pytest

IMAGE = os.environ.get("REDTUSK_TEST_HIGHDENSITY_IMAGE", "")
pytestmark = pytest.mark.docker


def _skip_if_no_image():
    if not IMAGE:
        pytest.skip("REDTUSK_TEST_HIGHDENSITY_IMAGE not set")


def test_high_density_image_exists():
    _skip_if_no_image()
    result = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Image {IMAGE!r} not found"


def test_high_density_job_processes_txt(tmp_path):
    """Full end-to-end: restore from checkpoint, signal FIFO, verify metadata.json."""
    _skip_if_no_image()

    scratch = tmp_path / "scratch"
    in_dir = scratch / "in"
    out_dir = scratch / "out"
    in_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    scratch.chmod(0o777)
    in_dir.chmod(0o777)
    out_dir.chmod(0o777)

    # Write sample input
    (in_dir / "sample.txt").write_text("Hello from high-density test\n")

    # Write job.json
    job = {
        "input_path": "/in/sample.txt",
        "output_dir": "/out",
        "sha256": "0" * 64,
        "filename_hint": "sample.txt",
        "limits": {
            "max_recursion_depth": 10,
            "max_embedded_entries": 100,
            "max_extracted_bytes": 10485760,
            "ocr_timeout_s": 30,
        },
        "enable_qr": False,
        "enable_ocr": False,
        "ocr_lang": "eng",
        "ocr_psm": 3,
        "sandbox_profile": "high-density",
        "sandbox_runtime": "runc",
        "appcds": True,
        "ksm": False,
        "crac": True,
        "redtusk_version": "0.1.0",
        "tika_version": "3.3.0",
    }
    (in_dir / "job.json").write_text(json.dumps(job))

    # Start the container (criu restore — no --run flag needed, restore.sh is ENTRYPOINT)
    container_id = subprocess.check_output(
        [
            "docker", "run", "--rm", "--detach",
            "--read-only",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "--cap-add", "CHECKPOINT_RESTORE",
            "--network", "none",
            "--tmpfs", "/tmp:rw,exec,nosuid,size=256m",
            "--tmpfs", "/var/lib/redtusk:rw,nosuid,size=32m,uid=10001,gid=10001",
            "--mount", f"type=bind,source={in_dir},target=/in,readonly",
            "--mount", f"type=bind,source={out_dir},target=/out",
            IMAGE,
        ],
        timeout=30,
        text=True,
    ).strip()

    # Wait for the FIFO (worker ready after CRaC restore)
    fifo = in_dir / "control.fifo"
    deadline = time.monotonic() + 10.0  # CRaC restore should be fast
    while time.monotonic() < deadline:
        if fifo.exists():
            break
        time.sleep(0.25)
    assert fifo.exists(), "FIFO not created — CRaC restore may have failed"

    # Signal the worker
    def _signal():
        with open(fifo, "w") as f:
            f.write("go\n")

    t = threading.Thread(target=_signal, daemon=True)
    t.start()
    t.join(timeout=5)

    # Wait for metadata.json
    metadata_path = out_dir / "metadata.json"
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if metadata_path.exists():
            break
        time.sleep(0.5)

    subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, timeout=10)

    assert metadata_path.exists(), "metadata.json not written"
    meta = json.loads(metadata_path.read_text())
    assert meta.get("extraction", {}).get("entries"), "No entries in metadata"
    root = meta["extraction"]["entries"][0]
    assert root["path"] == "/"
    assert root["depth"] == 0
