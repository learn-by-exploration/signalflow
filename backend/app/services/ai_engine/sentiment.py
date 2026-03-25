"""AI sentiment analysis using Claude API.

Fetches recent news for a symbol and uses Claude to score sentiment 0-100.
Results cached in Redis for 15 minutes.
Now also stores news events in DB and extracts event chains (V2+).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.news_fetcher import (
    fetch_news_for_symbol,
    fetch_news_for_symbol_structured,
)
from app.services.ai_engine.prompts import EVENT_CHAIN_PROMPT, SENTIMENT_PROMPT
from app.services.ai_engine.sanitizer import sanitize_text

logger = logging.getLogger(__name__)

# Map market type to readable label for prompts
MARKET_LABELS = {
    "stock": "Indian Stock (NSE)",
    "crypto": "Cryptocurrency",
    "forex": "Forex Currency Pair",
}


class AISentimentEngine:
    """Score market sentiment for symbols using Claude AI + news data.

    Args:
        redis_client: Optional Redis client for caching. If None, caching is skipped.
        db_session: Optional async DB session for persisting news events.
    """

    CACHE_TTL = 3600  # 60 minutes (matches sentiment task schedule)

    def __init__(
        self,
        redis_client: Any | None = None,
        db_session: Any | None = None,
    ) -> None:
        self.settings = get_settings()
        self.cost_tracker = CostTracker()
        self.redis = redis_client
        self.db = db_session

    async def analyze_sentiment(
        self, symbol: str, market_type: str
    ) -> dict[str, Any]:
        """Run sentiment analysis for a symbol.

        Args:
            symbol: The market symbol (e.g., HDFCBANK.NS, BTCUSDT, EUR/USD).
            market_type: One of 'stock', 'crypto', 'forex'.

        Returns:
            Dict with sentiment_score (0-100), key_factors, market_impact,
            events data, and news_event_ids for linking to signals.
        """
        # Check cache first
        cache_key = f"sentiment:{symbol}"
        if self.redis:
            cached = await self._get_cached(cache_key)
            if cached:
                logger.info("Sentiment cache hit for %s", symbol)
                return cached

        # Check budget
        if not self.cost_tracker.is_budget_available():
            logger.warning("AI budget exhausted, returning neutral sentiment for %s", symbol)
            return self._neutral_fallback(symbol, reason="budget_exhausted")

        # Fetch news (structured with metadata)
        structured_articles = await fetch_news_for_symbol_structured(
            symbol, market_type, max_articles=10
        )
        articles = [a["headline"] for a in structured_articles]

        if not articles:
            logger.info("No news articles found for %s, returning neutral", symbol)
            return self._neutral_fallback(symbol, reason="no_news")

        # Persist news events to DB if session is available
        news_event_ids: list[str] = []
        if self.db and structured_articles:
            news_event_ids = await self._persist_news_events(
                structured_articles, symbol, market_type
            )

        # Call Claude API with event chain extraction
        result = await self._call_claude_event_chain(
            symbol, market_type, articles, structured_articles
        )

        # Attach news metadata
        result["source_count"] = len(articles)
        result["news_event_ids"] = news_event_ids
        result["articles"] = [
            {
                "headline": a["headline"],
                "source": a.get("source", "unknown"),
                "published_at": a.get("published_at"),
            }
            for a in structured_articles[:5]
        ]

        # Cache the result
        if self.redis and result:
            await self._set_cached(cache_key, result)

        return result

    async def _persist_news_events(
        self,
        articles: list[dict[str, str]],
        symbol: str,
        market_type: str,
    ) -> list[str]:
        """Store news article headlines in the news_events table.

        Returns list of created news event UUIDs as strings.
        """
        from app.models.news_event import NewsEvent

        event_ids: list[str] = []
        try:
            for article in articles[:10]:
                news_event = NewsEvent(
                    headline=article["headline"],
                    source=article.get("source"),
                    source_url=article.get("source_url"),
                    symbol=symbol,
                    market_type=market_type,
                    published_at=None,  # TODO: parse published_at string
                    fetched_at=datetime.now(timezone.utc),
                )
                self.db.add(news_event)
                await self.db.flush()
                event_ids.append(str(news_event.id))
        except Exception:
            logger.warning("Failed to persist news events for %s", symbol)
        return event_ids

    async def _call_claude_event_chain(
        self,
        symbol: str,
        market_type: str,
        articles: list[str],
        structured_articles: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Call Claude with event chain extraction prompt (V2+).

        Falls back to standard sentiment prompt if event chain fails.
        """
        articles_text = "\n".join(
            f"- [{sanitize_text(a.get('source', 'unknown'), max_length=100)}] {sanitize_text(a['headline'])}"
            for a in structured_articles
        )
        market_label = MARKET_LABELS.get(market_type, market_type)

        prompt = EVENT_CHAIN_PROMPT.format(
            symbol=symbol,
            market_type=market_label,
            articles_text=articles_text,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.settings.claude_model,
                        "max_tokens": 800,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # Track cost
            usage = data.get("usage", {})
            self.cost_tracker.record_usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                task_type="event_chain",
                symbol=symbol,
            )

            # Parse JSON response
            content = data["content"][0]["text"].strip()
            result = json.loads(content)

            # Validate and clamp values
            raw_score = result.get("sentiment_score", 50)
            try:
                score = int(raw_score)
            except (TypeError, ValueError):
                score = 50
            events = result.get("events", []) if isinstance(result.get("events"), list) else []
            overall_direction = str(result.get("overall_direction", "neutral"))
            if overall_direction not in ("bullish", "bearish", "neutral"):
                overall_direction = "neutral"
            raw_confidence = result.get("overall_confidence", 0.5)
            try:
                overall_confidence = float(raw_confidence)
            except (TypeError, ValueError):
                overall_confidence = 0.5

            # Extract key factors from events
            key_factors = []
            for evt in events[:3]:
                desc = evt.get("description", "")
                if desc:
                    key_factors.append(desc)

            # Infer market_impact from overall_direction
            impact_map = {"bullish": "positive", "bearish": "negative", "neutral": "neutral"}

            return {
                "sentiment_score": max(0, min(100, score)),
                "key_factors": key_factors,
                "market_impact": impact_map.get(overall_direction, "neutral"),
                "time_horizon": "short_term",
                "confidence_in_analysis": int(overall_confidence * 100),
                "events": events,
                "overall_direction": overall_direction,
                "cross_event_interactions": result.get("cross_event_interactions", []),
            }

        except json.JSONDecodeError:
            logger.warning("Event chain parse failed for %s, falling back to sentiment", symbol)
            return await self._call_claude_sentiment_fallback(symbol, market_type, articles)
        except Exception:
            logger.exception("Claude API error for %s event chain", symbol)
            return await self._call_claude_sentiment_fallback(symbol, market_type, articles)

    async def _call_claude_sentiment_fallback(
        self, symbol: str, market_type: str, articles: list[str]
    ) -> dict[str, Any]:
        """Fallback to simple sentiment prompt if event chain extraction fails."""
        articles_text = "\n".join(f"- {sanitize_text(a)}" for a in articles)
        market_label = MARKET_LABELS.get(market_type, market_type)

        prompt = SENTIMENT_PROMPT.format(
            symbol=symbol,
            market_type=market_label,
            articles_text=articles_text,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.settings.claude_model,
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            usage = data.get("usage", {})
            self.cost_tracker.record_usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                task_type="sentiment",
                symbol=symbol,
            )

            content = data["content"][0]["text"].strip()
            result = json.loads(content)

            raw_score = result.get("sentiment_score", 50)
            try:
                score = int(raw_score)
            except (TypeError, ValueError):
                score = 50
            key_factors = result.get("key_factors", [])
            if not isinstance(key_factors, list):
                key_factors = []
            market_impact = str(result.get("market_impact", "neutral"))
            if market_impact not in ("positive", "negative", "neutral"):
                market_impact = "neutral"
            return {
                "sentiment_score": max(0, min(100, score)),
                "key_factors": key_factors[:5],
                "market_impact": market_impact,
                "time_horizon": str(result.get("time_horizon", "short_term")),
                "confidence_in_analysis": max(0, min(100, int(result.get("confidence_in_analysis", 50)))),
            }
        except Exception:
            logger.exception("Sentiment fallback also failed for %s", symbol)
            return self._neutral_fallback(symbol, reason="api_error")

    @staticmethod
    def _neutral_fallback(symbol: str, reason: str = "unknown") -> dict[str, Any]:
        """Return a neutral sentiment when analysis can't be performed."""
        return {
            "sentiment_score": 50,
            "key_factors": [],
            "market_impact": "neutral",
            "time_horizon": "short_term",
            "confidence_in_analysis": 0,
            "source_count": 0,
            "fallback_reason": reason,
        }

    async def _get_cached(self, key: str) -> dict | None:
        """Retrieve cached sentiment data from Redis."""
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception:
            logger.warning("Redis cache read failed for %s", key)
            return None

    async def _set_cached(self, key: str, data: dict) -> None:
        """Store sentiment data in Redis cache."""
        try:
            await self.redis.set(key, json.dumps(data), ex=self.CACHE_TTL)
        except Exception:
            logger.warning("Redis cache write failed for %s", key)
