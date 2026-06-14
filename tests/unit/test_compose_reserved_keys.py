"""Deploy-config guards for RedTusk's per-engine param security.

blastbox core is engine-agnostic — it names no RedTusk keys. RedTusk declares its own
dangerous knobs (the JVM binary/jar/opts/library + CRaC dirs — all code-exec vectors) as
reserved here, and every dispatcher (cold + the FC/gVisor warm sidecars) must carry both
the allowlist and the reserved floor, or a warm tier could forward a client's params to the
worker's REDTUSK_* knobs.
"""
from pathlib import Path

_DEPLOY = Path(__file__).resolve().parents[2] / "deploy" / "docker"

# Code-exec vectors a client must never set via job.params (engine reads them from
# os.environ when it launches / cold-falls-back the JVM).
_RESERVED = {
    "REDTUSK_JAVA_BIN", "REDTUSK_WORKER_JAR", "REDTUSK_JAVA_OPTS",
    "REDTUSK_JAVA_LIBRARY_PATH", "REDTUSK_AOT_CACHE",
    "REDTUSK_CRAC_CHECKPOINT", "REDTUSK_CRAC_SCRATCH",
}

_COMPOSE_FILES = (
    "docker-compose.yml",
    "docker-compose.firecracker.yml",
    "docker-compose.gvisor.yml",
)


def test_every_dispatcher_declares_redtusk_reserved_keys():
    """The reserved floor (RCE knobs) is set on cold + FC + gVisor dispatchers, with a
    non-empty default so it holds even with no extra .env config. Dropped unconditionally."""
    for fname in _COMPOSE_FILES:
        compose = (_DEPLOY / fname).read_text(encoding="utf-8")
        assert "BLASTBOX_ENGINE_REDTUSK_RESERVED_KEYS=" in compose, fname
        for key in _RESERVED:
            assert key in compose, f"{key} not reserved in {fname}"


def test_warm_sidecars_also_set_the_allowlist():
    """The FC + gVisor warm dispatchers must ALSO set the per-engine allowlist (default-deny)
    — mirroring the cold dispatcher. Without it they fall back to denylist-only and forward
    every shape-valid non-reserved param to the warm worker."""
    for fname in ("docker-compose.firecracker.yml", "docker-compose.gvisor.yml"):
        compose = (_DEPLOY / fname).read_text(encoding="utf-8")
        assert "BLASTBOX_ENGINE_REDTUSK_PARAM_KEYS=" in compose, (
            f"{fname} warm dispatcher is missing the allowlist (legacy denylist-only)"
        )


def test_tier_routing_env_wired():
    """Tier routing is operator/test-gated: the API carries BLASTBOX_ALLOW_TIER_ROUTING (default
    off) and every dispatcher carries BLASTBOX_MAX_QUEUED_AGE_S (bound a down-tier-pinned job)."""
    base = (_DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    assert "BLASTBOX_ALLOW_TIER_ROUTING=${BLASTBOX_ALLOW_TIER_ROUTING:-}" in base
    for fname in _COMPOSE_FILES:
        compose = (_DEPLOY / fname).read_text(encoding="utf-8")
        assert "BLASTBOX_MAX_QUEUED_AGE_S=${BLASTBOX_MAX_QUEUED_AGE_S:-0}" in compose, fname
