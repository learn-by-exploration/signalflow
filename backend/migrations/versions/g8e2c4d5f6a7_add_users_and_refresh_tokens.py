"""add users and refresh_tokens tables

Revision ID: g8e2c4d5f6a7
Revises: f7d1b2c3e4a5
Create Date: 2026-03-27 10:00:00.000000

"""
import uuid

import bcrypt
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "g8e2c4d5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt for seed data."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def upgrade() -> None:
    # ── users table ──
    users_table = op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger, unique=True, nullable=True),
        sa.Column("tier", sa.String(10), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── refresh_tokens table ──
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("is_revoked", sa.Boolean, server_default="false", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Seed admin and demo users ──
    op.bulk_insert(
        users_table,
        [
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "email": "admin@signalflow.ai",
                "password_hash": _hash_password("signalflow123"),
                "tier": "pro",
                "is_active": True,
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
                "email": "demo@signalflow.ai",
                "password_hash": _hash_password("demo123"),
                "tier": "free",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
