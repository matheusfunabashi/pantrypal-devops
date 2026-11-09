import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="request"):
        client.get("/health")

    assert any(
        "method=GET path=/health status=200 duration_ms=" in record.getMessage()
        for record in caplog.records
    )
