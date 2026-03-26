"""add user_id column to trades and alert_configs

Revision ID: h9f3d5e6g7b8
Revises: g8e2c4d5f6a7
Create Date: 2026-03-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "h9f3d5e6g7b8"
down_revision = "g8e2c4d5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id to trades (nullable for backward compat with Telegram-created trades)
    op.add_column("trades", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.create_index("idx_trades_user_id", "trades", ["user_id"])

    # Add user_id to alert_configs (nullable for backward compat)
    op.add_column("alert_configs", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.create_index("idx_alert_configs_user_id", "alert_configs", ["user_id"])

    # Make telegram_chat_id nullable on alert_configs (web users may not have one)
    op.alter_column("alert_configs", "telegram_chat_id", nullable=True)

    # Add user_id to price_alerts (nullable for backward compat)
    op.add_column("price_alerts", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.create_index("idx_price_alerts_user_id", "price_alerts", ["user_id"])

    # Make telegram_chat_id nullable on price_alerts (web users may not have one)
    op.alter_column("price_alerts", "telegram_chat_id", nullable=True)


def downgrade() -> None:
    op.alter_column("price_alerts", "telegram_chat_id", nullable=False)
    op.drop_index("idx_price_alerts_user_id", table_name="price_alerts")
    op.drop_column("price_alerts", "user_id")
    op.alter_column("alert_configs", "telegram_chat_id", nullable=False)
    op.drop_index("idx_alert_configs_user_id", table_name="alert_configs")
    op.drop_column("alert_configs", "user_id")
    op.drop_index("idx_trades_user_id", table_name="trades")
    op.drop_column("trades", "user_id")
