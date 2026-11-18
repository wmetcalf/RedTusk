"""CVE-2026-114938 ("Java4Shell") mitigation: every worker JVM runs with the HotSpot
Base64 intrinsic OFF (``-XX:-UseBASE64Intrinsics``).

The bug is a heap overflow in the AVX-512 VBMI Base64 *decode intrinsic* (JDK 17.0.6+ .. 27).
Hostile documents reach ``java.util.Base64`` inside the Tika fork (e.g. ICalParser's inline
ATTACH), so a JVM that boots without the flag is exploitable on a VBMI-capable host once C2
compiles the decoder (C1-only JVMs never install the stub, but checkpoint JVMs and operator
flag bundles run C2). These
tests fail if any launch path loses the flag: the engine argv (cold + warm FC/gVisor, which
all go through ``_java_worker_argv``), every ``java`` invocation in the Dockerfiles (AOT bake,
CRaC/warp checkpoint, ENTRYPOINT), the release/checkpoint scripts, and the gVisor tier's
JAVA_TOOL_OPTIONS override.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from redtusk import engine as eng

FLAG = "-XX:-UseBASE64Intrinsics"
REPO = Path(__file__).resolve().parents[2]
DOCKER = REPO / "deploy" / "docker"


# --- engine argv ---------------------------------------------------------------------------


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("REDTUSK_JAVA_OPTS", "REDTUSK_JAVA_BIN", "REDTUSK_AOT_CACHE"):
        monkeypatch.delenv(k, raising=False)


def test_default_bundle_disables_base64_intrinsics(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    assert FLAG in eng._DEFAULT_JVM_FLAGS
    argv = eng._java_worker_argv(Path("/scr"))
    assert FLAG in argv[: argv.index("-jar")], argv


def test_java_opts_override_cannot_reenable_the_intrinsic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("REDTUSK_JAVA_OPTS", "-Xmx1g -XX:+UseBASE64Intrinsics -XX:+UseSerialGC")
    argv = eng._java_worker_argv(Path("/scr"))
    jvm = argv[1 : argv.index("-jar")]
    assert "-XX:+UseBASE64Intrinsics" not in jvm
    # HotSpot honours the LAST occurrence; the OFF flag must be it.
    assert [f for f in jvm if "UseBASE64Intrinsics" in f] == [FLAG]
    assert jvm[-1] == FLAG
    assert jvm[:2] == ["-Xmx1g", "-XX:+UseSerialGC"]


def test_java_opts_override_without_the_flag_gets_it(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("REDTUSK_JAVA_OPTS", "-Xmx1g")
    argv = eng._java_worker_argv(Path("/scr"))
    assert argv[: argv.index("-jar")] == ["java", "-Xmx1g", FLAG]


# --- static launch-path inventory -----------------------------------------------------------
#
# Every ``java`` launch in the Dockerfiles, the deploy scripts and the guest init scripts is
# found by TOKEN (any token whose basename is ``java``, so wrappers like ``exec``/``setpriv``/
# ``timeout``/``sh -c``, absolute paths and ``$JAVA_HOME/bin/java`` are all seen), and the
# check is POSITIONAL: only the JVM options before ``-jar``/the main class count (Main ignores
# extra program args, so a flag after ``-jar x.jar`` does nothing), and the LAST
# UseBASE64Intrinsics option there must be the OFF flag (HotSpot honours the last one).


def _instructions(dockerfile: Path) -> list[str]:
    """Dockerfile instructions with line continuations joined and in-RUN comments dropped."""
    out: list[str] = []
    cur = ""
    for raw in dockerfile.read_text().splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if line.endswith("\\"):
            cur += line[:-1] + " "
            continue
        cur += line
        if cur.strip():
            out.append(cur.strip())
        cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


_OPERATORS = ";&|()`"
# Options that take their value as the NEXT token.
_ARG_OPTS = frozenset({"-cp", "-classpath", "--class-path", "-p", "--module-path",
                       "--add-modules", "--add-opens", "--add-exports", "--add-reads",
                       "--upgrade-module-path", "--limit-modules"})


def _tokens(text: str) -> list[str]:
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def _commands(text: str) -> list[list[str]]:
    """Split a shell string into commands on ; & | ( ) ` -- but only OUTSIDE quotes, so a
    quoted ``sh -c 'a; java ...'`` stays one argument (and is parsed recursively)."""
    lex = shlex.shlex(text, posix=True, punctuation_chars=_OPERATORS)
    lex.whitespace_split = True
    try:
        toks = list(lex)
    except ValueError:
        toks = text.split()
    groups: list[list[str]] = [[]]
    for tok in toks:
        if tok and all(c in _OPERATORS for c in tok):
            groups.append([])
        else:
            groups[-1].append(tok)
    return [g for g in groups if g]


def _is_java(tok: str) -> bool:
    return tok.rsplit("/", 1)[-1] == "java"


def _jvm_options(tokens: list[str]) -> list[str]:
    """The JVM options after a ``java`` token, stopping at ``-jar``/``-m``/the main class."""
    opts: list[str] = []
    it = iter(tokens)
    for tok in it:
        if tok in ("-jar", "-m", "--module") or not tok.startswith("-") and not tok.startswith("@"):
            break
        opts.append(tok)
        if tok in _ARG_OPTS:
            next(it, "")  # its value is not a VM option, whatever it looks like
    return opts


def _java_launches(command: str | list[str]) -> list[list[str]]:
    """JVM option lists of every java launch in a shell string or an exec-form argv."""
    if isinstance(command, list):
        groups = [command]
    else:
        groups = _commands(command)
    out: list[list[str]] = []
    for toks in groups:
        for i, tok in enumerate(toks):
            if _is_java(tok):
                out.append(_jvm_options(toks[i + 1:]))
            elif tok in ("-c",) and i + 1 < len(toks) and i > 0 and toks[i - 1].endswith("sh"):
                out.extend(_java_launches(toks[i + 1]))
    return out


def _is_restore_only(opts: list[str]) -> bool:
    # A CRaC/warp RESTORE resumes the checkpointed process with the checkpoint's VM flags; the
    # flag belongs on the checkpoint-creating JVM. A restore that may fall back to a fresh
    # boot (CRaCIgnoreRestoreIfUnavailable) is a boot, so it needs the flag too.
    joined = " ".join(opts)
    return ("CRaCRestoreFrom" in joined and "CRaCCheckpointTo" not in joined
            and "CRaCIgnoreRestoreIfUnavailable" not in joined)


def _launch_ok(opts: list[str]) -> bool:
    if _is_restore_only(opts):
        return True
    settings = [o for o in opts if "UseBASE64Intrinsics" in o]
    return bool(settings) and settings[-1] == FLAG


def _dockerfile_launches(text_or_path: Path) -> list[list[str]]:
    out: list[list[str]] = []
    for ins in _instructions(text_or_path):
        kw, _, rest = ins.partition(" ")
        if kw not in ("RUN", "CMD", "ENTRYPOINT"):
            continue
        while rest.startswith("--"):  # RUN --mount=... --network=...
            rest = rest.split(" ", 1)[1] if " " in rest else ""
        if rest.startswith("["):
            try:
                argv = json.loads(rest)
            except ValueError:
                argv = None
            if isinstance(argv, list):
                out.extend(_java_launches([str(a) for a in argv]))
                continue
        out.extend(_java_launches(rest))
    return out


def _script_launches(path: Path) -> list[list[str]]:
    code = "\n".join(
        ln for ln in path.read_text().splitlines() if not ln.lstrip().startswith("#")
    )
    return _java_launches(re.sub(r"\\\n\s*", " ", code))


class _Text:
    def __init__(self, text: str) -> None:
        self._text = text

    def read_text(self) -> str:
        return self._text


@pytest.mark.parametrize(
    "dockerfile",
    [
        "RUN java -XX:CRaCCheckpointTo=/c -jar /app/w.jar --checkpoint /s -XX:-UseBASE64Intrinsics",
        "RUN java -XX:-UseBASE64Intrinsics -XX:+UseBASE64Intrinsics -jar /app/w.jar --run /s",
        "RUN /opt/java/openjdk/bin/java -jar /app/w.jar --run /s",
        'RUN ["java", "-jar", "/app/w.jar", "--run", "/s"]',
        "RUN --mount=type=cache,target=/c java -jar /app/w.jar --run /s",
        "RUN sh -c 'java -jar /app/w.jar --run /s'",
        "RUN timeout 60 java -jar /app/w.jar --run /s",
        "RUN FOO=\"a b\" java -jar /app/w.jar --run /s",
        'CMD ["java", "-jar", "/app/w.jar", "--run", "/s"]',
        "RUN java -XX:CRaCRestoreFrom=/c -XX:+CRaCIgnoreRestoreIfUnavailable -jar /app/w.jar",
        "RUN $JAVA_HOME/bin/java -cp -XX:-UseBASE64Intrinsics Main",
        "RUN sh -c 'java -XX:+UseBASE64Intrinsics -jar /app/w.jar --run /s; echo done'",
        "RUN sh -c 'true && java -jar /app/w.jar --run /s'",
        "RUN true; java -jar /app/w.jar --run /s",
    ],
)
def test_inventory_catches_unflagged_launch_shapes(dockerfile: str) -> None:
    launches = _dockerfile_launches(_Text(dockerfile))  # type: ignore[arg-type]
    assert launches, f"scan did not see the launch: {dockerfile}"
    assert not all(_launch_ok(o) for o in launches), f"scan accepted: {dockerfile}"


def test_inventory_accepts_flagged_and_restore_launches() -> None:
    ok = [
        "RUN java -XX:-UseBASE64Intrinsics -jar /app/w.jar --run /s",
        'ENTRYPOINT ["java", "-XX:-UseBASE64Intrinsics", "-jar", "/app/w.jar"]',
        'ENTRYPOINT ["java", "-XX:CRaCRestoreFrom=/app/checkpoint"]',
    ]
    for df in ok:
        launches = _dockerfile_launches(_Text(df))  # type: ignore[arg-type]
        assert launches and all(_launch_ok(o) for o in launches), df


DOCKERFILES = sorted(DOCKER.glob("Dockerfile.*"))
SCRIPTS = sorted(
    {
        *REPO.glob("scripts/*.sh"),
        *REPO.glob("deploy/**/*.sh"),
        *REPO.glob("deploy/firecracker/init*"),
    }
)


def test_inventory_finds_the_launch_paths() -> None:
    # Guard against the scan silently matching nothing (and so proving nothing).
    docker = [o for df in DOCKERFILES for o in _dockerfile_launches(df)]
    scripts = [o for sc in SCRIPTS for o in _script_launches(sc)]
    assert len(docker) >= 8, docker
    assert len(scripts) >= 3, scripts


@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda p: p.name)
def test_every_dockerfile_java_launch_disables_the_intrinsic(dockerfile: Path) -> None:
    bad = [o for o in _dockerfile_launches(dockerfile) if not _launch_ok(o)]
    assert not bad, f"{dockerfile.name}: java launch without a final {FLAG}: {bad}"


@pytest.mark.parametrize(
    "dockerfile",
    ["Dockerfile.default", "Dockerfile.localtika", "Dockerfile.default.localsrc"],
)
def test_temurin_runtime_images_set_java_tool_options(dockerfile: str) -> None:
    # The catch-all for any java started inside the cold-worker image family.
    ins = [i for i in _instructions(DOCKER / dockerfile) if i.startswith("ENV JAVA_TOOL_OPTIONS=")]
    assert ins, dockerfile
    for i in ins:
        settings = [t for t in _tokens(i.split("=", 1)[1]) if "UseBASE64Intrinsics" in t]
        assert settings and settings[-1] == FLAG, i


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: str(p.relative_to(REPO)))
def test_scripts_launching_java_disable_the_intrinsic(script: Path) -> None:
    bad = [o for o in _script_launches(script) if not _launch_ok(o)]
    assert not bad, f"{script.relative_to(REPO)}: java launch without a final {FLAG}: {bad}"


def test_crac_worker_checkpoint_carries_the_marker() -> None:
    # The engine refuses to restore a checkpoint without the marker (one baked before the
    # mitigation keeps the intrinsic on), so the image that bakes the checkpoint the engine
    # restores must write it -- and only after the checkpoint actually exists.
    run = next(
        i for i in _instructions(DOCKER / "Dockerfile.crac-worker")
        if i.startswith("RUN ") and "CRaCCheckpointTo" in i
    )
    marker = f"/app/checkpoint/{eng._CRAC_BASE64_OFF_MARKER}"
    assert marker in run
    assert run.index("test -s /app/checkpoint/core.img") < run.index(marker)


def test_gvisor_java_tool_options_override_keeps_the_flag() -> None:
    # BLASTBOX_GVISOR_EXTRA_ENV REPLACES the image's JAVA_TOOL_OPTIONS for the gVisor tier.
    text = (DOCKER / "docker-compose.gvisor.yml").read_text()
    vals = re.findall(r"JAVA_TOOL_OPTIONS=([^\"\]]*)", text)
    assert vals, "gVisor overlay no longer sets JAVA_TOOL_OPTIONS -- re-check this test"
    for v in vals:
        settings = [t for t in v.split() if "UseBASE64Intrinsics" in t]
        assert settings and settings[-1] == FLAG, v


# --- live JVM: the flag is actually in effect ------------------------------------------------


@pytest.mark.skipif(shutil.which("java") is None, reason="no java on PATH")
def test_live_jvm_reports_the_intrinsic_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("REDTUSK_AOT_CACHE", "")  # no cache on a dev box; flags only
    argv = eng._java_worker_argv(Path("/scr"))
    jvm_flags = argv[1 : argv.index("-jar")]
    r = subprocess.run(
        ["java", *jvm_flags, "-XX:+PrintFlagsFinal", "-version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    line = next(ln for ln in r.stdout.splitlines() if " UseBASE64Intrinsics " in ln)
    assert re.search(r"UseBASE64Intrinsics\s+=\s+false", line), line


# --- environment overrides and stale checkpoints ----------------------------------------------


def test_jvm_env_appends_the_flag_to_java_options() -> None:
    # HotSpot reads _JAVA_OPTIONS after the command line, so it would beat the argv's flag.
    env = eng._jvm_env({"_JAVA_OPTIONS": "-XX:+UseBASE64Intrinsics", "PATH": "/bin"})
    assert env["_JAVA_OPTIONS"].split()[-1] == FLAG
    assert env["PATH"] == "/bin"
    assert "_JAVA_OPTIONS" not in eng._jvm_env({"PATH": "/bin"})


@pytest.mark.parametrize("site", ["cold", "warmup", "crac"])
def test_every_booting_launch_site_neutralises_java_options(
    site: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("_JAVA_OPTIONS", "-XX:+UseBASE64Intrinsics")
    seen: list[dict[str, str]] = []

    class _LaunchedError(Exception):
        pass

    def capture(*_a: object, **kw: object) -> None:
        seen.append(kw["env"])  # type: ignore[arg-type]
        raise _LaunchedError

    monkeypatch.setattr(subprocess, "run", capture)
    monkeypatch.setattr(subprocess, "Popen", capture)
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    if site == "cold":
        with pytest.raises(_LaunchedError):
            eng._run_worker(inp, tmp_path / "rmeta", timeout=5)
    elif site == "warmup":
        eng.RedTuskEngine().warmup()  # fail-soft: swallows the error
    else:
        ckpt = tmp_path / "ckpt"
        ckpt.mkdir()
        (ckpt / eng._CRAC_BASE64_OFF_MARKER).touch()
        with pytest.raises(_LaunchedError):
            eng._crac_restore_worker(
                inp, tmp_path / "rmeta", checkpoint_dir=str(ckpt),
                scratch_dir=str(tmp_path / "scr"), timeout=5,
            )
    assert seen, f"{site}: no JVM launched"
    if site == "crac":
        # A restore keeps the checkpoint's flags and CRaC rejects any non-restore-settable
        # option at restore, so appending the flag would only break every restore.
        assert seen[0]["_JAVA_OPTIONS"] == "-XX:+UseBASE64Intrinsics"
    else:
        assert seen[0]["_JAVA_OPTIONS"].split()[-1] == FLAG


def test_crac_restore_refuses_a_checkpoint_without_the_marker(tmp_path: Path) -> None:
    ckpt = tmp_path / "ckpt"
    ckpt.mkdir()
    (ckpt / "core.img").write_bytes(b"x")
    scratch = tmp_path / "scr"
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    with pytest.raises(RuntimeError, match="redtusk-base64-intrinsics-off"):
        eng._crac_restore_worker(
            inp, tmp_path / "rmeta", checkpoint_dir=str(ckpt), scratch_dir=str(scratch),
            timeout=5,
        )
    assert not scratch.exists(), "nothing may be staged for a refused checkpoint"


def test_stale_checkpoint_falls_back_to_a_cold_jvm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ckpt = tmp_path / "ckpt"
    ckpt.mkdir()
    (ckpt / "core.img").write_bytes(b"x")
    inp = tmp_path / "in.txt"
    inp.write_bytes(b"x")
    calls: list[str] = []
    restores: list[object] = []
    monkeypatch.setenv("REDTUSK_CRAC_CHECKPOINT", str(ckpt))
    monkeypatch.setenv("REDTUSK_CRAC_SCRATCH", str(tmp_path / "scr"))
    monkeypatch.setattr(eng, "_run_worker", lambda i, r, *, timeout: calls.append("cold"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: restores.append(a))
    eng.RedTuskEngine()._produce_rmeta(inp, tmp_path / "rmeta", 5.0)
    assert restores == [], "a checkpoint without the marker must never be restored"
    assert calls == ["cold"]


@pytest.mark.skipif(shutil.which("java") is None, reason="no java on PATH")
def test_live_jvm_java_options_cannot_reenable_the_intrinsic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("REDTUSK_AOT_CACHE", "")
    argv = eng._java_worker_argv(Path("/scr"))
    env = eng._jvm_env({**os.environ, "_JAVA_OPTIONS": "-XX:+UseBASE64Intrinsics"})
    r = subprocess.run(
        ["java", *argv[1 : argv.index("-jar")], "-XX:+PrintFlagsFinal", "-version"],
        capture_output=True, text=True, timeout=60, check=False, env=env,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    line = next(ln for ln in r.stdout.splitlines() if " UseBASE64Intrinsics " in ln)
    assert re.search(r"UseBASE64Intrinsics\s+=\s+false", line), line


_JAR = os.environ.get("REDTUSK_WORKER_JAR", "")


@pytest.mark.skipif(
    shutil.which("java") is None or not Path(_JAR).is_file(),
    reason="needs java and REDTUSK_WORKER_JAR",
)
def test_worker_refuses_to_start_with_the_intrinsic_on(tmp_path: Path) -> None:
    # The backstop for a launcher this file does not know about: the worker itself exits
    # before announcing ready (so before reading any input) when the intrinsic is on.
    probe = subprocess.run(
        ["java", "-XX:+UseBASE64Intrinsics", "-XX:+PrintFlagsFinal", "-version"],
        capture_output=True, text=True, timeout=60, check=False,
        env={k: v for k, v in os.environ.items() if k != "_JAVA_OPTIONS"},
    )
    if not re.search(r"UseBASE64Intrinsics\s+=\s+true", probe.stdout):
        pytest.skip("this CPU cannot enable the Base64 intrinsic, so the guard has nothing to do")
    for d in ("in", "control"):
        (tmp_path / d).mkdir()
    r = subprocess.run(
        ["java", "-XX:+UseBASE64Intrinsics", "--enable-native-access=ALL-UNNAMED",
         "-jar", _JAR, "--run", str(tmp_path)],
        capture_output=True, text=True, timeout=120, check=False,
        env={k: v for k, v in os.environ.items() if k != "_JAVA_OPTIONS"},
    )
    assert r.returncode == 2, (r.returncode, r.stderr[-2000:])
    assert "CVE-2026-114938" in r.stderr
    assert not (tmp_path / "control" / "control.ready").exists()
