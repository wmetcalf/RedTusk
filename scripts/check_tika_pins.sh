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
# THREAT MODEL -- read before extending this script.
#
# This gate exists to catch ACCIDENTAL drift: pins edited in one Dockerfile and not the
# others, a pin left behind on a file that no longer clones, a checkout that stops using
# the pin. It is static text analysis, so it tests for the PRESENCE of tokens, never for
# the EFFECT they have. It therefore cannot stop a Dockerfile author who is determined to
# compile a different commit -- git offers unboundedly many ways to move HEAD (reset,
# rebase, merge, cherry-pick, fetch + FETCH_HEAD, applying a patch, editing files
# outright), and enumerating them is a losing game.
#
# The checks below close the accidental cases and the cheap deliberate ones. The sound
# version of "the image really contains the pinned commit" builds the image and reads the
# resulting HEAD; that is a different and much more expensive CI job than a pre-install
# grep, and it belongs beside the image builds, not here.
#
# So: extend this for shapes a careless edit could plausibly produce. Do not try to make
# it adversarial -- that ambition belongs in the build-and-verify job.
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
    # Docker honours the LAST ARG default before the instruction that uses it, so a
    # second declaration would silently drive the build while `head -1` reported the
    # first. Rather than model Docker's resolution order, forbid the ambiguity.
    ndecl="$(grep -cE '^ARG TIKA_FORK_SHA=' "$f" || true)"
    if [ "$ndecl" -gt 1 ]; then
        echo "$f: declares TIKA_FORK_SHA $ndecl times." >&2
        echo "  Docker uses the last declaration before the checkout, so the pin this gate" >&2
        echo "  reports and the pin the build uses can differ. Keep exactly one." >&2
        rc=1
        continue
    fi
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
    # Strip comment lines first. Matching the raw file lets a Dockerfile hardcode the
    # real checkout while keeping an explanatory comment that mentions
    # `checkout "$TIKA_FORK_SHA"` -- the grep hits the prose and the build ignores the pin.
    #
    # Materialised, NOT piped into grep: under `set -o pipefail`, `grep -q` exits at the
    # first match and SIGPIPEs the still-writing sed, so the pipeline reports failure and
    # the check claims the pin is unused on a tree where it plainly is.
    stripped="$(sed 's/[[:space:]]*#.*$//' "$f")"
    # Every revision-setting checkout must use the pin, not merely one of them: a later
    # hardcoded `git checkout <other>` overrides an earlier pinned one, and the compiled
    # revision is the LAST one to win.
    #
    # Matching is anchored on a command boundary (start of line, &&, ;, |) and must be a
    # real `git ... checkout` COMMAND, so text that merely contains the words -- e.g.
    # `echo checkout "$TIKA_FORK_SHA"` logging the intent -- does not qualify.
    # Split on shell command separators FIRST so each command is judged on its own. A
    # line-oriented grep returns the whole physical line, so two checkouts sharing one
    # RUN line would pass as long as either mentioned the pin -- while the last one
    # still decides the build.
    # Normalise the RUN prefix (and any --mount=... flags) before splitting: a checkout
    # opening its own instruction reads as `RUN git ... checkout`, whose first token is
    # RUN, not git. That is ordinary Dockerfile authoring, not evasion, so missing it
    # would leave the gate blind to the most natural way to add an overriding checkout.
    commands="$(sed -E 's/^[[:space:]]*RUN([[:space:]]+--[^[:space:]]+)*[[:space:]]+/ /' <<<"$stripped" \
                | sed -E 's/(\&\&|\|\||;|\|)/\n/g')"
    checkouts="$(grep -E '^[[:space:]]*git[[:space:]][^|&;]*checkout' <<<"$commands" || true)"
    # Commands that move HEAD without a checkout, scoped to the tika worktree so an
    # unrelated `git reset` elsewhere in the file is not swept up.
    #
    # "Scoped" cannot mean "the command text mentions /src/tika". A git command reaches
    # that worktree two ways, and only one of them names it:
    #
    #     RUN git -C /src/tika reset --hard HEAD^     <- names it
    #     RUN cd /src/tika && git reset --hard HEAD^  <- does NOT, after splitting on &&
    #
    # The second is not evasion, it is how all four of these Dockerfiles already invoke
    # maven (`RUN cd /src/tika && mvn install`), so appending a reset to that existing
    # block is precisely the careless edit this gate is for -- and it exited 0. WORKDIR
    # has the same effect across whole instructions. So track the effective directory:
    # WORKDIR sets it for the rest of the file, a `cd` sets it for the rest of ITS RUN
    # (each RUN starts a fresh shell, so the cd does not carry to the next instruction).
    moved="$(awk '
        # Collapse . and .. so `cd /src/tika/../tika` and `WORKDIR /src` + `WORKDIR tika`
        # both land on the same answer as the shell would give.
        function normpath(pth,   parts, n, i, out, k) {
            gsub(/\/+/, "/", pth)
            n = split(pth, parts, "/")
            k = 0
            for (i = 1; i <= n; i++) {
                if (parts[i] == "" || parts[i] == ".") continue
                if (parts[i] == "..") { if (k > 0) k--; continue }
                out[++k] = parts[i]
            }
            pth = ""
            for (i = 1; i <= k; i++) pth = pth "/" out[i]
            return (pth == "") ? "/" : pth
        }
        function unquote(v) { gsub(/["\x27]/, "", v); return v }
        # Docker expands build variables in WORKDIR, so `ENV ROOT=/src` + `WORKDIR
        # $ROOT/tika` really is the Tika worktree. Recorded literally, it read as
        # `/$ROOT/tika` -- outside Tika -- and the gate passed.
        function expand(v, tbl,   out, i, c, rest, name, j, ch) {
            # Written as an explicit scan rather than gsub: a gsub replacement cannot
            # express "the value, and then whatever character terminated the name"
            # without `&`, which re-inserts the WHOLE match -- that produced
            # `/src$ROOT/tika` from `$ROOT/tika` and the case it was written for still
            # slipped through.
            out = ""; i = 1
            while (i <= length(v)) {
                c = substr(v, i, 1)
                if (c == "$") {
                    rest = substr(v, i + 1)
                    if (substr(rest, 1, 1) == "{") {
                        j = index(rest, "}")
                        if (j > 0) {
                            name = substr(rest, 2, j - 2)
                            if (name in tbl) { out = out tbl[name]; i += 1 + j; continue }
                        }
                    } else {
                        name = ""; j = 1
                        while (j <= length(rest)) {
                            ch = substr(rest, j, 1)
                            if (ch ~ /[A-Za-z0-9_]/) { name = name ch; j++ } else break
                        }
                        if (name != "" && (name in tbl)) {
                            out = out tbl[name]; i += 1 + length(name); continue
                        }
                    }
                }
                out = out c; i++
            }
            return out
        }
        # A directory still holding an unresolved variable is UNKNOWN, and a gate treats
        # unknown as in-scope. Failing closed costs a false alarm a human can read; failing
        # open is the silent acceptance this whole script exists to prevent.
        function scoped(dir) {
            if (dir ~ /\$/) return 1
            return dir == TIKA || index(dir, TIKA "/") == 1
        }
        # ENV/ARG are per-STAGE in Docker. One global map let a later unrelated stage
        # overwrite a value that a derived stage should still see, so a WORKDIR built
        # from it resolved outside the worktree and a real reset was accepted.
        function envsave(   k, out) {
            out = ""
            for (k in envval) out = out k SUBSEP envval[k] RS
            return out
        }
        function envload(blob,   n, rows, i, kv) {
            delete envval
            n = split(blob, rows, RS)
            for (i = 1; i <= n; i++) {
                if (rows[i] == "") continue
                split(rows[i], kv, SUBSEP)
                envval[kv[1]] = kv[2]
            }
        }
        BEGIN { TIKA = "/src/tika"; workdir = "/"; stage = ""; seen_from = 0
                SEPCH = sprintf("%c", 1); cwdalt = "" }
        { line = $0 }
        line ~ /^[[:space:]]*(ENV|ARG)[[:space:]]/ {
            e = line
            sub(/^[[:space:]]*(ENV|ARG)[[:space:]]+/, "", e)
            ne = split(e, ev, /[[:space:]]+/)
            for (i = 1; i <= ne; i++) {
                if (split(ev[i], kv, "=") == 2 && kv[1] != "") {
                    envval[kv[1]] = expand(unquote(kv[2]), envval)
                    # ARGs BEFORE the first FROM are global and, per Docker, usable in
                    # FROM itself. The per-stage reset below must not erase them.
                    if (!seen_from) globalarg[kv[1]] = envval[kv[1]]
                }
            }
            if (stage != "") stage_env[stage] = envsave()
            next
        }
        # A new stage starts at its BASE stage`s working directory when that base is one
        # of this file`s own stages -- Docker inherits it -- and at / otherwise.
        line ~ /^[[:space:]]*FROM[[:space:]]/ {
            hdr = line
            sub(/^[[:space:]]*FROM[[:space:]]+/, "", hdr)
            nf = split(hdr, ft, /[[:space:]]+/)
            # `FROM --platform=$BUILDPLATFORM base AS name` is the standard form, so the
            # base is the first NON-FLAG token. Taking ft[1] blindly read the flag as the
            # base, found it in no stage, and silently reset the inherited directory to /.
            b = 1
            while (b <= nf && ft[b] ~ /^--/) b++
            # EXPANDED: `ARG B=tika` + `FROM $B AS later` is how a build parameterises
            # its base, and the literal `$B` matches no stage, silently resetting the
            # inherited directory to /.
            seen_from = 1
            base = expand(unquote(ft[b]), globalarg); stage = ""
            for (i = b + 1; i <= nf; i++) if (tolower(ft[i]) == "as" && i < nf) stage = unquote(ft[i+1])
            workdir = (base in stage_wd) ? stage_wd[base] : "/"
            envload((base in stage_env) ? stage_env[base] : "")
            if (stage != "") { stage_wd[stage] = workdir; stage_env[stage] = envsave() }
            next
        }
        line ~ /^[[:space:]]*WORKDIR[[:space:]]/ {
            sub(/^[[:space:]]*WORKDIR[[:space:]]+/, "", line)
            line = expand(unquote(line), envval); sub(/[[:space:]]+$/, "", line)
            # RELATIVE WORKDIR resolves against the one in force, not against /.
            workdir = (line ~ /\$/) ? line : normpath((line ~ /^\//) ? line : workdir "/" line)
            if (stage != "") { stage_wd[stage] = workdir; stage_env[stage] = envsave() }
            next
        }
        line ~ /^[[:space:]]*RUN[[:space:]]/ || cont {
            # Each RUN starts a fresh shell at the current WORKDIR, so a `cd` in one
            # instruction does not carry into the next.
            if (!cont) { cwd = workdir; cwdalt = "" }
            cont = (line ~ /\\[[:space:]]*$/)
            sub(/^[[:space:]]*RUN([[:space:]]+--[^[:space:]]+)*[[:space:]]+/, "", line)
            sub(/\\[[:space:]]*$/, "", line)
            # A single `|` is a command boundary as much as `&&`. The sed this awk
            # replaced split on it; dropping it left `cat x.patch | git -C /src/tika
            # apply` as ONE segment starting with `cat`, so the git test skipped it.
            #
            # The SEPARATOR is kept, not just the boundary, because only `&&` proves the
            # command before it succeeded. After `cd /missing || git reset`, the shell is
            # still where it started and the reset runs THERE -- modelling the cd as
            # having happened moved the scope to /missing and let it through.
            tmp = line
            gsub(/\|\|/, SEPCH "O", tmp)      # OR first: leaves no stray | behind
            gsub(/&&/,   SEPCH "A", tmp)
            gsub(/;/,    SEPCH "S", tmp)
            gsub(/\|/,   SEPCH "P", tmp)
            n = split(tmp, seg, SEPCH)
            for (i = 1; i <= n; i++) {
                cmd = seg[i]
                if (i > 1) cmd = substr(cmd, 2)      # drop the separator code
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", cmd)
                if (cmd ~ /^cd[[:space:]]/) {
                    d = cmd; sub(/^cd[[:space:]]+/, "", d)
                    d = expand(unquote(d), envval); sub(/[[:space:]].*$/, "", d)
                    prev = cwd
                    cwd = (d ~ /\$/) ? d : normpath((d ~ /^\//) ? d : cwd "/" d)
                    # Only `&&` on the FOLLOWING boundary proves the cd succeeded. Under
                    # any other separator the old directory is still reachable, so it is
                    # kept as an alternative scope rather than discarded.
                    if (i < n && substr(seg[i+1], 1, 1) == "A") cwdalt = ""
                    else if (cwdalt == "") cwdalt = prev
                    continue
                }
                if (cmd !~ /^git[[:space:]]/) continue
                if (cmd !~ /[[:space:]](reset|rebase|merge|cherry-pick|revert|am|apply|pull|switch|restore|sparse-checkout)([[:space:]]|$)/) continue
                # `-C` names the worktree explicitly; otherwise the shell cwd decides.
                # Compared UNQUOTED: `git -C "/src/tika"` is the ordinary written form,
                # and requiring a bare path there silently un-scoped it.
                # git -C: "Run as if git was started in <path> instead of the current
                # working directory". So when it is present it DECIDES -- falling through
                # to the shell cwd flagged `cd /src/tika && git -C /src/other reset`, a
                # legitimate operation on a different repository (codex).
                # EVERY -C, in order. git(1): with multiple -C options, each subsequent
                # relative path is interpreted against the preceding one, so reading only
                # the first put `git -C /src -C tika reset` in /src rather than /src/tika.
                # Scanned only up to the SUBCOMMAND, because -C is a main-command option
                # and later arguments can carry an unrelated -C.
                bare = expand(unquote(cmd), envval)
                nt = split(bare, tok, /[[:space:]]+/)
                tgt = cwd; seen_c = 0; wt = ""; gd = ""
                for (t = 2; t <= nt; t++) {
                    o = tok[t]
                    if (o == "-C" && t < nt) {
                        arg = tok[++t]; seen_c = 1
                        tgt = (arg ~ /\$/) ? arg : normpath((arg ~ /^\//) ? arg : tgt "/" arg)
                    } else if (o ~ /^-C./) {
                        arg = substr(o, 3); seen_c = 1      # attached form: -C<path>
                        tgt = (arg ~ /\$/) ? arg : normpath((arg ~ /^\//) ? arg : tgt "/" arg)
                    } else if (o ~ /^--work-tree=/) {
                        wt = substr(o, 13)
                    } else if (o == "--work-tree" && t < nt) {
                        wt = tok[++t]
                    } else if (o ~ /^--git-dir=/) {
                        gd = substr(o, 11)
                    } else if (o == "--git-dir" && t < nt) {
                        gd = tok[++t]
                    } else if (o ~ /^(-c|--namespace|--super-prefix|--config-env|--exec-path)$/ && t < nt) {
                        # These take a SEPARATE operand. `git -c advice.x=false -C /src/tika
                        # reset` is ordinary, and reading the operand as the subcommand
                        # stopped the scan before the -C ever came into view.
                        t++
                    } else if (o ~ /^-/) {
                        continue
                    } else {
                        break   # the subcommand: stop reading main-command options
                    }
                }
                # git(1) documents --work-tree/--git-dir as top-level options, and
                # `git --git-dir=/src/tika/.git --work-tree=/src/tika reset` really does
                # reset that checkout from anywhere. --work-tree names the tree being
                # changed, so it wins; a bare --git-dir implies the tree beside it.
                if (wt != "") {
                    tgt = (wt ~ /\$/) ? wt : normpath((wt ~ /^\//) ? wt : tgt "/" wt)
                    seen_c = 1
                } else if (gd != "") {
                    if (gd !~ /\$/) { sub(/\/\.git\/?$/, "", gd) }
                    tgt = (gd ~ /\$/) ? gd : normpath((gd ~ /^\//) ? gd : tgt "/" gd)
                    seen_c = 1
                }
                # DEFENCE IN DEPTH, and the reason it is here: this parser replaced a
                # one-line text scan that asked only "does the command name the
                # worktree?". The parser gains the cases where nothing names it -- a cd,
                # a WORKDIR -- and it independently LOST four that the text scan caught,
                # each time silently and each time found by review rather than by CI: a
                # pipe boundary, `-c <name>=<value>` eating the scan, --work-tree/--git-dir,
                # and the attached `-C<path>`. Enumerating the git option grammar correctly
                # is not a thing to be confident about, so the two are UNIONED: whatever
                # the parser concludes, a HEAD-moving command that mentions the worktree
                # is still reported. That makes this strictly at least as strong as what
                # it replaced, structurally rather than by my remembering to check.
                if (index(bare, TIKA) > 0) { print cmd; continue }
                if (seen_c) { if (scoped(tgt)) print cmd; continue }
                if (scoped(cwd) || (cwdalt != "" && scoped(cwdalt))) print cmd
            }
        }
    ' <<<"$stripped" || true)"
    if [ -n "$moved" ]; then
        echo "$f: moves the Tika worktree's HEAD outside the pinned checkout:" >&2
        while IFS= read -r line; do
            [ -n "$line" ] && echo "    ${line#"${line%%[![:space:]]*}"}" >&2
        done <<<"$moved"
        echo "  The compiled revision would not be the pinned one." >&2
        rc=1
    fi

    if [ -z "$checkouts" ]; then
        echo "$f: clones the Tika fork but never checks out a revision." >&2
        rc=1
    else
        # Match an exact expansion of TIKA_FORK_SHA. A substring test also accepts
        # `$ALT_TIKA_FORK_SHA` / `$TIKA_FORK_SHA_OLD`, which are different variables
        # holding different commits.
        unpinned="$(grep -vE '\$\{?TIKA_FORK_SHA\}?([^A-Za-z0-9_]|$)' <<<"$checkouts" || true)"
        if [ -n "$unpinned" ]; then
            echo "$f: has a git checkout that does not use TIKA_FORK_SHA:" >&2
            while IFS= read -r line; do
                [ -n "$line" ] && echo "    ${line#"${line%%[![:space:]]*}"}" >&2
            done <<<"$unpinned"
            echo "  The LAST checkout wins, so an unpinned one silently decides the build." >&2
            rc=1
        fi
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
