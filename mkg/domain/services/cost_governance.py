# mkg/domain/services/cost_governance.py
"""CostGovernance — LLM API budget tracking and tier recommendation.

R-CG1 through R-CG4: $30/month budget, tier cascade, cost logging.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Estimated cost per character for tier 1 (Claude Sonnet)
_TIER_1_COST_PER_CHAR = 0.000004


class CostGovernance:
    """Tracks LLM API spending and recommends extraction tier."""

    def __init__(self, monthly_budget_usd: float = 30.0) -> None:
        self._monthly_budget = monthly_budget_usd
        self._total_spent = 0.0
        self._call_log: list[dict[str, Any]] = []

    @property
    def total_spent(self) -> float:
        return self._total_spent

    @property
    def budget_remaining(self) -> float:
        return max(0.0, self._monthly_budget - self._total_spent)

    def record_cost(self, cost_usd: float, tier: str, article_id: str) -> None:
        """Record cost of an extraction call."""
        self._total_spent += cost_usd
        self._call_log.append({
            "cost_usd": cost_usd,
            "tier": tier,
            "article_id": article_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def is_within_budget(self) -> bool:
        return self._total_spent < self._monthly_budget

    def can_afford(self, estimated_cost: float) -> bool:
        return (self._total_spent + estimated_cost) <= self._monthly_budget

    def recommend_tier(self, text_length: int) -> str:
        """Recommend extraction tier based on remaining budget."""
        estimated_cost = text_length * _TIER_1_COST_PER_CHAR
        if self.can_afford(estimated_cost) and self.budget_remaining > 5.0:
            return "tier_1_cloud"
        if self.budget_remaining > 0.0:
            return "tier_2_local"
        return "tier_3_regex"

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_spent": self._total_spent,
            "budget_remaining": self.budget_remaining,
            "monthly_budget": self._monthly_budget,
            "call_count": len(self._call_log),
        }

    def reset_monthly(self) -> None:
        """Reset for new billing month."""
        self._total_spent = 0.0
        self._call_log.clear()
