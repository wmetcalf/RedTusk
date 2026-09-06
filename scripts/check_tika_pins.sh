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

# Dockerfile INSTRUCTION names are case-insensitive; a build ARG NAME is not. So the
# keyword is matched either way and TIKA_FORK_SHA is matched exactly -- `arg tika_fork_sha=`
# declares a different variable and must not satisfy the pin. Requiring uppercase ARG here
# rejected a perfectly correct all-lowercase Dockerfile with "declares no full 40-char
# ARG", which is also the wrong reason a lowercase parser test was passing (codex).

mapfile -t cloners < <(grep -rlF "$CLONE_URL" deploy/ | sort)
mapfile -t declarers < <(grep -rlE '^[Aa][Rr][Gg][[:space:]]+TIKA_FORK_SHA=' deploy/ | sort)

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
    ndecl="$(grep -cE '^[Aa][Rr][Gg][[:space:]]+TIKA_FORK_SHA=' "$f" || true)"
    if [ "$ndecl" -gt 1 ]; then
        echo "$f: declares TIKA_FORK_SHA $ndecl times." >&2
        echo "  Docker uses the last declaration before the checkout, so the pin this gate" >&2
        echo "  reports and the pin the build uses can differ. Keep exactly one." >&2
        rc=1
        continue
    fi
    sha="$(grep -oE '^[Aa][Rr][Gg][[:space:]]+TIKA_FORK_SHA=[0-9a-f]{40}' "$f" | head -1 | cut -d= -f2 || true)"
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
    # Quote-AWARE: a bare sed truncated `RUN echo "#"; git reset ...` at the quoted
    # hash, so the real command never reached the scanner at all (codex). Only a `#`
    # outside quotes starts a comment.
    stripped="$(awk '''{
        out = ""; q = ""
        for (i = 1; i <= length($0); i++) {
            c = substr($0, i, 1)
            if (q == "\x27") { out = out c; if (c == q) q = ""; continue }
            if (c == "\\" && q != "" && i < length($0)) { out = out c substr($0, i+1, 1); i++; continue }
            if (q != "") { out = out c; if (c == q) q = ""; continue }
            if (c == "\"" || c == "\x27") { q = c; out = out c; continue }
            if (c == "#") break
            out = out c
        }
        sub(/[[:space:]]+$/, "", out)
        print out
    }''' "$f")"
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
    commands="$(sed -E 's/^[[:space:]]*[Rr][Uu][Nn]([[:space:]]+--[^[:space:]]+)*[[:space:]]+/ /' <<<"$stripped" \
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
        # Separators only count OUTSIDE quotes. An unconditional replacement split
        # inside `echo "recovery: cd /src/tika; git reset --hard HEAD"` and presented the
        # quoted text as a real command, rejecting a Dockerfile that only prints (codex).
        function mark_separators(v,   out, i, c, q, nx) {
            out = ""; q = ""
            for (i = 1; i <= length(v); i++) {
                c = substr(v, i, 1)
                # A backslash escapes the next character, so `echo recovery\; git reset`
                # is ONE echo. Treating the escaped separator as a boundary reported a
                # harmless command (codex).
                # Quote state FIRST: inside single quotes a backslash is literal, so
                # consuming the next character there ate the closing quote and left the
                # scanner stuck in quoted mode, hiding a real separator (codex).
                if (q == "\x27") { out = out c; if (c == q) q = ""; continue }
                if (c == "\\" && i < length(v)) { out = out c substr(v, i + 1, 1); i++; continue }
                if (q != "") { out = out c; if (c == q) q = ""; continue }
                if (c == "\"" || c == "\x27") { q = c; out = out c; continue }
                nx = substr(v, i + 1, 1)
                if (c == "|" && nx == "|") { out = out SEPCH "O"; i++; continue }
                if (c == "&" && nx == "&") { out = out SEPCH "A"; i++; continue }
                if (c == ";")              { out = out SEPCH "S"; continue }
                if (c == "|")              { out = out SEPCH "P"; continue }
                out = out c
            }
            return out
        }
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
        # The shell may be in more than ONE directory at a given command, so the model is
        # a SET rather than a cwd plus a single alternative. Two heuristics on one
        # alternative were each wrong in a different direction; this is the exact
        # dataflow instead. Sets are " a b c " strings -- awk has no set type and the
        # membership test wants delimiters on both sides.
        function sadd(set, d) { if (d == "" || index(set, " " d " ")) return set; return set d " " }
        function sunion(a, b,   n, parts, i, out) {
            out = a; n = split(b, parts, " ")
            for (i = 1; i <= n; i++) out = sadd(out, parts[i])
            return out
        }
        function resolve_all(set, d,   n, parts, i, out) {
            if (d ~ /\$/) return " " d " "
            if (d ~ /^\//) return " " normpath(d) " "
            out = ""; n = split(set, parts, " ")
            for (i = 1; i <= n; i++) out = sadd(out, normpath(parts[i] "/" d))
            return out
        }
        function sscoped(set,   n, parts, i) {
            n = split(set, parts, " ")
            for (i = 1; i <= n; i++) if (scoped(parts[i])) return 1
            return 0
        }
        # ENV/ARG are per-STAGE in Docker. One global map let a later unrelated stage
        # overwrite a value that a derived stage should still see, so a WORKDIR built
        # from it resolved outside the worktree and a real reset was accepted.
        function envsave(   k, out) {
            out = ""
            for (k in envval) out = out k SUBSEP (k in isenv ? 1 : 0) SUBSEP envval[k] RS
            return out
        }
        function envload(blob,   n, rows, i, kv) {
            delete envval; delete isenv
            n = split(blob, rows, RS)
            for (i = 1; i <= n; i++) {
                if (rows[i] == "") continue
                split(rows[i], kv, SUBSEP)
                envval[kv[1]] = kv[3]
                if (kv[2] == "1") isenv[kv[1]] = 1
            }
        }
        # Dockerfile instruction names are CASE-INSENSITIVE; `workdir /src/tika` is
        # valid and was being ignored entirely.
        BEGIN { TIKA = "/src/tika"; workdir = "/"; stage = ""; seen_from = 0
                SEPCH = sprintf("%c", 1) }
        { line = $0 }
        # ENV/ARG continue across `\` exactly as RUN does, and assignments on the
        # continuation belong to the SAME instruction.
        toupper(line) ~ /^[[:space:]]*(ENV|ARG)[[:space:]]/ || econt {
            if (line ~ /\\[[:space:]]*$/) {
                ebuf = (econt ? ebuf " " : "") line
                sub(/\\[[:space:]]*$/, "", ebuf)
                econt = 1
                next
            }
            if (econt) { line = ebuf " " line; econt = 0; ebuf = "" }
            e = line
            isarg = (toupper(line) ~ /^[[:space:]]*ARG[[:space:]]/)
            sub(/^[[:space:]]*([Ee][Nn][Vv]|[Aa][Rr][Gg])[[:space:]]+/, "", e)
            ne = split(e, ev, /[[:space:]]+/)
            # Docker expands EVERY value in one ENV against the environment that existed
            # BEFORE the instruction. Updating as we went made `ENV ROOT=/opt DEST=$ROOT`
            # record DEST=/opt where Docker gives the previous /src.
            delete pre
            for (pk in envval) pre[pk] = envval[pk]
            # Docker still accepts the legacy `ENV <key> <value>` form -- one pair, no
            # `=`. Ignoring it left the PREVIOUS value of that name in force, so a
            # WORKDIR built from it modelled the wrong directory.
            # `ARG NAME` with no default inside a stage IMPORTS the global value.
            # Ignoring it left the name unresolved, the directory unknown, and a
            # perfectly ordinary reset elsewhere convicted (codex).
            if (isarg && ne == 1 && ev[1] !~ /=/) {
                if ((ev[1] in globalarg) && !(ev[1] in isenv)) envval[ev[1]] = globalarg[ev[1]]
                if (stage != "") stage_env[stage] = envsave()
                next
            }
            if (!isarg && ne == 2 && ev[1] !~ /=/) {
                envval[ev[1]] = expand(unquote(ev[2]), pre)
                isenv[ev[1]] = 1
                if (stage != "") stage_env[stage] = envsave()
                next
            }
            for (i = 1; i <= ne; i++) {
                if (split(ev[i], kv, "=") == 2 && kv[1] != "") {
                    # Docker keeps an ENV value even when a later ARG declares the same
                    # name -- ENV wins for variable replacement. One flat map let the ARG
                    # overwrite it, so a WORKDIR built from the name resolved to the ARG
                    # default and the real directory went unseen.
                    if (isarg && (kv[1] in isenv)) continue
                    if (!isarg) isenv[kv[1]] = 1
                    envval[kv[1]] = expand(unquote(kv[2]), pre)
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
        toupper(line) ~ /^[[:space:]]*FROM[[:space:]]/ {
            hdr = line
            sub(/^[[:space:]]*[Ff][Rr][Oo][Mm][[:space:]]+/, "", hdr)
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
        # WORKDIR continues across `\` like every other instruction; recording the
        # first physical line kept `/src/\` and lost the `tika` that followed.
        toupper(line) ~ /^[[:space:]]*WORKDIR[[:space:]]/ || wcont {
            if (line ~ /\\[[:space:]]*$/) {
                wbuf = (wcont ? wbuf : "") line
                sub(/\\[[:space:]]*$/, "", wbuf)
                wcont = 1
                next
            }
            if (wcont) { line = wbuf line; wcont = 0; wbuf = "" }
        }
        toupper(line) ~ /^[[:space:]]*WORKDIR[[:space:]]/ {
            sub(/^[[:space:]]*[Ww][Oo][Rr][Kk][Dd][Ii][Rr][[:space:]]+/, "", line)
            line = expand(unquote(line), envval); sub(/[[:space:]]+$/, "", line)
            # RELATIVE WORKDIR resolves against the one in force, not against /.
            workdir = (line ~ /\$/) ? line : normpath((line ~ /^\//) ? line : workdir "/" line)
            if (stage != "") { stage_wd[stage] = workdir; stage_env[stage] = envsave() }
            next
        }
        toupper(line) ~ /^[[:space:]]*RUN[[:space:]]/ || cont || heredoc {
            # Each RUN starts a fresh shell at the current WORKDIR, so a `cd` in one
            # instruction does not carry into the next.
            #
            # A continued RUN is JOINED first and judged as one command. Judging physical
            # lines meant a `&&` opening a continuation line was invisible while the `cd`
            # before it was processed, so `RUN cd /opt/elsewhere \` + `&& git reset` kept
            # a stale alternative scope and was reported -- a false alarm on ordinary
            # formatting, which is worse than a miss because it gets the gate switched off.
            piece = line
            # EXEC form: `RUN ["git", "reset", "--hard", "HEAD^"]` runs git directly.
            # The parsed segment began with `["git"` and matched no test, so the reset
            # went unseen (codex). Rewritten to the shell form before anything else.
            if (piece ~ /^[[:space:]]*[Rr][Uu][Nn]([[:space:]]+--[^[:space:]]+)*[[:space:]]*\[/) {
                json = piece
                sub(/^[[:space:]]*[Rr][Uu][Nn]([[:space:]]+--[^[:space:]]+)*[[:space:]]*\[/, "", json)
                sub(/\][[:space:]]*$/, "", json)
                gsub(/[\"\x27]/, "", json)
                gsub(/[[:space:]]*,[[:space:]]*/, " ", json)
                piece = "RUN " json
            }
            # `RUN <<EOF` opens a heredoc whose BODY is the script. There is no trailing
            # backslash, so continuation tracking never saw it and every command inside
            # was ignored -- the text scan this parser replaced did catch them.
            # Only a BARE `RUN <<EOF` runs its body as a script. `RUN cat <<EOF` feeds
            # the body to a command as DATA, and scanning it reported generated text --
            # a script or documentation being written out -- as an executed command
            # (codex). What precedes `<<` decides.
            if (!cont && !heredoc && piece ~ /<<-?[\"\x27]?[^[:space:]<>&|;]+/) {
                lead = piece
                sub(/^[[:space:]]*[Rr][Uu][Nn]([[:space:]]+--[^[:space:]]+)*[[:space:]]*/, "", lead)
                if (lead ~ /^<<-?[\"\x27]?[^[:space:]<>&|;]/) {
                    hd = lead
                    hddash = (hd ~ /^<<-/)
                    sub(/^<<-?/, "", hd)
                    sub(/[[:space:]<>&|;].*$/, "", hd)
                    gsub(/[\"\x27]/, "", hd)
                    if (hd != "") { heredoc = hd; hdbuf = ""; S = " " workdir " "; csucc = S; cfail = S; orsucc = ""; andfail = ""; next }
                }
                # A DATA heredoc: skip its body rather than reading it as commands.
                hd = piece
                hddash = (hd ~ /<<-/)
                sub(/^.*<<-?/, "", hd)
                sub(/[[:space:]<>&|;].*$/, "", hd)
                gsub(/[\"\x27]/, "", hd)
                if (hd != "") {
                    heredoc = hd; hdbuf = ""; hdskip = 1
                    if (!cont) { S = " " workdir " "; csucc = S; cfail = S; orsucc = ""; andfail = ""; subdepth = 0 }
                    # The OPENER still carries real commands -- `cat <<EOF >/tmp/x && git
                    # -C /src/tika reset` runs the reset once cat succeeds. Skipping the
                    # whole line lost it. Judge the opener with the heredoc token removed.
                    sub(/<<-?[\"\x27]?[^[:space:]<>&|;]+/, "", piece)
                    line = piece; buf = ""; justopened = 1
                }
            }
            if (heredoc && !justopened) {
                probe = line
                # Only `<<-` strips leading TABS from the terminator. For a plain `<<`,
                # an indented line that looks like the delimiter is BODY -- trimming it
                # closed the heredoc early and hid everything after it.
                if (hddash) sub(/^\t+/, "", probe)
                sub(/[[:space:]]+$/, "", probe)
                gsub(/[\"\x27]/, "", probe)
                if (probe == heredoc) {
                    heredoc = ""
                    if (hdskip) { hdskip = 0; hdbuf = ""; next }
                    line = hdbuf; hdbuf = ""; buf = ""
                } else { hdbuf = hdbuf " ; " line; next }
            } else if (!justopened) {
            if (!cont) {
                S = " " workdir " "; csucc = S; cfail = S; orsucc = ""; andfail = ""; subdepth = 0; buf = ""
                sub(/^[[:space:]]*[Rr][Uu][Nn]([[:space:]]+--[^[:space:]]+)*[[:space:]]+/, "", piece)
            }
            cont = (piece ~ /\\[[:space:]]*$/)
            sub(/\\[[:space:]]*$/, "", piece)
            buf = (buf == "") ? piece : buf " " piece
            if (cont) next
            line = buf
            }
            justopened = 0
            # A single `|` is a command boundary as much as `&&`. The sed this awk
            # replaced split on it; dropping it left `cat x.patch | git -C /src/tika
            # apply` as ONE segment starting with `cat`, so the git test skipped it.
            #
            # The SEPARATOR is kept, not just the boundary, because only `&&` proves the
            # command before it succeeded. After `cd /missing || git reset`, the shell is
            # still where it started and the reset runs THERE -- modelling the cd as
            # having happened moved the scope to /missing and let it through.
            tmp = mark_separators(line)
            n = split(tmp, seg, SEPCH)
            for (i = 1; i <= n; i++) {
                cmd = seg[i]
                sepc = (i > 1) ? substr(cmd, 1, 1) : ""
                if (i > 1) cmd = substr(cmd, 2)      # drop the separator code
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", cmd)
                # `RUN (cd /src/tika && git reset)` is ordinary grouping. The opener made
                # the first segment start with `(cd`, which matched neither test, so the
                # cd was invisible and the git ran against the outer WORKDIR (codex).
                # A subshell does not survive the group, but nothing here reads the cwd
                # after it, so tracking the entry is enough.
                # `RUN (cd X && ...)` is ordinary grouping. The opener leaves the first
                # segment starting with `(cd`, matching neither test below -- but a
                # subshell also CONFINES the cd, and my first version stripped the paren
                # without restoring afterwards, so `(cd /src/tika && echo ok); git reset`
                # carried the worktree past the group and convicted a reset elsewhere
                # (codex). Enter and leave it properly.
                # ONLY parentheses make a subshell. `{ cd X; }` is a brace group and runs
                # in the CURRENT shell, so its cd persists -- restoring there accepted a
                # reset that really had moved (codex). Braces are stepped over without
                # any save or restore.
                while (cmd ~ /^\{[[:space:]]*/) sub(/^\{[[:space:]]*/, "", cmd)
                while (cmd ~ /^\([[:space:]]*/) {
                    if (subdepth == 0) subsaved = S
                    subdepth++
                    sub(/^\([[:space:]]*/, "", cmd)
                }
                subclose = 0
                while (cmd ~ /[[:space:]]*\}$/) sub(/[[:space:]]*\}$/, "", cmd)
                while (cmd ~ /[[:space:]]*\)$/ && subdepth > 0) {
                    sub(/[[:space:]]*\)$/, "", cmd)
                    subdepth--
                    if (subdepth == 0) subclose = 1
                }
                # Which directories the shell can be in HERE, from the previous command
                # and the separator that joined them:
                #   &&  runs on success -- and the previous FAILURE is remembered, because
                #       a later `||` catches it (`cd X && echo ok || git reset`)
                #   ||  runs on failure -- and the previous SUCCESS is remembered, because
                #       the command after the or-list runs if ANY branch succeeded
                #   ; | run unconditionally, so everything outstanding arrives
                if (sepc == "A")      { andfail = sunion(andfail, cfail); S = sunion(csucc, orsucc); orsucc = "" }
                else if (sepc == "O") { orsucc  = sunion(orsucc,  csucc); S = sunion(cfail, andfail); andfail = "" }
                else if (sepc != "")  { S = sunion(sunion(csucc, cfail), sunion(orsucc, andfail)); orsucc = ""; andfail = "" }
                # `exit` ENDS the shell, so nothing after it is reachable by any path.
                # `false` merely returns a status, which is why the two cannot be grouped.
                if (cmd ~ /^exit([[:space:]]|$)/) { csucc = ""; cfail = ""; continue }
                # Any other command leaves the directory alone.
                csucc = S; cfail = S
                if (cmd ~ /^cd([[:space:]]|$)/) {
                    d = cmd; sub(/^cd[[:space:]]*/, "", d)
                    # `cd [-L|[-P [-e]] [-@]] [dir]` -- skip the options and `--`, or the
                    # first one is read as the directory and the real target is lost.
                    while (d ~ /^-/) {
                        if (d ~ /^--([[:space:]]|$)/) { sub(/^--[[:space:]]*/, "", d); break }
                        sub(/^-[^[:space:]]*[[:space:]]*/, "", d)
                    }
                    d = expand(unquote(d), envval); sub(/[[:space:]].*$/, "", d)
                    # A bare `cd` goes to $HOME, not to where we already are. Treating the
                    # empty operand as the current directory kept the shell in the
                    # worktree and convicted a reset that had left it (codex). Docker
                    # builds run as root unless told otherwise, hence the fallback.
                    if (d == "") d = ("HOME" in envval) ? envval["HOME"] : "/root"
                    # On success the shell is in the target; on failure it has not moved.
                    csucc = ""
                    nS = split(S, sp, " ")
                    for (si = 1; si <= nS; si++)
                        csucc = sadd(csucc, (d ~ /\$/) ? d : normpath((d ~ /^\//) ? d : sp[si] "/" d))
                    cfail = S
                    if (subclose) { S = subsaved; csucc = S; cfail = S }
                    continue
                }
                if (subclose) { csucc = subsaved; cfail = subsaved }
                if (cmd !~ /^git[[:space:]]/) continue
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
                # An EMPTY quoted operand has to survive tokenisation. git documents
                # `-C ""` as leaving the current directory unchanged, so it is rewritten
                # to the equivalent `.` BEFORE unquoting -- otherwise the operand vanishes,
                # `-C` swallows the subcommand as its path, and the command is skipped as
                # unrecognised while the reset really runs in the worktree (codex).
                bare = cmd
                gsub(/""|\x27\x27/, ".", bare)
                bare = expand(unquote(bare), envval)
                nt = split(bare, tok, /[[:space:]]+/)
                tgt = ""; seen_c = 0; wt = ""; gd = ""; subcmd = ""; info = 0
                for (t = 2; t <= nt; t++) {
                    o = tok[t]
                    if (o == "-C" && t < nt) {
                        arg = tok[++t]; tgt = resolve_all(seen_c ? tgt : S, arg); seen_c = 1
                    } else if (o ~ /^-C./) {
                        arg = substr(o, 3)                  # attached form: -C<path>
                        tgt = resolve_all(seen_c ? tgt : S, arg); seen_c = 1
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
                    } else if (o ~ /^(-h|--help|-v|--version)$/) {
                        # `git --help reset` DISPLAYS the documentation for reset; the
                        # word after it is a help target, not a subcommand to run.
                        info = 1
                    } else if (o ~ /^-/) {
                        continue
                    } else {
                        subcmd = o   # the subcommand: stop reading main-command options
                        break
                    }
                }
                # The verb must be the SUBCOMMAND. Matching it anywhere in the command
                # rejected `git diff HEAD -- reset`, where `reset` is a pathspec and
                # nothing moves -- a read-only inspection failing the gate (codex).
                # A git command whose SUBCOMMAND could not be identified is UNKNOWN, and
                # unknown fails closed if the scope reaches the worktree. Skipping instead
                # meant any parse failure -- `git -C "" reset`, where the empty operand
                # vanishes and `reset` is eaten as the path -- turned into a silent pass.
                # This is the same rule already applied to unresolved directories.
                # `git --version` / `git --help` legitimately have NO subcommand and are
                # read-only. Only an otherwise-unparseable command fails closed.
                if (info) continue
                if (subcmd == "") {
                    if (sscoped(S)) print cmd
                    continue
                }
                if (subcmd !~ /^(reset|rebase|merge|cherry-pick|revert|am|apply|pull|switch|restore|sparse-checkout)$/) continue
                # git(1) documents --work-tree/--git-dir as top-level options, and
                # `git --git-dir=/src/tika/.git --work-tree=/src/tika reset` really does
                # reset that checkout from anywhere. --work-tree names the tree being
                # changed, so it wins; a bare --git-dir implies the tree beside it.
                # A --git-dir on its own does NOT relocate the worktree: git uses the
                # CURRENT directory. Verified against git 2.43 -- run from checkout A with
                # B/.git, `reset --hard HEAD~1` rewrote the files in A and left B untouched. So
                # scoping such a command to the git-dir accepted a reset that really ran in
                # the worktree the shell was standing in (codex).
                #
                # It is still reported when the GIT-DIR names the pinned repository,
                # because that is whose HEAD the reset moves even while it clobbers files
                # elsewhere. The two effects have different targets and both matter.
                if (gd != "") {
                    gdp = gd
                    if (gdp !~ /\$/) sub(/\/\.git\/?$/, "", gdp)
                    if (sscoped(resolve_all(seen_c ? tgt : S, gdp))) { print cmd; continue }
                }
                if (wt != "") {
                    tgt = resolve_all(seen_c ? tgt : S, wt)
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
                if (seen_c) { if (sscoped(tgt)) print cmd; continue }
                if (sscoped(S)) print cmd
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
