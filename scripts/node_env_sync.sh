#!/usr/bin/env bash
# node_env_sync.sh — materialize per-HOST identifiers into every engine stack's
# compose .env, so a freshly-provisioned box can join the fleet without hand-editing.
#
# WHY THIS EXISTS
# ---------------
# Compose `group_add:` entries need NUMERIC gids, and those gids differ per host
# (observed in the wild: docker gid 110 on one node, 988 on another; kvm likewise).
# The compose files carry defaults (`${DOCKER_GID:-984}`) which are silently WRONG
# on any box that doesn't happen to match. The failure is quiet and confusing: the
# dispatcher starts fine, cannot reach the docker socket, reports
# "runsc unavailable; falling back to runc (insecure)", and then REQUIRE_SECURE_RUNTIME
# refuses every job — which reads like an engine bug, not a gid bug.
#
# A second, nastier variant: compose overlays REPLACE lists rather than merging them.
# deploy/docker/docker-compose.firecracker.yml sets `group_add: ["${KVM_GID}"]`, which
# DROPS the docker gid inherited from the base file. The FC dispatcher then has /dev/kvm
# but no docker access, so the Firecracker tier never launches a worker and the gVisor
# tier silently absorbs the whole engine.
#
# This script is the single source of truth for those values. Run it on a node after
# provisioning (and after any docker/kvm reinstall, which can renumber the groups).
#
# Idempotent. Safe to re-run. Does not restart anything unless --restart is given.
#
# Usage:
#   scripts/node_env_sync.sh [--stack DIR]... [--restart] [--dry-run]
#
#   --stack DIR   A deploy/docker dir holding a .env (repeatable). If omitted, the
#                 script auto-discovers the standard fleet stacks under $HOME.
#   --restart     Recreate the dispatcher containers so the new gids take effect.
#                 (Env changes require container RECREATION, not just a restart.)
#   --dry-run     Print what would change; write nothing.
set -euo pipefail

DRY=0; RESTART=0; STACKS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --stack)   STACKS+=("$2"); shift 2 ;;
        --restart) RESTART=1; shift ;;
        --dry-run) DRY=1; shift ;;
        -h|--help) sed -n '1,32p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

log(){ printf '\033[1;36m[node-env]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[node-env]\033[0m %s\n' "$*" >&2; }
die(){ printf '\033[1;31m[node-env]\033[0m %s\n' "$*" >&2; exit 1; }

# ── 1. Discover the per-host values ──────────────────────────────────────────
# These are the ONLY things that legitimately vary per box. Everything else in
# .env is fleet-wide config and is left untouched.
DOCKER_GID=$(getent group docker | cut -d: -f3 || true)
# The DEVICE's group, not the group table: after custom udev rules, group
# renumbering or device passthrough the two disagree, and it is the device's GID
# that decides whether the non-root dispatcher can open /dev/kvm. Same source the
# compose wrapper uses for docker.sock. The group table is the fallback for a
# host where /dev/kvm is absent (nothing to read, and the FC tier is refused
# anyway).
KVM_GID=$(stat -c '%g' /dev/kvm 2>/dev/null || true)
[ -n "$KVM_GID" ] || KVM_GID=$(getent group kvm | cut -d: -f3 || true)

[ -n "$DOCKER_GID" ] || die "no 'docker' group on this host — is Docker installed?"
[ -n "$KVM_GID" ]    || die "no 'kvm' group on this host — Firecracker needs /dev/kvm"
[ -e /dev/kvm ]      || warn "/dev/kvm absent: the Firecracker tier will not work here"

log "host identifiers: DOCKER_GID=$DOCKER_GID  KVM_GID=$KVM_GID"

# Sanity: the socket must actually be readable by DOCKER_GID, else we'd write a
# plausible-but-useless value and reproduce the exact silent failure this fixes.
if [ -S /var/run/docker.sock ]; then
    sock_gid=$(stat -c %g /var/run/docker.sock)
    [ "$sock_gid" = "$DOCKER_GID" ] || \
        warn "docker.sock is group $sock_gid but 'docker' group is $DOCKER_GID — using the SOCKET's gid"
    [ "$sock_gid" = "$DOCKER_GID" ] || DOCKER_GID="$sock_gid"
fi

# ── 2. Locate the stacks ─────────────────────────────────────────────────────
if [ ${#STACKS[@]} -eq 0 ]; then
    for d in "$HOME"/*/deploy/docker; do
        [ -f "$d/.env" ] && STACKS+=("$d")
    done
fi
[ ${#STACKS[@]} -gt 0 ] || die "no stacks found (looked for \$HOME/*/deploy/docker/.env)"

# ── 3. Upsert the keys ───────────────────────────────────────────────────────
upsert(){ # $1=file  $2=key  $3=value  -> prints "changed" or "ok"
    local f="$1" k="$2" v="$3" cur
    cur=$(grep -E "^${k}=" "$f" 2>/dev/null | tail -1 | cut -d= -f2- || true)
    if [ "$cur" = "$v" ]; then printf 'ok'; return; fi
    [ "$DRY" = 1 ] && { printf 'would-set(%s->%s)' "${cur:-unset}" "$v"; return; }
    if grep -qE "^${k}=" "$f"; then
        sed -i -E "s|^${k}=.*|${k}=${v}|" "$f"
    else
        # keep a trailing newline discipline so repeated runs don't glue lines
        [ -s "$f" ] && [ "$(tail -c1 "$f" | wc -l)" -eq 0 ] && printf '\n' >> "$f"
        printf '%s=%s\n' "$k" "$v" >> "$f"
    fi
    printf 'set(%s->%s)' "${cur:-unset}" "$v"
}

changed_any=0
for d in "${STACKS[@]}"; do
    f="$d/.env"
    [ -f "$f" ] || { warn "skip $d (no .env)"; continue; }
    r1=$(upsert "$f" DOCKER_GID "$DOCKER_GID")
    r2=$(upsert "$f" KVM_GID    "$KVM_GID")
    log "$(basename "$(dirname "$(dirname "$d")")"): DOCKER_GID=$r1 KVM_GID=$r2"
    case "$r1$r2" in *set*) changed_any=1 ;; esac
done

# ── 4. Optionally recreate dispatchers so the gids take effect ───────────────
if [ "$RESTART" = 1 ] && [ "$DRY" = 0 ]; then
    if [ "$changed_any" = 0 ]; then
        log "nothing changed — skipping recreate"
    else
        for d in "${STACKS[@]}"; do
            ( cd "$d" || exit 0
              # `up -d` recreates only containers whose config hash changed.
              # A bare `restart` would NOT pick up new env — it reuses the old config.
              files=(-f docker-compose.yml)
              [ -f docker-compose.gvisor.yml ]     && files+=(-f docker-compose.gvisor.yml)
              [ -f docker-compose.firecracker.yml ] && files+=(-f docker-compose.firecracker.yml)
              [ -f docker-compose.autosizer.yml ]  && files+=(-f docker-compose.autosizer.yml)
              log "recreating dispatchers in $d"
              docker compose "${files[@]}" up -d --no-deps \
                  dispatcher dispatcher-fc dispatcher-gvisor 2>&1 | sed 's/^/    /' || \
                  warn "recreate failed in $d (check compose file set)"
            )
        done
    fi
fi

log "done. Verify with:  docker inspect <dispatcher> --format '{{.HostConfig.GroupAdd}}'"
