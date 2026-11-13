import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

INSERT = text(
    "INSERT INTO pantry_items (barcode, quantity, name_snapshot) VALUES (:barcode, :qty, 'x')"
)


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


def alembic_config(url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture
def engine(db_url):
    command.upgrade(alembic_config(db_url), "head")
    return create_engine(db_url)


def test_upgrade_creates_pantry_items(engine):
    columns = {c["name"]: c for c in inspect(engine).get_columns("pantry_items")}

    assert set(columns) == {
        "id",
        "barcode",
        "quantity",
        "name_snapshot",
        "brand_snapshot",
        "image_url_snapshot",
        "nutri_score_snapshot",
        "created_at",
        "updated_at",
    }
    for required in ("barcode", "quantity", "name_snapshot", "created_at", "updated_at"):
        assert columns[required]["nullable"] is False
    assert columns["brand_snapshot"]["nullable"] is True


@pytest.mark.parametrize("qty", [1, 999])
def test_quantity_accepts_1_to_999(engine, qty):
    with engine.begin() as conn:
        conn.execute(INSERT, {"barcode": "12345678", "qty": qty})


@pytest.mark.parametrize("qty", [0, -1, 1000])
def test_quantity_outside_1_to_999_is_rejected(engine, qty):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(INSERT, {"barcode": "12345678", "qty": qty})


def test_barcode_is_unique(engine):
    with engine.begin() as conn:
        conn.execute(INSERT, {"barcode": "12345678", "qty": 1})
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(INSERT, {"barcode": "12345678", "qty": 2})


def test_barcode_keeps_leading_zeros(engine):
    with engine.begin() as conn:
        conn.execute(INSERT, {"barcode": "00012345", "qty": 1})
        stored = conn.execute(text("SELECT barcode FROM pantry_items")).scalar_one()

    assert stored == "00012345"


def test_second_upgrade_applies_nothing(db_url, engine):
    command.upgrade(alembic_config(db_url), "head")

    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0001"


def test_downgrade_drops_the_table(db_url, engine):
    command.downgrade(alembic_config(db_url), "base")

    assert "pantry_items" not in inspect(engine).get_table_names()
