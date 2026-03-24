"""add missing columns to news/event tables

Revision ID: f7d1b2c3e4a5
Revises: e6c0a5d7b8f9
Create Date: 2026-03-24 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "f7d1b2c3e4a5"
down_revision = "e6c0a5d7b8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # event_entities — missing columns
    op.add_column("event_entities", sa.Column("source_category", sa.String(30), nullable=True))
    op.add_column("event_entities", sa.Column("affected_markets", JSONB, nullable=True))
    op.add_column("event_entities", sa.Column("geographic_scope", sa.String(20), nullable=True))
    op.add_column("event_entities", sa.Column("is_active", sa.Boolean, server_default="true", nullable=False))

    # news_events — missing is_active
    op.add_column("news_events", sa.Column("is_active", sa.Boolean, server_default="true", nullable=False))

    # event_calendar — missing columns
    op.add_column("event_calendar", sa.Column("description", sa.Text, nullable=True))
    op.add_column("event_calendar", sa.Column("affected_markets", JSONB, nullable=True))
    op.add_column("event_calendar", sa.Column("recurrence_rule", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("event_calendar", "recurrence_rule")
    op.drop_column("event_calendar", "affected_markets")
    op.drop_column("event_calendar", "description")
    op.drop_column("news_events", "is_active")
    op.drop_column("event_entities", "is_active")
    op.drop_column("event_entities", "geographic_scope")
    op.drop_column("event_entities", "affected_markets")
    op.drop_column("event_entities", "source_category")
