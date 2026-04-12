"""Add user_id to backtest_runs for ownership tracking.

Revision ID: n5f9g1h3i4j8
Revises: m4e8f0g2h3i7
Create Date: 2026-04-12 21:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "n5f9g1h3i4j8"
down_revision = "m4e8f0g2h3i7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backtest_runs",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_backtest_runs_user_id", "backtest_runs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_backtest_runs_user_id", table_name="backtest_runs")
    op.drop_column("backtest_runs", "user_id")
