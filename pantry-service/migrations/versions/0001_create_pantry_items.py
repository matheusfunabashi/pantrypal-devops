"""create pantry_items

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
    timestamp = sa.DateTime().with_variant(mssql.DATETIME2(), "mssql")
    # Default to the current UTC time. SYSUTCDATETIME() is SQL Server only, so the
    # tests on SQLite use CURRENT_TIMESTAMP, which SQLite also stores in UTC.
    if op.get_context().dialect.name == "mssql":
        utc_now = sa.text("SYSUTCDATETIME()")
    else:
        utc_now = sa.text("CURRENT_TIMESTAMP")

    op.create_table(
        "pantry_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        # A string, not a number, so leading zeros in barcodes are kept.
        sa.Column("barcode", sa.NVARCHAR(14), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("name_snapshot", sa.NVARCHAR(255), nullable=False),
        sa.Column("brand_snapshot", sa.NVARCHAR(255), nullable=True),
        sa.Column("image_url_snapshot", sa.NVARCHAR(1000), nullable=True),
        sa.Column("nutri_score_snapshot", sa.CHAR(1), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=utc_now),
        sa.Column("updated_at", timestamp, nullable=False, server_default=utc_now),
        sa.UniqueConstraint("barcode", name="uq_pantry_items_barcode"),
        sa.CheckConstraint("quantity BETWEEN 1 AND 999", name="ck_pantry_items_quantity"),
        sa.CheckConstraint(
            "nutri_score_snapshot IN ('a','b','c','d','e')", name="ck_pantry_items_nutri"
        ),
    )


def downgrade() -> None:
    op.drop_table("pantry_items")
