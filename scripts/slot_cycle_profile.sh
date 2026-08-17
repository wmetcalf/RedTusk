#!/usr/bin/env bash
# Break a warm-tier job down into slot-lifecycle phases, from the dispatcher's own logs.
#
# Why this exists: throughput on a disposable-slot tier is  slots / slot_cycle_time, NOT
# 1 / engine_time. Measured on toolz2: 24 slots sustain ~1.9-2.6 jobs/s, i.e. a slot cycle of
# ~10-12s per job, while a single job against an IDLE tier completes end-to-end in <1s. So most
# of the cycle is everything EXCEPT extraction (restore, readiness, dispatch, seal, outdisk read,
# upload, reap, respawn) -- tuning the engine there is nearly free of effect.
#
# It reports RATES only, on purpose. Attributing that cycle to phases needs a correlation id the
# guest logs do not currently carry; see the note in the body. Do not reintroduce order-paired
# durations -- they silently compare different jobs under concurrency.
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

ev, warm_size = [], None
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
    if "warm_pool_built" in line:
        w = re.search(r"warm_size=(\d+)", line)
        if w: warm_size = int(w.group(1))
ev.sort()
if len(ev) < 8:
    print("  not enough events in the window — is the tier idle?"); raise SystemExit(0)

span = (ev[-1][0] - ev[0][0]).total_seconds()
recv = [t for t, k in ev if k == "recv"]
done = [t for t, k in ev if k == "done"]
spawn = [t for t, k in ev if k == "spawn"]
read = [t for t, k in ev if k == "read"]

def pctl(xs, p):
    xs = sorted(xs)
    return xs[min(int(len(xs) * p), len(xs) - 1)] if xs else float("nan")

# RATES ONLY. Per-job durations are deliberately NOT reported here.
#
# The guest's `job_received` and `serve_warm returned` lines carry NO correlation id (only
# `outdisk_read` has slot_id), and with N concurrent slots completions do not occur in start
# order -- so pairing the k-th receive with the k-th completion pairs DIFFERENT JOBS. That method
# produced 0.67s and 5.48s for the same tier minutes apart, which is how you can tell it is
# measuring nothing. Anything derived from it (in-guest p50, utilisation, "% of slot time that is
# not extraction") is unreliable and has been removed rather than left to mislead.
#
# To get honest per-phase numbers, add a job_id/slot_id to those two guest log lines (or emit
# host-side per-phase timings keyed by job_id in dispatch.py) and pair on the id.
thr = len(done) / span if span else 0

print(f"  window {span:.0f}s   spawns={len(spawn)} starts={len(recv)} completions={len(done)} rdumps={len(read)}")
print(f"  throughput           {thr:.2f} jobs/s")
print(f"  spawn rate           {len(spawn)/span:.2f}/s      job-start rate {len(recv)/span:.2f}/s")
if warm_size:
    print(f"  slot cycle           {warm_size/thr:.2f}s per job across {warm_size} slots")
print()
print("  Per-job phase durations are NOT shown: the guest log lines have no correlation id, and")
print("  under concurrency order-pairing compares different jobs. Add an id to job_received /")
print("  serve_warm (or instrument dispatch.py per phase) before trusting any phase breakdown.")
print("  A single job submitted against an IDLE tier is the one duration you can trust today.")
PYEOF

# shellcheck disable=SC2029
ssh -o BatchMode=yes "$HOST" "python3 - '$WINDOW' '$CONTAINER'" <<< "$REMOTE"
