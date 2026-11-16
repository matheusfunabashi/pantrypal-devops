"""create cached_products

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cached_products",
        sa.Column("barcode", sa.NVARCHAR(14), primary_key=True),
        sa.Column("name", sa.NVARCHAR(255), nullable=False),
        sa.Column("brand", sa.NVARCHAR(255), nullable=True),
        sa.Column("image_url", sa.NVARCHAR(1000), nullable=True),
        sa.Column("nutri_score", sa.CHAR(1), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime().with_variant(mssql.DATETIME2(), "mssql"),
            nullable=False,
        ),
        sa.CheckConstraint("nutri_score IN ('a','b','c','d','e')", name="ck_cached_products_nutri"),
    )


def downgrade() -> None:
    op.drop_table("cached_products")
