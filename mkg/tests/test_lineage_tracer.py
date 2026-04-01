# mkg/tests/test_lineage_tracer.py
"""Tests for LineageTracer — full signal-to-article traceability.

Iterations 16-20: Given a signal enrichment result, trace back the complete
chain: enrichment → causal chains → entities → articles → data sources.
"""

import pytest


class TestLineageTracing:
    """Trace from signal enrichment back to source data."""

    def _build_tracer(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager

        pt = ProvenanceTracker()
        cm = ComplianceManager()
        return LineageTracer(provenance_tracker=pt, compliance_manager=cm), pt, cm

    def test_trace_enrichment_to_articles(self):
        """Given enrichment result, find which articles produced it."""
        lt, pt, _ = self._build_tracer()

        # Record provenance for two articles
        pt.record_step("art-001", "extraction", {"source": "reuters"}, {"entities_count": 2})
        pt.record_entity_origin("tsmc-001", "TSMC", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1_cloud", 0.92)
        pt.record_edge_origin("ed-001", "TSMC", "NVIDIA", "SUPPLIES_TO", "art-001", 0.9)

        pt.record_step("art-002", "extraction", {"source": "bloomberg"}, {"entities_count": 1})
        pt.record_entity_origin("apple-001", "Apple", "art-002", "tier_3_regex", 0.85)

        # Build enrichment-like result with entity references
        enrichment_context = {
            "entity_ids": ["tsmc-001", "nvidia-001", "apple-001"],
            "article_ids": ["art-001", "art-002"],
        }

        lineage = lt.trace_enrichment(enrichment_context)
        assert len(lineage["source_articles"]) == 2
        assert len(lineage["entities_involved"]) == 3

    def test_trace_single_entity_lineage(self):
        """Trace a single entity back to its articles."""
        lt, pt, _ = self._build_tracer()

        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-003", "tier_3_regex", 0.80)

        lineage = lt.trace_entity("nvidia-001")
        assert lineage["entity_id"] == "nvidia-001"
        assert len(lineage["source_articles"]) == 2
        assert lineage["highest_confidence"] == 0.95
        assert lineage["extraction_tiers_used"] == {"tier_1_cloud", "tier_3_regex"}

    def test_trace_causal_chain_lineage(self):
        """Trace a causal chain to its source data."""
        lt, pt, _ = self._build_tracer()

        pt.record_entity_origin("tsmc-001", "TSMC", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1_cloud", 0.92)
        pt.record_propagation("tsmc-001", "fab fire", "art-001", 3, 2, 2)

        chain = {
            "trigger": "tsmc-001",
            "trigger_name": "TSMC",
            "affected_entity": "nvidia-001",
            "affected_name": "NVIDIA",
            "impact_score": 0.85,
        }

        lineage = lt.trace_chain(chain)
        assert lineage["trigger_article"] == "art-001"
        assert lineage["trigger_confidence"] == 0.95

    def test_trace_returns_data_sources(self):
        """Lineage must include data source attribution."""
        lt, pt, _ = self._build_tracer()

        pt.record_step("art-001", "extraction",
                        {"source": "reuters", "url": "https://reuters.com/tsmc"}, {})
        pt.record_entity_origin("tsmc-001", "TSMC", "art-001", "tier_1", 0.9)

        lineage = lt.trace_entity("tsmc-001")
        assert len(lineage["data_sources"]) >= 1
        assert lineage["data_sources"][0]["source"] == "reuters"

    def test_trace_with_compliance_wrap(self):
        """Full lineage includes compliance disclaimers."""
        lt, pt, cm = self._build_tracer()

        pt.record_step("art-001", "extraction", {"source": "reuters"}, {})
        pt.record_entity_origin("tsmc-001", "TSMC", "art-001", "tier_1", 0.95)

        enrichment_context = {
            "entity_ids": ["tsmc-001"],
            "article_ids": ["art-001"],
            "supply_chain_risk": 0.8,
            "confidence_adjustment": -10,
            "has_material_impact": True,
        }

        full_lineage = lt.trace_enrichment_with_compliance(enrichment_context)
        assert "disclaimers" in full_lineage
        assert "lineage" in full_lineage
        assert "classification" in full_lineage


class TestLineageSummary:
    """Summary reports for lineage data."""

    def test_lineage_summary(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager

        pt = ProvenanceTracker()
        lt = LineageTracer(provenance_tracker=pt, compliance_manager=ComplianceManager())

        pt.record_entity_origin("e1", "TSMC", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("e2", "NVIDIA", "art-001", "tier_1_cloud", 0.92)
        pt.record_entity_origin("e3", "Apple", "art-002", "tier_3_regex", 0.85)

        summary = lt.get_summary()
        assert summary["total_entities_traced"] == 3
        assert summary["total_articles_referenced"] >= 1
        assert "tier_distribution" in summary

    def test_empty_lineage_summary(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager

        pt = ProvenanceTracker()
        lt = LineageTracer(provenance_tracker=pt, compliance_manager=ComplianceManager())
        summary = lt.get_summary()
        assert summary["total_entities_traced"] == 0
