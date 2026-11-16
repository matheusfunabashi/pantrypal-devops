from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import PantryItem


def test_model_matches_migrated_table(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url)

    with Session(engine) as session:
        session.add(PantryItem(barcode="3017620422003", quantity=2, name_snapshot="Nutella"))
        session.commit()
        item = session.query(PantryItem).one()

        assert item.id is not None
        assert item.quantity == 2
        assert item.brand_snapshot is None
        assert item.nutri_score_snapshot is None
        assert item.created_at is not None
        assert item.updated_at is not None
