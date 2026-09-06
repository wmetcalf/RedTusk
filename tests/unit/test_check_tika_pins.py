"""The Tika pin gate, executed rather than read.

`scripts/check_tika_pins.sh` is the only thing standing between an edited
Dockerfile and an image that compiles a different Tika than the one it
advertises. It runs straight from `.github/workflows/ci.yml` and had **no tests
at all**, which is why several ways of walking past it survived review: a gate
nobody exercises is a gate nobody can regress-test.

These tests copy the REAL script into a synthetic repo and run it. Asserting on
its source text would prove nothing about a shell script whose whole behaviour is
in how `awk`, `sed` and `grep` interact -- the bypasses below are all cases where
the text looked exactly right and the behaviour was wrong.

The `cd`-scoped case is not an exotic evasion. All four cloning Dockerfiles
already say `RUN cd /src/tika && mvn install`, so appending a `git reset` to that
existing block is the single most plausible careless edit, and the gate exited 0
on it.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_tika_pins.sh"

# Literals, deliberately: deriving these from the script under test would make
# every assertion true by construction.
PIN = "a" * 40
OTHER_PIN = "b" * 40
CLONE_URL = "https://github.com/wmetcalf/tika.git"

CLONES_AND_PINS = f"""\
FROM eclipse-temurin:25-jdk-jammy AS tika
ARG TIKA_FORK_SHA={PIN}
RUN git clone --filter=blob:none {CLONE_URL} /src/tika \\
    && git -C /src/tika checkout "$TIKA_FORK_SHA"
RUN cd /src/tika && \\
    mvn install -DskipTests -q
"""


def _repo(tmp_path: Path, **dockerfiles: str) -> Path:
    """A minimal tree the real script can be run against.

    The script does `cd "$(dirname "$0")/.."`, so dropping it in `<root>/scripts`
    makes `<root>` the repo it inspects.
    """
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, root / "scripts" / SCRIPT.name)
    docker = root / "deploy" / "docker"
    docker.mkdir(parents=True)
    for name, text in dockerfiles.items():
        (docker / f"Dockerfile.{name}").write_text(text)
    return root


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(root / "scripts" / SCRIPT.name)],
        capture_output=True, text=True, timeout=60,
    )


def test_a_consistent_tree_passes(tmp_path: Path) -> None:
    """The positive control. Without it, every 'the gate rejects X' test below
    would also pass on a gate that rejects everything."""
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS, crac=CLONES_AND_PINS))
    assert res.returncode == 0, f"a consistent tree was rejected: {res.stderr}"
    assert PIN in res.stdout


# Each entry appends a fragment to an otherwise-correct Dockerfile. Every one of
# them changes the revision the image actually compiles, so every one must fail.
BYPASSES = [
    pytest.param(
        'RUN cd /src/tika && git reset --hard HEAD^\n', id="cd-scoped-reset"),
    pytest.param(
        'WORKDIR /src/tika\nRUN git reset --hard HEAD^\n', id="workdir-scoped-reset"),
    pytest.param(
        'RUN cd /src/tika && \\\n    git reset --hard HEAD^\n', id="cd-scoped-reset-continued"),
    pytest.param(
        'RUN cd /src/tika && mvn -q install && git rebase upstream/main\n', id="cd-then-rebase"),
    pytest.param(
        'RUN cd /src/tika/tika-core && git reset --hard HEAD^\n', id="cd-into-subdir"),
    pytest.param(
        'RUN git -C /src/tika reset --hard HEAD^\n', id="dash-C-reset"),
    pytest.param(
        f'RUN git -C /src/tika checkout {OTHER_PIN}\n', id="overriding-checkout"),
    pytest.param(
        f'RUN cd /src/tika && git checkout {OTHER_PIN}\n', id="cd-scoped-checkout"),
    # Quoting the -C argument is the ordinary written form, not evasion. An earlier
    # revision of the cwd tracking regressed this: it required a bare path after
    # `-C`, so `git -C "/src/tika"` stopped being scoped to the worktree and the
    # gate accepted it, while the implementation it replaced had caught it (codex).
    pytest.param(
        'RUN git -C "/src/tika" reset --hard HEAD^\n', id="double-quoted-dash-C"),
    pytest.param(
        "RUN git -C '/src/tika' reset --hard HEAD^\n", id="single-quoted-dash-C"),
    pytest.param(
        'RUN cd "/src/tika" && git reset --hard HEAD^\n', id="quoted-cd"),
    # Docker resolves a relative WORKDIR against the one in force.
    pytest.param(
        'WORKDIR /src\nWORKDIR tika\nRUN git reset --hard HEAD^\n', id="relative-workdir"),
    pytest.param(
        'WORKDIR /src/tika/tika-core\nWORKDIR ..\nRUN git reset --hard HEAD^\n',
        id="workdir-dotdot-back-into-the-worktree"),
    # A stage built FROM a named earlier stage inherits that stage's WORKDIR.
    pytest.param(
        'FROM scratch AS pinned\nWORKDIR /src/tika\n'
        'FROM pinned AS later\nRUN git reset --hard HEAD^\n',
        id="workdir-inherited-from-a-named-base-stage"),
    # A relative `cd` resolves against the WORKDIR in force, the same as a relative
    # WORKDIR does. Without this case the two are not tested by the same rule.
    pytest.param(
        'WORKDIR /src\nRUN cd tika && git reset --hard HEAD^\n', id="relative-cd"),
    # `FROM --platform=... base AS name` is the standard form; the base is the first
    # NON-flag token. Reading the flag as the base silently reset the inherited dir.
    pytest.param(
        'FROM scratch AS pinned\nWORKDIR /src/tika\n'
        'FROM --platform=linux/amd64 pinned AS later\nRUN git reset --hard HEAD^\n',
        id="from-with-a-platform-flag"),
    # Docker expands build variables in WORKDIR and in the shell.
    pytest.param(
        'ENV ROOT=/src\nWORKDIR $ROOT/tika\nRUN git reset --hard HEAD^\n',
        id="workdir-from-an-env-var"),
    pytest.param(
        'ENV ROOT=/src\nWORKDIR ${ROOT}/tika\nRUN git reset --hard HEAD^\n',
        id="workdir-from-a-braced-env-var"),
    pytest.param(
        'ARG R=/src\nRUN cd $R/tika && git reset --hard HEAD^\n', id="cd-from-an-arg"),
    # A directory that still holds an unresolved variable is UNKNOWN, and a gate treats
    # unknown as in scope: a false alarm a human can read beats silent acceptance.
    pytest.param(
        'WORKDIR $UNSET_VAR/x\nRUN git reset --hard HEAD^\n',
        id="unresolvable-workdir-fails-closed"),
    # git(1): with multiple -C options, each subsequent relative path is interpreted
    # against the preceding one. Reading only the first put this in /src.
    pytest.param(
        'RUN git -C /src -C tika reset --hard HEAD^\n', id="multiple-dash-C-accumulate"),
    # A single `|` is a command boundary as much as `&&`; patching through a pipe is
    # ordinary. `apply` changes the tree without a checkout.
    pytest.param(
        'RUN cat /tmp/change.patch | git -C /src/tika apply\n', id="pipe-is-a-boundary"),
    # git(1) global options that take a SEPARATE operand: reading the operand as the
    # subcommand stops the scan before a later -C comes into view.
    pytest.param(
        'RUN git -c advice.detachedHead=false -C /src/tika reset --hard HEAD^\n',
        id="dash-c-consumes-its-operand"),
    # --work-tree / --git-dir reach the checkout from anywhere, naming no cwd at all.
    pytest.param(
        'RUN git --git-dir=/src/tika/.git --work-tree=/src/tika reset --hard HEAD^\n',
        id="explicit-work-tree"),
    pytest.param(
        'RUN git --git-dir=/src/tika/.git reset --hard HEAD^\n', id="explicit-git-dir"),
    pytest.param(
        'RUN git --work-tree /src/tika reset --hard HEAD^\n', id="work-tree-space-form"),
    # `-C<path>` attached is valid git and was caught by the text scan this parser
    # replaced. It is the fourth catch the rewrite silently gave up, which is why the
    # two approaches are now unioned rather than swapped.
    pytest.param(
        'RUN git -C/src/tika reset --hard HEAD^\n', id="attached-dash-C-path"),
    # Docker keeps an ENV value when a later ARG declares the same name.
    pytest.param(
        'ENV ROOT=/src\nARG ROOT=/opt\nWORKDIR $ROOT/tika\nRUN git reset --hard HEAD^\n',
        id="env-wins-over-a-later-arg"),
    # A bare --git-dir does NOT relocate the worktree -- git uses the CURRENT
    # directory. Verified against git 2.43: run from checkout A with B/.git,
    # `reset --hard HEAD~1` rewrote the files in A and left B untouched.
    pytest.param(
        'WORKDIR /src/tika\nRUN git --git-dir=/tmp/other/.git reset --hard HEAD\n',
        id="bare-git-dir-keeps-the-cwd-as-the-worktree"),
    # `cd [-L|[-P [-e]] [-@]] [dir]` -- the option was being read as the directory.
    pytest.param(
        'RUN cd -P /src/tika && git reset --hard HEAD^\n', id="cd-with-options"),
    # The shell groups this as `(cd A || cd B) && git reset`, so when A succeeds the
    # second cd never runs and the reset happens in A. Both branches stay reachable.
    pytest.param(
        'WORKDIR /\nRUN cd /src/tika || cd /opt && git reset --hard HEAD^\n',
        id="chained-fallback-cd-first-branch"),
    pytest.param(
        'WORKDIR /\nRUN cd /opt || cd /src/tika && git reset --hard HEAD^\n',
        id="chained-fallback-cd-second-branch"),
    # Dockerfile instruction names are case-insensitive.
    pytest.param(
        'workdir /src/tika\nRUN git reset --hard HEAD^\n', id="lowercase-workdir"),
    # ENV/ARG continue across `\` and the continuation belongs to the SAME
    # instruction, so the later ROOT is the one in force.
    pytest.param(
        'ENV ROOT=/opt\nENV OTHER=x \\\n    ROOT=/src\n'
        'WORKDIR $ROOT/tika\nRUN git reset --hard HEAD^\n',
        id="continued-env-instruction"),
    # git documents `-C ""` as leaving the current directory unchanged. The empty
    # operand must survive tokenisation, or -C swallows the subcommand as its path.
    pytest.param(
        'WORKDIR /src/tika\nRUN git -C "" reset --hard HEAD^\n', id="empty-quoted-dash-C"),
    pytest.param(
        'WORKDIR /src/tika\nRUN git -C . reset --hard HEAD^\n', id="explicit-dot-dash-C"),
    # `RUN <<EOF` opens a heredoc whose BODY is the script. There is no trailing
    # backslash, so continuation tracking never saw it.
    pytest.param(
        'RUN <<EOF\ngit -C /src/tika reset --hard HEAD^\nEOF\n', id="heredoc-run-body"),
    pytest.param(
        'WORKDIR /src/tika\nRUN <<EOF\ngit reset --hard HEAD^\nEOF\n',
        id="heredoc-body-under-a-workdir"),
    pytest.param(
        'RUN <<-"EOF"\ngit -C /src/tika reset --hard HEAD^\nEOF\n',
        id="heredoc-quoted-and-dash-form"),
    pytest.param(
        'RUN <<EOF\necho hello\nEOF\nRUN cd /src/tika && git reset --hard HEAD^\n',
        id="command-after-a-heredoc-is-still-seen"),
    # Docker still accepts the legacy two-token `ENV <key> <value>` form.
    pytest.param(
        'ENV ROOT=/opt\nENV ROOT /src\nWORKDIR $ROOT/tika\nRUN git reset --hard HEAD^\n',
        id="legacy-two-token-env"),
    # The `&&` skips after a failed cd, then the `||` catches the failure -- so the
    # reset runs in the ORIGINAL directory.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /missing && echo ok || git reset --hard HEAD^\n',
        id="failure-branch-reached-through-and-then-or"),
    # `false` returns a status; it does not end the shell the way `exit` does.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /missing || false; git reset --hard HEAD^\n',
        id="false-is-not-an-aborting-handler"),
    # A data heredoc still has real commands on its OPENING line.
    pytest.param(
        'RUN cat <<EOF >/tmp/note && git -C /src/tika reset --hard HEAD^\nx\nEOF\n',
        id="command-trailing-a-data-heredoc-redirect"),
    # Inside SINGLE quotes a backslash is literal, so the quote closes and the
    # semicolon really is a boundary.
    pytest.param(
        "WORKDIR /src/tika\nRUN echo 'x\\'; git reset --hard HEAD^\n",
        id="backslash-is-literal-inside-single-quotes"),
    # A heredoc delimiter is a WORD, not an identifier.
    pytest.param(
        'RUN <<BUILD-SCRIPT\ngit -C /src/tika reset --hard HEAD^\nBUILD-SCRIPT\n',
        id="heredoc-delimiter-with-punctuation"),
    # `(cd A || cd B || cd C) && reset` runs the reset if ANY branch succeeded, so
    # every branch target is reachable -- not just the last one parsed.
    pytest.param(
        'WORKDIR /\nRUN cd /src/tika || cd /opt || cd /var && git reset --hard HEAD^\n',
        id="three-branch-fallback-chain"),
    # Only `<<-` ignores leading whitespace on the terminator. For a plain `<<`, an
    # indented delimiter-looking line is BODY, and closing there hid the rest.
    pytest.param(
        'RUN <<EOF\n  EOF\ngit -C /src/tika reset --hard HEAD^\nEOF\n',
        id="indented-delimiter-does-not-close-a-plain-heredoc"),
    # `RUN (cd X && ...)` is ordinary grouping; the opener hid the cd.
    pytest.param(
        'RUN (cd /src/tika && git reset --hard HEAD^)\n', id="subshell-opener-before-cd"),
    # Only `&&` proves the preceding command succeeded. After a cd that may have
    # failed, the shell is still where it started and the reset runs THERE.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /missing || git reset --hard HEAD^\n',
        id="cd-may-have-failed-before-or"),
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /missing ; git reset --hard HEAD^\n',
        id="cd-may-have-failed-before-semicolon"),
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /missing \\\n    || git reset --hard HEAD^\n',
        id="cd-may-have-failed-across-a-continuation"),
    # Docker expands every value in one ENV against the environment as it was BEFORE
    # the instruction, so DEST here is the OLD /src, not the /opt assigned beside it.
    pytest.param(
        'ENV ROOT=/src\nENV ROOT=/opt DEST=$ROOT\n'
        'WORKDIR $DEST/tika\nRUN git reset --hard HEAD^\n',
        id="env-expands-from-the-pre-instruction-environment"),
]


@pytest.mark.parametrize("fragment", BYPASSES)
def test_the_gate_rejects_a_dockerfile_that_moves_head_off_the_pin(
    tmp_path: Path, fragment: str
) -> None:
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS + fragment, crac=CLONES_AND_PINS))
    assert res.returncode == 1, (
        f"the gate accepted a Dockerfile that compiles a different revision:\n"
        f"{fragment}stdout={res.stdout!r} stderr={res.stderr!r}"
    )
    assert "Dockerfile.default" in res.stderr


# The counterweight. A gate that rejects these is unusable, and "it rejected the
# bypass" says nothing until the same rule is shown NOT to reject ordinary files.
BENIGN = [
    pytest.param(
        'RUN cd /src/other && git reset --hard HEAD^\n', id="reset-in-another-worktree"),
    pytest.param(
        'WORKDIR /src/tika\nWORKDIR /build\nRUN git reset --hard HEAD^\n',
        id="workdir-moved-away-first"),
    pytest.param(
        'RUN cd /src/tika && mvn -q install\nRUN git reset --hard HEAD^\n',
        id="cd-does-not-leak-into-the-next-run"),
    pytest.param(
        'RUN echo "remember to git checkout $TIKA_FORK_SHA"\n', id="prose-mentioning-checkout"),
    # The counterweight to stage inheritance: a stage from an UNRELATED base starts
    # at /, so a bare reset there is not in the Tika worktree.
    pytest.param(
        'FROM scratch AS pinned\nWORKDIR /src/tika\n'
        'FROM scratch AS unrelated\nRUN git reset --hard HEAD^\n',
        id="fresh-stage-does-not-inherit-an-unrelated-workdir"),
    pytest.param(
        'WORKDIR /src/tika\nWORKDIR ..\nRUN git reset --hard HEAD^\n',
        id="workdir-dotdot-out-of-the-worktree"),
    pytest.param(
        'RUN git -C "/src/other" reset --hard HEAD^\n', id="quoted-dash-C-elsewhere"),
    # git -C: "Run as if git was started in <path> instead of the current working
    # directory". So when it is present it DECIDES -- falling through to the shell cwd
    # flagged a legitimate operation on a different repository (codex).
    pytest.param(
        'WORKDIR /src/tika\nRUN git -C /src/other reset --hard HEAD^\n',
        id="explicit-dash-C-overrides-the-shell-cwd"),
    pytest.param(
        'RUN cd /src/tika && git -C /src/other reset --hard HEAD^\n',
        id="explicit-dash-C-overrides-a-cd"),
    pytest.param(
        'ENV APPDIR=/opt/app\nWORKDIR $APPDIR\nRUN git reset --hard HEAD^\n',
        id="resolved-env-workdir-outside-the-worktree"),
    # The counterweight that makes `cd` expansion observable. Unexpanded, `$APPDIR`
    # still holds a `$`, the unknown-directory rule fails CLOSED, and the command is
    # flagged -- so a bypass case alone cannot tell whether expansion happened. Only a
    # variable path resolving OUTSIDE the worktree distinguishes them.
    pytest.param(
        'ENV APPDIR=/opt/app\nRUN cd $APPDIR && git reset --hard HEAD^\n',
        id="resolved-env-cd-outside-the-worktree"),
    pytest.param(
        'RUN git -C /src/other -C sub reset --hard HEAD^\n',
        id="multiple-dash-C-accumulating-elsewhere"),
    pytest.param(
        'RUN git --work-tree=/src/other --git-dir=/src/other/.git reset --hard HEAD^\n',
        id="explicit-work-tree-elsewhere"),
    pytest.param(
        'RUN cat /tmp/p.patch | git -C /src/other apply\n', id="pipe-into-another-worktree"),
    # The counterweight for the rule above: `&&` DOES prove the cd succeeded, so the
    # old directory is no longer reachable and must not be carried along.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /opt/elsewhere && git reset --hard HEAD^\n',
        id="cd-that-definitely-succeeded-leaves-the-worktree"),
    # The same, with the `&&` opening the continuation line. Judging physical lines
    # could not see it while processing the cd, and reported ordinary formatting.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /opt/elsewhere \\\n    && git reset --hard HEAD^\n',
        id="guaranteed-cd-with-the-and-on-the-next-line"),
    # The verb must be the SUBCOMMAND. Matching it anywhere rejected read-only
    # inspection whose PATHSPEC happens to be called `reset`.
    pytest.param(
        'WORKDIR /src/tika\nRUN git diff HEAD -- reset\n', id="pathspec-named-reset"),
    pytest.param(
        'WORKDIR /src/tika\nRUN git log --oneline -- reset\n',
        id="log-with-a-pathspec-named-reset"),
    # Read-only commands inside the worktree must pass, including through the
    # text-scan union -- naming the worktree is not moving its HEAD.
    pytest.param(
        'RUN git -C /src/tika log --oneline -1\n', id="read-only-log-in-the-worktree"),
    pytest.param(
        'RUN git -C /src/tika status --porcelain\n', id="read-only-status-in-the-worktree"),
    pytest.param(
        'RUN git diff HEAD -- /src/tika\n', id="read-only-diff-naming-the-worktree"),
    # The guarded-cd idiom: a failed cd exits, so the old directory is unreachable.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /src/other || exit 1; git reset --hard HEAD^\n',
        id="guarded-cd-that-aborts-on-failure"),
    # The counterweight for the fallback rule: when NEITHER branch is the worktree,
    # neither is reachable, and the directory that preceded the pair is not either.
    pytest.param(
        'WORKDIR /\nRUN cd /opt || cd /var && git reset --hard HEAD^\n',
        id="chained-fallback-cd-neither-branch-is-the-worktree"),
    # Separators inside quotes are text, not command boundaries. Printing a recovery
    # hint must not read as running it.
    pytest.param(
        'WORKDIR /src/tika\nRUN echo "recovery: cd /src/tika; git reset --hard HEAD"\n',
        id="separator-inside-a-quoted-string"),
    pytest.param(
        'WORKDIR /opt\nRUN git -C "" reset --hard HEAD^\n',
        id="empty-dash-C-outside-the-worktree"),
    # A backslash escapes the next character, so this is ONE echo.
    pytest.param(
        'WORKDIR /src/tika\nRUN echo recovery\\; git reset --hard HEAD\n',
        id="escaped-separator-is-literal"),
    pytest.param(
        'RUN <<EOF\ngit -C /src/other reset --hard HEAD^\nEOF\n',
        id="heredoc-body-in-another-worktree"),
    # Only a BARE `RUN <<EOF` runs its body. `RUN cat <<EOF` feeds it to a command as
    # DATA, so generated text must not read as executed commands.
    pytest.param(
        'WORKDIR /src/tika\nRUN cat <<EOF > /tmp/notes.txt\n'
        'git reset --hard HEAD^\nEOF\n',
        id="data-heredoc-is-not-a-script"),
    # git documents `[-v | --version] [-h | --help]` as standalone modes: no
    # subcommand, read-only, and valid outside a repository.
    pytest.param(
        'WORKDIR /src/tika\nRUN git --version\n', id="git-version-has-no-subcommand"),
    pytest.param(
        'WORKDIR /src/tika\nRUN git --help\n', id="git-help-has-no-subcommand"),
    # The counterweight for the failure-branch rule: here the reset can only run
    # AFTER a successful cd, so the original directory is not reachable at it.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /opt/elsewhere && git reset --hard HEAD^ || echo failed\n',
        id="reset-only-reachable-after-a-successful-cd"),
    # The counterweight for the fallback chain: when the shell cds AWAY in every
    # branch, the directory it started in is no longer reachable.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd /opt || cd /var && git reset --hard HEAD^\n',
        id="fallback-chain-that-leaves-the-worktree-in-every-branch"),
    # A bare `cd` goes to $HOME, not to where we already are. Written WITHOUT a
    # `-C`, deliberately: with one, the -C decides the scope and the test cannot
    # observe where the shell thinks it is -- checked, and it could not.
    pytest.param(
        'WORKDIR /src/tika\nRUN cd && git reset --hard HEAD^\n',
        id="operandless-cd-goes-to-home"),
    # `git --help reset` DISPLAYS documentation; the word after it is a help target.
    pytest.param(
        'WORKDIR /src/tika\nRUN git --help reset\n', id="help-target-is-not-a-subcommand"),
]


@pytest.mark.parametrize("fragment", BENIGN)
def test_the_gate_accepts_ordinary_dockerfiles(tmp_path: Path, fragment: str) -> None:
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS + fragment, crac=CLONES_AND_PINS))
    assert res.returncode == 0, (
        f"the gate rejected an ordinary Dockerfile:\n{fragment}stderr={res.stderr!r}"
    )


def test_drifted_pins_are_reported(tmp_path: Path) -> None:
    drifted = CLONES_AND_PINS.replace(PIN, OTHER_PIN)
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS, crac=drifted))
    assert res.returncode == 1
    assert "drifted" in res.stderr


def test_a_pin_on_a_file_that_never_clones_is_reported(tmp_path: Path) -> None:
    """The original defect this gate was written for: a pin advertising a Tika
    the image does not contain."""
    decoration = f"FROM scratch\nARG TIKA_FORK_SHA={PIN}\n"
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS, localsrc=decoration))
    assert res.returncode == 1
    assert "never clones" in res.stderr


def test_a_cloning_file_with_no_pin_is_reported(tmp_path: Path) -> None:
    unpinned = f"FROM scratch\nRUN git clone {CLONE_URL} /src/tika\n"
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS, loose=unpinned))
    assert res.returncode == 1
    assert "declares no full 40-char" in res.stderr


def test_two_declarations_are_reported(tmp_path: Path) -> None:
    """Docker honours the LAST ARG default before the instruction that uses it,
    so a second declaration drives the build while the gate reports the first."""
    doubled = CLONES_AND_PINS.replace(
        f"ARG TIKA_FORK_SHA={PIN}\n",
        f"ARG TIKA_FORK_SHA={PIN}\nARG TIKA_FORK_SHA={OTHER_PIN}\n",
    )
    res = _run(_repo(tmp_path, default=doubled, crac=CLONES_AND_PINS))
    assert res.returncode == 1
    assert "declares TIKA_FORK_SHA 2 times" in res.stderr


def test_no_cloning_dockerfile_at_all_is_an_error_not_a_pass(tmp_path: Path) -> None:
    """'Nothing to check' and 'everything checks out' must not look alike -- if
    the fork URL changes, the gate must say so rather than silently pass."""
    res = _run(_repo(tmp_path, default="FROM scratch\n"))
    assert res.returncode == 1
    assert "has the fork URL changed" in res.stderr


# These two need a whole Dockerfile rather than a fragment appended to a correct
# one: a global ARG is only global BEFORE the first FROM, and per-stage ENV needs
# several stages in a specific order. Appending them would produce files Docker
# would not interpret the way the test claims -- checked, and my first probe for
# the ARG case did exactly that and "failed" for the wrong reason.

def _cloning_stage(name: str) -> str:
    return (
        f"FROM eclipse-temurin:25-jdk-jammy AS {name}\n"
        f"ARG TIKA_FORK_SHA={PIN}\n"
        f"RUN git clone {CLONE_URL} /src/tika \\\n"
        '    && git -C /src/tika checkout "$TIKA_FORK_SHA"\n'
    )


def test_a_stage_selected_by_a_global_arg_still_inherits_its_workdir(tmp_path: Path) -> None:
    """`ARG B=pinned` + `FROM $B AS later` is how a build parameterises its base.
    The literal `$B` matches no stage, so the inherited directory silently reset
    to `/` and a bare reset in a stage that really is inside the worktree passed."""
    text = (
        "ARG B=pinned\n"
        + _cloning_stage("pinned")
        + "WORKDIR /src/tika\n"
        "FROM $B AS later\n"
        "RUN git reset --hard HEAD^\n"
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 1, f"accepted a reset in the inherited worktree: {res.stdout}"


def test_env_values_do_not_leak_between_unrelated_stages(tmp_path: Path) -> None:
    """ENV is per-stage. With one global map, a later unrelated stage's `ROOT=/opt`
    overwrote the `/src` that a stage derived from `tk` should still see, so
    `WORKDIR $ROOT/tika` resolved outside the worktree and the reset was accepted."""
    text = (
        _cloning_stage("tk")
        + "ENV ROOT=/src\n"
        "WORKDIR /src/tika\n"
        "FROM scratch AS other\n"
        "ENV ROOT=/opt\n"
        "FROM tk AS later\n"
        "WORKDIR $ROOT/tika\n"
        "RUN git reset --hard HEAD^\n"
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 1, f"a leaked ENV value hid a real reset: {res.stdout}"


def test_a_derived_stage_inherits_its_base_stages_env(tmp_path: Path) -> None:
    """The counterweight that makes inheritance observable.

    Not inheriting can only ever cause a FALSE POSITIVE here: the variable stays
    unresolved, the unknown-directory rule fails closed, and the command is
    flagged. So no bypass case can distinguish "inherited" from "gave up safely"
    -- only a stage whose inherited value resolves OUTSIDE the worktree can.
    """
    text = (
        _cloning_stage("tk")
        + "ENV ROOT=/opt\n"
        "FROM tk AS later\n"
        "WORKDIR $ROOT/app\n"
        "RUN git reset --hard HEAD^\n"
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 0, (
        f"a reset in the inherited /opt/app was reported as touching Tika: {res.stderr}"
    )


@pytest.mark.parametrize("verb", ["reset --hard HEAD^", "rebase upstream/main",
                                  "merge other", "apply /tmp/x.patch"])
def test_naming_the_worktree_is_always_reported_whatever_the_option_grammar(
    tmp_path: Path, verb: str
) -> None:
    """The invariant that keeps this gate from getting weaker as it gets smarter.

    The parser replaced a one-line text scan, and independently lost FOUR catches
    the text scan had -- a pipe boundary, `-c <name>=<value>` eating the scan,
    `--work-tree`/`--git-dir`, and attached `-C<path>` -- each silently, each found
    by review rather than by CI. Getting the git option grammar exactly right is
    not something to be confident about, so the parser's verdict is UNIONED with
    the old question: does the command name the worktree at all?

    This test states that union directly. It is deliberately indifferent to HOW
    the command reaches /src/tika, because that is the part that kept changing.
    """
    text = CLONES_AND_PINS + f"RUN git --exec-path=/usr/lib/git-core -C /src/tika {verb}\n"
    res = _run(_repo(tmp_path, default=text, crac=CLONES_AND_PINS))
    assert res.returncode == 1, (
        f"a HEAD-moving command naming the worktree was accepted: {verb}"
    )


def test_the_awk_program_contains_no_apostrophes() -> None:
    """The whole detector lives inside a single-quoted shell string, so one
    apostrophe in a COMMENT terminates it and the script dies with a bash syntax
    error. That has now happened twice while editing this file, both times from
    ordinary English possessives, and both times every case reported rc=2 at once
    -- which reads like the gate rejecting everything rather than not parsing.
    """
    text = SCRIPT.read_text()
    start = text.index("moved=\"$(awk '") + len("moved=\"$(awk '")
    end = text.index("' <<<\"$stripped\"", start)
    offenders = [ln.strip() for ln in text[start:end].splitlines() if "'" in ln]
    assert not offenders, (
        "an apostrophe inside the single-quoted awk program will break the script: "
        + "; ".join(offenders[:3])
    )


def test_lowercase_instructions_are_understood_throughout(tmp_path: Path) -> None:
    """Docker instruction names are case-insensitive. Recognising only uppercase
    made the parser skip a whole file silently -- it saw no FROM, no WORKDIR and
    no RUN, which is indistinguishable from a file that does nothing wrong."""
    text = (
        f"from eclipse-temurin:25-jdk-jammy as pinned\n"
        f"arg TIKA_FORK_SHA={PIN}\n"
        f"run git clone {CLONE_URL} /src/tika \\\n"
        '    && git -C /src/tika checkout "$TIKA_FORK_SHA"\n'
        "workdir /src/tika\n"
        "from pinned as later\n"
        "run git reset --hard HEAD^\n"
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 1, f"an all-lowercase Dockerfile was not parsed: {res.stdout}"
    assert "moves the Tika worktree" in res.stderr, (
        "the file was rejected, but not for the reason under test: "
        f"{res.stderr}"
    )


def test_a_correct_all_lowercase_dockerfile_is_accepted(tmp_path: Path) -> None:
    """The control the test above needed, and did not have.

    The discovery greps required an uppercase `ARG`, so ANY all-lowercase file was
    rejected with "declares no full 40-char ARG" -- which meant the rejection test
    passed even with every lowercase parser branch removed, and a perfectly correct
    lowercase Dockerfile was refused (codex). The instruction keyword is matched
    either way now; the ARG NAME still is not, since `arg tika_fork_sha=` declares
    a different variable and must not satisfy the pin.
    """
    text = (
        "from eclipse-temurin:25-jdk-jammy as pinned\n"
        f"arg TIKA_FORK_SHA={PIN}\n"
        f"run git clone {CLONE_URL} /src/tika \\\n"
        '    && git -C /src/tika checkout "$TIKA_FORK_SHA"\n'
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 0, f"a correct lowercase Dockerfile was rejected: {res.stderr}"


def test_a_lowercase_decoration_pin_is_still_reported(tmp_path: Path) -> None:
    """The decoration check has its own file-discovery grep, and it needed the same
    treatment: a pin on a file that never clones is just as misleading written in
    lowercase, and the uppercase-only scan could not see it at all."""
    decoration = f"from scratch\narg TIKA_FORK_SHA={PIN}\n"
    res = _run(_repo(tmp_path, default=CLONES_AND_PINS, localsrc=decoration))
    assert res.returncode == 1
    assert "never clones" in res.stderr


def test_a_lowercase_arg_name_does_not_satisfy_the_pin(tmp_path: Path) -> None:
    """Instruction names are case-insensitive; build ARG NAMES are not."""
    text = (
        "from eclipse-temurin:25-jdk-jammy as pinned\n"
        f"arg tika_fork_sha={PIN}\n"
        f"run git clone {CLONE_URL} /src/tika \\\n"
        '    && git -C /src/tika checkout "$TIKA_FORK_SHA"\n'
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 1
    assert "declares no full 40-char" in res.stderr


def test_a_defaultless_stage_arg_imports_the_global_value(tmp_path: Path) -> None:
    """`ARG ROOT=/opt` before the first FROM, then a bare `ARG ROOT` inside a stage:
    Docker imports the global value. Ignoring the defaultless form left the name
    unresolved, the directory unknown, and the unknown rule then convicted an
    ordinary reset in /opt/app (codex)."""
    text = (
        "ARG ROOT=/opt\n"
        + _cloning_stage("pinned")
        + "FROM pinned AS later\n"
        "ARG ROOT\n"
        "WORKDIR $ROOT/app\n"
        "RUN git reset --hard HEAD^\n"
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 0, f"a reset in the inherited /opt/app was rejected: {res.stderr}"


def test_a_lowercase_run_with_a_direct_checkout_is_accepted(tmp_path: Path) -> None:
    """The checkout scan strips the RUN prefix, and it only stripped an uppercase
    one. The earlier lowercase control passed only because its checkout followed
    `&&` on a continuation, which yields a segment already starting with `git`
    (codex). This is the direct form."""
    text = (
        "from eclipse-temurin:25-jdk-jammy as pinned\n"
        f"arg TIKA_FORK_SHA={PIN}\n"
        f"run git clone {CLONE_URL} /src/tika\n"
        'run git -C /src/tika checkout "$TIKA_FORK_SHA"\n'
    )
    res = _run(_repo(tmp_path, default=text))
    assert res.returncode == 0, f"a lowercase direct checkout was not seen: {res.stderr}"

