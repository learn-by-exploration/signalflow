"""Add seo_pages table.

Revision ID: k2c6d8e0f4g5
Revises: j1b5c7d9e3f4
Create Date: 2026-03-27 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "k2c6d8e0f4g5"
down_revision = "j1b5c7d9e3f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seo_pages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("market_type", sa.String(10), nullable=False),
        sa.Column("meta_description", sa.String(300), nullable=True),
        sa.Column("is_published", sa.Boolean(), default=True),
        sa.Column("page_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_seo_pages_slug", "seo_pages", ["slug"])
    op.create_index(
        "idx_seo_pages_market_date", "seo_pages", ["market_type", "page_date"]
    )


def downgrade() -> None:
    op.drop_index("idx_seo_pages_market_date", table_name="seo_pages")
    op.drop_index("idx_seo_pages_slug", table_name="seo_pages")
    op.drop_table("seo_pages")
