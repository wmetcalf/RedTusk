#!/usr/bin/env bash
# Bring a bare-metal host up to run RedTusk's Firecracker worker runtime
# (REDTUSK_WORKER_RUNTIME=firecracker). Idempotent — re-running is safe.
#
# What this does:
#   1. Preflight (kvm, sudo, docker, e2fsprogs).
#   2. Add the current user to the `kvm` group (must re-login after, or
#      launch the serve under `sg kvm`).
#   3. Locate the `firecracker` binary; refuse with a hint if missing.
#   4. Build the worker rootfs from Dockerfile.crac (`crac-vsock`), export,
#      mkfs.ext4, install the disk-output `init-vsock` as /init, and stage
#      it at REDTUSK_FC_ROOTFS.
#   5. Optionally (--with-kernel) fetch + patch + build a microVM kernel
#      with CONFIG_KSM=y and CONFIG_TRANSPARENT_HUGEPAGE=y and stage it at
#      REDTUSK_FC_KERNEL. This is opt-in because it's a multi-minute op
#      and most hosts already have a suitable kernel from a prior build.
#
# Compose-mode dispatcher CANNOT host FC (it has no /dev/kvm); after this
# script you run `redtusk serve` as a host process — see "Next steps" at
# the end.
#
# Usage:
#   scripts/setup_firecracker_host.sh [--with-kernel] [--force-rebuild]
#       [--state-dir /var/lib/redtusk/firecracker] [--kernel-version 6.18.28]
#       [--firecracker-bin /opt/kata/bin/firecracker]
set -euo pipefail

STATE_DIR=/var/lib/redtusk/firecracker
KERNEL_VERSION=6.18.28
FIRECRACKER_BIN_HINT=/opt/kata/bin/firecracker
WITH_KERNEL=0
FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --with-kernel)      WITH_KERNEL=1; shift ;;
        --force-rebuild)    FORCE=1; shift ;;
        --state-dir)        STATE_DIR=$2; shift 2 ;;
        --kernel-version)   KERNEL_VERSION=$2; shift 2 ;;
        --firecracker-bin)  FIRECRACKER_BIN_HINT=$2; shift 2 ;;
        -h|--help)          sed -n '/^#/,/^$/p' "$0" | sed 's/^# \?//' ; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
log() { printf '\033[1;36m[setup-fc]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[setup-fc] WARN:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[setup-fc] FATAL:\033[0m %s\n' "$*" >&2; exit 1; }

#───────────────────────── 1. preflight ─────────────────────────
log "preflight checks"
[ -e /dev/kvm ] || die "/dev/kvm not present — host needs KVM (bare metal or AWS c8i/m8i/r8i with nested virt)"
command -v sudo >/dev/null || die "sudo required"
command -v docker >/dev/null || die "docker required for the rootfs build (Dockerfile.crac)"
command -v mkfs.ext4 >/dev/null || { log "installing e2fsprogs"; sudo apt-get install -y -q e2fsprogs || sudo dnf install -y e2fsprogs; }
command -v debugfs >/dev/null || die "debugfs missing from e2fsprogs install — host reads the output disk with it"
command -v python3 >/dev/null || die "python3 required for the CRaC CPU-feature probe (scripts/fc_cpu_probe.py)"

#───────────────────── 2. kvm group membership ─────────────────────
if id -nG "$USER" | tr ' ' '\n' | grep -qx kvm; then
    log "user $USER is in kvm group"
else
    log "adding $USER to kvm group (re-login or use 'sg kvm -c ...' to take effect)"
    sudo usermod -aG kvm "$USER"
fi

#─────────────────── 3. firecracker binary ───────────────────────
FC_BIN=""
for cand in "$FIRECRACKER_BIN_HINT" /usr/local/bin/firecracker /usr/bin/firecracker; do
    if [ -x "$cand" ]; then FC_BIN=$cand; break; fi
    if [ -f "$cand" ] && [ ! -x "$cand" ]; then
        log "found $cand but not executable — chmod +x"
        sudo chmod 755 "$cand"
        FC_BIN=$cand; break
    fi
done
[ -n "$FC_BIN" ] || die "firecracker binary not found. Install it: https://github.com/firecracker-microvm/firecracker/releases (then re-run, or pass --firecracker-bin /path)"
log "firecracker: $FC_BIN ($($FC_BIN --version 2>&1 | head -1))"

#───────────────────── 4. state dir + rootfs ─────────────────────
sudo mkdir -p "$STATE_DIR"
ROOTFS=$STATE_DIR/rootfs-vsock.ext4

# CRaC CPU-feature pin baked into the warp checkpoint. Defaults to the known-good
# value so an unparameterized build is unchanged; the auto-bake step (5.5) probes
# the guest and rebuilds pinned to the value the guest actually needs if they have
# diverged. Override the STARTING point with REDTUSK_FC_CPU_FEATURES.
FC_CPU_FEATURES=${REDTUSK_FC_CPU_FEATURES:-0x102100055bbd7,0x1c8}

build_and_stage_rootfs() {  # $1 = -XX:CPUFeatures value to bake into the checkpoint
    local cpuf=$1
    log "building worker rootfs (Dockerfile.crac, CPUFeatures=$cpuf) — ~3 min cold"
    cd "$REPO_ROOT"
    sudo docker build -f deploy/docker/Dockerfile.crac \
        --build-arg "FC_CPU_FEATURES=$cpuf" \
        --no-cache-filter build,runtime \
        -t redtusk-worker:crac-vsock . 2>&1 | tail -8

    local BUILD CID
    BUILD=$(mktemp -d)
    log "exporting image → ext4 rootfs"
    CID=$(sudo docker create redtusk-worker:crac-vsock)
    sudo docker export "$CID" > "$BUILD/rootfs.tar"
    sudo docker rm "$CID" >/dev/null

    truncate -s 2G "$BUILD/rootfs-vsock.ext4"
    mkfs.ext4 -q -F "$BUILD/rootfs-vsock.ext4"
    sudo mkdir -p "$BUILD/mnt"
    sudo mount -o loop "$BUILD/rootfs-vsock.ext4" "$BUILD/mnt"
    sudo tar -xf "$BUILD/rootfs.tar" -C "$BUILD/mnt"
    sudo install -m 755 deploy/firecracker/init-vsock "$BUILD/mnt/init"
    sudo grep -q "REDTUSK_VSOCK_DISK_OUTPUT\|/dev/vdb" "$BUILD/mnt/init" \
        || warn "installed init-vsock doesn't mention the output disk — wrong file?"
    sudo sync; sudo umount "$BUILD/mnt"
    sudo install -m 644 "$BUILD/rootfs-vsock.ext4" "$ROOTFS"
    sudo rm -rf "$BUILD"
    log "installed rootfs: $ROOTFS ($(du -h "$ROOTFS" | cut -f1))"
}

BUILT=0
if [ -f "$ROOTFS" ] && [ "$FORCE" -eq 0 ]; then
    log "rootfs already at $ROOTFS — skipping (use --force-rebuild to remake)"
else
    build_and_stage_rootfs "$FC_CPU_FEATURES"
    BUILT=1
fi

#───────────────────── 5. optional kernel build ─────────────────────
KERNEL=$STATE_DIR/vmlinux
if [ "$WITH_KERNEL" -eq 1 ] && { [ ! -f "$KERNEL" ] || [ "$FORCE" -eq 1 ]; }; then
    log "building microVM kernel $KERNEL_VERSION with KSM + THP (this takes ~3-5 min)"
    KBUILD=$(mktemp -d)
    cd "$KBUILD"
    KMAJOR=$(echo "$KERNEL_VERSION" | cut -d. -f1)
    curl -fsSL -O "https://cdn.kernel.org/pub/linux/kernel/v${KMAJOR}.x/linux-${KERNEL_VERSION}.tar.xz"
    # SUPPLY CHAIN: verify the kernel tarball before extracting. kernel.org
    # publishes a sha256sums.asc per release directory; we fetch the matching
    # sha256sums.asc and check the line for our tarball. If the checksum file
    # can't be fetched, fall back to a pinned EXPECTED_KERNEL_SHA256 env var.
    # Fails closed — no verified checksum, no extraction.
    if curl -fsSL -o /tmp/kernel-sha256sums.asc \
        "https://cdn.kernel.org/pub/linux/kernel/v${KMAJOR}.x/sha256sums.asc" \
        && grep -q "linux-${KERNEL_VERSION}.tar.xz" /tmp/kernel-sha256sums.asc; then
        grep " linux-${KERNEL_VERSION}.tar.xz\$" /tmp/kernel-sha256sums.asc \
            | sha256sum -c - \
            || die "kernel tarball checksum verification FAILED"
    else
        # TODO: fill in the real sha256 of linux-${KERNEL_VERSION}.tar.xz, or
        # export EXPECTED_KERNEL_SHA256 before running. Empty value fails closed.
        : "${EXPECTED_KERNEL_SHA256:?kernel checksum unavailable and EXPECTED_KERNEL_SHA256 unset — refusing to extract an unverified kernel tarball}"
        echo "${EXPECTED_KERNEL_SHA256}  linux-${KERNEL_VERSION}.tar.xz" \
            | sha256sum -c - \
            || die "kernel tarball checksum verification FAILED"
    fi
    tar -xf "linux-${KERNEL_VERSION}.tar.xz"
    cd "linux-${KERNEL_VERSION}"
    # Start from a minimal x86_64 microvm-friendly config. Firecracker's
    # documented seed is "make microvm_defconfig" on recent kernels.
    if make help 2>&1 | grep -q microvm_defconfig; then
        make microvm_defconfig
    else
        make defconfig
        # Strip out the kernel cruft we don't need
        scripts/config --disable CONFIG_MODULES --disable CONFIG_BLK_DEV_INITRD \
                       --enable  CONFIG_VIRTIO_BLK --enable CONFIG_VIRTIO_PCI \
                       --enable  CONFIG_VIRTIO_VSOCKETS --enable CONFIG_VSOCKETS \
                       --enable  CONFIG_VMW_VSOCK_VIRTIO_TRANSPORT
    fi
    # Required for Azul Zulu warp's madvise calls on restore.
    scripts/config --enable CONFIG_KSM --enable CONFIG_TRANSPARENT_HUGEPAGE \
                   --enable CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS
    make olddefconfig
    make -j"$(nproc)" vmlinux
    sudo install -m 644 vmlinux "$KERNEL"
    cd /; rm -rf "$KBUILD"
    log "installed kernel: $KERNEL"
elif [ -f "$KERNEL" ]; then
    log "kernel already at $KERNEL — skipping (use --with-kernel --force-rebuild to remake)"
else
    warn "no kernel at $KERNEL — re-run with --with-kernel, or supply one yourself"
fi

#──────────────── 5.5 CRaC CPU-feature auto-bake ────────────────
# Boot the freshly-built rootfs once and confirm the warp checkpoint actually
# restores in THIS guest. If the guest's feature set has diverged from the pin,
# the probe reports the value the guest needs and we rebuild pinned to it — so a
# host/guest CPU change becomes a self-correcting build instead of a silent
# "pool never warms". See the blastbox fc-cpu-feature-automation spec.
probe_guest() {  # prints "STATUS [value]" on stdout (COMPATIBLE|MISMATCH <v>|INCONCLUSIVE)
    sudo python3 "$REPO_ROOT/scripts/fc_cpu_probe.py" \
        --fc-bin "$FC_BIN" --kernel "$KERNEL" --rootfs "$ROOTFS"
}

if [ "$BUILT" -eq 1 ] && [ -f "$KERNEL" ]; then
    log "auto-bake: probing the guest to confirm the checkpoint restores"
    set +e; PROBE=$(probe_guest); set -e
    case "${PROBE%% *}" in
        COMPATIBLE)
            log "auto-bake: checkpoint restores in the guest (CPUFeatures=$FC_CPU_FEATURES) ✓" ;;
        MISMATCH)
            NEW=${PROBE#MISMATCH }
            warn "auto-bake: guest needs -XX:CPUFeatures=$NEW (built with $FC_CPU_FEATURES) — rebuilding pinned"
            build_and_stage_rootfs "$NEW"
            set +e; PROBE2=$(probe_guest); set -e
            [ "${PROBE2%% *}" = "COMPATIBLE" ] \
                || die "auto-bake: rebuilt with $NEW but the probe still reports: $PROBE2"
            log "auto-bake: CPUFeatures=$NEW baked — checkpoint now restores ✓"
            log "auto-bake: set REDTUSK_FC_CPU_FEATURES=$NEW to start from this value next time" ;;
        *)
            die "auto-bake: probe could not confirm the checkpoint restores in the guest ($PROBE). Boot it manually — 'firecracker --no-api --config-file <cfg with console=ttyS0>' — and read the serial console." ;;
    esac
elif [ "$BUILT" -eq 1 ]; then
    warn "auto-bake: skipped — no kernel at $KERNEL yet (re-run with --with-kernel to enable the guest CPU-feature check)"
fi

#───────────────────────── 6. next steps ─────────────────────────
KERNEL_NOTE=""
[ -f "$KERNEL" ] || KERNEL_NOTE="  (missing — re-run with --with-kernel)"
WARM=$(( $(nproc) > 4 ? $(nproc) - 4 : $(nproc) ))
printf '\n\033[1;32m[setup-fc] done.\033[0m  Assets:\n'
cat <<EOF
  REDTUSK_FC_BIN     = $FC_BIN
  REDTUSK_FC_KERNEL  = $KERNEL${KERNEL_NOTE}
  REDTUSK_FC_ROOTFS  = $ROOTFS

Run the FC dispatcher on this host (NOT in compose — needs /dev/kvm):

  export REDTUSK_WORKER_RUNTIME=firecracker
  export REDTUSK_FC_BIN=$FC_BIN
  export REDTUSK_FC_KERNEL=$KERNEL
  export REDTUSK_FC_ROOTFS=$ROOTFS
  # don't oversubscribe: (warm + burst) × fc_vcpu_count ≤ cores ($(nproc) here)
  export REDTUSK_POOL_WARM_SIZE=$WARM
  export REDTUSK_POOL_BURST_SIZE=0
  # REDTUSK_SCRATCH_ROOT must NOT contain whitespace (debugfs request parser)
  export REDTUSK_SCRATCH_ROOT=/var/lib/redtusk/scratch
  sg kvm -c 'redtusk serve --host 0.0.0.0 --port 8000'
EOF
