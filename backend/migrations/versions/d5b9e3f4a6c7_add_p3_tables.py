"""add P3 tables: price_alerts, trades, signal_shares, backtest_runs

Revision ID: d5b9e3f4a6c7
Revises: c4a8f2d1e3b5
Create Date: 2026-03-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = "d5b9e3f4a6c7"
down_revision = "c4a8f2d1e3b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Price alerts
    op.create_table(
        "price_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("market_type", sa.String(10), nullable=False),
        sa.Column("condition", sa.String(10), nullable=False),
        sa.Column("threshold", sa.Numeric(20, 8), nullable=False),
        sa.Column("is_triggered", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Trades (portfolio)
    op.create_table(
        "trades",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_chat_id", sa.BigInteger, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("market_type", sa.String(10), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Signal shares
    op.create_table(
        "signal_shares",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("signal_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Backtest runs
    op.create_table(
        "backtest_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("market_type", sa.String(10), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_signals", sa.Integer, server_default="0"),
        sa.Column("wins", sa.Integer, server_default="0"),
        sa.Column("losses", sa.Integer, server_default="0"),
        sa.Column("win_rate", sa.Float, server_default="0"),
        sa.Column("avg_return_pct", sa.Float, server_default="0"),
        sa.Column("total_return_pct", sa.Float, server_default="0"),
        sa.Column("max_drawdown_pct", sa.Float, server_default="0"),
        sa.Column("parameters", JSONB, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="'pending'"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("backtest_runs")
    op.drop_table("signal_shares")
    op.drop_table("trades")
    op.drop_table("price_alerts")
