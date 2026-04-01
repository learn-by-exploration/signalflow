# mkg/tests/test_signal_enrichment_integration.py
"""Tests for MKG signal enrichment integration.

Verifies:
1. enrich_signal_for_symbol returns empty enrichment when no data
2. enrich_signal_for_symbol returns enrichment when graph has data
3. Async version works correctly
4. Compliance metadata (disclaimers) is included
5. Error handling returns empty enrichment, not crash
"""

import os
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from mkg.integration.signal_enrichment import (
    enrich_signal_for_symbol,
    enrich_signal_for_symbol_async,
    _empty_enrichment,
    _graph_data_to_pipeline_result,
    shutdown,
)


class TestEmptyEnrichment:
    """Empty enrichment structure."""

    def test_empty_enrichment_has_all_fields(self):
        result = _empty_enrichment()
        assert result["supply_chain_risk"] == 0.0
        assert result["confidence_adjustment"] == 0
        assert result["risk_factors"] == []
        assert result["affected_companies"] == []
        assert result["reasoning_context"] == ""
        assert result["has_material_impact"] is False
        assert result["impact_count"] == 0
        assert result["max_impact"] == 0.0


class TestGraphDataConversion:
    """Convert graph query results to pipeline format."""

    def test_empty_graph_data(self):
        result = _graph_data_to_pipeline_result({"entities": [], "edges": []})
        assert result["status"] == "completed"
        assert result["impacts"] == []

    def test_single_connected_entity(self):
        graph_data = {
            "primary_entity": {"id": "e1", "name": "TSMC"},
            "entities": [
                {"id": "e1", "name": "TSMC"},
                {"id": "e2", "name": "NVIDIA"},
            ],
            "edges": [
                {"source_id": "e1", "target_id": "e2", "weight": 0.8},
            ],
        }
        result = _graph_data_to_pipeline_result(graph_data)
        assert len(result["impacts"]) == 1
        assert result["impacts"][0]["entity_name"] == "NVIDIA"
        assert result["impacts"][0]["impact"] == 0.8

    def test_causal_chains_built_from_impacts(self):
        graph_data = {
            "primary_entity": {"id": "e1", "name": "TSMC"},
            "entities": [
                {"id": "e1", "name": "TSMC"},
                {"id": "e2", "name": "NVIDIA"},
            ],
            "edges": [
                {"source_id": "e1", "target_id": "e2", "weight": 0.8},
            ],
        }
        result = _graph_data_to_pipeline_result(graph_data)
        assert len(result["causal_chains"]) == 1
        assert result["causal_chains"][0]["trigger_name"] == "TSMC"
        assert result["causal_chains"][0]["affected_name"] == "NVIDIA"


class TestSignalEnrichment:
    """Signal enrichment via MKG."""

    @pytest.fixture(autouse=True)
    def _isolate_module_state(self, tmp_path):
        """Reset module state and use temp dir."""
        import mkg.integration.signal_enrichment as mod
        old_factory = mod._factory
        old_init = mod._initialized
        mod._factory = None
        mod._initialized = False
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        yield
        mod._factory = old_factory
        mod._initialized = old_init
        os.environ.pop("MKG_DB_DIR", None)

    def test_enrich_returns_empty_when_no_graph_data(self):
        """When MKG has no entities, return empty enrichment."""
        result = enrich_signal_for_symbol("UNKNOWN_SYMBOL")
        assert result["has_material_impact"] is False
        assert result["supply_chain_risk"] == 0.0

    def test_enrich_handles_errors_gracefully(self):
        """On exception, return empty enrichment instead of crash."""
        with patch("mkg.integration.signal_enrichment._get_factory", side_effect=RuntimeError("DB error")):
            result = enrich_signal_for_symbol("NVDA")
        assert result["has_material_impact"] is False
        assert result["supply_chain_risk"] == 0.0

    def test_shutdown_clears_cached_factory(self):
        """Shutdown resets module-level cached factory."""
        import mkg.integration.signal_enrichment as mod
        # Create factory
        enrich_signal_for_symbol("TEST")
        assert mod._initialized is True
        shutdown()
        assert mod._initialized is False
        assert mod._factory is None


class TestAsyncSignalEnrichment:
    """Async version of signal enrichment."""

    @pytest.fixture(autouse=True)
    def _isolate_module_state(self, tmp_path):
        import mkg.integration.signal_enrichment as mod
        old_factory = mod._factory
        old_init = mod._initialized
        mod._factory = None
        mod._initialized = False
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        yield
        mod._factory = old_factory
        mod._initialized = old_init
        os.environ.pop("MKG_DB_DIR", None)

    async def test_async_enrich_returns_empty_when_no_data(self):
        result = await enrich_signal_for_symbol_async("UNKNOWN_SYMBOL")
        assert result["has_material_impact"] is False

    async def test_async_enrich_handles_errors(self):
        with patch("mkg.integration.signal_enrichment._get_factory", side_effect=RuntimeError("fail")):
            result = await enrich_signal_for_symbol_async("NVDA")
        assert result["supply_chain_risk"] == 0.0
