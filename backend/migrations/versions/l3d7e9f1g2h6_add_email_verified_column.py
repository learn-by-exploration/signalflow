"""Add email_verified column to users table.

Revision ID: l3d7e9f1g2h6
Revises: k2c6d8e0f4g5
Create Date: 2026-04-03 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "l3d7e9f1g2h6"
down_revision = "k2c6d8e0f4g5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified")
