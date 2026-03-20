"""AI sentiment analysis using Claude API.

Fetches recent news for a symbol and uses Claude to score sentiment 0-100.
Results cached in Redis for 15 minutes.
"""

import json
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.news_fetcher import fetch_news_for_symbol
from app.services.ai_engine.prompts import SENTIMENT_PROMPT

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
    """

    CACHE_TTL = 3600  # 60 minutes (matches sentiment task schedule)

    def __init__(self, redis_client: Any | None = None) -> None:
        self.settings = get_settings()
        self.cost_tracker = CostTracker()
        self.redis = redis_client

    async def analyze_sentiment(
        self, symbol: str, market_type: str
    ) -> dict[str, Any]:
        """Run sentiment analysis for a symbol.

        Args:
            symbol: The market symbol (e.g., HDFCBANK.NS, BTCUSDT, EUR/USD).
            market_type: One of 'stock', 'crypto', 'forex'.

        Returns:
            Dict with sentiment_score (0-100), key_factors, market_impact, etc.
            Returns a neutral fallback if budget exhausted or API fails.
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

        # Fetch news
        articles = await self._fetch_news(symbol, market_type)
        if not articles:
            logger.info("No news articles found for %s, returning neutral", symbol)
            return self._neutral_fallback(symbol, reason="no_news")

        # Call Claude API
        result = await self._call_claude(symbol, market_type, articles)

        # Cache the result
        if self.redis and result:
            await self._set_cached(cache_key, result)

        return result

    async def _fetch_news(self, symbol: str, market_type: str) -> list[str]:
        """Fetch recent news articles for a symbol using multi-source fetcher.

        Returns a list of article text snippets (max 10).
        """
        return await fetch_news_for_symbol(symbol, market_type, max_articles=10)

    async def _call_claude(
        self, symbol: str, market_type: str, articles: list[str]
    ) -> dict[str, Any]:
        """Call Claude API with sentiment analysis prompt.

        Args:
            symbol: Market symbol.
            market_type: Market category.
            articles: List of news article titles/snippets.

        Returns:
            Parsed sentiment analysis dict.
        """
        articles_text = "\n".join(f"- {a}" for a in articles)
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

            # Track cost
            usage = data.get("usage", {})
            self.cost_tracker.record_usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                task_type="sentiment",
                symbol=symbol,
            )

            # Parse JSON response from Claude
            content = data["content"][0]["text"].strip()
            result = json.loads(content)

            # Validate expected fields
            score = int(result.get("sentiment_score", 50))
            return {
                "sentiment_score": max(0, min(100, score)),
                "key_factors": result.get("key_factors", []),
                "market_impact": result.get("market_impact", "neutral"),
                "time_horizon": result.get("time_horizon", "short_term"),
                "confidence_in_analysis": int(result.get("confidence_in_analysis", 50)),
                "source_count": len(articles),
            }

        except json.JSONDecodeError:
            logger.error("Claude returned invalid JSON for %s sentiment", symbol)
            return self._neutral_fallback(symbol, reason="invalid_response")
        except Exception:
            logger.exception("Claude API error for %s sentiment", symbol)
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
