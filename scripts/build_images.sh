#!/usr/bin/env bash
# Build RedTusk's images so each one RECORDS what it was built from.
#
# Why this exists: on 2026-09-02 the base image that built the running
# redtusk-cold-worker no longer existed. Its worker jar matched none of the
# fourteen redtusk-worker:* tags on the box and no dangling image, so the
# deployed worker could not be rebuilt at all -- and nothing had recorded the
# base, so the gap was invisible until someone went looking.
#
# `blastbox stamp` emits the labels that close that gap AND pins the build to
# the digest it records, so the stamp cannot describe an image the build did
# not use. It also refuses to pin a base whose ARG the Dockerfile does not
# declare (these Dockerfiles disagree: BASE_IMAGE here, BASE in blastbox's
# gvisor one), because docker silently ignores an undeclared --build-arg.
#
# Usage:
#   scripts/build_images.sh <tag> [blastbox-version]
# Example:
#   scripts/build_images.sh bb0128 0.1.28
set -euo pipefail

TAG="${1:?usage: build_images.sh <tag> [blastbox-version]}"
REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# The version the images will INSTALL, not the version of the CLI doing the
# stamping -- they are not necessarily the same, and recording the wrong one is
# worse than recording nothing.
BLASTBOX_VERSION="${2:-$(grep -oE 'blastbox>=[0-9.]+' pyproject.toml | head -1 | cut -d= -f3)}"

command -v blastbox >/dev/null || {
  echo "blastbox CLI not found. This script needs a blastbox providing" >&2
  echo "\`blastbox stamp\` (>= 0.1.28)." >&2
  exit 2
}
blastbox stamp --help >/dev/null 2>&1 || {
  echo "this blastbox has no \`stamp\` subcommand; need >= 0.1.28" >&2
  exit 2
}

# A deployed tree is often an rsync'd copy with no .git, and a stamp with no
# revision is refused. Record where this tree came from when git cannot say.
if ! git -C "$REPO" rev-parse HEAD >/dev/null 2>&1 && [ ! -f "$REPO/.blastbox-revision" ]; then
  echo "no git and no .blastbox-revision: write the source sha into" >&2
  echo "  $REPO/.blastbox-revision  as part of the deploy" >&2
  exit 2
fi

stamp_flags() {  # <dockerfile> [base] [base-arg]
  local df="$1" base="${2:-}" arg="${3:-BASE_IMAGE}"
  if [ -n "$base" ]; then
    blastbox stamp --repo "$REPO" -f "$df" --base "$base" --base-arg "$arg" \
                   --blastbox-version "$BLASTBOX_VERSION"
  else
    blastbox stamp --repo "$REPO" --blastbox-version "$BLASTBOX_VERSION"
  fi
}

echo ">> worker base (jar + AOT)  -> redtusk-worker:$TAG"
# shellcheck disable=SC2046  # word splitting is the point: these are flags
docker build -f deploy/docker/Dockerfile.default \
  $(stamp_flags deploy/docker/Dockerfile.default) \
  -t "redtusk-worker:$TAG" .

echo ">> cold worker              -> redtusk-cold-worker:$TAG"
# shellcheck disable=SC2046
docker build -f deploy/docker/Dockerfile.cold-worker \
  $(stamp_flags deploy/docker/Dockerfile.cold-worker "redtusk-worker:$TAG" BASE_IMAGE) \
  -t "redtusk-cold-worker:$TAG" .

echo ">> host / dispatcher        -> redtusk:$TAG"
# shellcheck disable=SC2046
docker build -f deploy/docker/Dockerfile.host \
  $(stamp_flags deploy/docker/Dockerfile.host) \
  -t "redtusk:$TAG" .

echo
echo ">> verify: every image must record what it was built from"
rc=0
for img in "redtusk-worker:$TAG" "redtusk-cold-worker:$TAG" "redtusk:$TAG"; do
  echo "-- $img"
  blastbox stamp --read "$img" || rc=1
done
[ "$rc" -eq 0 ] || {
  echo >&2
  echo "one or more images are not reproducible from what they record." >&2
  exit 1
}
echo
echo "all images stamped. Deploy by pointing REDTUSK_IMAGE / REDTUSK_WORKER_IMAGE"
echo "at :$TAG in deploy/docker/.env, then recreate api + every dispatcher."
