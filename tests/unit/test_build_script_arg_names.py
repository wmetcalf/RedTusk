"""`scripts/build_images.sh` must pin bases with ARGs docker will actually honour.

Docker WARNS and IGNORES a `--build-arg` the Dockerfile never declares, and
declaring one is not enough either: an ARG inside a stage cannot parameterize a
FROM, and in a multi-stage build only the LAST stage becomes the image, so a
parameterized *builder* pins nothing. Any of those leaves the build resolving a
mutable tag while the stamp claims a pinned digest -- a recorded provenance
wrong in the one way that matters.

`blastbox stamp` refuses all of that at build time; this test catches it in CI
without docker. Two design points, both learned the hard way:

* The (Dockerfile, base-arg) pairs are READ OUT OF THE SCRIPT, not written down
  here. A hand-maintained table only catches a rename on the Dockerfile side --
  a typo in the script's own argument, which is the failure this guards against,
  sailed straight through it.
* The Dockerfile parsing is imported from blastbox rather than reimplemented.
  A second copy of that parser drifts from the one that actually gates builds,
  and its guards end up exercised only by whichever Dockerfiles this repo
  happens to contain.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from blastbox.host.stamp import StampError, assert_arg_selects_base

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_images.sh"
TEXT = SCRIPT.read_text(encoding="utf-8")

# `stamp_flags <dockerfile> <base> [base-arg]` -- the base-arg defaults to
# BASE_IMAGE in the script, so an absent third word means that default.
CALLS = [
    (m.group("df"), (m.group("arg") or "BASE_IMAGE"))
    for m in re.finditer(
        r"^stamp_flags\s+(?P<df>\S+)\s+(?P<base>\S+|\"[^\"]*\")(?:\s+(?P<arg>[A-Za-z_]\w*))?\s*$",
        TEXT,
        re.MULTILINE,
    )
]


def test_the_script_actually_stamps_something() -> None:
    """Guard the guard: if the call syntax changes, every check below passes vacuously."""
    assert CALLS, (
        "no `stamp_flags <dockerfile> <base>` calls found in build_images.sh. "
        "Either the script stopped stamping, or its call shape changed and this "
        "test is now asserting nothing."
    )


@pytest.mark.parametrize("dockerfile,base_arg", CALLS)
def test_each_arg_the_script_passes_selects_that_dockerfiles_base(
    dockerfile: str, base_arg: str
) -> None:
    path = ROOT / dockerfile
    assert path.is_file(), f"build_images.sh stamps {dockerfile}, which does not exist"
    try:
        assert_arg_selects_base(path, base_arg)
    except StampError as exc:  # re-raise with the script's role in it
        pytest.fail(f"build_images.sh passes --base-arg {base_arg} for {dockerfile}: {exc}")


def test_every_docker_build_in_the_script_is_stamped() -> None:
    """An unstamped build is the whole problem; one must not sneak back in."""
    builds = re.findall(r"^docker build -f (\S+)", TEXT, re.MULTILINE)
    stamped = {df for df, _ in CALLS}
    assert builds, "no `docker build` lines found; this test is asserting nothing"
    assert set(builds) <= stamped, (
        f"built but never stamped: {sorted(set(builds) - stamped)}. "
        "An image with no recorded base reads back as UNSTAMPED and fails the "
        "script's own verification."
    )


@pytest.mark.parametrize(
    "var,dockerfile",
    [("WORKER_BASE", "deploy/docker/Dockerfile.default"),
     ("HOST_BASE", "deploy/docker/Dockerfile.host")],
)
def test_the_scripts_default_base_matches_the_dockerfiles_own_default(
    var: str, dockerfile: str
) -> None:
    """The script pins these; the Dockerfile defaults them. They must agree.

    If they drift, a plain `docker build` and a stamped build produce images on
    different bases while both look correct.
    """
    m = re.search(rf'^{var}="\$\{{{var}:-([^}}]+)\}}"', TEXT, re.MULTILINE)
    assert m, f"{var} is no longer set the way this test reads it"
    declared = re.search(
        r"^\s*ARG\s+BASE_IMAGE=(\S+)",
        (ROOT / dockerfile).read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert declared, f"{dockerfile} no longer defaults ARG BASE_IMAGE"
    assert m.group(1) == declared.group(1), (
        f"build_images.sh defaults {var}={m.group(1)!r} but {dockerfile} defaults "
        f"ARG BASE_IMAGE={declared.group(1)!r}"
    )


def test_a_refused_stamp_aborts_instead_of_building_unstamped() -> None:
    """`set -e` DISCARDS the status of a `$(...)` in a command's arguments.

    Left that way, a refusing stamp lets the build run with no labels and no
    --build-arg, so the cold worker falls back to its Dockerfile default
    `redtusk-worker:default` -- a mutable tag pointing at whatever stale base is
    on the box, which is the incident this script exists to prevent.
    """
    assert not re.search(r"docker build[^\n]*\$\(stamp_flags", TEXT), (
        "stamp_flags is called inside docker build's arguments; its failure "
        "would be silently discarded"
    )
    assert "read -r -a flags" in TEXT, "stamp output must be read into an array"
    # Scoped to stamp_flags' OWN body: the verify block at the end of the script
    # also ends in `|| { ... exit 1 }`, and a whole-file search for that pattern
    # is satisfied by it -- so this assertion passed with the abort removed.
    body = re.search(r"^stamp_flags\(\) \{(.*?)^\}", TEXT, re.MULTILINE | re.DOTALL)
    assert body, "stamp_flags is no longer a function this test can read"
    assert re.search(r"exit\s+1", body.group(1)), (
        "stamp_flags must abort when `blastbox stamp` refuses, or the build "
        "runs unstamped with the Dockerfile's mutable default base"
    )


def test_the_script_verifies_what_it_stamped() -> None:
    """A build that does not check its own stamps is how the gap reopens."""
    assert re.search(r"^\s*blastbox stamp --read", TEXT, re.MULTILINE), (
        "build_images.sh must read every stamp back (a commented-out line does "
        "not count)"
    )
    assert re.search(r"^\s*exit 1$", TEXT, re.MULTILINE), (
        "a failed verification must fail the build"
    )
