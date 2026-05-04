# RedTusk Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational `redtusk` Python library — types, errors, configuration, JobStore (3 backends), retention sweeper, and observability scaffolding — with full unit-test coverage. No HTTP service, no Docker, no JVM yet. This is the base everything else builds on.

**Architecture:** Pure-stdlib data model (frozen dataclasses) with `to_dict`/`from_dict` round-trip and JSON Schema validation. JobStore is a protocol with three implementations (memory, sqlite, postgres-via-psycopg). Limits configuration funnels through a single `Limits.from_env()` so CLI and HTTP API will share one source of truth. Observability uses structlog (JSON output) + prometheus_client.

**Tech Stack:** Python 3.12+, frozen dataclasses, `psycopg[binary,pool]>=3.2`, `jsonschema>=4.21`, `structlog>=24.1`, `prometheus-client>=0.20`, `pytest>=8.0`, `pytest-asyncio>=0.23`.

---

## File Structure

```
RedTusk/
├── .gitignore                          # ignore venv, caches, sqlite db
├── pyproject.toml                      # package metadata + deps
├── README.md                           # one-paragraph stub
├── src/redtusk/
│   ├── __init__.py                     # exports + version
│   ├── _version.py                     # __version__ = "0.1.0"
│   ├── errors.py                       # exception hierarchy
│   ├── limits.py                       # Limits dataclass + from_env
│   ├── types.py                        # in-memory data model
│   ├── schema.py                       # JSON Schema for canonical rmeta + validators
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py                  # structlog setup
│   │   └── metrics.py                  # prometheus_client registry + helpers
│   └── jobs/
│       ├── __init__.py
│       ├── base.py                     # JobStore protocol
│       ├── memory.py                   # in-process backend
│       ├── sql_store.py                # sqlite + postgres
│       └── retention.py                # async TTL sweeper
└── tests/
    ├── __init__.py
    ├── conftest.py                     # asyncio mode + shared fixtures
    └── unit/
        ├── __init__.py
        ├── test_errors.py
        ├── test_limits.py
        ├── test_types_values.py
        ├── test_types_extract_result.py
        ├── test_types_job_record.py
        ├── test_schema_validation.py
        ├── test_jobs_protocol.py
        ├── test_jobs_memory.py
        ├── test_jobs_sql_sqlite.py
        ├── test_jobs_sql_postgres.py
        ├── test_retention.py
        ├── test_observability_logging.py
        └── test_observability_metrics.py
```

Per-file responsibility:
- `errors.py` — every exception type the library raises. No logic, no I/O.
- `limits.py` — the single `Limits` frozen dataclass + `from_env()` classmethod. No I/O beyond reading `os.environ`.
- `types.py` — frozen dataclasses for `JobState`, `JobRecord`, `ExtractResult`, `EmbeddedEntry`, `QrResult`, `OcrResult`, `WarningEntry`, `TruncationInfo`, `SandboxInfo`, `InputInfo`, `ExtractionInfo`, `LimitsInfo`. Each gets `to_dict`/`from_dict`.
- `schema.py` — JSON Schema (Draft-07) for the canonical rmeta document + a `validate_rmeta(d)` helper that raises `SchemaValidationError`.
- `observability/logging.py` — `configure_logging()` sets up structlog with JSON output; `get_logger(name)` returns a structlog logger.
- `observability/metrics.py` — module-level Prometheus registry + counters/gauges/histograms used across the codebase. No metric is created elsewhere.
- `jobs/base.py` — `JobStore` Protocol with all methods every backend implements. No implementation, no I/O.
- `jobs/memory.py` — in-process dict-backed implementation, asyncio-safe via `asyncio.Lock`.
- `jobs/sql_store.py` — single class `SqlJobStore` that handles both sqlite (`sqlite+aiosqlite://`) and postgres (`postgresql://`) via psycopg async. Schema migration happens on `connect()`.
- `jobs/retention.py` — `RetentionSweeper(store, ttl_s, interval_s)` async task that wakes periodically and calls `store.delete_expired()`.

---

## Task 1: Repo bootstrap

**Files:**
- Create: `/home/coz/Downloads/RedTusk/.gitignore`
- Create: `/home/coz/Downloads/RedTusk/pyproject.toml`
- Create: `/home/coz/Downloads/RedTusk/README.md`
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/__init__.py`
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/_version.py`
- Create: `/home/coz/Downloads/RedTusk/tests/__init__.py`
- Create: `/home/coz/Downloads/RedTusk/tests/conftest.py`
- Create: `/home/coz/Downloads/RedTusk/tests/unit/__init__.py`

- [ ] **Step 1: Write `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
build/
dist/

# Virtual envs
.venv/
venv/

# Tooling caches
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Database files (sqlite default location)
*.db
*.db-journal
redtusk-jobs.db*

# Logs
*.log

# Editor / OS
.vscode/
.idea/
.DS_Store

# Local agent state
.claude/
CLAUDE.md
AGENTS.md
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "redtusk"
version = "0.1.0"
description = "Sandboxed Apache Tika service with warm-pool worker containers"
license = {text = "MIT"}
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",
    "structlog>=24.1.0",
    "prometheus-client>=0.20.0",
    "psycopg[binary,pool]>=3.2.0",
    "aiosqlite>=0.20.0",
    "jsonschema>=4.21.0",
    "python-magic>=0.4.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "ruff>=0.3.0",
    "mypy>=1.9.0",
]

[project.scripts]
redtusk = "redtusk.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra -q"
markers = [
    "integration: requires real worker container or external services (slow)",
    "docker: requires docker daemon",
    "postgres: requires a running postgres instance",
    "jvm: requires JDK + maven",
]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "N", "ASYNC"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
```

- [ ] **Step 3: Write `README.md`**

```markdown
# RedTusk

Sandboxed Apache Tika service with warm-pool worker containers and a tika-server-compatible HTTP API.

See `docs/specs/2026-05-04-redtusk-design.md` for the full design.

## Status

In active development. v1 not yet released.
```

- [ ] **Step 4: Write `src/redtusk/_version.py`**

```python
"""Single source of truth for RedTusk's version string."""
from __future__ import annotations

__version__ = "0.1.0"
```

- [ ] **Step 5: Write `src/redtusk/__init__.py`**

```python
"""RedTusk: sandboxed Apache Tika service."""
from __future__ import annotations

from redtusk._version import __version__

__all__ = ["__version__"]
```

- [ ] **Step 6: Write `tests/__init__.py` and `tests/unit/__init__.py`**

Both files are empty. Create them with no content (zero-byte files).

- [ ] **Step 7: Write `tests/conftest.py`**

```python
"""Shared pytest fixtures for the RedTusk test suite."""
from __future__ import annotations

import pytest


@pytest.fixture
def fixed_now() -> str:
    """A deterministic ISO-8601 timestamp used by tests that need a fake 'now'."""
    return "2026-05-04T18:23:11+00:00"
```

- [ ] **Step 8: Verify the package installs and version is correct**

```bash
cd /home/coz/Downloads/RedTusk
python3 -m venv .venv
.venv/bin/pip install -e .[dev]
.venv/bin/python -c "import redtusk; print(redtusk.__version__)"
```

Expected output:
```
0.1.0
```

- [ ] **Step 9: Verify pytest runs (no tests yet, but framework healthy)**

```bash
.venv/bin/pytest tests/ -v
```

Expected output (last line):
```
no tests ran in 0.01s
```

- [ ] **Step 10: Commit**

```bash
cd /home/coz/Downloads/RedTusk
git add .gitignore pyproject.toml README.md src/ tests/
git commit -m "$(cat <<'EOF'
chore: bootstrap python package layout

Initial pyproject.toml with runtime + dev deps, package skeleton
under src/redtusk/, pytest config with asyncio mode and markers
for integration/docker/postgres/jvm gating.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Errors module

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/errors.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_errors.py`

The exception hierarchy is small but central — every other module raises one of these. Building it first means every later test can assert against named exception types.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the redtusk.errors exception hierarchy."""
from __future__ import annotations

import pytest

from redtusk.errors import (
    ConfigurationError,
    DispatchError,
    ExtractionError,
    JobNotFoundError,
    JobNotTerminalError,
    PoolExhaustedError,
    RedTuskError,
    SchemaValidationError,
    StorageError,
    WorkerError,
)


def test_all_errors_inherit_from_base() -> None:
    """Every RedTusk exception must inherit from RedTuskError so callers
    can catch the whole family with one except clause."""
    subclasses = [
        ConfigurationError,
        DispatchError,
        ExtractionError,
        JobNotFoundError,
        JobNotTerminalError,
        PoolExhaustedError,
        SchemaValidationError,
        StorageError,
        WorkerError,
    ]
    for cls in subclasses:
        assert issubclass(cls, RedTuskError), f"{cls.__name__} must inherit from RedTuskError"


def test_base_inherits_from_exception() -> None:
    assert issubclass(RedTuskError, Exception)


def test_job_not_found_carries_job_id() -> None:
    exc = JobNotFoundError("abc-123")
    assert exc.job_id == "abc-123"
    assert "abc-123" in str(exc)


def test_job_not_terminal_carries_state() -> None:
    exc = JobNotTerminalError("abc-123", "running")
    assert exc.job_id == "abc-123"
    assert exc.state == "running"
    assert "abc-123" in str(exc)
    assert "running" in str(exc)


def test_pool_exhausted_carries_timeout() -> None:
    exc = PoolExhaustedError(timeout_s=30.0)
    assert exc.timeout_s == 30.0
    assert "30" in str(exc)


def test_schema_validation_carries_path() -> None:
    exc = SchemaValidationError(path="entries[0].sha256", reason="not a hex string")
    assert exc.path == "entries[0].sha256"
    assert exc.reason == "not a hex string"
    assert "entries[0].sha256" in str(exc)


def test_can_catch_all_with_base() -> None:
    """A caller using `except RedTuskError` should catch every subclass."""
    for raise_cls in [
        ConfigurationError("x"),
        DispatchError("x"),
        ExtractionError("x"),
        JobNotFoundError("x"),
        JobNotTerminalError("x", "queued"),
        PoolExhaustedError(timeout_s=1.0),
        SchemaValidationError(path="x", reason="x"),
        StorageError("x"),
        WorkerError("x"),
    ]:
        with pytest.raises(RedTuskError):
            raise raise_cls
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/coz/Downloads/RedTusk
.venv/bin/pytest tests/unit/test_errors.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.errors'`

- [ ] **Step 3: Write the implementation**

```python
"""Exception hierarchy for RedTusk.

Every exception RedTusk raises inherits from RedTuskError so callers
can catch the whole family with `except RedTuskError`. Specific subclasses
carry the structured fields callers will most often want to inspect.
"""
from __future__ import annotations


class RedTuskError(Exception):
    """Base class for all RedTusk exceptions."""


class ConfigurationError(RedTuskError):
    """Raised when configuration (env vars, Limits) is invalid or contradictory."""


class StorageError(RedTuskError):
    """Raised when the JobStore backend fails to read/write."""


class JobNotFoundError(RedTuskError):
    """Raised when a job ID is not present in the JobStore."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"job not found: {job_id}")
        self.job_id = job_id


class JobNotTerminalError(RedTuskError):
    """Raised when a delete is attempted on a job that is not in a terminal state.

    Terminal states: succeeded, failed.
    """

    def __init__(self, job_id: str, state: str) -> None:
        super().__init__(f"job {job_id} is not terminal (state={state})")
        self.job_id = job_id
        self.state = state


class PoolExhaustedError(RedTuskError):
    """Raised when the warm pool has no idle slot within the requested timeout."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(f"warm pool exhausted after {timeout_s:.1f}s")
        self.timeout_s = timeout_s


class DispatchError(RedTuskError):
    """Raised when the dispatcher cannot complete a job lifecycle step."""


class WorkerError(RedTuskError):
    """Raised when a worker container fails to spawn, signal, or produce output."""


class ExtractionError(RedTuskError):
    """Raised when extraction itself failed (Tika error, scanner crash, etc.)."""


class SchemaValidationError(RedTuskError):
    """Raised when a worker-produced rmeta document fails schema validation."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"rmeta validation failed at {path}: {reason}")
        self.path = path
        self.reason = reason
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_errors.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/errors.py tests/unit/test_errors.py
git commit -m "$(cat <<'EOF'
feat(errors): add exception hierarchy

Single base RedTuskError so callers can catch the whole family with
one except clause. Specific subclasses carry structured fields
(job_id, state, timeout_s, path) for the cases callers most often
want to inspect.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Limits + from_env

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/limits.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_limits.py`

The `Limits` dataclass is the single configuration source for the entire codebase. Both the future CLI and HTTP API will read from `Limits.from_env()`, so this is the discipline that keeps them in sync — exactly the pattern ClippyShot uses.

Every field has a corresponding `REDTUSK_<UPPERCASE_NAME>` env var. `from_env()` reads each one if present, otherwise uses the dataclass default.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for redtusk.limits.Limits and Limits.from_env()."""
from __future__ import annotations

import dataclasses
import os
from unittest.mock import patch

import pytest

from redtusk.errors import ConfigurationError
from redtusk.limits import Limits


def test_defaults_are_sensible() -> None:
    """Defaults should match the design spec's documented values."""
    limits = Limits()

    # Worker / extraction
    assert limits.max_input == 100 * 1024 * 1024
    assert limits.job_timeout_s == 60
    assert limits.max_recursion_depth == 10
    assert limits.max_embedded_entries == 5000
    assert limits.max_extracted_bytes == 500 * 1024 * 1024
    assert limits.max_metadata_bytes == 64 * 1024 * 1024

    # OCR/QR
    assert limits.enable_qr is True
    assert limits.enable_ocr is False
    assert limits.ocr_lang == "eng"
    assert limits.ocr_psm == 3
    assert limits.ocr_timeout_s == 60
    assert limits.ocr_per_call_timeout_s == 30
    assert limits.ocr_all is False

    # Pool
    assert limits.pool_size == 10
    assert limits.pool_burst_size == 5
    assert limits.pool_burst_trigger_s == 3
    assert limits.pool_burst_drain_s == 60
    assert limits.pool_max_size == 32
    assert limits.pool_spawn_rate_limit == 4.0
    assert limits.pool_spawn_retry_max == 5

    # Worker boot
    assert limits.worker_warmup_timeout_s == 15
    assert limits.sync_queue_timeout_s == 30

    # Profile
    assert limits.profile == "default"

    # Job retention
    assert limits.job_retention_seconds == 86400

    # Database
    assert limits.database_url == "sqlite:///./redtusk-jobs.db"

    # Disable knobs
    assert limits.disable_ksm is False


def test_is_frozen() -> None:
    limits = Limits()
    with pytest.raises(dataclasses.FrozenInstanceError):
        limits.pool_size = 99  # type: ignore[misc]


def test_from_env_with_no_env_returns_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        limits = Limits.from_env()
    assert limits == Limits()


def test_from_env_reads_int_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "20"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_size == 20


def test_from_env_reads_float_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SPAWN_RATE_LIMIT": "8.5"}, clear=True):
        limits = Limits.from_env()
    assert limits.pool_spawn_rate_limit == 8.5


def test_from_env_reads_str_fields() -> None:
    with patch.dict(os.environ, {"REDTUSK_OCR_LANG": "deu"}, clear=True):
        limits = Limits.from_env()
    assert limits.ocr_lang == "deu"


def test_from_env_reads_bool_truthy() -> None:
    for truthy in ["1", "true", "True", "TRUE", "yes", "on"]:
        with patch.dict(os.environ, {"REDTUSK_ENABLE_OCR": truthy}, clear=True):
            limits = Limits.from_env()
        assert limits.enable_ocr is True, f"{truthy!r} should be truthy"


def test_from_env_reads_bool_falsy() -> None:
    for falsy in ["0", "false", "False", "FALSE", "no", "off", ""]:
        with patch.dict(os.environ, {"REDTUSK_ENABLE_QR": falsy}, clear=True):
            limits = Limits.from_env()
        assert limits.enable_qr is False, f"{falsy!r} should be falsy"


def test_from_env_explicit_overrides_take_precedence() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "20"}, clear=True):
        limits = Limits.from_env(pool_size=99)
    assert limits.pool_size == 99


def test_from_env_invalid_int_raises_configuration_error() -> None:
    with patch.dict(os.environ, {"REDTUSK_POOL_SIZE": "not-a-number"}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_POOL_SIZE" in str(ei.value)


def test_from_env_invalid_float_raises_configuration_error() -> None:
    with patch.dict(
        os.environ, {"REDTUSK_POOL_SPAWN_RATE_LIMIT": "abc"}, clear=True
    ):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_POOL_SPAWN_RATE_LIMIT" in str(ei.value)


def test_from_env_unknown_override_raises() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env(no_such_field=123)
    assert "no_such_field" in str(ei.value)


def test_from_env_invalid_profile_raises() -> None:
    with patch.dict(os.environ, {"REDTUSK_PROFILE": "garbage"}, clear=True):
        with pytest.raises(ConfigurationError) as ei:
            Limits.from_env()
    assert "REDTUSK_PROFILE" in str(ei.value)
    assert "garbage" in str(ei.value)


def test_from_env_valid_profiles() -> None:
    for profile in ["default", "high-density"]:
        with patch.dict(os.environ, {"REDTUSK_PROFILE": profile}, clear=True):
            limits = Limits.from_env()
        assert limits.profile == profile
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_limits.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.limits'`

- [ ] **Step 3: Write the implementation**

```python
"""Configuration for RedTusk.

A single ``Limits`` frozen dataclass holds every tunable. Both the CLI
and the HTTP API read from ``Limits.from_env()`` so they cannot drift.
Each field maps to the env var ``REDTUSK_<UPPERCASE_FIELD_NAME>``.
"""
from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, fields
from typing import Any

from redtusk.errors import ConfigurationError

_VALID_PROFILES = {"default", "high-density"}
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


@dataclass(frozen=True)
class Limits:
    # Worker / extraction
    max_input: int = 100 * 1024 * 1024
    job_timeout_s: int = 60
    max_recursion_depth: int = 10
    max_embedded_entries: int = 5000
    max_extracted_bytes: int = 500 * 1024 * 1024
    max_metadata_bytes: int = 64 * 1024 * 1024

    # OCR / QR scanners
    enable_qr: bool = True
    enable_ocr: bool = False
    ocr_lang: str = "eng"
    ocr_psm: int = 3
    ocr_timeout_s: int = 60
    ocr_per_call_timeout_s: int = 30
    ocr_all: bool = False

    # Pool
    pool_size: int = 10
    pool_burst_size: int = 5
    pool_burst_trigger_s: int = 3
    pool_burst_drain_s: int = 60
    pool_max_size: int = 32
    pool_spawn_rate_limit: float = 4.0
    pool_spawn_retry_max: int = 5

    # Worker boot
    worker_warmup_timeout_s: int = 15
    sync_queue_timeout_s: int = 30

    # Deployment profile
    profile: str = "default"

    # Job retention (TTL)
    job_retention_seconds: int = 86400

    # JobStore
    database_url: str = "sqlite:///./redtusk-jobs.db"

    # Operator opt-outs
    disable_ksm: bool = False

    @classmethod
    def from_env(cls, **overrides: Any) -> Limits:
        """Construct a Limits from environment variables, then apply explicit overrides.

        Each field maps to ``REDTUSK_<FIELD_NAME_UPPER>`` (e.g. ``pool_size`` ->
        ``REDTUSK_POOL_SIZE``). Bools accept ``1/true/yes/on`` (case-insensitive)
        as truthy; ``0/false/no/off/""`` as falsy. Anything else raises
        ``ConfigurationError``.

        Explicit ``overrides`` are validated against known fields and replace
        anything from the environment.
        """
        field_map = {f.name: f for f in fields(cls)}

        # Validate overrides reference real fields before anything else.
        for key in overrides:
            if key not in field_map:
                raise ConfigurationError(
                    f"unknown Limits field in override: {key!r}"
                )

        kwargs: dict[str, Any] = {}
        for name, field in field_map.items():
            env_name = f"REDTUSK_{name.upper()}"
            if env_name not in os.environ:
                continue
            raw = os.environ[env_name]
            try:
                kwargs[name] = _coerce(field.type, raw, env_name)
            except ValueError as e:
                raise ConfigurationError(str(e)) from e

        kwargs.update(overrides)

        instance = cls(**kwargs)
        if instance.profile not in _VALID_PROFILES:
            raise ConfigurationError(
                f"REDTUSK_PROFILE must be one of {sorted(_VALID_PROFILES)}, "
                f"got {instance.profile!r}"
            )
        return instance


def _coerce(type_str: str | type, raw: str, env_name: str) -> Any:
    """Parse the env-var string for a given dataclass field type.

    The type comes in as a string (e.g. "int") because ``from __future__ import
    annotations`` defers evaluation. We resolve the few primitives we use.
    """
    target = type_str if isinstance(type_str, str) else type_str.__name__
    if target == "int":
        try:
            return int(raw)
        except ValueError as e:
            raise ValueError(
                f"{env_name}={raw!r} is not a valid int"
            ) from e
    if target == "float":
        try:
            return float(raw)
        except ValueError as e:
            raise ValueError(
                f"{env_name}={raw!r} is not a valid float"
            ) from e
    if target == "bool":
        lowered = raw.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
        raise ValueError(
            f"{env_name}={raw!r} is not a valid bool "
            f"(expected one of {sorted(_TRUTHY | _FALSY)})"
        )
    if target == "str":
        return raw
    raise ValueError(f"unsupported Limits field type: {target!r}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_limits.py -v
```

Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/limits.py tests/unit/test_limits.py
git commit -m "$(cat <<'EOF'
feat(limits): add Limits dataclass + from_env

Single source of truth for all REDTUSK_* env vars. Frozen dataclass;
from_env reads each field from REDTUSK_<UPPERCASE_NAME>, coerces to
the field type, and validates the deployment profile. Explicit
keyword overrides replace env values for tests / programmatic use.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Value types — QR, OCR, EmbeddedEntry building blocks

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/types.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_types_values.py`

The smaller value types come first because `EmbeddedEntry` composes them. Done in one task because each type is tiny and they're tightly related.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the building-block value types in redtusk.types."""
from __future__ import annotations

import dataclasses

import pytest

from redtusk.types import (
    EmbeddedEntry,
    JobState,
    OcrResult,
    QrCode,
    QrResult,
    SkipReason,
    TruncationInfo,
    TruncationReason,
    WarningEntry,
)


def test_job_state_string_values() -> None:
    assert JobState.QUEUED.value == "queued"
    assert JobState.RUNNING.value == "running"
    assert JobState.SUCCEEDED.value == "succeeded"
    assert JobState.FAILED.value == "failed"


def test_job_state_terminal_predicate() -> None:
    assert JobState.SUCCEEDED.is_terminal()
    assert JobState.FAILED.is_terminal()
    assert not JobState.QUEUED.is_terminal()
    assert not JobState.RUNNING.is_terminal()


def test_skip_reason_string_values() -> None:
    """SkipReason vocabulary is the same for QR and OCR."""
    assert SkipReason.NO_IMAGES.value == "no_images"
    assert SkipReason.TIMEOUT_BUDGET.value == "timeout_budget"
    assert SkipReason.ERROR.value == "error"
    assert SkipReason.DISABLED.value == "disabled"


def test_truncation_reason_string_values() -> None:
    assert TruncationReason.MAX_EMBEDDED_ENTRIES.value == "max_embedded_entries"
    assert TruncationReason.MAX_RECURSION_DEPTH.value == "max_recursion_depth"
    assert TruncationReason.MAX_EXTRACTED_BYTES.value == "max_extracted_bytes"


def test_qr_code_is_frozen() -> None:
    code = QrCode(type="QRCODE", data="hello", bbox=(1, 2, 3, 4))
    with pytest.raises(dataclasses.FrozenInstanceError):
        code.data = "changed"  # type: ignore[misc]


def test_qr_code_round_trip() -> None:
    code = QrCode(type="QRCODE", data="https://example.com", bbox=(10, 20, 30, 40))
    d = code.to_dict()
    assert d == {
        "type": "QRCODE",
        "data": "https://example.com",
        "bbox": [10, 20, 30, 40],
    }
    assert QrCode.from_dict(d) == code


def test_qr_result_default_empty() -> None:
    r = QrResult()
    assert r.codes == []
    assert r.skipped is None


def test_qr_result_round_trip() -> None:
    r = QrResult(
        codes=[QrCode(type="QRCODE", data="x", bbox=(0, 0, 1, 1))],
        skipped=None,
    )
    d = r.to_dict()
    assert d == {
        "codes": [{"type": "QRCODE", "data": "x", "bbox": [0, 0, 1, 1]}],
        "skipped": None,
    }
    assert QrResult.from_dict(d) == r


def test_qr_result_round_trip_skipped() -> None:
    r = QrResult(codes=[], skipped=SkipReason.DISABLED)
    d = r.to_dict()
    assert d == {"codes": [], "skipped": "disabled"}
    assert QrResult.from_dict(d) == r


def test_ocr_result_default_empty() -> None:
    r = OcrResult()
    assert r.text == ""
    assert r.language is None
    assert r.duration_ms == 0
    assert r.skipped is None


def test_ocr_result_round_trip() -> None:
    r = OcrResult(text="hello", language="eng", duration_ms=412, skipped=None)
    d = r.to_dict()
    assert d == {
        "text": "hello",
        "language": "eng",
        "duration_ms": 412,
        "skipped": None,
    }
    assert OcrResult.from_dict(d) == r


def test_ocr_result_round_trip_skipped() -> None:
    r = OcrResult(skipped=SkipReason.TIMEOUT_BUDGET)
    d = r.to_dict()
    assert d == {
        "text": "",
        "language": None,
        "duration_ms": 0,
        "skipped": "timeout_budget",
    }
    assert OcrResult.from_dict(d) == r


def test_warning_entry_round_trip() -> None:
    w = WarningEntry(code="ocr_scan_error", detail="tesseract crashed", entry_path="/embedded/img1.png")
    d = w.to_dict()
    assert d == {
        "code": "ocr_scan_error",
        "detail": "tesseract crashed",
        "entry_path": "/embedded/img1.png",
    }
    assert WarningEntry.from_dict(d) == w


def test_warning_entry_optional_path() -> None:
    w = WarningEntry(code="x", detail="y")
    d = w.to_dict()
    assert d == {"code": "x", "detail": "y", "entry_path": None}


def test_truncation_info_round_trip() -> None:
    t = TruncationInfo(
        reason=TruncationReason.MAX_EMBEDDED_ENTRIES, limit=5000, observed=6234
    )
    d = t.to_dict()
    assert d == {"reason": "max_embedded_entries", "limit": 5000, "observed": 6234}
    assert TruncationInfo.from_dict(d) == t


def test_embedded_entry_round_trip_full() -> None:
    e = EmbeddedEntry(
        path="/embedded/image1.png",
        parent_path="/",
        depth=1,
        content_type="image/png",
        size_bytes=1024,
        sha256="9f3d" + "0" * 60,
        metadata={"Image-Width": "200"},
        text="",
        language=None,
        qr=QrResult(
            codes=[QrCode(type="QRCODE", data="x", bbox=(0, 0, 10, 10))],
            skipped=None,
        ),
        ocr=OcrResult(text="hi", language="eng", duration_ms=100),
        error=None,
    )
    d = e.to_dict()
    assert EmbeddedEntry.from_dict(d) == e


def test_embedded_entry_root_no_parent() -> None:
    e = EmbeddedEntry(
        path="/",
        parent_path=None,
        depth=0,
        content_type="application/pdf",
        size_bytes=1000,
        sha256="ae1c" + "0" * 60,
        metadata={},
        text="hello",
        language="en",
        qr=QrResult(),
        ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
        error=None,
    )
    assert e.parent_path is None
    assert e.depth == 0
    d = e.to_dict()
    assert d["parent_path"] is None
    assert EmbeddedEntry.from_dict(d) == e
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_types_values.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.types'`

- [ ] **Step 3: Write the implementation**

```python
"""In-memory data model for RedTusk.

Frozen dataclasses for every value the system handles. Each carries
``to_dict`` / ``from_dict`` so they can be serialized to / from the
canonical JSON shape that workers produce and the API serves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        return self in (JobState.SUCCEEDED, JobState.FAILED)


class SkipReason(str, Enum):
    """Why a scanner (QR or OCR) was not run on an entry."""

    NO_IMAGES = "no_images"
    TIMEOUT_BUDGET = "timeout_budget"
    ERROR = "error"
    DISABLED = "disabled"


class TruncationReason(str, Enum):
    """Why recursive extraction was cut short."""

    MAX_EMBEDDED_ENTRIES = "max_embedded_entries"
    MAX_RECURSION_DEPTH = "max_recursion_depth"
    MAX_EXTRACTED_BYTES = "max_extracted_bytes"


@dataclass(frozen=True)
class QrCode:
    type: str
    data: str
    bbox: tuple[int, int, int, int]  # x, y, w, h

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": self.data, "bbox": list(self.bbox)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QrCode:
        bbox = d["bbox"]
        return cls(type=d["type"], data=d["data"], bbox=(bbox[0], bbox[1], bbox[2], bbox[3]))


@dataclass(frozen=True)
class QrResult:
    codes: list[QrCode] = field(default_factory=list)
    skipped: Optional[SkipReason] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "codes": [c.to_dict() for c in self.codes],
            "skipped": self.skipped.value if self.skipped is not None else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QrResult:
        skipped = SkipReason(d["skipped"]) if d.get("skipped") is not None else None
        return cls(
            codes=[QrCode.from_dict(c) for c in d.get("codes", [])],
            skipped=skipped,
        )


@dataclass(frozen=True)
class OcrResult:
    text: str = ""
    language: Optional[str] = None
    duration_ms: int = 0
    skipped: Optional[SkipReason] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "skipped": self.skipped.value if self.skipped is not None else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OcrResult:
        skipped = SkipReason(d["skipped"]) if d.get("skipped") is not None else None
        return cls(
            text=d.get("text", ""),
            language=d.get("language"),
            duration_ms=d.get("duration_ms", 0),
            skipped=skipped,
        )


@dataclass(frozen=True)
class WarningEntry:
    code: str
    detail: str
    entry_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "entry_path": self.entry_path}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WarningEntry:
        return cls(code=d["code"], detail=d["detail"], entry_path=d.get("entry_path"))


@dataclass(frozen=True)
class TruncationInfo:
    reason: TruncationReason
    limit: int
    observed: int

    def to_dict(self) -> dict[str, Any]:
        return {"reason": self.reason.value, "limit": self.limit, "observed": self.observed}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TruncationInfo:
        return cls(
            reason=TruncationReason(d["reason"]),
            limit=d["limit"],
            observed=d["observed"],
        )


@dataclass(frozen=True)
class EmbeddedEntry:
    path: str
    parent_path: Optional[str]
    depth: int
    content_type: str
    size_bytes: int
    sha256: str
    metadata: dict[str, Any]
    text: str
    language: Optional[str]
    qr: QrResult
    ocr: OcrResult
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "parent_path": self.parent_path,
            "depth": self.depth,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "metadata": dict(self.metadata),
            "text": self.text,
            "language": self.language,
            "qr": self.qr.to_dict(),
            "ocr": self.ocr.to_dict(),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EmbeddedEntry:
        return cls(
            path=d["path"],
            parent_path=d.get("parent_path"),
            depth=d["depth"],
            content_type=d["content_type"],
            size_bytes=d["size_bytes"],
            sha256=d["sha256"],
            metadata=dict(d.get("metadata", {})),
            text=d.get("text", ""),
            language=d.get("language"),
            qr=QrResult.from_dict(d["qr"]),
            ocr=OcrResult.from_dict(d["ocr"]),
            error=d.get("error"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_types_values.py -v
```

Expected: 17 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/types.py tests/unit/test_types_values.py
git commit -m "$(cat <<'EOF'
feat(types): add value types (JobState, QR/OCR, EmbeddedEntry)

Frozen dataclasses for every building-block value the canonical
rmeta document carries. Each has to_dict/from_dict for round-trip
serialization. JobState carries an is_terminal() predicate the
JobStore uses to enforce safe-delete semantics. SkipReason and
TruncationReason are enums so the limited vocabularies are checked
at construction time.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: ExtractResult composite type

**Files:**
- Modify: `/home/coz/Downloads/RedTusk/src/redtusk/types.py` (append)
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_types_extract_result.py`

`ExtractResult` is the canonical rmeta document — what the worker writes and the API serves. It composes everything from Task 4 plus a few wrapper structs.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for ExtractResult and its composing wrapper types."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from redtusk.types import (
    EmbeddedEntry,
    ExtractionInfo,
    ExtractResult,
    InputInfo,
    LimitsInfo,
    OcrResult,
    QrResult,
    SandboxInfo,
    SkipReason,
    TruncationInfo,
    TruncationReason,
    WarningEntry,
)


def _root_entry() -> EmbeddedEntry:
    return EmbeddedEntry(
        path="/",
        parent_path=None,
        depth=0,
        content_type="application/pdf",
        size_bytes=1024,
        sha256="ae1c" + "0" * 60,
        metadata={"Author": "test"},
        text="hello",
        language="en",
        qr=QrResult(),
        ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
        error=None,
    )


def _result(**overrides) -> ExtractResult:
    base = ExtractResult(
        redtusk_version="0.1.0",
        tika_version="3.0.0",
        input=InputInfo(
            sha256="ae1c" + "0" * 60,
            size_bytes=1024,
            filename_hint="test.pdf",
            submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc),
        ),
        extraction=ExtractionInfo(
            root_content_type="application/pdf",
            root_language="en",
            duration_ms=412,
            entries=[_root_entry()],
        ),
        limits=LimitsInfo(
            max_recursion_depth=10,
            max_embedded_entries=5000,
            max_extracted_bytes=524288000,
            ocr_timeout_s=60,
        ),
        truncated=None,
        warnings=[],
        sandbox=SandboxInfo(
            profile="default",
            runtime="runsc",
            appcds=True,
            ksm=True,
            crac=False,
        ),
    )
    if overrides:
        from dataclasses import replace
        return replace(base, **overrides)
    return base


def test_input_info_round_trip() -> None:
    info = InputInfo(
        sha256="abc",
        size_bytes=10,
        filename_hint="x.pdf",
        submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc),
    )
    d = info.to_dict()
    assert d == {
        "sha256": "abc",
        "size_bytes": 10,
        "filename_hint": "x.pdf",
        "submitted_at": "2026-05-04T18:23:11+00:00",
    }
    assert InputInfo.from_dict(d) == info


def test_input_info_no_filename_hint() -> None:
    info = InputInfo(
        sha256="abc",
        size_bytes=10,
        filename_hint=None,
        submitted_at=datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc),
    )
    d = info.to_dict()
    assert d["filename_hint"] is None
    assert InputInfo.from_dict(d) == info


def test_extraction_info_round_trip() -> None:
    info = ExtractionInfo(
        root_content_type="application/pdf",
        root_language="en",
        duration_ms=100,
        entries=[_root_entry()],
    )
    d = info.to_dict()
    assert d["root_content_type"] == "application/pdf"
    assert d["root_language"] == "en"
    assert d["duration_ms"] == 100
    assert len(d["entries"]) == 1
    assert ExtractionInfo.from_dict(d) == info


def test_extraction_info_no_root_language() -> None:
    info = ExtractionInfo(
        root_content_type="application/octet-stream",
        root_language=None,
        duration_ms=0,
        entries=[_root_entry()],
    )
    d = info.to_dict()
    assert d["root_language"] is None
    assert ExtractionInfo.from_dict(d) == info


def test_limits_info_round_trip() -> None:
    info = LimitsInfo(
        max_recursion_depth=10,
        max_embedded_entries=5000,
        max_extracted_bytes=524288000,
        ocr_timeout_s=60,
    )
    d = info.to_dict()
    assert d == {
        "max_recursion_depth": 10,
        "max_embedded_entries": 5000,
        "max_extracted_bytes": 524288000,
        "ocr_timeout_s": 60,
    }
    assert LimitsInfo.from_dict(d) == info


def test_sandbox_info_round_trip() -> None:
    s = SandboxInfo(profile="high-density", runtime="runc", appcds=True, ksm=True, crac=True)
    d = s.to_dict()
    assert d == {
        "profile": "high-density",
        "runtime": "runc",
        "appcds": True,
        "ksm": True,
        "crac": True,
    }
    assert SandboxInfo.from_dict(d) == s


def test_extract_result_round_trip_full() -> None:
    r = _result()
    d = r.to_dict()
    parsed = ExtractResult.from_dict(d)
    assert parsed == r


def test_extract_result_with_truncation() -> None:
    r = _result(
        truncated=TruncationInfo(
            reason=TruncationReason.MAX_EMBEDDED_ENTRIES, limit=5000, observed=6000
        )
    )
    d = r.to_dict()
    assert d["truncated"] == {
        "reason": "max_embedded_entries",
        "limit": 5000,
        "observed": 6000,
    }
    assert ExtractResult.from_dict(d) == r


def test_extract_result_with_warnings() -> None:
    r = _result(warnings=[WarningEntry(code="ocr_scan_error", detail="crash")])
    d = r.to_dict()
    assert d["warnings"] == [
        {"code": "ocr_scan_error", "detail": "crash", "entry_path": None}
    ]
    assert ExtractResult.from_dict(d) == r


def test_extract_result_top_level_keys_match_spec() -> None:
    """The top-level shape is part of the public API contract; pin it explicitly."""
    d = _result().to_dict()
    assert set(d.keys()) == {
        "redtusk_version",
        "tika_version",
        "input",
        "extraction",
        "limits",
        "truncated",
        "warnings",
        "sandbox",
    }
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_types_extract_result.py -v
```

Expected: FAIL with `ImportError: cannot import name 'ExtractResult' from 'redtusk.types'`

- [ ] **Step 3: Append implementation to `src/redtusk/types.py`**

Append (do not replace) to the existing `types.py`:

```python


@dataclass(frozen=True)
class InputInfo:
    sha256: str
    size_bytes: int
    filename_hint: Optional[str]
    submitted_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "filename_hint": self.filename_hint,
            "submitted_at": self.submitted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> InputInfo:
        return cls(
            sha256=d["sha256"],
            size_bytes=d["size_bytes"],
            filename_hint=d.get("filename_hint"),
            submitted_at=datetime.fromisoformat(d["submitted_at"]),
        )


@dataclass(frozen=True)
class ExtractionInfo:
    root_content_type: str
    root_language: Optional[str]
    duration_ms: int
    entries: list[EmbeddedEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_content_type": self.root_content_type,
            "root_language": self.root_language,
            "duration_ms": self.duration_ms,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExtractionInfo:
        return cls(
            root_content_type=d["root_content_type"],
            root_language=d.get("root_language"),
            duration_ms=d["duration_ms"],
            entries=[EmbeddedEntry.from_dict(e) for e in d["entries"]],
        )


@dataclass(frozen=True)
class LimitsInfo:
    max_recursion_depth: int
    max_embedded_entries: int
    max_extracted_bytes: int
    ocr_timeout_s: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_recursion_depth": self.max_recursion_depth,
            "max_embedded_entries": self.max_embedded_entries,
            "max_extracted_bytes": self.max_extracted_bytes,
            "ocr_timeout_s": self.ocr_timeout_s,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LimitsInfo:
        return cls(
            max_recursion_depth=d["max_recursion_depth"],
            max_embedded_entries=d["max_embedded_entries"],
            max_extracted_bytes=d["max_extracted_bytes"],
            ocr_timeout_s=d["ocr_timeout_s"],
        )


@dataclass(frozen=True)
class SandboxInfo:
    profile: str
    runtime: str
    appcds: bool
    ksm: bool
    crac: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "runtime": self.runtime,
            "appcds": self.appcds,
            "ksm": self.ksm,
            "crac": self.crac,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SandboxInfo:
        return cls(
            profile=d["profile"],
            runtime=d["runtime"],
            appcds=d["appcds"],
            ksm=d["ksm"],
            crac=d["crac"],
        )


@dataclass(frozen=True)
class ExtractResult:
    redtusk_version: str
    tika_version: str
    input: InputInfo
    extraction: ExtractionInfo
    limits: LimitsInfo
    truncated: Optional[TruncationInfo]
    warnings: list[WarningEntry]
    sandbox: SandboxInfo

    def to_dict(self) -> dict[str, Any]:
        return {
            "redtusk_version": self.redtusk_version,
            "tika_version": self.tika_version,
            "input": self.input.to_dict(),
            "extraction": self.extraction.to_dict(),
            "limits": self.limits.to_dict(),
            "truncated": self.truncated.to_dict() if self.truncated is not None else None,
            "warnings": [w.to_dict() for w in self.warnings],
            "sandbox": self.sandbox.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExtractResult:
        truncated = (
            TruncationInfo.from_dict(d["truncated"]) if d.get("truncated") is not None else None
        )
        return cls(
            redtusk_version=d["redtusk_version"],
            tika_version=d["tika_version"],
            input=InputInfo.from_dict(d["input"]),
            extraction=ExtractionInfo.from_dict(d["extraction"]),
            limits=LimitsInfo.from_dict(d["limits"]),
            truncated=truncated,
            warnings=[WarningEntry.from_dict(w) for w in d.get("warnings", [])],
            sandbox=SandboxInfo.from_dict(d["sandbox"]),
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_types_extract_result.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Run the full unit test suite to make sure nothing regressed**

```bash
.venv/bin/pytest tests/unit/ -v
```

Expected: all tests from Tasks 2-5 pass (≈ 36 total).

- [ ] **Step 6: Commit**

```bash
git add src/redtusk/types.py tests/unit/test_types_extract_result.py
git commit -m "$(cat <<'EOF'
feat(types): add ExtractResult and composing wrappers

ExtractResult is the canonical rmeta document workers produce and
the API serves. Composes InputInfo, ExtractionInfo, LimitsInfo,
SandboxInfo, and the value types from the previous commit. Top-level
key set is pinned by an explicit test so accidental schema drift
fails CI.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: JobRecord type

**Files:**
- Modify: `/home/coz/Downloads/RedTusk/src/redtusk/types.py` (append)
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_types_job_record.py`

`JobRecord` is what the JobStore persists. It carries identity, state, timestamps, input fingerprint, and (when complete) the `ExtractResult`. Mutable, unlike the value types — the dispatcher mutates it across the lifecycle.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for JobRecord and its lifecycle helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from redtusk.types import (
    EmbeddedEntry,
    ExtractionInfo,
    ExtractResult,
    InputInfo,
    JobRecord,
    JobState,
    LimitsInfo,
    OcrResult,
    QrResult,
    SandboxInfo,
    SkipReason,
)


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _result() -> ExtractResult:
    return ExtractResult(
        redtusk_version="0.1.0",
        tika_version="3.0.0",
        input=InputInfo(
            sha256="ae1c" + "0" * 60,
            size_bytes=10,
            filename_hint=None,
            submitted_at=_ts("2026-05-04T18:23:11+00:00"),
        ),
        extraction=ExtractionInfo(
            root_content_type="text/plain",
            root_language="en",
            duration_ms=10,
            entries=[
                EmbeddedEntry(
                    path="/",
                    parent_path=None,
                    depth=0,
                    content_type="text/plain",
                    size_bytes=10,
                    sha256="ae1c" + "0" * 60,
                    metadata={},
                    text="hi",
                    language="en",
                    qr=QrResult(),
                    ocr=OcrResult(skipped=SkipReason.NO_IMAGES),
                )
            ],
        ),
        limits=LimitsInfo(
            max_recursion_depth=10,
            max_embedded_entries=5000,
            max_extracted_bytes=524288000,
            ocr_timeout_s=60,
        ),
        truncated=None,
        warnings=[],
        sandbox=SandboxInfo(
            profile="default", runtime="runsc", appcds=True, ksm=True, crac=False
        ),
    )


def test_new_job_defaults() -> None:
    """A newly-created job is queued, no started/completed/result, no error."""
    job_id = str(uuid.uuid4())
    submitted = _ts("2026-05-04T18:23:11+00:00")
    job = JobRecord(
        id=job_id,
        state=JobState.QUEUED,
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    assert job.id == job_id
    assert job.state == JobState.QUEUED
    assert job.submitted_at == submitted
    assert job.started_at is None
    assert job.completed_at is None
    assert job.result is None
    assert job.error_code is None


def test_to_dict_round_trip_queued() -> None:
    submitted = _ts("2026-05-04T18:23:11+00:00")
    job = JobRecord(
        id="abc-123",
        state=JobState.QUEUED,
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint="x.pdf",
        result=None,
        error_code=None,
        error_detail=None,
    )
    d = job.to_dict()
    assert d["id"] == "abc-123"
    assert d["state"] == "queued"
    assert d["submitted_at"] == "2026-05-04T18:23:11+00:00"
    assert d["started_at"] is None
    assert d["completed_at"] is None
    assert d["filename_hint"] == "x.pdf"
    assert d["result"] is None
    assert JobRecord.from_dict(d) == job


def test_to_dict_round_trip_succeeded() -> None:
    submitted = _ts("2026-05-04T18:23:11+00:00")
    started = _ts("2026-05-04T18:23:12+00:00")
    completed = _ts("2026-05-04T18:23:13+00:00")
    job = JobRecord(
        id="abc-123",
        state=JobState.SUCCEEDED,
        submitted_at=submitted,
        started_at=started,
        completed_at=completed,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=_result(),
        error_code=None,
        error_detail=None,
    )
    d = job.to_dict()
    assert d["state"] == "succeeded"
    assert d["started_at"] == "2026-05-04T18:23:12+00:00"
    assert d["completed_at"] == "2026-05-04T18:23:13+00:00"
    assert d["result"]["redtusk_version"] == "0.1.0"
    assert JobRecord.from_dict(d) == job


def test_to_dict_round_trip_failed() -> None:
    job = JobRecord(
        id="abc-123",
        state=JobState.FAILED,
        submitted_at=_ts("2026-05-04T18:23:11+00:00"),
        started_at=_ts("2026-05-04T18:23:12+00:00"),
        completed_at=_ts("2026-05-04T18:23:13+00:00"),
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code="worker_crash",
        error_detail="container exited 139",
    )
    d = job.to_dict()
    assert d["state"] == "failed"
    assert d["error_code"] == "worker_crash"
    assert d["error_detail"] == "container exited 139"
    assert JobRecord.from_dict(d) == job


def test_is_terminal_via_state() -> None:
    """Convenience: job.state.is_terminal() is what callers actually use; sanity-check it from JobRecord."""
    submitted = _ts("2026-05-04T18:23:11+00:00")
    base = dict(
        id="x",
        submitted_at=submitted,
        started_at=None,
        completed_at=None,
        input_sha256="ae1c" + "0" * 60,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    assert not JobRecord(state=JobState.QUEUED, **base).state.is_terminal()
    assert not JobRecord(state=JobState.RUNNING, **base).state.is_terminal()
    assert JobRecord(state=JobState.SUCCEEDED, **base).state.is_terminal()
    assert JobRecord(state=JobState.FAILED, **base).state.is_terminal()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_types_job_record.py -v
```

Expected: FAIL with `ImportError: cannot import name 'JobRecord' from 'redtusk.types'`

- [ ] **Step 3: Append implementation to `src/redtusk/types.py`**

Append:

```python


@dataclass
class JobRecord:
    """Persisted record of a single extraction job.

    Mutable across its lifecycle: state transitions queued -> running ->
    succeeded|failed; timestamps are filled as the job moves; result is
    populated on success; error_code/error_detail are populated on failure.
    """

    id: str
    state: JobState
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_sha256: str
    input_size_bytes: int
    filename_hint: Optional[str]
    result: Optional[ExtractResult]
    error_code: Optional[str]
    error_detail: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state.value,
            "submitted_at": self.submitted_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_sha256": self.input_sha256,
            "input_size_bytes": self.input_size_bytes,
            "filename_hint": self.filename_hint,
            "result": self.result.to_dict() if self.result is not None else None,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> JobRecord:
        return cls(
            id=d["id"],
            state=JobState(d["state"]),
            submitted_at=datetime.fromisoformat(d["submitted_at"]),
            started_at=datetime.fromisoformat(d["started_at"]) if d.get("started_at") else None,
            completed_at=datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None,
            input_sha256=d["input_sha256"],
            input_size_bytes=d["input_size_bytes"],
            filename_hint=d.get("filename_hint"),
            result=ExtractResult.from_dict(d["result"]) if d.get("result") is not None else None,
            error_code=d.get("error_code"),
            error_detail=d.get("error_detail"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_types_job_record.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/types.py tests/unit/test_types_job_record.py
git commit -m "$(cat <<'EOF'
feat(types): add JobRecord

Mutable record persisted by the JobStore across a job's lifecycle.
Carries identity, state, all four lifecycle timestamps, input
fingerprint (sha256 + size + filename hint), the ExtractResult on
success, and structured error fields on failure. Round-trip
serialization to/from dict for all backends.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: JSON Schema for canonical rmeta

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/schema.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_schema_validation.py`

The dispatcher will validate every worker-produced rmeta document against this schema before trusting it. Built as a Python dict so it can be both validated (jsonschema) and introspected by tests.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the canonical rmeta JSON schema validator."""
from __future__ import annotations

import copy

import pytest

from redtusk.errors import SchemaValidationError
from redtusk.schema import RMETA_SCHEMA, validate_rmeta


def _good_rmeta() -> dict:
    return {
        "redtusk_version": "0.1.0",
        "tika_version": "3.0.0",
        "input": {
            "sha256": "ae" + "0" * 62,
            "size_bytes": 10,
            "filename_hint": "x.pdf",
            "submitted_at": "2026-05-04T18:23:11+00:00",
        },
        "extraction": {
            "root_content_type": "text/plain",
            "root_language": "en",
            "duration_ms": 10,
            "entries": [
                {
                    "path": "/",
                    "parent_path": None,
                    "depth": 0,
                    "content_type": "text/plain",
                    "size_bytes": 10,
                    "sha256": "ae" + "0" * 62,
                    "metadata": {},
                    "text": "hi",
                    "language": "en",
                    "qr": {"codes": [], "skipped": None},
                    "ocr": {
                        "text": "",
                        "language": None,
                        "duration_ms": 0,
                        "skipped": "no_images",
                    },
                    "error": None,
                }
            ],
        },
        "limits": {
            "max_recursion_depth": 10,
            "max_embedded_entries": 5000,
            "max_extracted_bytes": 524288000,
            "ocr_timeout_s": 60,
        },
        "truncated": None,
        "warnings": [],
        "sandbox": {
            "profile": "default",
            "runtime": "runsc",
            "appcds": True,
            "ksm": True,
            "crac": False,
        },
    }


def test_schema_is_dict() -> None:
    assert isinstance(RMETA_SCHEMA, dict)
    assert RMETA_SCHEMA["$schema"].startswith("http")
    assert RMETA_SCHEMA["type"] == "object"


def test_minimal_good_doc_passes() -> None:
    validate_rmeta(_good_rmeta())  # raises on failure


def test_truncated_object_passes() -> None:
    doc = _good_rmeta()
    doc["truncated"] = {
        "reason": "max_embedded_entries",
        "limit": 5000,
        "observed": 6234,
    }
    validate_rmeta(doc)


def test_warnings_populated_passes() -> None:
    doc = _good_rmeta()
    doc["warnings"] = [
        {"code": "ocr_scan_error", "detail": "tesseract crashed", "entry_path": "/embedded/img1.png"},
        {"code": "qr_scan_error", "detail": "zbar segfault", "entry_path": None},
    ]
    validate_rmeta(doc)


def test_missing_top_level_key_fails() -> None:
    doc = _good_rmeta()
    del doc["sandbox"]
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "sandbox" in str(ei.value)


def test_extra_top_level_key_fails() -> None:
    doc = _good_rmeta()
    doc["unexpected_field"] = "garbage"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "unexpected_field" in str(ei.value)


def test_invalid_state_in_truncation_reason_fails() -> None:
    doc = _good_rmeta()
    doc["truncated"] = {"reason": "garbage", "limit": 1, "observed": 2}
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_invalid_skipped_value_fails() -> None:
    doc = _good_rmeta()
    doc["extraction"]["entries"][0]["qr"]["skipped"] = "garbage"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_negative_size_bytes_fails() -> None:
    doc = _good_rmeta()
    doc["input"]["size_bytes"] = -1
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_sha256_must_be_64_hex() -> None:
    doc = _good_rmeta()
    doc["input"]["sha256"] = "tooshort"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_root_entry_must_have_path_slash() -> None:
    """The dispatcher relies on entries[0].path == '/'.

    The schema enforces it via const on the first entry's path.
    """
    doc = _good_rmeta()
    doc["extraction"]["entries"][0]["path"] = "/not-root"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "path" in str(ei.value)


def test_entries_must_not_be_empty() -> None:
    doc = _good_rmeta()
    doc["extraction"]["entries"] = []
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_qr_field_required_on_every_entry() -> None:
    doc = _good_rmeta()
    del doc["extraction"]["entries"][0]["qr"]
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_ocr_field_required_on_every_entry() -> None:
    doc = _good_rmeta()
    del doc["extraction"]["entries"][0]["ocr"]
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_invalid_profile_fails() -> None:
    doc = _good_rmeta()
    doc["sandbox"]["profile"] = "garbage"
    with pytest.raises(SchemaValidationError):
        validate_rmeta(doc)


def test_validation_error_includes_path() -> None:
    """SchemaValidationError.path should point at the offending field."""
    doc = _good_rmeta()
    doc["input"]["size_bytes"] = "not-a-number"
    with pytest.raises(SchemaValidationError) as ei:
        validate_rmeta(doc)
    assert "input" in ei.value.path
    assert "size_bytes" in ei.value.path
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_schema_validation.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.schema'`

- [ ] **Step 3: Write the implementation**

```python
"""JSON Schema for the canonical rmeta document.

The dispatcher validates every worker-produced metadata.json against
this schema before trusting the worker's output. The schema enforces
shape, types, and the small set of value vocabularies (skip reasons,
truncation reasons, profile names) that have closed enumerations.
"""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from redtusk.errors import SchemaValidationError

_SHA256_PATTERN = "^[a-f0-9]{64}$"
_SKIP_REASONS = ["no_images", "timeout_budget", "error", "disabled"]
_TRUNCATION_REASONS = ["max_embedded_entries", "max_recursion_depth", "max_extracted_bytes"]
_PROFILES = ["default", "high-density"]

_QR_CODE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["type", "data", "bbox"],
    "properties": {
        "type": {"type": "string"},
        "data": {"type": "string"},
        "bbox": {
            "type": "array",
            "items": {"type": "integer", "minimum": 0},
            "minItems": 4,
            "maxItems": 4,
        },
    },
}

_QR_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["codes", "skipped"],
    "properties": {
        "codes": {"type": "array", "items": _QR_CODE_SCHEMA},
        "skipped": {"type": ["string", "null"], "enum": [*_SKIP_REASONS, None]},
    },
}

_OCR_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text", "language", "duration_ms", "skipped"],
    "properties": {
        "text": {"type": "string"},
        "language": {"type": ["string", "null"]},
        "duration_ms": {"type": "integer", "minimum": 0},
        "skipped": {"type": ["string", "null"], "enum": [*_SKIP_REASONS, None]},
    },
}

_ENTRY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "path",
        "parent_path",
        "depth",
        "content_type",
        "size_bytes",
        "sha256",
        "metadata",
        "text",
        "language",
        "qr",
        "ocr",
        "error",
    ],
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "parent_path": {"type": ["string", "null"]},
        "depth": {"type": "integer", "minimum": 0},
        "content_type": {"type": "string", "minLength": 1},
        "size_bytes": {"type": "integer", "minimum": 0},
        "sha256": {"type": "string", "pattern": _SHA256_PATTERN},
        "metadata": {"type": "object"},
        "text": {"type": "string"},
        "language": {"type": ["string", "null"]},
        "qr": _QR_RESULT_SCHEMA,
        "ocr": _OCR_RESULT_SCHEMA,
        "error": {"type": ["string", "null"]},
    },
}

_ROOT_ENTRY_SCHEMA = {
    "allOf": [
        _ENTRY_SCHEMA,
        {
            "type": "object",
            "properties": {
                "path": {"const": "/"},
                "depth": {"const": 0},
                "parent_path": {"const": None},
            },
        },
    ]
}

RMETA_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "redtusk_version",
        "tika_version",
        "input",
        "extraction",
        "limits",
        "truncated",
        "warnings",
        "sandbox",
    ],
    "properties": {
        "redtusk_version": {"type": "string", "minLength": 1},
        "tika_version": {"type": "string", "minLength": 1},
        "input": {
            "type": "object",
            "additionalProperties": False,
            "required": ["sha256", "size_bytes", "filename_hint", "submitted_at"],
            "properties": {
                "sha256": {"type": "string", "pattern": _SHA256_PATTERN},
                "size_bytes": {"type": "integer", "minimum": 0},
                "filename_hint": {"type": ["string", "null"]},
                "submitted_at": {"type": "string", "format": "date-time"},
            },
        },
        "extraction": {
            "type": "object",
            "additionalProperties": False,
            "required": ["root_content_type", "root_language", "duration_ms", "entries"],
            "properties": {
                "root_content_type": {"type": "string", "minLength": 1},
                "root_language": {"type": ["string", "null"]},
                "duration_ms": {"type": "integer", "minimum": 0},
                "entries": {
                    "type": "array",
                    "minItems": 1,
                    "items": _ENTRY_SCHEMA,
                    "prefixItems": [_ROOT_ENTRY_SCHEMA],
                },
            },
        },
        "limits": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "max_recursion_depth",
                "max_embedded_entries",
                "max_extracted_bytes",
                "ocr_timeout_s",
            ],
            "properties": {
                "max_recursion_depth": {"type": "integer", "minimum": 0},
                "max_embedded_entries": {"type": "integer", "minimum": 0},
                "max_extracted_bytes": {"type": "integer", "minimum": 0},
                "ocr_timeout_s": {"type": "integer", "minimum": 0},
            },
        },
        "truncated": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reason", "limit", "observed"],
                    "properties": {
                        "reason": {"enum": _TRUNCATION_REASONS},
                        "limit": {"type": "integer", "minimum": 0},
                        "observed": {"type": "integer", "minimum": 0},
                    },
                },
            ]
        },
        "warnings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "detail", "entry_path"],
                "properties": {
                    "code": {"type": "string", "minLength": 1},
                    "detail": {"type": "string"},
                    "entry_path": {"type": ["string", "null"]},
                },
            },
        },
        "sandbox": {
            "type": "object",
            "additionalProperties": False,
            "required": ["profile", "runtime", "appcds", "ksm", "crac"],
            "properties": {
                "profile": {"enum": _PROFILES},
                "runtime": {"type": "string", "minLength": 1},
                "appcds": {"type": "boolean"},
                "ksm": {"type": "boolean"},
                "crac": {"type": "boolean"},
            },
        },
    },
}

_VALIDATOR = Draft202012Validator(RMETA_SCHEMA)


def validate_rmeta(doc: dict[str, Any]) -> None:
    """Validate ``doc`` against RMETA_SCHEMA.

    Raises ``SchemaValidationError`` (with a JSON-pointer-ish path) on any
    violation. The first error is reported; we intentionally don't aggregate
    every error since the dispatcher rejects on first failure anyway.
    """
    try:
        _VALIDATOR.validate(doc)
    except ValidationError as e:
        path = ".".join(str(p) for p in e.absolute_path) or "<root>"
        raise SchemaValidationError(path=path, reason=e.message) from e
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_schema_validation.py -v
```

Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/schema.py tests/unit/test_schema_validation.py
git commit -m "$(cat <<'EOF'
feat(schema): add JSON Schema validator for canonical rmeta

Draft 2020-12 schema covering top-level shape + every nested object.
Closed enumerations for skip reasons, truncation reasons, and
deployment profile name. Root entry constrained via prefixItems +
const so entries[0] must have path='/' depth=0 parent_path=null.
SHA-256 pattern-checked. validate_rmeta wraps jsonschema's
ValidationError in our SchemaValidationError so callers handle one
exception type and get a JSON-pointer-style path.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: JobStore Protocol

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/jobs/__init__.py`
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/jobs/base.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_jobs_protocol.py`

The Protocol defines the contract every backend implements. Tested by introspection — we verify the protocol has exactly the methods the implementations must implement, with the expected signatures.

- [ ] **Step 1: Write the failing test**

```python
"""Tests that the JobStore protocol has the expected method surface."""
from __future__ import annotations

import inspect
from typing import get_type_hints

from redtusk.jobs.base import JobStore


def test_job_store_has_expected_methods() -> None:
    """Pin the protocol's method names so backends can't drift silently."""
    expected = {
        "connect",
        "close",
        "create",
        "get",
        "update",
        "claim_next_queued",
        "list_recent",
        "delete",
        "delete_expired",
    }
    actual = {
        name
        for name, member in inspect.getmembers(JobStore)
        if not name.startswith("_") and callable(member)
    }
    assert expected.issubset(actual), f"missing methods: {expected - actual}"


def test_job_store_methods_are_async() -> None:
    """Every JobStore method must be async — backends use I/O."""
    for name in [
        "connect",
        "close",
        "create",
        "get",
        "update",
        "claim_next_queued",
        "list_recent",
        "delete",
        "delete_expired",
    ]:
        method = getattr(JobStore, name)
        assert inspect.iscoroutinefunction(method), f"{name} must be async"


def test_job_store_create_signature() -> None:
    sig = inspect.signature(JobStore.create)
    params = list(sig.parameters.values())
    # self + record
    assert len(params) == 2
    assert params[1].name == "record"


def test_job_store_get_signature() -> None:
    sig = inspect.signature(JobStore.get)
    params = list(sig.parameters.values())
    assert len(params) == 2
    assert params[1].name == "job_id"


def test_job_store_list_recent_signature() -> None:
    sig = inspect.signature(JobStore.list_recent)
    params = list(sig.parameters.values())
    assert len(params) == 2
    assert params[1].name == "limit"
    assert params[1].default == 50


def test_job_store_delete_expired_signature() -> None:
    sig = inspect.signature(JobStore.delete_expired)
    params = list(sig.parameters.values())
    # self + now + ttl_seconds
    assert len(params) == 3
    assert params[1].name == "now"
    assert params[2].name == "ttl_seconds"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_jobs_protocol.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.jobs'`

- [ ] **Step 3: Write `src/redtusk/jobs/__init__.py`**

```python
"""JobStore backends for RedTusk."""
from __future__ import annotations

from redtusk.jobs.base import JobStore

__all__ = ["JobStore"]
```

- [ ] **Step 4: Write `src/redtusk/jobs/base.py`**

```python
"""JobStore protocol — contract every backend implements."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

from redtusk.types import JobRecord


@runtime_checkable
class JobStore(Protocol):
    """Persists JobRecords across the lifecycle queued -> running -> succeeded|failed.

    Every method is async; even the in-memory backend uses an asyncio.Lock
    so the contract stays uniform.
    """

    async def connect(self) -> None:
        """Initialize the backend (open db, run migrations). Idempotent."""
        ...

    async def close(self) -> None:
        """Release backend resources. Idempotent."""
        ...

    async def create(self, record: JobRecord) -> None:
        """Persist a new record. Raises ``StorageError`` if the id already exists."""
        ...

    async def get(self, job_id: str) -> Optional[JobRecord]:
        """Fetch a record by id, or return None if no such job exists."""
        ...

    async def update(self, record: JobRecord) -> None:
        """Replace the record for ``record.id``. Raises ``JobNotFoundError`` if missing."""
        ...

    async def claim_next_queued(self) -> Optional[JobRecord]:
        """Atomically find the oldest QUEUED job, transition it to RUNNING, and return it.

        Returns None if no QUEUED jobs exist. The returned record reflects the
        post-transition state (state=RUNNING, started_at set to now).
        """
        ...

    async def list_recent(self, limit: int = 50) -> list[JobRecord]:
        """Return up to ``limit`` most-recently-submitted jobs, newest first."""
        ...

    async def delete(self, job_id: str) -> bool:
        """Safe-delete: removes the record only if state is terminal.

        Returns True if deleted, False if the record was non-terminal (caller
        should treat as 409). Raises ``JobNotFoundError`` if the id is unknown.
        """
        ...

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        """Delete every terminal job whose completed_at is older than ``now - ttl_seconds``.

        Returns the count of deleted records. Non-terminal jobs are never
        affected by retention.
        """
        ...
```

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_jobs_protocol.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/redtusk/jobs/__init__.py src/redtusk/jobs/base.py tests/unit/test_jobs_protocol.py
git commit -m "$(cat <<'EOF'
feat(jobs): add JobStore protocol

Contract every backend implements: connect/close, CRUD, atomic
claim_next_queued for the dispatcher, list_recent for the UI,
safe-delete that returns False for non-terminal jobs (caller maps to
409), and delete_expired for the retention sweeper. Every method is
async so all backends present a uniform interface.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: MemoryJobStore

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/jobs/memory.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_jobs_memory.py`

In-process dict-backed JobStore. Used in unit tests, single-node dev runs, and as the simplest reference implementation against which the SQL backends can be validated.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for MemoryJobStore."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.memory import MemoryJobStore
from redtusk.types import JobRecord, JobState


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState = JobState.QUEUED, **overrides) -> JobRecord:
    base = dict(
        id=job_id,
        state=state,
        submitted_at=_now(),
        started_at=None,
        completed_at=None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    base.update(overrides)
    return JobRecord(**base)


@pytest.fixture
async def store() -> MemoryJobStore:
    s = MemoryJobStore()
    await s.connect()
    yield s
    await s.close()


async def test_create_and_get(store: MemoryJobStore) -> None:
    r = _record("a")
    await store.create(r)
    fetched = await store.get("a")
    assert fetched == r


async def test_get_unknown_returns_none(store: MemoryJobStore) -> None:
    assert await store.get("does-not-exist") is None


async def test_create_duplicate_raises(store: MemoryJobStore) -> None:
    r = _record("a")
    await store.create(r)
    with pytest.raises(StorageError):
        await store.create(r)


async def test_update_replaces(store: MemoryJobStore) -> None:
    r = _record("a", state=JobState.QUEUED)
    await store.create(r)
    updated = _record("a", state=JobState.RUNNING, started_at=_now(1))
    await store.update(updated)
    assert (await store.get("a")) == updated


async def test_update_unknown_raises(store: MemoryJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.update(_record("nope"))


async def test_claim_next_queued_returns_oldest(store: MemoryJobStore) -> None:
    a = _record("a", submitted_at=_now(0))
    b = _record("b", submitted_at=_now(1))
    c = _record("c", submitted_at=_now(2))
    # Insert out of order to make sure ordering is by submitted_at, not insert order.
    await store.create(c)
    await store.create(a)
    await store.create(b)

    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING
    assert claimed.started_at is not None


async def test_claim_next_queued_skips_non_queued(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    await store.create(_record("b", state=JobState.SUCCEEDED))
    await store.create(_record("c", state=JobState.QUEUED))
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "c"


async def test_claim_next_queued_returns_none_when_empty(store: MemoryJobStore) -> None:
    assert await store.claim_next_queued() is None


async def test_claim_next_queued_persists_state_change(store: MemoryJobStore) -> None:
    await store.create(_record("a"))
    await store.claim_next_queued()
    fetched = await store.get("a")
    assert fetched is not None
    assert fetched.state == JobState.RUNNING


async def test_list_recent_returns_newest_first(store: MemoryJobStore) -> None:
    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent(limit=3)
    assert [r.id for r in recent] == ["job-4", "job-3", "job-2"]


async def test_list_recent_default_limit(store: MemoryJobStore) -> None:
    for i in range(60):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent()
    assert len(recent) == 50


async def test_delete_terminal_returns_true(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.SUCCEEDED, completed_at=_now(1)))
    assert (await store.delete("a")) is True
    assert (await store.get("a")) is None


async def test_delete_non_terminal_returns_false(store: MemoryJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False
    assert (await store.get("a")) is not None  # still there


async def test_delete_unknown_raises(store: MemoryJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: MemoryJobStore) -> None:
    # 1h ago, succeeded, eligible
    await store.create(
        _record(
            "old-success",
            state=JobState.SUCCEEDED,
            completed_at=_now(-3600),
        )
    )
    # 1h ago, failed, eligible
    await store.create(
        _record(
            "old-failed",
            state=JobState.FAILED,
            completed_at=_now(-3600),
        )
    )
    # 1h ago, still queued (no completed_at), NOT eligible
    await store.create(_record("old-queued", state=JobState.QUEUED, submitted_at=_now(-3600)))
    # 1h ago, still running (no completed_at), NOT eligible
    await store.create(
        _record("old-running", state=JobState.RUNNING, started_at=_now(-3600))
    )
    # 1m ago, succeeded, NOT eligible (too recent)
    await store.create(
        _record(
            "recent-success",
            state=JobState.SUCCEEDED,
            completed_at=_now(-60),
        )
    )

    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 2
    assert (await store.get("old-success")) is None
    assert (await store.get("old-failed")) is None
    assert (await store.get("old-queued")) is not None
    assert (await store.get("old-running")) is not None
    assert (await store.get("recent-success")) is not None


async def test_implements_protocol() -> None:
    """MemoryJobStore must satisfy isinstance check against JobStore protocol."""
    from redtusk.jobs.base import JobStore

    s = MemoryJobStore()
    assert isinstance(s, JobStore)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_jobs_memory.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.jobs.memory'`

- [ ] **Step 3: Write the implementation**

```python
"""In-process JobStore backend.

Used for unit tests, single-process dev runs, and as a reference
implementation. Asyncio-safe via a single Lock since it backs every
method onto plain dict operations.
"""
from __future__ import annotations

import asyncio
import copy
from datetime import datetime, timedelta
from typing import Optional

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.types import JobRecord, JobState


class MemoryJobStore:
    """In-memory JobStore. All state lives in a process-local dict."""

    def __init__(self) -> None:
        self._records: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def create(self, record: JobRecord) -> None:
        async with self._lock:
            if record.id in self._records:
                raise StorageError(f"job already exists: {record.id}")
            self._records[record.id] = copy.deepcopy(record)

    async def get(self, job_id: str) -> Optional[JobRecord]:
        async with self._lock:
            r = self._records.get(job_id)
            return copy.deepcopy(r) if r is not None else None

    async def update(self, record: JobRecord) -> None:
        async with self._lock:
            if record.id not in self._records:
                raise JobNotFoundError(record.id)
            self._records[record.id] = copy.deepcopy(record)

    async def claim_next_queued(self) -> Optional[JobRecord]:
        async with self._lock:
            queued = [r for r in self._records.values() if r.state == JobState.QUEUED]
            if not queued:
                return None
            queued.sort(key=lambda r: r.submitted_at)
            chosen = queued[0]
            now = _utcnow()
            updated = JobRecord(
                id=chosen.id,
                state=JobState.RUNNING,
                submitted_at=chosen.submitted_at,
                started_at=now,
                completed_at=chosen.completed_at,
                input_sha256=chosen.input_sha256,
                input_size_bytes=chosen.input_size_bytes,
                filename_hint=chosen.filename_hint,
                result=chosen.result,
                error_code=chosen.error_code,
                error_detail=chosen.error_detail,
            )
            self._records[chosen.id] = updated
            return copy.deepcopy(updated)

    async def list_recent(self, limit: int = 50) -> list[JobRecord]:
        async with self._lock:
            ordered = sorted(
                self._records.values(), key=lambda r: r.submitted_at, reverse=True
            )
            return [copy.deepcopy(r) for r in ordered[:limit]]

    async def delete(self, job_id: str) -> bool:
        async with self._lock:
            r = self._records.get(job_id)
            if r is None:
                raise JobNotFoundError(job_id)
            if not r.state.is_terminal():
                return False
            del self._records[job_id]
            return True

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        cutoff = now - timedelta(seconds=ttl_seconds)
        async with self._lock:
            doomed = [
                r.id
                for r in self._records.values()
                if r.state.is_terminal()
                and r.completed_at is not None
                and r.completed_at < cutoff
            ]
            for job_id in doomed:
                del self._records[job_id]
            return len(doomed)


def _utcnow() -> datetime:
    """Indirection so tests can monkeypatch if needed; production uses real UTC."""
    from datetime import timezone

    return datetime.now(tz=timezone.utc)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_jobs_memory.py -v
```

Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/jobs/memory.py tests/unit/test_jobs_memory.py
git commit -m "$(cat <<'EOF'
feat(jobs): add MemoryJobStore backend

Asyncio-safe dict-backed JobStore. Every read/write goes through a
single Lock and returns deep copies so callers can't mutate stored
state. Implements the full protocol: claim_next_queued sorts by
submitted_at to enforce FIFO; safe-delete returns False for
non-terminal jobs; delete_expired only touches terminal records with
a populated completed_at.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: SqlJobStore (sqlite + postgres)

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/jobs/sql_store.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_jobs_sql_sqlite.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_jobs_sql_postgres.py`

A single class handles both backends, switching between aiosqlite and psycopg based on the URL scheme. The schema is one `jobs` table with the record JSON-blob in a single `payload` column plus indexed columns for the queries that have to be fast (`state`, `submitted_at`, `completed_at`).

The sqlite test runs in-process against a temp file. The postgres test is gated by the `postgres` pytest marker; it requires `REDTUSK_TEST_POSTGRES_URL` set in the environment and is skipped otherwise.

- [ ] **Step 1: Write the sqlite test**

```python
"""Tests for SqlJobStore against a sqlite backend."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.sql_store import SqlJobStore
from redtusk.types import JobRecord, JobState


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState = JobState.QUEUED, **overrides) -> JobRecord:
    base = dict(
        id=job_id,
        state=state,
        submitted_at=_now(),
        started_at=None,
        completed_at=None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    base.update(overrides)
    return JobRecord(**base)


@pytest.fixture
async def store(tmp_path) -> SqlJobStore:
    db_path = tmp_path / "test.db"
    s = SqlJobStore(f"sqlite:///{db_path}")
    await s.connect()
    yield s
    await s.close()


async def test_connect_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    s = SqlJobStore(f"sqlite:///{db_path}")
    await s.connect()
    # If we can create + get without error, the schema exists.
    await s.create(_record("a"))
    assert (await s.get("a")) is not None
    await s.close()


async def test_create_and_get(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    fetched = await store.get("a")
    assert fetched == r


async def test_get_unknown_returns_none(store: SqlJobStore) -> None:
    assert await store.get("does-not-exist") is None


async def test_create_duplicate_raises(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    with pytest.raises(StorageError):
        await store.create(r)


async def test_update_replaces(store: SqlJobStore) -> None:
    r = _record("a", state=JobState.QUEUED)
    await store.create(r)
    updated = _record("a", state=JobState.RUNNING, started_at=_now(1))
    await store.update(updated)
    assert (await store.get("a")) == updated


async def test_update_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.update(_record("nope"))


async def test_claim_next_queued_returns_oldest(store: SqlJobStore) -> None:
    a = _record("a", submitted_at=_now(0))
    b = _record("b", submitted_at=_now(1))
    c = _record("c", submitted_at=_now(2))
    await store.create(c)
    await store.create(a)
    await store.create(b)
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING
    assert claimed.started_at is not None


async def test_claim_next_queued_returns_none_when_empty(store: SqlJobStore) -> None:
    assert await store.claim_next_queued() is None


async def test_list_recent_newest_first(store: SqlJobStore) -> None:
    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    recent = await store.list_recent(limit=3)
    assert [r.id for r in recent] == ["job-4", "job-3", "job-2"]


async def test_delete_terminal_returns_true(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.SUCCEEDED, completed_at=_now(1)))
    assert (await store.delete("a")) is True
    assert (await store.get("a")) is None


async def test_delete_non_terminal_returns_false(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False
    assert (await store.get("a")) is not None


async def test_delete_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: SqlJobStore) -> None:
    await store.create(
        _record("old-success", state=JobState.SUCCEEDED, completed_at=_now(-3600))
    )
    await store.create(
        _record("old-failed", state=JobState.FAILED, completed_at=_now(-3600))
    )
    await store.create(_record("old-queued", state=JobState.QUEUED, submitted_at=_now(-3600)))
    await store.create(_record("old-running", state=JobState.RUNNING, started_at=_now(-3600)))
    await store.create(
        _record("recent-success", state=JobState.SUCCEEDED, completed_at=_now(-60))
    )
    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 2
    assert (await store.get("old-success")) is None
    assert (await store.get("old-failed")) is None
    assert (await store.get("old-queued")) is not None
    assert (await store.get("old-running")) is not None
    assert (await store.get("recent-success")) is not None


async def test_implements_protocol(tmp_path) -> None:
    from redtusk.jobs.base import JobStore

    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    assert isinstance(s, JobStore)


async def test_close_is_idempotent(tmp_path) -> None:
    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    await s.connect()
    await s.close()
    await s.close()  # second call must not raise


async def test_connect_is_idempotent(tmp_path) -> None:
    s = SqlJobStore(f"sqlite:///{tmp_path / 'x.db'}")
    await s.connect()
    await s.connect()  # second call must not raise
    await s.create(_record("a"))
    assert (await s.get("a")) is not None
    await s.close()
```

- [ ] **Step 2: Write the postgres test (parallel structure, gated by marker)**

```python
"""Tests for SqlJobStore against a real postgres backend.

Skipped unless REDTUSK_TEST_POSTGRES_URL is set in the environment.
Each test uses a fresh schema (set_test_schema fixture) so they don't
collide if run in parallel.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.jobs.sql_store import SqlJobStore
from redtusk.types import JobRecord, JobState

pytestmark = pytest.mark.postgres

_TEST_URL = os.environ.get("REDTUSK_TEST_POSTGRES_URL")


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState = JobState.QUEUED, **overrides) -> JobRecord:
    base = dict(
        id=job_id,
        state=state,
        submitted_at=_now(),
        started_at=None,
        completed_at=None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )
    base.update(overrides)
    return JobRecord(**base)


@pytest.fixture
async def store():
    if not _TEST_URL:
        pytest.skip("REDTUSK_TEST_POSTGRES_URL not set")
    schema = f"redtusk_test_{uuid.uuid4().hex[:8]}"
    s = SqlJobStore(_TEST_URL, schema=schema)
    await s.connect()
    yield s
    await s.drop_schema()
    await s.close()


async def test_create_and_get(store: SqlJobStore) -> None:
    r = _record("a")
    await store.create(r)
    assert (await store.get("a")) == r


async def test_create_duplicate_raises(store: SqlJobStore) -> None:
    await store.create(_record("a"))
    with pytest.raises(StorageError):
        await store.create(_record("a"))


async def test_claim_next_queued_returns_oldest(store: SqlJobStore) -> None:
    await store.create(_record("c", submitted_at=_now(2)))
    await store.create(_record("a", submitted_at=_now(0)))
    await store.create(_record("b", submitted_at=_now(1)))
    claimed = await store.claim_next_queued()
    assert claimed is not None
    assert claimed.id == "a"
    assert claimed.state == JobState.RUNNING


async def test_claim_next_queued_is_atomic_under_concurrency(store: SqlJobStore) -> None:
    """Two concurrent claims against the same QUEUED set must each get a different job."""
    import asyncio

    for i in range(5):
        await store.create(_record(f"job-{i}", submitted_at=_now(i)))
    results = await asyncio.gather(*[store.claim_next_queued() for _ in range(5)])
    ids = [r.id for r in results if r is not None]
    assert len(ids) == 5
    assert len(set(ids)) == 5  # all distinct, none claimed twice


async def test_delete_non_terminal_returns_false(store: SqlJobStore) -> None:
    await store.create(_record("a", state=JobState.RUNNING))
    assert (await store.delete("a")) is False


async def test_delete_unknown_raises(store: SqlJobStore) -> None:
    with pytest.raises(JobNotFoundError):
        await store.delete("nope")


async def test_delete_expired_only_terminal(store: SqlJobStore) -> None:
    await store.create(
        _record("old-success", state=JobState.SUCCEEDED, completed_at=_now(-3600))
    )
    await store.create(_record("old-running", state=JobState.RUNNING, started_at=_now(-3600)))
    deleted = await store.delete_expired(now=_now(0), ttl_seconds=600)
    assert deleted == 1
    assert (await store.get("old-success")) is None
    assert (await store.get("old-running")) is not None
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/unit/test_jobs_sql_sqlite.py tests/unit/test_jobs_sql_postgres.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.jobs.sql_store'`

- [ ] **Step 4: Write the implementation**

```python
"""SQL-backed JobStore.

A single class handles both sqlite (via aiosqlite) and postgres (via psycopg
async). The URL scheme determines the dialect; the schema is one ``jobs``
table with a JSON ``payload`` column plus indexed columns for the queries
that have to be fast (state, submitted_at, completed_at).

The atomic ``claim_next_queued`` uses ``SELECT ... FOR UPDATE SKIP LOCKED``
on postgres for safe concurrent claims; sqlite is single-writer so an
``IMMEDIATE`` transaction is sufficient.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from redtusk.errors import JobNotFoundError, StorageError
from redtusk.types import JobRecord, JobState

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    completed_at TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_state_submitted_idx
    ON jobs(state, submitted_at);
CREATE INDEX IF NOT EXISTS jobs_completed_at_idx
    ON jobs(completed_at);
"""

_SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS {schema}.jobs (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_state_submitted_idx
    ON {schema}.jobs(state, submitted_at);
CREATE INDEX IF NOT EXISTS jobs_completed_at_idx
    ON {schema}.jobs(completed_at);
"""


class SqlJobStore:
    """JobStore backed by sqlite or postgres.

    Pass a URL like ``sqlite:///./jobs.db`` or
    ``postgresql://user:pass@host/db`` to the constructor. The ``schema``
    argument is postgres-only and lets tests isolate themselves.
    """

    def __init__(self, url: str, *, schema: str = "public") -> None:
        self._url = url
        self._schema = schema
        self._connected = False
        self._lock = asyncio.Lock()
        if url.startswith("sqlite:///"):
            self._dialect = "sqlite"
            self._sqlite_path = url.removeprefix("sqlite:///")
            self._aiosqlite_conn = None
        elif url.startswith(("postgresql://", "postgres://")):
            self._dialect = "postgres"
            self._psycopg_pool = None
        else:
            raise StorageError(f"unsupported database URL scheme: {url!r}")

    async def connect(self) -> None:
        async with self._lock:
            if self._connected:
                return
            if self._dialect == "sqlite":
                import aiosqlite

                self._aiosqlite_conn = await aiosqlite.connect(self._sqlite_path)
                await self._aiosqlite_conn.executescript(_SCHEMA_SQLITE)
                await self._aiosqlite_conn.commit()
            else:
                from psycopg_pool import AsyncConnectionPool

                self._psycopg_pool = AsyncConnectionPool(
                    self._url, min_size=1, max_size=10, open=False
                )
                await self._psycopg_pool.open()
                async with self._psycopg_pool.connection() as conn:
                    if self._schema != "public":
                        await conn.execute(
                            f'CREATE SCHEMA IF NOT EXISTS "{self._schema}"'
                        )
                    await conn.execute(
                        _SCHEMA_POSTGRES.format(schema=f'"{self._schema}"')
                    )
                    await conn.commit()
            self._connected = True

    async def close(self) -> None:
        async with self._lock:
            if not self._connected:
                return
            if self._dialect == "sqlite" and self._aiosqlite_conn is not None:
                await self._aiosqlite_conn.close()
                self._aiosqlite_conn = None
            elif self._dialect == "postgres" and self._psycopg_pool is not None:
                await self._psycopg_pool.close()
                self._psycopg_pool = None
            self._connected = False

    async def drop_schema(self) -> None:
        """Postgres-only test helper: drop the schema this store created."""
        if self._dialect != "postgres":
            return
        async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
            await conn.execute(f'DROP SCHEMA IF EXISTS "{self._schema}" CASCADE')
            await conn.commit()

    async def create(self, record: JobRecord) -> None:
        payload = json.dumps(record.to_dict())
        if self._dialect == "sqlite":
            try:
                await self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                    "INSERT INTO jobs(id, state, submitted_at, completed_at, payload) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        record.id,
                        record.state.value,
                        record.submitted_at.isoformat(),
                        record.completed_at.isoformat() if record.completed_at else None,
                        payload,
                    ),
                )
                await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise StorageError(f"job already exists: {record.id}") from e
                raise StorageError(str(e)) from e
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                try:
                    await conn.execute(
                        f'INSERT INTO "{self._schema}".jobs'
                        "(id, state, submitted_at, completed_at, payload) "
                        "VALUES (%s, %s, %s, %s, %s::jsonb)",
                        (
                            record.id,
                            record.state.value,
                            record.submitted_at,
                            record.completed_at,
                            payload,
                        ),
                    )
                    await conn.commit()
                except Exception as e:
                    if "duplicate key" in str(e):
                        raise StorageError(f"job already exists: {record.id}") from e
                    raise StorageError(str(e)) from e

    async def get(self, job_id: str) -> Optional[JobRecord]:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "SELECT payload FROM jobs WHERE id = ?", (job_id,)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs WHERE id = %s',
                        (job_id,),
                    )
                    row = await cur.fetchone()
        if row is None:
            return None
        payload = row[0] if isinstance(row[0], str) else json.dumps(row[0])
        return JobRecord.from_dict(json.loads(payload))

    async def update(self, record: JobRecord) -> None:
        payload = json.dumps(record.to_dict())
        if self._dialect == "sqlite":
            cur = await self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "UPDATE jobs SET state=?, submitted_at=?, completed_at=?, payload=? "
                "WHERE id=?",
                (
                    record.state.value,
                    record.submitted_at.isoformat(),
                    record.completed_at.isoformat() if record.completed_at else None,
                    payload,
                    record.id,
                ),
            )
            if cur.rowcount == 0:
                raise JobNotFoundError(record.id)
            await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'UPDATE "{self._schema}".jobs '
                        "SET state=%s, submitted_at=%s, completed_at=%s, payload=%s::jsonb "
                        "WHERE id=%s",
                        (
                            record.state.value,
                            record.submitted_at,
                            record.completed_at,
                            payload,
                            record.id,
                        ),
                    )
                    if cur.rowcount == 0:
                        raise JobNotFoundError(record.id)
                await conn.commit()

    async def claim_next_queued(self) -> Optional[JobRecord]:
        now = datetime.now(tz=timezone.utc)
        if self._dialect == "sqlite":
            async with self._lock:
                await self._aiosqlite_conn.execute("BEGIN IMMEDIATE")  # type: ignore[union-attr]
                async with self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                    "SELECT id, payload FROM jobs WHERE state = ? "
                    "ORDER BY submitted_at ASC LIMIT 1",
                    (JobState.QUEUED.value,),
                ) as cur:
                    row = await cur.fetchone()
                if row is None:
                    await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
                    return None
                job_id, payload = row[0], row[1]
                record = JobRecord.from_dict(json.loads(payload))
                updated = JobRecord(
                    id=record.id,
                    state=JobState.RUNNING,
                    submitted_at=record.submitted_at,
                    started_at=now,
                    completed_at=record.completed_at,
                    input_sha256=record.input_sha256,
                    input_size_bytes=record.input_size_bytes,
                    filename_hint=record.filename_hint,
                    result=record.result,
                    error_code=record.error_code,
                    error_detail=record.error_detail,
                )
                await self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                    "UPDATE jobs SET state=?, payload=? WHERE id=?",
                    (JobState.RUNNING.value, json.dumps(updated.to_dict()), job_id),
                )
                await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
                return updated
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT id, payload FROM "{self._schema}".jobs '
                        "WHERE state = %s ORDER BY submitted_at ASC LIMIT 1 "
                        "FOR UPDATE SKIP LOCKED",
                        (JobState.QUEUED.value,),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        await conn.commit()
                        return None
                    job_id = row[0]
                    payload = row[1] if isinstance(row[1], str) else json.dumps(row[1])
                    record = JobRecord.from_dict(json.loads(payload))
                    updated = JobRecord(
                        id=record.id,
                        state=JobState.RUNNING,
                        submitted_at=record.submitted_at,
                        started_at=now,
                        completed_at=record.completed_at,
                        input_sha256=record.input_sha256,
                        input_size_bytes=record.input_size_bytes,
                        filename_hint=record.filename_hint,
                        result=record.result,
                        error_code=record.error_code,
                        error_detail=record.error_detail,
                    )
                    await cur.execute(
                        f'UPDATE "{self._schema}".jobs '
                        "SET state=%s, payload=%s::jsonb WHERE id=%s",
                        (JobState.RUNNING.value, json.dumps(updated.to_dict()), job_id),
                    )
                await conn.commit()
                return updated

    async def list_recent(self, limit: int = 50) -> list[JobRecord]:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "SELECT payload FROM jobs ORDER BY submitted_at DESC LIMIT ?",
                (limit,),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT payload FROM "{self._schema}".jobs '
                        "ORDER BY submitted_at DESC LIMIT %s",
                        (limit,),
                    )
                    rows = await cur.fetchall()
        out: list[JobRecord] = []
        for row in rows:
            payload = row[0] if isinstance(row[0], str) else json.dumps(row[0])
            out.append(JobRecord.from_dict(json.loads(payload)))
        return out

    async def delete(self, job_id: str) -> bool:
        if self._dialect == "sqlite":
            async with self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "SELECT state FROM jobs WHERE id = ?", (job_id,)
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            state = JobState(row[0])
            if not state.is_terminal():
                return False
            await self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "DELETE FROM jobs WHERE id = ?", (job_id,)
            )
            await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
            return True
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'SELECT state FROM "{self._schema}".jobs WHERE id = %s',
                        (job_id,),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise JobNotFoundError(job_id)
                    state = JobState(row[0])
                    if not state.is_terminal():
                        return False
                    await cur.execute(
                        f'DELETE FROM "{self._schema}".jobs WHERE id = %s', (job_id,)
                    )
                await conn.commit()
                return True

    async def delete_expired(self, now: datetime, ttl_seconds: int) -> int:
        cutoff = now - timedelta(seconds=ttl_seconds)
        terminal_states = (JobState.SUCCEEDED.value, JobState.FAILED.value)
        if self._dialect == "sqlite":
            cur = await self._aiosqlite_conn.execute(  # type: ignore[union-attr]
                "DELETE FROM jobs WHERE state IN (?, ?) "
                "AND completed_at IS NOT NULL AND completed_at < ?",
                (terminal_states[0], terminal_states[1], cutoff.isoformat()),
            )
            await self._aiosqlite_conn.commit()  # type: ignore[union-attr]
            return cur.rowcount or 0
        else:
            async with self._psycopg_pool.connection() as conn:  # type: ignore[union-attr]
                async with conn.cursor() as cur:
                    await cur.execute(
                        f'DELETE FROM "{self._schema}".jobs '
                        "WHERE state = ANY(%s) AND completed_at IS NOT NULL "
                        "AND completed_at < %s",
                        (list(terminal_states), cutoff),
                    )
                    deleted = cur.rowcount or 0
                await conn.commit()
                return deleted
```

- [ ] **Step 5: Run tests — sqlite path should pass, postgres should skip**

```bash
.venv/bin/pytest tests/unit/test_jobs_sql_sqlite.py tests/unit/test_jobs_sql_postgres.py -v
```

Expected:
- sqlite: 17 passed
- postgres: 7 skipped (because `REDTUSK_TEST_POSTGRES_URL` is not set)

- [ ] **Step 6 (optional, only run if you have postgres handy): verify postgres path**

```bash
# Spin up postgres if needed:
docker run -d --name redtusk-test-pg -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:16
sleep 3
export REDTUSK_TEST_POSTGRES_URL="postgresql://postgres:test@localhost:55432/postgres"
.venv/bin/pytest tests/unit/test_jobs_sql_postgres.py -v
docker rm -f redtusk-test-pg
unset REDTUSK_TEST_POSTGRES_URL
```

Expected: 7 passed.

- [ ] **Step 7: Commit**

```bash
git add src/redtusk/jobs/sql_store.py tests/unit/test_jobs_sql_sqlite.py tests/unit/test_jobs_sql_postgres.py
git commit -m "$(cat <<'EOF'
feat(jobs): add SqlJobStore (sqlite + postgres)

Single class dispatches on URL scheme: aiosqlite for sqlite,
psycopg async pool for postgres. Schema is one jobs table with the
record JSON-encoded in a payload column plus indexed columns for the
hot queries (state, submitted_at, completed_at).

claim_next_queued uses BEGIN IMMEDIATE on sqlite and
SELECT ... FOR UPDATE SKIP LOCKED on postgres so concurrent
dispatchers each receive a distinct job. Postgres path adds a
drop_schema test helper so each integration test gets an isolated
schema.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Retention sweeper

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/jobs/retention.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_retention.py`

The sweeper is an async task that periodically calls `store.delete_expired()`. Designed to start, run, and stop cleanly so the dispatcher can manage it as part of its lifecycle.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the RetentionSweeper background task."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from redtusk.jobs.memory import MemoryJobStore
from redtusk.jobs.retention import RetentionSweeper
from redtusk.types import JobRecord, JobState


def _now(offset_s: int = 0) -> datetime:
    return datetime(2026, 5, 4, 18, 23, 11, tzinfo=timezone.utc) + timedelta(seconds=offset_s)


def _record(job_id: str, state: JobState, completed_offset_s: int) -> JobRecord:
    return JobRecord(
        id=job_id,
        state=state,
        submitted_at=_now(-completed_offset_s),
        started_at=_now(-completed_offset_s),
        completed_at=_now(-completed_offset_s) if state.is_terminal() else None,
        input_sha256="ae" + "0" * 62,
        input_size_bytes=10,
        filename_hint=None,
        result=None,
        error_code=None,
        error_detail=None,
    )


async def test_sweeper_runs_one_pass_and_deletes() -> None:
    store = MemoryJobStore()
    await store.connect()
    await store.create(_record("old", JobState.SUCCEEDED, completed_offset_s=3600))
    await store.create(_record("recent", JobState.SUCCEEDED, completed_offset_s=10))

    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=0.05,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    await asyncio.sleep(0.15)  # let it run several iterations
    await sweeper.stop()
    await store.close()

    assert await store.get("old") is None
    assert await store.get("recent") is not None


async def test_sweeper_stop_is_idempotent() -> None:
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=10,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    await sweeper.stop()
    await sweeper.stop()  # second call must not raise


async def test_sweeper_start_twice_raises() -> None:
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=10,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    with pytest.raises(RuntimeError):
        await sweeper.start()
    await sweeper.stop()


async def test_sweeper_stops_promptly() -> None:
    """Even with a long interval, stop() should return within a small fraction of it."""
    store = MemoryJobStore()
    await store.connect()
    sweeper = RetentionSweeper(
        store=store,
        ttl_seconds=600,
        interval_seconds=300,
        clock=lambda: _now(0),
    )
    await sweeper.start()
    start = asyncio.get_event_loop().time()
    await sweeper.stop()
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed < 1.0, f"stop() took {elapsed:.2f}s, expected < 1s"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_retention.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'redtusk.jobs.retention'`

- [ ] **Step 3: Write the implementation**

```python
"""Periodic JobStore retention sweeper.

A long-running asyncio task that wakes every ``interval_seconds``,
calls ``store.delete_expired(now, ttl_seconds)``, and logs the count.
``start()`` / ``stop()`` give the dispatcher tight lifecycle control.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Callable, Optional

from redtusk.jobs.base import JobStore


class RetentionSweeper:
    """Background task that periodically deletes expired terminal jobs."""

    def __init__(
        self,
        *,
        store: JobStore,
        ttl_seconds: int,
        interval_seconds: float = 60.0,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self._store = store
        self._ttl_seconds = ttl_seconds
        self._interval_seconds = interval_seconds
        self._clock = clock or (lambda: datetime.now(tz=timezone.utc))
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("RetentionSweeper already started")
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="redtusk-retention-sweeper")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            self._task.cancel()
        self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._store.delete_expired(
                    now=self._clock(), ttl_seconds=self._ttl_seconds
                )
            except Exception:
                # Don't let sweeper failures kill the task; observability layer
                # will surface this once metrics are wired in.
                pass
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._interval_seconds
                )
            except asyncio.TimeoutError:
                continue
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_retention.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/redtusk/jobs/retention.py tests/unit/test_retention.py
git commit -m "$(cat <<'EOF'
feat(jobs): add RetentionSweeper background task

Wakes every interval_seconds, calls store.delete_expired with a
configurable clock for deterministic tests. Uses an Event-driven
sleep so stop() returns promptly even with a 5-minute interval.
Sweeper failures are swallowed so transient store errors don't kill
the long-running task; once metrics land they'll surface via the
errors counter.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Observability — logging

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/observability/__init__.py`
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/observability/logging.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_observability_logging.py`

structlog with JSON output to stdout. `configure_logging(level)` is called once at process startup; `get_logger(name)` returns a structlog logger callers use for the rest of the process's life.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the structlog-based logging configuration."""
from __future__ import annotations

import io
import json
import logging

import pytest
import structlog

from redtusk.observability.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def reset_structlog():
    """Each test starts from a clean structlog config."""
    structlog.reset_defaults()
    # Restore root logger handlers so other tests aren't affected.
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    yield
    structlog.reset_defaults()
    root.handlers = saved_handlers
    root.level = saved_level


def test_configure_logging_writes_json_to_stream() -> None:
    stream = io.StringIO()
    configure_logging(level="INFO", stream=stream)
    log = get_logger("test")
    log.info("hello", foo="bar", n=42)
    line = stream.getvalue().strip()
    assert line, "logger should have written something"
    record = json.loads(line)
    assert record["event"] == "hello"
    assert record["foo"] == "bar"
    assert record["n"] == 42
    assert record["logger"] == "test"
    assert record["level"] == "info"
    assert "timestamp" in record


def test_log_level_filters_below_threshold() -> None:
    stream = io.StringIO()
    configure_logging(level="WARNING", stream=stream)
    log = get_logger("test")
    log.info("should-not-appear")
    log.warning("should-appear")
    output = stream.getvalue()
    assert "should-not-appear" not in output
    assert "should-appear" in output


def test_get_logger_includes_name() -> None:
    stream = io.StringIO()
    configure_logging(level="DEBUG", stream=stream)
    log = get_logger("redtusk.test.something")
    log.info("x")
    record = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert record["logger"] == "redtusk.test.something"


def test_bind_carries_context() -> None:
    stream = io.StringIO()
    configure_logging(level="INFO", stream=stream)
    log = get_logger("test").bind(job_id="abc-123")
    log.info("processing")
    record = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert record["job_id"] == "abc-123"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_observability_logging.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/redtusk/observability/__init__.py`**

```python
"""Observability scaffolding: structured logging + Prometheus metrics."""
from __future__ import annotations

from redtusk.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
```

- [ ] **Step 4: Write `src/redtusk/observability/logging.py`**

```python
"""structlog setup for RedTusk.

Configures structlog to emit JSON one event per line to stdout (or any stream
the test passes in). Standard-library ``logging`` is also routed through the
same processor chain so dependencies that use stdlib logging show up in the
same stream.
"""
from __future__ import annotations

import logging
import sys
from typing import IO, Any, Optional

import structlog


def configure_logging(level: str = "INFO", stream: Optional[IO[str]] = None) -> None:
    """Configure structlog + stdlib logging to emit JSON.

    ``level`` is a logging level name (DEBUG/INFO/WARNING/ERROR/CRITICAL).
    ``stream`` defaults to sys.stdout; tests pass io.StringIO to capture.
    """
    target_stream = stream if stream is not None else sys.stdout
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"invalid log level: {level!r}")

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    pre_chain: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=[
            *pre_chain,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.PrintLoggerFactory(file=target_stream),
        cache_logger_on_first_use=False,
    )

    # Route stdlib logging through structlog so library logs go to the same stream.
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(target_stream)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=pre_chain,
        processor=structlog.processors.JSONRenderer(),
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(numeric_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to ``name``.

    ``name`` shows up in the JSON output's ``logger`` field; pass the module
    name (e.g. ``__name__``) for traceability.
    """
    return structlog.get_logger(name)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_observability_logging.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/redtusk/observability/__init__.py src/redtusk/observability/logging.py tests/unit/test_observability_logging.py
git commit -m "$(cat <<'EOF'
feat(observability): add structlog JSON logging

configure_logging routes both structlog and stdlib logging to a JSON
processor on a configurable stream (stdout by default; tests pass
StringIO to capture). get_logger returns a bound logger; callers
use .bind(job_id=...) to attach context. Tests verify structured
fields, level filtering, logger naming, and contextvar binding.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Observability — metrics

**Files:**
- Create: `/home/coz/Downloads/RedTusk/src/redtusk/observability/metrics.py`
- Modify: `/home/coz/Downloads/RedTusk/src/redtusk/observability/__init__.py`
- Test: `/home/coz/Downloads/RedTusk/tests/unit/test_observability_metrics.py`

A single module-level Prometheus registry with every metric the codebase will use. Centralizing them here means no metric is created elsewhere by accident, and the API tier's `/metrics` endpoint just serializes this one registry.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the centralized Prometheus metrics module."""
from __future__ import annotations

from prometheus_client import REGISTRY as DEFAULT_REGISTRY
from prometheus_client.exposition import generate_latest

from redtusk.observability import metrics as m


def test_metrics_registry_separate_from_default() -> None:
    """RedTusk owns its own registry so other libraries' metrics don't bleed in."""
    assert m.REGISTRY is not DEFAULT_REGISTRY


def test_extractions_total_counter_exposed() -> None:
    m.extractions_total.labels(outcome="success", format="application/pdf").inc()
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_extractions_total" in output


def test_extraction_duration_histogram_exposed() -> None:
    m.extraction_duration_seconds.labels(stage="parse").observe(0.5)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_extraction_duration_seconds" in output


def test_pool_target_size_gauge() -> None:
    m.pool_target_size.set(10)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_target_size 10.0" in output


def test_pool_idle_slots_gauge() -> None:
    m.pool_idle_slots.set(7)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_idle_slots 7.0" in output


def test_pool_assigned_slots_gauge() -> None:
    m.pool_assigned_slots.set(3)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_assigned_slots 3.0" in output


def test_pool_warming_slots_gauge() -> None:
    m.pool_warming_slots.set(2)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_warming_slots 2.0" in output


def test_pool_spawn_total_counter() -> None:
    m.pool_spawn_total.labels(outcome="success").inc()
    m.pool_spawn_total.labels(outcome="failed").inc(2)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_spawn_total" in output
    assert 'outcome="success"' in output
    assert 'outcome="failed"' in output


def test_pool_spawn_duration_histogram() -> None:
    m.pool_spawn_duration_seconds.observe(2.5)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_pool_spawn_duration_seconds" in output


def test_jobs_in_flight_gauge() -> None:
    m.jobs_in_flight.set(5)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_jobs_in_flight 5.0" in output


def test_input_bytes_histogram() -> None:
    m.input_bytes.observe(1024)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_input_bytes" in output


def test_extracted_entries_histogram() -> None:
    m.extracted_entries.observe(42)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_extracted_entries" in output


def test_rejections_total_counter() -> None:
    m.rejections_total.labels(reason="too_large").inc()
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_rejections_total" in output


def test_sync_queue_wait_histogram() -> None:
    m.sync_queue_wait_seconds.observe(0.05)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_sync_queue_wait_seconds" in output


def test_ksm_pages_shared_gauge() -> None:
    m.ksm_pages_shared.set(123456)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_ksm_pages_shared" in output


def test_appcds_mapped_bytes_gauge() -> None:
    m.appcds_mapped_bytes.set(50_000_000)
    output = generate_latest(m.REGISTRY).decode()
    assert "redtusk_appcds_mapped_bytes" in output


def test_render_for_endpoint_returns_text_format() -> None:
    """The API tier will call render_for_endpoint() to populate /metrics."""
    payload, content_type = m.render_for_endpoint()
    assert isinstance(payload, bytes)
    assert content_type.startswith("text/plain")
    assert b"redtusk_" in payload
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/unit/test_observability_metrics.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/redtusk/observability/metrics.py`**

```python
"""Centralized Prometheus metrics for RedTusk.

Every metric the codebase exposes lives here on a private CollectorRegistry.
The API tier's ``/metrics`` endpoint calls ``render_for_endpoint()`` to
serialize this registry; nothing else creates metrics directly.
"""
from __future__ import annotations

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
)
from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest

REGISTRY = CollectorRegistry()

# Extractions
extractions_total = Counter(
    "redtusk_extractions_total",
    "Total extractions performed, labeled by outcome and root content-type",
    labelnames=["outcome", "format"],
    registry=REGISTRY,
)

extraction_duration_seconds = Histogram(
    "redtusk_extraction_duration_seconds",
    "Extraction duration by stage (parse, scanners, total)",
    labelnames=["stage"],
    registry=REGISTRY,
)

# Pool state gauges
pool_target_size = Gauge(
    "redtusk_pool_target_size",
    "Configured warm-pool target size",
    registry=REGISTRY,
)
pool_idle_slots = Gauge(
    "redtusk_pool_idle_slots",
    "Number of warm slots currently idle",
    registry=REGISTRY,
)
pool_assigned_slots = Gauge(
    "redtusk_pool_assigned_slots",
    "Number of warm slots currently processing a job",
    registry=REGISTRY,
)
pool_warming_slots = Gauge(
    "redtusk_pool_warming_slots",
    "Number of slots currently spawning",
    registry=REGISTRY,
)

# Pool spawn lifecycle
pool_spawn_total = Counter(
    "redtusk_pool_spawn_total",
    "Total worker container spawn attempts",
    labelnames=["outcome"],  # success | failed | timeout
    registry=REGISTRY,
)
pool_spawn_duration_seconds = Histogram(
    "redtusk_pool_spawn_duration_seconds",
    "Time from docker-run to fifo-ready for a worker container",
    registry=REGISTRY,
)

# Jobs
jobs_in_flight = Gauge(
    "redtusk_jobs_in_flight",
    "Jobs currently in queued or running state",
    registry=REGISTRY,
)

# Inputs / outputs
input_bytes = Histogram(
    "redtusk_input_bytes",
    "Distribution of accepted input sizes in bytes",
    buckets=(1024, 10_240, 102_400, 1_048_576, 10_485_760, 104_857_600),
    registry=REGISTRY,
)
extracted_entries = Histogram(
    "redtusk_extracted_entries",
    "Distribution of entry counts produced by extraction",
    buckets=(1, 5, 25, 100, 500, 5000),
    registry=REGISTRY,
)

# Rejections + sync queue waits
rejections_total = Counter(
    "redtusk_rejections_total",
    "Inputs rejected before reaching the worker, labeled by reason",
    labelnames=["reason"],
    registry=REGISTRY,
)
sync_queue_wait_seconds = Histogram(
    "redtusk_sync_queue_wait_seconds",
    "Time a synchronous request waited for a warm slot",
    registry=REGISTRY,
)

# Memory dedup observability (scraped from procfs / sysfs by the worker / dispatcher)
ksm_pages_shared = Gauge(
    "redtusk_ksm_pages_shared",
    "Value of /sys/kernel/mm/ksm/pages_shared on the host",
    registry=REGISTRY,
)
appcds_mapped_bytes = Gauge(
    "redtusk_appcds_mapped_bytes",
    "Bytes mapped from the AppCDS archive into worker memory",
    registry=REGISTRY,
)


def render_for_endpoint() -> tuple[bytes, str]:
    """Serialize the registry for serving on /metrics.

    Returns ``(body, content_type)`` so the FastAPI handler can drop both
    into the Response constructor.
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
```

- [ ] **Step 4: Update `src/redtusk/observability/__init__.py` to re-export the metrics module**

Replace the file with:

```python
"""Observability scaffolding: structured logging + Prometheus metrics."""
from __future__ import annotations

from redtusk.observability import metrics
from redtusk.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger", "metrics"]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/pytest tests/unit/test_observability_metrics.py -v
```

Expected: 17 passed.

- [ ] **Step 6: Commit**

```bash
git add src/redtusk/observability/metrics.py src/redtusk/observability/__init__.py tests/unit/test_observability_metrics.py
git commit -m "$(cat <<'EOF'
feat(observability): add Prometheus metrics registry

Single private CollectorRegistry holds every metric the codebase
exposes. Centralizing here prevents accidental metric creation
elsewhere; the API tier's /metrics endpoint will call
render_for_endpoint() to serialize this registry. Covers the full
v1 metric surface: extractions, durations, pool state, spawn
lifecycle, jobs in flight, input/output distributions, rejections,
sync queue waits, KSM and AppCDS observability gauges.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Wrap-up — full suite + ruff + mypy + README pointer

**Files:**
- Modify: `/home/coz/Downloads/RedTusk/README.md`

- [ ] **Step 1: Run the full unit test suite**

```bash
cd /home/coz/Downloads/RedTusk
.venv/bin/pytest tests/unit/ -v
```

Expected: ~130 tests passed (the 7 postgres tests skip without `REDTUSK_TEST_POSTGRES_URL`).

- [ ] **Step 2: Run ruff lint**

```bash
.venv/bin/ruff check src tests
```

Expected: `All checks passed!`

If any issue surfaces, fix it inline. Common ones in this plan: unused imports (`F401`), missing newlines (`W292`). Use `.venv/bin/ruff check --fix src tests` for auto-fixable.

- [ ] **Step 3: Run mypy**

```bash
.venv/bin/mypy src
```

Expected: `Success: no issues found in N source files`.

If any issue surfaces, fix it inline. Common ones: missing type hints on dataclass fields, missing return type annotations.

- [ ] **Step 4: Update `README.md` with foundation status**

Replace `README.md` with:

```markdown
# RedTusk

Sandboxed Apache Tika service with warm-pool worker containers and a tika-server-compatible HTTP API.

See `docs/specs/2026-05-04-redtusk-design.md` for the full design.

## Status

**Foundation (Plan 1) complete.** The `redtusk` Python library has its full data model, configuration layer, JobStore (memory + sqlite + postgres), retention sweeper, and observability scaffolding. No HTTP service, no Docker, no JVM yet — see `docs/plans/` for the remaining plans.

## Local development

```sh
python3 -m venv .venv
.venv/bin/pip install -e .[dev]
.venv/bin/pytest tests/unit/
```

The unit suite runs in pure Python without Docker or a JVM. Postgres tests are skipped unless `REDTUSK_TEST_POSTGRES_URL` is set.

## License

MIT.
```

- [ ] **Step 5: Final commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): mark foundation plan complete

Library's data model, JobStore (3 backends), retention sweeper, and
observability scaffolding are all in place with full unit-test
coverage. Subsequent plans add the JVM worker, dispatcher, API,
Docker images, and ops artifacts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Verify the git log**

```bash
cd /home/coz/Downloads/RedTusk && git log --oneline
```

Expected: roughly 14 commits — initial spec + spec edit + 14 plan commits.

---

## Done

The foundation library is complete. Plan 2 (Java worker) can begin once this is merged.

Coverage summary:
- `errors.py`: 9 exception types, all inheriting from `RedTuskError`
- `limits.py`: 27 tunable fields, env-var driven via `from_env()`
- `types.py`: 13 frozen dataclasses + 3 enums, full to_dict/from_dict round-trip
- `schema.py`: Draft 2020-12 JSON Schema for canonical rmeta + `validate_rmeta()`
- `jobs/`: Protocol + 2 backends (memory, sqlite/postgres) + retention sweeper
- `observability/`: structlog JSON logging + Prometheus metrics registry with 14 metrics

~130 unit tests, all in pure Python, no external dependencies at test time beyond the deps in `pyproject.toml`.
