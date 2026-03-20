"""add watchlist column to alert_configs

Revision ID: c4a8f2d1e3b5
Revises: b0396d5bb542
Create Date: 2026-03-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "c4a8f2d1e3b5"
down_revision = "b0396d5bb542"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alert_configs", sa.Column("watchlist", JSONB, nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("alert_configs", "watchlist")
