#!/usr/bin/env bash
# Every Dockerfile that CLONES the Tika fork must pin the SAME commit.
#
# They drifted to three different values once already (c4bcec9f / de08f007 /
# 74997d72), so crac, localsrc and localtika were each building a different parser
# set while looking uniform. Nothing caught it because nothing compared them.
#
# Dockerfile.default.localsrc is deliberately absent from this check: it builds from
# .tika-src and carries no pin. It previously declared one that nothing used, which
# is exactly the failure this script exists to prevent.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

mapfile -t hits < <(grep -rlE '^ARG TIKA_FORK_SHA=' deploy/ | sort)
if [ "${#hits[@]}" -eq 0 ]; then
    echo "no Dockerfile declares TIKA_FORK_SHA -- has the pin been renamed?" >&2
    exit 1
fi

declare -A seen=()
for f in "${hits[@]}"; do
    sha="$(grep -oE '^ARG TIKA_FORK_SHA=[0-9a-f]{40}' "$f" | head -1 | cut -d= -f2)"
    if [ -z "$sha" ]; then
        echo "$f: TIKA_FORK_SHA is not a full 40-char sha" >&2
        exit 1
    fi
    seen["$sha"]+="$f "
done

if [ "${#seen[@]}" -ne 1 ]; then
    echo "TIKA_FORK_SHA has drifted -- ${#seen[@]} different pins across ${#hits[@]} files:" >&2
    for sha in "${!seen[@]}"; do
        echo "  $sha" >&2
        for f in ${seen[$sha]}; do echo "    $f" >&2; done
    done
    echo "" >&2
    echo "All cloning Dockerfiles must build the same Tika commit." >&2
    exit 1
fi

for sha in "${!seen[@]}"; do
    echo "TIKA_FORK_SHA consistent across ${#hits[@]} Dockerfile(s): $sha"
done
