"""Add UNIQUE constraint on market_data(symbol, timestamp) and CHECK constraints.

Revision ID: a1b2c3d4e5f6
Revises: f7d1b2c3e4a5
Create Date: 2026-03-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f7d1b2c3e4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CRIT-11: Prevent duplicate candles for same symbol at same timestamp
    op.create_unique_constraint(
        "uq_market_data_symbol_timestamp",
        "market_data",
        ["symbol", "timestamp"],
    )

    # CRIT-12 (DB layer): CHECK constraint on signals.confidence
    op.execute(
        "ALTER TABLE signals ADD CONSTRAINT ck_signals_confidence "
        "CHECK (confidence >= 0 AND confidence <= 100)"
    )

    # CRIT-12 (DB layer): CHECK constraint on signals.market_type
    op.execute(
        "ALTER TABLE signals ADD CONSTRAINT ck_signals_market_type "
        "CHECK (market_type IN ('stock', 'crypto', 'forex'))"
    )

    # CRIT-12 (DB layer): CHECK constraint on signals.signal_type
    op.execute(
        "ALTER TABLE signals ADD CONSTRAINT ck_signals_signal_type "
        "CHECK (signal_type IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'))"
    )

    # CHECK constraint on market_data.market_type
    op.execute(
        "ALTER TABLE market_data ADD CONSTRAINT ck_market_data_market_type "
        "CHECK (market_type IN ('stock', 'crypto', 'forex'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market_data DROP CONSTRAINT IF EXISTS ck_market_data_market_type")
    op.execute("ALTER TABLE signals DROP CONSTRAINT IF EXISTS ck_signals_signal_type")
    op.execute("ALTER TABLE signals DROP CONSTRAINT IF EXISTS ck_signals_market_type")
    op.execute("ALTER TABLE signals DROP CONSTRAINT IF EXISTS ck_signals_confidence")
    op.drop_constraint("uq_market_data_symbol_timestamp", "market_data", type_="unique")
