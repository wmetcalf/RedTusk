#!/usr/bin/env bash
# Report what is ACTUALLY deployed on each fleet node, and flag drift between the
# artifacts that must move together.
#
# Written because "what is deployed where" was not knowable by inspection. Three
# traps this exists to catch, all of which were live when it was written:
#
#   1. A stack running MIXED images (api on one build, a dispatcher on another).
#   2. Version skew WITHIN a stack (api on blastbox 0.1.17, dispatchers on 0.1.24).
#   3. The big one: the FC rootfs is a SECOND, independent copy of blastbox+redtusk.
#      Rebuilding the container image does not touch it. A rootfs older than the
#      running image means the guest is executing older code than the host.
#   4. A dispatcher with NO blob store. It seals results into a LocalBlobStore nobody
#      else reads, so its jobs reach DONE and their results 404 from the API -- green
#      status, no error, no log line. Live on this fleet for the gvisor and cold tiers
#      until 2026-08-18: 17,617 completed jobs with unfetchable, unrecoverable results.
#   5. The node's compose files drifting from the repo's. /home/coz/redtusk-bb is not a
#      git checkout, which is precisely why #4 stayed invisible for months.
#
# Usage:
#   scripts/deploy_inventory.sh                 # default hosts, shallow
#   scripts/deploy_inventory.sh --deep          # also mount rootfs images (needs sudo on node)
#   scripts/deploy_inventory.sh host1 host2
#   scripts/deploy_inventory.sh --self-test     # prove the drift checks actually fire
#
# Exit status: 0 clean, 1 drift detected.
set -uo pipefail

DEEP=0
HOSTS=()
for a in "$@"; do
    case "$a" in
        --deep) DEEP=1 ;;
        --self-test) SELFTEST=1 ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) HOSTS+=("$a") ;;
    esac
done
[ ${#HOSTS[@]} -eq 0 ] && read -r -a HOSTS <<< "${BLASTBOX_FLEET_HOSTS:-172.18.101.15}"

SSH="ssh -o BatchMode=yes -o ConnectTimeout=8"
DRIFT=0
warn() { printf '  !! %s\n' "$*"; DRIFT=1; }

# Remote probe: one TSV row per blastbox container.
# stack \t container \t image \t image_created \t blastbox \t redtusk \t rootfs_host \t rootfs_mtime
REMOTE='
for c in $(docker ps --format "{{.Names}}" | grep -E -- "-bb-(api|dispatcher)" ); do
  stack=${c%%-bb-*}
  img=$(docker inspect "$c" --format "{{.Config.Image}}" 2>/dev/null)
  cre=$(docker inspect "$c" --format "{{.Created}}" 2>/dev/null | cut -c1-10)
  bb=$(docker exec "$c" sh -c "/opt/redtusk/bin/pip show blastbox 2>/dev/null || pip show blastbox 2>/dev/null" 2>/dev/null | awk "/^Version:/{print \$2}")
  rt=$(docker exec "$c" sh -c "/opt/redtusk/bin/pip show redtusk 2>/dev/null || pip show redtusk 2>/dev/null" 2>/dev/null | awk "/^Version:/{print \$2}")
  rootfs=$(docker exec "$c" printenv BLASTBOX_FC_ROOTFS 2>/dev/null)
  hp=""; hm=""
  if [ -n "$rootfs" ]; then
    d=$(dirname "$rootfs")
    src=$(docker inspect "$c" --format "{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}" 2>/dev/null | tr " " "\n" | awk -F: -v d="$d" "\$2==d {print \$1}" | head -1)
    [ -n "$src" ] && hp="$src/$(basename "$rootfs")" && hm=$(date -r "$hp" +%F 2>/dev/null)
  fi
  blob=$(docker exec "$c" printenv BLASTBOX_BLOB_URL 2>/dev/null)
  cfg=$(docker inspect "$c" --format "{{index .Config.Labels \"com.docker.compose.project.config_files\"}}" 2>/dev/null)
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$stack" "$c" "${img:-?}" "${cre:-?}" "${bb:-?}" "${rt:-?}" "${hp:--}" "${hm:--}" "${blob:--}" "${cfg:--}"
done'

# Drift checks over a rows TSV. A pure function of its input -- no ssh, no docker -- which is
# what makes --self-test possible. A check nobody has ever seen fire is a check you do not have.
check_rows() {
    local ROWS="$1"
    for stack in $(cut -f1 <<< "$ROWS" | sort -u); do
        srows=$(awk -F'\t' -v s="$stack" '$1==s' <<< "$ROWS")
        imgs=$(cut -f3 <<< "$srows" | sort -u)
        bbs=$(cut -f5 <<< "$srows" | sort -u | grep -v '^?$')
        [ "$(wc -l <<< "$imgs")" -gt 1 ] && \
            warn "$stack: MIXED IMAGES — $(tr '\n' ' ' <<< "$imgs"). One stack should run one build."
        [ -n "$bbs" ] && [ "$(wc -l <<< "$bbs")" -gt 1 ] && \
            warn "$stack: blastbox VERSION SKEW — $(tr '\n' ' ' <<< "$bbs")"
        # rootfs vs image recency: the guest carries its own blastbox+redtusk copy.
        newest_img=$(cut -f4 <<< "$srows" | sort -r | head -1)
        rootfs_date=$(cut -f8 <<< "$srows" | grep -v '^-$' | sort -r | head -1)
        if [ -n "$rootfs_date" ] && [ "$rootfs_date" \< "$newest_img" ]; then
            warn "$stack: ROOTFS PREDATES IMAGE (rootfs $rootfs_date < image $newest_img) — the FC guest is running OLDER blastbox/redtusk than the host containers. Rebuild it IF the change touched guest code (blastbox/worker/*, src/redtusk/*, worker_jvm/); a host-only change (blastbox/host/*) does not reach the guest and this is expected until the next engine bump. Deliberately date-based: it cannot tell which, and under-warning here is how a guest ran two-week-old code unnoticed."
        fi

        # Blob-store coverage. A dispatcher without one seals results where nothing else
        # looks: DONE jobs whose results 404, with no error anywhere. All-local (every
        # container unset) is a legitimate single-node mode; a MIX never is.
        blobs=$(cut -f9 <<< "$srows" | sort -u)
        set_n=$(cut -f9 <<< "$srows" | grep -vc '^-$')
        tot_n=$(wc -l <<< "$srows")
        if [ "$set_n" -gt 0 ] && [ "$set_n" -lt "$tot_n" ]; then
            missing=$(awk -F'\t' '$9=="-"{printf "%s ", $2}' <<< "$srows")
            warn "$stack: NO BLOB STORE on ${missing}— these seal results into a local store the API never reads, so their jobs go DONE and the results 404. Add BLASTBOX_BLOB_URL to their compose service (dispatchers use the http://minio:9000 ALIAS; they have no egress route)."
        elif [ "$set_n" -gt 0 ] && [ "$(grep -vc '^-$' <<< "$blobs")" -gt 1 ]; then
            warn "$stack: BLOB STORE DISAGREEMENT — $(tr '\n' ' ' <<< "$blobs"). One stack must share one bucket or results land where the API does not look."
        fi
    done

}

# --- self-test ------------------------------------------------------------------
# Every check here exists because the thing it detects was LIVE on this fleet. A check that
# has never been seen to fire is a check you do not have, so each one gets a fixture that
# makes it fire and a fixture that must keep it quiet.
#
# Fields: stack c img img_built bb rt rootfs_path rootfs_built blob_url compose_cfgs
if [ "${SELFTEST:-0}" -eq 1 ]; then
    fails=0
    t() {  # t <name> <expect-substring|CLEAN> <rows...>
        local name="$1" expect="$2"; shift 2
        local rows out
        rows=$(printf '%s\n' "$@")
        # NB: this is a command substitution, so DRIFT is set in a SUBSHELL and never comes
        # back. The captured warn output is the assertion; do not add a DRIFT check here
        # expecting it to mean anything.
        out=$(check_rows "$rows")
        if [ "$expect" = "CLEAN" ]; then
            if [ -z "$out" ]; then echo "  ok   $name"
            else echo "  FAIL $name — expected no warning, got: $out"; fails=$((fails+1)); fi
        else
            if grep -qF -- "$expect" <<< "$out"; then echo "  ok   $name"
            else echo "  FAIL $name — expected '$expect', got: ${out:-<nothing>}"; fails=$((fails+1)); fi
        fi
    }
    R() { printf 'redtusk\t%s\t%s\t2026-08-18\t0.1.26\t0.1.0\t%s\t%s\t%s\t/c/docker-compose.yml' "$@"; }
    #     container                image            rootfs_path rootfs_built blob

    echo "check_rows self-test"
    # THE BUG THIS WAS WRITTEN FOR: gvisor/cold had no blob store while the api had one.
    t "missing blob store is caught" "NO BLOB STORE" \
        "$(R api          redtusk:x - - s3://blastbox/redtusk)" \
        "$(R dispatcher-fc redtusk:x - - s3://blastbox/redtusk)" \
        "$(R dispatcher-gv redtusk:x - - -)"
    # ...and it must NAME the offender, or the operator cannot act on it.
    t "and it names the container" "dispatcher-gv" \
        "$(R api          redtusk:x - - s3://blastbox/redtusk)" \
        "$(R dispatcher-gv redtusk:x - - -)"
    # A stack with NO blob store anywhere is legitimate single-node local mode.
    t "all-local is not drift" CLEAN \
        "$(R api          redtusk:x - - -)" \
        "$(R dispatcher-fc redtusk:x - - -)"
    # A consistent stack is quiet.
    t "consistent blob config is quiet" CLEAN \
        "$(R api          redtusk:x - - s3://blastbox/redtusk)" \
        "$(R dispatcher-fc redtusk:x - - s3://blastbox/redtusk)"
    # Two buckets in one stack: results land where the API does not look.
    t "disagreeing buckets are caught" "BLOB STORE DISAGREEMENT" \
        "$(R api          redtusk:x - - s3://blastbox/redtusk)" \
        "$(R dispatcher-fc redtusk:x - - s3://other/redtusk)"
    # The pre-existing checks, so a refactor of this function cannot quietly drop them.
    t "mixed images still caught" "MIXED IMAGES" \
        "$(R api redtusk:a - - -)" "$(R dispatcher-fc redtusk:b - - -)"
    t "rootfs older than image still caught" "ROOTFS PREDATES IMAGE" \
        "$(R dispatcher-fc redtusk:x /f.ext4 2026-08-01 -)"
    t "rootfs newer than image is quiet" CLEAN \
        "$(R dispatcher-fc redtusk:x /f.ext4 2026-08-19 -)"

    # The exit code contract. check_rows is called DIRECTLY (not in a command substitution) on
    # the real path, which is the only reason warn's DRIFT=1 reaches the caller and the script
    # exits 1. Wrapping that call in $( ) later would still print every warning and still exit
    # 0 -- a CI gate that reports drift and passes. Pin it.
    DRIFT=0
    check_rows "$(R dispatcher-fc redtusk:a - - -)
$(R api redtusk:b - - -)" >/dev/null
    if [ "$DRIFT" -eq 1 ]; then echo "  ok   drift sets the exit status"
    else echo "  FAIL drift sets the exit status — warnings printed but the script would exit 0"; fails=$((fails+1)); fi

    echo
    [ "$fails" -gt 0 ] && { echo "SELFTEST: $fails failure(s)"; exit 1; }
    echo "SELFTEST: all checks fire when they should and stay quiet when they should"
    exit 0
fi

for H in "${HOSTS[@]}"; do
    echo
    echo "================ $H ================"
    if ! $SSH "$H" true 2>/dev/null; then
        warn "UNREACHABLE — a node that is down is fleet capacity you do not have"
        continue
    fi

    rows=$($SSH "$H" "$REMOTE" 2>/dev/null)
    [ -z "$rows" ] && { echo "  (no blastbox containers)"; continue; }

    printf "  %-30s %-22s %-8s %-8s %-10s %s\n" CONTAINER IMAGE BLASTBOX REDTUSK IMG_BUILT ROOTFS_BUILT
    while IFS=$'\t' read -r stack c img cre bb rt hp hm blob cfg; do
        printf "  %-30s %-22s %-8s %-8s %-10s %s\n" "$c" "$img" "$bb" "$rt" "$cre" "$hm"
    done <<< "$rows"

    check_rows "$rows"

    # --- compose files vs the repo -------------------------------------------------
    # The node's deploy dir is not a git checkout, so it drifts silently and the drift is
    # invisible until an end-to-end job fails. Compare by hash; report which files differ.
    repo_compose="$(cd "$(dirname "$0")/../deploy/docker" 2>/dev/null && pwd)"
    if [ -n "$repo_compose" ]; then
        node_cfgs=$(awk -F'\t' '$1=="redtusk" && $10!="-"{print $10}' <<< "$rows" | tr ',' '\n' | sort -u)
        for f in $node_cfgs; do
            base=$(basename "$f")
            [ -f "$repo_compose/$base" ] || continue
            nsum=$($SSH "$H" "sha256sum '$f' 2>/dev/null | cut -d' ' -f1")
            rsum=$(sha256sum "$repo_compose/$base" | cut -d' ' -f1)
            [ -z "$nsum" ] && continue
            if [ "$nsum" != "$rsum" ]; then
                warn "COMPOSE DRIFT: $base on the node differs from the repo's deploy/docker/$base. Diff them before trusting either: ssh $H cat $f | diff $repo_compose/$base -"
            fi
        done
    fi

    # Sibling rootfs images: only one is live; the rest are traps for the next reader.
    for d in $(cut -f7 <<< "$rows" | grep -v '^-$' | xargs -r -n1 dirname | sort -u); do
        n=$($SSH "$H" "ls -1 $d/*.ext4 2>/dev/null | wc -l")
        [ "${n:-0}" -gt 1 ] && echo "  note: $n .ext4 images in $d — only the one listed above is live"
    done

    if [ "$DEEP" -eq 1 ]; then
        echo "  -- rootfs contents [deep]"
        for hp in $(cut -f7 <<< "$rows" | grep -v '^-$' | sort -u); do
            out=$($SSH "$H" "
              mp=\$(mktemp -d)
              sudo -n mount -o ro,loop '$hp' \"\$mp\" 2>/dev/null || { echo '    (cannot mount; sudo required on node)'; exit 0; }
              jar=\"\$mp/app/redtusk-worker.jar\"; aot=\"\$mp/app/redtusk.aot\"
              echo \"    engine=\$(cat \$mp/opt/blastbox/engine 2>/dev/null || echo UNSET)\"
              [ -f \"\$jar\" ] && echo \"    jar sha=\$(sudo -n sha256sum \"\$jar\" | cut -c1-12) mtime=\$(date -r \"\$jar\" +%F)\" || echo '    jar MISSING'
              if [ -f \"\$aot\" ]; then
                echo \"    aot mtime=\$(date -r \"\$aot\" +%F)\"
                [ \"\$aot\" -ot \"\$jar\" ] && echo '    STALE_AOT'
              else echo '    aot MISSING'; fi
              sudo -n umount \"\$mp\" 2>/dev/null; rmdir \"\$mp\" 2>/dev/null" 2>/dev/null)
            echo "  $hp"; echo "$out" | grep -v STALE_AOT
            grep -q STALE_AOT <<< "$out" && \
                warn "STALE AOT in $hp — the cache is generated FROM the jar and is flag/classpath sensitive; an older cache fails to map ('Unable to map shared spaces') and silently costs startup on every job. Regenerate with the image build."
        done
    fi
done

echo
[ "$DRIFT" -eq 1 ] && { echo "RESULT: drift detected (see !! lines)"; exit 1; }
echo "RESULT: no drift detected"
