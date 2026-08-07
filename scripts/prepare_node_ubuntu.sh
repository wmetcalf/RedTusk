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
# at ~/.aws/credentials on the burst node yourself, and the burst overlay mounts them
# read-only. The AWS tiers fail closed unless `aws sts get-caller-identity` passes.
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
    printf '  aws creds   : %s\n' "$(have aws && aws sts get-caller-identity >/dev/null 2>&1 && echo 'valid (sts ok)' || echo 'absent/invalid — place ~/.aws/credentials')"
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
        $SUDO apt-get update -q && $SUDO apt-get install -y -q runsc
        # register the runsc docker runtime (for the gVisor tier if used directly)
        have runsc && $SUDO runsc install >/dev/null 2>&1 && $SUDO systemctl restart docker || warn "runsc docker-runtime registration skipped"
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
    if [ ! -r "${AWS_CREDS_HOME:-/home/$DEPLOY_USER}/.aws/credentials" ] && [ -z "${AWS_ACCESS_KEY_ID:-}" ]; then
        warn "no AWS credentials yet — place ~/.aws/credentials on this node, then re-run --check"
    elif aws sts get-caller-identity >/dev/null 2>&1; then
        log "aws entitlement OK (sts get-caller-identity passed)"
    else
        warn "AWS credentials present but 'aws sts get-caller-identity' FAILED — the burst tier will fail closed"
    fi
fi

# ── 7. standard dirs (owned by the deploy user/group) ──────────────────────
log "creating standard dirs"
DGRP=$(id -gn "$DEPLOY_USER")
for d in "$REDTUSK_DATA_DIR/jobs" "$REDTUSK_DATA_DIR/scratch" "$REDTUSK_FC_DIR"; do
    $SUDO mkdir -p "$d"; $SUDO chown "$DEPLOY_USER:$DGRP" "$d"
done
# node-autosizer share: single-trust-domain surface written only by dispatchers on
# THIS host; bind-mounted into each engine stack. Group-writable so co-located
# dispatchers (same deploy group) all publish/read.
$SUDO mkdir -p "$NODE_SHARE_DIR"; $SUDO chown "$DEPLOY_USER:$DGRP" "$NODE_SHARE_DIR"; $SUDO chmod 2770 "$NODE_SHARE_DIR"

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
    if ! $SUDO -u "$DEPLOY_USER" sg kvm -c "cd '$REPO_ROOT' && scripts/setup_firecracker_host.sh ${FC_ARGS[*]}"; then
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
  aws creds : $(have aws && aws sts get-caller-identity >/dev/null 2>&1 && echo 'valid (sts ok)' || echo 'place ~/.aws/credentials, then re-run --check')
  1. Put your AWS credentials at ~/.aws/credentials (this script never touches them).
  2. Deploy the burst dispatcher with the overlay:
       docker compose -f docker-compose.yml -f docker-compose.aws-burst.yml up -d dispatcher-aws-burst
  3. Set the AWS resource ids + tier in deploy/docker/.env (see the overlay header:
       BLASTBOX_AWS_TIER, BLASTBOX_AWS_REGION, and the EC2/Lambda ids for that tier).
  The AWS tiers fail CLOSED unless 'aws sts get-caller-identity' + a service probe pass,
  so a half-configured burst node stays on the local FC/gVisor tiers rather than erroring.
EOF
fi
