"""CVE-2026-114938 mitigation, functional half: with ``-XX:-UseBASE64Intrinsics`` in the
worker argv, Base64 content in a sample must still be decoded and extracted.

The sample is an iCalendar invite carrying an inline ``ATTACH;ENCODING=BASE64`` payload --
the Tika fork's ICalParser decodes that with ``java.util.Base64`` (the exact API whose
intrinsic is disabled), hashes the bytes into ``ical:attach_sha256`` and parses them as an
embedded entry. The payload is a few KiB so that, on a VBMI host without the flag, the decode
would have gone through the vulnerable intrinsic.

Requires a JRE and the worker jar (``REDTUSK_WORKER_JAR``), like the other live tests here.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, cast

import pytest
from blastbox.contract import ExtractedText, find_by_type
from blastbox.host.trust import validate_worker_output
from blastbox.limits import Limits
from blastbox.worker.harness import run_detonation

from redtusk.engine import _DEFAULT_WORKER_JAR, RedTuskEngine, _java_worker_argv

pytestmark = pytest.mark.integration

_JAR = os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)
_SKIP = shutil.which("java") is None or not Path(_JAR).is_file()

CANARY = "JAVA4SHELL-BASE64-CANARY-7f3e"


def _ics_with_inline_attach(payload: bytes) -> bytes:
    b64 = base64.b64encode(payload).decode("ascii")
    # RFC 5545 line folding: 75 octets, continuation lines start with one space.
    first = "ATTACH;FMTTYPE=text/plain;ENCODING=BASE64;VALUE=BINARY:"
    line = first + b64
    folded = [line[:75]] + [" " + line[i : i + 74] for i in range(75, len(line), 74)]
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//redtusk//java4shell-test//EN",
        "BEGIN:VEVENT",
        "UID:java4shell-test@redtusk",
        "DTSTAMP:20261118T000000Z",
        "DTSTART:20261118T010000Z",
        "SUMMARY:base64 decode check",
        *folded,
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


@pytest.mark.skipif(_SKIP, reason=f"java or worker jar {_JAR!r} unavailable")
def test_inline_base64_attach_still_decodes_with_intrinsic_off(tmp_path: Path) -> None:
    assert "-XX:-UseBASE64Intrinsics" in _java_worker_argv(tmp_path)

    payload = ("\n".join(f"{CANARY} line {i:04d}" for i in range(200)) + "\n").encode()
    assert len(payload) > 4096
    sample = tmp_path / "invite.ics"
    sample.write_bytes(_ics_with_inline_attach(payload))

    outdir = tmp_path / "out"
    rc = run_detonation(
        cast(Any, RedTuskEngine()), input_path=sample, output_dir=outdir, limits=Limits()
    )
    assert rc == 0
    env = validate_worker_output(
        output_dir=outdir,
        input_sha256=hashlib.sha256(sample.read_bytes()).hexdigest(),
        engine="redtusk",
        limits=Limits(),
    )
    assert env.status == "ok"

    # The decoded bytes are byte-exact: their SHA-256 is what ICalParser recorded.
    rmeta = json.dumps(json.loads((outdir / "metadata.json").read_text()))
    assert hashlib.sha256(payload).hexdigest() in rmeta, "decoded ATTACH sha256 missing"
    # ...and the embedded text made it through extraction.
    texts = " ".join(t.text for t in find_by_type(env.payload, ExtractedText))
    assert f"{CANARY} line 0199" in texts
