# Plan 4 — Pool, Dispatcher, and Worker Runtime

**Date:** 2026-05-05
**Status:** In progress
**Depends on:** Plans 1–3 (foundation, Java worker, default Docker image — all merged at 838e41b)

## Goal

Implement the Python-side hot path: the warm pool of slots, the dispatcher that drives jobs through
those slots, the Docker runtime shim that actually spawns/kills containers, and the sandbox flag
builder that sets the hardening options. After this plan the dispatcher can fully process a job
end-to-end (input → worker container → validated metadata → success/fail). API and UI come in Plan 5.

## File targets

```
src/redtusk/
  pool.py                   # SlotState + Slot + Pool state machine
  dispatcher.py             # Async claim loop, drives pool
  worker_runtime.py         # Protocol + DockerWorkerRuntime (spawn/signal/reap)
  sandbox/
    __init__.py
    container.py            # Hardening flag builder
  runtime/
    __init__.py
    docker_runtime.py       # runsc/runc detect, docker run argv, docker rm/kill/wait
tests/unit/
  test_pool.py
  test_dispatcher.py
  test_worker_runtime.py
```

No new files beyond the above. `limits.py` and `metrics.py` already exist — add fields to them as
needed (Limits.pool_size etc; new metrics functions). Do not touch Plan 1–3 files unless necessary
to add a missing field.

## Tasks

### Task 1 — Slot state machine (`pool.py`)

**Slot** is a frozen-ish dataclass (use `dataclasses.dataclass` with `eq=True`). Fields:

```python
@dataclass
class Slot:
    id: UUID
    state: SlotState
    container_id: str | None      # set after spawn succeeds
    scratch_dir: Path | None      # set when WorkerRuntime.create_scratch() called
    assigned_job_id: str | None
    assigned_at: datetime | None  # UTC, set on ASSIGNED transition
    spawn_attempts: int           # incremented each SPAWN_FAILED retry
    is_burst: bool                # True if spawned above pool_size baseline
```

`SlotState(StrEnum)`: WARMING, IDLE, ASSIGNED, DRAINING, SPAWN_FAILED.

**Pool** class — does NOT call Docker itself; it holds a reference to a `WorkerRuntime` interface
and calls through it. This makes unit testing trivial with `AsyncMock`.

```python
class Pool:
    def __init__(
        self,
        limits: Limits,
        worker_runtime: WorkerRuntime,
        store: JobStore,            # read queue depth for burst trigger
        profile: str,               # "default" | "high-density"
    ) -> None: ...

    async def start(self) -> None:  # begin spawn loop
    async def stop(self) -> None:   # drain and cancel tasks

    async def claim(self, timeout: float) -> Slot:
        # Waits up to `timeout` seconds for an IDLE slot.
        # Raises PoolExhaustedError if timeout elapses with no slot.

    async def release(self, slot: Slot, *, success: bool) -> None:
        # ASSIGNED → DRAINING. Initiates replacement spawn immediately (fire-and-forget task).
        # If success=False, records the failure; pool still replaces the slot.

    def idle_count(self) -> int:
    def assigned_count(self) -> int:
    def warming_count(self) -> int:
    def is_healthy(self) -> bool:
        # True if pool has >=1 IDLE slot, or a slot has been successfully IDLE
        # in the last 30s, or pool is still warming up (total age < WORKER_WARMUP_TIMEOUT_S).
```

**Internal spawn loop** (`_spawn_loop` background task):
- Maintains `target_size` slots (starts at `limits.pool_size`).
- Uses `asyncio.Semaphore(limits.pool_spawn_rate_limit)` to cap spawn rate.
- On SPAWN_FAILED: exponential backoff (250ms, 500ms, 1s, 2s, 5s). After `limits.pool_spawn_retry_max`
  consecutive failures, decrements `target_size` by 1, logs CRITICAL, never goes below 1.

**Burst logic** (simple, correct):
- Every 1s, check the JobStore queued count (call `store.count_by_state(JobState.QUEUED)` — add this
  method to the Protocol and all implementations).
- If queued > 0 for > `limits.pool_burst_trigger_s` consecutive seconds: spawn burst slots up to
  `limits.pool_max_size`.
- Mark them `is_burst=True`.
- After `limits.pool_burst_drain_s` of no burst slots being claimed, reap the idle burst slots (let
  them expire on next DRAINING without replacement).
- A burst slot that gets claimed just works normally; only unclaimed idle ones are reaped.

**Metrics** — after each state transition call the module-level functions in `observability/metrics.py`:
- `record_pool_idle(n)`, `record_pool_assigned(n)`, `record_pool_warming(n)`, `record_pool_target(n)`.
- `record_spawn_outcome(outcome: str)` — "success" | "failed" | "timeout".
- `record_spawn_duration(seconds: float)`.

These functions already exist in `metrics.py` if they were added in Plan 1; if not, add them now.

### Task 2 — Docker runtime (`runtime/docker_runtime.py`)

```python
@dataclass
class DockerRuntime:
    runtime: str          # "runsc" or "runc"

    @classmethod
    async def detect(cls) -> "DockerRuntime":
        # Run: docker info --format '{{json .Runtimes}}'
        # If "runsc" key present → runtime="runsc"
        # Fall back to "runc".
        # If docker not available: raise DispatchError("docker not found")

    async def run(self, argv: list[str]) -> str:
        # Runs argv (complete docker run command), returns container ID (strip whitespace).
        # argv[0] must be "docker"; raises DispatchError on non-zero exit.
        # Uses asyncio.create_subprocess_exec, captures stdout/stderr.

    async def kill(self, container_id: str, signal: str = "SIGKILL") -> None:
        # docker kill --signal=SIGNAL container_id; ignore non-zero (already dead is ok).

    async def rm(self, container_id: str) -> None:
        # docker rm -f container_id; ignore "no such container".

    async def wait(self, container_id: str) -> int:
        # docker wait container_id → exit code as int.
```

All subprocess calls use `asyncio.create_subprocess_exec` (not shell=True). Stderr captured and
logged at DEBUG.

### Task 3 — Sandbox flag builder (`sandbox/container.py`)

```python
def build_run_argv(
    *,
    runtime: str,           # "runsc" | "runc"
    profile: str,           # "default" | "high-density"
    image: str,             # worker image name
    limits: Limits,
    scratch_dir: Path,      # host path to scratch dir
    container_name: str,    # unique name for the container (slot UUID)
) -> list[str]:
    """Build complete 'docker run ...' argv for a single worker slot."""
```

Flags emitted (in this order so it's auditable):

```
docker run
  --name {container_name}
  --rm
  --read-only
  --security-opt no-new-privileges
  --cap-drop ALL
  [--cap-add CHECKPOINT_RESTORE]  # high-density only
  --network none
  --memory {limits.worker_memory_mb}m
  --pids-limit {limits.worker_pids_limit}
  --cpus {limits.worker_cpus}
  --tmpfs /tmp:rw,exec,nosuid,size=512m
  --tmpfs /var/lib/redtusk:rw,nosuid,size=64m,uid=10001,gid=10001
  --mount type=bind,source={scratch_dir}/in,target=/in,readonly
  --mount type=bind,source={scratch_dir}/out,target=/out
  [--runtime runsc]   # only if runtime == "runsc"
  --user 10001:10001
  {image}
```

Limits fields needed (add to `Limits` if missing):
- `worker_memory_mb: int = 1024` (env: `REDTUSK_WORKER_MEMORY_MB`)
- `worker_pids_limit: int = 256` (env: `REDTUSK_WORKER_PIDS_LIMIT`)
- `worker_cpus: float = 1.0` (env: `REDTUSK_WORKER_CPUS`)

### Task 4 — Worker runtime protocol + implementation (`worker_runtime.py`)

**Protocol** (runtime_checkable, for mocking):

```python
@runtime_checkable
class WorkerRuntime(Protocol):
    async def create_scratch(self, slot_id: UUID) -> Path:
        """Create scratch_dir/{slot_id}/in and /out. Return scratch_dir/{slot_id}."""
    async def spawn(self, slot: Slot, limits: Limits, profile: str) -> str:
        """docker run → container_id."""
    async def poll_fifo(self, slot: Slot, timeout: float) -> bool:
        """Poll for control.fifo under scratch_dir/in until timeout. Return True if found."""
    async def signal_job(self, slot: Slot, job: "JobRecord", limits: Limits) -> None:
        """Write job.json to scratch_dir/in/job.json. Open fifo write-end, write 'go\n', close."""
    async def wait(self, slot: Slot, timeout: float) -> int:
        """Wait for container exit. Return exit code. SIGKILL + return 137 on timeout."""
    async def reap(self, slot: Slot) -> None:
        """docker rm (best-effort). Remove scratch_dir tree (best-effort)."""
```

**DockerWorkerRuntime** — concrete implementation backed by `DockerRuntime`.

`poll_fifo`: polling loop every 0.25s checking if `Path(slot.scratch_dir / "in" / "control.fifo")` exists. Returns `True` as soon as it appears or `False` on timeout. Use `await asyncio.sleep(0.25)`.

`signal_job`:
1. Write `job.json` to `scratch_dir/in/job.json` (sync write in threadpool via `asyncio.to_thread`).
2. Open the FIFO for writing (non-blocking `os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)`). On
   ENXIO (no reader yet), retry with exponential backoff up to 2s total. Then write `b"go\n"` and close.

`wait`: call `DockerRuntime.wait()` via `asyncio.wait_for(docker.wait(container_id), timeout)`. On
`asyncio.TimeoutError`, call `docker.kill(container_id)` then return 137.

**job.json schema** passed to the worker:

The worker already reads `JobDescriptor` from Java. The Python side must write a dict that matches
`JobDescriptor`'s `@JsonProperty` names. Read `worker_jvm/src/main/java/io/redtusk/worker/JobDescriptor.java`
to get the exact field names. Write it with `json.dumps(..., ensure_ascii=False)`.

### Task 5 — Dispatcher (`dispatcher.py`)

```python
class Dispatcher:
    def __init__(
        self,
        pool: Pool,
        store: JobStore,
        worker_runtime: WorkerRuntime,
        limits: Limits,
    ) -> None: ...

    async def start(self) -> None:
        # Start pool.start() and _claim_loop task.

    async def stop(self) -> None:
        # Cancel _claim_loop, pool.stop().

    async def _claim_loop(self) -> None:
        # Tight loop:
        #   jobs = await store.list_by_state(JobState.QUEUED, limit=limits.pool_max_size)
        #   for each job, if we have IDLE slots, _dispatch(job) as a task
        #   await asyncio.sleep(0.1)   # don't spin-burn CPU

    async def _dispatch(self, job: JobRecord) -> None:
        # 1. Transition job QUEUED → RUNNING in store.
        # 2. claim a slot from pool (timeout = limits.job_timeout_s; PoolExhausted → fail job)
        # 3. Hardlink job input to scratch_dir/in/ (asyncio.to_thread os.link)
        # 4. worker_runtime.signal_job(slot, job, limits)
        # 5. exit_code = await worker_runtime.wait(slot, timeout=limits.job_timeout_s)
        # 6. If exit_code == 0: _ingest_result(slot, job)
        #    Else: _fail_job(job, code="worker_crash" if exit_code != 137 else "timeout")
        # 7. pool.release(slot, success=(exit_code == 0))

    async def _ingest_result(self, slot: Slot, job: JobRecord) -> None:
        # 1. Read scratch_dir/out/metadata.json; cap at limits.max_metadata_bytes.
        # 2. parse JSON; validate against schema (call validate_rmeta from schema.py).
        # 3. Recompute SHA-256 on scratch_dir/in/<input_file>; compare to metadata.input.sha256.
        # 4. If any check fails: _fail_job(job, code="metadata_invalid").
        # 5. Copy scratch_dir/out/ tree to artifact_dir(job.id).
        # 6. Update job: state=succeeded, result=rmeta dict.

    async def submit_sync(
        self,
        body: bytes,
        filename: str,
        limits: Limits,
    ) -> ExtractResult:
        # Used by tika-compat endpoints (Plan 5).
        # 1. Write body to a temp file in submission volume.
        # 2. Build an ephemeral JobRecord (no persistence).
        # 3. Claim a slot (timeout=limits.sync_queue_timeout_s) → 503 on PoolExhaustedError.
        # 4. Signal worker, wait, ingest.
        # 5. Return ExtractResult (translated in api.py).

    def is_healthy(self) -> bool:
        return self.pool.is_healthy()
```

`artifact_dir(job_id: str) -> Path`: `Path(limits.artifact_root) / job_id[:2] / job_id`.
Add `artifact_root: str = "/var/lib/redtusk/artifacts"` to Limits (env: `REDTUSK_ARTIFACT_ROOT`).

Dispatcher must NOT import `docker` SDK — all Docker interaction goes through `DockerRuntime`.

### Task 6 — Unit tests

#### `tests/unit/test_pool.py`

Use `pytest-asyncio` (`@pytest.mark.asyncio`). Create a `MockWorkerRuntime` with `AsyncMock` methods
that track calls.

Cover:
- `claim()` returns an IDLE slot immediately when one is available.
- `claim()` blocks and unblocks when a warming slot becomes idle.
- `claim()` raises `PoolExhaustedError` after timeout.
- `release(success=True)` transitions to DRAINING and triggers a replacement spawn.
- `release(success=False)` marks DRAINING; slot is not counted as healthy.
- SPAWN_FAILED → exponential retry → after max retries, target_size decrements.
- Burst trigger: when queued count stays > 0 for burst_trigger_s, extra slots are spawned.
- Burst drain: idle burst slots are reaped after burst_drain_s.
- `is_healthy()` returns True while pool is warming up, False after sustained zero IDLE.

#### `tests/unit/test_dispatcher.py`

Use `AsyncMock` for pool and store. Cover:
- `_dispatch()` happy path: job transitions QUEUED→RUNNING→SUCCEEDED.
- Worker crash (exit 1): job transitions to FAILED with code `worker_crash`.
- Worker timeout (exit 137): job transitions to FAILED with code `timeout`.
- Metadata validation failure: job transitions to FAILED with code `metadata_invalid`.
- SHA-256 mismatch: job transitions to FAILED.
- PoolExhaustedError during claim: job transitions to FAILED.

For `_ingest_result`, write a real metadata.json to a temp directory so the schema validation code path
runs (use `pytest`'s `tmp_path` fixture).

#### `tests/unit/test_worker_runtime.py`

Mock `DockerRuntime` with `AsyncMock`. Cover:
- `create_scratch()` creates the expected directory tree.
- `spawn()` calls `DockerRuntime.run()` with expected hardening argv.
- `poll_fifo()` returns True when fifo appears within timeout.
- `poll_fifo()` returns False when timeout elapses.
- `signal_job()` writes correct job.json and writes `b"go\n"` to fifo.
- `wait()` returns exit code on clean exit.
- `wait()` sends SIGKILL and returns 137 on timeout.
- `reap()` calls `DockerRuntime.rm()` and removes the scratch directory.

#### `tests/unit/test_sandbox_container.py`

Pure unit test, no async needed. Cover:
- `build_run_argv("runc", "default", ...)` contains `--cap-drop ALL`, no `--cap-add`.
- `build_run_argv("runsc", "default", ...)` contains `--runtime runsc`.
- `build_run_argv("runc", "high-density", ...)` contains `--cap-add CHECKPOINT_RESTORE`.
- All required hardening flags present in all combinations.
- `--network none` always present.
- `--read-only` always present.

## Acceptance criteria

- `pytest tests/unit/test_pool.py tests/unit/test_dispatcher.py tests/unit/test_worker_runtime.py tests/unit/test_sandbox_container.py` passes with no skips.
- `pytest tests/unit tests/cli tests/http` (full unit suite) passes.
- `ruff check src tests` clean.
- `mypy src` clean.
- Pool state transitions never leave the Pool in an inconsistent state (invariant: `warming + idle + assigned ≤ target_size + burst_slots_count` at all times).

## What this plan does NOT include

- FastAPI app (`api.py`) — Plan 5.
- Translation layer (`translation.py`) — Plan 5.
- High-density Dockerfile + CRaC — Plan 6.
- Compose stack + parity suite — Plan 7.
- `cli.py` serve/dispatcher subcommands — Plan 5.
- Integration tests (need real Docker + JVM) — gated by `integration` marker, written in Plan 7.
