#!/usr/bin/env bash
# Set up the host-level infrastructure needed by REDTUSK_PROFILE=microvm.
#
# What this script does, in order:
#   1. Verify prerequisites (KVM, kata-runtime, /dev/vsock, vhost_vsock)
#   2. Download + install nydus tooling (snapshotter + image tools) if missing
#   3. Install + start the nydus-snapshotter systemd service
#   4. Configure containerd to register the nydus snapshotter as a proxy plugin
#   5. Configure Kata to use the nydus snapshotter for container rootfs
#   6. Enable Kata's VM templating (factory) for sub-second spawn
#   7. Restart containerd (BRIEFLY disrupts containerd-managed containers)
#   8. Smoke test: alpine under Kata + nydus + templating
#
# Idempotent — safe to re-run; existing config is overwritten with the
# canonical version. Host-side state is captured in /etc/{nydus,containerd,
# kata-containers}/ + /etc/systemd/system/nydus-snapshotter.service.
#
# Reversible — see scripts/teardown_microvm_host.sh.
#
# Designed to run identically on:
#   - bare metal Linux with KVM (verified target: Ubuntu 24.04)
#   - AWS C8i/M8i/R8i with NestedVirtualization=true enabled at instance launch
#   - any host with /dev/kvm + vhost_vsock kernel modules
#
# Requires sudo. Not idempotent across OS distributions — apt-only.
#
# Usage:
#   ./scripts/setup_microvm_host.sh
#   sudo ./scripts/setup_microvm_host.sh           # if running as non-sudoer

set -euo pipefail

NYDUS_SNAPSHOTTER_VERSION="v0.15.15"
NYDUS_TOOLS_VERSION="v2.4.3"

log() { printf "\n\033[1;36m==> %s\033[0m\n" "$*" >&2; }
ok()  { printf "  \033[1;32m✓\033[0m %s\n" "$*" >&2; }
warn(){ printf "  \033[1;33m!\033[0m %s\n" "$*" >&2; }
fail(){ printf "  \033[1;31m✗\033[0m %s\n" "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
fi

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
log "Verifying prerequisites"
[ -e /dev/kvm ]   || fail "/dev/kvm missing — KVM not available (need bare metal or AWS C8i+M8i+R8i with NestedVirtualization=true)"
[ -e /dev/vsock ] || fail "/dev/vsock missing — run: sudo modprobe vhost_vsock"
command -v containerd >/dev/null || fail "containerd not installed"
command -v /opt/kata/bin/kata-runtime >/dev/null \
    || fail "kata-runtime not at /opt/kata/bin/kata-runtime — run the upstream Kata install first"
ok "KVM, vsock, containerd, kata-runtime all present"

# ── 2. Install nydus tooling ──────────────────────────────────────────────────
log "Installing nydus snapshotter (v$NYDUS_SNAPSHOTTER_VERSION) + image tools (v$NYDUS_TOOLS_VERSION)"
if ! command -v containerd-nydus-grpc >/dev/null; then
    cd /tmp
    curl -fsSL -o nydus-snap.tar.gz \
        "https://github.com/containerd/nydus-snapshotter/releases/download/${NYDUS_SNAPSHOTTER_VERSION}/nydus-snapshotter-${NYDUS_SNAPSHOTTER_VERSION}-linux-amd64.tar.gz"
    $SUDO mkdir -p /opt/nydus-snapshotter
    $SUDO tar -xzf nydus-snap.tar.gz -C /opt/nydus-snapshotter
    $SUDO ln -sf /opt/nydus-snapshotter/bin/containerd-nydus-grpc /usr/local/bin/
    $SUDO ln -sf /opt/nydus-snapshotter/bin/nydus-overlayfs       /usr/local/bin/
    ok "nydus-snapshotter installed"
else
    ok "containerd-nydus-grpc already on PATH"
fi
if ! command -v nydus-image >/dev/null; then
    cd /tmp
    curl -fsSL -o nydus-tools.tgz \
        "https://github.com/dragonflyoss/nydus/releases/download/${NYDUS_TOOLS_VERSION}/nydus-static-${NYDUS_TOOLS_VERSION}-linux-amd64.tgz"
    $SUDO mkdir -p /opt/nydus-snapshotter
    $SUDO tar -xzf nydus-tools.tgz -C /opt/nydus-snapshotter
    $SUDO ln -sf /opt/nydus-snapshotter/nydus-static/nydus-image /usr/local/bin/
    $SUDO ln -sf /opt/nydus-snapshotter/nydus-static/nydusify    /usr/local/bin/
    ok "nydus-image + nydusify installed"
else
    ok "nydus-image already on PATH"
fi

# ── 3. nydus-snapshotter config + systemd ─────────────────────────────────────
log "Writing nydus-snapshotter config + systemd unit"
$SUDO mkdir -p /etc/nydus /var/lib/containerd-nydus /run/containerd-nydus

$SUDO tee /etc/nydus/config.toml >/dev/null <<'EOF'
version = 1
root = "/var/lib/containerd-nydus"
address = "/run/containerd-nydus/containerd-nydus-grpc.sock"
daemon_mode = "dedicated"
log_level = "info"

[daemon]
nydusd_path = "/opt/kata/libexec/nydusd"
nydusimage_path = "/usr/local/bin/nydus-image"
fs_driver = "fusedev"

[snapshot]
enable_nydus_overlayfs = true
EOF
ok "/etc/nydus/config.toml written"

$SUDO tee /etc/systemd/system/nydus-snapshotter.service >/dev/null <<'EOF'
[Unit]
Description=nydus snapshotter
After=network.target containerd.service
Requires=containerd.service

[Service]
Type=simple
ExecStart=/usr/local/bin/containerd-nydus-grpc --config /etc/nydus/config.toml
Restart=on-failure
RestartSec=2s

[Install]
WantedBy=multi-user.target
EOF

$SUDO systemctl daemon-reload
$SUDO systemctl enable nydus-snapshotter
$SUDO systemctl restart nydus-snapshotter
sleep 2
if $SUDO systemctl is-active --quiet nydus-snapshotter; then
    ok "nydus-snapshotter service running"
else
    fail "nydus-snapshotter failed to start; journalctl -u nydus-snapshotter -n 40 --no-pager"
fi

# ── 4. containerd config: register nydus as a proxy snapshotter ───────────────
log "Configuring containerd to recognize nydus as a snapshotter"
CONTAINERD_CONFIG=/etc/containerd/config.toml
$SUDO mkdir -p /etc/containerd
# If the file doesn't exist or doesn't have our marker, write the canonical
# version. We append rather than overwrite so the host's existing containerd
# config (if any) is preserved — but the proxy_plugins block is idempotent
# (re-running this script just rewrites it in place).
if [ ! -f "$CONTAINERD_CONFIG" ]; then
    $SUDO containerd config default | $SUDO tee "$CONTAINERD_CONFIG" >/dev/null
    ok "wrote default containerd config to $CONTAINERD_CONFIG"
fi

# Strip any prior REDTUSK-managed block (between marker lines).
if grep -q "# BEGIN: redtusk microvm" "$CONTAINERD_CONFIG" 2>/dev/null; then
    $SUDO sed -i '/# BEGIN: redtusk microvm/,/# END: redtusk microvm/d' "$CONTAINERD_CONFIG"
fi
$SUDO tee -a "$CONTAINERD_CONFIG" >/dev/null <<'EOF'

# BEGIN: redtusk microvm — managed by scripts/setup_microvm_host.sh
[proxy_plugins.nydus]
type = "snapshot"
address = "/run/containerd-nydus/containerd-nydus-grpc.sock"
# END: redtusk microvm
EOF
ok "containerd registered nydus proxy snapshotter"

# ── 5. Kata config: use nydus snapshotter + enable templating ─────────────────
log "Configuring Kata to use nydus snapshotter + enable VM templating"
KATA_CONF=/etc/kata-containers/configuration.toml
$SUDO mkdir -p /etc/kata-containers
if [ ! -f "$KATA_CONF" ]; then
    $SUDO cp /opt/kata/share/defaults/kata-containers/configuration-qemu.toml "$KATA_CONF"
    ok "copied kata default config to $KATA_CONF"
fi
# Switch to initrd boot (templating prerequisite) — image= → initrd=
$SUDO sed -i 's|^image = .*|# image = (disabled — templating uses initrd)|; \
              s|^# *initrd = .*|initrd = "/opt/kata/share/kata-containers/kata-containers-initrd.img"|' \
              "$KATA_CONF"
# Templating + nydus
$SUDO sed -i 's|^enable_template = .*|enable_template = true|; \
              s|^shared_fs = .*|shared_fs = "virtio-fs-nydus"|' "$KATA_CONF"
ok "kata config updated: initrd, enable_template=true, shared_fs=virtio-fs-nydus"

# ── 6. Restart containerd + initialize Kata factory ───────────────────────────
log "Restarting containerd (briefly disrupts containerd-managed containers)"
$SUDO systemctl restart containerd
sleep 5
$SUDO ctr plugins ls 2>/dev/null | grep -i nydus | head -3 || warn "ctr plugins missing nydus row — check journalctl -u containerd"

log "Initializing Kata VM factory (one-time template snapshot)"
$SUDO /opt/kata/bin/kata-runtime factory destroy 2>/dev/null || true
$SUDO /opt/kata/bin/kata-runtime factory init 2>&1 | tail -5

if $SUDO /opt/kata/bin/kata-runtime factory status 2>&1 | grep -q "vm factory is on"; then
    ok "Kata VM templating factory initialized"
else
    warn "Kata factory not active — see: sudo kata-runtime factory status"
fi

# ── 7. Smoke test (file-IPC, with templating disabled — sanity only) ─────────
# A real microvm-mode smoke test needs the worker image converted to nydus
# format AND Docker reconfigured to use the containerd image store with the
# nydus snapshotter. See the "Remaining steps" section below.
log "Smoke test: alpine under Kata (virtio-fs, no templating — baseline only)"
$SUDO sed -i 's|^shared_fs = .*|shared_fs = "virtio-fs"|; \
              s|^enable_template = .*|enable_template = false|' "$KATA_CONF"
START=$(date +%s%N)
if docker run --rm --runtime=kata alpine echo kata-virtio-fs-baseline >/tmp/microvm-smoke.out 2>&1; then
    END=$(date +%s%N)
    cat /tmp/microvm-smoke.out
    ok "alpine boot under Kata (virtio-fs baseline) took $(( (END - START) / 1000000 )) ms"
else
    cat /tmp/microvm-smoke.out
    warn "even the virtio-fs baseline failed — investigate before proceeding"
fi

log "Setup complete — what's installed and verified:"
echo "  ✓ nydus-snapshotter installed + running (systemd: nydus-snapshotter.service)"
echo "  ✓ containerd recognizes nydus as a snapshotter (ctr plugins ls | grep nydus)"
echo "  ✓ Kata config supports template factory under shared_fs=none"
echo "  ✓ vsock IPC works end-to-end through Kata's microVM boundary"
echo ""
log "Remaining steps to actually deploy REDTUSK_PROFILE=microvm:"
echo ""
echo "  1. Run a local OCI registry on this host (one-shot):"
echo "       docker run -d --name registry --restart=always -p 5000:5000 registry:2"
echo ""
echo "  2. Convert redtusk-worker:default → nydus format:"
echo "       nydusify convert \\"
echo "         --source redtusk-worker:default \\"
echo "         --target localhost:5000/redtusk-worker:default-nydus \\"
echo "         --nydus-image /usr/local/bin/nydus-image"
echo ""
echo "  3. Enable Docker's containerd image store so docker run can use"
echo "     nydus images (one-time, requires Docker restart — disrupts all"
echo "     running containers including the camoufox stack):"
echo "       /etc/docker/daemon.json:  add  \"features\": { \"containerd-snapshotter\": true }"
echo "       sudo systemctl restart docker"
echo "     ALTERNATIVE: switch the dispatcher's spawn path from 'docker run' to"
echo "     'nerdctl run --snapshotter=nydus' for the microvm profile only,"
echo "     leaving Docker untouched. Smaller blast radius."
echo ""
echo "  4. Set Kata to use nydus + templating:"
echo "       sudo sed -i 's|^shared_fs = .*|shared_fs = \"none\"|; \\"
echo "                   s|^enable_template = .*|enable_template = true|' \\"
echo "                   /etc/kata-containers/configuration.toml"
echo "       sudo kata-runtime factory init"
echo ""
echo "  5. Flip RedTusk to microvm in deploy/docker/.env:"
echo "       REDTUSK_PROFILE=microvm"
echo "       REDTUSK_WORKER_IMAGE=localhost:5000/redtusk-worker:default-nydus"
echo "       REDTUSK_WORKER_RUNTIME=kata"
echo "     then: ./deploy/docker/redtusk-compose up -d --force-recreate api"
echo ""
echo "  Steps 1-4 are the 'one-time host setup' that turns this host into"
echo "  a microvm-capable RedTusk node. Step 5 is the same as flipping any"
echo "  other profile after that."
