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
STAGE_IMAGE="redtusk-tika-stage:${TIKA_FORK_SHA:-pinned}"
DF="$REPO/deploy/docker/Dockerfile.localtika"

sha=$(grep -oE '^ARG TIKA_FORK_SHA=[0-9a-f]+' "$DF" | cut -d= -f2)
[ -n "$sha" ] || { echo "could not read TIKA_FORK_SHA from $DF" >&2; exit 1; }
echo ">> Tika pinned at ${sha:0:12} (from Dockerfile.localtika)"

# Build ONLY the tika-build stage. Layer-cached, so this compiles Tika once per SHA bump.
docker build --target tika-build -t "$STAGE_IMAGE" -f "$DF" "$REPO" \
    || { echo "tika-build stage failed" >&2; exit 1; }

case "$GOAL" in
    shell) CMD=(bash) ;;
    *)     CMD=(bash -lc "cd /build/worker_jvm && mvn -B $GOAL") ;;
esac

# The stage image already has Maven 3.9 + the JDK + Tika installed in its ~/.m2, which is the
# whole point: no host ~/.m2 is mounted, so a stale local artifact cannot leak in.
# -t only when there IS a tty: `docker run -it` fails outright in CI or any non-interactive
# shell ("the input device is not a TTY"), which would make this script unusable in exactly the
# automation it exists to serve.
TTY_FLAGS=()
[ -t 0 ] && [ -t 1 ] && TTY_FLAGS=(-it)
docker run --rm "${TTY_FLAGS[@]}" \
    -v "$REPO/worker_jvm:/build/worker_jvm" \
    -w /build \
    "$STAGE_IMAGE" "${CMD[@]}"
