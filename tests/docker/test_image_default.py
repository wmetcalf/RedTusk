"""Tests for redtusk-worker:default Docker image.

Marked 'docker' — requires docker daemon and the built image.
Run: pytest tests/docker/ -v -m docker
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, cast

import pytest

from redtusk.engine import _signal_worker_loop

pytestmark = pytest.mark.docker

IMAGE = "redtusk-worker:default"


def _image_exists() -> bool:
    r = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True)
    return r.returncode == 0


@pytest.fixture(scope="session", autouse=True)
def require_image() -> None:
    if not _image_exists():
        pytest.skip(
            f"Image {IMAGE} not built — run: "
            f"docker build -f deploy/docker/Dockerfile.default -t {IMAGE} ."
        )


def run_worker(input_text: str, filename_hint: str = "test.txt") -> dict[str, Any]:
    """Run the worker container against in-memory text; return parsed metadata.json."""
    with tempfile.TemporaryDirectory() as scratch_base:
        scratch = Path(scratch_base) / "slot"
        scratch.mkdir()
        (scratch / "in").mkdir()
        (scratch / "out").mkdir()
        control = scratch / "control"
        control.mkdir()

        # Fix permissions so container UID 10001 can read/write. `control` is
        # created HERE rather than left to the worker for a second reason: the
        # worker runs as 10001, and a control dir it owns is one this test's
        # own tempdir cleanup cannot empty -- `PermissionError: control.ready`
        # out of shutil.rmtree. Unlinking depends on the DIRECTORY's mode, so a
        # dir we own at 0777 stays removable whatever the worker writes into it.
        scratch.chmod(0o777)
        (scratch / "in").chmod(0o777)
        (scratch / "out").chmod(0o777)
        control.chmod(0o777)

        # Write input file
        input_file = scratch / "in" / filename_hint
        input_file.write_text(input_text)
        sha256 = hashlib.sha256(input_text.encode()).hexdigest()

        # Write job.json
        job = {
            "input_path": f"/scratch/in/{filename_hint}",
            "output_dir": "/scratch/out",
            "sha256": sha256,
            "filename_hint": filename_hint,
            "limits": {
                "max_recursion_depth": 10,
                "max_embedded_entries": 5000,
                "max_extracted_bytes": 524288000,
                "ocr_timeout_s": 60,
            },
            "enable_qr": False,
            "enable_ocr": False,
            "ocr_lang": "eng",
            "ocr_psm": 3,
            "sandbox_profile": "default",
            "sandbox_runtime": "runc",
            "appcds": True,
            "ksm": False,
            "crac": False,
            "redtusk_version": "0.1.0",
            "zxing_path": "/usr/local/bin/ZXingReader",
            "tesseract_path": "tesseract",
            "ocr_max_image_dim": 2000,
            "ocr_skip_blank": True,
            "enable_thumbnails": True,
        }
        # Drive the PRODUCT's handshake loop rather than a copy of it. That is
        # what `_signal_worker_loop` is module-level for, and this test had a
        # copy that still spoke the pre-`control/` protocol: job.json and
        # control.go at the slot ROOT, and a fixed 2s sleep instead of waiting
        # for control.ready. The worker has announced readiness in
        # `control/control.ready` and taken its job from `control/` for some
        # time now, so it waited for a go-signal that was never written where
        # it looks, and every test here died on the 90s docker timeout.
        worker_done = threading.Event()
        t = threading.Thread(
            target=_signal_worker_loop,
            args=(control, job, 60.0, worker_done),
            daemon=True,
        )
        t.start()

        started = time.monotonic()
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--memory=1g",
                "--pids-limit=256",
                f"--volume={scratch}:/scratch/",
                "--env=REDTUSK_LOG_LEVEL=WARNING",
                IMAGE,
                "--run", "/scratch",
            ],
            capture_output=True,
            timeout=90,
        )
        elapsed = time.monotonic() - started
        worker_done.set()
        t.join(timeout=5)

        # The handshake's readiness wait is otherwise unobservable from out here:
        # `_signal_worker_loop` writes the go-signal even if control.ready never
        # appears, so a broken ready-file path costs LATENCY, not correctness, and
        # every assertion below still passes. Measured on this image: 2.35s with
        # readiness detection working, 61.87s with it pointed at a filename nothing
        # writes. This bound sits an order of magnitude above the former and below
        # the 60s fallback, so it can only fire when that path is broken.
        assert elapsed < 30, (
            f"worker took {elapsed:.1f}s; the go-signal is most likely arriving "
            f"from the loop's fallback rather than from seeing control.ready"
        )

        assert result.returncode == 0, (
            f"Worker exited {result.returncode}\n"
            f"stderr: {result.stderr.decode()[-2000:]}"
        )

        meta_path = scratch / "out" / "metadata.json"
        assert meta_path.exists(), "metadata.json must be written"
        return cast(dict[str, Any], json.loads(meta_path.read_text()))


def test_worker_produces_metadata_for_text_file() -> None:
    meta = run_worker("Hello from the Docker image test.\n", "test.txt")

    assert meta["redtusk_version"] == "0.1.0"

    entries = meta["extraction"]["entries"]
    assert len(entries) >= 1
    root = entries[0]
    assert root["path"] == "/"
    assert root["depth"] == 0
    assert root["parent_path"] is None
    assert "Hello" in root["text"]
    assert root["qr"] is not None
    assert root["ocr"] is not None
    assert root["error"] is None

    # Exact top-level key set from the JSON Schema
    assert set(meta.keys()) == {
        "redtusk_version", "input", "extraction",
        "limits", "truncated", "warnings", "sandbox",
    }


def test_worker_sandbox_profile_is_default() -> None:
    meta = run_worker("sandbox profile test\n")
    assert meta["sandbox"]["profile"] == "default"
    assert meta["sandbox"]["appcds"] is True
    assert meta["sandbox"]["crac"] is False


def test_worker_exits_zero_for_valid_input() -> None:
    meta = run_worker("RedTusk Docker smoke test.\n")
    assert meta
    assert meta["extraction"]["duration_ms"] >= 0
    assert meta["truncated"] is None


def test_worker_handles_html_input() -> None:
    html = "<html><body><h1>RedTusk</h1><p>Docker image HTML test.</p></body></html>"
    meta = run_worker(html, "test.html")
    root = meta["extraction"]["entries"][0]
    assert ("html" in root["content_type"].lower() or
            "text" in root["content_type"].lower())
    assert root["error"] is None
