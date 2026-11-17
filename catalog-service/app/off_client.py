"""Client for the Open Food Facts v3 product API."""

import httpx

from app import config

FIELDS = "product_name,brands,image_front_small_url,nutriscore_grade"


class ProductNotFound(Exception):
    """Open Food Facts does not know this barcode."""


class CatalogUnavailable(Exception):
    """Open Food Facts could not be reached or answered with an error."""


def build_client() -> httpx.Client:
    return httpx.Client(
        base_url=config.OFF_BASE_URL,
        headers={"User-Agent": config.OFF_USER_AGENT},
        timeout=config.OFF_TIMEOUT_SECONDS,
    )


def fetch_product(client: httpx.Client, barcode: str) -> dict:
    """Return the raw "product" object for a barcode. One attempt, no retries."""
    try:
        response = client.get(f"/api/v3/product/{barcode}", params={"fields": FIELDS})
    except httpx.HTTPError as exc:  # timeouts and connection errors
        raise CatalogUnavailable(str(exc)) from exc

    if response.status_code == 404:
        raise ProductNotFound(barcode)
    if response.status_code != 200:  # 5xx, and anything else we cannot use
        raise CatalogUnavailable(f"Open Food Facts answered {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise CatalogUnavailable("Open Food Facts sent invalid JSON") from exc

    product = body.get("product") if isinstance(body, dict) else None
    if body.get("status") == "failure" or not isinstance(product, dict):
        raise ProductNotFound(barcode)
    return product
