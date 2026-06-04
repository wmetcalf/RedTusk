#!/usr/bin/env bash
# One-shot Firecracker microVM job runner.
#
# Usage: fc-run.sh <input-file> <output-metadata-path> [<slot-id>]
#
# Boots a fresh Firecracker microVM with the redtusk worker CRaC-restored
# inside, hands it the input file via a per-slot virtio-blk scratch device,
# waits for the worker to finish, kills the VM, copies metadata.json out.
#
# Env-vars (optional):
#   FC_WORK_DIR       — base directory holding rootfs.ext4, vmlinux, etc.   (default /tmp/fc-work)
#   FC_BIN            — Firecracker binary                                   (default /opt/kata/bin/firecracker)
#   FC_TIMEOUT        — kill the VM after this many seconds                  (default 120)
#   FC_VCPU_COUNT     — vCPUs                                                (default 2)
#   FC_MEM_MIB        — guest RAM in MiB                                     (default 1024)
#   FC_SCRATCH_MIB    — per-slot scratch ext4 size in MiB                    (default 32)
#
# Exits non-zero on any failure (timeout, missing metadata, etc).

set -euo pipefail

INPUT=${1:?"usage: fc-run.sh <input-file> <output-metadata-path> [slot-id]"}
OUT_META=${2:?"usage: fc-run.sh <input-file> <output-metadata-path> [slot-id]"}
SLOT_ID=${3:-fc-$$-$(date +%N)}

WORK=${FC_WORK_DIR:-/tmp/fc-work}
FC=${FC_BIN:-/opt/kata/bin/firecracker}
TIMEOUT=${FC_TIMEOUT:-120}
VCPU=${FC_VCPU_COUNT:-1}  # MUST be 1 - vcpu>1 corrupts the virtio-vsock stream under load
MEM=${FC_MEM_MIB:-1024}
SCRATCH=${FC_SCRATCH_MIB:-32}

[ -f "$WORK/rootfs.ext4" ] || { echo "fc-run: $WORK/rootfs.ext4 not found — build it first per deploy/firecracker/README.md" >&2; exit 2; }
[ -f "$WORK/vmlinux" ]    || { echo "fc-run: $WORK/vmlinux not found" >&2; exit 2; }
[ -f "$INPUT" ]           || { echo "fc-run: input file '$INPUT' not found" >&2; exit 2; }

SLOT_DIR="$WORK/slot-$SLOT_ID"
SCRATCH_EXT4="$SLOT_DIR.scratch.ext4"
CONFIG="$SLOT_DIR.config.json"
LOG="$SLOT_DIR.log"

cleanup() {
    rc=$?
    sudo umount "$SLOT_DIR.mnt" 2>/dev/null || true
    sudo rmdir "$SLOT_DIR.mnt" 2>/dev/null || true
    sudo rm -f "$SCRATCH_EXT4" "$CONFIG" "$LOG"
    exit $rc
}
trap cleanup EXIT

# Shared read-only rootfs: every slot mounts the same file ro, no per-slot
# copy needed. Saves ~2s of reflink/copy I/O per job and lets concurrent FCs
# share the page cache. The init script remounts / read-only inside the VM.
ROOTFS="$WORK/rootfs.ext4"

# Per-slot scratch ext4 (job + input go in; metadata comes out)
sudo truncate -s ${SCRATCH}M "$SCRATCH_EXT4"
sudo mkfs.ext4 -q -F "$SCRATCH_EXT4"
sudo mkdir -p "$SLOT_DIR.mnt"
sudo mount -o loop "$SCRATCH_EXT4" "$SLOT_DIR.mnt"
sudo mkdir -p "$SLOT_DIR.mnt/in" "$SLOT_DIR.mnt/out" "$SLOT_DIR.mnt/control"

BASE=$(basename "$INPUT" | tr -c 'a-zA-Z0-9._-' '_')
sudo cp "$INPUT" "$SLOT_DIR.mnt/in/$BASE"
SHA=$(sha256sum "$SLOT_DIR.mnt/in/$BASE" | awk '{print $1}')

sudo tee "$SLOT_DIR.mnt/control/job.json" >/dev/null <<EOF
{
  "input_path": "/in/$BASE",
  "output_dir": "/out",
  "sha256": "$SHA",
  "filename_hint": "$BASE",
  "limits": {"max_recursion_depth": 5, "max_embedded_entries": 100, "max_extracted_bytes": 104857600, "ocr_timeout_s": 30},
  "enable_qr": true, "enable_ocr": true, "enable_thumbnails": false,
  "ocr_lang": "eng", "ocr_psm": 3,
  "sandbox_profile": "default", "sandbox_runtime": "firecracker",
  "appcds": true, "ksm": true, "crac": true,
  "redtusk_version": "fc-cli",
  "zxing_path": "/usr/local/bin/ZXingReader", "tesseract_path": "tesseract",
  "ocr_max_image_dim": 2000, "ocr_skip_blank": true
}
EOF
sudo touch "$SLOT_DIR.mnt/control/control.go"
sudo chown -R 10001:10001 "$SLOT_DIR.mnt"
sudo umount "$SLOT_DIR.mnt"

sudo tee "$CONFIG" >/dev/null <<EOF
{
  "boot-source": {
    "kernel_image_path": "$WORK/vmlinux",
    "boot_args": "console=ttyS0 reboot=k panic=1 pci=off init=/init ro"
  },
  "drives": [
    {"drive_id": "rootfs",  "path_on_host": "$ROOTFS",        "is_root_device": true,  "is_read_only": true},
    {"drive_id": "scratch", "path_on_host": "$SCRATCH_EXT4", "is_root_device": false, "is_read_only": false}
  ],
  "machine-config": {"vcpu_count": $VCPU, "mem_size_mib": $MEM, "smt": false}
}
EOF

# Boot FC. We poll its stdout for "Wrote metadata.json" — the worker's signal
# that processing is done. The init script then syncs and shuts down.
sudo $FC --no-api --config-file "$CONFIG" > "$LOG" 2>&1 &
FC_PID=$!

# Watch for the init script's "SCRATCH-FLUSHED" sentinel, which is printed
# AFTER the init has sync'd + unmounted the scratch ext4 — at that point
# writes are guaranteed durable on the block device and we can safely
# SIGKILL FC for the fastest possible teardown. Watching for the worker's
# "Wrote metadata.json" instead races the kernel's writeback and corrupts
# results.
DEADLINE=$(( $(date +%s) + TIMEOUT ))
DONE=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    # NOTE on the sentinel race:
    #   The init script does: worker exit → sync → umount /scratch → sync
    #     → echo SCRATCH-FLUSHED → poweroff -f
    # We must NOT kill FC the moment we see the sentinel — FC has a few ms
    # of host-side work left (fsync the backing file, release fd, etc).
    # SIGKILLing here races that and corrupts the scratch ext4 on the host
    # side under concurrency. We always wait for FC to exit naturally
    # (poweroff -f makes it exit in ~20 ms after the sentinel).
    if ! kill -0 $FC_PID 2>/dev/null; then
        DONE=1
        break
    fi
    sleep 0.05
done

if [ "$DONE" -eq 0 ]; then
    # Hard timeout — fall back to SIGKILL.
    sudo kill -9 $FC_PID 2>/dev/null || true
fi
wait $FC_PID 2>/dev/null || true

if [ "$DONE" -eq 0 ]; then
    echo "fc-run: timeout after ${TIMEOUT}s, no 'Wrote metadata.json' in log" >&2
    tail -20 "$LOG" >&2
    exit 3
fi

# Mount scratch and extract metadata.json
sudo mount -o loop "$SCRATCH_EXT4" "$SLOT_DIR.mnt"
if [ ! -f "$SLOT_DIR.mnt/out/metadata.json" ]; then
    echo "fc-run: worker reported done but metadata.json missing in scratch" >&2
    sudo ls -la "$SLOT_DIR.mnt/out/" >&2
    exit 4
fi
sudo cp "$SLOT_DIR.mnt/out/metadata.json" "$OUT_META"
sudo chown $(id -u):$(id -g) "$OUT_META" 2>/dev/null || true
sudo umount "$SLOT_DIR.mnt"
echo "fc-run: ok, metadata at $OUT_META"
