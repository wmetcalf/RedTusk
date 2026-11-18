"""CVE-2026-114938 ("Java4Shell") mitigation: every worker JVM runs with the HotSpot
Base64 intrinsic OFF (``-XX:-UseBASE64Intrinsics``).

The bug is a heap overflow in the AVX-512 VBMI Base64 *decode intrinsic* (JDK 17.0.6+ .. 27).
Hostile documents reach ``java.util.Base64`` inside the Tika fork (e.g. ICalParser's inline
ATTACH), so a JVM that boots without the flag is exploitable on a VBMI-capable host. These
tests fail if any launch path loses the flag: the engine argv (cold + warm FC/gVisor, which
all go through ``_java_worker_argv``), every ``java`` invocation in the Dockerfiles (AOT bake,
CRaC/warp checkpoint, ENTRYPOINT), the release/checkpoint scripts, and the gVisor tier's
JAVA_TOOL_OPTIONS override.
"""
from __future__ import annotations

import re
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


_SEGMENT_SPLIT = re.compile(r"&&|\|\||;")
_ENV_ASSIGN = re.compile(r"^(?:[A-Z_][A-Z0-9_]*=\S*\s+)+")


def _java_commands(shell: str) -> list[str]:
    """Each `java ...` command in a shell string (env-assignment prefixes stripped)."""
    cmds = []
    for seg in _SEGMENT_SPLIT.split(shell):
        seg = _ENV_ASSIGN.sub("", seg.strip())
        if re.match(r"^java\s", seg):
            cmds.append(seg)
    return cmds


def _is_restore_only(cmd: str) -> bool:
    # A CRaC/warp RESTORE resumes the checkpointed process with the checkpoint's VM flags; the
    # flag belongs on the checkpoint-creating JVM (asserted separately), not on restore.
    return "CRaCRestoreFrom" in cmd and "CRaCCheckpointTo" not in cmd


DOCKERFILES = sorted(DOCKER.glob("Dockerfile.*"))


def test_inventory_finds_the_launch_paths() -> None:
    # Guard against the scan silently matching nothing (and so proving nothing).
    runs = [
        c
        for df in DOCKERFILES
        for ins in _instructions(df)
        if ins.startswith("RUN ")
        for c in _java_commands(ins[4:])
    ]
    assert len(runs) >= 8, runs


@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda p: p.name)
def test_every_dockerfile_java_launch_disables_the_intrinsic(dockerfile: Path) -> None:
    missing = []
    for ins in _instructions(dockerfile):
        if ins.startswith("RUN "):
            for cmd in _java_commands(ins[4:]):
                if not _is_restore_only(cmd) and FLAG not in cmd:
                    missing.append(cmd[:160])
        elif ins.startswith("ENTRYPOINT [") and '"java"' in ins:
            if not _is_restore_only(ins) and f'"{FLAG}"' not in ins:
                missing.append(ins[:160])
    assert not missing, f"{dockerfile.name}: java launch without {FLAG}: {missing}"


@pytest.mark.parametrize(
    "dockerfile",
    ["Dockerfile.default", "Dockerfile.localtika", "Dockerfile.default.localsrc"],
)
def test_temurin_runtime_images_set_java_tool_options(dockerfile: str) -> None:
    # The catch-all for any java started inside the cold-worker image family.
    ins = _instructions(DOCKER / dockerfile)
    assert any(
        i.startswith("ENV JAVA_TOOL_OPTIONS=") and FLAG in i for i in ins
    ), dockerfile


@pytest.mark.parametrize(
    "script", ["deploy/docker/build-vsock-checkpoint.sh", "scripts/release_engine.sh"]
)
def test_scripts_launching_java_disable_the_intrinsic(script: str) -> None:
    code = "\n".join(
        ln for ln in (REPO / script).read_text().splitlines() if not ln.lstrip().startswith("#")
    )
    joined = re.sub(r"\\\n\s*", " ", code)
    # A java launch is `java` followed by an option, up to its `-jar` (or end of line).
    cmds = [
        m.group(0)
        for m in re.finditer(r"(?<![\w/.$-])java\s+-[^\n]*?(?=\s-jar\s|$)", joined, re.M)
    ]
    assert cmds, f"{script}: no java invocation found -- the scan is stale"
    for c in cmds:
        assert FLAG in c, f"{script}: {c[:160]}"


def test_gvisor_java_tool_options_override_keeps_the_flag() -> None:
    # BLASTBOX_GVISOR_EXTRA_ENV REPLACES the image's JAVA_TOOL_OPTIONS for the gVisor tier.
    text = (DOCKER / "docker-compose.gvisor.yml").read_text()
    vals = re.findall(r"JAVA_TOOL_OPTIONS=([^\"\]]*)", text)
    assert vals, "gVisor overlay no longer sets JAVA_TOOL_OPTIONS -- re-check this test"
    for v in vals:
        assert FLAG in v, v


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
