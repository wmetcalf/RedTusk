"""The AWS burst overlay must be deployable by following the documented steps.

`docker-compose.aws-burst.yml` mounts the deploy user's credentials through a
REQUIRED interpolation::

    ${AWS_CREDS_DIR:?set AWS_CREDS_DIR to the deploy user's .aws dir, ...}

The absence of a default is deliberate and correct -- a default naming one
developer's home silently mounts the wrong directory, and the STS probe then
fails closed and reads as bad credentials rather than a wrong path. But nothing
in the documented flow ever told the operator to set it: `AWS_CREDS_DIR`
appeared exactly once in the whole repository, in the interpolation itself, so
every first-time deployment aborted at `docker compose up` even with credentials
correctly installed (codex, #50).

These tests run `docker compose config` rather than grepping the YAML. The
failure being fixed is not "the file lacks a line", it is "the documented
sequence does not produce a working stack", and only Compose's own interpolation
can answer that.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKER_DIR = REPO_ROOT / "deploy" / "docker"
ENV_EXAMPLE = DOCKER_DIR / ".env.example"

# The other two `:?` variables in the merged stack. Pinned here so the tests vary
# exactly one thing -- without them Compose reports POSTGRES_PASSWORD first and
# the AWS assertion would pass or fail for an unrelated reason.
BASE_ENV = "POSTGRES_PASSWORD=x\nBLASTBOX_AWS_REGION=us-east-1\n"

_compose_missing = shutil.which("docker") is None
requires_compose = pytest.mark.skipif(
    _compose_missing, reason="docker is not installed on this host"
)


def _config(tmp_path: Path, env_text: str) -> subprocess.CompletedProcess[str]:
    env_file = tmp_path / "test.env"
    env_file.write_text(env_text)
    return subprocess.run(
        [
            "docker", "compose", "--env-file", str(env_file),
            "-f", "docker-compose.yml",
            "-f", "docker-compose.aws-burst.yml",
            "config",
        ],
        cwd=DOCKER_DIR, capture_output=True, text=True, timeout=120,
    )


@requires_compose
def test_the_overlay_refuses_to_start_without_a_credentials_path(tmp_path: Path) -> None:
    """The required interpolation is the point -- it must keep failing loudly.

    Paired with the test below so this is not merely "it errors": a fix that
    handed the variable a default would pass that one and fail this, which is
    the trade the overlay's own comment argues against.
    """
    res = _config(tmp_path, BASE_ENV)
    assert res.returncode != 0
    assert "AWS_CREDS_DIR" in res.stderr, res.stderr


@requires_compose
def test_the_documented_variable_produces_a_read_only_creds_mount(tmp_path: Path) -> None:
    res = _config(tmp_path, BASE_ENV + "AWS_CREDS_DIR=/home/ubuntu/.aws\n")
    assert res.returncode == 0, f"the documented deploy still aborts: {res.stderr}"

    # PARSED, not grepped. `read_only: true` occurs on several unrelated mounts in
    # the merged stack, so a substring test cannot tell whether THIS one is
    # read-only -- checked, and it could not: dropping `:ro` from the creds mount
    # left the substring assertion green.
    import yaml

    cfg = yaml.safe_load(res.stdout)
    svc = cfg["services"]["dispatcher-aws-burst"]
    creds = [v for v in svc["volumes"] if v.get("target") == "/aws"]
    assert len(creds) == 1, f"expected exactly one /aws mount, got {creds}"
    assert creds[0]["source"] == "/home/ubuntu/.aws", creds[0]
    assert creds[0].get("read_only") is True, (
        f"credentials are mounted writable into the burst dispatcher: {creds[0]}"
    )


def test_the_env_example_documents_the_required_variable() -> None:
    """`.env.example` is where an operator looks for what a stack needs, and it
    had no AWS section at all. Commented out on purpose -- the value is
    host-specific, so shipping a live default would reintroduce the wrong-path
    failure the overlay deliberately avoids."""
    text = ENV_EXAMPLE.read_text()
    assert "AWS_CREDS_DIR" in text
    assert "#AWS_CREDS_DIR=" in text, "the example must not set a live default"
