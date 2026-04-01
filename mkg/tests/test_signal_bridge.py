# mkg/tests/test_signal_bridge.py
"""Tests for SignalBridge — MKG-to-signal integration.

Iteration 31: Tests that the bridge correctly translates MKG pipeline
results into signal enrichment data.
"""

import pytest

from mkg.domain.services.signal_bridge import SignalBridge


class TestSignalBridgeEmptyInputs:
    """Edge cases: empty/None/failed pipeline results."""

    def test_none_pipeline_result(self):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", None)
        assert result["has_material_impact"] is False
        assert result["supply_chain_risk"] == 0.0
        assert result["confidence_adjustment"] == 0

    def test_empty_pipeline_result(self):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", {})
        assert result["has_material_impact"] is False

    def test_failed_pipeline_result(self):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", {"status": "failed"})
        assert result["has_material_impact"] is False

    def test_no_impacts(self):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", {
            "status": "completed",
            "impacts": [],
            "causal_chains": [],
        })
        assert result["has_material_impact"] is False
        assert result["risk_factors"] == []

    def test_below_threshold_impacts(self):
        """Impacts below MIN_IMPACT_THRESHOLD are ignored."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", {
            "status": "completed",
            "impacts": [{"entity_id": "e1", "impact": 0.01}],
            "causal_chains": [],
        })
        assert result["has_material_impact"] is False


class TestSignalBridgeEnrichment:
    """Core enrichment: supply chain risk, confidence adjustment, risk factors."""

    @pytest.fixture
    def tsmc_pipeline_result(self):
        """Simulated TSMC fab disruption pipeline result."""
        return {
            "status": "completed",
            "entities_created": 4,
            "relations_created": 3,
            "propagation_ran": True,
            "impacts": [
                {"entity_id": "nvidia-1", "impact": 0.85, "depth": 1,
                 "path": ["tsmc-1", "nvidia-1"]},
                {"entity_id": "apple-1", "impact": 0.80, "depth": 1,
                 "path": ["tsmc-1", "apple-1"]},
                {"entity_id": "amd-1", "impact": 0.45, "depth": 2,
                 "path": ["tsmc-1", "nvidia-1", "amd-1"]},
            ],
            "causal_chains": [
                {
                    "trigger": "tsmc-1",
                    "trigger_name": "TSMC",
                    "trigger_event": "fab fire",
                    "affected_entity": "nvidia-1",
                    "affected_name": "NVIDIA",
                    "impact_score": 0.85,
                    "hops": 1,
                    "path": ["tsmc-1", "nvidia-1"],
                    "edge_labels": ["SUPPLIES_TO"],
                    "narrative": "fab fire at TSMC affects NVIDIA via supplies to (85% impact).",
                },
                {
                    "trigger": "tsmc-1",
                    "trigger_name": "TSMC",
                    "trigger_event": "fab fire",
                    "affected_entity": "apple-1",
                    "affected_name": "Apple",
                    "impact_score": 0.80,
                    "hops": 1,
                    "path": ["tsmc-1", "apple-1"],
                    "edge_labels": ["SUPPLIES_TO"],
                    "narrative": "fab fire at TSMC affects Apple via supplies to (80% impact).",
                },
            ],
            "impact_table": {
                "rows": [
                    {"rank": 1, "entity_name": "NVIDIA", "impact_pct": 85,
                     "entity_type": "Company", "entity_id": "nvidia-1"},
                    {"rank": 2, "entity_name": "Apple", "impact_pct": 80,
                     "entity_type": "Company", "entity_id": "apple-1"},
                    {"rank": 3, "entity_name": "AMD", "impact_pct": 45,
                     "entity_type": "Company", "entity_id": "amd-1"},
                ],
                "total": 3,
                "trigger": "TSMC",
            },
        }

    def test_has_material_impact(self, tsmc_pipeline_result):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        assert result["has_material_impact"] is True

    def test_supply_chain_risk_high(self, tsmc_pipeline_result):
        """High-impact events yield high supply chain risk."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        assert result["supply_chain_risk"] >= 0.5

    def test_confidence_adjustment_negative_for_disruption(self, tsmc_pipeline_result):
        """Supply disruption should produce negative confidence adjustment."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVIDIA", tsmc_pipeline_result)
        assert result["confidence_adjustment"] < 0

    def test_confidence_adjustment_capped(self, tsmc_pipeline_result):
        """Adjustment should not exceed MAX_CONFIDENCE_ADJUSTMENT."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVIDIA", tsmc_pipeline_result)
        assert abs(result["confidence_adjustment"]) <= SignalBridge.MAX_CONFIDENCE_ADJUSTMENT

    def test_risk_factors_populated(self, tsmc_pipeline_result):
        """Risk factors should contain relevant narratives."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVIDIA", tsmc_pipeline_result)
        assert len(result["risk_factors"]) > 0
        assert any("TSMC" in f for f in result["risk_factors"])

    def test_risk_factors_capped_at_5(self):
        """Should return at most 5 risk factors."""
        bridge = SignalBridge()
        chains = [
            {
                "trigger_name": f"COMPANY_{i}",
                "affected_name": "NVIDIA",
                "trigger_event": f"event_{i}",
                "impact_score": 0.6,
                "narrative": f"Event {i} at COMPANY_{i} affects NVIDIA.",
            }
            for i in range(10)
        ]
        result = bridge.enrich_signal("NVIDIA", {
            "status": "completed",
            "impacts": [{"entity_id": f"c-{i}", "impact": 0.6} for i in range(10)],
            "causal_chains": chains,
            "impact_table": {"rows": []},
        })
        assert len(result["risk_factors"]) <= 5

    def test_affected_companies_from_table(self, tsmc_pipeline_result):
        """Should extract company list from impact table."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        names = [c["name"] for c in result["affected_companies"]]
        assert "NVIDIA" in names
        assert "Apple" in names

    def test_reasoning_context_generated(self, tsmc_pipeline_result):
        """Should build plain text reasoning context for Claude prompt."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        ctx = result["reasoning_context"]
        assert "Supply Chain Analysis" in ctx
        assert "TSMC" in ctx
        assert "NVIDIA" in ctx

    def test_max_impact_reported(self, tsmc_pipeline_result):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        assert result["max_impact"] == 0.85

    def test_impact_count(self, tsmc_pipeline_result):
        bridge = SignalBridge()
        result = bridge.enrich_signal("NVDA", tsmc_pipeline_result)
        assert result["impact_count"] == 3

    def test_unrelated_symbol_gets_no_confidence_adj(self, tsmc_pipeline_result):
        """A symbol not in chains should get 0 adjustment."""
        bridge = SignalBridge()
        result = bridge.enrich_signal("RELIANCE", tsmc_pipeline_result)
        assert result["confidence_adjustment"] == 0
        # But still should report material impact (graph has impacts)
        assert result["has_material_impact"] is True
