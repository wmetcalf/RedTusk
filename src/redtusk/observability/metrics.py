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
fc_cpu_feature_mismatch_total = Counter(
    "redtusk_fc_cpu_feature_mismatch_total",
    "Firecracker warm spawns that failed because the CRaC checkpoint needs CPU "
    "features the microVM guest lacks (rebuild rootfs with -XX:CPUFeatures=<v>)",
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


# Pool helper functions — called by pool.py to avoid repeated label lookups.


def record_pool_idle(n: int) -> None:
    pool_idle_slots.set(n)


def record_pool_assigned(n: int) -> None:
    pool_assigned_slots.set(n)


def record_pool_warming(n: int) -> None:
    pool_warming_slots.set(n)


def record_pool_target(n: int) -> None:
    pool_target_size.set(n)


def record_spawn_outcome(outcome: str) -> None:
    """Increment pool_spawn_total for the given outcome (success|failed|timeout)."""
    pool_spawn_total.labels(outcome=outcome).inc()


def record_spawn_duration(seconds: float) -> None:
    """Observe spawn duration in the pool_spawn_duration_seconds histogram."""
    pool_spawn_duration_seconds.observe(seconds)


def record_cpu_feature_mismatch() -> None:
    """Increment the Firecracker CRaC CPU-feature-mismatch counter."""
    fc_cpu_feature_mismatch_total.inc()


def record_extraction_total(outcome: str, fmt: str) -> None:
    """Increment extractions_total for the given outcome and format."""
    extractions_total.labels(outcome=outcome, format=fmt).inc()


def record_extraction_duration(stage: str, seconds: float) -> None:
    """Observe extraction duration for a given stage."""
    extraction_duration_seconds.labels(stage=stage).observe(seconds)


def record_jobs_in_flight(n: int) -> None:
    """Set the jobs_in_flight gauge."""
    jobs_in_flight.set(n)
