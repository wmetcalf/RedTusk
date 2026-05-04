"""Tests for ops endpoints."""


def test_readyz_healthy(client, mock_dispatcher):
    mock_dispatcher.is_healthy.return_value = True
    resp = client.get("/v1/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readyz_degraded(client, mock_dispatcher):
    mock_dispatcher.is_healthy.return_value = False
    resp = client.get("/v1/readyz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degraded"


def test_metrics_returns_prometheus_format(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    ct = resp.headers.get("content-type", "")
    assert "text/plain" in ct


def test_ui_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    ct = resp.headers.get("content-type", "")
    assert "text/html" in ct
    assert b"RedTusk" in resp.content
