"""The burst credentials must be readable by the uid the dispatcher runs as.

`docker-compose.aws-burst.yml` mounts the deploy user's `.aws` read-only at `/aws`,
and `Dockerfile.host` runs the dispatcher as UID 10001 with no capabilities. A
normal `~/.aws` is 0700/0600 owned by the deploy user, so that process cannot read
it and the tier fails CLOSED -- silently -- while `prepare_node_ubuntu.sh --check`
ran `aws sts` as the deploy user and printed `valid`.

The helpers are lifted out of the REAL script and run under bash; running the
provisioner itself would provision the test machine. `aws`, `setpriv` and `sudo`
are stubs on PATH, so nothing here escalates privilege or touches AWS.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "prepare_node_ubuntu.sh"
DOCKER_DIR = REPO_ROOT / "deploy" / "docker"

HELPERS = ("_aws_creds_home", "_dispatcher_ids", "_aws_creds_dir",
           "_aws_creds_effective_dir", "_aws_sts_ok",
           "_aws_readable_by_dispatcher", "_aws_creds_status")


def _block(name: str) -> str:
    m = re.search(rf"^{re.escape(name)}\(\) \{{.*?^\}}", SCRIPT.read_text(), re.S | re.M)
    assert m, f"{name} not found in {SCRIPT}"
    return m.group(0)


def _stub(bindir: Path, name: str, body: str) -> None:
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body)
    p.chmod(0o755)


def _run(tmp_path: Path, call: str, *, stub: dict[str, str] | None = None,
         env: dict[str, str] | None = None, repo_root: Path | None = None,
         probe: str | None = None, sts_rc: int = 0) -> str:
    """Run `call` with the script's helpers defined.

    `probe` replaces `_aws_readable_by_dispatcher` with a shell body when given.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    _stub(bindir, "aws",
          f'echo "$AWS_SHARED_CREDENTIALS_FILE" > "{tmp_path}/sts-file"; exit {sts_rc}\n')
    if repo_root is not None:
        (repo_root / "deploy" / "docker").mkdir(parents=True, exist_ok=True)
    # Without docker, _aws_creds_dir cannot resolve and the fallback is used.
    path = f"{bindir}:/usr/bin:/bin"
    for name, body in (stub or {}).items():
        _stub(bindir, name, body)
    defs = [_block(h) for h in HELPERS]
    if probe is not None:
        defs.append(f"_aws_readable_by_dispatcher() {{ {probe}; }}")
    script = "\n".join([
        "set -euo pipefail",
        'have() { command -v "$1" >/dev/null 2>&1; }',
        f"REPO_ROOT={str(repo_root or tmp_path / 'norepo')!r}",
        "DEPLOY_USER=nobody-here",
        *defs,
        call,
    ])
    base = {k: v for k, v in os.environ.items()
            if not k.startswith(("AWS_", "REDTUSK_WORKER_"))}
    res = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60,
                         env={**base, "PATH": path, "AWS_CREDS_HOME": str(tmp_path / "home"),
                              **(env or {})})
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def _creds(tmp_path: Path, *, config: bool = False) -> Path:
    d = tmp_path / "home" / ".aws"
    d.mkdir(parents=True, exist_ok=True)
    (d / "credentials").write_text("[default]\n")
    if config:
        (d / "config").write_text("[default]\n")
    return d


# ── the verdict ────────────────────────────────────────────────────────────

def _resolved(d: Path) -> dict[str, str]:
    """A docker stub so compose 'resolves' the mount to `d` (via python3)."""
    return {"docker": f"echo '{{\"services\":{{\"dispatcher-aws-burst\":{{\"volumes\":"
                      f"[{{\"target\":\"/aws\",\"source\":\"{d}\"}}]}}}}}}'\n"}


def test_unreadable_credentials_are_unusable(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path,
               probe="return 1")
    assert out.startswith("UNUSABLE"), out
    assert "uid 10001" in out and "fail closed" in out


def test_readable_credentials_are_valid(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path,
               probe="return 0")
    assert out.startswith("valid") and "readable by uid 10001" in out, out
    assert "NOT CONFIRMED" not in out


def test_an_untestable_probe_is_not_confirmed(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path,
               probe="return 2")
    assert "NOT CONFIRMED" in out and "could not be tested" in out, out


def test_an_unreadable_config_is_unusable_and_an_absent_one_is_fine(tmp_path: Path) -> None:
    d = _creds(tmp_path, config=True)
    probe = 'case "$1" in */config) return 1 ;; esac; return 0'
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path, probe=probe)
    assert out.startswith("UNUSABLE") and str(d / "config") in out, out
    (d / "config").unlink()
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path, probe=probe)
    assert out.startswith("valid") and "NOT CONFIRMED" not in out, out


def test_a_symlinked_credentials_file_is_not_confirmed(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    real = tmp_path / "elsewhere"
    (d / "credentials").rename(real)
    (d / "credentials").symlink_to(real)
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(d), repo_root=tmp_path,
               probe="return 0")
    assert "NOT CONFIRMED" in out and "symlink" in out, out


def test_an_unresolved_mount_is_never_convicted(tmp_path: Path) -> None:
    """Without compose the directory is a guess at the deploy user's ~/.aws; an
    unreadable guess must not be reported as a definitive UNUSABLE."""
    _creds(tmp_path)
    out = _run(tmp_path, "_aws_creds_status", probe="return 1")
    assert not out.startswith("UNUSABLE") and "NOT CONFIRMED" in out, out
    assert "compose could not resolve" in out


def test_sts_and_the_probe_use_the_mounted_directory(tmp_path: Path) -> None:
    _creds(tmp_path)  # a home copy that must NOT be the one checked
    mounted = tmp_path / "etc-aws"
    mounted.mkdir()
    (mounted / "credentials").write_text("[default]\n")
    out = _run(tmp_path, "_aws_creds_status", stub=_resolved(mounted), repo_root=tmp_path,
               probe=f'echo "$1" > "{tmp_path}/probed"; return 0')
    assert str(mounted / "credentials") in out, out
    assert (tmp_path / "sts-file").read_text().strip() == str(mounted / "credentials")
    assert (tmp_path / "probed").read_text().strip() == str(mounted / "credentials")


def test_the_dispatcher_ids_match_the_dockerfile_and_honour_the_override(tmp_path: Path) -> None:
    assert re.search(r"^USER 10001:10001$", (DOCKER_DIR / "Dockerfile.host").read_text(), re.M)
    assert _run(tmp_path, "_dispatcher_ids") == "10001 10001"
    assert _run(tmp_path, "_dispatcher_ids", env={"REDTUSK_WORKER_UID": "2000"}) == "2000 2000"
    assert _run(tmp_path, "_dispatcher_ids",
                env={"REDTUSK_WORKER_UID": "2000", "REDTUSK_WORKER_GID": "3000"}) == "2000 3000"


# ── the probe itself ───────────────────────────────────────────────────────

SETPRIV_RECORDER = (
    # Record cwd + args, then run what follows the option list, as setpriv would.
    'echo "$PWD" > "$REC"; echo "$*" >> "$REC"\n'
    'while [ $# -gt 0 ]; do case "$1" in --*) shift ;; *) break ;; esac; done\n'
    'exec "$@"\n'
)


def test_the_probe_drops_ids_groups_and_capabilities_from_inside_the_dir(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    rec = tmp_path / "rec"
    out = _run(tmp_path, f'_aws_readable_by_dispatcher {d}/credentials && echo RC0 || echo RC$?',
               stub={"setpriv": SETPRIV_RECORDER, "sudo": '[ "$1" = -n ] && shift; exec "$@"\n'},
               env={"REC": str(rec), "REDTUSK_WORKER_GID": "10002"})
    assert out == "RC0", out
    cwd, args = rec.read_text().splitlines()[:2]
    assert cwd == str(d)
    for flag in ("--reuid=10001", "--regid=10002", "--clear-groups", "--bounding-set=-all",
                 "--inh-caps=-all", "--ambient-caps=-all", "--nnp"):
        assert flag in args.split(), (flag, args)
    assert args.split()[-1] == "credentials", "must test a RELATIVE name"


def test_the_probe_reports_no_only_on_an_actual_no(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    (d / "credentials").chmod(0)
    if os.access(d / "credentials", os.R_OK):
        pytest.skip("running with DAC override; cannot make an unreadable file")
    out = _run(tmp_path, f'_aws_readable_by_dispatcher {d}/credentials && echo RC0 || echo RC$?',
               stub={"setpriv": SETPRIV_RECORDER, "sudo": '[ "$1" = -n ] && shift; exec "$@"\n'},
               env={"REC": str(tmp_path / "rec")})
    assert out == "RC1", out


@pytest.mark.parametrize("stub", [
    {},                                                   # no setpriv
    {"setpriv": "exit 1\n", "sudo": "exit 1\n"},          # sudo -n refused
])
def test_a_probe_that_cannot_run_is_unknown(tmp_path: Path, stub: dict[str, str]) -> None:
    d = _creds(tmp_path)
    out = _run(tmp_path, f'_aws_readable_by_dispatcher {d}/credentials && echo RC0 || echo RC$?',
               stub=stub)
    assert out == "RC2", out


def test_a_non_numeric_id_is_unknown_not_guessed(tmp_path: Path) -> None:
    d = _creds(tmp_path)
    out = _run(tmp_path, f'_aws_readable_by_dispatcher {d}/credentials && echo RC0 || echo RC$?',
               stub={"setpriv": SETPRIV_RECORDER}, env={"REDTUSK_WORKER_UID": "redtusk"})
    assert out == "RC2", out


# ── the mount, as compose resolves it ──────────────────────────────────────

def _compose_ok() -> bool:
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "compose", "version"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _compose_ok(), reason="docker compose not available")
def test_compose_resolves_the_mount_with_the_deploy_users_home(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(DOCKER_DIR, repo / "deploy" / "docker",
                    ignore=shutil.ignore_patterns(".env"))
    (repo / "deploy" / "docker" / ".env").write_text("AWS_CREDS_DIR=${HOME}/.aws\n")
    run_env = {"PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}"}
    script = "\n".join([
        'have() { command -v "$1" >/dev/null 2>&1; }',
        f"REPO_ROOT={str(repo)!r}", "DEPLOY_USER=nobody-here",
        _block("_aws_creds_home"), _block("_aws_creds_dir"), "_aws_creds_dir",
    ])
    base = {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}

    def resolve(extra: dict[str, str]) -> str:
        r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=120,
                           env={**base, **run_env, "AWS_CREDS_HOME": "/home/deployer", **extra})
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    assert resolve({}) == "/home/deployer/.aws"
    # An exported value beats .env, exactly as it does for `docker compose up`.
    assert resolve({"AWS_CREDS_DIR": "/etc/redtusk/aws"}) == "/etc/redtusk/aws"


def test_the_docs_name_the_flag_the_parser_accepts() -> None:
    for f in (DOCKER_DIR / ".env.example", DOCKER_DIR / "docker-compose.aws-burst.yml"):
        assert "--status" not in f.read_text(), f
    assert re.search(r"--check\)\s+CHECK_ONLY=1", SCRIPT.read_text())


def test_the_overlay_still_mounts_the_credentials_read_only() -> None:
    text = (DOCKER_DIR / "docker-compose.aws-burst.yml").read_text()
    assert re.search(r"\$\{AWS_CREDS_DIR:\?[^}]*\}:/aws:ro", text)
    assert "AWS_SHARED_CREDENTIALS_FILE=/aws/credentials" in text
