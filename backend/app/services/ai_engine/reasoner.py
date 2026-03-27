"""Signal reasoning generator using Claude AI.

Produces human-readable explanations for generated trading signals.
Uses Claude tool_use for structured output when generating reasoning.
"""

import json
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.prompts import REASONING_PROMPT

logger = logging.getLogger(__name__)

# Claude tool_use schema for reasoning output
REASONING_TOOL = {
    "name": "report_reasoning",
    "description": "Report the signal reasoning explanation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
                "description": "2-3 sentence explanation of the signal, framed as analysis not advice.",
            },
        },
        "required": ["explanation"],
    },
}


class AIReasoner:
    """Generate AI-powered explanations for trading signals."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.cost_tracker = CostTracker()

    async def generate_reasoning(
        self,
        symbol: str,
        signal_type: str,
        confidence: int,
        technical_data: dict[str, Any],
        sentiment_data: dict[str, Any] | None,
    ) -> str:
        """Generate a human-readable explanation for a signal.

        Args:
            symbol: Market symbol.
            signal_type: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL.
            confidence: Confidence score 0-100.
            technical_data: Full technical indicators dict.
            sentiment_data: AI sentiment analysis dict (may be None).

        Returns:
            2-3 sentence explanation string. Falls back to template if API fails.
        """
        if not self.cost_tracker.is_budget_available():
            logger.warning("AI budget exhausted, using template reasoning for %s", symbol)
            return self._template_reasoning(symbol, signal_type, confidence, technical_data)

        technical_summary = self._summarize_technical(technical_data)
        sentiment_summary = self._summarize_sentiment(sentiment_data)

        prompt = REASONING_PROMPT.format(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            technical_summary=technical_summary,
            sentiment_summary=sentiment_summary,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                request_body: dict[str, Any] = {
                    "model": self.settings.claude_model,
                    "max_tokens": 200,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": [REASONING_TOOL],
                    "tool_choice": {"type": "tool", "name": "report_reasoning"},
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
                task_type="reasoning",
                symbol=symbol,
            )

            # Extract tool_use result for structured output
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "report_reasoning":
                    return block.get("input", {}).get("explanation", "")

            # Fallback: plain text response
            return data["content"][0]["text"].strip()

        except Exception:
            logger.exception("Claude API error for %s reasoning", symbol)
            return self._template_reasoning(symbol, signal_type, confidence, technical_data)

    @staticmethod
    def _summarize_technical(data: dict[str, Any]) -> str:
        """Create a compact text summary of technical indicators."""
        parts = []
        rsi = data.get("rsi", {})
        if rsi.get("value") is not None:
            parts.append(f"RSI: {rsi['value']} ({rsi['signal']})")

        macd = data.get("macd", {})
        if macd.get("histogram") is not None:
            direction = "bullish" if macd["histogram"] > 0 else "bearish"
            parts.append(f"MACD: {direction} (hist={macd['histogram']})")

        bb = data.get("bollinger", {})
        if bb.get("percent_b") is not None:
            parts.append(f"Bollinger %B: {bb['percent_b']:.2f}")

        vol = data.get("volume", {})
        if vol.get("ratio") is not None:
            parts.append(f"Volume ratio: {vol['ratio']}x avg")

        sma = data.get("sma_cross", {})
        if sma.get("golden_cross"):
            parts.append("SMA: Golden Cross detected")
        elif sma.get("death_cross"):
            parts.append("SMA: Death Cross detected")
        elif sma.get("fast_sma") is not None:
            trend = "above" if sma["fast_sma"] > sma["slow_sma"] else "below"
            parts.append(f"SMA50 {trend} SMA200")

        return " | ".join(parts) if parts else "No technical data available"

    @staticmethod
    def _summarize_sentiment(data: dict[str, Any] | None) -> str:
        """Create a compact text summary of sentiment data."""
        if not data or data.get("fallback_reason"):
            return "No sentiment data available"

        score = data.get("sentiment_score", 50)
        impact = data.get("market_impact", "neutral")
        factors = data.get("key_factors", [])

        label = "bullish" if score >= 60 else "bearish" if score <= 40 else "neutral"
        summary = f"Sentiment: {label} ({score}/100), Market impact: {impact}"
        if factors:
            summary += f". Key factors: {', '.join(factors[:3])}"
        return summary

    @staticmethod
    def _template_reasoning(
        symbol: str,
        signal_type: str,
        confidence: int,
        technical_data: dict[str, Any],
    ) -> str:
        """Generate a template-based reasoning when AI is unavailable."""
        rsi = technical_data.get("rsi", {})
        macd = technical_data.get("macd", {})

        rsi_text = f"RSI at {rsi['value']}" if rsi.get("value") else "RSI neutral"
        macd_text = (
            f"MACD histogram {'positive' if macd.get('histogram', 0) > 0 else 'negative'}"
            if macd.get("histogram") is not None
            else "MACD neutral"
        )

        direction = "upside" if "BUY" in signal_type else "downside" if "SELL" in signal_type else "sideways"

        return (
            f"Technical analysis for {symbol} indicates {direction} potential "
            f"with {confidence}% confidence. {rsi_text} and {macd_text} "
            f"support this {signal_type.replace('_', ' ').lower()} signal."
        )
