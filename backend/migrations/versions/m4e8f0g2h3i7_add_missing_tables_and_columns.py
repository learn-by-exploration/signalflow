"""Add missing tables and columns: signal_feedback, confidence_calibration,
signal_shares.expires_at, signal_shares.created_by.

Revision ID: m4e8f0g2h3i7
Revises: l3d7e9f1g2h6
Create Date: 2026-04-03 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "m4e8f0g2h3i7"
down_revision = "l3d7e9f1g2h6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- signal_feedback table (model existed, no migration) --
    op.create_table(
        "signal_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    # -- confidence_calibration table (model existed, no migration) --
    op.create_table(
        "confidence_calibration",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("score_bucket", sa.Integer, nullable=False),
        sa.Column("total_signals", sa.Integer, server_default="0"),
        sa.Column("successful_signals", sa.Integer, server_default="0"),
        sa.Column("calibrated_probability", sa.Numeric(5, 4), nullable=True),
        sa.Column("market_type", sa.String(10), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.func.now()),
        sa.UniqueConstraint("score_bucket", "market_type", name="uq_bucket_market"),
    )

    # -- signal_shares: add missing columns --
    op.add_column(
        "signal_shares",
        sa.Column("created_by", sa.String(36), nullable=True),
    )
    op.add_column(
        "signal_shares",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("signal_shares", "expires_at")
    op.drop_column("signal_shares", "created_by")
    op.drop_table("confidence_calibration")
    op.drop_table("signal_feedback")
