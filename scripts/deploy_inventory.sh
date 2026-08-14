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
#
# Usage:
#   scripts/deploy_inventory.sh                 # default hosts, shallow
#   scripts/deploy_inventory.sh --deep          # also mount rootfs images (needs sudo on node)
#   scripts/deploy_inventory.sh host1 host2
#
# Exit status: 0 clean, 1 drift detected.
set -uo pipefail

DEEP=0
HOSTS=()
for a in "$@"; do
    case "$a" in
        --deep) DEEP=1 ;;
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
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$stack" "$c" "${img:-?}" "${cre:-?}" "${bb:-?}" "${rt:-?}" "${hp:--}" "${hm:--}"
done'

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
    while IFS=$'\t' read -r stack c img cre bb rt hp hm; do
        printf "  %-30s %-22s %-8s %-8s %-10s %s\n" "$c" "$img" "$bb" "$rt" "$cre" "$hm"
    done <<< "$rows"

    # --- drift checks, per stack -------------------------------------------------
    for stack in $(cut -f1 <<< "$rows" | sort -u); do
        srows=$(awk -F'\t' -v s="$stack" '$1==s' <<< "$rows")
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
            warn "$stack: ROOTFS PREDATES IMAGE (rootfs $rootfs_date < image $newest_img) — the FC guest is running OLDER blastbox/redtusk than the host containers. Rebuild the rootfs."
        fi
    done

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
