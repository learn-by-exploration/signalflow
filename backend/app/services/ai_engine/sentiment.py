"""AI sentiment analysis using Claude API.

Fetches recent news for a symbol and uses Claude to score sentiment 0-100.
Results cached in Redis for 60 minutes (market-specific TTLs available).
Uses Claude tool_use for guaranteed structured JSON output.
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

# Market-specific sentiment cache TTLs (seconds)
SENTIMENT_CACHE_TTLS = {
    "crypto": 1800,   # 30 min — crypto news moves fast
    "stock": 3600,    # 60 min
    "forex": 5400,    # 90 min — forex is more macro-driven
}

# Claude tool_use schema for sentiment analysis (guaranteed structured output)
SENTIMENT_TOOL = {
    "name": "report_sentiment",
    "description": "Report the sentiment analysis result for the given symbol.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment_score": {
                "type": "integer",
                "description": "Sentiment score 0-100 (0=extremely bearish, 100=extremely bullish)",
                "minimum": 0,
                "maximum": 100,
            },
            "key_factors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Top 3 key factors driving sentiment",
                "maxItems": 5,
            },
            "market_impact": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"],
                "description": "Expected market impact direction",
            },
            "time_horizon": {
                "type": "string",
                "enum": ["short_term", "medium_term", "long_term"],
            },
            "confidence_in_analysis": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
        },
        "required": ["sentiment_score", "key_factors", "market_impact", "time_horizon", "confidence_in_analysis"],
    },
}

# Claude tool_use schema for event chain extraction
EVENT_CHAIN_TOOL = {
    "name": "report_event_chains",
    "description": "Report extracted causal event chains from news articles.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
            "overall_direction": {
                "type": "string",
                "enum": ["bullish", "bearish", "neutral"],
            },
            "overall_confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "category": {"type": "string"},
                        "sentiment_direction": {
                            "type": "string",
                            "enum": ["bullish", "bearish", "neutral"],
                        },
                        "magnitude": {"type": "number"},
                    },
                    "required": ["description", "sentiment_direction"],
                },
            },
            "cross_event_interactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "events": {"type": "array", "items": {"type": "integer"}},
                        "interaction": {"type": "string"},
                        "net_effect": {"type": "string"},
                    },
                },
            },
        },
        "required": ["sentiment_score", "overall_direction", "overall_confidence", "events"],
    },
}


class AISentimentEngine:
    """Score market sentiment for symbols using Claude AI + news data.

    Args:
        redis_client: Optional Redis client for caching. If None, caching is skipped.
        db_session: Optional async DB session for persisting news events.
    """

    CACHE_TTL = 3600  # Default 60 minutes; overridden by SENTIMENT_CACHE_TTLS per market

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

        # Cache the result (market-specific TTL)
        if self.redis and result:
            ttl = SENTIMENT_CACHE_TTLS.get(market_type, self.CACHE_TTL)
            await self._set_cached(cache_key, result, ttl=ttl)

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
                published_at = None
                pub_str = article.get("published_at")
                if pub_str:
                    try:
                        from dateutil.parser import parse as parse_dt

                        published_at = parse_dt(pub_str)
                    except (ValueError, TypeError):
                        pass
                news_event = NewsEvent(
                    headline=article["headline"],
                    source=article.get("source"),
                    source_url=article.get("source_url"),
                    symbol=symbol,
                    market_type=market_type,
                    published_at=published_at,
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
                request_body: dict[str, Any] = {
                    "model": self.settings.claude_model,
                    "max_tokens": 800,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": [EVENT_CHAIN_TOOL],
                    "tool_choice": {"type": "tool", "name": "report_event_chains"},
                }
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=request_body,
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

            # Extract tool_use result (guaranteed structured JSON)
            result = self._extract_tool_result(data, "report_event_chains")
            if result is None:
                # Fallback: try parsing text content (backward compat)
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
                request_body: dict[str, Any] = {
                    "model": self.settings.claude_model,
                    "max_tokens": 300,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": [SENTIMENT_TOOL],
                    "tool_choice": {"type": "tool", "name": "report_sentiment"},
                }
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=request_body,
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

            # Extract tool_use result
            result = self._extract_tool_result(data, "report_sentiment")
            if result is None:
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

    async def _set_cached(self, key: str, data: dict, ttl: int | None = None) -> None:
        """Store sentiment data in Redis cache."""
        try:
            cache_ttl = ttl if ttl is not None else self.CACHE_TTL
            await self.redis.set(key, json.dumps(data), ex=cache_ttl)
        except Exception:
            logger.warning("Redis cache write failed for %s", key)

    @staticmethod
    def _extract_tool_result(response_data: dict, tool_name: str) -> dict | None:
        """Extract structured result from Claude tool_use response.

        Args:
            response_data: Full Claude API response.
            tool_name: Expected tool name.

        Returns:
            The tool input dict, or None if not found.
        """
        for block in response_data.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == tool_name:
                return block.get("input", {})
        return None
