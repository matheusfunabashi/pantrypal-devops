from datetime import datetime

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import CachedProduct


def test_model_matches_migrated_table(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url)

    with Session(engine) as session:
        session.add(
            CachedProduct(barcode="3017620422003", name="Nutella", fetched_at=datetime(2026, 1, 1))
        )
        session.commit()
        product = session.get(CachedProduct, "3017620422003")

    assert product.name == "Nutella"
    assert product.brand is None
    assert product.nutri_score is None
