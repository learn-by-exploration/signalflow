"""Morning and evening market briefing generator using Claude AI."""

import logging
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.prompts import EVENING_WRAP_PROMPT, MORNING_BRIEF_PROMPT

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


class BriefingGenerator:
    """Generate morning and evening market briefings via Claude AI."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.cost_tracker = CostTracker()

    async def morning_brief(
        self,
        market_data: dict[str, Any],
        signals_summary: str,
    ) -> str:
        """Generate a morning market briefing.

        Args:
            market_data: Summary of overnight market moves.
            signals_summary: Active signals summary text.

        Returns:
            Briefing text (150-200 words).
        """
        now_ist = datetime.now(IST)
        prompt = MORNING_BRIEF_PROMPT.format(
            date=now_ist.strftime("%B %d, %Y"),
            day_of_week=now_ist.strftime("%A"),
            market_data=self._format_market_data(market_data),
            signals_summary=signals_summary,
        )
        return await self._call_claude(prompt, task_type="morning_brief")

    async def evening_wrap(
        self,
        performance_data: dict[str, Any],
        signal_outcomes: str,
    ) -> str:
        """Generate an evening market wrap.

        Args:
            performance_data: Today's market performance summary.
            signal_outcomes: Summary of how signals performed.

        Returns:
            Wrap text (150-200 words).
        """
        now_ist = datetime.now(IST)
        prompt = EVENING_WRAP_PROMPT.format(
            date=now_ist.strftime("%B %d, %Y"),
            performance_data=self._format_market_data(performance_data),
            signal_outcomes=signal_outcomes,
        )
        return await self._call_claude(prompt, task_type="evening_wrap")

    async def _call_claude(self, prompt: str, task_type: str) -> str:
        """Call Claude API for briefing generation.

        Falls back to a placeholder message if budget exhausted or API fails.
        """
        if not self.cost_tracker.is_budget_available():
            logger.warning("AI budget exhausted, skipping %s generation", task_type)
            return f"[{task_type}] AI briefing unavailable — monthly budget reached."

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
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            usage = data.get("usage", {})
            self.cost_tracker.record_usage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                task_type=task_type,
            )

            return data["content"][0]["text"].strip()

        except Exception:
            logger.exception("Claude API error for %s", task_type)
            return f"[{task_type}] Briefing unavailable due to API error."

    @staticmethod
    def _format_market_data(data: dict[str, Any]) -> str:
        """Format market data dict into readable text for prompts."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                parts = [f"{k}: {v}" for k, v in value.items()]
                lines.append(f"{key}: {', '.join(parts)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines) if lines else "No market data available"
