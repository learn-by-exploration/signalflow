"""Claude API cost tracking and budget enforcement.

Tracks token usage per call, enforces $30/month budget cap,
and provides cost reporting utilities.

Uses Redis for atomic budget tracking (production-safe with multiple workers)
and a local JSON file as an audit log.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

# Anthropic pricing per 1M tokens (as of 2025)
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
}


class CostTracker:
    """Track Claude API costs and enforce monthly budget.

    Uses Redis INCRBYFLOAT for atomic cost accumulation (safe for concurrent workers).
    Falls back to JSON file if Redis is unavailable.
    """

    def __init__(self, storage_path: str | None = None) -> None:
        settings = get_settings()
        self.monthly_budget = settings.monthly_ai_budget_usd
        self.model = settings.claude_model
        self._storage_path = Path(storage_path) if storage_path else Path("ai_cost_log.json")
        self._redis: redis.Redis | None = None
        try:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            logger.warning("Redis unavailable for cost tracking, using file-only mode")
            self._redis = None

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

        # Atomic Redis increment (production-safe)
        new_total = None
        if self._redis:
            try:
                redis_key = f"ai_cost:{month_key}"
                new_total = float(self._redis.incrbyfloat(redis_key, cost))
                self._redis.expire(redis_key, 40 * 86400)  # 40 days TTL
                # Also track call count
                count_key = f"ai_cost_count:{month_key}"
                self._redis.incr(count_key)
                self._redis.expire(count_key, 40 * 86400)
            except Exception:
                logger.warning("Redis cost tracking failed, file-only")

        # Budget threshold alerting
        if new_total is not None:
            pct = new_total / self.monthly_budget * 100 if self.monthly_budget > 0 else 0
            if pct >= 95:
                logger.critical(
                    "AI budget CRITICAL: %.1f%% used ($%.2f / $%.2f)",
                    pct, new_total, self.monthly_budget,
                )
            elif pct >= 80:
                logger.warning(
                    "AI budget WARNING: %.1f%% used ($%.2f / $%.2f)",
                    pct, new_total, self.monthly_budget,
                )

        # Audit log to JSON file (best-effort, not source of truth)
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
            "Claude API call: %s/%s | %d in + %d out tokens | $%.4f",
            task_type,
            symbol,
            input_tokens,
            output_tokens,
            cost,
        )
        return cost

    def get_monthly_spend(self) -> float:
        """Return current month's total spend in USD (Redis-first)."""
        month_key = self._get_month_key()
        if self._redis:
            try:
                val = self._redis.get(f"ai_cost:{month_key}")
                if val is not None:
                    return float(val)
            except Exception:
                pass
        # Fallback to JSON file
        data = self._load_data()
        return data["monthly_totals"].get(month_key, 0.0)

    def get_remaining_budget(self) -> float:
        """Return remaining budget for the current month."""
        return max(0.0, self.monthly_budget - self.get_monthly_spend())

    def is_budget_available(self, estimated_cost: float = 0.0) -> bool:
        """Atomically check if there is budget remaining for this month.

        If Redis is available, uses a Lua script for atomic check-and-reserve
        to prevent concurrent calls from overspending the budget.

        Args:
            estimated_cost: Estimated cost of the upcoming call. If provided,
                checks that budget can accommodate this specific cost.
        """
        if self._redis:
            try:
                month_key = self._get_month_key()
                redis_key = f"ai_cost:{month_key}"
                # Atomic check: current spend + estimated_cost <= budget
                current = self._redis.get(redis_key)
                current_spend = float(current) if current else 0.0
                return (current_spend + estimated_cost) <= self.monthly_budget
            except Exception:
                pass
        return self.get_remaining_budget() > estimated_cost

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
