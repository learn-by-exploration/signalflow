"""add news and event chain tables

Revision ID: e6c0a5d7b8f9
Revises: d5b9e3f4a6c7
Create Date: 2026-03-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = "e6c0a5d7b8f9"
down_revision = "d5b9e3f4a6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # News events — individual articles/headlines
    op.create_table(
        "news_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("market_type", sa.String(10), nullable=False),
        sa.Column("sentiment_direction", sa.String(10), nullable=True),
        sa.Column("impact_magnitude", sa.Integer, nullable=True),
        sa.Column("event_category", sa.String(50), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_news_events_symbol_time", "news_events", ["symbol", "fetched_at"])
    op.create_index("idx_news_events_market", "news_events", ["market_type", "fetched_at"])

    # Event entities — deduplicated real-world events
    op.create_table(
        "event_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("event_category", sa.String(50), nullable=False),
        sa.Column("affected_symbols", JSONB, server_default="[]"),
        sa.Column("affected_sectors", JSONB, server_default="[]"),
        sa.Column("impact_magnitude", sa.Integer, nullable=False, server_default="3"),
        sa.Column("sentiment_direction", sa.String(10), nullable=False, server_default="'neutral'"),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="50"),
        sa.Column("article_count", sa.Integer, server_default="1"),
        sa.Column("news_event_ids", JSONB, server_default="[]"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_event_entities_category", "event_entities", ["event_category"])
    op.create_index("idx_event_entities_active", "event_entities", ["expires_at"])

    # Causal links — directed edges between events
    op.create_table(
        "causal_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_event_id", UUID(as_uuid=True), sa.ForeignKey("event_entities.id"), nullable=False),
        sa.Column("target_event_id", UUID(as_uuid=True), sa.ForeignKey("event_entities.id"), nullable=False),
        sa.Column("relationship_type", sa.String(20), nullable=False, server_default="'causes'"),
        sa.Column("propagation_delay", sa.String(50), nullable=True),
        sa.Column("impact_decay", sa.Float, server_default="0.8"),
        sa.Column("confidence", sa.Integer, nullable=False, server_default="50"),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_causal_links_source", "causal_links", ["source_event_id"])
    op.create_index("idx_causal_links_target", "causal_links", ["target_event_id"])

    # Signal-news links — M:N join table
    op.create_table(
        "signal_news_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("signal_id", UUID(as_uuid=True), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("news_event_id", UUID(as_uuid=True), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_signal_news_links_signal", "signal_news_links", ["signal_id"])
    op.create_index("idx_signal_news_links_news", "signal_news_links", ["news_event_id"])

    # Event calendar — scheduled known events
    op.create_table(
        "event_calendar",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("affected_symbols", JSONB, server_default="[]"),
        sa.Column("impact_magnitude", sa.Integer, server_default="3"),
        sa.Column("is_recurring", sa.Boolean, server_default="false"),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("is_completed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_event_calendar_scheduled", "event_calendar", ["scheduled_at"])


def downgrade() -> None:
    op.drop_table("event_calendar")
    op.drop_table("signal_news_links")
    op.drop_table("causal_links")
    op.drop_table("event_entities")
    op.drop_table("news_events")
