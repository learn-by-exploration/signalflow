"""Claude API cost tracking and budget enforcement.

Tracks token usage per call, enforces $30/month budget cap,
and provides cost reporting utilities.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

# Anthropic pricing per 1M tokens (as of 2025)
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
}


class CostTracker:
    """Track Claude API costs and enforce monthly budget.

    Stores usage data in a local JSON file. In production,
    this would use Redis or PostgreSQL for persistence.
    """

    def __init__(self, storage_path: str | None = None) -> None:
        settings = get_settings()
        self.monthly_budget = settings.monthly_ai_budget_usd
        self.model = settings.claude_model
        self._storage_path = Path(storage_path) if storage_path else Path("ai_cost_log.json")

    def _load_data(self) -> dict:
        """Load cost tracking data from storage."""
        if self._storage_path.exists():
            try:
                return json.loads(self._storage_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupted cost log, starting fresh")
        return {"calls": [], "monthly_totals": {}}

    def _save_data(self, data: dict) -> None:
        """Persist cost tracking data."""
        self._storage_path.write_text(json.dumps(data, indent=2, default=str))

    def _get_month_key(self) -> str:
        """Return current month key as YYYY-MM."""
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate USD cost for a given token usage.

        Args:
            input_tokens: Number of input tokens used.
            output_tokens: Number of output tokens used.

        Returns:
            Cost in USD.
        """
        pricing = PRICING.get(self.model, PRICING["claude-sonnet-4-20250514"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        task_type: str,
        symbol: str = "",
    ) -> float:
        """Record a Claude API call's token usage.

        Args:
            input_tokens: Input tokens consumed.
            output_tokens: Output tokens consumed.
            task_type: Type of task (sentiment, reasoning, briefing).
            symbol: Market symbol if applicable.

        Returns:
            Cost of this call in USD.
        """
        cost = self.calculate_cost(input_tokens, output_tokens)
        month_key = self._get_month_key()

        data = self._load_data()
        data["calls"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_type": task_type,
            "symbol": symbol,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "model": self.model,
        })

        data["monthly_totals"][month_key] = (
            data["monthly_totals"].get(month_key, 0.0) + cost
        )

        self._save_data(data)

        logger.info(
            "Claude API call: %s/%s | %d in + %d out tokens | $%.4f | Month total: $%.2f",
            task_type,
            symbol,
            input_tokens,
            output_tokens,
            cost,
            data["monthly_totals"][month_key],
        )
        return cost

    def get_monthly_spend(self) -> float:
        """Return current month's total spend in USD."""
        data = self._load_data()
        return data["monthly_totals"].get(self._get_month_key(), 0.0)

    def get_remaining_budget(self) -> float:
        """Return remaining budget for the current month."""
        return max(0.0, self.monthly_budget - self.get_monthly_spend())

    def is_budget_available(self) -> bool:
        """Check if there is budget remaining for this month."""
        return self.get_remaining_budget() > 0

    def get_usage_summary(self) -> dict:
        """Return a summary of current month's API usage.

        Returns:
            Dict with total_calls, total_cost, remaining_budget, by_task_type.
        """
        data = self._load_data()
        month_key = self._get_month_key()

        month_calls = [
            c for c in data["calls"] if c["timestamp"].startswith(month_key)
        ]

        by_task: dict[str, float] = {}
        for call in month_calls:
            task = call["task_type"]
            by_task[task] = by_task.get(task, 0.0) + call["cost_usd"]

        total_cost = data["monthly_totals"].get(month_key, 0.0)

        return {
            "month": month_key,
            "total_calls": len(month_calls),
            "total_cost_usd": round(total_cost, 4),
            "remaining_budget_usd": round(self.get_remaining_budget(), 4),
            "budget_pct_used": round(total_cost / self.monthly_budget * 100, 1),
            "by_task_type": {k: round(v, 4) for k, v in by_task.items()},
        }
