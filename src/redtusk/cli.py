"""RedTusk command-line interface."""
from __future__ import annotations

import asyncio
import os
import sys

import click

from redtusk._version import __version__
from redtusk.observability.logging import configure_logging

_DEFAULT_DB_URL = "sqlite:///./redtusk-jobs.db"


def _make_store(limits):
    """Select job store based on database_url."""
    from redtusk.jobs.memory import MemoryJobStore
    from redtusk.jobs.sql_store import SqlJobStore

    url = limits.database_url
    # Use MemoryJobStore for the default sqlite sentinel — no persistence needed
    # for a plain `redtusk serve`.  Any explicit sqlite:// or postgresql:// URL
    # gets the SQL backend.
    if url == _DEFAULT_DB_URL:
        return MemoryJobStore()
    return SqlJobStore(url=url)


async def _run_server(host: str, port: int, log_level: str, limits, image: str) -> None:
    """Wire all components and run uvicorn."""
    import uvicorn

    from redtusk.api import create_app
    from redtusk.dispatcher import Dispatcher
    from redtusk.jobs.retention import RetentionSweeper
    from redtusk.pool import Pool
    from redtusk.runtime.docker_runtime import DockerRuntime
    from redtusk.worker_runtime import DockerWorkerRuntime

    store = _make_store(limits)
    if hasattr(store, "connect"):
        await store.connect()

    docker_rt = await DockerRuntime.detect()
    worker_rt = DockerWorkerRuntime(docker=docker_rt, limits=limits, image=image)
    pool = Pool(limits=limits, worker_runtime=worker_rt, store=store, profile=limits.profile)
    dispatcher = Dispatcher(pool=pool, store=store, worker_runtime=worker_rt, limits=limits)
    app = create_app(dispatcher=dispatcher, store=store, limits=limits)

    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=limits.job_retention_seconds,
        artifact_root=limits.artifact_root,
    )
    await sweeper.start()

    config = uvicorn.Config(app, host=host, port=port, log_level=log_level, loop="asyncio")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        await sweeper.stop()
        if hasattr(store, "close"):
            await store.close()


@click.group()
def cli() -> None:
    """RedTusk — sandboxed Apache Tika service."""


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option(
    "--log-level",
    default="info",
    show_default=True,
    type=click.Choice(["debug", "info", "warning", "error"]),
)
def serve(host: str, port: int, log_level: str) -> None:
    """Start the RedTusk API server with embedded dispatcher."""
    configure_logging()
    from redtusk.limits import Limits
    limits = Limits.from_env()
    image = os.environ.get("REDTUSK_WORKER_IMAGE", "redtusk:latest")
    asyncio.run(_run_server(host, port, log_level, limits, image))


@cli.command()
def version() -> None:
    """Print version and exit."""
    click.echo(f"RedTusk {__version__}")


@cli.command()
def selftest() -> None:
    """Run a quick self-test (imports and limits validation)."""
    from redtusk.limits import Limits
    configure_logging()
    try:
        limits = Limits.from_env()
        click.echo(f"Limits OK: pool_size={limits.pool_size}, profile={limits.profile!r}")
        click.echo("Self-test passed.")
    except Exception as e:
        click.echo(f"Self-test FAILED: {e}", err=True)
        sys.exit(1)
