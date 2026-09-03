#!/usr/bin/env bash
# Turn the stamped warm-tier IMAGES into the rootfs artifacts the gVisor and
# Firecracker tiers actually boot.
#
# Those tiers do not run a container image: gVisor runs an exported directory
# tree and Firecracker boots an ext4 file. Both are produced FROM the images
# `scripts/build_images.sh` stamped, so the provenance carries through -- which
# is the whole point. Rebuilding them any other way (for example letting
# build-rootfs.sh build its own image from a Dockerfile default) produces an
# UNSTAMPED artifact on an unrelated base, which is the gap this closes.
#
# Usage:  scripts/export_warm_rootfs.sh <tag>
# Env:    REDTUSK_GVISOR_DIR (default /var/lib/redtusk-gvisor)
#         REDTUSK_FC_DIR     (default $HOME/redtusk-bb-fc)
#         ROOTFS_MIB         (default: match the existing ext4, else 1536)
set -euo pipefail

TAG="${1:?usage: export_warm_rootfs.sh <tag>}"
GVISOR_DIR="${REDTUSK_GVISOR_DIR:-/var/lib/redtusk-gvisor}"
FC_DIR="${REDTUSK_FC_DIR:-$HOME/redtusk-bb-fc}"
GV_IMAGE="redtusk-warm:gvisor-$TAG"
FC_IMAGE="redtusk-fc-worker:$TAG"

for img in "$GV_IMAGE" "$FC_IMAGE"; do
  docker image inspect --format '{{.Id}}' "$img" >/dev/null 2>&1 || {
    echo "$img is not built. Run scripts/build_images.sh $TAG with BLASTBOX_SRC set." >&2
    exit 2
  }
done

# `docker export | tar -x` over an EXISTING tree overwrites the members in the
# archive and leaves everything else behind: a file the new image deleted or
# renamed stays, and the guest boots a mixture of two builds. Extract into a
# fresh directory and swap, keeping the old one for rollback.
echo ">> gvisor rootfs <- $GV_IMAGE"
staging="$GVISOR_DIR/rootfs-$TAG"
sudo rm -rf "$staging"
sudo mkdir -p "$staging"
cid="$(docker create "$GV_IMAGE")"
trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' EXIT
docker export "$cid" | sudo tar -x -C "$staging"
docker rm "$cid" >/dev/null; trap - EXIT
if [ -d "$GVISOR_DIR/rootfs" ]; then
  sudo rm -rf "$GVISOR_DIR/rootfs.bak"
  sudo mv "$GVISOR_DIR/rootfs" "$GVISOR_DIR/rootfs.bak"
fi
sudo mv "$staging" "$GVISOR_DIR/rootfs"
echo "   $GVISOR_DIR/rootfs  (previous kept as rootfs.bak)"

# The ext4 is built from the SAME stamped image, not rebuilt from a Dockerfile:
# build-rootfs.sh given only a Dockerfile builds its own image on that file's
# default base, so the booted rootfs would not be the artifact that was verified.
echo ">> firecracker rootfs <- $FC_IMAGE"
out="$FC_DIR/redtusk-rootfs.ext4"
mib="${ROOTFS_MIB:-}"
if [ -z "$mib" ]; then
  if [ -f "$out" ]; then mib=$(( $(stat -c %s "$out") / 1024 / 1024 )); else mib=1536; fi
fi
rd="$(mktemp -d "${TMPDIR:-/tmp}/rtrootfs.XXXXXX")"
cid="$(docker create "$FC_IMAGE")"
trap 'docker rm -f "$cid" >/dev/null 2>&1 || true; rm -rf "$rd"' EXIT
docker export "$cid" | tar -x -C "$rd"
docker rm "$cid" >/dev/null
mkdir -p "$FC_DIR"
[ -f "$out" ] && mv "$out" "$out.bak"
truncate -s "${mib}M" "$out"
# `mke2fs -d` populates the image directly: no mount, no root -- the same
# discipline the host side uses for never mounting a handled disk.
mkfs.ext4 -F -q -d "$rd" "$out"
rm -rf "$rd"; trap - EXIT
echo "   $out  (${mib} MiB, previous kept as redtusk-rootfs.ext4.bak)"

echo
echo "both warm rootfs artifacts replaced. Restart the gvisor and fc dispatchers"
echo "to pick them up; the tiers boot the rootfs, not the image tag."
