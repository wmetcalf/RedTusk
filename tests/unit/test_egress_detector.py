"""Unit test for the egress drift-gate's connect()-line detector.

Proves the detector flags an external AF_INET/AF_INET6 connect() and ignores
loopback + AF_UNIX — i.e. the integration gate (test_no_network_egress) would
actually catch an XXE/SSRF egress regression, not silently pass.
"""

from __future__ import annotations

from tests.integration.test_no_network_egress import _external_connects

_EXTERNAL_V4 = (
    '12345 connect(7, {sa_family=AF_INET, sin_port=htons(1), '
    'sin_addr=inet_addr("192.0.2.1")}, 16) = -1 EINPROGRESS'
)
_EXTERNAL_V6 = (
    '12345 connect(7, {sa_family=AF_INET6, sin6_port=htons(1), '
    'sin6_addr=inet_pton(AF_INET6, "2001:db8::1")}, 28) = -1 EINPROGRESS'
)
_LOOPBACK = (
    '12345 connect(7, {sa_family=AF_INET, sin_port=htons(8080), '
    'sin_addr=inet_addr("127.0.0.1")}, 16) = 0'
)
_UNIX = '12345 connect(4, {sa_family=AF_UNIX, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT'


def test_external_inet_is_flagged():
    assert len(_external_connects(_EXTERNAL_V4)) == 1
    assert len(_external_connects(_EXTERNAL_V6)) == 1


def test_loopback_and_unix_are_ignored():
    assert _external_connects(_LOOPBACK) == []
    assert _external_connects(_UNIX) == []
    assert _external_connects(f"{_LOOPBACK}\n{_UNIX}") == []


def test_mixed_trace_flags_only_external():
    trace = f"{_UNIX}\n{_LOOPBACK}\n{_EXTERNAL_V4}"
    flagged = _external_connects(trace)
    assert len(flagged) == 1
    assert "192.0.2.1" in flagged[0]
