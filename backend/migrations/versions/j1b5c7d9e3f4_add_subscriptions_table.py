"""Add subscriptions table.

Revision ID: j1b5c7d9e3f4
Revises: i0a4b6c8d2e3
Create Date: 2026-03-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "j1b5c7d9e3f4"
down_revision = "i0a4b6c8d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("razorpay_subscription_id", sa.String(100), nullable=True, unique=True),
        sa.Column("razorpay_customer_id", sa.String(100), nullable=True),
        sa.Column("amount_paise", sa.Integer, nullable=False, server_default="49900"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
