"""Shared test fixtures for SignalFlow backend tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

# ── Teach SQLite to render PostgreSQL-specific types ──
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"

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

    # Import ALL models so Base.metadata.create_all creates all tables
    import app.models.alert_config  # noqa: F401
    import app.models.backtest  # noqa: F401
    import app.models.market_data  # noqa: F401
    import app.models.price_alert  # noqa: F401
    import app.models.signal  # noqa: F401
    import app.models.signal_history  # noqa: F401
    import app.models.signal_share  # noqa: F401
    import app.models.trade  # noqa: F401

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
async def db_engine_and_session():
    """Provide both engine and session factory for API tests that need DB override."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.database import Base

    # Import ALL models so Base.metadata.create_all creates all tables
    import app.models.alert_config  # noqa: F401
    import app.models.backtest  # noqa: F401
    import app.models.market_data  # noqa: F401
    import app.models.price_alert  # noqa: F401
    import app.models.signal  # noqa: F401
    import app.models.signal_history  # noqa: F401
    import app.models.signal_share  # noqa: F401
    import app.models.trade  # noqa: F401

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine, session_factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_db(db_engine_and_session):
    """A test DB pre-seeded with signals, history, market data, trades, and alert configs.

    Returns a session factory for use in API test overrides.
    """
    engine, session_factory = db_engine_and_session
    async with session_factory() as session:
        from app.models.alert_config import AlertConfig
        from app.models.market_data import MarketData
        from app.models.signal import Signal
        from app.models.signal_history import SignalHistory
        from app.models.trade import Trade

        now = datetime.now(timezone.utc)

        # -- Signals --
        sig1_id = uuid4()
        sig2_id = uuid4()
        sig3_id = uuid4()
        sig4_id = uuid4()
        signals = [
            Signal(id=sig1_id, symbol="HDFCBANK.NS", market_type="stock", signal_type="STRONG_BUY",
                   confidence=92, current_price=Decimal("1678.90"), target_price=Decimal("1780.00"),
                   stop_loss=Decimal("1630.00"), timeframe="2-4 weeks", is_active=True,
                   ai_reasoning="Credit growth accelerating.", technical_data={"rsi": {"value": 62.7, "signal": "neutral"}},
                   sentiment_data={"score": 85}, created_at=now),
            Signal(id=sig2_id, symbol="BTCUSDT", market_type="crypto", signal_type="BUY",
                   confidence=78, current_price=Decimal("97842.00"), target_price=Decimal("105000.00"),
                   stop_loss=Decimal("93500.00"), timeframe="1-3 weeks", is_active=True,
                   ai_reasoning="ETF inflows strong.", technical_data={"rsi": {"value": 68.5, "signal": "neutral"}},
                   sentiment_data=None, created_at=now),
            Signal(id=sig3_id, symbol="EUR/USD", market_type="forex", signal_type="SELL",
                   confidence=65, current_price=Decimal("1.0854"), target_price=Decimal("1.0700"),
                   stop_loss=Decimal("1.0950"), timeframe="1-2 weeks", is_active=True,
                   ai_reasoning="Dollar strength anticipated.", technical_data={"rsi": {"value": 45, "signal": "neutral"}},
                   sentiment_data=None, created_at=now),
            Signal(id=sig4_id, symbol="TCS.NS", market_type="stock", signal_type="HOLD",
                   confidence=55, current_price=Decimal("3962.40"), target_price=Decimal("4050.00"),
                   stop_loss=Decimal("3850.00"), timeframe="2-3 weeks", is_active=False,
                   ai_reasoning="Range-bound trading.", technical_data={"rsi": {"value": 50, "signal": "neutral"}},
                   sentiment_data=None, created_at=now),
        ]
        session.add_all(signals)

        # -- Signal History --
        histories = [
            SignalHistory(id=uuid4(), signal_id=sig4_id, outcome="hit_target",
                         exit_price=Decimal("4050.00"), return_pct=Decimal("2.21"),
                         resolved_at=now, created_at=now),
            SignalHistory(id=uuid4(), signal_id=sig4_id, outcome="hit_stop",
                         exit_price=Decimal("3850.00"), return_pct=Decimal("-2.84"),
                         resolved_at=now, created_at=now),
            SignalHistory(id=uuid4(), signal_id=sig4_id, outcome="expired",
                         exit_price=Decimal("3960.00"), return_pct=Decimal("-0.06"),
                         resolved_at=now, created_at=now),
            SignalHistory(id=uuid4(), signal_id=sig4_id, outcome="pending",
                         exit_price=None, return_pct=None,
                         resolved_at=None, created_at=now),
        ]
        session.add_all(histories)

        # -- Market Data --
        market_data = [
            MarketData(id=1, symbol="HDFCBANK.NS", market_type="stock",
                       open=Decimal("1670.00"), high=Decimal("1690.50"),
                       low=Decimal("1665.25"), close=Decimal("1678.90"),
                       volume=Decimal("15234567"), timestamp=now),
            MarketData(id=2, symbol="BTCUSDT", market_type="crypto",
                       open=Decimal("95000.00"), high=Decimal("98500.00"),
                       low=Decimal("94800.00"), close=Decimal("97842.00"),
                       volume=Decimal("45000"), timestamp=now),
            MarketData(id=3, symbol="EUR/USD", market_type="forex",
                       open=Decimal("1.0880"), high=Decimal("1.0910"),
                       low=Decimal("1.0840"), close=Decimal("1.0854"),
                       volume=None, timestamp=now),
        ]
        session.add_all(market_data)

        # -- Trades --
        trades = [
            Trade(telegram_chat_id=12345, symbol="HDFCBANK.NS", market_type="stock",
                  side="buy", quantity=Decimal("10"), price=Decimal("1650.00"), created_at=now),
            Trade(telegram_chat_id=12345, symbol="BTCUSDT", market_type="crypto",
                  side="buy", quantity=Decimal("0.5"), price=Decimal("95000.00"), created_at=now),
        ]
        session.add_all(trades)

        # -- Alert Config --
        alert_config = AlertConfig(
            telegram_chat_id=12345, username="testuser",
            markets=["stock", "crypto", "forex"], min_confidence=60,
            signal_types=["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
            watchlist=["HDFCBANK.NS", "BTCUSDT"],
        )
        session.add(alert_config)

        await session.commit()

    yield session_factory


@pytest_asyncio.fixture
async def test_client(seeded_db):
    """HTTP test client with the database overridden to the seeded test DB."""
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    async def override_get_db():
        async with seeded_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


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
