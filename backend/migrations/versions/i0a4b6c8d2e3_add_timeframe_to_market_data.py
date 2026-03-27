"""Add timeframe column to market_data.

Revision ID: i0a4b6c8d2e3
Revises: h9f3d5e6g7b8
Create Date: 2026-03-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "i0a4b6c8d2e3"
down_revision = "h9f3d5e6g7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timeframe column with default '1d' for existing data
    op.add_column(
        "market_data",
        sa.Column("timeframe", sa.String(10), nullable=False, server_default="1d"),
    )
    # Unique constraint to prevent duplicate data per symbol/timestamp/timeframe/market
    op.create_index(
        "idx_market_data_unique",
        "market_data",
        ["symbol", "timestamp", "timeframe", "market_type"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_market_data_unique", table_name="market_data")
    op.drop_column("market_data", "timeframe")
