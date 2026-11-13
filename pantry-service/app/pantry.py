"""Core pantry logic. No FastAPI here: the routes in main.py call these functions."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog_client import Catalog
from app.models import PantryItem

MAX_QUANTITY = 999
NUTRI_SCORES = {"a", "b", "c", "d", "e"}


class ItemNotFound(Exception):
    """No pantry item has this id."""


class QuantityTooHigh(Exception):
    """Adding would take the item's quantity above MAX_QUANTITY."""


def _utc_now() -> datetime:
    # DATETIME2 has no time zone, so store UTC without tzinfo.
    return datetime.now(UTC).replace(tzinfo=None)


def list_items(session: Session) -> list[PantryItem]:
    """All items, newest first. id breaks ties between items added in the same instant."""
    query = select(PantryItem).order_by(PantryItem.created_at.desc(), PantryItem.id.desc())
    return list(session.scalars(query))


def get_item(session: Session, item_id: int) -> PantryItem:
    item = session.get(PantryItem, item_id)
    if item is None:
        raise ItemNotFound(item_id)
    return item


def _find_by_barcode(session: Session, barcode: str) -> PantryItem | None:
    return session.scalars(select(PantryItem).where(PantryItem.barcode == barcode)).first()


def _increment(session: Session, item: PantryItem, quantity: int) -> PantryItem:
    new_quantity = item.quantity + quantity
    if new_quantity > MAX_QUANTITY:
        raise QuantityTooHigh(new_quantity)
    item.quantity = new_quantity
    item.updated_at = _utc_now()
    session.commit()
    session.refresh(item)
    return item


def add_item(
    session: Session, barcode: str, quantity: int, catalog: Catalog
) -> tuple[PantryItem, bool]:
    """Add a product to the pantry. Returns (item, created).

    - Barcode already in the pantry: its quantity goes up and Catalog is not called,
      so this still works when the Catalog Service is down.
    - New barcode: the product details come from Catalog and are saved as snapshots.
      ProductNotFound and CatalogUnavailable from Catalog are passed on to the caller.
    """
    existing = _find_by_barcode(session, barcode)
    if existing is not None:
        return _increment(session, existing, quantity), False

    product = catalog.get_product(barcode)
    nutri_score = product.get("nutri_score")
    item = PantryItem(
        barcode=barcode,
        quantity=quantity,
        name_snapshot=product.get("name") or "Unknown product",
        brand_snapshot=product.get("brand"),
        image_url_snapshot=product.get("image_url"),
        nutri_score_snapshot=nutri_score if nutri_score in NUTRI_SCORES else None,
    )
    session.add(item)
    try:
        session.commit()
    except IntegrityError:
        # Another request added the same barcode between our check and our insert.
        # The unique constraint stopped the duplicate, so add to that row instead.
        session.rollback()
        existing = _find_by_barcode(session, barcode)
        if existing is None:
            raise
        return _increment(session, existing, quantity), False
    session.refresh(item)
    return item, True
