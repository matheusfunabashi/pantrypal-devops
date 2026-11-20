"""Create stock_targets.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    timestamp = sa.DateTime().with_variant(mssql.DATETIME2(), "mssql")
    utc_default = (
        "SYSUTCDATETIME()" if op.get_context().dialect.name == "mssql" else "CURRENT_TIMESTAMP"
    )

    op.create_table(
        "stock_targets",
        sa.Column("barcode", sa.NVARCHAR(14), primary_key=True),
        sa.Column("name", sa.NVARCHAR(255), nullable=False),
        sa.Column("target", sa.Integer, nullable=False),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text(utc_default)),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.text(utc_default)),
        sa.CheckConstraint("target BETWEEN 1 AND 999", name="ck_stock_targets_target"),
    )


def downgrade() -> None:
    op.drop_table("stock_targets")
