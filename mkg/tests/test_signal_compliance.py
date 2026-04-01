# mkg/tests/test_signal_compliance.py
"""Tests for Signal Compliance Integration — Iterations 26-30.

Verifies that SignalBridge wraps enrichment outputs with compliance
metadata (disclaimers, data source disclosure, regulatory classification)
using ComplianceManager and LineageTracer.
"""

import pytest

from mkg.domain.services.signal_bridge import SignalBridge
from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType
from mkg.domain.services.provenance_tracker import ProvenanceTracker
from mkg.domain.services.lineage_tracer import LineageTracer


def _make_pipeline_result(
    article_id: str = "art-001",
    impacts: list | None = None,
    chains: list | None = None,
    table: dict | None = None,
    provenance_chain: dict | None = None,
) -> dict:
    """Build a minimal pipeline result for testing."""
    return {
        "article_id": article_id,
        "status": "completed",
        "tier_used": "tier_3",
        "entities_created": 2,
        "relations_created": 1,
        "propagation_ran": True,
        "impacts": impacts or [
            {"entity_id": "e1", "entity_name": "NVIDIA", "impact": 0.8},
            {"entity_id": "e2", "entity_name": "Apple", "impact": 0.3},
        ],
        "causal_chains": chains or [
            {
                "trigger_name": "TSMC",
                "affected_name": "NVIDIA",
                "trigger_event": "fab fire",
                "impact_score": 0.85,
                "hops": 1,
                "narrative": "TSMC fab disruption impacts NVIDIA chip supply",
            },
        ],
        "impact_table": table or {
            "rows": [
                {"entity_name": "NVIDIA", "impact_pct": 80, "entity_type": "Company"},
            ],
        },
        "provenance_chain": provenance_chain or {
            "article_id": article_id,
            "steps": [
                {"step": "extraction", "inputs": {"source": "reuters"}, "outputs": {}},
            ],
        },
    }


class TestSignalComplianceWrap:
    """Signal enrichment must carry compliance metadata."""

    def _build_bridge(self):
        pt = ProvenanceTracker()
        cm = ComplianceManager()
        lt = LineageTracer(provenance_tracker=pt, compliance_manager=cm)
        bridge = SignalBridge(
            compliance_manager=cm,
            lineage_tracer=lt,
        )
        return bridge, pt, cm, lt

    def test_enrichment_includes_disclaimers(self):
        """Every enrichment must include mandatory disclaimers."""
        bridge, _, _, _ = self._build_bridge()
        result = bridge.enrich_signal_with_compliance("NVIDIA", _make_pipeline_result())
        assert "disclaimers" in result
        assert len(result["disclaimers"]) >= 2  # NOT_FINANCIAL_ADVICE + AI_GENERATED

    def test_enrichment_includes_classification(self):
        """Enrichment must include regulatory risk classification."""
        bridge, _, _, _ = self._build_bridge()
        result = bridge.enrich_signal_with_compliance("NVIDIA", _make_pipeline_result())
        assert "classification" in result
        assert "risk_level" in result["classification"]

    def test_high_risk_enrichment_adds_risk_warning(self):
        """High supply chain risk triggers RISK_WARNING disclaimer."""
        bridge, _, _, _ = self._build_bridge()
        # High impact pipeline result
        high_impact = _make_pipeline_result(
            impacts=[{"entity_id": "e1", "entity_name": "NVIDIA", "impact": 0.95}],
        )
        result = bridge.enrich_signal_with_compliance("NVIDIA", high_impact)
        disclaimer_texts = result["disclaimers"]
        risk_text = "substantial risk of loss"
        assert any(risk_text in d for d in disclaimer_texts)

    def test_enrichment_includes_data_sources(self):
        """Enrichment must disclose data sources."""
        bridge, pt, _, _ = self._build_bridge()
        # Record provenance to have data sources
        pt.record_step("art-001", "extraction", {"source": "reuters", "url": "https://reuters.com"}, {})
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1", 0.95)

        result = bridge.enrich_signal_with_compliance("NVIDIA", _make_pipeline_result())
        assert "data_sources" in result
        assert len(result["data_sources"]) >= 1

    def test_enrichment_includes_original_data(self):
        """Compliance wrapping preserves original enrichment data."""
        bridge, _, _, _ = self._build_bridge()
        result = bridge.enrich_signal_with_compliance("NVIDIA", _make_pipeline_result())
        assert "supply_chain_risk" in result
        assert "confidence_adjustment" in result
        assert "risk_factors" in result

    def test_empty_pipeline_result_still_has_compliance(self):
        """Even empty enrichment gets disclaimers."""
        bridge, _, _, _ = self._build_bridge()
        empty_result = {
            "status": "completed",
            "impacts": [],
            "causal_chains": [],
            "impact_table": {},
            "provenance_chain": {"article_id": "x", "steps": []},
        }
        result = bridge.enrich_signal_with_compliance("NVIDIA", empty_result)
        assert "disclaimers" in result
        assert len(result["disclaimers"]) >= 2

    def test_classification_reflects_impact(self):
        """Classification risk level should reflect supply chain risk."""
        bridge, _, _, _ = self._build_bridge()
        high = _make_pipeline_result(
            impacts=[{"entity_id": "e1", "entity_name": "NVIDIA", "impact": 0.95}],
        )
        result = bridge.enrich_signal_with_compliance("NVIDIA", high)
        # High impact should produce medium or high classification
        assert result["classification"]["risk_level"] in ("medium", "high")

    def test_original_enrich_signal_still_works(self):
        """Original enrich_signal() method remains unchanged (backward compat)."""
        bridge, _, _, _ = self._build_bridge()
        result = bridge.enrich_signal("NVIDIA", _make_pipeline_result())
        assert "supply_chain_risk" in result
        assert "disclaimers" not in result  # Original method has no compliance


class TestSignalBridgeBackwardCompat:
    """Signal bridge without compliance (backward compat)."""

    def test_bridge_without_compliance_still_works(self):
        """SignalBridge with no compliance manager still produces enrichment."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVIDIA", _make_pipeline_result())
        assert "supply_chain_risk" in result
        assert result["has_material_impact"] is True

    def test_bridge_without_compliance_no_disclaimers(self):
        """Old-style bridge has no disclaimers."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVIDIA", _make_pipeline_result())
        assert "disclaimers" not in result
