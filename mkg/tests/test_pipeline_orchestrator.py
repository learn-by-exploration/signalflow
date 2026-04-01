# mkg/tests/test_pipeline_orchestrator.py
"""Tests for PipelineOrchestrator — full end-to-end article processing.

Iterations 21-25: Article → Extract → Verify → Mutate → Propagate → Alert.
"""

import pytest

from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
from mkg.domain.services.causal_chain_builder import CausalChainBuilder
from mkg.domain.services.cost_governance import CostGovernance
from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
from mkg.domain.services.graph_mutation import GraphMutationService
from mkg.domain.services.hallucination_verifier import HallucinationVerifier
from mkg.domain.services.impact_table import ImpactTableBuilder
from mkg.domain.services.propagation_engine import PropagationEngine
from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage


class _FakeExtractor:
    """Returns predefined extraction results."""

    def __init__(self, result: dict):
        self._result = result
        self.call_count = 0

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_3

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0

    async def extract_all(self, text: str, context=None) -> dict:
        self.call_count += 1
        return self._result


def _semiconductor_extraction():
    """Simulated extraction from a TSMC fab disruption article."""
    return {
        "entities": [
            {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
            {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
            {"name": "Apple", "entity_type": "Company", "confidence": 0.88},
            {"name": "Taiwan", "entity_type": "Country", "confidence": 0.9},
        ],
        "relations": [
            {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
             "weight": 0.85, "confidence": 0.9},
            {"source": "TSMC", "target": "Apple", "relation_type": "SUPPLIES_TO",
             "weight": 0.80, "confidence": 0.85},
            {"source": "TSMC", "target": "Taiwan", "relation_type": "OPERATES_IN",
             "weight": 0.95, "confidence": 0.98},
        ],
    }


class TestPipelineOrchestrator:

    @pytest.fixture
    def storage(self):
        return InMemoryGraphStorage()

    @pytest.fixture
    def graph_mutation(self, storage):
        registry = CanonicalEntityRegistry()
        return GraphMutationService(storage, registry)

    @pytest.fixture
    def orchestrator(self, storage, graph_mutation):
        from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.article_dedup import ArticleDedup

        extractor = _FakeExtractor(_semiconductor_extraction())
        extraction_orch = ExtractionOrchestrator(
            extractors=[extractor],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
        )

        return PipelineOrchestrator(
            graph_storage=storage,
            extraction_orchestrator=extraction_orch,
            hallucination_verifier=HallucinationVerifier(),
            graph_mutation=graph_mutation,
            propagation_engine=PropagationEngine(storage),
            causal_chain_builder=CausalChainBuilder(storage),
            alert_system=AlertSystem(),
            impact_table_builder=ImpactTableBuilder(storage),
            article_dedup=ArticleDedup(),
        )

    @pytest.mark.asyncio
    async def test_process_article_creates_entities(self, orchestrator, storage):
        """Processing an article should create entities in the graph."""
        result = await orchestrator.process_article(
            title="TSMC fab disruption affects NVIDIA and Apple supply chains",
            content="TSMC, the world's largest semiconductor manufacturer based in Taiwan, "
                    "supplies chips to NVIDIA for AI GPUs and to Apple for iPhone processors.",
            source="reuters",
            url="https://reuters.com/tsmc-disruption",
        )

        assert result["status"] == "completed"
        assert result["entities_created"] > 0

        # Verify entities exist in graph
        entities = await storage.find_entities(entity_type="Company")
        names = {e["name"] for e in entities}
        assert "TSMC" in names

    @pytest.mark.asyncio
    async def test_process_article_creates_edges(self, orchestrator, storage):
        """Processing should create relationship edges."""
        result = await orchestrator.process_article(
            title="TSMC supplies NVIDIA and Apple",
            content="TSMC supplies chips to NVIDIA and Apple. TSMC operates in Taiwan.",
            source="test",
        )

        assert result["relations_created"] > 0
        edges = await storage.find_edges(relation_type="SUPPLIES_TO")
        assert len(edges) >= 1

    @pytest.mark.asyncio
    async def test_process_article_runs_propagation(self, orchestrator):
        """Should run propagation and return impact results."""
        result = await orchestrator.process_article(
            title="TSMC fab fire",
            content="TSMC fab fire disrupts chip supply to NVIDIA and Apple in Taiwan.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="fab fire",
        )

        assert result["propagation_ran"] is True
        assert len(result.get("impacts", [])) > 0

    @pytest.mark.asyncio
    async def test_process_article_generates_causal_chains(self, orchestrator):
        """Should generate causal chains from propagation."""
        result = await orchestrator.process_article(
            title="TSMC earthquake impact",
            content="TSMC earthquake disruption affects NVIDIA GPU supply and Apple iPhone production in Taiwan.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="earthquake disruption",
        )

        chains = result.get("causal_chains", [])
        assert len(chains) > 0
        assert any("narrative" in c for c in chains)

    @pytest.mark.asyncio
    async def test_process_article_generates_alerts(self, orchestrator):
        """Should generate alerts from high-impact chains."""
        result = await orchestrator.process_article(
            title="TSMC Taiwan disruption",
            content="TSMC Taiwan disruption hits NVIDIA and Apple chip supplies.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="disruption",
        )

        assert "alerts" in result

    @pytest.mark.asyncio
    async def test_process_article_returns_impact_table(self, orchestrator):
        """Should return ranked impact table."""
        result = await orchestrator.process_article(
            title="TSMC supply shock",
            content="TSMC supply shock hits NVIDIA AI GPU and Apple processor lines in Taiwan.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="supply shock",
        )

        table = result.get("impact_table", {})
        assert "rows" in table or "trigger_name" in table

    @pytest.mark.asyncio
    async def test_duplicate_article_skipped(self, orchestrator):
        """Processing the same article twice should skip the duplicate."""
        content = "TSMC fab disruption affects NVIDIA supply in Taiwan."
        r1 = await orchestrator.process_article(
            title="TSMC disruption", content=content, source="test",
            url="https://example.com/same-article",
        )
        r2 = await orchestrator.process_article(
            title="TSMC disruption copy", content=content, source="test",
            url="https://example.com/same-article",
        )
        assert r1["status"] == "completed"
        assert r2["status"] == "duplicate"

    @pytest.mark.asyncio
    async def test_empty_content_fails_gracefully(self, orchestrator):
        """Empty content should fail gracefully."""
        result = await orchestrator.process_article(
            title="Empty", content="", source="test",
        )
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_result_includes_metadata(self, orchestrator):
        """Result should include timing and tier metadata."""
        result = await orchestrator.process_article(
            title="TSMC test",
            content="TSMC supplies chips to NVIDIA for AI GPUs in Taiwan.",
            source="test",
        )
        assert "article_id" in result
        assert "tier_used" in result
        assert "status" in result
