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
