#!/usr/bin/env bash
# Deploy the local RedTusk checkout to a remote host via rsync, EXCLUDING
# files that are per-host config and must not be overwritten by a deploy:
#
#   deploy/docker/.env  — POSTGRES_PASSWORD, REDTUSK_PORT, REDTUSK_STATE_DIR,
#                         DOCKER_GID. Setting these from a dev workstation's
#                         copy will desynchronize Postgres credentials, break
#                         the API port, and trigger a state-dir permission
#                         failure on the remote.
#   var/                — local state dir (artifacts, scratch). Per-host.
#   .venv/, __pycache__/, *.pyc, .git/  — build/source artifacts.
#   tests/fixtures/corpus/  — corpus files are sensitive and per-host.
#
# Usage:
#   scripts/deploy_to_host.sh user@host:/path/on/remote/redtusk
#
# Example:
#   scripts/deploy_to_host.sh coz@172.18.101.15:/home/coz/redtusk
#
# After a successful rsync, this script:
#   1. Reminds you to confirm REDTUSK_STATE_DIR ownership on the remote
#   2. Does NOT restart any service — you decide when to bounce the api,
#      because a restart drops in-flight uploads and re-runs orphan recovery.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 user@host:/remote/path" >&2
    exit 2
fi
TARGET="$1"
shift

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Exclusions are listed via --exclude-from instead of inline so a future
# maintainer can audit the deploy boundary in one place. The file is
# kept in scripts/ next to this script.
EXCLUDE_FILE="scripts/deploy-exclude.txt"
if [ ! -f "$EXCLUDE_FILE" ]; then
    cat > "$EXCLUDE_FILE" <<EOF
# Per-host config — overwriting these will break the remote deployment.
deploy/docker/.env
# Per-host state.
var/
# Build/source artifacts.
.venv/
__pycache__/
*.pyc
.git/
.pytest_cache/
.mypy_cache/
.ruff_cache/
# Sensitive fixtures that should never leave the maintainer's machine.
tests/fixtures/corpus/
# IDE / OS noise.
.vscode/
.idea/
.DS_Store
EOF
fi

echo "==> rsync to $TARGET (excludes: see $EXCLUDE_FILE)"
rsync -az --delete --exclude-from="$EXCLUDE_FILE" \
      "$@" ./ "$TARGET/"

echo ""
echo "==> deploy complete. Remember:"
echo "    1. On the remote, REDTUSK_STATE_DIR must be owned by UID 10001"
echo "         ssh ${TARGET%:*} 'sudo chown -R 10001:10001 \$REDTUSK_STATE_DIR'"
echo "    2. To pick up code changes, rebuild + restart the api:"
echo "         ssh ${TARGET%:*} 'cd ${TARGET#*:} && ./deploy/docker/redtusk-compose build api && ./deploy/docker/redtusk-compose up -d api'"
