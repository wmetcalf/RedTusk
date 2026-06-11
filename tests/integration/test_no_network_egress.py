"""Egress drift-gate — the JVM/Tika worker must make NO outbound network
connections.

RedTusk detonates untrusted, hostile documents. Apache Tika has a long history of
XXE / SSRF issues (external DTDs, OOXML/SVG external relationships, etc.), so a
single regression that re-enables external-entity resolution would let a crafted
document exfiltrate data or pivot (SSRF) from the worker. This test locks the
property in: strace a detonation (including a hostile XXE document whose external
entities point at TEST-NET-1) and assert the worker opens NO connect() to a
non-loopback AF_INET/AF_INET6 address.

A benign document is included too, so the gate also proves a normal parse stays
egress-free (the JVM lazily creates resolver sockets but never connects them out).

Mark: ``integration`` (needs java + the worker jar + strace).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from redtusk.engine import _DEFAULT_WORKER_JAR

_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = _ROOT / "tests" / "fixtures"


def _worker_jar() -> str:
    import os

    return os.environ.get("REDTUSK_WORKER_JAR", _DEFAULT_WORKER_JAR)


def _skip_reason() -> str | None:
    if shutil.which("strace") is None:
        return "strace not available"
    if shutil.which("java") is None:
        return "java not on PATH"
    if not Path(_worker_jar()).is_file():
        return f"worker jar {_worker_jar()!r} not present"
    return None


_SKIP = _skip_reason()

pytestmark = pytest.mark.integration


def _external_connects(strace_text: str) -> list[str]:
    """Return strace connect() lines to a non-loopback AF_INET/AF_INET6 address.

    AF_UNIX (e.g. the nscd socket) and AF_NETLINK are local IPC, not egress.
    Loopback (127.0.0.0/8, ::1) is not external. Anything else is a real outbound
    connection attempt — the regression we guard against.
    """
    bad: list[str] = []
    for line in strace_text.splitlines():
        if "connect(" not in line or "AF_INET" not in line:
            continue
        # loopback is fine (the worker uses no local services, but be lenient)
        if '"127.' in line or '"::1"' in line:
            continue
        bad.append(line.strip())
    return bad


def _detonate_under_strace(input_path: Path, tmp_path: Path) -> str:
    """Run RedTuskEngine.detonate(input) under strace; return the trace text.

    strace -f follows the java subprocess + all its threads, so a connect() from
    any Tika parser thread is captured.
    """
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    runner = tmp_path / "_detonate.py"
    runner.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(_ROOT / 'src')!r})\n"
        "from pathlib import Path\n"
        "from redtusk.engine import RedTuskEngine\n"
        "from blastbox.limits import Limits\n"
        f"RedTuskEngine().detonate(Path({str(input_path)!r}), "
        f"Path({str(out_dir)!r}), Limits.from_env())\n"
    )
    trace = tmp_path / "trace.txt"
    subprocess.run(
        ["strace", "-f", "-e", "trace=%network", "-o", str(trace), sys.executable, str(runner)],
        capture_output=True,
        timeout=180,
    )
    return trace.read_text(errors="replace")


@pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")
@pytest.mark.parametrize(
    "fixture",
    ["xxe_external_entity.xml", "../../deploy/docker/appcds-warmup-corpus/qr_fixture.docx"],
)
def test_worker_makes_no_external_network_connection(fixture: str, tmp_path: Path) -> None:
    fx = (_FIXTURES / fixture).resolve()
    assert fx.is_file(), f"fixture missing: {fx}"
    trace = _detonate_under_strace(fx, tmp_path)
    egress = _external_connects(trace)
    assert not egress, (
        "worker opened external network connection(s) — XXE/SSRF egress regression:\n"
        + "\n".join(egress)
    )
