# mkg/tests/test_reliability.py
"""Reliability & error recovery tests.

Iterations 36-40: Circuit breaker behavior, DLQ retry flow, extraction
fallback, backpressure, concurrent operations, and health monitoring.
"""

import asyncio
import os
import tempfile

import pytest

from mkg.domain.services.backpressure import BackpressureManager
from mkg.domain.services.cost_governance import CostGovernance
from mkg.domain.services.dlq import DeadLetterQueue
from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
from mkg.domain.services.pipeline_observability import PipelineObservability
from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


# ── Fake extractors for reliability testing ──


class _FailingExtractor:
    """Extractor that always raises."""

    def __init__(self, error_cls=Exception, error_msg="extraction failed"):
        self._error_cls = error_cls
        self._error_msg = error_msg
        self.call_count = 0

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_1

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.001

    async def extract_all(self, text: str, context=None) -> dict:
        self.call_count += 1
        raise self._error_cls(self._error_msg)


class _ExpensiveExtractor:
    """Extractor that costs a lot per call."""

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_1

    def get_cost_estimate(self, text_length: int) -> float:
        return 100.0  # $100 per call — over budget

    async def extract_all(self, text: str, context=None) -> dict:
        return {"entities": [{"name": "X", "entity_type": "Company"}], "relations": []}


class _CheapExtractor:
    """Extractor that works and costs nothing."""

    def __init__(self):
        self.call_count = 0

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_3

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0

    async def extract_all(self, text: str, context=None) -> dict:
        self.call_count += 1
        return {"entities": [{"name": "Fallback", "entity_type": "Company"}], "relations": []}


# ════════════════════════════════════════════════════════════
# DLQ RETRY FLOW
# ════════════════════════════════════════════════════════════


class TestDLQRetryFlow:
    """DLQ should accumulate failures and track retries."""

    @pytest.mark.asyncio
    async def test_failed_item_added_to_dlq(self):
        dlq = DeadLetterQueue(max_retries=3)
        await dlq.add("art-1", "extraction_error", {"title": "Bad article"})
        items = await dlq.get_all()
        assert len(items) == 1
        assert items[0]["item_id"] == "art-1"

    @pytest.mark.asyncio
    async def test_retry_count_increments(self):
        dlq = DeadLetterQueue(max_retries=3)
        await dlq.add("art-1", "error", {})
        await dlq.increment_retry("art-1")
        await dlq.increment_retry("art-1")
        items = await dlq.get_all()
        assert items[0]["retry_count"] == 2

    @pytest.mark.asyncio
    async def test_exhausted_items_not_retriable(self):
        dlq = DeadLetterQueue(max_retries=2)
        await dlq.add("art-1", "error", {})
        await dlq.increment_retry("art-1")
        await dlq.increment_retry("art-1")
        assert await dlq.is_exhausted("art-1") is True
        retriable = await dlq.get_retriable()
        assert len(retriable) == 0

    @pytest.mark.asyncio
    async def test_successful_reprocessing_removes_from_dlq(self):
        dlq = DeadLetterQueue(max_retries=3)
        await dlq.add("art-1", "transient_error", {})
        await dlq.remove("art-1")
        items = await dlq.get_all()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_dlq_stats(self):
        dlq = DeadLetterQueue(max_retries=2)
        await dlq.add("art-1", "err", {})
        await dlq.add("art-2", "err", {})
        await dlq.increment_retry("art-1")
        await dlq.increment_retry("art-1")  # exhausted
        stats = await dlq.get_stats()
        assert stats["total"] == 2
        assert stats["exhausted"] == 1
        assert stats["retriable"] == 1


# ════════════════════════════════════════════════════════════
# EXTRACTION TIER FALLBACK
# ════════════════════════════════════════════════════════════


class TestExtractionFallback:
    """When Tier 1 (Claude) fails, should fall back to Tier 3 (regex)."""

    @pytest.mark.asyncio
    async def test_fallback_to_cheap_when_expensive_unaffordable(self):
        """If budget is too low for Tier 1, should skip to Tier 3."""
        expensive = _ExpensiveExtractor()
        cheap = _CheapExtractor()
        orch = ExtractionOrchestrator(
            extractors=[expensive, cheap],
            cost_governance=CostGovernance(monthly_budget_usd=1.0),
        )
        result = await orch.extract("Some text about companies", article_id="a1")
        assert result.get("tier_used") == "tier_3_regex"
        assert cheap.call_count == 1

    @pytest.mark.asyncio
    async def test_fallback_when_tier1_raises(self):
        """If Tier 1 raises, fall through to Tier 3."""
        failing = _FailingExtractor()
        cheap = _CheapExtractor()
        dlq = DeadLetterQueue()
        orch = ExtractionOrchestrator(
            extractors=[failing, cheap],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
            dlq=dlq,
        )
        result = await orch.extract("Text about NVIDIA and AMD", article_id="a2")
        assert failing.call_count == 1
        assert cheap.call_count == 1
        assert len(result.get("entities", [])) >= 1

    @pytest.mark.asyncio
    async def test_all_extractors_fail_routes_to_dlq(self):
        """When all extractors fail, item goes to DLQ."""
        f1 = _FailingExtractor()
        f2 = _FailingExtractor()
        dlq = DeadLetterQueue()
        orch = ExtractionOrchestrator(
            extractors=[f1, f2],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
            dlq=dlq,
        )
        result = await orch.extract("Some text", article_id="a3")
        assert result.get("entities", []) == []
        # DLQ should have the failed item
        dlq_items = await dlq.get_all()
        assert len(dlq_items) == 1


# ════════════════════════════════════════════════════════════
# BACKPRESSURE MANAGEMENT
# ════════════════════════════════════════════════════════════


class TestBackpressure:
    """Flow control under high article volume."""

    def test_normal_state_accepts(self):
        bp = BackpressureManager(max_queue_depth=10, throttle_threshold=0.8)
        assert bp.state == "normal"
        assert bp.try_enqueue("article-1") is True

    def test_throttled_state(self):
        bp = BackpressureManager(max_queue_depth=10, throttle_threshold=0.8)
        for i in range(8):
            bp.enqueue(f"a-{i}")
        assert bp.state == "throttled"
        # Still accepts in throttled mode
        assert bp.try_enqueue("a-8") is True

    def test_shedding_rejects(self):
        bp = BackpressureManager(max_queue_depth=5, throttle_threshold=0.8)
        for i in range(5):
            bp.enqueue(f"a-{i}")
        assert bp.state == "shedding"
        assert bp.try_enqueue("overflow") is False

    def test_dequeue_restores_capacity(self):
        bp = BackpressureManager(max_queue_depth=3)
        for i in range(3):
            bp.enqueue(f"a-{i}")
        assert bp.state == "shedding"
        bp.dequeue()
        assert bp.can_accept() is True

    def test_stats_report(self):
        bp = BackpressureManager(max_queue_depth=10)
        bp.enqueue("a")
        stats = bp.get_stats()
        assert stats["queue_depth"] == 1
        assert stats["state"] == "normal"


# ════════════════════════════════════════════════════════════
# COST GOVERNANCE EDGE CASES
# ════════════════════════════════════════════════════════════


class TestCostGovernanceReliability:
    """Budget enforcement under edge conditions."""

    def test_budget_exhaustion(self):
        cg = CostGovernance(monthly_budget_usd=0.01)
        cg.record_cost(0.01, "tier_1_cloud", "art-1")
        assert cg.is_within_budget() is False
        assert cg.budget_remaining == 0.0

    def test_cannot_afford_over_budget(self):
        cg = CostGovernance(monthly_budget_usd=1.0)
        assert cg.can_afford(1.01) is False
        assert cg.can_afford(0.99) is True

    def test_tier_recommendation_degrades(self):
        cg = CostGovernance(monthly_budget_usd=10.0)
        # Spend most of the budget
        cg.record_cost(6.0, "tier_1_cloud", "art-1")
        # Should recommend lower tier
        assert cg.recommend_tier(1000) in ("tier_2_local", "tier_3_regex")

    def test_monthly_reset(self):
        cg = CostGovernance(monthly_budget_usd=10.0)
        cg.record_cost(10.0, "tier_1_cloud", "a")
        assert cg.is_within_budget() is False
        cg.reset_monthly()
        assert cg.is_within_budget() is True
        assert cg.total_spent == 0.0

    def test_negative_budget_rejected(self):
        with pytest.raises(ValueError):
            CostGovernance(monthly_budget_usd=-1)

    def test_negative_cost_rejected(self):
        cg = CostGovernance(monthly_budget_usd=10.0)
        with pytest.raises(ValueError):
            cg.record_cost(-0.01, "tier_1_cloud", "a")


# ════════════════════════════════════════════════════════════
# OBSERVABILITY & HEALTH
# ════════════════════════════════════════════════════════════


class TestPipelineObservability:
    """Observability layer tracks stages, errors, and health."""

    def test_record_stage_timing(self):
        obs = PipelineObservability()
        obs.record_stage("extraction", 150.0)
        obs.record_stage("extraction", 200.0)
        assert len(obs._stages["extraction"]) == 2

    def test_increment_counter(self):
        obs = PipelineObservability()
        obs.increment("articles_processed", 5)
        obs.increment("articles_processed", 3)
        assert obs._counters["articles_processed"] == 8

    def test_record_error(self):
        obs = PipelineObservability()
        obs.record_error("extraction", "TimeoutError")
        obs.record_error("extraction", "TimeoutError")
        assert obs._errors["extraction"] == 2

    def test_timer_context_manager(self):
        obs = PipelineObservability()
        with obs.timer("test_stage"):
            pass  # fast op
        assert len(obs._stages["test_stage"]) == 1
        assert obs._stages["test_stage"][0] >= 0


# ════════════════════════════════════════════════════════════
# SQLITE STORAGE RESILIENCE
# ════════════════════════════════════════════════════════════


class TestSQLiteResilience:
    """SQLite storage handles edge cases gracefully."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            entity = await s.get_entity("nonexistent-id")
            assert entity is None
            await s.close()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            result = await s.delete_entity("nonexistent-id")
            assert result is False
            await s.close()

    @pytest.mark.asyncio
    async def test_find_entities_empty_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            entities = await s.find_entities()
            assert entities == []
            await s.close()

    @pytest.mark.asyncio
    async def test_search_empty_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            results = await s.search("anything")
            assert results == []
            await s.close()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            health = await s.health_check()
            assert health["status"] == "healthy"
            await s.close()

    @pytest.mark.asyncio
    async def test_concurrent_writes(self):
        """Multiple concurrent entity creations should not corrupt DB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()

            async def create_entity(i: int):
                await s.create_entity(
                    entity_type="Company",
                    properties={"name": f"Company_{i}", "canonical_name": f"COMPANY_{i}"},
                )

            # Create 20 entities concurrently
            await asyncio.gather(*[create_entity(i) for i in range(20)])

            entities = await s.find_entities()
            assert len(entities) == 20
            await s.close()

    @pytest.mark.asyncio
    async def test_large_properties_json(self):
        """Entity with large JSON properties should store and retrieve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            big_props = {
                "name": "BigCo",
                "canonical_name": "BIGCO",
                "description": "x" * 10000,
                "tags": [f"tag_{i}" for i in range(100)],
            }
            entity = await s.create_entity(entity_type="Company", properties=big_props)
            fetched = await s.get_entity(entity["id"])
            assert fetched is not None
            # Properties are spread into top-level dict by SQLiteGraphStorage
            assert fetched["description"] == "x" * 10000
            await s.close()


# ════════════════════════════════════════════════════════════
# PIPELINE ORCHESTRATOR ERROR RECOVERY
# ════════════════════════════════════════════════════════════


class TestPipelineErrorRecovery:
    """Pipeline handles partial failures gracefully."""

    @pytest.mark.asyncio
    async def test_extraction_failure_does_not_crash_pipeline(self):
        """Pipeline should handle extraction errors without crashing."""
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.article_dedup import ArticleDedup
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        from mkg.domain.services.graph_mutation import GraphMutationService
        from mkg.domain.services.hallucination_verifier import HallucinationVerifier
        from mkg.domain.services.impact_table import ImpactTableBuilder
        from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
        from mkg.domain.services.propagation_engine import PropagationEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await storage.initialize()

            # All extractors fail
            f1 = _FailingExtractor()
            f2 = _FailingExtractor()
            dlq = DeadLetterQueue()
            orch = ExtractionOrchestrator(
                extractors=[f1, f2],
                cost_governance=CostGovernance(monthly_budget_usd=30.0),
                dlq=dlq,
            )
            registry = CanonicalEntityRegistry()
            pipeline = PipelineOrchestrator(
                graph_storage=storage,
                extraction_orchestrator=orch,
                hallucination_verifier=HallucinationVerifier(),
                graph_mutation=GraphMutationService(storage, registry),
                propagation_engine=PropagationEngine(storage),
                causal_chain_builder=CausalChainBuilder(storage),
                alert_system=AlertSystem(),
                impact_table_builder=ImpactTableBuilder(storage),
                article_dedup=ArticleDedup(),
            )

            result = await pipeline.process_article(
                title="Test failure",
                content="This article should survive extraction failure.",
                source="test",
            )
            # Should complete with 0 entities, not crash
            assert result["status"] == "completed"
            assert result["entities_created"] == 0

            await storage.close()
