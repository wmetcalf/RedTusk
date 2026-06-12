"""RedTusk command-line interface (lean: selftest + version).

RedTusk runs ON blastbox.host — the operator runs ``blastbox serve`` /
``blastbox dispatch`` directly, not a redtusk ``serve`` subcommand (which would
force the lean redtusk core to depend on ``blastbox[host]``). This CLI keeps only
in-process, dependency-light commands; the engine adapter
(``redtusk.engine:RedTuskEngine``) is what the host's cold/warm workers load.
"""
from __future__ import annotations

import sys

import click

from redtusk._version import __version__
from redtusk.observability.logging import configure_logging


@click.group()
def cli() -> None:
    """RedTusk — sandboxed Apache Tika engine for blastbox.host."""


@cli.command()
def version() -> None:
    """Print version and exit."""
    click.echo(f"RedTusk {__version__}")


@cli.command()
def selftest() -> None:
    """Quick self-test: engine adapter import + blastbox limits resolve."""
    configure_logging()
    try:
        from blastbox.limits import Limits

        from redtusk.engine import RedTuskEngine

        limits = Limits.from_env()
        engine = RedTuskEngine()
        click.echo(
            f"Engine OK: name={engine.name!r} formats={sorted(engine.formats)} "
            f"timeout_s={limits.timeout_s}"
        )
        click.echo("Self-test passed.")
    except Exception as e:
        click.echo(f"Self-test FAILED: {e}", err=True)
        sys.exit(1)
