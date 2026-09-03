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
# Continuations are joined the way the shell joins them, THEN each logical line
# is matched whole. Trying to express "or a backslash-newline here" inside the
# pattern let `\s+` cross a line boundary, so a two-line call swallowed the next
# line's first word as its base-arg -- every plain call came back with
# `--base-arg docker`.
#
# Leading whitespace is allowed too: the warm-artifact calls sit inside an `if`,
# and an anchor that ignored indentation made every guard below skip them
# silently, passing while covering nothing.
LOGICAL = re.sub(r"\\\n[ \t]*", " ", TEXT)

_CALL = re.compile(
    r"^[ \t]*stamp_flags[ \t]+(?P<df>\"[^\"]*\"|\S+)[ \t]+(?P<base>\"[^\"]*\"|\S+)"
    # The optional 4th argument (source repo) may be quoted or bare -- matching
    # only the quoted form would silently stop recognising a call that passed an
    # unquoted path, and an unrecognised call is an unguarded one.
    r"(?:[ \t]+(?P<arg>[A-Za-z_]\w*))?(?:[ \t]+(?:\"[^\"]*\"|\S+))?[ \t]*$",
    re.MULTILINE,
)
CALLS = [
    (m.group("df").strip('"'), (m.group("arg") or "BASE_IMAGE"))
    for m in _CALL.finditer(LOGICAL)
]

# Dockerfiles that live in blastbox, not here. Their ARG names are part of this
# ecosystem's contract and differ from ours, which is the whole reason the names
# are asserted rather than assumed. CI cannot open them -- blastbox ships as a
# wheel and the deploy/ tree is not in it -- so the pair is pinned here and
# `blastbox stamp` refuses at build time if the real file disagrees.
FOREIGN_ARGS = {
    "deploy/gvisor/Dockerfile.redtusk": "BASE",
    "deploy/firecracker/Dockerfile.redtusk": "BASE_IMAGE",
}


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
    if "$BLASTBOX_SRC" in dockerfile:
        rel = dockerfile.split("$BLASTBOX_SRC/", 1)[-1]
        expected = FOREIGN_ARGS.get(rel)
        assert expected, (
            f"{rel} is built from blastbox but has no entry in FOREIGN_ARGS; "
            "record which ARG selects its base so a rename is caught here"
        )
        assert base_arg == expected, (
            f"build_images.sh passes --base-arg {base_arg} for {rel}, "
            f"but that file uses {expected}. docker silently ignores the wrong one."
        )
        return
    path = ROOT / dockerfile
    assert path.is_file(), f"build_images.sh stamps {dockerfile}, which does not exist"
    try:
        assert_arg_selects_base(path, base_arg)
    except StampError as exc:  # re-raise with the script's role in it
        pytest.fail(f"build_images.sh passes --base-arg {base_arg} for {dockerfile}: {exc}")


def test_every_docker_build_in_the_script_is_stamped() -> None:
    """An unstamped build is the whole problem; one must not sneak back in."""
    builds = [
        b.strip('"')
        for b in re.findall(r"^[ \t]*docker build -f (\"[^\"]*\"|\S+)", LOGICAL, re.MULTILINE)
    ]
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
    # Scoped to the verification block. A whole-file `exit 1` search is
    # satisfied by stamp_flags' own abort, so it stayed green with the final
    # gate removed -- the same wrong-reason failure as the assertion above,
    # in its sibling test.
    gate = re.search(r'\[ "\$rc" -eq 0 \][^\n]*\|\|\s*\{(.*?)^\}', TEXT, re.MULTILINE | re.DOTALL)
    assert gate, "the read-back results are no longer gated the way this test reads"
    assert re.search(r"exit\s+1", gate.group(1)), (
        "a failed verification must fail the build, not just print"
    )


def test_the_minimum_blastbox_version_is_stated_once() -> None:
    """A minimum that appears in two places drifts.

    It did: the not-found diagnostic kept saying >= 0.1.29 after the gate moved
    to 0.1.30, so the script told an operator to install a version it would then
    reject. Every mention must come from BB_MIN.
    """
    assigns = re.findall(r"^BB_MIN=(\S+)", TEXT, re.MULTILINE)
    assert len(assigns) == 1, f"BB_MIN is assigned {len(assigns)} times: {assigns}"
    floor = assigns[0]

    # A message may NAME a version that is too old ("0.1.28 and 0.1.29 have
    # `stamp` but ..."), and those literals are the point. What must never be a
    # literal is the version the operator is told to GET: an exemption broad
    # enough to cover both is an exemption that lets the real bug through --
    # the drift that happened was a hardcoded ">= 0.1.29" in exactly such a
    # line, and a first version of this test waved it past.
    for line in TEXT.splitlines():
        if not line.lstrip().startswith("echo"):
            continue
        for m in re.finditer(r">=\s*(\$\{?\w+\}?|\d+(?:\.\d+)*)", line):
            got = m.group(1).strip("${}")
            assert got in ("BB_MIN", floor), (
                f"the version an operator is told to install is hardcoded as "
                f"{got!r}: {line.strip()!r}. Use $BB_MIN so it cannot drift "
                "from the gate."
            )


def test_the_floor_matches_what_pyproject_pins() -> None:
    """The script's gate and the package's own floor must agree.

    If the gate is lower, the script accepts a blastbox the package refuses to
    install alongside; if higher, it rejects one the package considers fine.
    """
    floor = re.search(r"^BB_MIN=(\S+)", TEXT, re.MULTILINE)
    assert floor
    pins = re.findall(
        r"blastbox(?:\[[^\]]*\])?>=(\d+\.\d+\.\d+)",
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    assert pins, "pyproject no longer pins blastbox the way this test reads it"
    assert set(pins) == {floor.group(1)}, (
        f"build_images.sh requires >= {floor.group(1)} but pyproject pins {sorted(set(pins))}"
    )
