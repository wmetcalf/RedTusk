#!/usr/bin/env bash
# Verify a warm tier is actually warm, by exploiting the one property that cannot be faked:
# on a genuinely warm tier the per-job cost is INDEPENDENT of document size, because the
# fixed cost was paid before the snapshot. If a 3-byte file costs the same as a real
# document AND that cost is seconds, the fixed cost is still being paid per job.
#
# This is the acceptance test for any warm-tier deployment. It caught a tier that restored
# a warm microVM in 0.5s and then spent 3.3s per job rebuilding the Tika parser tree.
#
# Usage: scripts/verify_warm_tier.sh [--api http://host:8003] [--engine redtusk] [--budget 1.5]
set -uo pipefail

API="${BLASTBOX_API:-http://172.18.101.15:8003}"
ENGINE="redtusk"
BUDGET="1.5"     # seconds; a warm tier should land well under this
while [ $# -gt 0 ]; do
    case "$1" in
        --api) API="$2"; shift 2 ;;
        --engine) ENGINE="$2"; shift 2 ;;
        --budget) BUDGET="$2"; shift 2 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
printf 'hi' > "$tmp/tiny.txt"
# ~200KB of structured HTML: real parsing work, no external fixture needed.
{ echo "<html><body>"; for i in $(seq 1 4000); do
    echo "<p>row $i with some text content to give the parser real work to do</p>"; done
  echo "</body></html>"; } > "$tmp/big.html"

submit_and_time() {
    local f="$1" start id st
    start=$(date +%s%N)
    id=$(curl -s -F "file=@$f" -F "engine=$ENGINE" "$API/v1/jobs" \
         | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("id") or d.get("job_id") or "")' 2>/dev/null)
    [ -z "$id" ] && { echo "SUBMIT_FAILED"; return 1; }
    for _ in $(seq 1 600); do
        st=$(curl -s "$API/v1/jobs/$id" \
             | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status",""))' 2>/dev/null)
        case "$st" in done|failed|error) break ;; esac
        sleep 0.1
    done
    echo "$(( ($(date +%s%N) - start) / 1000000 )) $st"
}

echo "api=$API engine=$ENGINE budget=${BUDGET}s"
read -r tiny_ms tiny_st <<< "$(submit_and_time "$tmp/tiny.txt")"
read -r big_ms  big_st  <<< "$(submit_and_time "$tmp/big.html")"
[ "$tiny_ms" = "SUBMIT_FAILED" ] || [ "$big_ms" = "SUBMIT_FAILED" ] && {
    echo "FAIL: could not submit jobs to $API"; exit 2; }

printf '  %-22s %6s ms  (%s)\n' "3-byte input"  "$tiny_ms" "$tiny_st"
printf '  %-22s %6s ms  (%s)\n' "200KB document" "$big_ms" "$big_st"

budget_ms=$(python3 -c "print(int(float('$BUDGET')*1000))")
# The 3-byte job IS the floor: whatever it costs is fixed overhead, because three bytes
# cannot take meaningful time to extract. The big document only tells us how much of ITS
# cost is marginal (real parsing) on top of that same floor.
marginal=$(( big_ms - tiny_ms ))
(( marginal < 0 )) && marginal=0

echo
printf '  fixed overhead (floor) : %s ms\n' "$tiny_ms"
printf '  marginal cost of 200KB : %s ms\n' "$marginal"
echo
if [ "$tiny_ms" -le "$budget_ms" ]; then
    echo "PASS: fixed overhead ${tiny_ms}ms is within the ${BUDGET}s budget — tier is warm."
    exit 0
fi
cat <<EOF
FAIL: ${tiny_ms}ms to process THREE BYTES. That is fixed per-job overhead, not extraction —
      the tier is warm in name only, and every job pays it. Check, in order:
        1. 'redtusk warm JVM unavailable ... cold fallback' in the dispatcher log
           -> the warm JVM is not being reached at all.
        2. 'redtusk warm JVM ready ... after N.NNs' -> N ~0.8s means REDTUSK_PREWARM
           never reached the JVM, so Tika initialises on the first real job instead.
        3. scripts/deploy_inventory.sh --deep -> STALE AOT, or a rootfs older than the image
           (the FC guest carries its own blastbox/redtusk copy).
EOF
exit 1
