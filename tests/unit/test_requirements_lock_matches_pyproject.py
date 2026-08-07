"""The hashed lock must actually satisfy pyproject's constraints.

`deploy/requirements.lock` is compiled from `pyproject.toml --extra host` and
`Dockerfile.fc-dispatcher` installs it with `--require-hashes`, then adds redtusk
with `pip install -e . --no-deps`. That `--no-deps` is the trap: pip never
re-checks pyproject's constraints against what the lock already installed, so a
lock that has drifted builds perfectly green. This one sat at `blastbox==0.1.15`
while pyproject required `>=0.1.25,<0.2` — ten releases — and the image shipped
a dispatcher running contract-layer code the rest of the fleet had moved past.

Nothing in the repo compared the two files, and there is no CI, so these tests
are the guard: regenerate the lock in the same commit as any dependency change.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "deploy/requirements.lock"
PYPROJECT = ROOT / "pyproject.toml"

# `name==1.2.3 \` at the start of a line; the trailing hashes are indented.
_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)", re.MULTILINE)


def _locked() -> dict[str, str]:
    """Canonicalised distribution name -> pinned version."""
    return {
        re.sub(r"[-_.]+", "-", name).lower(): version
        for name, version in _PIN.findall(LOCK.read_text())
    }


def _host_requirements() -> list[Requirement]:
    cfg = tomllib.loads(PYPROJECT.read_text())
    project = cfg["project"]
    return [
        Requirement(spec)
        for spec in project["dependencies"] + project["optional-dependencies"]["host"]
    ]


def test_every_direct_requirement_is_pinned_in_the_lock() -> None:
    locked = _locked()
    missing = [
        req.name for req in _host_requirements()
        if re.sub(r"[-_.]+", "-", req.name).lower() not in locked
    ]
    assert not missing, (
        f"{missing} are required by pyproject but absent from the lock; the "
        f"fc-dispatcher image installs the lock with --require-hashes and then adds "
        f"redtusk with --no-deps, so these would simply never be installed. "
        f"Regenerate: uv pip compile pyproject.toml --extra host --generate-hashes "
        f"-o deploy/requirements.lock"
    )


def test_the_locked_versions_satisfy_pyprojects_constraints() -> None:
    locked = _locked()
    violations = []
    for req in _host_requirements():
        key = re.sub(r"[-_.]+", "-", req.name).lower()
        pinned = locked.get(key)
        if pinned is None:
            continue                       # reported by the test above
        if not req.specifier.contains(Version(pinned), prereleases=True):
            violations.append(f"{req.name}: locked {pinned}, pyproject wants {req.specifier}")
    assert not violations, (
        "the lock contradicts pyproject: " + "; ".join(violations) + ". `pip install -e . "
        "--no-deps` will NOT catch this at image build time. Regenerate the lock."
    )


def test_the_s3_extra_reaches_the_dispatcher_image() -> None:
    """boto3 is a real dependency of the dispatcher, not an image-build detail.

    On a multi-node fleet the dispatcher materialises samples and seals results
    through an S3/MinIO BlobStore (BLASTBOX_BLOB_URL=s3://...). It used to be
    appended as a second `blastbox[s3]` argument on Dockerfile.host's pip line,
    which left the lock-driven fc-dispatcher image without it entirely.
    """
    host_extra = tomllib.loads(PYPROJECT.read_text())["project"]["optional-dependencies"]["host"]
    blastbox = [r for r in map(Requirement, host_extra) if r.name == "blastbox"]
    assert any("s3" in r.extras for r in blastbox), (
        "the host extra must request blastbox[host,s3] so boto3 is a declared dependency"
    )
    assert "boto3" in _locked(), "boto3 is missing from the hashed lock"
