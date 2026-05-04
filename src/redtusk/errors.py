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
    """Raised when a caller tries to delete a non-terminal job.

    Note: The ``JobStore`` backends (MemoryJobStore, SqlJobStore) return ``False``
    from ``delete()`` instead of raising this exception — they implement the
    protocol's return-False semantics. This exception is intended for use by the
    API tier, which translates the ``False`` return into an HTTP 409 response and
    may raise this for its own internal validation.

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
