"""Tests for AI engine — sentiment, reasoner, cost tracker (mocked Claude API)."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.reasoner import AIReasoner
from app.services.ai_engine.sentiment import AISentimentEngine


class TestCostTracker:
    """Test cost tracking and budget enforcement."""

    def test_calculate_cost(self, tmp_path: Path) -> None:
        tracker = CostTracker(storage_path=str(tmp_path / "costs.json"))
        cost = tracker.calculate_cost(input_tokens=1000, output_tokens=500)
        # claude-sonnet: $3/M input + $15/M output
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.0001

    def test_record_usage(self, tmp_path: Path) -> None:
        tracker = CostTracker(storage_path=str(tmp_path / "costs.json"))
        cost = tracker.record_usage(
            input_tokens=1000,
            output_tokens=500,
            task_type="sentiment",
            symbol="BTCUSDT",
        )
        assert cost > 0
        assert tracker.get_monthly_spend() > 0

    def test_budget_available(self, tmp_path: Path) -> None:
        tracker = CostTracker(storage_path=str(tmp_path / "costs.json"))
        tracker._redis = None  # Isolate from Docker Redis
        assert tracker.is_budget_available() is True

    def test_budget_exhausted(self, tmp_path: Path) -> None:
        tracker = CostTracker(storage_path=str(tmp_path / "costs.json"))
        tracker.monthly_budget = 0.001
        # Record enough to exceed tiny budget
        tracker.record_usage(1000000, 500000, "test")
        assert tracker.is_budget_available() is False

    def test_usage_summary(self, tmp_path: Path) -> None:
        tracker = CostTracker(storage_path=str(tmp_path / "costs.json"))
        tracker._redis = None  # Isolate from Docker Redis
        tracker.record_usage(1000, 500, "sentiment", "BTC")
        tracker.record_usage(2000, 300, "reasoning", "ETH")
        summary = tracker.get_usage_summary()
        assert summary["total_calls"] == 2
        assert "sentiment" in summary["by_task_type"]
        assert "reasoning" in summary["by_task_type"]
        assert summary["remaining_budget_usd"] > 0


class TestAISentimentEngine:
    """Test sentiment analysis with mocked external calls."""

    @pytest.mark.asyncio
    async def test_neutral_fallback_on_no_budget(self) -> None:
        engine = AISentimentEngine(redis_client=None)
        with patch.object(engine.cost_tracker, "is_budget_available", return_value=False):
            result = await engine.analyze_sentiment("BTCUSDT", "crypto")
        assert result["sentiment_score"] == 50
        assert result["fallback_reason"] == "budget_exhausted"

    @pytest.mark.asyncio
    async def test_neutral_fallback_on_no_news(self) -> None:
        engine = AISentimentEngine(redis_client=None)
        with patch.object(engine.cost_tracker, "is_budget_available", return_value=True):
            with patch("app.services.ai_engine.sentiment.fetch_news_for_symbol_structured", return_value=[]):
                result = await engine.analyze_sentiment("BTCUSDT", "crypto")
        assert result["sentiment_score"] == 50
        assert result["fallback_reason"] == "no_news"

    @pytest.mark.asyncio
    async def test_cache_hit(self) -> None:
        mock_redis = AsyncMock()
        cached_data = json.dumps({"sentiment_score": 75, "key_factors": ["growth"]})
        mock_redis.get = AsyncMock(return_value=cached_data)

        engine = AISentimentEngine(redis_client=mock_redis)
        result = await engine.analyze_sentiment("HDFCBANK.NS", "stock")
        assert result["sentiment_score"] == 75
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_analysis(self) -> None:
        engine = AISentimentEngine(redis_client=None)
        mock_claude_response = {
            "content": [{"text": json.dumps({
                "events": [
                    {"headline": "Stock XYZ rises 5%", "description": "earnings beat",
                     "sentiment_direction": "bullish", "impact_magnitude": 3,
                     "event_category": "earnings", "confidence": 80},
                    {"headline": "Sector momentum strong", "description": "sector momentum",
                     "sentiment_direction": "bullish", "impact_magnitude": 2,
                     "event_category": "sector", "confidence": 70},
                ],
                "overall_direction": "bullish",
                "overall_confidence": 0.85,
                "sentiment_score": 72,
                "cross_event_interactions": [],
            })}],
            "usage": {"input_tokens": 500, "output_tokens": 100},
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_claude_response
        mock_response.raise_for_status = MagicMock()

        structured_articles = [{"headline": "Stock XYZ rises 5%", "source": "Reuters", "source_url": "https://example.com", "published_at": None}]

        with patch.object(engine.cost_tracker, "is_budget_available", return_value=True):
            with patch("app.services.ai_engine.sentiment.fetch_news_for_symbol_structured", return_value=structured_articles):
                with patch("app.services.ai_engine.sentiment.httpx.AsyncClient") as MockClient:
                    mock_client_instance = AsyncMock()
                    mock_client_instance.post.return_value = mock_response
                    MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
                    MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

                    result = await engine.analyze_sentiment("TEST", "stock")
                    assert result["sentiment_score"] == 72
                    assert "earnings beat" in result["key_factors"]

    def test_parse_rss(self) -> None:
        from app.services.ai_engine.news_fetcher import _parse_rss_titles

        xml = """<rss><channel>
            <title>Feed Title</title>
            <item><title>Article 1 About Markets</title></item>
            <item><title>Article 2 About Trading</title></item>
        </channel></rss>"""
        articles = _parse_rss_titles(xml)
        assert len(articles) == 2

    def test_parse_rss_cdata(self) -> None:
        from app.services.ai_engine.news_fetcher import _parse_rss_titles

        xml = """<rss><channel>
            <title><![CDATA[Feed]]></title>
            <item><title><![CDATA[News about BTC cryptocurrency markets]]></title></item>
        </channel></rss>"""
        articles = _parse_rss_titles(xml)
        assert len(articles) == 1
        assert "BTC" in articles[0]


class TestAIReasoner:
    """Test signal reasoning generation with mocked Claude."""

    @pytest.mark.asyncio
    async def test_template_fallback_on_no_budget(self) -> None:
        reasoner = AIReasoner()
        with patch.object(reasoner.cost_tracker, "is_budget_available", return_value=False):
            result = await reasoner.generate_reasoning(
                symbol="BTCUSDT",
                signal_type="STRONG_BUY",
                confidence=85,
                technical_data={"rsi": {"value": 35, "signal": "buy"}, "macd": {"histogram": 0.5}},
                sentiment_data=None,
            )
        assert "BTCUSDT" in result
        assert "upside" in result

    def test_summarize_technical(self) -> None:
        data = {
            "rsi": {"value": 35, "signal": "buy"},
            "macd": {"histogram": 0.5},
            "bollinger": {"percent_b": 0.15},
            "volume": {"ratio": 1.8},
            "sma_cross": {"golden_cross": True, "fast_sma": 105, "slow_sma": 100},
        }
        summary = AIReasoner._summarize_technical(data)
        assert "RSI" in summary
        assert "MACD" in summary
        assert "Golden Cross" in summary

    def test_summarize_sentiment_with_data(self) -> None:
        data = {"sentiment_score": 75, "market_impact": "positive", "key_factors": ["earnings", "growth"]}
        summary = AIReasoner._summarize_sentiment(data)
        assert "bullish" in summary
        assert "earnings" in summary

    def test_summarize_sentiment_no_data(self) -> None:
        summary = AIReasoner._summarize_sentiment(None)
        assert "No sentiment data" in summary

    def test_template_reasoning_buy(self) -> None:
        result = AIReasoner._template_reasoning(
            "HDFCBANK.NS", "STRONG_BUY", 90,
            {"rsi": {"value": 45}, "macd": {"histogram": 0.3}},
        )
        assert "HDFCBANK" in result
        assert "upside" in result

    def test_template_reasoning_sell(self) -> None:
        result = AIReasoner._template_reasoning(
            "ETHUSDT", "SELL", 30,
            {"rsi": {"value": 72}, "macd": {"histogram": -0.5}},
        )
        assert "ETHUSDT" in result
        assert "downside" in result
