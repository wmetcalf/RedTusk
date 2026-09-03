"""The node-autosizer overlay must not pin images or drift from the fleet.

Two failures this file guards, both observed in production:

* The host-local copy hardcoded `image: redtusk:024`, so applying it silently
  pinned all three dispatchers to blastbox 0.1.24 while the api followed .env.
  The stack ran mixed images and a version skew for weeks, invisible unless you
  diffed per container.
* The per-engine RAM figures are fleet-wide config -- every co-located
  dispatcher sizes against the same physical host -- and a figure that does not
  match what a guest ACTUALLY takes over-admits. titanarum declared 2560 against
  a `-Xmx4g -XX:+AlwaysPreTouch` engine and over-admitted by ~1.8x.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "deploy" / "docker" / "docker-compose.autosizer.yml"

# What every co-located dispatcher on a shared host must declare identically.
# Changing one of these is a FLEET change: titanarum's and clippyshot's copies
# must move with it, or the host is sized against two different budgets.
FLEET_WIDE = {
    "BLASTBOX_NODE_ENGINES": "redtusk,clippyshot,titanarum",
    # Derived from the guest setting rather than restated -- see the overlay.
    "BLASTBOX_NODE_ENGINE_REDTUSK_RAM_MIB": "${BLASTBOX_FC_MEM_MIB:-2048}",
    "BLASTBOX_NODE_ENGINE_CLIPPYSHOT_RAM_MIB": "4096",
    "BLASTBOX_NODE_ENGINE_TITANARUM_RAM_MIB": "4608",
    "BLASTBOX_NODE_SHARE_DIR": "/var/lib/blastbox/node",
    "BLASTBOX_NODE_RAM_HEADROOM": "0.8",
    "BLASTBOX_NODE_VCPU_OVERSUBSCRIPTION": "2.0",
}


@pytest.fixture(scope="module")
def overlay() -> dict[str, Any]:
    assert OVERLAY.is_file(), f"{OVERLAY} is gone; the fleet overlay must stay tracked"
    loaded = yaml.safe_load(OVERLAY.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _env_of(service: dict[str, Any]) -> dict[str, str]:
    env = service.get("environment") or []
    if isinstance(env, dict):
        return {str(k): str(v) for k, v in env.items()}
    out: dict[str, str] = {}
    for item in env:
        k, _, v = str(item).partition("=")
        out[k] = v
    return out


def test_no_service_hardcodes_an_image_tag(overlay: dict[str, Any]) -> None:
    """A literal tag here outranks .env and pins the stack to a stale build."""
    for name, svc in (overlay.get("services") or {}).items():
        image = (svc or {}).get("image")
        if image is None:
            continue
        assert image.startswith("${"), (
            f"service {name} hardcodes image {image!r}. The host-local copy did "
            "exactly this with redtusk:024 and pinned three dispatchers to "
            "blastbox 0.1.24 for weeks. Track ${REDTUSK_IMAGE}."
        )


def test_the_api_is_not_given_a_pool_identity(overlay: dict[str, Any]) -> None:
    """The api holds no warm pool; including it is how the stale tag spread."""
    assert "api" not in (overlay.get("services") or {}), (
        "the api is not a dispatcher and has nothing to publish"
    )


def test_every_dispatcher_participates(overlay: dict[str, Any]) -> None:
    """A dispatcher left out is a pool the balancer cannot see.

    That is the failure this overlay exists to fix: redtusk held 24 live
    firecracker guests that no peer could account for.
    """
    services = overlay.get("services") or {}
    for name in ("dispatcher", "dispatcher-fc", "dispatcher-gvisor"):
        assert name in services, f"{name} does not participate in node balancing"
        env = _env_of(services[name])
        assert env.get("BLASTBOX_NODE_RESOURCE_MANAGEMENT") == "1", name
        assert env.get("BLASTBOX_NODE_BALANCING") == "1", name


def test_every_participant_mounts_the_shared_view(overlay: dict[str, Any]) -> None:
    """Publishing without the mount writes into the container and helps nobody.

    Checked for every service the overlay defines, and the message says so: an
    earlier version claimed the service "declares node balancing" without ever
    checking that, which would have been a wrong diagnosis for any future
    non-participant service added here.
    """
    for name, svc in (overlay.get("services") or {}).items():
        vols = [str(v) for v in ((svc or {}).get("volumes") or [])]
        assert any("/var/lib/blastbox/node" in v for v in vols), (
            f"{name} is defined in the autosizer overlay but does not mount "
            "the node share dir; it would publish into its own container"
        )


@pytest.mark.parametrize("key,value", sorted(FLEET_WIDE.items()))
def test_the_fleet_wide_values_are_what_every_peer_declares(
    overlay: dict[str, Any], key: str, value: str
) -> None:
    """These are not per-repo preferences; they describe one physical host."""
    for name, svc in (overlay.get("services") or {}).items():
        env = _env_of(svc)
        assert env.get(key) == value, (
            f"{name} declares {key}={env.get(key)!r}, fleet expects {value!r}. "
            "If this is a deliberate fleet change, titanarum's and clippyshot's "
            "overlays must move with it."
        )


def test_the_declared_redtusk_ram_matches_what_a_guest_gets() -> None:
    """The balancer's figure must be the guest's ACTUAL size.

    `BLASTBOX_FC_MEM_MIB` is what a firecracker guest is given; declaring
    anything else over- or under-admits by exactly that ratio.
    """
    env_example = ROOT / "deploy" / "docker" / ".env.example"
    if not env_example.is_file():
        pytest.skip("no .env.example to compare against")
    text = env_example.read_text(encoding="utf-8")
    import re

    m = re.search(r"^BLASTBOX_FC_MEM_MIB=(\d+)", text, re.MULTILINE)
    if not m:
        pytest.skip(".env.example does not set BLASTBOX_FC_MEM_MIB")
    declared = FLEET_WIDE["BLASTBOX_NODE_ENGINE_REDTUSK_RAM_MIB"]
    fallback = declared.split(":-")[1].rstrip("}") if ":-" in declared else declared
    assert m.group(1) == fallback, (
        f"guests get {m.group(1)} MiB but the overlay's fallback declares "
        f"{fallback}. The overlay derives from BLASTBOX_FC_MEM_MIB, so only the "
        "fallback can drift -- keep it equal to the documented guest size."
    )
