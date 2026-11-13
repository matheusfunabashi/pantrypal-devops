"""How the Pantry Service gets product details from the Catalog Service.

S1-10a only defines the interface. The real HTTP client (httpx, CATALOG_URL,
timeout) is added in S1-11. Until then, adding a new barcode returns 503,
while listing, viewing and adding an existing barcode work normally.
"""

from typing import Protocol, TypedDict


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


class NotConnectedCatalog:
    """Placeholder used until S1-11 adds the real client."""

    def get_product(self, barcode: str) -> Product:
        raise CatalogUnavailable("Catalog client not implemented yet")


def get_catalog() -> Catalog:
    """FastAPI dependency. Tests replace it with a fake catalog."""
    return NotConnectedCatalog()
