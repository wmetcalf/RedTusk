#!/usr/bin/env bash
# One command to take an engine change from source to a verified warm tier.
#
# The point of blastbox + attached engines is that shipping an engine onto whatever
# hardware is available should be a platform property, not per-engine tribal knowledge.
# This wires the existing pieces into that single path, with a gate at each end:
#
#   pre-gate   scripts/deploy_inventory.sh        -- know the current state before touching it
#   1. test    mvn test                           -- fast feedback before a long image build
#   2. image   Dockerfile.localtika               -- builds the jar from source AND regenerates
#                                                    the AOT cache from it (record -> create)
#   3. audit   jar/AOT consistency in the image   -- the stale-AOT trap, caught before deploy
#   4. deploy  blastbox deploy/redeploy-warm.sh   -- rebuilds BOTH rootfs, stages with .bak,
#                                                    recreates api+dispatchers, prints rollback
#   post-gate  scripts/verify_warm_tier.sh        -- proves the tier is warm, not warm-in-name
#              scripts/deploy_inventory.sh        -- proves no drift was introduced
#
# DRY RUN BY DEFAULT. Nothing touches production without --apply.
#
# Usage:
#   scripts/release_engine.sh                          # show the plan
#   scripts/release_engine.sh --apply --tag 0815       # do it
#   scripts/release_engine.sh --apply --skip-image     # reuse an already-built cold image
#
# Env: BLASTBOX_REPO (default ../blastbox), BLASTBOX_REF, BLASTBOX_API, BLASTBOX_FLEET_HOSTS
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BLASTBOX_REPO="${BLASTBOX_REPO:-$(cd "$REPO/../blastbox" 2>/dev/null && pwd)}"
TAG="$(date +%m%d)"
APPLY=0
SKIP_IMAGE=0
ENGINE_NAME="redtusk"

while [ $# -gt 0 ]; do
    case "$1" in
        --apply) APPLY=1; shift ;;
        --tag) TAG="$2"; shift 2 ;;
        --skip-image) SKIP_IMAGE=1; shift ;;
        --engine) ENGINE_NAME="$2"; shift 2 ;;
        -h|--help) sed -n '2,28p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

COLD_IMAGE="${ENGINE_NAME}-cold-worker:${TAG}"
run() {
    if [ "$APPLY" -eq 1 ]; then
        echo "+ $*"; "$@" || return $?
    else
        echo "  [dry-run] $*"
    fi
}
step() { echo; echo "=== $*"; }
die()  { echo "ABORT: $*" >&2; exit 1; }

[ -d "$BLASTBOX_REPO" ] || die "blastbox repo not found (set BLASTBOX_REPO=/path/to/blastbox)"
echo "engine=$ENGINE_NAME tag=$TAG cold_image=$COLD_IMAGE apply=$APPLY"
echo "blastbox_repo=$BLASTBOX_REPO"

step "PRE-GATE: current fleet state"
if [ "$APPLY" -eq 1 ]; then
    "$REPO/scripts/deploy_inventory.sh" || echo "  (drift present before deploy — noted, continuing)"
else
    echo "  [dry-run] $REPO/scripts/deploy_inventory.sh"
fi

step "1. test the engine before spending a long image build on it"
run mvn -f "$REPO/worker_jvm/pom.xml" test \
    || die "java tests failed — not building an image from this"
run python3 -m pytest "$REPO/tests" -q --ignore="$REPO/tests/http" --ignore="$REPO/tests/docker" \
    || die "python tests failed — not building an image from this"

step "2. build the cold-worker image (compiles the jar AND regenerates the AOT cache from it)"
if [ "$SKIP_IMAGE" -eq 1 ]; then
    echo "  --skip-image: reusing existing $COLD_IMAGE"
else
    run docker build -f "$REPO/deploy/docker/Dockerfile.localtika" -t "$COLD_IMAGE" "$REPO" \
        || die "image build failed"
fi

step "3. audit the built image: the AOT cache must match the jar it was built from"
if [ "$APPLY" -eq 1 ] && [ "$SKIP_IMAGE" -eq 0 ]; then
    audit=$(docker run --rm --entrypoint sh "$COLD_IMAGE" -c '
        [ -f /app/redtusk-worker.jar ] || { echo "JAR_MISSING"; exit 0; }
        [ -f /app/redtusk.aot ] || { echo "AOT_MISSING"; exit 0; }
        [ /app/redtusk.aot -ot /app/redtusk-worker.jar ] && echo "AOT_STALE" || echo "OK"' 2>/dev/null)
    case "$audit" in
        OK) echo "  jar + AOT present and consistent" ;;
        AOT_STALE) die "AOT cache is older than the jar — it will fail to map and silently cost startup on every job" ;;
        *) die "image audit failed: $audit" ;;
    esac
    # Prove the AOT cache MAPS under the exact flags production uses. It is flag- and
    # classpath-sensitive: a mismatch does not fail the job, it silently disables the cache and
    # costs JVM startup on every single one.
    #
    # This does NOT exercise the prewarm path, and used to claim it did: it set
    # REDTUSK_PREWARM=1, but that variable is only read on the `--run` path, while
    # `--appcds-warmup` goes to runWarmup and exits immediately on a non-directory. Exercising
    # prewarm for real needs a full job handshake (and, since the go-wait is unbounded by
    # design, would park here forever), so it belongs in the Java tests that step 1 already
    # runs -- MainIntegrationTest.prewarmIsSkippedUnlessExplicitlyEnabled and
    # prewarmRunsWhenEnabledAndNeverThrows. A gate that says more than it checks is worse than
    # no gate.
    echo "  checking the AOT cache maps under the production JVM flags..."
    aot_errs=$(docker run --rm --entrypoint sh "$COLD_IMAGE" -c '
        java -XX:AOTCache=/app/redtusk.aot -Djava.library.path=/app -XX:+UseSerialGC \
             -XX:TieredStopAtLevel=1 -Xms800m -Xmx800m --enable-native-access=ALL-UNNAMED \
             -jar /app/redtusk-worker.jar --appcds-warmup /nonexistent 2>&1 | grep -ci "error.*aot" ')
    # ...and DIE on it. This used to only echo "!!", so the one thing it checked could fail and
    # the release still walked past it.
    if [ "${aot_errs:-1}" = "0" ]; then
        echo "  AOT cache maps cleanly"
    else
        die "AOT cache did NOT map cleanly (${aot_errs} error line(s)) — the JVM flags here must
     match the ones the cache was built with, or every job silently pays full startup"
    fi
else
    echo "  [dry-run] docker run --rm $COLD_IMAGE -> assert jar+AOT present, AOT newer than jar, AOT maps cleanly"
fi

step "4. rebuild both rootfs + recreate the stack (blastbox redeploy-warm.sh)"
echo "  This rebuilds the FC *and* gVisor rootfs from $COLD_IMAGE, stages them with .bak"
echo "  backups, bumps the compose image vars, recreates api+dispatchers (never postgres),"
echo "  and prints a ROLLBACK block. Run it ON the deploy host, from the blastbox repo."
DEPLOY_CMD=(env "ENGINE=$ENGINE_NAME" "COLD_IMAGE=$COLD_IMAGE" ${BLASTBOX_REF:+"BLASTBOX_REF=$BLASTBOX_REF"} \
            "$BLASTBOX_REPO/deploy/redeploy-warm.sh")
if [ "$APPLY" -eq 1 ]; then
    echo "  NOT auto-running: this step recreates production containers."
    echo "  Run it yourself, then re-run this script's post-gate with --skip-image:"
fi
printf '    %q ' "${DEPLOY_CMD[@]}"; echo

step "POST-GATE: prove the tier is actually warm, and that nothing drifted"
if [ "$APPLY" -eq 1 ]; then
    # PROVE the deploy happened before judging it. Step 4 above deliberately does not run
    # (it recreates production containers), so an operator who runs --apply and stops there
    # would otherwise get verify+inventory run against the STILL-OLD deployment and a
    # "RELEASE OK: <image> is live" for a build that never reached the fleet -- the worst
    # possible output, because it is a green that certifies the wrong thing.
    #
    # The engine image the dispatchers actually launch is in their BLASTBOX_ENGINES env, so
    # this is checkable rather than assertable. No flag to forget, no operator to trust.
    read -r -a _HOSTS <<< "${BLASTBOX_FLEET_HOSTS:-172.18.101.15}"
    _live=""
    for _h in "${_HOSTS[@]}"; do
        _live+=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$_h" \
            'for c in $(docker ps --format "{{.Names}}" | grep -E -- "-bb-dispatcher"); do
                 docker exec "$c" printenv BLASTBOX_ENGINES 2>/dev/null; done' 2>/dev/null)
    done
    if [ -z "$_live" ]; then
        die "could not read BLASTBOX_ENGINES from any dispatcher on ${_HOSTS[*]} — cannot prove
     what is deployed, so refusing to certify this release. Check ssh/BLASTBOX_FLEET_HOSTS."
    fi
    if ! grep -qF -- "$COLD_IMAGE" <<< "$_live"; then
        die "STEP 4 WAS NOT RUN: the dispatchers are still launching [$(tr '\n' ' ' <<< "$_live")],
     not $COLD_IMAGE. Run the deploy command printed above, then re-run this script with
     --apply --skip-image to execute the post-gate against the new deployment."
    fi
    echo "  confirmed: dispatchers launch $COLD_IMAGE"
    "$REPO/scripts/verify_warm_tier.sh" || die "warm-tier check FAILED — the deploy did not achieve a warm tier"
    "$REPO/scripts/deploy_inventory.sh" || die "drift detected after deploy"
    echo; echo "RELEASE OK: $COLD_IMAGE is live and the tier is warm."
else
    echo "  [dry-run] $REPO/scripts/verify_warm_tier.sh   # 3-byte job must be well under budget"
    echo "  [dry-run] $REPO/scripts/deploy_inventory.sh   # no mixed images, no rootfs older than image"
fi
