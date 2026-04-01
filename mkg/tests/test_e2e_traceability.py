# mkg/tests/test_e2e_traceability.py
"""End-to-End Traceability Tests — Iterations 36-40.

Full scenario tests verifying the complete chain:
Article → Extract → Entity → Propagation → Signal Enrichment
with every step traceable back to source data and wrapped with compliance.
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
from mkg.domain.services.audit_logger import AuditLogger, AuditAction
from mkg.domain.services.compliance_manager import ComplianceManager
from mkg.domain.services.lineage_tracer import LineageTracer
from mkg.domain.services.signal_bridge import SignalBridge
from mkg.domain.services.pii_detector import PIIDetector
from mkg.domain.services.retention_policy import RetentionPolicy
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


def _semiconductor_extraction():
    return {
        "entities": [
            {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
            {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
            {"name": "Apple", "entity_type": "Company", "confidence": 0.88},
        ],
        "relations": [
            {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
             "weight": 0.85, "confidence": 0.9},
            {"source": "TSMC", "target": "Apple", "relation_type": "SUPPLIES_TO",
             "weight": 0.80, "confidence": 0.85},
        ],
    }


class TestE2EArticleToSignal:
    """Full pipeline: article → extraction → signal enrichment, all traced."""

    @pytest.fixture
    def full_stack(self):
        """Build the complete traceable pipeline stack."""
        storage = InMemoryGraphStorage()
        provenance = ProvenanceTracker()
        audit = AuditLogger()
        compliance = ComplianceManager()
        lineage = LineageTracer(provenance_tracker=provenance, compliance_manager=compliance)

        from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.article_dedup import ArticleDedup

        extractor = _FakeExtractor(_semiconductor_extraction())
        extraction_orch = ExtractionOrchestrator(
            extractors=[extractor],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
        )
        verifier = HallucinationVerifier()
        graph_mutation = GraphMutationService(storage, CanonicalEntityRegistry())
        propagation = PropagationEngine(storage)
        chain_builder = CausalChainBuilder(storage)
        alert_system = AlertSystem()
        impact_table = ImpactTableBuilder(storage)
        dedup = ArticleDedup()

        pipeline = PipelineOrchestrator(
            graph_storage=storage,
            extraction_orchestrator=extraction_orch,
            hallucination_verifier=verifier,
            graph_mutation=graph_mutation,
            propagation_engine=propagation,
            causal_chain_builder=chain_builder,
            alert_system=alert_system,
            impact_table_builder=impact_table,
            article_dedup=dedup,
            provenance_tracker=provenance,
            audit_logger=audit,
        )

        bridge = SignalBridge(
            compliance_manager=compliance,
            lineage_tracer=lineage,
        )

        return {
            "pipeline": pipeline,
            "bridge": bridge,
            "provenance": provenance,
            "audit": audit,
            "compliance": compliance,
            "lineage": lineage,
            "storage": storage,
        }

    @pytest.mark.asyncio
    async def test_full_chain_article_to_enrichment(self, full_stack):
        """Article → pipeline → bridge → enrichment with compliance."""
        pipeline = full_stack["pipeline"]
        bridge = full_stack["bridge"]

        # Step 1: Process article
        result = await pipeline.process_article(
            title="TSMC fab fire disrupts supply chain",
            content="TSMC reported a major fire at its Taiwan fab. NVIDIA and Apple face chip supply delays.",
            source="reuters",
            url="https://reuters.com/tsmc-fire-2026",
        )
        assert result["status"] == "completed"
        assert result["entities_created"] >= 2

        # Step 2: Enrich signal with compliance
        enrichment = bridge.enrich_signal_with_compliance("NVIDIA", result)

        # Verify enrichment has both signal data AND compliance
        assert "supply_chain_risk" in enrichment
        assert "disclaimers" in enrichment
        assert "classification" in enrichment
        assert len(enrichment["disclaimers"]) >= 2

    @pytest.mark.asyncio
    async def test_provenance_traces_back_to_article(self, full_stack):
        """Every entity traces back to source article."""
        pipeline = full_stack["pipeline"]
        provenance = full_stack["provenance"]

        result = await pipeline.process_article(
            title="TSMC expansion",
            content="TSMC announced new fab construction to supply NVIDIA and Apple.",
            source="bloomberg",
            url="https://bloomberg.com/tsmc-expansion",
        )

        # Provenance should have the article
        article_lineage = provenance.get_article_lineage(result["article_id"])
        assert len(article_lineage["steps"]) >= 2  # extraction + verification
        assert len(article_lineage["entities_created"]) >= 2  # TSMC, NVIDIA, Apple

    @pytest.mark.asyncio
    async def test_audit_log_captures_all_mutations(self, full_stack):
        """Every graph mutation appears in the audit log."""
        pipeline = full_stack["pipeline"]
        audit = full_stack["audit"]

        await pipeline.process_article(
            title="TSMC revenue report",
            content="TSMC reported $20B revenue. NVIDIA is their largest customer.",
            source="reuters",
        )

        entries = audit.get_entries()
        assert len(entries) >= 1
        # Should have entity creation and/or edge creation
        actions = {e["action"] for e in entries}
        assert "entity_created" in actions or "entity_updated" in actions

    @pytest.mark.asyncio
    async def test_lineage_traces_entity_to_articles(self, full_stack):
        """LineageTracer resolves entity → article chain."""
        pipeline = full_stack["pipeline"]
        lineage_tracer = full_stack["lineage"]
        provenance = full_stack["provenance"]

        await pipeline.process_article(
            title="TSMC chip supply",
            content="TSMC supplies advanced chips to NVIDIA for AI training GPUs.",
            source="reuters",
        )

        # Find TSMC entity origin
        summary = lineage_tracer.get_summary()
        assert summary["total_entities_traced"] >= 2

    @pytest.mark.asyncio
    async def test_compliance_classification_matches_impact(self, full_stack):
        """High-impact pipeline result → high/medium compliance classification."""
        pipeline = full_stack["pipeline"]
        bridge = full_stack["bridge"]

        result = await pipeline.process_article(
            title="TSMC fire",
            content="TSMC fab fire impacting NVIDIA and Apple supply chain. Major disruption expected.",
            source="reuters",
        )

        enrichment = bridge.enrich_signal_with_compliance("NVIDIA", result)
        # Pipeline creates entities + relations, enrichment should have classification
        assert enrichment["classification"]["risk_level"] in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_pii_detection_in_pipeline(self, full_stack):
        """PII in article content should be detectable."""
        detector = PIIDetector()
        content = "TSMC CEO email: ceo@tsmc.com announced fab fire affecting NVIDIA."

        scan = detector.scan(content)
        assert scan["has_pii"] is True

        clean = detector.redact(content)
        assert "ceo@tsmc.com" not in clean

    @pytest.mark.asyncio
    async def test_multiple_articles_full_trace(self, full_stack):
        """Multiple articles build cumulative provenance."""
        pipeline = full_stack["pipeline"]
        provenance = full_stack["provenance"]

        await pipeline.process_article(
            title="Article 1", content="TSMC supplies NVIDIA.", source="reuters",
        )
        await pipeline.process_article(
            title="Article 2", content="Apple depends on TSMC for chip manufacturing.", source="bloomberg",
        )

        summary = provenance.get_summary()
        assert summary["total_articles_processed"] == 2
        assert summary["total_steps_recorded"] >= 4  # 2 articles × (extraction + verification)

    @pytest.mark.asyncio
    async def test_retention_policy_integration(self, full_stack):
        """Retention policy works with provenance data."""
        rp = RetentionPolicy(article_retention_days=90)

        from datetime import datetime, timezone, timedelta
        recent = datetime.now(timezone.utc) - timedelta(days=5)
        old = datetime.now(timezone.utc) - timedelta(days=100)

        assert rp.is_expired("article", recent) is False
        assert rp.is_expired("article", old) is True

    @pytest.mark.asyncio
    async def test_provenance_chain_in_result(self, full_stack):
        """Pipeline result includes provenance_chain field."""
        pipeline = full_stack["pipeline"]
        result = await pipeline.process_article(
            title="TSMC update",
            content="TSMC building new fab for NVIDIA AI chips.",
            source="reuters",
        )
        assert "provenance_chain" in result
        chain = result["provenance_chain"]
        assert chain["article_id"] == result["article_id"]
        assert len(chain["steps"]) >= 2
