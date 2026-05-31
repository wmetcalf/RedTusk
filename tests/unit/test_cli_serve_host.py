"""Unit test for the CLI serve --host default (finding 6).

The `serve` command must default to binding 127.0.0.1 (loopback), not 0.0.0.0
(all interfaces). Operators can still opt in to 0.0.0.0 by passing --host
explicitly.
"""
from __future__ import annotations

from redtusk.cli import serve


def _host_param_default() -> str:
    for param in serve.params:
        if param.name == "host":
            return param.default
    raise AssertionError("serve has no --host option")


def test_serve_host_defaults_to_loopback() -> None:
    assert _host_param_default() == "127.0.0.1"


def test_serve_host_default_is_not_wildcard() -> None:
    assert _host_param_default() != "0.0.0.0"
