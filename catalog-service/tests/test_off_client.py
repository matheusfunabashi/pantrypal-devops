import httpx
import pytest

from app import config
from app.off_client import CatalogUnavailable, ProductNotFound, fetch_product
from tests.conftest import NUTELLA, make_client


def test_sends_user_agent_fields_and_path():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["user-agent"]
        seen["path"] = request.url.path
        seen["fields"] = request.url.params["fields"]
        return httpx.Response(200, json=NUTELLA)

    product = fetch_product(make_client(handler), "3017620422003")

    assert product["product_name"].strip() == "Nutella"
    assert seen["ua"] == config.OFF_USER_AGENT
    assert seen["path"] == "/api/v3/product/3017620422003"
    assert seen["fields"] == "product_name,brands,image_front_small_url,nutriscore_grade"


def test_http_404_is_not_found():
    client = make_client(lambda r: httpx.Response(404, json={"status": "failure"}))
    with pytest.raises(ProductNotFound):
        fetch_product(client, "00000000")


def test_failure_status_with_200_is_not_found():
    client = make_client(lambda r: httpx.Response(200, json={"status": "failure"}))
    with pytest.raises(ProductNotFound):
        fetch_product(client, "00000000")


def test_server_error_is_unavailable():
    client = make_client(lambda r: httpx.Response(503))
    with pytest.raises(CatalogUnavailable):
        fetch_product(client, "3017620422003")


def test_timeout_is_unavailable():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(CatalogUnavailable):
        fetch_product(make_client(handler), "3017620422003")


def test_connection_error_is_unavailable():
    def handler(request):
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(CatalogUnavailable):
        fetch_product(make_client(handler), "3017620422003")


def test_invalid_json_is_unavailable():
    client = make_client(lambda r: httpx.Response(200, content=b"<html>"))
    with pytest.raises(CatalogUnavailable):
        fetch_product(client, "3017620422003")


def test_exactly_one_attempt_is_made():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    with pytest.raises(CatalogUnavailable):
        fetch_product(make_client(handler), "3017620422003")
    assert len(calls) == 1
