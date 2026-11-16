from datetime import timedelta

import pytest

from app import config
from app.models import CachedProduct
from app.off_client import CatalogUnavailable, ProductNotFound
from app.products import InvalidBarcode, get_product, utcnow

BARCODE = "3017620422003"
RAW = {
    "product_name": "  Nutella  ",
    "brands": "Ferrero, Nutella",
    "image_front_small_url": "https://images.example/nutella.jpg",
    "nutriscore_grade": "e",
}


class FakeOff:
    def __init__(self, raw=None, error=None):
        self.raw, self.error, self.calls = raw, error, 0

    def __call__(self, barcode):
        self.calls += 1
        if self.error:
            raise self.error
        return self.raw


def stale_row(session, days):
    session.add(
        CachedProduct(
            barcode=BARCODE,
            name="Old name",
            brand=None,
            image_url=None,
            nutri_score="a",
            fetched_at=utcnow() - timedelta(days=days),
        )
    )
    session.commit()


def test_cache_miss_fetches_normalises_and_saves(session):
    off = FakeOff(RAW)

    result = get_product(session, BARCODE, off)

    assert result == {
        "barcode": BARCODE,
        "name": "Nutella",
        "brand": "Ferrero",
        "image_url": "https://images.example/nutella.jpg",
        "nutri_score": "e",
        "source": "openfoodfacts",
    }
    assert session.get(CachedProduct, BARCODE).name == "Nutella"


def test_fresh_hit_does_not_call_off(session):
    off = FakeOff(RAW)
    get_product(session, BARCODE, off)

    second = get_product(session, BARCODE, off)

    assert second["source"] == "cache"
    assert off.calls == 1


def test_stale_row_is_refreshed(session):
    stale_row(session, config.CACHE_TTL_DAYS + 1)
    off = FakeOff(RAW)

    result = get_product(session, BARCODE, off)

    assert off.calls == 1
    assert result["source"] == "openfoodfacts"
    assert result["name"] == "Nutella"
    assert session.query(CachedProduct).count() == 1  # updated, not duplicated


def test_row_just_inside_ttl_is_fresh(session):
    stale_row(session, config.CACHE_TTL_DAYS - 1)
    off = FakeOff(RAW)

    assert get_product(session, BARCODE, off)["source"] == "cache"
    assert off.calls == 0


def test_off_down_returns_stale_row(session):
    stale_row(session, config.CACHE_TTL_DAYS + 1)

    result = get_product(session, BARCODE, FakeOff(error=CatalogUnavailable("down")))

    assert result["name"] == "Old name"
    assert result["source"] == "cache"


def test_off_down_without_cache_raises(session):
    with pytest.raises(CatalogUnavailable):
        get_product(session, BARCODE, FakeOff(error=CatalogUnavailable("down")))


def test_not_found_raises_and_saves_nothing(session):
    with pytest.raises(ProductNotFound):
        get_product(session, BARCODE, FakeOff(error=ProductNotFound(BARCODE)))
    assert session.query(CachedProduct).count() == 0


@pytest.mark.parametrize("barcode", ["", "1234567", "123456789012345", "12345abc", "12 345 678"])
def test_malformed_barcode_is_rejected_before_any_call(session, barcode):
    off = FakeOff(RAW)
    with pytest.raises(InvalidBarcode):
        get_product(session, barcode, off)
    assert off.calls == 0


@pytest.mark.parametrize("grade", [None, "", "unknown", "not-applicable", "f", "A "])
def test_nutri_score_only_kept_when_a_to_e(session, grade):
    raw = {**RAW, "nutriscore_grade": grade}

    result = get_product(session, BARCODE, FakeOff(raw))

    assert result["nutri_score"] == (grade.strip().lower() if grade == "A " else None)


def test_missing_fields_are_handled(session):
    result = get_product(session, BARCODE, FakeOff({}))

    assert result["name"] == "Unknown product"
    assert result["brand"] is None
    assert result["image_url"] is None
    assert result["nutri_score"] is None


def test_leading_zeros_are_kept(session):
    get_product(session, "00012345678", FakeOff(RAW))

    assert session.get(CachedProduct, "00012345678").barcode == "00012345678"
