"""Shared test fixtures for SignalFlow backend tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

# Use an in-memory SQLite for fast unit tests (swap for test PG in CI)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator:
    """Provide a test database session.

    Only used by integration tests that import this fixture explicitly.
    Requires PostgreSQL (or a JSONB-capable backend).
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.database import Base

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator:
    """Provide an async HTTP test client with DB override.

    Only used by API integration tests.
    """
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_market_data() -> dict:
    """Sample OHLCV data for testing."""
    return {
        "symbol": "HDFCBANK",
        "market_type": "stock",
        "open": Decimal("1670.00"),
        "high": Decimal("1690.50"),
        "low": Decimal("1665.25"),
        "close": Decimal("1678.90"),
        "volume": Decimal("15234567"),
    }


@pytest.fixture
def sample_signal() -> dict:
    """Sample signal data for testing."""
    return {
        "id": uuid4(),
        "symbol": "HDFCBANK",
        "market_type": "stock",
        "signal_type": "STRONG_BUY",
        "confidence": 92,
        "current_price": Decimal("1678.90"),
        "target_price": Decimal("1780.00"),
        "stop_loss": Decimal("1630.00"),
        "timeframe": "2-4 weeks",
        "ai_reasoning": "Credit growth accelerating. NIM expansion confirmed.",
        "technical_data": {"rsi": {"value": 62.7, "signal": "neutral"}},
        "sentiment_data": {"score": 85, "key_factors": ["credit growth"]},
    }
