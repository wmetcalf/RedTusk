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

import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest


class Run(NamedTuple):
    """What one `_aws_creds_status` invocation reported and did.

    A record rather than attributes stashed on the function object: mypy rejects
    those (correctly -- the annotation does not describe them), and I reintroduced
    that mistake once already in this file after fixing it.
    """

    out: str
    uid_asked: str
    sts_files: str


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "prepare_node_ubuntu.sh"
COMPOSE = REPO_ROOT / "deploy" / "docker" / "docker-compose.aws-burst.yml"
DOCKERFILE = REPO_ROOT / "deploy" / "docker" / "Dockerfile.host"


def _status(readable: str, tmp_path: Path, *, unreadable: str = "",
            make_config: bool = False, creds_dir: str = "",
            symlink_to: str = "", extra_env: dict[str, str] | None = None,
            make_creds: bool = True, sts: str = "0") -> Run:
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
    sts_log = tmp_path / "sts-files"
    # A synthetic repo so the .env the status function consults is this test's.
    repo_root = tmp_path / "repo"
    (repo_root / "deploy" / "docker").mkdir(parents=True)
    if creds_dir:
        (repo_root / "deploy" / "docker" / ".env").write_text(f"AWS_CREDS_DIR={creds_dir}\n")
    shutil.copy2(DOCKERFILE, repo_root / "deploy" / "docker" / "Dockerfile.host")
    creds = tmp_path / ".aws" / "credentials"
    creds.parent.mkdir(parents=True, exist_ok=True)
    if make_creds:
        creds.write_text("[default]\n")
    if make_config:
        (tmp_path / ".aws" / "config").write_text("[profile x]\n")
    if symlink_to:
        if creds.exists() or creds.is_symlink():
            creds.unlink()
        creds.symlink_to(symlink_to)
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
        # Records WHICH credentials sts was pointed at -- a stub that only
        # returns 0 cannot tell a check of the mounted copy from a check of
        # the home one.
        'aws() { echo "$AWS_SHARED_CREDENTIALS_FILE|$AWS_CONFIG_FILE"'
        f' > {str(sts_log)!r}; return {sts}; }}',
        # REPO_ROOT is the scratch project for .env, but _dispatcher_uid reads the
        # real Dockerfile, so it is copied in.
        f'REPO_ROOT={str(repo_root)!r}',
        block("_aws_creds_home"),
        # STUBBED: resolving the mount is compose's job and has its own test
        # below. Injecting the real one would run `docker compose` against this
        # synthetic repo and resolve to nothing.
        f'_aws_creds_dir() {{ printf "%s" {creds_dir!r}; }}',
        block("_aws_sts_ok"),
        block("_dispatcher_uid"),
        block("_aws_link_hazard"),
        block("_aws_creds_status"),
        # The probe is REPLACED rather than driven through a flag, so the harness
        # sees which uid the real call site asks about. A production hook that
        # exists only for tests is one more thing that can drift from the caller.
        # Per-FILE, so one unreadable file among several is expressible -- the
        # config case cannot be stated with a single global answer.
        f'_aws_readable_by_uid() {{ echo "$1" > {str(uid_log)!r}; '
        f'case "$2" in *{unreadable or "__nomatch__"}) return 1 ;; esac; return {readable}; }}',
        "_aws_creds_status",
    ])
    res = subprocess.run(["bash", "-c", harness], capture_output=True, text=True,
                         timeout=60, env={**os.environ, **(extra_env or {})})
    assert res.returncode == 0, res.stderr
    return Run(
        out=res.stdout.strip(),
        uid_asked=uid_log.read_text().strip() if uid_log.exists() else "",
        sts_files=sts_log.read_text().strip() if sts_log.exists() else "",
    )


def test_credentials_the_dispatcher_uid_cannot_read_are_reported_unusable(tmp_path: Path) -> None:
    out = _status("1", tmp_path)
    assert "UNUSABLE" in out.out, out
    assert "cannot read" in out.out
    assert "fail closed" in out.out


def test_credentials_the_dispatcher_uid_can_read_are_reported_valid(tmp_path: Path) -> None:
    """The counterweight. Without it, 'reports UNUSABLE' would also be satisfied
    by a probe that says UNUSABLE unconditionally."""
    out = _status("0", tmp_path)
    assert out.out.startswith("valid"), out
    assert "UNUSABLE" not in out.out


def test_an_unrunnable_probe_is_reported_as_unknown_not_as_valid(tmp_path: Path) -> None:
    """`sts ok` plus an unchecked uid is NOT the same claim as `sts ok`, and the
    difference is exactly the failure this file exists for."""
    out = _status("2", tmp_path)
    assert "NOT CONFIRMED" in out.out, out


def test_the_uid_checked_is_the_uid_the_dispatcher_runs_as(tmp_path: Path) -> None:
    """A probe against the wrong uid would satisfy every test above and prove
    nothing, so the harness records the uid the REAL call site asks about."""
    run = _status("0", tmp_path)
    assert run.uid_asked == "10001", (
        f"the readability probe asked about uid {run.uid_asked!r}, "
        "not the uid Dockerfile.host runs the dispatcher as"
    )
    assert re.search(r"^USER 10001:10001$", DOCKERFILE.read_text(), re.M), \
        "Dockerfile.host no longer runs the dispatcher as 10001"


def _uid(*, docker_says: str | None, env: dict[str, str] | None = None,
         repo_root: Path | None = None) -> str:
    """Run the REAL `_dispatcher_uid` with `docker image inspect` stubbed.

    `docker_says` is what the stub prints; None means the image cannot be
    inspected (not present, or docker refuses). Stubbed rather than skipped
    because the answer must not depend on which images this host happens to
    have built -- a real `redtusk:dev` on the developer's machine makes every
    row pass for the wrong reason, and CI, which has none, then disagrees.
    """
    bindir = Path(tempfile.mkdtemp())
    if docker_says is None:
        (bindir / "docker").write_text("#!/bin/sh\nexit 1\n")
    else:
        (bindir / "docker").write_text(f"#!/bin/sh\nprintf '%s\\n' {docker_says!r}\n")
    (bindir / "docker").chmod(0o755)
    text = SCRIPT.read_text()
    m = re.search(r"^_dispatcher_uid\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "_dispatcher_uid not found"
    harness = "\n".join([
        "set -u",
        f"export PATH={f'{bindir}:' + os.environ['PATH']!r}",
        f"REPO_ROOT={str(repo_root or REPO_ROOT)!r}",
        'have() { command -v "$1" >/dev/null; }',
        m.group(0),
        "_dispatcher_uid",
    ])
    base = {k: v for k, v in os.environ.items() if k != "REDTUSK_WORKER_UID"}
    r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True,
                       timeout=60, env={**base, **(env or {}),
                                        "PATH": f"{bindir}:{os.environ['PATH']}"})
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _image(env_file: str = "", env: dict[str, str] | None = None,
           *, tmp_path: Path) -> str:
    """Run the REAL `_dispatcher_image` against the REAL compose files.

    `.env` is a compose-file rule, so the project is copied into a scratch
    directory to carry one without touching the repository.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_dispatcher_image\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "_dispatcher_image not found"
    root = Path(tempfile.mkdtemp(dir=tmp_path, prefix="project-"))
    (root / "deploy" / "docker").mkdir(parents=True)
    for name in ("docker-compose.yml", "docker-compose.aws-burst.yml"):
        shutil.copy2(REPO_ROOT / "deploy" / "docker" / name,
                     root / "deploy" / "docker" / name)
    if env_file:
        (root / "deploy" / "docker" / ".env").write_text(env_file)
    harness = "\n".join([
        "set -u",
        f'REPO_ROOT={str(root)!r}',
        'have() { command -v "$1" >/dev/null; }',
        "_aws_creds_home() { echo /home/tester; }",
        m.group(0),
        "_dispatcher_image",
    ])
    base = {k: v for k, v in os.environ.items() if k != "REDTUSK_IMAGE"}
    r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True,
                       timeout=180, env={**base, **(env or {})})
    return r.stdout.strip()


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_the_image_is_the_one_compose_will_actually_launch(tmp_path: Path) -> None:
    """`REDTUSK_IMAGE` is documented as a per-host `deploy/docker/.env` value,
    and .env is compose's file to read -- it is never exported into this script.
    Reading the environment alone inspected `redtusk:dev` while the node launches
    something else, so --check could validate credentials for the wrong uid and
    provisioning chown the node share to it (codex).

    The middle row is the finding, and the only one that discriminates: it is
    also the only row whose answer the environment cannot supply.
    """
    assert _image(tmp_path=tmp_path) == "redtusk:dev"
    assert _image("REDTUSK_IMAGE=redtusk:prod-42\n", tmp_path=tmp_path) == "redtusk:prod-42"
    assert _image("REDTUSK_IMAGE=redtusk:from-the-file\n",
                  {"REDTUSK_IMAGE": "redtusk:exported"},
                  tmp_path=tmp_path) == "redtusk:exported"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_the_image_is_readable_without_a_configured_creds_dir(tmp_path: Path) -> None:
    """The placeholder passed for AWS_CREDS_DIR has to be an ABSOLUTE path:
    compose reads a bare name as a NAMED VOLUME and rejects the whole project
    ("refers to undefined volume placeholder"), which would make the image
    unreadable on exactly the nodes being provisioned -- the ones whose .env is
    not finished yet. This fixture writes no AWS_CREDS_DIR at all.
    """
    assert _image("REDTUSK_IMAGE=redtusk:prod-42\n", tmp_path=tmp_path) == "redtusk:prod-42"


def test_the_image_is_resolved_once_before_anything_interpolates_the_uid() -> None:
    """Asking compose costs about a second and the burst notes interpolate
    `_dispatcher_uid` eight times, so the answer is resolved into a global once,
    at the top level -- a memo inside the function would not survive the `$( )`
    each of those call sites uses.
    """
    text = SCRIPT.read_text()
    assign = text.index('REDTUSK_IMAGE_RESOLVED="$(_dispatcher_image)"')
    check = text.index('if [ "$CHECK_ONLY" -eq 1 ]; then')
    assert assign < check, "the image is resolved after the check block already ran"
    assert 'image="${REDTUSK_IMAGE_RESOLVED:-${REDTUSK_IMAGE:-redtusk:dev}}"' in text, (
        "_dispatcher_uid no longer consumes the resolved image"
    )


OVERRIDE = {"REDTUSK_WORKER_UID": "2000"}


@pytest.mark.parametrize("docker_says,env,expected,why", [
    ("10001:10001", OVERRIDE, "10001",
     "the image that will run is authoritative; a stale override cannot move it"),
    ("12345:12345", OVERRIDE, "12345",
     "and that stays true when the image is NOT the stock one"),
    ("appuser", OVERRIDE, "2000",
     "a NAME resolves against the image's passwd, not this host's, so it is "
     "unusable here and the operator's answer is the next best source"),
    ("appuser", None, "10001",
     "with no override either, the repository's Dockerfile"),
    ("", OVERRIDE, "2000", "an image with no USER at all"),
    (None, OVERRIDE, "2000",
     "provisioning normally runs BEFORE the image exists; the override is then "
     "the only source there is"),
    (None, None, "10001", "and without one, the repository's Dockerfile"),
], ids=["image-stock", "image-custom", "image-name-with-override",
        "image-name-no-override", "image-no-user", "no-image-with-override",
        "no-image-no-override"])
def test_the_dispatcher_uid_comes_from_the_most_authoritative_source(
    docker_says: str | None, env: dict[str, str] | None, expected: str, why: str,
) -> None:
    """Two findings pulled in opposite directions and both were right (codex).

    Probing an operator's `REDTUSK_WORKER_UID` reported credentials readable by
    a uid the dispatcher never becomes; ignoring it chowns the node share to a
    uid a custom dispatcher image cannot write, silently disabling node sizing.
    `${REDTUSK_IMAGE}` selects the image in every compose file here, so the
    resolution is: the image if it can be asked, else the operator, else the
    repository's Dockerfile.
    """
    assert _uid(docker_says=docker_says, env=env) == expected, why


def test_the_uid_falls_back_when_there_is_no_repository_either(
    tmp_path: Path,
) -> None:
    """The last resort has to be a number, not empty: every caller interpolates
    this into a chown or an install, and an empty one would widen or fail them."""
    assert _uid(docker_says=None, repo_root=tmp_path) == "10001"


def test_the_node_share_is_owned_by_the_uid_the_dispatcher_runs_as() -> None:
    """The share is mode 2770 and the dispatcher writes it; an uninhabitable
    owner disables node sizing silently. This asserts the assignment feeding
    that chown goes through the same resolution as everything else -- it was
    briefly pinned to the repository's Dockerfile, which discards the override
    a custom `${REDTUSK_IMAGE}` needs (codex).
    """
    text = SCRIPT.read_text()
    assert re.search(r"^REDTUSK_WORKER_UID=\$\(_dispatcher_uid\)$", text, re.M), (
        "the node-share uid no longer comes from _dispatcher_uid"
    )
    chown = re.search(r'chown "\$REDTUSK_WORKER_UID:\$DGRP" "\$NODE_SHARE_DIR"', text)
    assert chown, "the node share is no longer chowned to REDTUSK_WORKER_UID"


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
    target = tmp_path / "creds"
    target.write_text("[default]\n")
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
        # A REAL path: the probe cds into the directory before dropping privilege,
        # modelling the bind mount, so a fixture pointing at a nonexistent
        # directory would measure the failed cd rather than the readability.
        f'_aws_readable_by_uid 10001 {str(target)!r}; echo "rc=$?"',
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


def test_an_unreadable_config_file_is_reported(tmp_path: Path) -> None:
    """The overlay sets `AWS_CONFIG_FILE=/aws/config`, and a role profile does not
    resolve without it -- so an unreadable config fails the tier exactly as an
    unreadable credentials file does.

    Driven through the status function rather than asserted from the source: an
    earlier version of this test pinned the literal `conf="$home/.aws/config"` and
    broke the moment that path was correctly derived from AWS_CREDS_DIR instead.
    """
    out = _status("0", tmp_path, unreadable="config", make_config=True)
    assert "UNUSABLE" in out.out, out
    assert "config" in out.out


def test_an_absent_config_file_is_not_treated_as_broken(tmp_path: Path) -> None:
    """A plain access-key profile needs no config, and convicting that setup would
    be a new false alarm on the common case."""
    # The stub answers "unreadable" for anything named config, so WITHOUT the
    # existence guard the absent file would be probed and reported UNUSABLE.
    # With `make_config=False` and a permissive stub the test could not tell.
    out = _status("0", tmp_path, unreadable="config", make_config=False)
    assert out.out.startswith("valid"), out


def test_the_remediations_cover_the_config_file_too() -> None:
    """A remediation that exposes only `credentials` leaves a role profile broken
    in the same silent way, so both documented fixes have to mention config."""
    text = SCRIPT.read_text()
    copy_block = text[text.index("install -d -m 0500"):]
    assert ".aws/config /etc/redtusk/aws/" in copy_block[:600], "the copy remediation skips config"
    acl_block = text[text.index("setfacl -m"):]
    assert ".aws/config" in acl_block[:600], "the ACL remediation skips config"


def test_the_notes_state_the_boundaries_the_code_defers_to_them_for() -> None:
    """`_aws_creds_env_override` tells the reader that the one-off-shell boundary
    is "stated in the burst notes", and the symlink refusal is only actionable if
    the operator was told the rule up front. A comment that points at
    documentation which does not say it is the same defect one level up, so the
    cross-reference is asserted rather than assumed.
    """
    text = SCRIPT.read_text()
    notes = text[text.index("The dispatcher runs as UID"):]
    assert "one-off interactive shell" in notes[:2000], (
        "the code defers the export boundary to the burst notes; the notes do not state it"
    )
    assert "EXPORTED value precedence" in notes[:2000], (
        "the notes do not say an exported AWS_CREDS_DIR beats the .env file"
    )
    assert "relative and stay inside" in notes[:2000], (
        "the notes do not state the symlink rule the check refuses on"
    )


def test_the_prefix_matches_the_privilege_of_the_caller(tmp_path: Path) -> None:
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
    target = tmp_path / "creds"
    target.write_text("[default]\n")
    harness = "\n".join([
        "set -u",
        f'export PATH={str(bindir)!r}:$PATH',
        m.group(0),
        f"_aws_readable_by_uid 10001 {str(target)!r} || true",
    ])
    subprocess.run(["bash", "-c", harness], capture_output=True, text=True, timeout=60)
    seen = argv_log.read_text() if argv_log.exists() else ""
    # Assert the branch this RUNNER actually takes. A root-run suite (a container,
    # some CI images) legitimately takes the direct branch, and demanding the sudo
    # form there fails on the runner rather than on the code (codex).
    if os.geteuid() == 0:
        assert "setpriv --reuid=10001" in seen and "sudo" not in seen.split("\n")[0], (
            f"a root caller should invoke setpriv directly; saw: {seen!r}"
        )
    else:
        assert "sudo -n setpriv --reuid=10001" in seen, (
            f"a non-root caller did not run setpriv through sudo; saw: {seen!r}"
        )


def test_the_probe_tests_a_relative_name_from_inside_the_directory(tmp_path: Path) -> None:
    """Docker bind-mounts the `.aws` DIRECTORY at /aws, so the container never
    traverses the deploy user's home. Probing the absolute host path required that
    traversal and reported a WORKING configuration as UNUSABLE whenever the home
    denied it -- and led the remediation to widen the home unnecessarily (codex).

    Verified on toolz2 with a real privilege drop, which a non-root test cannot do:

        home denies traversal, .aws readable -> readable   (the mount works)
        .aws itself denies                   -> not readable

    What IS checkable here is the shape that produces those answers: the dropped
    process must be handed a RELATIVE name, having been cd'd in beforehand.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_aws_readable_by_uid\(\) \{.*?^\}", text, re.S | re.M)
    assert m
    creds_dir = tmp_path / "home" / ".aws"
    creds_dir.mkdir(parents=True)
    (creds_dir / "credentials").write_text("[default]\n")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    argv_log = tmp_path / "argv"
    for name in ("sudo", "setpriv", "su"):
        (bindir / name).write_text(
            f'#!/bin/sh\necho "$*" >> {str(argv_log)!r}\nexit 1\n')
        (bindir / name).chmod(0o755)
    harness = "\n".join([
        "set -u",
        f'export PATH={str(bindir)!r}:$PATH',
        m.group(0),
        f"_aws_readable_by_uid 10001 {str(creds_dir / 'credentials')!r} || true",
    ])
    subprocess.run(["bash", "-c", harness], capture_output=True, text=True, timeout=60)
    seen = argv_log.read_text() if argv_log.exists() else ""
    assert seen, "the probe invoked nothing"
    assert str(creds_dir) not in seen, (
        "the probe handed the dropped process an ABSOLUTE path, which forces it to "
        f"traverse the home the bind mount bypasses: {seen!r}"
    )
    assert "credentials" in seen, seen


def test_the_acl_remediation_does_not_widen_the_home_directory() -> None:
    """The overlay bind-mounts `.aws` itself, so the container never traverses the
    home -- and an ACL granting traversal there exposes more of the deploy user's
    account than the burst tier needs. Advice that over-grants is a defect in the
    same way a missing check is: it is the instruction an operator actually runs.
    """
    text = SCRIPT.read_text()
    acl_lines = [ln for ln in text.splitlines() if "setfacl -m" in ln]
    assert acl_lines, "the ACL remediation vanished"
    for ln in acl_lines:
        assert "$(_aws_creds_home) " not in ln, (
            f"the ACL remediation grants access to the HOME directory: {ln.strip()!r}"
        )


def test_the_status_probes_the_configured_directory_not_the_home(tmp_path: Path) -> None:
    """`_aws_creds_dir` resolving correctly is not the same claim as the status
    function USING it -- checked, and a version that read `$home/.aws` directly
    passed every other test in this file.
    """
    elsewhere = tmp_path / "etc-redtusk-aws"
    elsewhere.mkdir()
    (elsewhere / "credentials").write_text("[default]\n")
    out = _status("0", tmp_path, creds_dir=str(elsewhere))
    assert str(elsewhere / "credentials") in out.out, (
        f"the status reported on the home convention, not the configured mount: {out.out!r}"
    )


def test_the_config_probed_is_the_one_in_the_configured_directory(tmp_path: Path) -> None:
    """The credentials path following AWS_CREDS_DIR does not imply the config path
    does -- they are two derivations, and only one of them was covered until a
    mutant reverting the config half survived.
    """
    elsewhere = tmp_path / "etc-redtusk-aws"
    elsewhere.mkdir()
    (elsewhere / "credentials").write_text("[default]\n")
    (elsewhere / "config").write_text("[profile x]\n")
    out = _status("0", tmp_path, unreadable="config", creds_dir=str(elsewhere))
    assert "UNUSABLE" in out.out, out
    assert str(elsewhere / "config") in out.out, (
        f"the status probed a config outside the configured mount: {out.out!r}"
    )


def test_sts_validates_the_configured_credentials(tmp_path: Path) -> None:
    """`aws sts` has to check the copy the overlay will MOUNT.

    Redirecting only the readability probes to the configured directory left this
    validating the home copy, so a stale mounted copy read as valid because the
    home one passed (codex). The stub records which files it was pointed at --
    a stub that merely returns 0 cannot tell the two apart.
    """
    elsewhere = tmp_path / "etc-redtusk-aws"
    elsewhere.mkdir()
    (elsewhere / "credentials").write_text("[default]\n")
    seen = _status("0", tmp_path, creds_dir=str(elsewhere)).sts_files
    assert seen == f"{elsewhere}/credentials|{elsewhere}/config", (
        f"sts validated the wrong credentials: {seen!r}"
    )


def _real_creds_dir(env: dict[str, str], *, env_file: str = "",
                   tmp_path: Path | None = None,
                   deploy_home: str = "/home/deployuser",
                   override_stub: str | None = None) -> str:
    """Run the REAL `_aws_creds_dir` against the REAL compose files.

    When `env_file` is given the compose files are copied into a scratch project
    so a `.env` can be written without touching the repository -- interpolation
    is a .env-file rule, since a value arriving through the environment would
    already have been expanded by the shell that set it.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_aws_creds_dir\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "_aws_creds_dir not found"
    mo = re.search(r"^_aws_creds_env_override\(\) \{.*?^\}", text, re.S | re.M)
    assert mo, "_aws_creds_env_override not found"

    root = REPO_ROOT
    if env_file:
        assert tmp_path is not None
        root = Path(tempfile.mkdtemp(dir=tmp_path, prefix="project-"))
        (root / "deploy" / "docker").mkdir(parents=True)
        for name in ("docker-compose.yml", "docker-compose.aws-burst.yml"):
            shutil.copy2(REPO_ROOT / "deploy" / "docker" / name,
                         root / "deploy" / "docker" / name)
        (root / "deploy" / "docker" / ".env").write_text(env_file)

    harness = "\n".join([
        "set -u",
        f'REPO_ROOT={str(root)!r}',
        'have() { command -v "$1" >/dev/null; }',
        f'_aws_creds_home() {{ echo {deploy_home!r}; }}',
        # The REAL override lookup, not a stub: it decides what compose is asked
        # with, and passing an empty value would defeat the .env file entirely.
        # `override_stub` replaces only the SOURCE of that value, for the case
        # that cannot be reached through this process's own environment.
        # `return 0` because presence is the STATUS: an empty value is an
        # override, and the stub has to be able to say so.
        (f'_aws_creds_env_override() {{ printf "%s" {override_stub!r}; return 0; }}'
         if override_stub is not None else mo.group(0)),
        m.group(0),
        "_aws_creds_dir",
    ])
    # AWS_CREDS_DIR is REMOVED, not blanked: compose treats a set-but-empty
    # environment variable as missing, which defeats the .env file entirely. That
    # subtlety cost a test failure here and is worth knowing -- an operator who
    # exports it empty gets the same result.
    base = {k: v for k, v in os.environ.items() if k != "AWS_CREDS_DIR"}
    r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True,
                       timeout=180, env={**base, **env})
    return r.stdout.strip()


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_the_mount_source_is_resolved_by_compose_itself(tmp_path: Path) -> None:
    """Compose owns environment precedence, `${VAR}` interpolation and relative
    sources resolved against the project directory.

    I reimplemented those three in shell and grew a bug per review round, ending
    with an `eval` that executed command substitution from `.env` as root. This
    asks the tool that owns them instead, so there is one test here rather than
    four -- and none of them is a reimplementation of compose semantics.

    Placeholders are supplied for the OTHER required variables so a
    half-configured node still resolves; they cannot affect this value.
    """
    absolute = _real_creds_dir({"AWS_CREDS_DIR": "/etc/redtusk/aws"})
    assert absolute == "/etc/redtusk/aws", absolute

    interpolated = _real_creds_dir(
        {"HOME": "/home/tester"},
        env_file="AWS_CREDS_DIR=${HOME}/.aws\n", tmp_path=tmp_path,
        deploy_home="/home/tester")
    assert interpolated == "/home/tester/.aws", interpolated

    # A RELATIVE source resolves against the project directory, not the caller's.
    relative = _real_creds_dir({}, env_file="AWS_CREDS_DIR=./aws\n", tmp_path=tmp_path)
    assert relative.endswith("/deploy/docker/aws"), relative

    # Command substitution is DATA to compose. The marker must not appear.
    marker = tmp_path / "EXECUTED"
    out = _real_creds_dir(
        {}, env_file=f"AWS_CREDS_DIR=$(touch {marker}; echo /pwned)\n",
        tmp_path=tmp_path)
    assert not marker.exists(), f"resolving executed a value from the environment: {out!r}"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_home_interpolation_uses_the_deploy_users_home_not_the_callers(
    tmp_path: Path,
) -> None:
    """`AWS_CREDS_DIR=${HOME}/.aws` must resolve to the DEPLOY user's home.

    The documented invocation is `sudo scripts/prepare_node_ubuntu.sh`, where HOME
    is /root, while the deployment itself is run by the deploy user. Interpolating
    the caller's HOME resolved a different directory than the one that gets
    mounted (codex) -- which is the same reason `_aws_creds_home` exists at all.
    """
    for caller_home in ("/root", "/somewhere/else"):
        got = _real_creds_dir(
            {"HOME": caller_home},
            env_file="AWS_CREDS_DIR=${HOME}/.aws\n",
            tmp_path=tmp_path,
            deploy_home="/home/deployuser",
        )
        assert got == "/home/deployuser/.aws", (
            f"caller HOME={caller_home} leaked into the resolution: {got!r}"
        )


# ---------------------------------------------------------------------------
# One rule, every shape it can take: EVERY link traversed while resolving the
# file -- at every path component -- must be relative and stay inside the mount.
#
# Four review rounds each found one instance of it. The table is here so the
# fifth shape is a row rather than another round, and the benign rows are what
# keep the rule from collapsing into "no symlinks", which would break a
# dotfile-managed ~/.aws for no reason.
# ---------------------------------------------------------------------------


def _links(tmp_path: Path, build: Callable[[Path, Path], None]) -> Run:
    """`build(mount, outside)` lays out the directory; the check then runs
    against it with everything else neutral."""
    mount = tmp_path / ".aws"
    outside = tmp_path / "outside"
    mount.mkdir(parents=True, exist_ok=True)
    outside.mkdir(parents=True, exist_ok=True)
    build(mount, outside)
    return _status("0", tmp_path, creds_dir=str(mount), make_creds=False)


def _plain(m: Path, _o: Path) -> None:
    (m / "credentials").write_text("[default]\n")


def _relative_inside(m: Path, _o: Path) -> None:
    (m / "actual").write_text("[default]\n")
    (m / "credentials").symlink_to("actual")


def _multi_hop_relative(m: Path, _o: Path) -> None:
    (m / "actual").write_text("[default]\n")
    (m / "cur").symlink_to("actual")
    (m / "credentials").symlink_to("cur")


def _relative_directory_component(m: Path, _o: Path) -> None:
    (m / "sub").mkdir()
    (m / "sub" / "actual").write_text("[default]\n")
    (m / "cur").symlink_to("sub")
    (m / "credentials").symlink_to("cur/actual")


def _final_absolute(m: Path, _o: Path) -> None:
    (m / "actual").write_text("[default]\n")
    (m / "credentials").symlink_to(m / "actual")


def _later_hop_absolute(m: Path, _o: Path) -> None:
    (m / "actual").write_text("[default]\n")
    (m / "cur").symlink_to(m / "actual")
    (m / "credentials").symlink_to("cur")


def _absolute_directory_component(m: Path, _o: Path) -> None:
    (m / "sub").mkdir()
    (m / "sub" / "actual").write_text("[default]\n")
    (m / "cur").symlink_to(m / "sub")
    (m / "credentials").symlink_to("cur/actual")


def _escaping(m: Path, o: Path) -> None:
    (o / "real").write_text("[default]\n")
    (m / "credentials").symlink_to("../outside/real")


def _escapes_and_returns(m: Path, _o: Path) -> None:
    (m / "actual").write_text("[default]\n")
    (m / "credentials").symlink_to(f"../{m.name}/actual")


def _loop_through_config(m: Path, _o: Path) -> None:
    (m / "credentials").write_text("[default]\n")
    (m / "config").symlink_to("other")
    (m / "other").symlink_to("config")


@pytest.mark.parametrize("build,expected", [
    # Accepted: nothing on the path is a link, or every link is relative and
    # stays inside. These are the rows that fail if the rule over-reaches.
    (_plain, "valid"),
    (_relative_inside, "valid"),
    (_multi_hop_relative, "valid"),
    (_relative_directory_component, "valid"),
    # Refused: each was a separate review finding.
    (_final_absolute, "ABSOLUTE"),
    (_later_hop_absolute, "ABSOLUTE"),
    (_absolute_directory_component, "ABSOLUTE"),
    (_escaping, "leaves"),
    (_escapes_and_returns, "leaves"),
    (_loop_through_config, "loops"),
], ids=["plain-file", "relative-link", "multi-hop-relative",
        "relative-directory-component", "final-component-absolute",
        "later-hop-absolute", "absolute-directory-component",
        "relative-escaping", "escapes-and-returns", "loop"])
def test_every_link_on_the_path_must_be_relative_and_stay_inside(
    tmp_path: Path, build: Callable[[Path, Path], None], expected: str,
) -> None:
    """A bind mount does not rewrite link TEXT and mounts nothing but
    AWS_CREDS_DIR, so a link that is absolute -- or that leaves the directory
    even momentarily -- names a path the container does not have, while every
    host-side check follows it happily and reports valid.

    `escapes-and-returns` and `absolute-directory-component` both resolve INSIDE
    the mount on the host, so `readlink -f` containment cannot see either one.
    """
    out = _links(tmp_path, build)
    if expected == "valid":
        assert out.out.startswith("valid"), out.out
    else:
        assert "UNUSABLE" in out.out, out.out
        assert expected in out.out, out.out


def test_a_symlink_out_of_the_mount_is_reported_without_realpath(
    tmp_path: Path,
) -> None:
    """The backstop check, which is what catches a target outside the mount when
    the walk itself is not what finds it. Kept as its own case because the
    message names the destination, which is the actionable part."""
    outside = tmp_path / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    real = outside / "real-credentials"
    real.write_text("[default]\n")
    out = _status("0", tmp_path, symlink_to="../outside/real-credentials")
    assert "UNUSABLE" in out.out, out.out


# ---------------------------------------------------------------------------
# An unresolved mount makes every conclusion about the guessed path a guess.
# ---------------------------------------------------------------------------


def test_absent_credentials_are_not_diagnosed_when_the_mount_is_unresolved(
    tmp_path: Path,
) -> None:
    """With compose unavailable the checked directory is a FALLBACK GUESS at the
    home copy, so `absent — place ~/.aws/credentials` is a confident diagnosis of
    a directory that is not necessarily the one mounted: a populated
    /etc/redtusk/aws named in .env reads as missing, and the operator is sent to
    create a second copy in the wrong place (codex).
    """
    out = _status("0", tmp_path, make_creds=False)      # creds_dir="" -> unresolved
    assert out.out.startswith("UNKNOWN"), out.out
    assert "could not resolve" in out.out


def test_absent_credentials_are_still_diagnosed_when_the_mount_is_resolved(
    tmp_path: Path,
) -> None:
    """The counterweight, and the one that can fail if the fix over-reaches: when
    compose DID resolve the directory, an absent file is a fact about the right
    directory and must still be reported plainly."""
    resolved = tmp_path / ".aws"
    resolved.mkdir(parents=True, exist_ok=True)
    out = _status("0", tmp_path, make_creds=False, creds_dir=str(resolved))
    assert out.out.startswith("absent"), out.out
    assert "UNKNOWN" not in out.out


def test_failed_sts_is_not_diagnosed_when_the_mount_is_unresolved(
    tmp_path: Path,
) -> None:
    """Same class as the absent case: credentials that fail sts in the GUESSED
    directory say nothing about the credentials the burst tier actually uses."""
    out = _status("0", tmp_path, sts="1")
    assert out.out.startswith("UNKNOWN"), out.out
    assert "may not be the credentials" in out.out


def test_failed_sts_is_still_diagnosed_when_the_mount_is_resolved(
    tmp_path: Path,
) -> None:
    """The counterweight: a resolved directory whose credentials fail sts is
    invalid, and deferring THAT would hide the failure this check exists for."""
    resolved = tmp_path / ".aws"
    out = _status("0", tmp_path, sts="1", creds_dir=str(resolved))
    assert out.out.startswith("invalid"), out.out


# ---------------------------------------------------------------------------
# The override the DEPLOYMENT launches with, not just the one in .env.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_an_exported_creds_dir_beats_the_env_file_in_the_resolution(
    tmp_path: Path,
) -> None:
    """Compose gives an environment variable precedence over `.env`, so a node
    whose operator exports AWS_CREDS_DIR mounts THAT -- and the check has to
    resolve the same way or it validates a directory the stack never uses.

    NOTE this one passes with the forwarding removed entirely, because the
    variable is in this process's environment and `env` inherits it. It is here
    as the precedence statement; the test below is the one that discriminates.
    """
    got = _real_creds_dir({"AWS_CREDS_DIR": "/etc/redtusk/aws"},
                          env_file="AWS_CREDS_DIR=/some/other/place\n",
                          tmp_path=tmp_path)
    assert got == "/etc/redtusk/aws", got


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_a_lookup_only_override_is_carried_into_the_compose_resolution(
    tmp_path: Path,
) -> None:
    """The discriminating case: the override is NOT in this process's environment
    -- it is the deploy user's, which the root-run check has to go and fetch --
    so nothing is inherited and the resolution is correct only if the value is
    explicitly forwarded.
    """
    got = _real_creds_dir({}, env_file="AWS_CREDS_DIR=/some/other/place\n",
                          tmp_path=tmp_path, override_stub="/etc/redtusk/aws")
    assert got == "/etc/redtusk/aws", got


def _override(env: dict[str, str], *, uid: str = "0", exports: str | None = None,
              banner: str = "", deploy_user: str = "deployuser",
              missing: tuple[str, ...] = ()) -> tuple[bool, str]:
    """Run the REAL `_aws_creds_env_override`, returning (present, value).

    Its whole job is to see a value this process cannot see, so the deploy
    user's login shell is what has to be stubbed -- there is no second account
    here to export anything in. `exports` is what the login environment carries
    (None = nothing exported, "" = exported empty) and `banner` is anything the
    profile prints first. The stub EXECUTES the command the lookup hands it, so
    the sentinel protocol under test is the real one.
    """
    text = SCRIPT.read_text()
    m = re.search(r"^_aws_creds_env_override\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "_aws_creds_env_override not found"
    bindir = Path(tempfile.mkdtemp())
    (bindir / "id").write_text(f"#!/bin/sh\necho {uid}\n")
    # The stub RUNS the command it is handed, in a login environment this fixture
    # controls -- it does not print a canned answer. A stub that ignored its
    # arguments made the remote command a string nothing ever executed, so
    # dropping `${AWS_CREDS_DIR+S}` from it (which erases the difference between
    # unset and exported-empty) could not be observed by any test here.
    setenv = (f"AWS_CREDS_DIR={exports!r}\nexport AWS_CREDS_DIR\n"
              if exports is not None else "unset AWS_CREDS_DIR\n")
    (bindir / "sudo").write_text(
        "#!/bin/sh\n"
        f"printf '%s' {banner!r}\n"
        # Step over sudo's own flags to the `sh -c <command>` it was given.
        'while [ $# -gt 0 ]; do case "$1" in sh) shift; break ;; *) shift ;; esac; done\n'
        f"{setenv}"
        'exec sh "$@"\n')
    (bindir / "timeout").write_text('#!/bin/sh\nshift\nexec "$@"\n')
    for n in ("id", "sudo", "timeout"):
        (bindir / n).chmod(0o755)
    path = f"{bindir}:{os.environ['PATH']}"
    # A host that lacks the tool is modelled through the script's OWN capability
    # probe. Truncating PATH instead removed `bash` from it and the fixture died
    # before reaching the code -- which is not the same as the tool being absent.
    absent = " ".join(missing)
    harness = "\n".join([
        "set -u",
        f"export PATH={path!r}",
        f"DEPLOY_USER={deploy_user!r}",
        f'have() {{ for n in {absent}; do [ "$1" = "$n" ] && return 1; done;'
        ' command -v "$1" >/dev/null; }',
        m.group(0),
        'if v="$(_aws_creds_env_override)"; then printf "SET\\t%s" "$v";'
        ' else printf "UNSET\\t"; fi',
    ])
    base = {k: v for k, v in os.environ.items() if k != "AWS_CREDS_DIR"}
    r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True,
                       timeout=60, env={**base, **env, "PATH": path})
    assert r.returncode == 0, r.stderr
    state, _, value = r.stdout.partition("\t")
    return state == "SET", value


def test_the_override_is_read_from_the_deploy_users_login_environment() -> None:
    """Plain `sudo` resets the environment -- measured on toolz2:

        under sudo:    AWS_CREDS_DIR=[<stripped>]
        under sudo -E: AWS_CREDS_DIR=[/etc/redtusk/aws]

    so on the documented `sudo prepare_node_ubuntu.sh` path an override the
    deploy user exports is invisible to the check, which then validated the
    .env path while the stack ran on another (codex).
    """
    assert _override({}, exports="/etc/redtusk/aws") == (True, "/etc/redtusk/aws")


def test_an_exported_empty_override_is_not_flattened_into_no_override() -> None:
    """Set-but-empty is a THIRD state and the overlay is sensitive to it: it
    mounts `${AWS_CREDS_DIR:?...}`, so an empty value makes compose reject the
    stack, while .env alone would have launched it. Reporting "no override"
    here validates the .env directory on a node whose stack cannot start
    (codex). Presence is the return status, so an empty value survives it.
    """
    assert _override({}, exports="") == (True, "")


def test_this_processes_own_environment_wins_over_the_lookup() -> None:
    """`sudo -E`, or a root shell that exported it: an explicit value here is
    what compose would see, so it must not be overridden by the login lookup."""
    assert _override({"AWS_CREDS_DIR": "/from/the/caller"},
                     exports="/from/the/login/shell") == (True, "/from/the/caller")


def test_an_empty_value_in_this_process_is_also_a_value() -> None:
    """The same third state, one level up: `AWS_CREDS_DIR=` in the caller's own
    environment is what compose will see, so it is an override, not an absence."""
    assert _override({"AWS_CREDS_DIR": ""}, exports="/from/the/login") == (True, "")


def test_no_override_anywhere_is_reported_as_absent() -> None:
    """The counterweight: a deploy user who exports nothing must produce NO
    override, so the .env file is what compose is asked with."""
    assert _override({}) == (False, "")


def test_the_lookup_is_skipped_when_it_cannot_be_performed() -> None:
    """A non-root caller cannot become the deploy user, and a host without sudo
    or timeout cannot either. Neither is an override of empty -- both are
    'unknown', and the .env file is then the best available answer."""
    assert _override({}, uid="1000", exports="/etc/redtusk/aws") == (False, "")
    assert _override({}, exports="/etc/redtusk/aws", missing=("sudo",)) == (False, "")
    assert _override({}, exports="/etc/redtusk/aws", missing=("timeout",)) == (False, "")




def test_login_shell_chatter_is_not_read_as_part_of_the_value() -> None:
    """A LOGIN shell is what carries a persistent export -- and what prints motd
    banners and profile output, onto the same stdout. Reading the whole output
    made an `echo` in .profile part of the credentials path, which then resolves
    nowhere; the value is emitted after a sentinel and read from the LAST one.
    """
    got = _override({}, banner="Welcome to toolz2!\n* 3 updates available\n",
                    exports="/etc/redtusk/aws")
    assert got == (True, "/etc/redtusk/aws"), got


def test_a_banner_alone_is_not_mistaken_for_an_override() -> None:
    """The counterweight: chatter without an export is still NO override, or
    every node with an motd would look like it had one."""
    assert _override({}, banner="Welcome to toolz2!\n") == (False, "")


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_an_exported_empty_override_is_forwarded_to_compose(tmp_path: Path) -> None:
    """The forwarding half of the set-but-empty finding, end to end against the
    real compose files: the overlay mounts `${AWS_CREDS_DIR:?...}`, so compose
    REJECTS an empty value and the mount is correctly left unresolved.

    Skipping the forward leaves .env resolving cleanly, and --check then
    validates a directory on a node whose stack cannot start (codex).
    """
    got = _real_creds_dir({}, env_file="AWS_CREDS_DIR=/some/other/place\n",
                          tmp_path=tmp_path, override_stub="")
    assert got == "", f"an empty override did not reach compose: {got!r}"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker is not installed")
def test_no_override_does_not_blank_the_env_file_value(tmp_path: Path) -> None:
    """RESTORED: a rewrite of this section to EOF dropped it, and the mutant it
    was the only guard against ("forward the override unconditionally") went
    from killed to surviving.

    It is the counterweight for the whole override feature. Compose treats a
    SET-BUT-EMPTY variable as an override of the file, so a node that exports
    nothing -- which is most of them -- must still resolve its own .env.
    """
    got = _real_creds_dir({}, env_file="AWS_CREDS_DIR=/etc/redtusk/aws\n",
                          tmp_path=tmp_path)
    assert got == "/etc/redtusk/aws", got
