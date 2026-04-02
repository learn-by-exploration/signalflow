# mkg/tests/test_phase_c_advanced_intelligence.py
"""Phase C — Advanced Intelligence.

TDD Red tests for:
  C1: Contradiction detection & resolution
  C2: Shock event bypass in weight adjustment
  C3: Historical propagation replay
  C4: Multi-trigger simultaneous propagation
  C5: Confidence aggregation reporting
"""

import pytest
from datetime import datetime, timezone, timedelta

from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


@pytest.fixture
async def storage():
    s = SQLiteGraphStorage(":memory:")
    await s.initialize()
    yield s
    await s.close()


async def _seed_graph(storage):
    """Create a test graph: A->B->C, A->D, with varied directions."""
    await storage.create_entity("Company", {"name": "CompanyA", "canonical_name": "COMPANY_A"}, "a")
    await storage.create_entity("Company", {"name": "CompanyB", "canonical_name": "COMPANY_B"}, "b")
    await storage.create_entity("Company", {"name": "CompanyC", "canonical_name": "COMPANY_C"}, "c")
    await storage.create_entity("Company", {"name": "CompanyD", "canonical_name": "COMPANY_D"}, "d")

    await storage.create_edge("a", "b", "SUPPLIES_TO", {
        "weight": 0.9, "confidence": 0.95, "direction": "positive",
    })
    await storage.create_edge("b", "c", "SUPPLIES_TO", {
        "weight": 0.8, "confidence": 0.85, "direction": "positive",
    })
    await storage.create_edge("a", "d", "COMPETES_WITH", {
        "weight": 0.7, "confidence": 0.80, "direction": "negative",
    })


# ── C1: Contradiction Detection ──


class TestContradictionDetection:
    """C1: Detect contradictory signals about the same entity."""

    @pytest.mark.asyncio
    async def test_detector_exists(self):
        """ContradictionDetector class exists and is importable."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector
        detector = ContradictionDetector()
        assert detector is not None

    @pytest.mark.asyncio
    async def test_detect_opposing_signals(self):
        """Opposing signals for the same entity are flagged as contradictions."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector

        detector = ContradictionDetector()
        signals = [
            {"entity_id": "tsmc", "impact": 0.8, "direction": "positive", "source": "reuters"},
            {"entity_id": "tsmc", "impact": 0.6, "direction": "negative", "source": "bbc"},
        ]
        contradictions = detector.detect(signals)
        assert len(contradictions) >= 1
        assert contradictions[0]["entity_id"] == "tsmc"

    @pytest.mark.asyncio
    async def test_no_contradiction_for_same_direction(self):
        """Same-direction signals are not contradictions."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector

        detector = ContradictionDetector()
        signals = [
            {"entity_id": "tsmc", "impact": 0.8, "direction": "positive", "source": "reuters"},
            {"entity_id": "tsmc", "impact": 0.5, "direction": "positive", "source": "bbc"},
        ]
        contradictions = detector.detect(signals)
        assert len(contradictions) == 0

    @pytest.mark.asyncio
    async def test_contradiction_includes_resolution(self):
        """Each contradiction includes a suggested resolution strategy."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector

        detector = ContradictionDetector()
        signals = [
            {"entity_id": "tsmc", "impact": 0.8, "direction": "positive", "source": "reuters"},
            {"entity_id": "tsmc", "impact": 0.6, "direction": "negative", "source": "blog.example.com"},
        ]
        contradictions = detector.detect(signals)
        assert len(contradictions) >= 1
        c = contradictions[0]
        assert "resolution" in c
        assert c["resolution"] in ("higher_credibility", "higher_impact", "average", "flag_for_review")

    @pytest.mark.asyncio
    async def test_resolve_contradiction_by_credibility(self):
        """resolve() picks the signal from the more credible source."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector

        detector = ContradictionDetector()
        signals = [
            {"entity_id": "tsmc", "impact": 0.8, "direction": "positive", "source": "reuters.com", "credibility": 0.95},
            {"entity_id": "tsmc", "impact": 0.6, "direction": "negative", "source": "blog.example.com", "credibility": 0.3},
        ]
        resolved = detector.resolve(signals)
        # The higher-credibility source wins
        tsmc_resolved = [r for r in resolved if r["entity_id"] == "tsmc"]
        assert len(tsmc_resolved) == 1
        assert tsmc_resolved[0]["direction"] == "positive"

    @pytest.mark.asyncio
    async def test_different_entities_not_contradictions(self):
        """Opposing signals for DIFFERENT entities are not contradictions."""
        from mkg.domain.services.contradiction_detector import ContradictionDetector

        detector = ContradictionDetector()
        signals = [
            {"entity_id": "tsmc", "impact": 0.8, "direction": "positive", "source": "reuters"},
            {"entity_id": "nvidia", "impact": 0.6, "direction": "negative", "source": "bbc"},
        ]
        contradictions = detector.detect(signals)
        assert len(contradictions) == 0


# ── C2: Shock Event Bypass ──


class TestShockEventBypass:
    """C2: Shock events (black swan) bypass normal weight decay."""

    @pytest.mark.asyncio
    async def test_shock_event_flag(self):
        """Weight adjustment with is_shock=True bypasses normal decay."""
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService

        storage = SQLiteGraphStorage(":memory:")
        await storage.initialize()
        await _seed_graph(storage)

        was = WeightAdjustmentService(storage)

        # Get edge a->b
        edges = await storage.find_edges(source_id="a", target_id="b")
        assert len(edges) == 1
        edge_id = edges[0]["id"]

        # Shock event: weight jumps immediately
        result = await was.apply_shock(
            edge_id=edge_id,
            new_weight=0.99,
        )
        assert result is not None
        await storage.close()

    @pytest.mark.asyncio
    async def test_shock_event_produces_larger_change(self):
        """Shock events move weight more aggressively than normal updates."""
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService

        storage = SQLiteGraphStorage(":memory:")
        await storage.initialize()
        await _seed_graph(storage)

        was = WeightAdjustmentService(storage)
        edges = await storage.find_edges(source_id="a", target_id="b")
        edge_id = edges[0]["id"]
        old_weight = edges[0]["weight"]

        # Normal update (small alpha)
        await was.update_edge_weight(edge_id, 0.99, 0.3)
        edges_after_normal = await storage.find_edges(source_id="a", target_id="b")
        normal_delta = abs(edges_after_normal[0]["weight"] - old_weight)

        # Reset
        await storage.update_edge(edge_id, {"weight": old_weight})

        # Shock update — bypasses blending, goes straight to target
        await was.apply_shock(edge_id, 0.99)
        edges_after_shock = await storage.find_edges(source_id="a", target_id="b")
        shock_delta = abs(edges_after_shock[0]["weight"] - old_weight)

        assert shock_delta >= normal_delta
        await storage.close()


# ── C3: Historical Replay ──


class TestHistoricalReplay:
    """C3: Replay propagation at a past point in time."""

    @pytest.mark.asyncio
    async def test_propagation_at_past_time(self, storage):
        """Propagation with as_of returns only edges valid at that time."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        past = "2024-01-01T00:00:00+00:00"
        future = "2026-01-01T00:00:00+00:00"

        await storage.create_entity("Company", {"name": "X"}, "x")
        await storage.create_entity("Company", {"name": "Y"}, "y")
        await storage.create_entity("Company", {"name": "Z"}, "z")

        # Edge X->Y valid only until 2025
        await storage.create_edge("x", "y", "SUPPLIES_TO", {
            "weight": 0.9, "confidence": 1.0,
            "valid_from": "2023-01-01T00:00:00+00:00",
            "valid_until": "2025-01-01T00:00:00+00:00",
        })
        # Edge X->Z valid from 2025 onwards
        await storage.create_edge("x", "z", "SUPPLIES_TO", {
            "weight": 0.8, "confidence": 1.0,
            "valid_from": "2025-01-01T00:00:00+00:00",
        })

        engine = PropagationEngine(storage)

        # In 2024: only Y reachable
        results_past = await engine.propagate("x", 1.0, as_of=past)
        entities_past = {r["entity_id"] for r in results_past}
        assert "y" in entities_past
        assert "z" not in entities_past

        # In 2026: only Z reachable
        results_future = await engine.propagate("x", 1.0, as_of=future)
        entities_future = {r["entity_id"] for r in results_future}
        assert "z" in entities_future
        assert "y" not in entities_future

    @pytest.mark.asyncio
    async def test_causal_chain_at_time(self, storage):
        """CausalChainBuilder supports as_of for historical chains."""
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder

        await storage.create_entity("Company", {"name": "X"}, "x")
        await storage.create_entity("Company", {"name": "Y"}, "y")
        await storage.create_edge("x", "y", "SUPPLIES_TO", {
            "weight": 0.9, "confidence": 1.0,
            "valid_from": "2023-01-01T00:00:00+00:00",
            "valid_until": "2025-01-01T00:00:00+00:00",
        })

        from mkg.domain.services.propagation_engine import PropagationEngine

        engine = PropagationEngine(storage)
        results = await engine.propagate("x", 0.8, as_of="2024-06-01T00:00:00+00:00")

        builder = CausalChainBuilder(storage)
        chains = await builder.build_chains(
            trigger_entity_id="x",
            trigger_event="Test event",
            propagation_results=results,
        )
        assert chains is not None
        assert len(chains) >= 1


# ── C4: Multi-trigger Propagation ──


class TestMultiTriggerPropagation:
    """C4: Simultaneous propagation from multiple trigger entities."""

    @pytest.mark.asyncio
    async def test_propagate_multi_exists(self, storage):
        """PropagationEngine has propagate_multi() method."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        engine = PropagationEngine(storage)
        assert hasattr(engine, "propagate_multi")

    @pytest.mark.asyncio
    async def test_propagate_multi_basic(self, storage):
        """Multi-trigger returns merged results from all triggers."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        await _seed_graph(storage)
        engine = PropagationEngine(storage)

        triggers = [
            {"entity_id": "a", "impact_score": 0.8},
            {"entity_id": "b", "impact_score": 0.5},
        ]
        results = await engine.propagate_multi(triggers)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_propagate_multi_merges_impacts(self, storage):
        """When same entity is reached from multiple triggers, impacts combine."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        await _seed_graph(storage)
        engine = PropagationEngine(storage)

        # Both A and B can reach C (A->B->C, B->C directly)
        triggers = [
            {"entity_id": "a", "impact_score": 1.0},
            {"entity_id": "b", "impact_score": 1.0},
        ]
        results = await engine.propagate_multi(triggers)
        entity_ids = [r["entity_id"] for r in results]
        assert "c" in entity_ids

    @pytest.mark.asyncio
    async def test_propagate_multi_preserves_trigger_source(self, storage):
        """Each result tracks which trigger(s) it came from."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        await _seed_graph(storage)
        engine = PropagationEngine(storage)

        triggers = [
            {"entity_id": "a", "impact_score": 0.8},
        ]
        results = await engine.propagate_multi(triggers)
        for r in results:
            assert "trigger_sources" in r or "path" in r


# ── C5: Confidence Aggregation ──


class TestConfidenceAggregation:
    """C5: Aggregate confidence reporting across propagation results."""

    @pytest.mark.asyncio
    async def test_aggregate_confidence_exists(self, storage):
        """PropagationEngine has aggregate_confidence() method."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        engine = PropagationEngine(storage)
        assert hasattr(engine, "aggregate_confidence")

    @pytest.mark.asyncio
    async def test_aggregate_confidence_basic(self, storage):
        """aggregate_confidence returns overall confidence metrics."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        await _seed_graph(storage)
        engine = PropagationEngine(storage)
        results = await engine.propagate("a", 0.8)

        metrics = engine.aggregate_confidence(results)
        assert "mean_impact" in metrics
        assert "max_impact" in metrics
        assert "entity_count" in metrics
        assert "weighted_confidence" in metrics

    @pytest.mark.asyncio
    async def test_aggregate_confidence_empty(self, storage):
        """Aggregation on empty results returns zero metrics."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        engine = PropagationEngine(storage)
        metrics = engine.aggregate_confidence([])
        assert metrics["mean_impact"] == 0.0
        assert metrics["entity_count"] == 0

    @pytest.mark.asyncio
    async def test_aggregate_by_direction(self, storage):
        """Aggregation breaks down by direction (positive/negative)."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        await _seed_graph(storage)
        engine = PropagationEngine(storage)
        results = await engine.propagate("a", 0.8)

        metrics = engine.aggregate_confidence(results)
        assert "positive_count" in metrics
        assert "negative_count" in metrics
