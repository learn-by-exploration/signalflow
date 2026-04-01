# mkg/tests/test_extraction_orchestrator.py
"""Tests for ExtractionOrchestrator — tier cascade with cost governance.

Iterations 3-5: Claude → Regex fallback, budget-aware tier selection.
"""

import pytest

from mkg.domain.services.cost_governance import CostGovernance
from mkg.infrastructure.llm.regex_extractor import RegexExtractor


class _MockClaudeExtractor:
    """Mock Claude extractor for testing cascade logic."""

    def __init__(self, should_fail: bool = False):
        self._should_fail = should_fail
        self.call_count = 0

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_1

    def get_cost_estimate(self, text_length: int) -> float:
        return text_length * 0.000004

    async def extract_all(self, text: str, context=None) -> dict:
        self.call_count += 1
        if self._should_fail:
            raise Exception("Claude API unavailable")
        return {
            "entities": [
                {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
                {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
            ],
            "relations": [
                {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
                 "weight": 0.85, "confidence": 0.9},
            ],
        }

    async def extract_entities(self, text: str, context=None) -> list:
        self.call_count += 1
        if self._should_fail:
            raise Exception("Claude API unavailable")
        return [{"name": "TSMC", "entity_type": "Company", "confidence": 0.95}]


class TestExtractionOrchestrator:
    """Tests for tier cascade logic."""

    @pytest.fixture
    def governance(self):
        return CostGovernance(monthly_budget_usd=30.0)

    @pytest.fixture
    def claude_ok(self):
        return _MockClaudeExtractor(should_fail=False)

    @pytest.fixture
    def claude_fail(self):
        return _MockClaudeExtractor(should_fail=True)

    @pytest.fixture
    def regex(self):
        return RegexExtractor()

    @pytest.fixture
    def orchestrator(self, claude_ok, regex, governance):
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        return ExtractionOrchestrator(
            extractors=[claude_ok, regex],
            cost_governance=governance,
        )

    @pytest.mark.asyncio
    async def test_uses_tier1_when_available(self, orchestrator, claude_ok):
        """Should use Claude (Tier 1) when budget allows and API works."""
        result = await orchestrator.extract("TSMC supplies chips to NVIDIA")
        assert claude_ok.call_count == 1
        assert result["tier_used"] == "tier_1_cloud"
        assert len(result["entities"]) >= 1

    @pytest.mark.asyncio
    async def test_cascades_to_regex_on_failure(self, claude_fail, regex, governance):
        """Should fall back to Regex (Tier 3) when Claude fails."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        orch = ExtractionOrchestrator(
            extractors=[claude_fail, regex],
            cost_governance=governance,
        )
        result = await orch.extract("TSMC supplies chips to NVIDIA")
        assert claude_fail.call_count == 1
        assert result["tier_used"] == "tier_3_regex"
        assert len(result["entities"]) >= 1

    @pytest.mark.asyncio
    async def test_cascades_when_budget_exhausted(self, regex, governance):
        """Should skip Claude when budget is exhausted."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        # Exhaust budget
        governance.record_cost(30.0, "tier_1_cloud", "test")

        claude = _MockClaudeExtractor(should_fail=False)
        orch = ExtractionOrchestrator(
            extractors=[claude, regex],
            cost_governance=governance,
        )
        result = await orch.extract("TSMC supplies chips to NVIDIA")
        assert claude.call_count == 0  # Skipped due to budget
        assert result["tier_used"] == "tier_3_regex"

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_fail(self, governance):
        """Should return empty result when all extractors fail."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        failing1 = _MockClaudeExtractor(should_fail=True)
        failing2 = _MockClaudeExtractor(should_fail=True)
        orch = ExtractionOrchestrator(
            extractors=[failing1, failing2],
            cost_governance=governance,
        )
        result = await orch.extract("test text")
        assert result["entities"] == []
        assert result["relations"] == []
        assert result["tier_used"] == "none"

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self, orchestrator):
        """Should return empty for empty text without calling extractors."""
        result = await orchestrator.extract("")
        assert result["entities"] == []
        assert result["relations"] == []

    @pytest.mark.asyncio
    async def test_records_cost_after_claude_extraction(self, orchestrator, governance):
        """Should track cost when Claude extraction succeeds."""
        budget_before = governance.budget_remaining
        text = "TSMC supplies chips to NVIDIA"
        await orchestrator.extract(text)
        assert governance.budget_remaining < budget_before

    @pytest.mark.asyncio
    async def test_result_includes_metadata(self, orchestrator):
        """Result should include extraction metadata."""
        result = await orchestrator.extract("TSMC supplies chips")
        assert "tier_used" in result
        assert "entities" in result
        assert "relations" in result
        assert "article_id" in result

    @pytest.mark.asyncio
    async def test_accepts_article_id(self, orchestrator):
        """Should pass through article_id."""
        result = await orchestrator.extract("TSMC", article_id="art-123")
        assert result["article_id"] == "art-123"

    @pytest.mark.asyncio
    async def test_cost_not_recorded_for_regex(self, claude_fail, regex, governance):
        """Regex extraction should not cost anything."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        orch = ExtractionOrchestrator(
            extractors=[claude_fail, regex],
            cost_governance=governance,
        )
        budget_before = governance.budget_remaining
        await orch.extract("TSMC test")
        # Regex is free, budget should be same
        assert governance.budget_remaining == budget_before


class TestExtractionOrchestratorWithDLQ:
    """Tests for DLQ integration."""

    @pytest.fixture
    def dlq(self):
        from mkg.domain.services.dlq import DeadLetterQueue
        return DeadLetterQueue()

    @pytest.mark.asyncio
    async def test_failed_extraction_goes_to_dlq(self, dlq):
        """When all tiers fail, article should go to DLQ."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        from mkg.domain.services.cost_governance import CostGovernance

        failing = _MockClaudeExtractor(should_fail=True)
        orch = ExtractionOrchestrator(
            extractors=[failing],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
            dlq=dlq,
        )
        result = await orch.extract("test text", article_id="art-456")
        assert result["tier_used"] == "none"
        items = await dlq.get_retriable()
        assert len(items) == 1
        assert items[0]["item_id"] == "art-456"

    @pytest.mark.asyncio
    async def test_successful_extraction_not_in_dlq(self, dlq):
        """Successful extraction should NOT go to DLQ."""
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        from mkg.domain.services.cost_governance import CostGovernance

        claude = _MockClaudeExtractor(should_fail=False)
        orch = ExtractionOrchestrator(
            extractors=[claude],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
            dlq=dlq,
        )
        await orch.extract("TSMC test", article_id="art-789")
        items = await dlq.get_retriable()
        assert len(items) == 0
