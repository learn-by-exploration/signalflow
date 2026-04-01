# mkg/tests/test_pipeline_provenance.py
"""Tests for Pipeline Provenance Wiring — Iterations 21-25.

Verifies that PipelineOrchestrator automatically records provenance
(via ProvenanceTracker) and audit entries (via AuditLogger) for every
pipeline step: dedup, extraction, verification, mutation, propagation.
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
from mkg.domain.services.provenance_tracker import ProvenanceTracker
from mkg.domain.services.audit_logger import AuditLogger
from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage


class _FakeExtractor:
    def __init__(self, result: dict):
        self._result = result

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_3

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0

    async def extract_all(self, text: str, context=None) -> dict:
        return self._result


def _sample_extraction():
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


class TestPipelineProvenance:
    """Verify provenance is recorded at each pipeline step."""

    @pytest.fixture
    def storage(self):
        return InMemoryGraphStorage()

    @pytest.fixture
    def provenance(self):
        return ProvenanceTracker()

    @pytest.fixture
    def audit(self):
        return AuditLogger()

    @pytest.fixture
    def orchestrator(self, storage, provenance, audit):
        from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.article_dedup import ArticleDedup

        extractor = _FakeExtractor(_sample_extraction())
        extraction_orch = ExtractionOrchestrator(
            extractors=[extractor],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
        )
        verifier = HallucinationVerifier()
        propagation = PropagationEngine(storage)
        chain_builder = CausalChainBuilder(storage)
        alert_system = AlertSystem()
        impact_table = ImpactTableBuilder(storage)
        dedup = ArticleDedup()

        return PipelineOrchestrator(
            graph_storage=storage,
            extraction_orchestrator=extraction_orch,
            hallucination_verifier=verifier,
            graph_mutation=GraphMutationService(storage, CanonicalEntityRegistry()),
            propagation_engine=propagation,
            causal_chain_builder=chain_builder,
            alert_system=alert_system,
            impact_table_builder=impact_table,
            article_dedup=dedup,
            provenance_tracker=provenance,
            audit_logger=audit,
        )

    @pytest.mark.asyncio
    async def test_extraction_recorded_in_provenance(self, orchestrator, provenance):
        """Pipeline extraction step creates provenance records."""
        result = await orchestrator.process_article(
            title="TSMC fab disruption",
            content="TSMC reported a major fire at its Taiwan fab, affecting NVIDIA supply.",
            source="reuters",
            url="https://reuters.com/tsmc-fire",
        )
        assert result["status"] == "completed"

        # Provenance should have extraction step
        records = provenance.get_records(result["article_id"])
        step_names = [r["step"] for r in records]
        assert "extraction" in step_names

    @pytest.mark.asyncio
    async def test_entity_origins_recorded(self, orchestrator, provenance):
        """Extracted entities have provenance origin records."""
        result = await orchestrator.process_article(
            title="TSMC + NVIDIA",
            content="TSMC supplies chips to NVIDIA for GPU production.",
            source="bloomberg",
        )

        # Should have entity origins for extracted entities
        summary = provenance.get_summary()
        assert summary["total_entities_tracked"] >= 2  # TSMC, NVIDIA at minimum

    @pytest.mark.asyncio
    async def test_mutation_recorded_in_audit(self, orchestrator, audit):
        """Graph mutations appear in the audit log."""
        await orchestrator.process_article(
            title="TSMC NVIDIA supply",
            content="TSMC is a major supplier to NVIDIA.",
            source="reuters",
        )

        entries = audit.get_entries()
        action_names = [e["action"] if isinstance(e["action"], str) else e["action"].value for e in entries]
        assert "entity_created" in action_names or "entity_updated" in action_names

    @pytest.mark.asyncio
    async def test_dedup_skip_recorded_in_provenance(self, orchestrator, provenance):
        """Duplicate articles still get provenance (as 'duplicate' status)."""
        url = "https://reuters.com/tsmc-dup"
        await orchestrator.process_article(
            title="First", content="TSMC fab fire report.", source="reuters", url=url,
        )
        result = await orchestrator.process_article(
            title="Duplicate", content="TSMC fab fire report.", source="reuters", url=url,
        )
        assert result["status"] == "duplicate"

        records = provenance.get_records(result["article_id"])
        step_names = [r["step"] for r in records]
        assert "dedup" in step_names

    @pytest.mark.asyncio
    async def test_verification_recorded_in_provenance(self, orchestrator, provenance):
        """Hallucination verification step appears in provenance."""
        result = await orchestrator.process_article(
            title="TSMC fab",
            content="TSMC reported a disruption impacting NVIDIA chip supply.",
            source="reuters",
        )

        records = provenance.get_records(result["article_id"])
        step_names = [r["step"] for r in records]
        assert "verification" in step_names

    @pytest.mark.asyncio
    async def test_propagation_recorded_in_provenance(self, orchestrator, provenance, storage):
        """If propagation runs, it appears in provenance."""
        # First article to populate graph
        await orchestrator.process_article(
            title="TSMC base", content="TSMC supplies NVIDIA with chips.", source="reuters",
        )

        result = await orchestrator.process_article(
            title="TSMC fire",
            content="TSMC fire disrupts semiconductor supply to NVIDIA customers.",
            source="reuters",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="fab fire",
        )

        if result.get("propagation_ran"):
            records = provenance.get_records(result["article_id"])
            step_names = [r["step"] for r in records]
            assert "propagation" in step_names

    @pytest.mark.asyncio
    async def test_empty_content_not_recorded(self, orchestrator, provenance):
        """Empty content fails fast — no provenance pollution."""
        result = await orchestrator.process_article(
            title="Empty", content="", source="reuters",
        )
        assert result["status"] == "failed"
        # No provenance for failed articles (optional, but clean)
        records = provenance.get_records(result["article_id"])
        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_provenance_summary_after_pipeline(self, orchestrator, provenance):
        """Provenance summary reflects pipeline activity."""
        await orchestrator.process_article(
            title="Article 1", content="TSMC supplies NVIDIA.", source="reuters",
        )
        summary = provenance.get_summary()
        assert summary["total_articles_processed"] >= 1
        assert summary["total_steps_recorded"] >= 2  # extraction + verification at minimum

    @pytest.mark.asyncio
    async def test_result_includes_provenance_chain(self, orchestrator):
        """Pipeline result includes provenance_chain for downstream tracing."""
        result = await orchestrator.process_article(
            title="TSMC article",
            content="TSMC reported strong revenue driven by NVIDIA demand.",
            source="reuters",
        )
        assert "provenance_chain" in result
        assert "article_id" in result["provenance_chain"]
        assert len(result["provenance_chain"]["steps"]) >= 1
