#!/usr/bin/env bash
# Regenerate docs/metadata-fields-static-augmented.json by running the
# fork's static analyzer with --extra-root pointing at our worker_jvm/.
#
# This is what feeds inventory_combine.py — distinct from the fork's
# own Tika-only docs/metadata-fields-static.json which is CI-gated and
# must NOT include extra-root entries (CI has no RedTusk checkout).
#
# Usage:   scripts/inventory_augment.sh [path-to-tika-fork-checkout]
# Default tika path: ~/.config/superpowers/worktrees/tika/4.0-upstream-office-links

set -euo pipefail

TIKA_ROOT="${1:-$HOME/.config/superpowers/worktrees/tika/4.0-upstream-office-links}"
REDTUSK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKER_JVM="$REDTUSK_ROOT/worker_jvm"
OUT="$REDTUSK_ROOT/docs/metadata-fields-static-augmented.json"

if [[ ! -d "$TIKA_ROOT/tools" ]]; then
  echo "error: $TIKA_ROOT does not look like a tika fork checkout" >&2
  echo "       (no tools/ directory)" >&2
  exit 2
fi
if [[ ! -d "$WORKER_JVM" ]]; then
  echo "error: $WORKER_JVM not found" >&2
  exit 2
fi

python3 "$TIKA_ROOT/tools/inventory_static.py" \
  --tika-root "$TIKA_ROOT" \
  --extra-root "$WORKER_JVM" \
  --out "$OUT"

echo "regenerated $OUT"
