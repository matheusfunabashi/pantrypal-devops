import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_off_http_client, get_session
from tests.conftest import NUTELLA, make_client

BARCODE = "3017620422003"


@pytest.fixture
def call(session):
    def run(handler, barcode=BARCODE):
        app.dependency_overrides[get_session] = lambda: session
        app.dependency_overrides[get_off_http_client] = lambda: make_client(handler)
        try:
            return TestClient(app).get(f"/products/{barcode}")
        finally:
            app.dependency_overrides.clear()

    return run


def test_200_then_cache(call):
    hits = []

    def handler(request):
        hits.append(1)
        return httpx.Response(200, json=NUTELLA)

    first = call(handler)
    second = call(handler)

    assert first.status_code == 200
    assert first.json()["source"] == "openfoodfacts"
    assert second.json()["source"] == "cache"
    assert second.json()["name"] == "Nutella"
    assert len(hits) == 1


def test_404(call):
    response = call(lambda r: httpx.Response(404, json={"status": "failure"}))

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


def test_422(call):
    response = call(lambda r: httpx.Response(200, json=NUTELLA), barcode="abc")

    assert response.status_code == 422


def test_503(call):
    response = call(lambda r: httpx.Response(500))

    assert response.status_code == 503
    assert response.json() == {"detail": "Product lookup is temporarily unavailable"}
