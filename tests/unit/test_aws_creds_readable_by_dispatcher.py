"""The burst credentials must be readable by the uid the dispatcher runs as.

`docker-compose.aws-burst.yml` mounts the deploy user's `.aws` read-only at
`/aws`, and `Dockerfile.host` runs the dispatcher as UID 10001. A normal `~/.aws`
is `0700` owned by the deploy user with `0600` credentials, so mounting it leaves
that process unable to read a byte -- measured on toolz2, where a real access test
as uid 10001 against the deploy user's credentials returns false.

The tier then fails CLOSED and stays on the local FC/gVisor tiers, which is
silent by design. Meanwhile `scripts/prepare_node_ubuntu.sh --check` ran its
`aws sts` probe as the DEPLOY user and printed `valid`. Green check, dead tier.

The same class is already recorded in that script for the node-autosizer share
directory, which had to be owned by the worker uid for exactly this reason.

These tests source the REAL helper out of the script and run it. The reporting is
what was silent, so both branches of the probe are driven through the documented
override rather than asserted from the source text.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "prepare_node_ubuntu.sh"
COMPOSE = REPO_ROOT / "deploy" / "docker" / "docker-compose.aws-burst.yml"
DOCKERFILE = REPO_ROOT / "deploy" / "docker" / "Dockerfile.host"


def _status(readable: str, tmp_path: Path) -> tuple[str, str]:
    """Run the real `_aws_creds_status` with the probe forced either way.

    Only the function definitions are taken from the script -- running the
    provisioner itself would provision the machine running the tests.
    """
    text = SCRIPT.read_text()

    def block(name: str) -> str:
        m = re.search(rf"^{re.escape(name)}\(\) \{{.*?^\}}", text, re.S | re.M)
        assert m, f"{name} not found in {SCRIPT}"
        return m.group(0)

    uid_log = tmp_path / "uid-asked"
    creds = tmp_path / ".aws" / "credentials"
    creds.parent.mkdir(parents=True)
    creds.write_text("[default]\n")
    harness = "\n".join([
        "set -u",
        f'DEPLOY_USER={Path.home().name!r}',
        f'AWS_CREDS_HOME={str(tmp_path)!r}',
        # Derived the way the script derives it, NOT hardcoded: `sudo
        # prepare_node_ubuntu.sh` is the documented invocation, so SUDO is ""
        # on the primary path. A harness that pinned it to "sudo" tested a
        # configuration the deployment never uses -- and hid a probe that was
        # inert as root.
        'SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO=sudo',
        'have() { command -v "$1" >/dev/null; }',
        "aws() { return 0; }",           # the sts probe passes
        block("_aws_creds_home"),
        block("_aws_sts_ok"),
        block("_aws_creds_status"),
        # The probe is REPLACED rather than driven through a flag, so the harness
        # sees which uid the real call site asks about. A production hook that
        # exists only for tests is one more thing that can drift from the caller.
        f'_aws_readable_by_uid() {{ echo "$1" > {str(uid_log)!r}; return {readable}; }}',
        "_aws_creds_status",
    ])
    res = subprocess.run(["bash", "-c", harness], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    asked = uid_log.read_text().strip() if uid_log.exists() else ""
    return res.stdout.strip(), asked


def test_credentials_the_dispatcher_uid_cannot_read_are_reported_unusable(tmp_path: Path) -> None:
    out, _ = _status("1", tmp_path)
    assert "UNUSABLE" in out, out
    assert "cannot read" in out
    assert "fail closed" in out


def test_credentials_the_dispatcher_uid_can_read_are_reported_valid(tmp_path: Path) -> None:
    """The counterweight. Without it, 'reports UNUSABLE' would also be satisfied
    by a probe that says UNUSABLE unconditionally."""
    out, _ = _status("0", tmp_path)
    assert out.startswith("valid"), out
    assert "UNUSABLE" not in out


def test_an_unrunnable_probe_is_reported_as_unknown_not_as_valid(tmp_path: Path) -> None:
    """`sts ok` plus an unchecked uid is NOT the same claim as `sts ok`, and the
    difference is exactly the failure this file exists for."""
    out, _ = _status("2", tmp_path)
    assert "NOT CHECKED" in out, out


def test_the_uid_checked_is_the_uid_the_dispatcher_runs_as(tmp_path: Path) -> None:
    """A probe against the wrong uid would satisfy every test above and prove
    nothing, so the harness records the uid the REAL call site asks about."""
    _out, asked = _status("0", tmp_path)
    assert asked == "10001", (
        f"the readability probe asked about uid {asked!r}, "
        "not the uid Dockerfile.host runs the dispatcher as"
    )
    assert re.search(r"^USER 10001:10001$", DOCKERFILE.read_text(), re.M), \
        "Dockerfile.host no longer runs the dispatcher as 10001"


def test_the_overlay_still_mounts_the_credentials_read_only() -> None:
    """Read-only is the reason the uid matters: the dispatcher cannot fix the
    permissions from inside, so the host has to be right."""
    assert ":/aws:ro" in COMPOSE.read_text()


def _probe(sudo_behaviour: str, tmp_path: Path) -> int:
    """Run the REAL `_aws_readable_by_uid` with `sudo` and `setpriv` stubbed.

    The harness above replaces this function, so its own logic needs exercising
    separately -- and its logic is where the first version was wrong.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_aws_readable_by_uid\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "probe not found"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    # Both mechanisms are stubbed, and `sudo` too: the probe picks a prefix from
    # whether it is root, so pinning only one of them would leave a path untested.
    for name in ("sudo", "setpriv", "su"):
        (bindir / name).write_text(sudo_behaviour)
        (bindir / name).chmod(0o755)
    harness = "\n".join([
        "set -u",
        f'export PATH={str(bindir)!r}:$PATH',
        'SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO=sudo',
        m.group(0),
        '_aws_readable_by_uid 10001 /some/file; echo "rc=$?"',
    ])
    res = subprocess.run(["bash", "-c", harness], capture_output=True, text=True, timeout=60)
    m2 = re.search(r"rc=(\d+)", res.stdout)
    assert m2, f"probe produced no rc line: {res.stdout!r} {res.stderr!r}"
    return int(m2.group(1))


def test_the_probe_reports_unknown_when_it_cannot_run_at_all(tmp_path: Path) -> None:
    """`sudo -u "#10001"` fails with `unknown user #10001` on a host with no passwd
    entry for that uid -- which is EVERY host here, since the user exists only
    inside the image. Reading that failure as "cannot read" convicts a correctly
    provisioned node, and the first version of this probe did exactly that.

    Verified on toolz2: that sudo form really does fail there.
    """
    assert _probe("#!/bin/sh\nexit 1\n", tmp_path) == 2


def test_the_probe_reports_not_readable_only_on_an_actual_no(tmp_path: Path) -> None:
    assert _probe("#!/bin/sh\necho NO\n", tmp_path) == 1


def test_the_probe_reports_readable_on_yes(tmp_path: Path) -> None:
    assert _probe("#!/bin/sh\necho YES\n", tmp_path) == 0


def test_the_config_file_is_checked_when_it_exists(tmp_path: Path) -> None:
    """The overlay sets `AWS_CONFIG_FILE=/aws/config`, and a role profile does not
    resolve without it -- so an unreadable config fails the tier exactly as an
    unreadable credentials file does. Absent is fine; present-but-unreadable is not.
    """
    text = SCRIPT.read_text()
    assert 'conf="$home/.aws/config"' in text
    assert "[ -f \"$conf\" ]" in text, "an absent config must not be treated as broken"


def test_the_remediations_cover_the_config_file_too() -> None:
    """A remediation that exposes only `credentials` leaves a role profile broken
    in the same silent way, so both documented fixes have to mention config."""
    text = SCRIPT.read_text()
    copy_block = text[text.index("install -d -m 0500"):]
    assert ".aws/config /etc/redtusk/aws/" in copy_block[:600], "the copy remediation skips config"
    acl_block = text[text.index("setfacl -m"):]
    assert ".aws/config" in acl_block[:600], "the ACL remediation skips config"


def test_a_non_root_caller_runs_setpriv_through_sudo(tmp_path: Path) -> None:
    """The prefix has to COMPOSE with the tool, not replace it.

    A non-root caller must end up running `sudo -n setpriv ...`; the first version
    of this probe built the command as `$SUDO -n <tool>`, which as root -- the
    documented `sudo prepare_node_ubuntu.sh` invocation, where SUDO is "" --
    expanded to a command literally beginning with `-n`. Every probe then returned
    unknown and the check was inert on the primary deployment path (codex).

    The root half of that decision cannot be exercised from a test that is not
    root; it is verified on toolz2 instead, where as root the probe returns 1 for
    the deploy user's 0600 credentials and 0 for a world-readable file. This test
    pins the half that IS reachable, so the composition cannot silently regress.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_aws_readable_by_uid\(\) \{.*?^\}", text, re.S | re.M)
    assert m
    bindir = tmp_path / "bin"
    bindir.mkdir()
    argv_log = tmp_path / "argv"
    for name in ("sudo", "setpriv", "su"):
        (bindir / name).write_text(
            f'#!/bin/sh\necho "{name} $*" >> {str(argv_log)!r}\nexit 1\n'
        )
        (bindir / name).chmod(0o755)
    harness = "\n".join([
        "set -u",
        f'export PATH={str(bindir)!r}:$PATH',
        m.group(0),
        "_aws_readable_by_uid 10001 /some/file || true",
    ])
    subprocess.run(["bash", "-c", harness], capture_output=True, text=True, timeout=60)
    seen = argv_log.read_text() if argv_log.exists() else ""
    assert "sudo -n setpriv --reuid=10001" in seen, (
        f"a non-root caller did not run setpriv through sudo; saw: {seen!r}"
    )

