from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# DATETIME2 on SQL Server, a plain DateTime elsewhere (SQLite in the tests).
Timestamp = DateTime().with_variant(mssql.DATETIME2(), "mssql")


class PantryItem(Base):
    """One product in the user's pantry.

    The *_snapshot columns copy the product details from the Catalog Service when
    the item is added, so the pantry still shows them if Catalog is down.
    """

    __tablename__ = "pantry_items"
    __table_args__ = (
        CheckConstraint("quantity BETWEEN 1 AND 999", name="ck_pantry_items_quantity"),
        CheckConstraint(
            "nutri_score_snapshot IN ('a','b','c','d','e')", name="ck_pantry_items_nutri"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    barcode: Mapped[str] = mapped_column(String(14), unique=True)
    quantity: Mapped[int] = mapped_column(Integer)
    name_snapshot: Mapped[str] = mapped_column(String(255))
    brand_snapshot: Mapped[str | None] = mapped_column(String(255))
    image_url_snapshot: Mapped[str | None] = mapped_column(String(1000))
    nutri_score_snapshot: Mapped[str | None] = mapped_column(String(1))
    created_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(Timestamp, server_default=func.now())
