# Plan 7 — Compose Stack, Ops, and Parity Suite

**Date:** 2026-05-06
**Status:** In progress
**Depends on:** Plans 1–6 (all merged)

## Goal

Make RedTusk operationally deployable. After this plan:
- `./deploy/docker/redtusk-compose up --build -d` starts the full stack (postgres + api/dispatcher).
- `redtusk serve` auto-selects SqlJobStore when `REDTUSK_DATABASE_URL` is set (postgres or sqlite).
- KSM can be enabled on EC2 with a one-liner systemd unit.
- A tika-server parity test skeleton is in place (skipped unless real infrastructure is available).
- `README.md` documents the full project.

## File targets

```
deploy/docker/
  docker-compose.yml        # postgres + redtusk api+dispatcher
  redtusk-compose           # GID-detect wrapper (chmod +x)
  .env.example              # sample env overrides
deploy/ksm/
  enable-ksm.sh             # sysctl KSM knobs
  redtusk-ksm.service       # systemd unit
  README.md                 # KSM side-channel note + deployment guide
src/redtusk/
  cli.py                    # update serve: auto-select SqlJobStore
tests/integration/
  __init__.py
  test_tika_compat_pipeline.py  # parity skeleton (gated by `integration` marker)
README.md                   # comprehensive project readme
```

## Tasks

### Task 1 — `cli.py`: auto-select SqlJobStore

Update the `serve` command in `src/redtusk/cli.py` to pick the job store based on
`REDTUSK_DATABASE_URL` (exposed via `Limits.database_url`):

```python
def _make_store(limits: Limits):
    """Return the appropriate JobStore for the configured database_url."""
    from redtusk.jobs.memory import MemoryJobStore
    from redtusk.jobs.sql_store import SqlJobStore
    from redtusk.jobs.retention import RetentionSweeper

    url = limits.database_url
    if url == "sqlite:///./redtusk-jobs.db":
        # Default (no explicit config) — use in-memory for single-process dev.
        return MemoryJobStore()
    # sqlite:// or postgresql:// → sql backend
    store = SqlJobStore(database_url=url)
    return store
```

Also start `RetentionSweeper` alongside the store in `serve`:

```python
async def _run_app(host, port, log_level, limits, image):
    """Async entrypoint: wire everything, start server."""
    import uvicorn
    from redtusk.jobs.retention import RetentionSweeper
    from redtusk.pool import Pool
    from redtusk.worker_runtime import DockerWorkerRuntime
    from redtusk.runtime.docker_runtime import DockerRuntime
    from redtusk.dispatcher import Dispatcher
    from redtusk.api import create_app

    store = _make_store(limits)
    if hasattr(store, 'connect'):
        await store.connect()

    docker_rt = await DockerRuntime.detect()
    worker_rt = DockerWorkerRuntime(docker=docker_rt, limits=limits, image=image)
    pool = Pool(limits=limits, worker_runtime=worker_rt, store=store, profile=limits.profile)
    dispatcher = Dispatcher(pool=pool, store=store, worker_runtime=worker_rt, limits=limits)
    app = create_app(dispatcher=dispatcher, store=store, limits=limits)

    sweeper = RetentionSweeper(store=store, retention_seconds=limits.job_retention_seconds)
    sweeper_task = asyncio.create_task(sweeper.run())

    config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        sweeper_task.cancel()
        if hasattr(store, 'close'):
            await store.close()
```

Then in the `serve` click command:
```python
def serve(host, port, log_level):
    configure_logging()
    limits = Limits.from_env()
    image = os.environ.get("REDTUSK_WORKER_IMAGE", "redtusk:latest")
    asyncio.run(_run_app(host, port, log_level, limits, image))
```

This keeps the `serve` command clean and makes the sql store auto-selected via env var.

### Task 2 — `deploy/docker/docker-compose.yml`

```yaml
# RedTusk compose stack
# Usage: ./deploy/docker/redtusk-compose up --build -d
# Web UI + API at http://localhost:8000/

services:

  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB:       ${POSTGRES_DB:-redtusk}
      POSTGRES_USER:     ${POSTGRES_USER:-redtusk}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-redtusk-dev}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks:
      - backend

  api:
    image: ${REDTUSK_API_IMAGE:-redtusk-api:dev}
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile.api
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - REDTUSK_DATABASE_URL=postgresql://${POSTGRES_USER:-redtusk}:${POSTGRES_PASSWORD:-redtusk-dev}@postgres:5432/${POSTGRES_DB:-redtusk}
      - REDTUSK_WORKER_IMAGE=${REDTUSK_WORKER_IMAGE:-redtusk:latest}
      - REDTUSK_PROFILE=${REDTUSK_PROFILE:-default}
      - REDTUSK_POOL_SIZE=${REDTUSK_POOL_SIZE:-4}
      - REDTUSK_ARTIFACT_ROOT=/var/lib/redtusk/artifacts
      - REDTUSK_SCRATCH_ROOT=/var/lib/redtusk/scratch
    ports:
      - "${REDTUSK_PORT:-8000}:8000"
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    group_add:
      - "${DOCKER_GID:-984}"         # docker socket GID — set by redtusk-compose wrapper
    tmpfs:
      - /tmp:rw,nosuid,size=256m
    volumes:
      - redtusk-data:/var/lib/redtusk
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: ["serve", "--host", "0.0.0.0", "--port", "8000"]
    healthcheck:
      test: ["CMD", "redtusk", "selftest"]
      interval: 30s
      timeout: 15s
      start_period: 30s
      retries: 3
    networks:
      - backend
      - frontend

volumes:
  postgres-data:
  redtusk-data:

networks:
  backend:
  frontend:
```

**Note:** RedTusk runs api + dispatcher in a single process (`redtusk serve`), unlike
ClippyShot's two-container split. The dispatcher spawns worker containers via the Docker
socket bind-mounted read-only into the api container. This requires the api container's
user (or group) to have read access to the socket — handled by `group_add: [DOCKER_GID]`.

**`deploy/docker/Dockerfile.api`** — a thin Python image for the API/dispatcher process:

```dockerfile
FROM python:3.12-slim-bookworm

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 10001 redtusk && \
    useradd --uid 10001 --gid 10001 --no-create-home --shell /sbin/nologin redtusk

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

USER 10001:10001
ENTRYPOINT ["redtusk"]
```

### Task 3 — `deploy/docker/redtusk-compose` wrapper

Mirrors `clippyshot-compose` exactly, adapted for RedTusk:

```bash
#!/usr/bin/env bash
# Wrapper for `docker compose` that auto-detects the host's docker-socket
# GID and writes it to deploy/docker/.env so the api container's
# group_add matches the host socket's group.
#
# Usage — same as `docker compose`:
#   ./deploy/docker/redtusk-compose up --build -d
#   ./deploy/docker/redtusk-compose logs -f api
#   ./deploy/docker/redtusk-compose down
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DOCKER_SOCK="${DOCKER_SOCK:-/var/run/docker.sock}"
if [ -S "$DOCKER_SOCK" ]; then
    SOCKET_GID="$(stat -c '%g' "$DOCKER_SOCK")"
elif [ -n "${DOCKER_GID:-}" ]; then
    echo "note: $DOCKER_SOCK not found; using DOCKER_GID=$DOCKER_GID from env" >&2
    SOCKET_GID="$DOCKER_GID"
else
    echo "error: $DOCKER_SOCK not found and DOCKER_GID env is unset" >&2
    echo "       point DOCKER_SOCK at the real socket or export DOCKER_GID" >&2
    exit 1
fi

touch .env
grep -v '^DOCKER_GID=' .env > .env.tmp || true
mv .env.tmp .env
echo "DOCKER_GID=$SOCKET_GID" >> .env

exec docker compose "$@"
```

`chmod +x deploy/docker/redtusk-compose`

### Task 4 — `deploy/docker/.env.example`

```ini
# RedTusk Compose configuration — copy to .env and edit.

# Postgres credentials
POSTGRES_DB=redtusk
POSTGRES_USER=redtusk
POSTGRES_PASSWORD=change-me-in-production

# Worker image (build with: docker build -f deploy/docker/Dockerfile.default -t redtusk:latest .)
REDTUSK_WORKER_IMAGE=redtusk:latest

# Deployment profile: default | high-density
REDTUSK_PROFILE=default

# Pool size (idle worker slots)
REDTUSK_POOL_SIZE=4

# External port
REDTUSK_PORT=8000
```

### Task 5 — KSM deployment files (`deploy/ksm/`)

**`deploy/ksm/enable-ksm.sh`:**
```bash
#!/usr/bin/env bash
# Enable KSM (Kernel Same-page Merging) for RedTusk worker memory dedup.
# Run once at host boot or via the systemd unit.
# Requires Linux with CONFIG_KSM=y (standard on all major distros).
set -euo pipefail
echo 1    > /sys/kernel/mm/ksm/run
echo 1000 > /sys/kernel/mm/ksm/pages_to_scan
echo 200  > /sys/kernel/mm/ksm/sleep_millisecs
echo "KSM enabled: run=$(cat /sys/kernel/mm/ksm/run), pages_to_scan=$(cat /sys/kernel/mm/ksm/pages_to_scan)"
```

**`deploy/ksm/redtusk-ksm.service`:**
```ini
[Unit]
Description=Enable KSM for RedTusk worker memory dedup
After=network.target
ConditionPathExists=/sys/kernel/mm/ksm/run

[Service]
Type=oneshot
ExecStart=/usr/local/bin/redtusk-enable-ksm.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

**`deploy/ksm/README.md`:**
```markdown
# KSM (Kernel Same-page Merging) for RedTusk

KSM lets the Linux kernel deduplicate identical memory pages across processes.
RedTusk worker containers share the JVM's AppCDS archive pages via the host
page cache, and KSM can further merge JVM heap pages that contain identical
object graphs (common for Tika's internal registries).

## Deployment

### EC2 / self-managed Linux

```sh
sudo install -m 755 deploy/ksm/enable-ksm.sh /usr/local/bin/redtusk-enable-ksm.sh
sudo install -m 644 deploy/ksm/redtusk-ksm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now redtusk-ksm
```

### EKS on EC2

Use a DaemonSet to run `enable-ksm.sh` on each node:
```yaml
# deploy/ksm/ksm-daemonset.yaml (not included — generate from enable-ksm.sh)
```

### Fargate / cloud-managed

KSM is not available on Fargate (Firecracker microVM). The worker logs a warning
at startup if it set `MADV_MERGEABLE` but `/sys/kernel/mm/ksm/run` reads `0`.
Set `REDTUSK_DISABLE_KSM=1` to suppress the `madvise` call entirely on Fargate.

## Expected savings

A pool of 10 default-profile slots without KSM: ~1.5 GB RSS.
With KSM enabled and warm: ~900 MB RSS (40% reduction; varies by workload).

## Side-channel disclosure

KSM enables FLUSH+RELOAD timing observation across merged pages. The RedTusk
threat model (--network=none, one job per container, container destroyed after
job) makes exploitation mostly theoretical. Operators who process highly sensitive
documents and have adversarial access to timing channels should set
`REDTUSK_DISABLE_KSM=1`.
```

### Task 6 — Integration test skeleton (`tests/integration/`)

```python
"""Tika-server parity integration tests.

Requires:
  - REDTUSK_TEST_URL pointing at a running RedTusk instance
  - TIKA_TEST_URL pointing at a running tika-server instance
  - pytest marker: integration

Run:
  pytest tests/integration -m integration --tb=short
"""
from __future__ import annotations

import os
import pytest
import httpx

REDTUSK_URL = os.environ.get("REDTUSK_TEST_URL", "")
TIKA_URL = os.environ.get("TIKA_TEST_URL", "")

pytestmark = pytest.mark.integration


def _skip_if_not_configured():
    if not REDTUSK_URL or not TIKA_URL:
        pytest.skip("REDTUSK_TEST_URL and TIKA_TEST_URL must be set")


@pytest.fixture(scope="module")
def redtusk():
    _skip_if_not_configured()
    return httpx.Client(base_url=REDTUSK_URL, timeout=60)


@pytest.fixture(scope="module")
def tika():
    _skip_if_not_configured()
    return httpx.Client(base_url=TIKA_URL, timeout=60)


# ── /detect/stream ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename,expected_ct", [
    ("sample.txt",  "text/plain"),
    ("sample.pdf",  "application/pdf"),
    ("sample.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
])
def test_detect_parity(redtusk, tika, filename):
    _skip_if_not_configured()
    fixture = (pytest.importorskip("pathlib").Path(__file__).parent.parent
               / "fixtures" / "safe" / filename)
    if not fixture.exists():
        pytest.skip(f"Fixture {filename} not in tests/fixtures/safe/")
    body = fixture.read_bytes()
    r_result = redtusk.put("/detect/stream", content=body).text.strip()
    t_result = tika.put("/detect/stream", content=body).text.strip()
    assert r_result == t_result, f"{filename}: RedTusk={r_result!r} Tika={t_result!r}"


# ── /meta ────────────────────────────────────────────────────────────────────

def test_meta_has_content_type(redtusk):
    _skip_if_not_configured()
    body = b"Hello, RedTusk!\n"
    result = redtusk.put("/meta", content=body).json()
    assert "Content-Type" in result


def test_meta_parity_txt(redtusk, tika):
    _skip_if_not_configured()
    body = b"Parity check\n"
    r = set(redtusk.put("/meta", content=body).json().keys())
    t = set(tika.put("/meta", content=body).json().keys())
    # RedTusk is a subset (may omit Tika-internal keys like X-TIKA:Parsed-By)
    missing = t - r - {"X-TIKA:Parsed-By", "X-TIKA:Parsed-By-Full-Set"}
    assert not missing, f"Keys in Tika but not RedTusk: {missing}"


# ── /rmeta ───────────────────────────────────────────────────────────────────

def test_rmeta_is_list(redtusk):
    _skip_if_not_configured()
    result = redtusk.put("/rmeta", content=b"test").json()
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "Content-Type" in result[0]


# ── /tika ────────────────────────────────────────────────────────────────────

def test_tika_text_extraction(redtusk):
    _skip_if_not_configured()
    body = b"Hello world from integration test\n"
    text = redtusk.put("/tika", content=body).text
    assert "Hello world" in text


def test_tika_parity_txt(redtusk, tika):
    _skip_if_not_configured()
    body = b"Parity: the quick brown fox\n"
    r_text = redtusk.put("/tika", content=body).text.strip()
    t_text = tika.put("/tika", content=body).text.strip()
    assert r_text == t_text, f"Text mismatch:\n  RedTusk: {r_text!r}\n  Tika:    {t_text!r}"
```

Also create `tests/integration/__init__.py` (empty).

Add the `integration` marker to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "integration: requires running RedTusk + Tika instances",
    "docker: requires Docker daemon and built images",
]
```

### Task 7 — `README.md`

Write a comprehensive README covering:
- What RedTusk is (one paragraph)
- Architecture diagram (ASCII)
- Quick start (compose up, then PUT /tika)
- Two deployment profiles table (default vs high-density)
- Configuration reference (key REDTUSK_* vars)
- KSM / AppCDS / CRaC memory dedup section
- Security / threat model note
- Building the worker image
- Running tests

Keep it under 250 lines. No fluff.

## Acceptance criteria

- `pytest tests/unit tests/http tests/docker -q` → 231 passed, 9 skipped (unchanged).
- `pytest tests/integration -m integration -q` → all skipped (no live infra).
- `ruff check src tests` clean.
- `mypy src` clean.
- `./deploy/docker/redtusk-compose` is executable and prints usage when run without docker.
- `redtusk serve --help` shows updated help.

## What this plan does NOT include

- ARM64 seccomp validation.
- Multi-tenant auth (v2).
- CRaC under runsc.
- Per-tenant JobStore isolation.
