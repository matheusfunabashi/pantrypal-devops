import logging

import httpx
import pytest

from app import catalog_client, config
from app.catalog_client import CatalogUnavailable, HttpCatalog, ProductNotFound, get_catalog

BARCODE = "3017620422003"
NUTELLA = {
    "barcode": BARCODE,
    "name": "Nutella",
    "brand": "Ferrero",
    "image_url": "https://example.com/nutella.jpg",
    "nutri_score": "e",
    "source": "openfoodfacts",
}


def catalog_answering(handler):
    """An HttpCatalog whose requests are answered by handler instead of the network."""
    return HttpCatalog("http://catalog.test", 10, transport=httpx.MockTransport(handler))


def test_found_product_is_returned():
    seen = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(200, json=NUTELLA)

    product = catalog_answering(handler).get_product(BARCODE)

    assert product == {
        "name": "Nutella",
        "brand": "Ferrero",
        "image_url": "https://example.com/nutella.jpg",
        "nutri_score": "e",
    }
    assert str(seen[0]) == f"http://catalog.test/products/{BARCODE}"


def test_missing_optional_fields_become_none():
    catalog = catalog_answering(lambda r: httpx.Response(200, json={"name": "Milk"}))

    product = catalog.get_product(BARCODE)

    assert product == {"name": "Milk", "brand": None, "image_url": None, "nutri_score": None}


def test_404_raises_product_not_found():
    catalog = catalog_answering(lambda r: httpx.Response(404, json={"detail": "Product not found"}))

    with pytest.raises(ProductNotFound):
        catalog.get_product(BARCODE)


@pytest.mark.parametrize("status", [500, 502, 503, 422])
def test_error_status_raises_catalog_unavailable(status, caplog):
    catalog = catalog_answering(lambda r: httpx.Response(status, json={"detail": "x"}))

    with caplog.at_level(logging.WARNING, logger="catalog_client"):
        with pytest.raises(CatalogUnavailable):
            catalog.get_product(BARCODE)

    assert caplog.messages == [f"catalog lookup failed barcode={BARCODE} error=status {status}"]


def test_timeout_raises_catalog_unavailable(caplog):
    def handler(request):
        raise httpx.ReadTimeout("too slow", request=request)

    with caplog.at_level(logging.WARNING, logger="catalog_client"):
        with pytest.raises(CatalogUnavailable):
            catalog_answering(handler).get_product(BARCODE)

    assert caplog.messages == [f"catalog lookup failed barcode={BARCODE} error=timeout"]


def test_connection_error_raises_catalog_unavailable(caplog):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with caplog.at_level(logging.WARNING, logger="catalog_client"):
        with pytest.raises(CatalogUnavailable):
            catalog_answering(handler).get_product(BARCODE)

    assert caplog.messages == [f"catalog lookup failed barcode={BARCODE} error=ConnectError"]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"brand": "no name"}),
        httpx.Response(200, json=["a", "list"]),
    ],
)
def test_invalid_body_raises_catalog_unavailable(response):
    with pytest.raises(CatalogUnavailable):
        catalog_answering(lambda r: response).get_product(BARCODE)


def test_timeout_setting_is_used():
    catalog = HttpCatalog("http://catalog.test", 7.5)

    assert catalog._client.timeout.read == 7.5
    assert catalog._client.timeout.connect == 7.5


def test_get_catalog_uses_config_and_is_shared(monkeypatch):
    monkeypatch.setattr(catalog_client, "_catalog", None)
    monkeypatch.setattr(config, "CATALOG_URL", "http://catalog-service:8000")
    monkeypatch.setattr(config, "CATALOG_TIMEOUT_SECONDS", 3.0)

    first = get_catalog()

    assert isinstance(first, HttpCatalog)
    assert str(first._client.base_url) == "http://catalog-service:8000"
    assert first._client.timeout.read == 3.0
    assert get_catalog() is first
