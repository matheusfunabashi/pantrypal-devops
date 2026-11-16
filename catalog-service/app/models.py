from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CachedProduct(Base):
    """A product fetched from Open Food Facts. fetched_at drives the 7-day cache rule."""

    __tablename__ = "cached_products"
    __table_args__ = (
        CheckConstraint("nutri_score IN ('a','b','c','d','e')", name="ck_cached_products_nutri"),
    )

    barcode: Mapped[str] = mapped_column(String(14), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    nutri_score: Mapped[str | None] = mapped_column(String(1))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime().with_variant(mssql.DATETIME2(), "mssql")
    )
