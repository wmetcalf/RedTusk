"""Tests that the JobStore protocol has the expected method surface."""
from __future__ import annotations

import inspect

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
