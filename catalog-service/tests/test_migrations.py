import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


def alembic_config(url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_upgrade_creates_cached_products(db_url):
    command.upgrade(alembic_config(db_url), "head")

    columns = {c["name"]: c for c in inspect(create_engine(db_url)).get_columns("cached_products")}
    assert set(columns) == {"barcode", "name", "brand", "image_url", "nutri_score", "fetched_at"}
    assert columns["name"]["nullable"] is False
    assert columns["fetched_at"]["nullable"] is False
    assert columns["brand"]["nullable"] is True


def test_nutri_score_only_a_to_e(db_url):
    command.upgrade(alembic_config(db_url), "head")
    engine = create_engine(db_url)
    insert = text(
        "INSERT INTO cached_products (barcode, name, nutri_score, fetched_at) "
        "VALUES (:b, 'x', :n, '2026-01-01 00:00:00')"
    )

    with engine.begin() as conn:
        conn.execute(insert, {"b": "1", "n": "a"})
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(insert, {"b": "2", "n": "f"})


def test_downgrade_drops_the_table(db_url):
    cfg = alembic_config(db_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    assert "cached_products" not in inspect(create_engine(db_url)).get_table_names()
