"""Tika-server parity integration tests.

Requires a running RedTusk instance and a running tika-server instance.

Environment variables:
  REDTUSK_TEST_URL   e.g. http://localhost:8000
  TIKA_TEST_URL      e.g. http://localhost:9998

Run:
  pytest tests/integration -m integration -v

These tests are skipped automatically when the env vars are not set.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

REDTUSK_URL = os.environ.get("REDTUSK_TEST_URL", "")
TIKA_URL = os.environ.get("TIKA_TEST_URL", "")
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "safe"

pytestmark = pytest.mark.integration


def _skip_unless_configured() -> None:
    if not REDTUSK_URL or not TIKA_URL:
        pytest.skip("REDTUSK_TEST_URL and TIKA_TEST_URL must both be set")


@pytest.fixture(scope="module")
def redtusk():
    _skip_unless_configured()
    import httpx
    return httpx.Client(base_url=REDTUSK_URL, timeout=60)


@pytest.fixture(scope="module")
def tika():
    _skip_unless_configured()
    import httpx
    return httpx.Client(base_url=TIKA_URL, timeout=60)


# ── /detect/stream parity ─────────────────────────────────────────────────

@pytest.mark.parametrize("filename,expected_ct", [
    ("sample.txt",  "text/plain"),
])
def test_detect_parity(redtusk, tika, filename, expected_ct):
    fixture = FIXTURES_DIR / filename
    if not fixture.exists():
        pytest.skip(f"Fixture {filename} not in tests/fixtures/safe/")
    body = fixture.read_bytes()
    r_ct = redtusk.put("/detect/stream", content=body).text.strip()
    t_ct = tika.put("/detect/stream", content=body).text.strip()
    assert r_ct == t_ct, f"Detect mismatch for {filename}: RedTusk={r_ct!r} Tika={t_ct!r}"
    assert expected_ct in r_ct


# ── /tika text extraction parity ──────────────────────────────────────────

def test_tika_text_plain(redtusk, tika):
    body = b"Parity: the quick brown fox jumps over the lazy dog\n"
    r_text = redtusk.put("/tika", content=body).text.strip()
    t_text = tika.put("/tika", content=body).text.strip()
    assert r_text == t_text, f"Text mismatch:\n  RedTusk: {r_text!r}\n  Tika:    {t_text!r}"


# ── /rmeta shape ──────────────────────────────────────────────────────────

def test_rmeta_is_list_with_content_type(redtusk):
    result = redtusk.put("/rmeta", content=b"shape test").json()
    assert isinstance(result, list), "rmeta must return a list"
    assert len(result) >= 1
    assert "Content-Type" in result[0], "First rmeta entry must have Content-Type"


def test_rmeta_parity_keys(redtusk, tika):
    body = b"Key parity test\n"
    r_keys = set(redtusk.put("/rmeta", content=body).json()[0].keys())
    t_keys = set(tika.put("/rmeta", content=body).json()[0].keys())
    # Tika-internal keys RedTusk may omit legitimately
    allowed_missing = {"X-TIKA:Parsed-By", "X-TIKA:Parsed-By-Full-Set",
                       "X-TIKA:embedded_depth", "X-TIKA:EXCEPTION:warn"}
    unexpected_missing = t_keys - r_keys - allowed_missing
    assert not unexpected_missing, f"Keys in Tika but not RedTusk: {unexpected_missing}"


# ── /meta ─────────────────────────────────────────────────────────────────

def test_meta_has_content_type(redtusk):
    result = redtusk.put("/meta", content=b"meta test").json()
    assert isinstance(result, dict)
    assert "Content-Type" in result


# ── /v1/readyz ────────────────────────────────────────────────────────────

def test_readyz_ok(redtusk):
    resp = redtusk.get("/v1/readyz")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
