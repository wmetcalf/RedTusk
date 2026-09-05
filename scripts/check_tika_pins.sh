#!/usr/bin/env bash
# Every Dockerfile that CLONES the Tika fork must pin the SAME commit.
#
# They drifted to three different values once already (c4bcec9f / de08f007 /
# 74997d72), so crac, localsrc and localtika were each building a different parser
# set while looking uniform. Nothing caught it because nothing compared them.
#
# Discovery keys on the CLONE URL, never on the ARG this script enforces. An
# earlier version listed files by `^ARG TIKA_FORK_SHA=`, which fails open: a
# cloning Dockerfile that drops the ARG and hardcodes a checkout silently leaves
# the check's scope while the surviving files keep reporting "consistent".
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

CLONE_URL='github.com/wmetcalf/tika.git'

mapfile -t cloners < <(grep -rlF "$CLONE_URL" deploy/ | sort)
mapfile -t declarers < <(grep -rlE '^ARG TIKA_FORK_SHA=' deploy/ | sort)

if [ "${#cloners[@]}" -eq 0 ]; then
    echo "no Dockerfile clones $CLONE_URL -- has the fork URL changed?" >&2
    exit 1
fi

rc=0

# A pin on a file that never clones is decoration: it advertises a Tika the image
# does not contain. Dockerfile.default.localsrc shipped exactly that for weeks.
for f in "${declarers[@]}"; do
    if ! printf '%s\n' "${cloners[@]}" | grep -qxF "$f"; then
        echo "$f: declares TIKA_FORK_SHA but never clones $CLONE_URL." >&2
        echo "  A pin nothing uses misleads anyone auditing which Tika is in the image." >&2
        rc=1
    fi
done

declare -A seen=()
for f in "${cloners[@]}"; do
    sha="$(grep -oE '^ARG TIKA_FORK_SHA=[0-9a-f]{40}' "$f" | head -1 | cut -d= -f2 || true)"
    if [ -z "$sha" ]; then
        echo "$f: clones the Tika fork but declares no full 40-char ARG TIKA_FORK_SHA." >&2
        echo "  Every cloning image must pin a commit, or it builds an unknown Tika." >&2
        rc=1
        continue
    fi
    seen["$sha"]+="$f "
done

# A declared pin that no checkout consumes is the same lie in a different place: the
# file can keep `ARG TIKA_FORK_SHA` for the checker to find while checking out a
# hardcoded commit. Require the pin to be USED, not merely present.
for f in "${cloners[@]}"; do
    if ! grep -qE 'checkout[^|&]*"?\$\{?TIKA_FORK_SHA\}?"?' "$f"; then
        echo "$f: declares TIKA_FORK_SHA but no checkout consumes it." >&2
        echo "  The pin must drive the checkout, or CI is validating a value the build ignores." >&2
        rc=1
    fi
done

if [ "$rc" -ne 0 ]; then
    exit 1
fi

if [ "${#seen[@]}" -ne 1 ]; then
    echo "TIKA_FORK_SHA has drifted -- ${#seen[@]} different pins across ${#cloners[@]} files:" >&2
    for sha in "${!seen[@]}"; do
        echo "  $sha" >&2
        for f in ${seen[$sha]}; do echo "    $f" >&2; done
    done
    echo "" >&2
    echo "All cloning Dockerfiles must build the same Tika commit." >&2
    exit 1
fi

for sha in "${!seen[@]}"; do
    echo "TIKA_FORK_SHA consistent across ${#cloners[@]} cloning Dockerfile(s): $sha"
done
