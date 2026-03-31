# mkg/tests/test_cost_governance.py
"""Tests for CostGovernance — budget tracking for LLM API calls."""

import pytest


class TestCostGovernance:

    @pytest.fixture
    def governor(self):
        from mkg.domain.services.cost_governance import CostGovernance
        return CostGovernance(monthly_budget_usd=30.0)

    def test_initial_spend_is_zero(self, governor):
        assert governor.total_spent == 0.0

    def test_record_cost(self, governor):
        governor.record_cost(0.005, "tier_1_cloud", "art-001")
        assert governor.total_spent == 0.005

    def test_budget_remaining(self, governor):
        governor.record_cost(10.0, "tier_1_cloud", "art-001")
        assert governor.budget_remaining == 20.0

    def test_is_within_budget(self, governor):
        assert governor.is_within_budget() is True
        governor.record_cost(30.0, "tier_1_cloud", "art-001")
        assert governor.is_within_budget() is False

    def test_can_afford(self, governor):
        assert governor.can_afford(5.0) is True
        governor.record_cost(28.0, "tier_1_cloud", "art-001")
        assert governor.can_afford(5.0) is False

    def test_should_use_tier(self, governor):
        # With budget available, should use tier 1
        tier = governor.recommend_tier(text_length=1000)
        assert tier == "tier_1_cloud"

    def test_recommends_lower_tier_near_budget(self, governor):
        governor.record_cost(25.0, "tier_1_cloud", "art-001")
        tier = governor.recommend_tier(text_length=1000)
        assert tier in ("tier_2_local", "tier_3_regex")

    def test_recommends_regex_when_budget_exhausted(self, governor):
        governor.record_cost(30.0, "tier_1_cloud", "art-001")
        tier = governor.recommend_tier(text_length=1000)
        assert tier == "tier_3_regex"

    def test_get_stats(self, governor):
        governor.record_cost(0.005, "tier_1_cloud", "art-001")
        governor.record_cost(0.0, "tier_3_regex", "art-002")
        stats = governor.get_stats()
        assert stats["total_spent"] == 0.005
        assert stats["budget_remaining"] == 29.995
        assert stats["call_count"] == 2

    def test_reset_monthly(self, governor):
        governor.record_cost(15.0, "tier_1_cloud", "art-001")
        governor.reset_monthly()
        assert governor.total_spent == 0.0

    def test_negative_budget_raises(self):
        from mkg.domain.services.cost_governance import CostGovernance
        with pytest.raises(ValueError, match="must be > 0"):
            CostGovernance(monthly_budget_usd=-1.0)

    def test_zero_budget_raises(self):
        from mkg.domain.services.cost_governance import CostGovernance
        with pytest.raises(ValueError, match="must be > 0"):
            CostGovernance(monthly_budget_usd=0.0)

    def test_negative_cost_raises(self, governor):
        with pytest.raises(ValueError, match="cost_usd must be >= 0"):
            governor.record_cost(-1.0, "tier_1_cloud", "art-001")

    def test_zero_cost_is_valid(self, governor):
        governor.record_cost(0.0, "tier_3_regex", "art-001")
        assert governor.total_spent == 0.0

    def test_budget_remaining_never_negative(self, governor):
        governor.record_cost(35.0, "tier_1_cloud", "art-001")  # Over budget
        assert governor.budget_remaining == 0.0
