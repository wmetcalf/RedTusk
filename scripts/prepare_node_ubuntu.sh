#!/usr/bin/env bash
# Prepare a bare Ubuntu node to be a RedTusk warm worker (Firecracker + gVisor)
# in the multi-node autoscaling fleet. Idempotent — re-running is safe.
#
# This is the OS-LEVEL provisioner. It installs everything a fresh node needs so
# that `scripts/setup_firecracker_host.sh` can build the kernel+rootfs and the
# blastbox FC/gVisor dispatchers can run:
#
#   1. Preflight: Ubuntu 24.04 / x86_64, root/sudo, /dev/kvm.
#   2. Base apt packages (curl, gnupg, git, jq, e2fsprogs, python3, build deps).
#   3. Docker Engine (official repo) — if missing.
#   4. KVM group: ensure it exists, add the deploy user, report KVM_GID (the
#      compose `group_add` needs it).
#   5. Firecracker + jailer (pinned release from GitHub, TLS + optional sha256
#      pin) → /usr/local/bin and the FC assets dir.
#   6. gVisor / runsc (official apt repo) — for the gVisor tier / cascade fallback.
#   7. Standard dirs: job root, scratch, FC assets, and the node-autosizer share
#      dir (0.1.24) — all owned by the deploy user/group.
#   8. Host tuning: fd limits + vm.max_map_count (JVM + many microVMs).
#   9. Hand off to scripts/setup_firecracker_host.sh for the kernel + rootfs
#      (unless --no-fc-assets). Pass --with-kernel to build one here, or
#      --kernel-from host:/path to copy a known-good vmlinux from a reference node.
#  10. Validate + print the compose .env fragment + next steps.
#
# This script does NOT deploy the stack or start any service. It only provisions
# the host. Deploy is a separate, reviewed step.
#
# Usage:
#   sudo scripts/prepare_node_ubuntu.sh \
#       [--deploy-user <user>] \
#       [--firecracker-version 1.16.0] [--firecracker-sha256 <hex>] \
#       [--firecracker-from <user>@<reference-node>:/usr/local/bin/firecracker] \
#       [--no-gvisor] \
#       [--no-fc-assets] [--with-kernel] [--kernel-from <user>@<reference-node>:/path/vmlinux] \
#       [--aws-burst] \
#       [--check]
#
# --aws-burst installs the AWS CLI v2 so THIS node can run the control-plane burst
# dispatcher (BLASTBOX_POOL_RUNTIME=aws-*, the demand-driven AWS scale-out tier). It
# installs tooling ONLY — AWS credentials are NEVER written by this script; place them
# in a directory named by AWS_CREDS_DIR in deploy/docker/.env, which the burst overlay
# mounts read-only. The dispatcher runs as uid 10001 and must be able to READ them,
# which a 0700 ~/.aws is not. The AWS tiers fail closed unless `aws sts` passes.
set -euo pipefail

# ── config / args ──────────────────────────────────────────────────────────
DEPLOY_USER="${SUDO_USER:-$USER}"
FIRECRACKER_VERSION=1.16.0        # match an existing reference node's /usr/local/bin/firecracker
FIRECRACKER_SHA256=""             # optional: verify the downloaded tarball (fail-closed if set + mismatch)
FIRECRACKER_FROM=""               # optional: scp the binary from a reference node instead of downloading
WITH_GVISOR=1
FC_ASSETS=1                       # call setup_firecracker_host.sh at the end
WITH_KERNEL=0                     # pass through to setup_firecracker_host.sh
KERNEL_FROM=""                    # scp a known-good vmlinux from a reference node (skips the kernel build)
AWS_BURST=0                       # also install the AWS CLI for the control-plane burst dispatcher
CHECK_ONLY=0

# Standard host paths (match deploy/docker/docker-compose.firecracker.yml defaults).
REDTUSK_DATA_DIR=/var/lib/redtusk        # job root lives at $REDTUSK_DATA_DIR/jobs
REDTUSK_FC_DIR=/var/lib/redtusk-fc       # FC assets: firecracker, vmlinux, redtusk-rootfs.ext4
NODE_SHARE_DIR=/var/lib/blastbox/node    # node-autosizer shared dir (0.1.24)

while [ $# -gt 0 ]; do
    case "$1" in
        --deploy-user)         DEPLOY_USER=$2; shift 2 ;;
        --firecracker-version) FIRECRACKER_VERSION=$2; shift 2 ;;
        --firecracker-sha256)  FIRECRACKER_SHA256=$2; shift 2 ;;
        --firecracker-from)    FIRECRACKER_FROM=$2; shift 2 ;;
        --no-gvisor)           WITH_GVISOR=0; shift ;;
        --no-fc-assets)        FC_ASSETS=0; shift ;;
        --with-kernel)         WITH_KERNEL=1; shift ;;
        --kernel-from)         KERNEL_FROM=$2; shift 2 ;;
        --aws-burst)           AWS_BURST=1; shift ;;
        --check)               CHECK_ONLY=1; shift ;;
        -h|--help)             sed -n '/^#/,/^set -euo/p' "$0" | sed 's/^# \?//;/^set -euo/d'; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
ARCH=$(uname -m)
log()  { printf '\033[1;36m[prep-node]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[prep-node] WARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[prep-node] FATAL:\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# Run a privileged command. When invoked as root, sudo may be absent — run directly.
SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO=sudo

# ── 1. preflight ───────────────────────────────────────────────────────────
log "preflight"
[ -r /etc/os-release ] && . /etc/os-release || die "cannot read /etc/os-release"
[ "${ID:-}" = "ubuntu" ] || warn "not Ubuntu ($ID) — tested on 24.04; proceeding best-effort"
case "${VERSION_ID:-}" in 24.04|22.04) : ;; *) warn "untested Ubuntu $VERSION_ID (expected 24.04)";; esac
[ "$ARCH" = "x86_64" ] || warn "arch $ARCH — FC assets + firecracker URL assume x86_64; aarch64 needs the arm64 artifacts"
have "$([ -n "$SUDO" ] && echo sudo || echo sh)" || die "sudo required when not root"
[ -e /dev/kvm ] || die "/dev/kvm absent — this node has no KVM (bare metal or nested-virt required for Firecracker)"
id "$DEPLOY_USER" >/dev/null 2>&1 || die "deploy user '$DEPLOY_USER' does not exist"
log "node: $PRETTY_NAME / $ARCH / deploy-user=$DEPLOY_USER / $(nproc)vCPU / $(free -g | awk '/^Mem:/{print $2"GB"}') RAM"

run_as_deploy() {
    # Run a command AS THE DEPLOY USER, whether or not we are already root.
    # `$SUDO -u "$DEPLOY_USER" ...` was wrong under the documented `sudo`
    # invocation: as root $SUDO is EMPTY, so the command began with `-u` and the
    # shell could not execute it. The caller's `if !` turned that into a warning,
    # so provisioning printed `done` having never built the kernel or rootfs.
    if [ "$(id -un)" = "$DEPLOY_USER" ]; then
        "$@"
    elif [ "$(id -u)" -eq 0 ] && have runuser; then
        runuser -u "$DEPLOY_USER" -- "$@"
    else
        sudo -u "$DEPLOY_USER" -- "$@"
    fi
}

_aws_creds_home() {
    # The deploy user's home from passwd, not $HOME: under the documented `sudo`
    # invocation $HOME is /root, and every probe below would read /root/.aws.
    local home
    home=$(getent passwd "$DEPLOY_USER" 2>/dev/null | cut -d: -f6)
    [ -n "$home" ] || home="$HOME"
    echo "${AWS_CREDS_HOME:-$home}"
}

# The uid and gid the burst dispatcher runs as: Dockerfile.host's `USER 10001:10001`,
# or REDTUSK_WORKER_UID/GID for a ${REDTUSK_IMAGE} that runs as someone else.
# Prints `uid gid`.
_dispatcher_ids() {
    local uid="${REDTUSK_WORKER_UID:-10001}"
    echo "$uid ${REDTUSK_WORKER_GID:-$uid}"
}

# What the burst dispatcher will be given, ASKED OF COMPOSE: it owns the
# environment-over-.env precedence, ${VAR} interpolation and relative paths, so
# re-deriving them here would be a second resolver to drift from the first. HOME
# is the deploy user's (`AWS_CREDS_DIR=${HOME}/.aws` is a valid .env value and
# this runs under sudo). Placeholders stand in for the overlay's OTHER required
# variables so an unfinished .env still resolves; they cannot affect these values.
# Prints three lines -- the /aws mount source, BLASTBOX_AWS_PROFILE, and `1` when
# .env passes the container a non-empty AWS_ACCESS_KEY_ID (never the key itself) --
# or nothing when compose cannot be asked (no docker yet on a fresh node). Those keys
# do not replace the files: blastbox always runs `aws --profile <that>`, and an
# explicit profile reads the mounted files -- unless that profile says
# `credential_source = Environment`.
_aws_burst_compose() {
    have docker && have python3 || return 0
    ( cd "$REPO_ROOT/deploy/docker" &&
      env HOME="$(_aws_creds_home)" POSTGRES_PASSWORD=placeholder BLASTBOX_AWS_REGION=placeholder \
          docker compose -f docker-compose.yml -f docker-compose.aws-burst.yml config --format json |
      python3 -c 'import json, sys
svc = json.load(sys.stdin)["services"]["dispatcher-aws-burst"]
env = svc.get("environment") or {}
if isinstance(env, list):
    env = dict(e.split("=", 1) if "=" in e else (e, "") for e in env)
src = [m.get("source", "") for m in svc.get("volumes", []) if m.get("target") == "/aws"]
if src and src[0]:
    print(src[0]); print(env.get("BLASTBOX_AWS_PROFILE") or "default")
    print(1 if env.get("AWS_ACCESS_KEY_ID") else 0)' ) 2>/dev/null || true
}

_aws_creds_dir() {
    _aws_burst_compose | sed -n 1p
}

# The directory every consumer below uses: what compose mounts, else the deploy
# user's ~/.aws. Returns 1 for the fallback, so a verdict can say it is a guess.
_aws_creds_effective_dir() {
    local dir; dir="$(_aws_creds_dir)"
    if [ -n "$dir" ]; then printf '%s' "$dir"; return 0; fi
    printf '%s' "$(_aws_creds_home)/.aws"; return 1
}

_aws_sts_ok() {
    # Against the credentials the overlay will MOUNT and the profile it selects,
    # as the caller -- WITHOUT the caller's own AWS_* environment, which the CLI
    # prefers over the files and the container never sees.
    local dir profile
    dir="$(_aws_creds_effective_dir)" || true
    profile="$(_aws_burst_compose | sed -n 2p)"
    (
        # EVERY AWS_* variable, not a list of the ones known today: endpoint, SSO
        # and container-credential variables all change what sts answers.
        while read -r v; do unset "$v"; done < <(compgen -e | grep '^AWS_' || true)
        AWS_PROFILE="${profile:-default}" \
        AWS_SHARED_CREDENTIALS_FILE="$dir/credentials" \
        AWS_CONFIG_FILE="$dir/config" \
        aws sts get-caller-identity >/dev/null 2>&1
    )
}

# Can the DISPATCHER read this file? `aws sts` above runs as the deploy user or
# root; the container runs as $(_dispatcher_ids) with `cap_drop: ALL` and
# no-new-privileges, and a normal ~/.aws is 0700/0600 owned by the deploy user.
# So the OS is asked, as that uid and gid, with no supplementary groups and no
# capabilities (root keeping CAP_DAC_OVERRIDE would read anything). setpriv takes
# raw ids, which matters: 10001 has no passwd entry on the host, so `sudo -u
# '#10001'` fails before testing anything. The test runs from INSIDE the
# directory on a relative name, because docker binds the directory itself and
# the container never traverses its parents.
#
# Returns 0 readable, 1 NOT readable, 2 could not test -- a probe that cannot run
# is not evidence either way.
_aws_readable_by_dispatcher() {
    local file="$1" uid gid pre="" out=""
    read -r uid gid <<< "$(_dispatcher_ids)"
    case "$uid$gid" in ""|*[!0-9]*) return 2 ;; esac
    have setpriv || return 2
    if [ "$(id -u)" != 0 ]; then have sudo || return 2; pre="sudo -n"; fi
    out="$(cd "$(dirname "$file")" 2>/dev/null &&
           $pre setpriv --reuid="$uid" --regid="$gid" --clear-groups \
               --bounding-set=-all --inh-caps=-all --ambient-caps=-all --nnp \
               sh -c 'test -r "$1" && echo YES || echo NO' _ "$(basename "$file")" 2>/dev/null)" || true
    case "$out" in
        YES) return 0 ;;
        NO)  return 1 ;;
        *)   return 2 ;;
    esac
}

_aws_creds_status() {
    local dir guess="" creds f rc uid gid why="" bad="" envsrc="" sts="sts ok"
    have aws || { echo "n/a (no aws cli)"; return; }
    if ! dir="$(_aws_creds_effective_dir)"; then
        guess=" [compose could not resolve AWS_CREDS_DIR; this is the deploy user's ~/.aws]"
    fi
    creds="$dir/credentials"
    if [ -e "$dir" ] && [ ! -d "$dir" ]; then
        echo "invalid — $dir is not a directory; AWS_CREDS_DIR must name the directory holding credentials$guess"
        return
    fi
    read -r uid gid <<< "$(_dispatcher_ids)"
    # A dispatcher-owned copy (the first remediation below) is one the CALLER may
    # not be able to see into; that is not the same as absent or invalid.
    if [ -e "$dir" ] && { [ ! -x "$dir" ] ||
            { [ -e "$creds" ] && [ ! -r "$creds" ]; } ||
            { [ -e "$dir/config" ] && [ ! -r "$dir/config" ]; }; }; then
        echo "NOT CONFIRMED — $(id -un) cannot read $dir; re-run with sudo$guess"
        return
    fi
    [ -f "$creds" ] || { echo "absent — place $creds$guess"; return; }
    if ! _aws_sts_ok; then
        # sts runs WITHOUT any keys (they are secrets this script does not
        # handle), so a profile that sources them from the environment fails
        # here while working in the container.
        # A profile with `credential_source = Environment` uses the keys .env
        # passes the container, which --check deliberately does not handle, so
        # with keys in .env a failure here is not proof. Which profile does that
        # is the CLI's config grammar to decide, not this script's -- the same
        # reason the mount is asked of compose. The probe below still runs.
        if [ "$(_aws_burst_compose | sed -n 3p)" = 1 ]; then
            envsrc=1
            sts="sts failed without keys, but .env passes the container AWS_ACCESS_KEY_ID, which a credential_source=Environment profile would use"
        else
            echo "invalid — $creds present but 'aws sts get-caller-identity' failed$guess"
            return
        fi
    fi
    # The overlay sets AWS_CONFIG_FILE=/aws/config too, and a role profile does not
    # resolve without it: absent is fine, present-but-unreadable is not.
    for f in "$creds" "$dir/config"; do
        [ -e "$f" ] || [ -L "$f" ] || continue
        if [ -L "$f" ]; then
            # The directory is bind-mounted ALONE and link text is not rewritten,
            # so a link can resolve on the host and dangle in the container.
            why="${why:-$f is a symlink; copy the real file in}"; continue
        fi
        case "$uid$gid" in
            ""|*[!0-9]*) why="REDTUSK_WORKER_UID/GID must be numeric (got '$uid:$gid')"; break ;;
        esac
        rc=0; _aws_readable_by_dispatcher "$f" || rc=$?
        case "$rc" in
            1) bad="$f"; break ;;
            2) why="${why:-uid $uid could not be tested (needs setpriv, and root or sudo -n)}" ;;
        esac
    done
    # Every verdict about a GUESSED directory leads with NOT CONFIRMED: the overlay
    # requires AWS_CREDS_DIR, so the real mount may be somewhere else entirely.
    if [ -n "$bad" ] && [ -z "$guess" ]; then
        echo "UNUSABLE — uid $uid (the dispatcher) cannot read $bad; the burst tier will fail closed ($sts for $creds as $(id -un)). See the burst notes."
    elif [ -n "$guess" ]; then
        echo "NOT CONFIRMED — $sts for $creds, and $([ -n "$bad" ] && echo "uid $uid cannot read $bad" || echo "${why:-uid $uid can read it}"), but that is only a guess at the mount$guess"
    elif [ -n "$envsrc" ]; then
        echo "NOT CONFIRMED — $sts; ${why:-uid $uid can read $creds and the config}"
    elif [ -n "$why" ]; then
        echo "valid (sts ok, $creds; NOT CONFIRMED — $why)$guess"
    else
        echo "valid (sts ok, $creds; readable by uid $uid)$guess"
    fi
}

if [ "$CHECK_ONLY" -eq 1 ]; then
    log "--check: reporting current state, changing nothing"
    printf '  docker      : %s\n' "$(docker --version 2>/dev/null || echo MISSING)"
    printf '  firecracker : %s\n' "$( (firecracker --version 2>/dev/null || echo MISSING) | head -1)"
    printf '  jailer      : %s\n' "$(have jailer && echo present || echo MISSING)"
    printf '  runsc       : %s\n' "$(runsc --version 2>/dev/null | head -1 || echo MISSING)"
    printf '  kvm gid     : %s\n' "$(getent group kvm | cut -d: -f3 || echo MISSING)"
    printf '  user in kvm : %s\n' "$(id -nG "$DEPLOY_USER" | tr ' ' '\n' | grep -qx kvm && echo yes || echo NO)"
    printf '  e2fsprogs   : %s\n' "$(have mkfs.ext4 && have debugfs && echo present || echo MISSING)"
    for d in "$REDTUSK_DATA_DIR/jobs" "$REDTUSK_FC_DIR" "$NODE_SHARE_DIR"; do
        printf '  dir %-24s : %s\n' "$d" "$([ -d "$d" ] && echo present || echo MISSING)"
    done
    printf '  fc assets   : %s\n' "$([ -f "$REDTUSK_FC_DIR/vmlinux" ] && [ -f "$REDTUSK_FC_DIR/redtusk-rootfs.ext4" ] && echo present || echo INCOMPLETE)"
    printf '  aws cli     : %s\n' "$(aws --version 2>/dev/null | head -1 || echo 'MISSING (--aws-burst)')"
    # The directory compose mounts at /aws (the deploy user's ~/.aws only as a flagged
    # guess), validated with sts and probed for readability as the dispatcher uid.
    printf '  aws creds   : %s\n' "$(_aws_creds_status)"
    exit 0
fi

# ── 2. base packages ───────────────────────────────────────────────────────
log "installing base packages"
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -q
BASE_PKGS="ca-certificates curl gnupg git jq e2fsprogs python3 acl"
# kernel build deps only when we'll build a kernel here
[ "$WITH_KERNEL" -eq 1 ] && BASE_PKGS="$BASE_PKGS build-essential bc flex bison libelf-dev libssl-dev"
$SUDO apt-get install -y -q $BASE_PKGS
have mkfs.ext4 && have debugfs || die "e2fsprogs did not provide mkfs.ext4/debugfs"

# ── 3. Docker Engine ───────────────────────────────────────────────────────
if have docker; then
    log "docker present: $(docker --version)"
else
    log "installing Docker Engine (official repo)"
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
        | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
    $SUDO apt-get update -q
    $SUDO apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    $SUDO systemctl enable --now docker
fi
# let the deploy user drive docker (for image builds / setup_firecracker_host.sh)
id -nG "$DEPLOY_USER" | tr ' ' '\n' | grep -qx docker || { log "adding $DEPLOY_USER to docker group"; $SUDO usermod -aG docker "$DEPLOY_USER"; }

# ── 4. KVM group ───────────────────────────────────────────────────────────
getent group kvm >/dev/null || { log "creating kvm group"; $SUDO groupadd -r kvm; }
KVM_GID=$(getent group kvm | cut -d: -f3)
if id -nG "$DEPLOY_USER" | tr ' ' '\n' | grep -qx kvm; then
    log "$DEPLOY_USER already in kvm group (gid $KVM_GID)"
else
    log "adding $DEPLOY_USER to kvm group (gid $KVM_GID) — re-login or 'sg kvm' to take effect"
    $SUDO usermod -aG kvm "$DEPLOY_USER"
fi

# ── 5. Firecracker + jailer ────────────────────────────────────────────────
FC_ARCH="$ARCH"   # firecracker publishes x86_64 / aarch64
install_firecracker() {
    local tmp; tmp=$(mktemp -d)
    if [ -n "$FIRECRACKER_FROM" ]; then
        log "copying firecracker from $FIRECRACKER_FROM"
        scp -q "$FIRECRACKER_FROM" "$tmp/firecracker" || die "scp firecracker from $FIRECRACKER_FROM failed"
        # jailer sits next to it on the reference node by convention
        scp -q "${FIRECRACKER_FROM%/*}/jailer" "$tmp/jailer" 2>/dev/null || warn "no jailer next to $FIRECRACKER_FROM — bare-metal jailer mode unavailable"
    else
        local url="https://github.com/firecracker-microvm/firecracker/releases/download/v${FIRECRACKER_VERSION}/firecracker-v${FIRECRACKER_VERSION}-${FC_ARCH}.tgz"
        log "downloading firecracker v$FIRECRACKER_VERSION ($FC_ARCH)"
        curl -fsSL -o "$tmp/fc.tgz" "$url" || die "download failed: $url"
        if [ -n "$FIRECRACKER_SHA256" ]; then
            echo "${FIRECRACKER_SHA256}  $tmp/fc.tgz" | sha256sum -c - || die "firecracker tarball sha256 MISMATCH (supply-chain check)"
            log "firecracker tarball sha256 verified"
        else
            warn "no --firecracker-sha256 pin — trusting the TLS GitHub release only. Pin a hash for a hardened deploy (sha256sum a known-good reference node's binary)."
        fi
        tar -xf "$tmp/fc.tgz" -C "$tmp"
        local rel="$tmp/release-v${FIRECRACKER_VERSION}-${FC_ARCH}"
        cp "$rel/firecracker-v${FIRECRACKER_VERSION}-${FC_ARCH}" "$tmp/firecracker"
        cp "$rel/jailer-v${FIRECRACKER_VERSION}-${FC_ARCH}" "$tmp/jailer" 2>/dev/null || true
    fi
    $SUDO install -m 0755 "$tmp/firecracker" /usr/local/bin/firecracker
    [ -f "$tmp/jailer" ] && $SUDO install -m 0755 "$tmp/jailer" /usr/local/bin/jailer || true
    rm -rf "$tmp"
}
if have firecracker; then
    log "firecracker present: $(firecracker --version 2>&1 | head -1)"
else
    install_firecracker
    log "firecracker installed: $(firecracker --version 2>&1 | head -1)"
fi

# ── 6. gVisor / runsc ──────────────────────────────────────────────────────
if [ "$WITH_GVISOR" -eq 1 ]; then
    if have runsc; then
        log "runsc present: $(runsc --version | head -1)"
    else
        log "installing gVisor (runsc) from the official apt repo"
        curl -fsSL https://gvisor.dev/archive.key | $SUDO gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" \
            | $SUDO tee /etc/apt/sources.list.d/gvisor.list >/dev/null
        # SEPARATE statements. `set -e` does not fire for the left operand of `&&`, so an
        # apt-get update that failed (unreachable repo, key problem) SKIPPED the install and
        # provisioning carried on: `have runsc` was false, the line below warned about
        # "registration", and the final log printed `runsc installed:` with an empty version
        # because the failing `runsc --version` sits inside a command substitution whose
        # status nothing reads. The node then joined the fleet with no gVisor tier at all,
        # reporting success -- the same silent-tier failure as the per-host GID drift.
        $SUDO apt-get update -q
        $SUDO apt-get install -y -q runsc
        have runsc || die "gVisor install reported success but runsc is not on PATH"
        # register the runsc docker runtime (for the gVisor tier if used directly)
        $SUDO runsc install >/dev/null 2>&1 && $SUDO systemctl restart docker || warn "runsc docker-runtime registration skipped"
        log "runsc installed: $(runsc --version | head -1)"
    fi
else
    log "skipping gVisor (--no-gvisor)"
fi

# ── 6b. AWS CLI v2 (control-plane burst tier, --aws-burst) ──────────────────
# The AWS scale-out tier runs a burst dispatcher that claims from the shared queue
# and PUSHES jobs to disposable AWS workers over HTTPS (blastbox aws_worker shells
# out to `aws`). Install the CLI system-wide so the burst dispatcher container can
# bind-mount it. TOOLING ONLY — credentials are the operator's to place at
# ~/.aws/credentials; this script never reads or writes them.
if [ "$AWS_BURST" -eq 1 ]; then
    if have aws; then
        log "aws cli present: $(aws --version 2>&1 | head -1)"
    else
        log "installing AWS CLI v2 (system-wide, for the burst dispatcher)"
        case "$ARCH" in
            x86_64)  AWS_ZIP_ARCH=x86_64 ;;
            aarch64) AWS_ZIP_ARCH=aarch64 ;;
            *) die "AWS CLI v2 has no bundle for arch $ARCH" ;;
        esac
        have unzip || $SUDO apt-get install -y -q unzip
        tmpd=$(mktemp -d)
        curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ZIP_ARCH}.zip" -o "$tmpd/awscliv2.zip" \
            || die "AWS CLI download failed"
        unzip -q -o "$tmpd/awscliv2.zip" -d "$tmpd"
        # --update makes re-runs idempotent (in-place upgrade of an existing install).
        $SUDO "$tmpd/aws/install" --update 2>&1 | tail -1
        rm -rf "$tmpd"
        have aws && log "installed: $(aws --version 2>&1 | head -1)" || warn "aws still not on PATH after install"
    fi
    # Provision-time entitlement check — friendlier than discovering it at first burst
    # (the runtime ALSO fails closed on this). Warn, don't die: creds may be placed later.
    # The same verdict --check gives: sts passing as root says nothing about
    # whether the dispatcher uid can read the mounted files.
    _creds_status="$(_aws_creds_status)"
    case "$_creds_status" in
        *"NOT CONFIRMED"*) warn "aws creds: $_creds_status — address the reason given, then re-run --check" ;;
        valid*) log "aws creds: $_creds_status" ;;
        *)      warn "aws creds: $_creds_status — fix, then re-run --check" ;;
    esac
fi

# ── 7. standard dirs (owned by the deploy user/group) ──────────────────────
log "creating standard dirs"
DGRP=$(id -gn "$DEPLOY_USER")
# The uid the api/dispatcher/worker containers run as (see Dockerfile.host).
REDTUSK_WORKER_UID=${REDTUSK_WORKER_UID:-10001}
# The FC dispatcher runs in a container with ${REDTUSK_FC_DIR} bind-mounted at
# /var/lib/blastbox-fc, and reads BLASTBOX_FC_BIN=/var/lib/blastbox-fc/firecracker
# from there -- /usr/local/bin on the host is not visible to it. Installing only
# to /usr/local/bin left the tier unable to find its own executable on a node
# this script had just declared ready.
stage_firecracker_asset() {
    have firecracker || return 0
    [ -x "$REDTUSK_FC_DIR/firecracker" ] && return 0
    $SUDO install -m 0755 "$(command -v firecracker)" "$REDTUSK_FC_DIR/firecracker" \
        && log "staged firecracker into $REDTUSK_FC_DIR (the dispatcher's mounted path)"
}

for d in "$REDTUSK_DATA_DIR/jobs" "$REDTUSK_DATA_DIR/scratch" "$REDTUSK_FC_DIR"; do
    $SUDO mkdir -p "$d"; $SUDO chown "$DEPLOY_USER:$DGRP" "$d"
done
stage_firecracker_asset
# node-autosizer share: single-trust-domain surface written only by dispatchers on
# THIS host; bind-mounted into each engine stack. Group-writable so co-located
# dispatchers (same deploy group) all publish/read.
#
# Owned by the WORKER uid, not the deploy user: the dispatcher publishes from
# inside its container as UID 10001, and 2770 owned by the deploy user left that
# process unable to write. The failure is silent -- blastbox logs and disables
# sizing rather than crashing dispatch -- so the node simply never joins the
# balancer and nothing says so. setgid keeps the deploy group on new files, so
# an operator can still read the view.
$SUDO mkdir -p "$NODE_SHARE_DIR"
$SUDO chown "$REDTUSK_WORKER_UID:$DGRP" "$NODE_SHARE_DIR"
$SUDO chmod 2770 "$NODE_SHARE_DIR"

# ── 8. host tuning (JVM + many microVMs) ───────────────────────────────────
log "applying host tuning (fd limits, vm.max_map_count)"
$SUDO tee /etc/sysctl.d/99-redtusk-node.conf >/dev/null <<EOF
# RedTusk warm-worker node: many concurrent microVMs + JVM heaps.
fs.file-max = 2097152
vm.max_map_count = 1048576
EOF
$SUDO sysctl -q --system >/dev/null || warn "sysctl reload reported an issue"
$SUDO tee /etc/security/limits.d/99-redtusk-node.conf >/dev/null <<EOF
$DEPLOY_USER soft nofile 1048576
$DEPLOY_USER hard nofile 1048576
EOF

# ── 9. FC kernel + rootfs (delegate to the existing script) ────────────────
if [ "$FC_ASSETS" -eq 1 ]; then
    if [ -n "$KERNEL_FROM" ]; then
        log "copying known-good vmlinux from $KERNEL_FROM"
        tmpk=$(mktemp); scp -q "$KERNEL_FROM" "$tmpk" || die "scp kernel from $KERNEL_FROM failed"
        $SUDO install -m 644 "$tmpk" "$REDTUSK_FC_DIR/vmlinux"; rm -f "$tmpk"
        # setup_firecracker_host.sh stages assets under its --state-dir; point it at ours
        # so the rootfs lands next to the copied kernel, and it validates the CPU pin.
    fi
    log "delegating kernel+rootfs to scripts/setup_firecracker_host.sh (state-dir=$REDTUSK_FC_DIR)"
    FC_ARGS=(--state-dir "$REDTUSK_FC_DIR" --firecracker-bin /usr/local/bin/firecracker)
    # Build a kernel here only if asked AND we didn't copy one in.
    [ "$WITH_KERNEL" -eq 1 ] && [ -z "$KERNEL_FROM" ] && FC_ARGS+=(--with-kernel)
    # Run as the deploy user under sg kvm (the FC script needs kvm access + docker).
    if ! run_as_deploy sg kvm -c "cd '$REPO_ROOT' && scripts/setup_firecracker_host.sh ${FC_ARGS[*]}"; then
        warn "setup_firecracker_host.sh did not complete — build the rootfs/kernel manually (see deploy/firecracker/README.md)."
    fi
    # The FC compose expects the rootfs named redtusk-rootfs.ext4; the FC script
    # produces rootfs-vsock.ext4. Symlink so BLASTBOX_FC_ROOTFS resolves.
    if [ -f "$REDTUSK_FC_DIR/rootfs-vsock.ext4" ] && [ ! -e "$REDTUSK_FC_DIR/redtusk-rootfs.ext4" ]; then
        $SUDO ln -s rootfs-vsock.ext4 "$REDTUSK_FC_DIR/redtusk-rootfs.ext4"
    fi
else
    log "skipping FC assets (--no-fc-assets) — run scripts/setup_firecracker_host.sh later"
fi

# ── 10. summary ────────────────────────────────────────────────────────────
# Say plainly when the FC tier CANNOT start. setup_firecracker_host.sh only warns
# about a missing kernel and returns 0, and the fresh-node command in the README
# passes neither --with-kernel nor --kernel-from -- so provisioning printed
# `done` on a node whose Firecracker dispatcher would refuse at startup.
fc_missing=""
for asset in firecracker vmlinux redtusk-rootfs.ext4; do
    [ -e "$REDTUSK_FC_DIR/$asset" ] || fc_missing="$fc_missing $asset"
done
if [ -n "$fc_missing" ]; then
    warn "Firecracker tier NOT ready — missing from $REDTUSK_FC_DIR:$fc_missing"
    warn "  kernel: re-run with --with-kernel (builds one) or --kernel-from <host>:/path/vmlinux"
    warn "  rootfs: scripts/build_images.sh writes redtusk-rootfs.ext4 into that directory"
    warn "  the cold and gVisor tiers do not need these and are unaffected"
fi

printf '\n\033[1;32m[prep-node] done.\033[0m\n'
cat <<EOF

Compose .env fragment for this node (deploy/docker/.env):
  KVM_GID=$KVM_GID
  REDTUSK_DATA_DIR=$REDTUSK_DATA_DIR
  REDTUSK_FC_DIR=$REDTUSK_FC_DIR
  BLASTBOX_NODE_SHARE_DIR=$NODE_SHARE_DIR

Node-autosizer env (add to EVERY dispatcher on this host):
  BLASTBOX_NODE_RESOURCE_MANAGEMENT=1
  BLASTBOX_NODE_BALANCING=1
  BLASTBOX_NODE_ENGINES=redtusk
  BLASTBOX_NODE_ENGINE_REDTUSK_RAM_MIB=2048
  BLASTBOX_NODE_SHARE_DIR=$NODE_SHARE_DIR
  BLASTBOX_DISPATCH_CONCURRENCY=<= (RAM*0.8/2GB and vCPU*2) — this node ~$(( $(free -m | awk '/^Mem:/{print $2}') * 8 / 10 / 2048 )) RAM-bound slots

Verify: scripts/prepare_node_ubuntu.sh --check
Notes:
  - Re-login (or use 'sg kvm') so the $DEPLOY_USER kvm-group membership is live.
  - FC assets at $REDTUSK_FC_DIR: $([ -f "$REDTUSK_FC_DIR/vmlinux" ] && echo 'vmlinux ✓' || echo 'vmlinux MISSING (--with-kernel or --kernel-from)') / $([ -e "$REDTUSK_FC_DIR/redtusk-rootfs.ext4" ] && echo 'rootfs ✓' || echo 'rootfs MISSING (run setup_firecracker_host.sh)')
EOF

if [ "$AWS_BURST" -eq 1 ]; then
cat <<EOF

AWS burst tier (this is the control-plane node):
  aws cli   : $(aws --version 2>/dev/null | head -1 || echo 'MISSING')
  aws creds : $(_aws_creds_status)
  1. Put your AWS credentials at ~/.aws/credentials (this script never touches them).
  2. Add this line to deploy/docker/.env -- the overlay mounts the directory and
     REQUIRES the variable, so 'docker compose up' aborts without it:
       AWS_CREDS_DIR=$(_aws_creds_home)/.aws
     (Put it in .env rather than exporting it: sudo strips an exported value, so
     --check would resolve a different directory than your 'docker compose up'.)
     The dispatcher runs as uid:gid $(_dispatcher_ids | tr ' ' :), and a normal ~/.aws is
     0700/0600 -- mounting it is not enough, that uid must READ it. (A custom
     REDTUSK_IMAGE running as another uid: pass it THROUGH sudo, which strips exports:
       sudo REDTUSK_WORKER_UID=<uid> REDTUSK_WORKER_GID=<gid> scripts/prepare_node_ubuntu.sh --check) 'aws creds' above says UNUSABLE when it cannot.
     Either give it a copy it owns (this script never writes credentials itself):
       sudo install -d -m 0500 -o $(_dispatcher_ids | cut -d' ' -f1) /etc/redtusk/aws
       sudo install -m 0400 -o $(_dispatcher_ids | cut -d' ' -f1) $(_aws_creds_home)/.aws/credentials /etc/redtusk/aws/
       (and the same for config, if you have one), then AWS_CREDS_DIR=/etc/redtusk/aws
     or grant it narrow ACLs on the existing files (the home directory itself need not
     be widened -- the overlay mounts .aws directly):
       sudo setfacl -m u:$(_dispatcher_ids | cut -d' ' -f1):x $(_aws_creds_home)/.aws
       sudo setfacl -m u:$(_dispatcher_ids | cut -d' ' -f1):r $(_aws_creds_home)/.aws/credentials   (and config)
     Use real files, not symlinks: the directory is mounted alone, link text unchanged.
  3. Deploy the burst dispatcher with the overlay:
       docker compose -f docker-compose.yml -f docker-compose.aws-burst.yml up -d dispatcher-aws-burst
  4. Set the AWS resource ids + tier in deploy/docker/.env (see the overlay header:
       BLASTBOX_AWS_TIER, BLASTBOX_AWS_REGION, and the EC2/Lambda ids for that tier).
  The AWS tiers fail CLOSED unless 'aws sts get-caller-identity' + a service probe pass,
  so a half-configured burst node stays on the local FC/gVisor tiers rather than erroring.
EOF
fi
