"""Tests for signal_feedback API endpoints."""

from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import AuthContext, get_current_user, require_auth
from app.database import get_db


@pytest_asyncio.fixture
async def feedback_client():
    """HTTP test client with seeded DB + signal_feedback table."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.database import Base
    from app.main import app as fastapi_app
    from app.models.signal import Signal
    from app.models.signal_feedback import SignalFeedback  # noqa: F401

    # Import all models for table creation
    import app.models  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed a signal
    signal_id = uuid4()
    async with session_factory() as session:
        sig = Signal(
            id=signal_id,
            symbol="HDFCBANK.NS",
            market_type="stock",
            signal_type="STRONG_BUY",
            confidence=92,
            current_price=Decimal("1678.90"),
            target_price=Decimal("1780.00"),
            stop_loss=Decimal("1630.00"),
            timeframe="2-4 weeks",
            is_active=True,
            ai_reasoning="Test signal.",
            technical_data={"rsi": {"value": 62.7}},
        )
        session.add(sig)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_require_auth() -> AuthContext:
        return AuthContext(
            auth_type="api_key",
            user_id="00000000-0000-0000-0000-000000000099",
            tier="pro",
        )

    async def override_get_current_user() -> AuthContext:
        return AuthContext(
            auth_type="jwt",
            user_id="00000000-0000-0000-0000-000000000099",
            telegram_chat_id=12345,
            tier="pro",
        )

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[require_auth] = override_require_auth
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, signal_id
    fastapi_app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_submit_feedback_took(feedback_client):
    """Test submitting 'took' feedback on a signal."""
    client, signal_id = feedback_client
    resp = await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "took", "entry_price": "1680.00", "notes": "Looks promising"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["action"] == "took"
    assert data["signal_id"] == str(signal_id)
    assert data["entry_price"] == "1680.00000000"
    assert data["notes"] == "Looks promising"


@pytest.mark.asyncio
async def test_submit_feedback_skipped(feedback_client):
    """Test submitting 'skipped' feedback."""
    client, signal_id = feedback_client
    resp = await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "skipped"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["action"] == "skipped"


@pytest.mark.asyncio
async def test_submit_feedback_watching(feedback_client):
    """Test submitting 'watching' feedback."""
    client, signal_id = feedback_client
    resp = await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "watching"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["action"] == "watching"


@pytest.mark.asyncio
async def test_submit_feedback_invalid_action(feedback_client):
    """Test that invalid action values are rejected."""
    client, signal_id = feedback_client
    resp = await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "invalid_action"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_feedback(feedback_client):
    """Test retrieving feedback for a signal."""
    client, signal_id = feedback_client
    # Submit first
    await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "took", "entry_price": "1680.00"},
    )
    # Retrieve
    resp = await client.get(f"/api/v1/signals/{signal_id}/feedback")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["action"] == "took"
    assert data["signal_id"] == str(signal_id)


@pytest.mark.asyncio
async def test_get_feedback_none(feedback_client):
    """Test retrieving feedback when none exists."""
    client, signal_id = feedback_client
    resp = await client.get(f"/api/v1/signals/{signal_id}/feedback")
    assert resp.status_code == 200
    assert resp.json()["data"] is None


@pytest.mark.asyncio
async def test_feedback_notes_max_length(feedback_client):
    """Test that notes exceeding max length are rejected."""
    client, signal_id = feedback_client
    resp = await client.post(
        f"/api/v1/signals/{signal_id}/feedback",
        json={"action": "took", "notes": "x" * 501},
    )
    assert resp.status_code == 422
