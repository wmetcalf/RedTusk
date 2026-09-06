"""Every Dockerfile must pin the SAME Tika fork commit.

Four Dockerfiles declare `TIKA_FORK_SHA` independently and nothing kept them in
step. A bump that updates three of them leaves the fourth building a different
fork -- and every file still looks deliberate, because each one carries a
plausible pinned sha and a comment explaining it. That is the failure mode a
supply-chain pin exists to prevent, reintroduced by having four of them.

Discovered while moving the pin to the OCR downscale fix: `Dockerfile.crac`
carries the pin too and is easy to miss, because it declares it on a different
line than the others.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCKER_DIR = REPO / "deploy" / "docker"
_PIN = re.compile(r"^ARG TIKA_FORK_SHA=(\S+)", re.MULTILINE)


def _declared_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    for f in sorted(DOCKER_DIR.glob("Dockerfile*")):
        m = _PIN.search(f.read_text())
        if m:
            pins[f.name] = m.group(1)
    return pins


def test_every_dockerfile_pins_the_same_tika_commit():
    pins = _declared_pins()
    assert pins, f"no Dockerfile under {DOCKER_DIR} declares TIKA_FORK_SHA"
    distinct = set(pins.values())
    assert len(distinct) == 1, (
        "these Dockerfiles would build from different Tika forks: "
        + "; ".join(f"{k}={v}" for k, v in sorted(pins.items()))
    )


def test_the_pin_is_a_full_length_commit_sha():
    """An abbreviated sha is ambiguous, and `git checkout` accepts a branch name
    just as happily -- either would turn a pin into a moving target."""
    for name, sha in sorted(_declared_pins().items()):
        assert re.fullmatch(r"[0-9a-f]{40}", sha), f"{name} pins {sha!r}"
