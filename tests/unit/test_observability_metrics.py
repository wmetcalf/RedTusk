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
