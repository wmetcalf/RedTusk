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
#
# Env: WORKER_BASE / HOST_BASE  override the upstream bases
#      BLASTBOX_WHEEL          ship a pre-release host blastbox (section 1)
# Example:
#   scripts/build_images.sh bb0129 0.1.29
set -euo pipefail

TAG="${1:?usage: build_images.sh <tag> [blastbox-version]}"
REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# The version the images will INSTALL, not the version of the CLI doing the
# stamping -- they are not necessarily the same, and recording the wrong one is
# worse than recording nothing.
# `cut -d= -f<n>` cannot do this: `blastbox>=0.1.27` splits into TWO fields on
# `=` (field 2 is the version), `blastbox==0.1.28` into three, and a range like
# `blastbox>=0.1.27,<0.2` drags the upper bound into whichever field it lands
# in. Match the version digits themselves instead of counting delimiters.
# Comment lines are dropped first for the same reason `blastbox pins` ignores
# them: a version mentioned in prose is not a pin, and letting one win here
# would stamp a version nothing installs. The extras form (`blastbox[host]>=`)
# is matched too -- missing it silently fell through to the empty check.
# `|| true` is load-bearing: under `set -e` with `pipefail`, a grep that
# matches nothing makes the ASSIGNMENT fail, which kills the script before the
# check below can print anything. The observable symptom is no output and
# exit 1 -- the worst possible diagnostic for a missing pin.
BLASTBOX_VERSION="${2:-$(grep -v '^[[:space:]]*#' pyproject.toml |
    grep -oE 'blastbox(\[[A-Za-z0-9,._-]+\])?[[:space:]]*[<>=!~]=[[:space:]]*[0-9]+(\.[0-9]+)*' |
    head -1 | grep -oE '[0-9]+(\.[0-9]+)*$' || true)}"
[ -n "$BLASTBOX_VERSION" ] || {
  echo "could not read a blastbox version from pyproject.toml." >&2
  echo "Pass it explicitly:  scripts/build_images.sh $TAG <blastbox-version>" >&2
  exit 2
}

# The upstream bases the two root images build on. Overridable so a base bump
# is one env var rather than an edit in two files; the DEFAULTS must match the
# Dockerfiles' own ARG defaults, which tests/unit/test_build_script_arg_names.py
# asserts -- a drift here would pin a base the Dockerfile does not otherwise use.
WORKER_BASE="${WORKER_BASE:-eclipse-temurin:25-jre-jammy}"
HOST_BASE="${HOST_BASE:-python:3.12-slim-bookworm}"

command -v blastbox >/dev/null || {
  echo "blastbox CLI not found. This script needs a blastbox providing" >&2
  echo "\`blastbox stamp\` (>= 0.1.29)." >&2
  exit 2
}
# Checking that the SUBCOMMAND exists is not the same as checking the version:
# 0.1.28 has `stamp` too, and it pins a local base by a reference no builder can
# resolve. The build then dies inside the first `docker build` with what reads
# like a registry auth error, which points nowhere near the real cause.
BB_MIN=0.1.29
BB_HAVE="$(blastbox version 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)+' | head -1 || true)"
[ -n "$BB_HAVE" ] || {
  echo "this blastbox has no usable \`version\` output; need >= $BB_MIN" >&2
  exit 2
}
# sort -V puts the smaller first, so the minimum leading means it is satisfied.
# A PEP 440 local version (0.1.29+gabc) sorts after its release, as intended.
[ "$(printf '%s\n%s\n' "$BB_MIN" "$BB_HAVE" | sort -V | head -1)" = "$BB_MIN" ] || {
  echo "blastbox $BB_HAVE is too old; need >= $BB_MIN." >&2
  echo "0.1.28 has \`stamp\` but pins a local base by a reference buildkit" >&2
  echo "cannot resolve, so the build fails looking like a registry auth error." >&2
  echo "  pip install --upgrade 'blastbox>=$BB_MIN'" >&2
  exit 2
}

# A deployed tree is often an rsync'd copy with no .git, and a stamp with no
# revision is refused. Record where this tree came from when git cannot say.
if ! git -C "$REPO" rev-parse HEAD >/dev/null 2>&1 && [ ! -f "$REPO/.blastbox-revision" ]; then
  echo "no git and no .blastbox-revision: write the source sha into" >&2
  echo "  $REPO/.blastbox-revision  as part of the deploy" >&2
  exit 2
fi

# Every image gets a pinned base, including the two built on upstream tags.
# `blastbox stamp --read` reports an image with no recorded base digest as
# UNSTAMPED and exits 1, so an unpinned image would fail this script's own
# verification -- and rightly: `python:3.12-slim-bookworm` and
# `eclipse-temurin:25-jre-jammy` are mutable, so without a digest the same
# source and tag rebuild on different bytes.
# Sets `flags` (an array) from `blastbox stamp`, and ABORTS if stamp refuses.
#
# This must not be a `$(...)` in docker's argument list. `set -e` reacts to the
# status of the whole command -- `docker build` -- and DISCARDS the status of a
# command substitution in its arguments. A refusing stamp would leave the build
# running with no labels and no --build-arg, so the cold worker would fall back
# to its Dockerfile default `redtusk-worker:default`: a mutable tag pointing at
# whatever stale base is on the box. That is the 2026-09-02 incident exactly,
# silently reproduced under the intended tag, and the script would print
# "all images stamped" afterwards.
#
# Reading into an array also keeps each flag one argv entry regardless of what
# a label value contains, instead of relying on word splitting.
stamp_flags() {  # <dockerfile> <base> [base-arg]
  local df="$1" base="$2" arg="${3:-BASE_IMAGE}" out
  out="$(blastbox stamp --repo "$REPO" -f "$df" --base "$base" --base-arg "$arg" \
                  --blastbox-version "$BLASTBOX_VERSION")" || {
    echo "blastbox stamp refused to stamp $df -- not building it unstamped." >&2
    exit 1
  }
  read -r -a flags <<<"$out"
}

# An upstream tag has to be present locally before it can be resolved to a
# digest, and `docker build` would otherwise pull it itself -- possibly a
# DIFFERENT push of the same tag than the one recorded. Each pull is its own
# command so `set -e` sees its status; wrapping it in `$(...)` would discard
# that, and an `exit` inside a substitution only leaves the SUBSHELL.

# The images install this blastbox; the Dockerfiles default the ARG, and a
# default that drifts from what is stamped produces the exact lie this tooling
# exists to catch: a label naming one version over a venv holding another.
version_arg=(--build-arg "BLASTBOX_VERSION=$BLASTBOX_VERSION")

# The pre-release escape hatch documented for the host image (DEPLOYMENT.md
# section 1) is `ARG BLASTBOX_WHEEL`. Without a way to pass it, an operator
# told to build with this script would silently get the PyPI blastbox instead
# of the host-side fix they came for. Empty = the pinned PyPI release ships.
wheel_arg=()
if [ -n "${BLASTBOX_WHEEL:-}" ]; then
  wheel_arg=(--build-arg "BLASTBOX_WHEEL=$BLASTBOX_WHEEL")
fi

echo ">> worker base (jar + AOT)  -> redtusk-worker:$TAG"
docker pull -q "$WORKER_BASE" >/dev/null
stamp_flags deploy/docker/Dockerfile.default "$WORKER_BASE"
docker build -f deploy/docker/Dockerfile.default \
  "${flags[@]}" \
  -t "redtusk-worker:$TAG" .

echo ">> cold worker              -> redtusk-cold-worker:$TAG"
stamp_flags deploy/docker/Dockerfile.cold-worker "redtusk-worker:$TAG"
docker build -f deploy/docker/Dockerfile.cold-worker \
  "${flags[@]}" \
  "${version_arg[@]}" \
  -t "redtusk-cold-worker:$TAG" .

echo ">> host / dispatcher        -> redtusk:$TAG"
docker pull -q "$HOST_BASE" >/dev/null
stamp_flags deploy/docker/Dockerfile.host "$HOST_BASE"
docker build -f deploy/docker/Dockerfile.host \
  "${flags[@]}" \
  "${version_arg[@]}" "${wheel_arg[@]}" \
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
