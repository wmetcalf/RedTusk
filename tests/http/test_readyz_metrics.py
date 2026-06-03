"""Tests for ops endpoints."""


def test_readyz_healthy(client, mock_dispatcher):
    mock_dispatcher.is_healthy.return_value = True
    resp = client.get("/v1/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readyz_degraded(client, mock_dispatcher):
    mock_dispatcher.is_healthy.return_value = False
    mock_dispatcher.fatal_spawn_error = None
    resp = client.get("/v1/readyz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degraded"
    assert "detail" not in resp.json()


def test_readyz_surfaces_fatal_spawn_remediation(client, mock_dispatcher):
    mock_dispatcher.is_healthy.return_value = False
    mock_dispatcher.fatal_spawn_error = (
        "rebuild the rootfs/checkpoint with -XX:CPUFeatures=0x102100055bbd7,0x1c8"
    )
    resp = client.get("/v1/readyz")
    assert resp.status_code == 503
    assert "-XX:CPUFeatures=" in resp.json()["detail"]


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
