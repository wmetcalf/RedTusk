#!/usr/bin/env bash
# Build/test worker_jvm in the SAME environment the deployed image uses.
#
# Why this exists: `mvn test` on a developer box resolves Tika from ~/.m2, which is whatever
# that machine happens to have. On 2026-08-19 this repo's own laptop had Tika 3.0.0 there while
# the image shipped 4.0.0-SNAPSHOT -- so `mvn test` compiled against a DIFFERENT API than the
# jar in production. Code that compiled locally failed inside the image build, and 26 green
# tests said nothing about what shipped.
#
# The image's Tika comes from Dockerfile.localtika's `tika-build` stage, pinned by
# TIKA_FORK_SHA. This script reuses that exact stage, so local test runs and the release build
# agree by construction rather than by luck.
#
# Usage:
#   scripts/worker_build.sh test        # run the worker_jvm test suite (default)
#   scripts/worker_build.sh package     # build the fat jar
#   scripts/worker_build.sh shell       # interactive, same environment
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
GOAL="${1:-test}"
# Tag and contents are both derived from the SHA parsed out of the Dockerfile below. An earlier
# version tagged with ${TIKA_FORK_SHA:-pinned} and never passed it as a --build-arg, so
# `TIKA_FORK_SHA=other scripts/worker_build.sh` produced an image whose TAG named one Tika and
# whose CONTENTS were another -- the exact failure class this script exists to eliminate. With
# the variable unset it also collapsed every SHA onto one ":pinned" tag.
DF="$REPO/deploy/docker/Dockerfile.localtika"

sha=$(grep -oE '^ARG TIKA_FORK_SHA=[0-9a-f]+' "$DF" | cut -d= -f2)
[ -n "$sha" ] || { echo "could not read TIKA_FORK_SHA from $DF" >&2; exit 1; }
STAGE_IMAGE="redtusk-tika-stage:${sha:0:12}"
echo ">> Tika pinned at ${sha:0:12} (from Dockerfile.localtika)"

# Build ONLY the tika-build stage. Layer-cached, so this compiles Tika once per SHA bump.
docker build --target tika-build --build-arg "TIKA_FORK_SHA=$sha" -t "$STAGE_IMAGE" -f "$DF" "$REPO" \
    || { echo "tika-build stage failed" >&2; exit 1; }

# The stage image already has Maven 3.9 + the JDK + Tika installed in its ~/.m2, which is the
# whole point: no host ~/.m2 is mounted, so a stale local artifact cannot leak in.
# -t only when there IS a tty: `docker run -it` fails outright in CI or any non-interactive
# shell ("the input device is not a TTY"), which would make this script unusable in exactly the
# automation it exists to serve.
TTY_FLAGS=()
[ -t 0 ] && [ -t 1 ] && TTY_FLAGS=(-it)
# Runs as ROOT on purpose: the stage image keeps its Tika artifacts in /root/.m2, which a
# mapped host uid cannot read (and redirecting HOME just hides them -- that mistake produced
# "Could not find artifact org.apache.tika:tika-core:jar:4.0.0-SNAPSHOT" on every dependency).
#
# The host tree is bind-mounted, so root would otherwise leave target/ root-owned, and a later
# host-side mvn, `git clean -xdf` or IDE build then fails on it. So hand ownership back on the
# way out, whatever the build did -- including on failure, hence the trap.
HOST_UID=$(id -u); HOST_GID=$(id -g)
if [ "$GOAL" = "shell" ]; then
    INNER=(bash)
else
    INNER=(bash -lc "trap 'chown -R $HOST_UID:$HOST_GID /build/worker_jvm/target 2>/dev/null || true' EXIT; cd /build/worker_jvm && mvn -B $GOAL")
fi
docker run --rm "${TTY_FLAGS[@]}" \
    -v "$REPO/worker_jvm:/build/worker_jvm" \
    -w /build \
    "$STAGE_IMAGE" "${INNER[@]}"
