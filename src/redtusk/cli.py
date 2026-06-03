"""RedTusk command-line interface."""
from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING, Any

import click

from redtusk._version import __version__
from redtusk.observability.logging import configure_logging

if TYPE_CHECKING:
    from redtusk.jobs.base import JobStore
    from redtusk.limits import Limits
    from redtusk.worker_runtime import WorkerRuntime

_DEFAULT_DB_URL = "sqlite:///./redtusk-jobs.db"


def _make_store(limits: Limits) -> JobStore:
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


async def _run_server(
    host: str, port: int, log_level: str, limits: Limits, image: str, role: str = "both"
) -> None:
    """Wire the components for the requested role and run.

    both       — HTTP + warm pool + dispatcher claim-loop (single process; default).
    api        — HTTP + enqueue only. No pool, no worker runtime, NO /dev/kvm; sync
                 goes through the queue. Pairs with a separate `dispatcher` process.
    dispatcher — warm pool + claim-loop, no HTTP. Holds /dev/kvm, internal-only.
    """
    import signal

    import uvicorn

    from redtusk.api import create_app
    from redtusk.dispatcher import Dispatcher
    from redtusk.jobs.retention import RetentionSweeper
    from redtusk.pool import Pool
    from redtusk.runtime.docker_runtime import DockerRuntime
    from redtusk.worker_runtime import DockerWorkerRuntime, FirecrackerWorkerRuntime

    store = _make_store(limits)
    if hasattr(store, "connect"):
        await store.connect()

    async def _run_uvicorn(app: Any, sweeper: RetentionSweeper | None) -> None:
        config = uvicorn.Config(app, host=host, port=port, log_level=log_level, loop="asyncio")
        try:
            await uvicorn.Server(config).serve()
        finally:
            if sweeper is not None:
                await sweeper.stop()
            if hasattr(store, "close"):
                await store.close()

    if role == "api":
        # HTTP + enqueue only — no pool, no worker runtime, no /dev/kvm. The
        # dispatcher container drains the queue. (No retention sweeper here; the
        # dispatcher owns artifact pruning.)
        dispatcher = Dispatcher(
            pool=None, store=store, worker_runtime=None, limits=limits, role="api"
        )
        app = create_app(dispatcher=dispatcher, store=store, limits=limits)
        await _run_uvicorn(app, sweeper=None)
        return

    # both / dispatcher both need the pool + worker runtime.
    # REDTUSK_WORKER_RUNTIME=firecracker picks the FC backend (each slot is a
    # Firecracker subprocess + AF_VSOCK); everything else flows through Docker.
    worker_rt: WorkerRuntime
    if limits.worker_runtime == "firecracker":
        worker_rt = FirecrackerWorkerRuntime(limits=limits)
    else:
        docker_rt = await DockerRuntime.detect()
        worker_rt = DockerWorkerRuntime(docker=docker_rt, limits=limits, image=image)
    pool = Pool(limits=limits, worker_runtime=worker_rt, store=store, profile=limits.profile)
    dispatcher = Dispatcher(
        pool=pool, store=store, worker_runtime=worker_rt, limits=limits, role=role
    )
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=limits.job_retention_seconds,
        artifact_root=limits.artifact_root,
    )
    await sweeper.start()

    if role == "dispatcher":
        # Pool + claim-loop, no HTTP. Run until SIGINT/SIGTERM.
        await dispatcher.start()
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except (NotImplementedError, RuntimeError):
                pass
        try:
            await stop.wait()
        finally:
            await dispatcher.stop()
            await sweeper.stop()
            if hasattr(store, "close"):
                await store.close()
        return

    # both (default): create_app's lifespan starts/stops the dispatcher.
    app = create_app(dispatcher=dispatcher, store=store, limits=limits)
    await _run_uvicorn(app, sweeper=sweeper)


@click.group()
def cli() -> None:
    """RedTusk — sandboxed Apache Tika service."""


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option(
    "--log-level",
    default="info",
    show_default=True,
    type=click.Choice(["debug", "info", "warning", "error"]),
)
@click.option(
    "--role",
    type=click.Choice(["both", "api", "dispatcher"]),
    default="both",
    envvar="REDTUSK_ROLE",
    show_default=True,
    help="both=HTTP+pool+dispatcher (default). api=HTTP+enqueue only, no /dev/kvm. "
    "dispatcher=pool+claim-loop, no HTTP. Split mode removes KVM/spawn from the "
    "internet-facing api.",
)
def serve(host: str, port: int, log_level: str, role: str) -> None:
    """Start the RedTusk API server with embedded dispatcher."""
    configure_logging()
    from redtusk.limits import Limits
    limits = Limits.from_env()
    image = os.environ.get("REDTUSK_WORKER_IMAGE", "redtusk:latest")
    asyncio.run(_run_server(host, port, log_level, limits, image, role=role))


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
        click.echo(
            f"Limits OK: pool_warm_size={limits.pool_warm_size}, "
            f"pool_concurrent_size={limits.pool_concurrent_size}, "
            f"profile={limits.profile!r}"
        )
        click.echo("Self-test passed.")
    except Exception as e:
        click.echo(f"Self-test FAILED: {e}", err=True)
        sys.exit(1)
