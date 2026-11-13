import pytest
from sqlalchemy.exc import IntegrityError

from app import pantry
from app.catalog_client import CatalogUnavailable, NotConnectedCatalog, ProductNotFound
from app.models import PantryItem
from tests.conftest import NUTELLA, FakeCatalog

BARCODE = "3017620422003"


def test_add_new_item_saves_the_catalog_details(session, catalog):
    item, created = pantry.add_item(session, BARCODE, 2, catalog)

    assert created is True
    assert item.id is not None
    assert item.quantity == 2
    assert item.name_snapshot == "Nutella"
    assert item.brand_snapshot == "Ferrero"
    assert item.image_url_snapshot == NUTELLA["image_url"]
    assert item.nutri_score_snapshot == "e"
    assert catalog.calls == [BARCODE]


def test_add_existing_barcode_increments_without_calling_catalog(session, catalog):
    first, _ = pantry.add_item(session, BARCODE, 2, catalog)
    catalog.calls.clear()

    item, created = pantry.add_item(session, BARCODE, 3, catalog)

    assert created is False
    assert item.id == first.id
    assert item.quantity == 5
    assert catalog.calls == []
    assert len(pantry.list_items(session)) == 1


def test_add_existing_barcode_works_when_catalog_is_down(session, catalog):
    pantry.add_item(session, BARCODE, 1, catalog)
    down = FakeCatalog(error=CatalogUnavailable())

    item, _ = pantry.add_item(session, BARCODE, 1, down)

    assert item.quantity == 2


def test_total_above_999_is_rejected_and_quantity_unchanged(session, catalog):
    item, _ = pantry.add_item(session, BARCODE, 998, catalog)

    with pytest.raises(pantry.QuantityTooHigh):
        pantry.add_item(session, BARCODE, 2, catalog)

    assert pantry.get_item(session, item.id).quantity == 998


def test_total_of_exactly_999_is_allowed(session, catalog):
    pantry.add_item(session, BARCODE, 998, catalog)

    item, _ = pantry.add_item(session, BARCODE, 1, catalog)

    assert item.quantity == 999


def test_unknown_product_raises_and_saves_nothing(session):
    with pytest.raises(ProductNotFound):
        pantry.add_item(session, "12345678", 1, FakeCatalog())

    assert pantry.list_items(session) == []


def test_catalog_down_raises_and_saves_nothing(session):
    with pytest.raises(CatalogUnavailable):
        pantry.add_item(session, "12345678", 1, FakeCatalog(error=CatalogUnavailable()))

    assert pantry.list_items(session) == []


def test_missing_details_are_stored_as_unknown_or_null(session):
    catalog = FakeCatalog(products={"12345678": {"name": None, "nutri_score": "unknown"}})

    item, _ = pantry.add_item(session, "12345678", 1, catalog)

    assert item.name_snapshot == "Unknown product"
    assert item.brand_snapshot is None
    assert item.image_url_snapshot is None
    assert item.nutri_score_snapshot is None


def test_list_items_newest_first(session, catalog):
    catalog.products["12345678"] = {"name": "Milk", "brand": None, "image_url": None}
    pantry.add_item(session, BARCODE, 1, catalog)
    pantry.add_item(session, "12345678", 1, catalog)

    barcodes = [item.barcode for item in pantry.list_items(session)]

    assert barcodes == ["12345678", BARCODE]


def test_get_item_and_missing_item(session, catalog):
    item, _ = pantry.add_item(session, BARCODE, 1, catalog)

    assert pantry.get_item(session, item.id).barcode == BARCODE
    with pytest.raises(pantry.ItemNotFound):
        pantry.get_item(session, 999)


def test_duplicate_insert_race_becomes_an_increment(session, catalog, monkeypatch):
    # Simulate another request inserting the same barcode right after our check:
    # the first lookup sees nothing, but the row already exists when we insert.
    session.add(PantryItem(barcode=BARCODE, quantity=1, name_snapshot="Nutella"))
    session.commit()
    real_find = pantry._find_by_barcode
    calls = {"n": 0}

    def find_misses_once(s, barcode):
        calls["n"] += 1
        return None if calls["n"] == 1 else real_find(s, barcode)

    monkeypatch.setattr(pantry, "_find_by_barcode", find_misses_once)

    item, created = pantry.add_item(session, BARCODE, 2, catalog)

    assert created is False
    assert item.quantity == 3


def test_other_integrity_errors_are_not_hidden(session, catalog, monkeypatch):
    monkeypatch.setattr(pantry, "_find_by_barcode", lambda s, b: None)

    def failing_commit():
        raise IntegrityError("INSERT", {}, Exception("some other constraint"))

    monkeypatch.setattr(session, "commit", failing_commit)

    with pytest.raises(IntegrityError):
        pantry.add_item(session, BARCODE, 1, catalog)


def test_placeholder_catalog_is_unavailable():
    with pytest.raises(CatalogUnavailable):
        NotConnectedCatalog().get_product(BARCODE)
