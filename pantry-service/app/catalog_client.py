"""How the Pantry Service gets product details from the Catalog Service.

The Pantry Service calls GET {CATALOG_URL}/products/{barcode} over HTTP, with a
total timeout of CATALOG_TIMEOUT_SECONDS. Failures become two exceptions that the
routes turn into the agreed answers:

- Catalog 404                                  -> ProductNotFound   -> Pantry 404
- timeout, connection error, 5xx, bad response -> CatalogUnavailable -> Pantry 503
"""

import logging
from typing import Protocol, TypedDict

import httpx

from app import config

log = logging.getLogger("catalog_client")


class ProductNotFound(Exception):
    """The Catalog Service doesn't know this barcode (Catalog 404)."""


class CatalogUnavailable(Exception):
    """The Catalog Service timed out, couldn't be reached or returned a 5xx."""


class Product(TypedDict):
    name: str
    brand: str | None
    image_url: str | None
    nutri_score: str | None


class Catalog(Protocol):
    def get_product(self, barcode: str) -> Product: ...


class HttpCatalog:
    """Calls the Catalog Service over HTTP."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # transport lets tests answer the requests without a real Catalog Service.
        self._client = httpx.Client(base_url=base_url, timeout=timeout_seconds, transport=transport)

    def get_product(self, barcode: str) -> Product:
        try:
            response = self._client.get(f"/products/{barcode}")
        except httpx.TimeoutException as exc:
            self._warn(barcode, "timeout")
            raise CatalogUnavailable("Catalog timed out") from exc
        except httpx.HTTPError as exc:
            # Connection refused, DNS failure, connection reset, ...
            self._warn(barcode, type(exc).__name__)
            raise CatalogUnavailable("Catalog could not be reached") from exc

        if response.status_code == 404:
            raise ProductNotFound(barcode)
        if response.status_code != 200:
            # 5xx, or anything else the contract doesn't allow for a valid barcode.
            self._warn(barcode, f"status {response.status_code}")
            raise CatalogUnavailable(f"Catalog answered {response.status_code}")

        try:
            body = response.json()
            name = body["name"]
        except (ValueError, KeyError, TypeError) as exc:
            self._warn(barcode, "invalid response body")
            raise CatalogUnavailable("Catalog sent an invalid response") from exc

        return Product(
            name=name,
            brand=body.get("brand"),
            image_url=body.get("image_url"),
            nutri_score=body.get("nutri_score"),
        )

    @staticmethod
    def _warn(barcode: str, error: str) -> None:
        # One line per failure: the barcode and the error type only, no URLs or bodies.
        log.warning("catalog lookup failed barcode=%s error=%s", barcode, error)


_catalog: HttpCatalog | None = None


def get_catalog() -> Catalog:
    """FastAPI dependency. One shared client, so connections are reused between
    requests. Tests replace this with a fake catalog."""
    global _catalog
    if _catalog is None:
        _catalog = HttpCatalog(config.CATALOG_URL, config.CATALOG_TIMEOUT_SECONDS)
    return _catalog
