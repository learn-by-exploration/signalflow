"""Tests for the news intelligence and event chain features."""

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

# ── Event Chain Engine Tests ──


class TestComputeEventImpact:
    """Tests for compute_event_impact decay function."""

    def test_no_decay_at_time_zero(self):
        from app.services.ai_engine.event_chain import compute_event_impact

        result = compute_event_impact(1.0, 0.0, "earnings")
        assert abs(result - 1.0) < 1e-6

    def test_half_life_decay(self):
        from app.services.ai_engine.event_chain import compute_event_impact, DECAY_HALF_LIVES

        half_life = DECAY_HALF_LIVES["earnings"]
        result = compute_event_impact(1.0, half_life, "earnings")
        assert abs(result - 0.5) < 1e-6

    def test_full_decay_after_long_time(self):
        from app.services.ai_engine.event_chain import compute_event_impact

        result = compute_event_impact(1.0, 10000.0, "technical")
        assert result < 0.01

    def test_magnitude_scales_linearly(self):
        from app.services.ai_engine.event_chain import compute_event_impact

        result_half = compute_event_impact(0.5, 10.0, "sector")
        result_full = compute_event_impact(1.0, 10.0, "sector")
        assert abs(result_full - 2.0 * result_half) < 1e-6

    def test_unknown_category_uses_default_half_life(self):
        from app.services.ai_engine.event_chain import compute_event_impact

        # Unknown category should still work (defaults to 48h half-life)
        result = compute_event_impact(1.0, 48.0, "unknown_category")
        assert abs(result - 0.5) < 1e-6


class TestComputeChainScore:
    """Tests for compute_chain_score aggregation."""

    def test_empty_events_returns_neutral(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        result = compute_chain_score([])
        assert result["chain_score"] == 50
        assert result["chain_count"] == 0
        assert result["chain_net_direction"] == 0.0

    def test_single_bullish_event(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        events = [
            {
                "direction": "bullish",
                "magnitude": 0.8,
                "confidence": 80,
                "hours_since": 0,
                "category": "earnings",
            }
        ]
        result = compute_chain_score(events)
        assert result["chain_score"] > 50  # bullish → above 50
        assert result["chain_count"] == 1
        assert result["chain_net_direction"] > 0

    def test_single_bearish_event(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        events = [
            {
                "direction": "bearish",
                "magnitude": 0.8,
                "confidence": 80,
                "hours_since": 0,
                "category": "earnings",
            }
        ]
        result = compute_chain_score(events)
        assert result["chain_score"] < 50  # bearish → below 50
        assert result["chain_net_direction"] < 0

    def test_mixed_events_lower_consensus(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        events = [
            {"direction": "bullish", "magnitude": 0.7, "confidence": 70, "hours_since": 0, "category": "sector"},
            {"direction": "bearish", "magnitude": 0.7, "confidence": 70, "hours_since": 0, "category": "sector"},
        ]
        result = compute_chain_score(events)
        # Mixed → consensus should be 0.0 (evenly split)
        assert result["chain_consensus"] == 0.0
        # Score should be close to 50
        assert 40 <= result["chain_score"] <= 60

    def test_decayed_event_has_less_impact(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        fresh = [{"direction": "bullish", "magnitude": 0.8, "confidence": 80, "hours_since": 0, "category": "earnings"}]
        stale = [{"direction": "bullish", "magnitude": 0.8, "confidence": 80, "hours_since": 500, "category": "earnings"}]

        fresh_result = compute_chain_score(fresh)
        stale_result = compute_chain_score(stale)
        # Fresh event should produce higher chain_score
        assert fresh_result["chain_score"] >= stale_result["chain_score"]

    def test_score_bounded_0_to_100(self):
        from app.services.ai_engine.event_chain import compute_chain_score

        extreme_bullish = [
            {"direction": "bullish", "magnitude": 1.0, "confidence": 100, "hours_since": 0, "category": "macro_policy"}
            for _ in range(10)
        ]
        result = compute_chain_score(extreme_bullish)
        assert 0 <= result["chain_score"] <= 100


class TestSectorMapping:
    """Tests for sector <-> symbol mapping."""

    def test_get_sectors_for_known_symbol(self):
        from app.services.ai_engine.event_chain import get_sectors_for_symbol

        sectors = get_sectors_for_symbol("HDFCBANK.NS")
        assert "banking" in sectors

    def test_get_sectors_for_unknown_symbol(self):
        from app.services.ai_engine.event_chain import get_sectors_for_symbol

        sectors = get_sectors_for_symbol("UNKNOWN")
        assert sectors == []

    def test_propagate_event_excludes_origin(self):
        from app.services.ai_engine.event_chain import propagate_event_to_symbols

        symbols = propagate_event_to_symbols(["banking"], "HDFCBANK.NS")
        assert "HDFCBANK.NS" not in symbols
        assert "ICICIBANK.NS" in symbols

    def test_propagate_event_multiple_sectors(self):
        from app.services.ai_engine.event_chain import propagate_event_to_symbols

        symbols = propagate_event_to_symbols(["banking", "it"], "HDFCBANK.NS")
        assert "TCS.NS" in symbols
        assert "INFY.NS" in symbols
        assert "HDFCBANK.NS" not in symbols


# ── Scorer Tests ──


class TestChainAwareScorer:
    """Tests for the updated chain-aware scoring."""

    def test_no_sentiment_caps_at_60(self):
        from app.services.signal_gen.scorer import compute_final_confidence

        tech_data = {
            "rsi": {"signal": "buy", "strength": 90},
            "macd": {"signal": "buy", "strength": 90},
            "bollinger": {"signal": "buy", "strength": 90},
            "volume": {"signal": "buy", "strength": 90},
            "sma_cross": {"signal": "buy", "strength": 90},
        }
        confidence, signal_type = compute_final_confidence(tech_data, None)
        assert confidence <= 60

    def test_with_sentiment_no_chains_uses_60_40(self):
        from app.services.signal_gen.scorer import compute_final_confidence

        tech_data = {
            "rsi": {"signal": "buy", "strength": 80},
            "macd": {"signal": "buy", "strength": 80},
            "bollinger": {"signal": "buy", "strength": 80},
            "volume": {"signal": "buy", "strength": 80},
            "sma_cross": {"signal": "buy", "strength": 80},
        }
        # Sentiment without events → 60/40 fallback
        sentiment = {"sentiment_score": 80, "confidence_in_analysis": 70}
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence > 60
        assert signal_type in ("STRONG_BUY", "BUY")

    def test_with_chain_events_uses_new_formula(self):
        from app.services.signal_gen.scorer import compute_final_confidence

        tech_data = {
            "rsi": {"signal": "buy", "strength": 70},
            "macd": {"signal": "buy", "strength": 70},
            "bollinger": {"signal": "neutral", "strength": 50},
            "volume": {"signal": "buy", "strength": 60},
            "sma_cross": {"signal": "buy", "strength": 70},
        }
        sentiment = {
            "sentiment_score": 75,
            "confidence_in_analysis": 80,
            "events": [
                {
                    "sentiment_direction": "bullish",
                    "impact_magnitude": 4,
                    "confidence": 80,
                    "hours_since": 2,
                    "event_category": "earnings",
                }
            ],
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence >= 50
        # Should be actionable
        assert signal_type in ("STRONG_BUY", "BUY", "HOLD")

    def test_extract_chain_events_from_sentiment(self):
        from app.services.signal_gen.scorer import _extract_chain_events

        sentiment = {
            "events": [
                {"sentiment_direction": "bullish", "impact_magnitude": 4, "confidence": 80, "hours_since": 1, "event_category": "earnings"},
                {"sentiment_direction": "bearish", "impact_magnitude": 2, "confidence": 60, "hours_since": 5, "event_category": "sector"},
            ]
        }
        chain_events = _extract_chain_events(sentiment)
        assert len(chain_events) == 2
        assert chain_events[0]["direction"] == "bullish"
        assert chain_events[0]["magnitude"] == 0.8  # 4/5
        assert chain_events[1]["direction"] == "bearish"

    def test_extract_chain_events_empty(self):
        from app.services.signal_gen.scorer import _extract_chain_events

        assert _extract_chain_events({}) == []
        assert _extract_chain_events({"events": []}) == []


# ── News API Tests ──


@pytest.mark.asyncio
async def test_news_list_endpoint(test_client):
    """GET /api/v1/news returns news list."""
    response = await test_client.get("/api/v1/news")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data


@pytest.mark.asyncio
async def test_news_events_endpoint(test_client):
    """GET /api/v1/news/events returns event entities."""
    response = await test_client.get("/api/v1/news/events")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_news_calendar_endpoint(test_client):
    """GET /api/v1/news/calendar returns calendar events."""
    response = await test_client.get("/api/v1/news/calendar")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_news_calendar_create(test_client):
    """POST /api/v1/news/calendar creates a calendar event."""
    payload = {
        "title": "RBI MPC Meeting",
        "event_type": "macro_policy",
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "affected_symbols": ["HDFCBANK.NS", "SBIN.NS"],
        "impact_magnitude": 4,
    }
    response = await test_client.post("/api/v1/news/calendar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "RBI MPC Meeting"


@pytest.mark.asyncio
async def test_signal_detail_includes_news(test_client):
    """GET /api/v1/signals/{id} returns news context."""
    # Get a signal first
    signals_resp = await test_client.get("/api/v1/signals")
    signals = signals_resp.json()["data"]
    if signals:
        signal_id = signals[0]["id"]
        resp = await test_client.get(f"/api/v1/signals/{signal_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "news" in data  # news key always present, may be empty


@pytest.mark.asyncio
async def test_news_chains_endpoint(test_client):
    """GET /api/v1/news/chains/{symbol} returns causal chains."""
    response = await test_client.get("/api/v1/news/chains/HDFCBANK.NS")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


# ── Model Tests ──


@pytest.mark.asyncio
async def test_news_event_model(db_session):
    """Test NewsEvent can be created and queried."""
    from app.models.news_event import NewsEvent

    ne = NewsEvent(
        headline="RBI keeps repo rate unchanged at 6.5%",
        source="Reuters",
        source_url="https://example.com/article",
        symbol="HDFCBANK.NS",
        market_type="stock",
        sentiment_direction="bullish",
        impact_magnitude=4,
        event_category="macro_policy",
    )
    db_session.add(ne)
    await db_session.flush()

    from sqlalchemy import select
    result = await db_session.execute(select(NewsEvent).where(NewsEvent.symbol == "HDFCBANK.NS"))
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.headline == "RBI keeps repo rate unchanged at 6.5%"
    assert found.source == "Reuters"


@pytest.mark.asyncio
async def test_event_entity_model(db_session):
    """Test EventEntity can be created."""
    from app.models.event_entity import EventEntity

    ee = EventEntity(
        title="RBI Monetary Policy Decision",
        description="Central bank maintained status quo",
        event_category="macro_policy",
        affected_symbols=["HDFCBANK.NS", "SBIN.NS"],
        affected_sectors=["banking"],
        impact_magnitude=4,
        sentiment_direction="bullish",
        confidence=85,
        article_count=3,
    )
    db_session.add(ee)
    await db_session.flush()

    from sqlalchemy import select
    result = await db_session.execute(select(EventEntity))
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.title == "RBI Monetary Policy Decision"


@pytest.mark.asyncio
async def test_event_calendar_model(db_session):
    """Test EventCalendar can be created."""
    from app.models.event_calendar import EventCalendar

    ec = EventCalendar(
        title="FOMC Meeting",
        event_type="macro_policy",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=14),
        affected_symbols=["EUR/USD", "GBP/USD"],
        impact_magnitude=5,
        is_recurring=True,
    )
    db_session.add(ec)
    await db_session.flush()

    from sqlalchemy import select
    result = await db_session.execute(select(EventCalendar))
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.title == "FOMC Meeting"
    assert found.is_recurring is True


@pytest.mark.asyncio
async def test_signal_news_link_model(db_session):
    """Test SignalNewsLink join table."""
    from app.models.news_event import NewsEvent
    from app.models.signal import Signal
    from app.models.signal_news_link import SignalNewsLink

    # Create a signal
    sig = Signal(
        symbol="BTCUSDT",
        market_type="crypto",
        signal_type="BUY",
        confidence=75,
        current_price=Decimal("97000.00"),
        target_price=Decimal("105000.00"),
        stop_loss=Decimal("93000.00"),
        timeframe="1-2 weeks",
        ai_reasoning="Strong momentum.",
        technical_data={"rsi": {"value": 65}},
    )
    db_session.add(sig)
    await db_session.flush()

    # Create a news event
    ne = NewsEvent(
        headline="Bitcoin ETF sees record inflows",
        symbol="BTCUSDT",
        market_type="crypto",
    )
    db_session.add(ne)
    await db_session.flush()

    # Link them
    link = SignalNewsLink(signal_id=sig.id, news_event_id=ne.id)
    db_session.add(link)
    await db_session.flush()

    from sqlalchemy import select
    result = await db_session.execute(
        select(SignalNewsLink).where(SignalNewsLink.signal_id == sig.id)
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.news_event_id == ne.id


# ── Event Expiry Constants ──


class TestEventExpiry:
    """Tests for event expiry configuration."""

    def test_all_categories_have_expiry(self):
        from app.services.ai_engine.event_chain import EVENT_EXPIRY_HOURS, DECAY_HALF_LIVES

        for cat in EVENT_EXPIRY_HOURS:
            assert cat in DECAY_HALF_LIVES, f"Missing decay half-life for {cat}"

    def test_decay_half_lives_positive(self):
        from app.services.ai_engine.event_chain import DECAY_HALF_LIVES

        for cat, hours in DECAY_HALF_LIVES.items():
            assert hours > 0, f"Non-positive half-life for {cat}"
