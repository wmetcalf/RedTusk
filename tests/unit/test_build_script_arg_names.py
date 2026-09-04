"""What blastbox-images.toml declares must match the Dockerfiles it names.

These used to assert the same things about scripts/build_images.sh. The bash is
gone -- `blastbox build-images` executes the declaration now -- but the failure
modes did not go anywhere: docker silently ignores a --build-arg the Dockerfile
does not declare, so a wrong `base_arg` pins nothing while the stamp claims a
digest the build never used.

The generic checks live in blastbox and are tested there. What is REPO business
is that this repo's own declaration matches this repo's own Dockerfiles, which
is what breaks when a Dockerfile is renamed or an ARG is changed here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
images = pytest.importorskip("blastbox.host.images")

PLAN = images.load_plan(ROOT)
LOCAL = [i for i in PLAN.images if i.context == "."]


def test_the_declaration_names_every_tier() -> None:
    """A tier missing from the spec is a tier that never gets rebuilt -- the
    fleet then runs two versions while every tag says one."""
    names = {i.name for i in PLAN.images}
    assert {"redtusk-worker", "redtusk-cold-worker", "redtusk"} <= names
    assert {"redtusk-warm-gvisor", "redtusk-fc-worker"} <= names


@pytest.mark.parametrize("spec", LOCAL, ids=lambda s: s.name)
def test_each_declared_base_arg_selects_that_dockerfiles_base(spec) -> None:
    """docker discards a --build-arg the Dockerfile does not declare, so the
    build resolves its own default while the stamp claims the pinned base."""
    from blastbox.host.stamp import StampError, assert_arg_selects_base

    path = ROOT / spec.dockerfile
    assert path.is_file(), f"the plan names {spec.dockerfile}, which does not exist"
    try:
        assert_arg_selects_base(path, spec.base_arg)
    except StampError as exc:
        pytest.fail(f"blastbox-images.toml declares base_arg={spec.base_arg}: {exc}")


@pytest.mark.parametrize("spec", LOCAL, ids=lambda s: s.name)
def test_a_declared_upstream_base_matches_the_dockerfiles_own_default(spec) -> None:
    """The plan pins these; the Dockerfile defaults them. They must agree.

    If they drift, a plain `docker build` and a planned build produce images on
    different bases while both look correct.
    """
    if spec.internal:  # a chain base has no upstream default to agree with
        pytest.skip(f"{spec.name} builds on {spec.base}, which this plan builds")
    declared = re.search(
        rf"^\s*ARG\s+{re.escape(spec.base_arg)}=(\S+)",
        (ROOT / spec.dockerfile).read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert declared, (
        f"{spec.dockerfile} no longer defaults ARG {spec.base_arg}; without a "
        "default a plain `docker build` of it cannot work at all"
    )
    assert spec.base == declared.group(1), (
        f"the plan pins {spec.name} to {spec.base!r} but {spec.dockerfile} "
        f"defaults ARG {spec.base_arg}={declared.group(1)!r}"
    )


def test_the_warm_images_are_declared_against_the_blastbox_tree() -> None:
    """They are built from Dockerfiles that live in blastbox, and stamping them
    with THIS repo's revision would record a commit that does not contain the
    file that built them."""
    warm = [i for i in PLAN.images if i.name in {"redtusk-warm-gvisor", "redtusk-fc-worker"}]
    assert len(warm) == 2
    for spec in warm:
        assert spec.context == "$BLASTBOX_SRC", (
            f"{spec.name} must be built from the blastbox tree, not this repo"
        )


def test_the_two_warm_dockerfiles_use_different_arg_names() -> None:
    """Not a style note -- it is the trap. They genuinely differ (BASE for
    gvisor, BASE_IMAGE for firecracker), and passing the wrong one pins nothing
    while the label claims a digest. Pinned here so a copy-paste is caught.
    """
    by_name = {i.name: i for i in PLAN.images}
    assert by_name["redtusk-warm-gvisor"].base_arg == "BASE"
    assert by_name["redtusk-fc-worker"].base_arg == "BASE_IMAGE"


def test_the_firecracker_rootfs_declares_what_it_must_contain() -> None:
    """The guest boots /init. A rootfs without it hangs every warm guest until
    the boot timeout -- which took the titanarum FC tier down, because nothing
    had written down what the artifact needed."""
    fc = [r for r in PLAN.rootfs if r.kind == "ext4"]
    assert len(fc) == 1
    assert "/init" in fc[0].requires


def test_the_floor_matches_what_pyproject_pins() -> None:
    """The wrapper's gate and the package's own floor must agree.

    Lower, and the script accepts a blastbox the package refuses to install
    alongside; higher, and it rejects one the package considers fine.
    """
    text = (ROOT / "scripts" / "build_images.sh").read_text(encoding="utf-8")
    floor = re.search(r"^BB_MIN=(\S+)", text, re.MULTILINE)
    assert floor, "build_images.sh no longer states a minimum the way this test reads it"
    pins = re.findall(
        r"blastbox(?:\[[^\]]*\])?>=(\d+\.\d+\.\d+)",
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    )
    assert pins, "pyproject no longer pins blastbox the way this test reads it"
    assert set(pins) == {floor.group(1)}, (
        f"build_images.sh requires >= {floor.group(1)} but pyproject pins {sorted(set(pins))}"
    )


def test_every_dockerfile_default_blastbox_version_matches_the_pin() -> None:
    """The Dockerfiles say "keep the default in sync with the floor in
    pyproject.toml" and nothing enforced it.

    A default that drifts produces exactly the lie this tooling exists to catch:
    a plain `docker build` installs one version while the label — and every
    planned build, which passes the pin explicitly — names another.
    """
    pins = set(
        re.findall(
            r"blastbox(?:\[[^\]]*\])?>=(\d+\.\d+\.\d+)",
            (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        )
    )
    assert len(pins) == 1, f"pyproject pins several blastbox versions: {sorted(pins)}"
    pin = pins.pop()

    defaults = {}
    for path in sorted((ROOT / "deploy" / "docker").glob("Dockerfile*")):
        m = re.search(
            r"^ARG BLASTBOX_VERSION=(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE
        )
        if m:
            defaults[path.name] = m.group(1)
    assert defaults, "no Dockerfile defaults ARG BLASTBOX_VERSION; this test asserts nothing"
    wrong = {k: v for k, v in defaults.items() if v != pin}
    assert not wrong, f"pyproject pins {pin} but these default otherwise: {wrong}"
