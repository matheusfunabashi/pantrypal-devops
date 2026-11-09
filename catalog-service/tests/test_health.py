import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logging_middleware import RequestLogMiddleware
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "catalog"}


def test_request_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="request"):
        client.get("/health")

    assert any(
        "method=GET path=/health status=200 duration_ms=" in record.getMessage()
        for record in caplog.records
    )


def test_failing_request_is_logged_as_500(caplog):
    failing_app = FastAPI()
    failing_app.add_middleware(RequestLogMiddleware)

    @failing_app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    failing_client = TestClient(failing_app, raise_server_exceptions=False)
    with caplog.at_level(logging.INFO, logger="request"):
        response = failing_client.get("/boom")

    assert response.status_code == 500
    assert any(
        "method=GET path=/boom status=500 duration_ms=" in record.getMessage()
        for record in caplog.records
    )
