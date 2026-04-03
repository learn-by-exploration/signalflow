"""Alembic environment configuration for async SQLAlchemy."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.database import Base
from app.models import (  # noqa: F401
    MarketData, Signal, AlertConfig, SignalHistory,
    PriceAlert, User, RefreshToken, Trade, SignalShare,
    BacktestRun, NewsEvent, EventEntity, CausalLink,
    SignalNewsLink, EventCalendar, SignalFeedback,
    SeoPage, Subscription, ConfidenceCalibration,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use sync URL for migrations (Alembic doesn't support async natively)
db_url = os.environ.get(
    "DATABASE_URL_SYNC",
    config.get_main_option("sqlalchemy.url"),
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Supports two modes:
    1. Normal CLI usage: creates engine from db_url
    2. Programmatic usage (e.g., tests): reuses connection from config.attributes
    """
    # Standard Alembic pattern: allow callers to pass an existing connection
    connectable = config.attributes.get("connection")

    if connectable is None:
        connectable = create_engine(db_url, poolclass=pool.NullPool)

    # If we were given a Connection, use it directly; otherwise connect()
    if hasattr(connectable, "connect"):
        # It's an engine — we need to open a connection
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    else:
        # It's already a Connection object
        context.configure(connection=connectable, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
