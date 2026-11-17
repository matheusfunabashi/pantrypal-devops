"""Core lookup logic: validate, read the cache, fall back to Open Food Facts."""

import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app import config
from app.models import CachedProduct
from app.off_client import CatalogUnavailable

BARCODE_PATTERN = re.compile(r"\d{8,14}")
NUTRI_SCORES = {"a", "b", "c", "d", "e"}


class InvalidBarcode(ValueError):
    """The barcode is not 8 to 14 digits."""


def validate_barcode(barcode: str) -> str:
    if not BARCODE_PATTERN.fullmatch(barcode):
        raise InvalidBarcode(barcode)
    return barcode


def utcnow() -> datetime:
    # DATETIME2 holds no time zone, so store naive UTC.
    return datetime.now(UTC).replace(tzinfo=None)


def normalise(barcode: str, raw: dict, fetched_at: datetime) -> CachedProduct:
    name = str(raw.get("product_name") or "").strip() or "Unknown product"
    first_brand = str(raw.get("brands") or "").split(",")[0].strip()
    grade = str(raw.get("nutriscore_grade") or "").strip().lower()
    return CachedProduct(
        barcode=barcode,
        name=name[:255],
        brand=first_brand[:255] or None,
        image_url=(str(raw.get("image_front_small_url") or "")[:1000] or None),
        nutri_score=grade if grade in NUTRI_SCORES else None,
        fetched_at=fetched_at,
    )


def to_dict(product: CachedProduct, source: str) -> dict:
    return {
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "image_url": product.image_url,
        "nutri_score": product.nutri_score,
        "source": source,
    }


def get_product(
    session: Session,
    barcode: str,
    fetch: Callable[[str], dict],
    now: Callable[[], datetime] = utcnow,
) -> dict:
    """Look a product up. Raises InvalidBarcode, ProductNotFound or CatalogUnavailable."""
    validate_barcode(barcode)
    cached = session.get(CachedProduct, barcode)
    current = now()

    if cached and current - cached.fetched_at < timedelta(days=config.CACHE_TTL_DAYS):
        return to_dict(cached, "cache")

    try:
        raw = fetch(barcode)
    except CatalogUnavailable:
        if cached:  # a stale answer beats no answer
            return to_dict(cached, "cache")
        raise

    product = session.merge(normalise(barcode, raw, current))
    session.commit()
    return to_dict(product, "openfoodfacts")
