"""`prepare_node_ubuntu.sh` must not report a node ready without the tier it claims.

These tests EXECUTE the real script with every privileged call routed through a stub
`sudo`, so nothing on the host is touched: the only commands the script runs without
`$SUDO` operate inside its own `mktemp` directories.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "prepare_node_ubuntu.sh"

# The script's preflight requires a real /dev/kvm (the Firecracker tier needs it) and dies
# otherwise, which no unprivileged process can fake -- `unshare -r` cannot even map uids in
# the usual container. So this is skipped in container CI and runs on the fleet nodes and any
# KVM-capable workstation. Named precisely, because a skip nobody can satisfy is a test that
# does not exist.
pytestmark = [
    pytest.mark.skipif(
        not os.path.exists("/dev/kvm"),
        reason="prepare_node_ubuntu.sh preflight requires /dev/kvm (run on a fleet node)",
    ),
    # NEVER as root. The script computes `SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO=sudo`, so as
    # root the fake sudo is simply not used and every privileged call -- apt-get, usermod,
    # mkdir -p /var/lib/... -- resolves to the REAL binary and mutates the host. Stubbing the
    # individual tools (below) is defence in depth, but the set of privileged commands is
    # open-ended, so the guarantee has to be "not root", not "we remembered them all".
    pytest.mark.skipif(
        os.geteuid() == 0,
        reason="runs the real provisioning script; as root its $SUDO is empty and the "
               "stubs are bypassed, so this must only run unprivileged",
    ),
]


@pytest.fixture(scope="module")
def sysbin(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A mirror of the system PATH with `runsc` removed.

    `have runsc` has to be FALSE to reach the install branch at all, and on a node that
    already runs the gVisor tier the real binary is right there on the PATH.
    """
    d = tmp_path_factory.mktemp("sysbin")
    for src in ("/usr/bin", "/usr/sbin", "/sbin"):
        p = Path(src)
        if not p.is_dir():
            continue
        for f in p.iterdir():
            if f.name == "runsc" or (d / f.name).exists():
                continue
            try:
                (d / f.name).symlink_to(f)
            except OSError:
                pass
    assert shutil.which("bash", path=str(d)), "the mirror is missing bash"
    assert not shutil.which("runsc", path=str(d)), "runsc must not be reachable"
    return d


def _stubs(tmp_path: Path, *, apt_update_fails_for_gvisor: bool) -> tuple[Path, Path]:
    """Stub bin dir plus a log of every privileged command the script ran.

    The behaviour lives in the individual TOOL stubs, not in the `sudo` stub, because the
    script drops `$SUDO` entirely when it is already root -- so a stub that only intercepts
    `sudo` intercepts nothing there. `sudo` merely logs and executes, which means these
    tests exercise the same stubs either way.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ran = tmp_path / "ran.log"
    stage = tmp_path / "gvisor_stage"

    def stub(name: str, body: str) -> None:
        (bin_dir / name).write_text(f'#!/bin/sh\necho "{name} $*" >> {ran}\n{body}')

    stub("sudo", 'shift 0\nexec "$@"\n')          # log, then run the stubbed tool
    stub("apt-get",
         f'if [ "$1" = update ] && [ -f {stage} ]; then\n'
         + ("  echo \"E: Could not resolve 'storage.googleapis.com'\" >&2; exit 100\n"
            if apt_update_fails_for_gvisor else "  :\n")
         + "fi\nexit 0\n")
    # The gvisor repo is configured by `... | $SUDO tee /etc/apt/sources.list.d/gvisor.list`.
    stub("tee", f'case "$*" in *gvisor.list*) : > {stage} ;; esac\ncat >/dev/null\nexit 0\n')
    stub("gpg", "cat >/dev/null\nexit 0\n")       # drain stdin; no SIGPIPE upstream
    for tool in ("systemctl", "usermod", "groupadd", "install", "apt-mark"):
        stub(tool, "exit 0\n")
    # curl must emit something: `curl ... | $SUDO gpg` under pipefail turns an empty
    # producer into a 141 that stops the script before the code under test.
    stub("curl", 'echo "dummy-key"\nexit 0\n')
    for tool in ("docker", "firecracker", "jailer", "mkfs.ext4", "debugfs"):
        stub(tool, "exit 0\n")
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    return bin_dir, ran


def _prep(
    tmp_path: Path, sysbin: Path, *, apt_update_fails_for_gvisor: bool
) -> tuple[subprocess.CompletedProcess[str], str]:
    bin_dir, ran = _stubs(tmp_path, apt_update_fails_for_gvisor=apt_update_fails_for_gvisor)
    p = subprocess.run(
        ["bash", str(SCRIPT), "--deploy-user", os.environ.get("USER") or str(os.getuid()),
         "--no-fc-assets"],
        capture_output=True, text=True, check=False,
        env={"PATH": f"{bin_dir}:{sysbin}", "HOME": os.path.expanduser("~"),
             "USER": os.environ.get("USER", ""), "TERM": "dumb"},
    )
    return p, (ran.read_text() if ran.exists() else "")


def test_a_gvisor_repo_that_cannot_be_reached_fails_the_provision(
    tmp_path: Path, sysbin: Path
) -> None:
    """`apt-get update && apt-get install runsc` is exempt from `set -e`.

    An update that failed skipped the install and provisioning CARRIED ON: the node
    finished with rc=0, logged `runsc installed:` with an empty version (the failing
    `runsc --version` sits in a command substitution whose status nothing reads), and
    signed off telling the operator "the cold and gVisor tiers ... are unaffected" --
    while the gVisor tier did not exist. Silent-tier failures are how this fleet loses
    a whole runtime; they have to be loud at provision time.
    """
    p, ran = _prep(tmp_path, sysbin, apt_update_fails_for_gvisor=True)

    assert p.returncode != 0, "provisioning reported success without installing runsc"
    assert "runsc installed:" not in p.stdout, "claimed an install that never ran"
    assert "apt-get install -y -q runsc" not in ran, "fixture: the install should not be reached"
    # The apt-get STUB logged this line itself, not the sudo wrapper -- i.e. the interception
    # does not depend on $SUDO being non-empty. That is the property that keeps this safe if
    # the root guard above is ever relaxed.
    assert any(ln.startswith("apt-get ") for ln in ran.splitlines()), (
        f"the apt-get stub was bypassed; a real apt-get may have run: {ran!r}"
    )


def test_an_install_that_leaves_no_runsc_is_fatal(tmp_path: Path, sysbin: Path) -> None:
    """apt reports success and runsc is still not on PATH -- the package moved, the repo
    served a stub, the binary landed somewhere unexpected. Provisioning must not continue.
    """
    p, ran = _prep(tmp_path, sysbin, apt_update_fails_for_gvisor=False)

    assert p.returncode != 0
    assert "runsc is not on PATH" in p.stderr
    assert "apt-get install -y -q runsc" in ran, "fixture: the install should have been attempted"
