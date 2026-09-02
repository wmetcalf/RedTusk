"""The build script names an ARG per Dockerfile; those names must be real.

Docker WARNS and IGNORES a `--build-arg` the Dockerfile never declares. The
build then resolves the mutable base tag itself while the stamp claims a pinned
digest -- a recorded provenance that is wrong in the one way that matters,
caused by nothing worse than a typo.

`blastbox stamp -f <dockerfile>` refuses that at build time. This test catches
it earlier and without docker: if someone renames an ARG, or points the script
at a different Dockerfile, it fails here.

The names are NOT uniform across this ecosystem -- blastbox's gvisor Dockerfile
uses `BASE`, these use `BASE_IMAGE` -- which is exactly why they are asserted
rather than assumed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_images.sh"

# (Dockerfile, base-arg the script passes for it). None = built with no pinned base.
EXPECTED = [
    ("deploy/docker/Dockerfile.default", None),
    ("deploy/docker/Dockerfile.cold-worker", "BASE_IMAGE"),
    ("deploy/docker/Dockerfile.host", None),
]


def _declared_args(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*ARG\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.MULTILINE))


@pytest.mark.parametrize("dockerfile,base_arg", EXPECTED)
def test_the_script_names_an_arg_the_dockerfile_declares(dockerfile, base_arg):
    path = ROOT / dockerfile
    assert path.is_file(), f"{dockerfile} is gone; build_images.sh still builds it"
    if base_arg is None:
        return
    declared = _declared_args(path)
    assert base_arg in declared, (
        f"{dockerfile} declares {sorted(declared)}, not {base_arg!r}. "
        "docker would silently ignore the --build-arg that pins the base."
    )


def test_the_script_builds_every_dockerfile_this_test_knows_about():
    """Keep the table and the script from drifting apart."""
    script = SCRIPT.read_text(encoding="utf-8")
    for dockerfile, _ in EXPECTED:
        assert dockerfile in script, f"{dockerfile} is in the table but not in the script"


def test_the_script_verifies_its_own_output():
    """A build that does not check its stamps is how the gap reopens."""
    script = SCRIPT.read_text(encoding="utf-8")
    assert "stamp --read" in script, "build_images.sh must verify what it stamped"
    assert "exit 1" in script, "a failed verification must fail the build"
