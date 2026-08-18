#!/usr/bin/env bash
# Break a warm-tier job down into slot-lifecycle phases, from the dispatcher's own logs.
#
# Why this exists: throughput on a disposable-slot tier is  slots / slot_cycle_time, NOT
# 1 / engine_time. Measured on toolz2: 24 slots sustain ~1.9-2.6 jobs/s, i.e. a slot cycle of
# ~10-12s per job, while a single job against an IDLE tier completes end-to-end in <1s. So most
# of the cycle is everything EXCEPT extraction (restore, readiness, dispatch, seal, outdisk read,
# upload, reap, respawn) -- tuning the engine there is nearly free of effect.
#
# It reports rates AND a per-phase breakdown -- but the breakdown comes ONLY from the
# dispatcher's own `warm_phases` line (blastbox >= 2d88c70), which is emitted once per job with
# a job_id and is measured host-side inside the single thread that owns the job. Do NOT
# reintroduce order-paired guest durations: the guest log lines have no correlation id, so under
# concurrency pairing the k-th start with the k-th completion compares DIFFERENT JOBS. That
# method reported 0.67s and 5.48s for the same tier minutes apart.
#
# Usage: scripts/slot_cycle_profile.sh [--host H] [--container C] [--window 3m]
set -uo pipefail

HOST="${BLASTBOX_FLEET_HOST:-172.18.101.15}"
CONTAINER="redtusk-bb-dispatcher-fc-1"
WINDOW="3m"
while [ $# -gt 0 ]; do
    case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --container) CONTAINER="$2"; shift 2 ;;
        --window) WINDOW="$2"; shift 2 ;;
        -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

read -r -d '' REMOTE <<'PYEOF'
import re, sys, datetime, subprocess
window, container = sys.argv[1], sys.argv[2]
raw = subprocess.run(["docker","logs","--since",window,"--timestamps",container],
                     capture_output=True, text=True).stdout + \
      subprocess.run(["docker","logs","--since",window,"--timestamps",container],
                     capture_output=True, text=True).stderr

ev, warm_size, phase_rows = [], None, []
for line in raw.splitlines():
    m = re.match(r"(\S+)Z ", line)
    if not m:
        continue
    try:
        t = datetime.datetime.fromisoformat(m.group(1)[:26])
    except ValueError:
        continue
    if "snapshot.spawn" in line:            ev.append((t, "spawn"))
    elif "job_received" in line:            ev.append((t, "recv"))
    elif "serve_warm returned" in line:     ev.append((t, "done"))
    elif "outdisk_read" in line:            ev.append((t, "read"))
    if "warm_phases" in line:
        # One line per job, already correlated by job_id and already ordered by construction:
        # nothing here is inferred from log ORDER, which is the whole point.
        rec = dict(re.findall(r"(\w+)=([\d.]+)\b", line))
        outcome = re.search(r"outcome=(\w+)", line)
        phase_rows.append((outcome.group(1) if outcome else "?", rec))
    if "warm_pool_built" in line:
        w = re.search(r"warm_size=(\d+)", line)
        if w: warm_size = int(w.group(1))
ev.sort()
if len(ev) < 8 and not phase_rows:
    print("  not enough events in the window — is the tier idle?"); raise SystemExit(0)

span = (ev[-1][0] - ev[0][0]).total_seconds() if ev else 0.0
recv = [t for t, k in ev if k == "recv"]
done = [t for t, k in ev if k == "done"]
spawn = [t for t, k in ev if k == "spawn"]
read = [t for t, k in ev if k == "read"]

def pctl(xs, p):
    xs = sorted(xs)
    return xs[min(int(len(xs) * p), len(xs) - 1)] if xs else float("nan")

thr = len(done) / span if span else 0

print(f"  window {span:.0f}s   spawns={len(spawn)} starts={len(recv)} completions={len(done)} rdumps={len(read)}")
print(f"  throughput           {thr:.2f} jobs/s")
if span:
    print(f"  spawn rate           {len(spawn)/span:.2f}/s      job-start rate {len(recv)/span:.2f}/s")
if warm_size and thr:
    print(f"  slot cycle           {warm_size/thr:.2f}s per job across {warm_size} slots")

if not phase_rows:
    print()
    print("  No `warm_phases` lines in the window. Either the tier served no warm jobs, or the")
    print("  dispatcher image predates blastbox 2d88c70 -- check scripts/deploy_inventory.sh.")
    raise SystemExit(0)

# ORDER of the breakdown is the order of the slot cycle, not sorted by size: reading it top to
# bottom is reading one job's life, and that is what makes a fat phase obvious in context.
ORDER = ["slot_claim", "stage", "go", "guest", "rdump", "validate",
         "seal", "upload", "commit", "release", "purge"]
ok = [r for outcome, r in phase_rows if outcome == "done"]
print()
print(f"  per-phase breakdown over {len(ok)} clean job(s)"
      f"{' (%d non-clean excluded)' % (len(phase_rows) - len(ok)) if len(phase_rows) != len(ok) else ''}")
if not ok:
    print("  every job in the window failed; the phase they died in is the last one on their line.")
    raise SystemExit(0)

tot = [float(r["total"]) for r in ok if "total" in r]
tot_p50 = pctl(tot, 0.50)
for name in ORDER:
    xs = [float(r[name]) for r in ok if name in r]
    if not xs:
        continue
    p50, p95 = pctl(xs, 0.50), pctl(xs, 0.95)
    share = (p50 / tot_p50 * 100) if tot_p50 else 0
    bar = "#" * int(round(share / 4))
    print(f"    {name:<11} p50 {p50:7.3f}s  p95 {p95:7.3f}s  {share:5.1f}%  {bar}")
print(f"    {'TOTAL':<11} p50 {tot_p50:7.3f}s  p95 {pctl(tot, 0.95):7.3f}s")
print()
print("  `guest` is the ONLY phase that is extraction. If the others outweigh it, the engine is")
print("  the wrong thing to tune -- the sandbox around it is the cost.")

# The dispatcher line covers ONE THREAD's view of a job. It does NOT include the time a job
# spent QUEUED before a thread claimed it, so TOTAL p50 is legitimately smaller than the
# warm_size/throughput slot cycle above; the gap between them is queueing, not lost work.
PYEOF

# shellcheck disable=SC2029
ssh -o BatchMode=yes "$HOST" "python3 - '$WINDOW' '$CONTAINER'" <<< "$REMOTE"
