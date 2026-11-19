"""Core pantry logic. No FastAPI here: the routes in main.py call these functions."""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
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


def _try_increment(session: Session, barcode: str, quantity: int) -> PantryItem | None:
    """Add to an existing item's quantity in one atomic UPDATE.

    The database does "quantity = quantity + n" itself, so two requests adding the
    same barcode at the same time both count; neither overwrites the other with a
    stale value. The 999 limit is part of the same statement.

    Returns the updated item, or None if no item has this barcode.
    Raises QuantityTooHigh if the item exists but the total would go above 999.
    """
    result = session.execute(
        update(PantryItem)
        .where(
            PantryItem.barcode == barcode,
            PantryItem.quantity + quantity <= MAX_QUANTITY,
        )
        .values(quantity=PantryItem.quantity + quantity, updated_at=_utc_now())
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        session.rollback()
        if _find_by_barcode(session, barcode) is not None:
            raise QuantityTooHigh(barcode)
        return None
    session.commit()
    # commit() expires loaded objects, so this reads the new values from the database.
    return _find_by_barcode(session, barcode)


def add_item(
    session: Session, barcode: str, quantity: int, catalog: Catalog
) -> tuple[PantryItem, bool]:
    """Add a product to the pantry. Returns (item, created).

    - Barcode already in the pantry: its quantity goes up and Catalog is not called,
      so this still works when the Catalog Service is down.
    - New barcode: the product details come from Catalog and are saved as snapshots.
      ProductNotFound and CatalogUnavailable from Catalog are passed on to the caller.
    """
    existing = _try_increment(session, barcode, quantity)
    if existing is not None:
        return existing, False

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
        existing = _try_increment(session, barcode, quantity)
        if existing is None:
            raise
        return existing, False
    session.refresh(item)
    return item, True


def set_quantity(session: Session, item_id: int, quantity: int) -> PantryItem:
    """Set an item's quantity to a new value (PUT /pantry/{id}). Never calls Catalog.

    One UPDATE statement, so an item deleted at the same moment gives ItemNotFound
    instead of an error. The 1-999 range is checked by the schema before we get here,
    and again by the database's check constraint.
    """
    result = session.execute(
        update(PantryItem)
        .where(PantryItem.id == item_id)
        .values(quantity=quantity, updated_at=_utc_now())
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        session.rollback()
        raise ItemNotFound(item_id)
    session.commit()
    # commit() expires loaded objects, so this reads the new values from the database.
    return get_item(session, item_id)


def delete_item(session: Session, item_id: int) -> None:
    """Remove an item from the pantry (DELETE /pantry/{id}). Never calls Catalog.

    One DELETE statement: if two requests delete the same item, the second one
    gets ItemNotFound (404) instead of an error.
    """
    result = session.execute(
        delete(PantryItem)
        .where(PantryItem.id == item_id)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        session.rollback()
        raise ItemNotFound(item_id)
    session.commit()
