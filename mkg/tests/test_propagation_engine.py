# mkg/tests/test_propagation_engine.py
"""Tests for PropagationEngine — impact propagation through the graph.

R-PE1 through R-PE5: BFS traversal with weight decay, depth limiting,
impact scoring, and affected entity collection.
"""

import pytest


class TestPropagationEngine:

    @pytest.fixture
    async def engine(self):
        """Build a test graph: TSMC -> NVIDIA -> AMD (supply chain)."""
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.propagation_engine import PropagationEngine
        store = InMemoryGraphStorage()
        # Create entities
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Company", {"name": "AMD"}, entity_id="amd")
        await store.create_entity("Company", {"name": "Apple"}, entity_id="apple")
        # Chain: TSMC -> NVIDIA -> AMD
        await store.create_edge("tsmc", "nvidia", "SUPPLIES_TO",
                                {"weight": 0.9, "confidence": 0.9}, edge_id="e1")
        await store.create_edge("nvidia", "amd", "COMPETES_WITH",
                                {"weight": 0.7, "confidence": 0.8}, edge_id="e2")
        # TSMC -> Apple (separate branch)
        await store.create_edge("tsmc", "apple", "SUPPLIES_TO",
                                {"weight": 0.8, "confidence": 0.85}, edge_id="e3")
        return PropagationEngine(store), store

    @pytest.mark.asyncio
    async def test_propagate_from_trigger(self, engine):
        eng, _ = engine
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        assert len(results) > 0
        # NVIDIA should be affected
        ids = [r["entity_id"] for r in results]
        assert "nvidia" in ids

    @pytest.mark.asyncio
    async def test_impact_decays_with_depth(self, engine):
        eng, _ = engine
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        nvidia_hit = next(r for r in results if r["entity_id"] == "nvidia")
        amd_hit = next((r for r in results if r["entity_id"] == "amd"), None)
        if amd_hit:
            assert amd_hit["impact"] < nvidia_hit["impact"]

    @pytest.mark.asyncio
    async def test_max_depth_limits_propagation(self, engine):
        eng, _ = engine
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0, max_depth=1)
        ids = [r["entity_id"] for r in results]
        assert "nvidia" in ids
        assert "amd" not in ids  # depth 2, should be excluded

    @pytest.mark.asyncio
    async def test_min_impact_threshold(self, engine):
        eng, _ = engine
        results = await eng.propagate(
            trigger_entity_id="tsmc", impact_score=0.01, min_impact=0.5
        )
        # Very small initial impact, nothing should exceed threshold
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_propagate_returns_sorted_by_impact(self, engine):
        eng, _ = engine
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        impacts = [r["impact"] for r in results]
        assert impacts == sorted(impacts, reverse=True)

    @pytest.mark.asyncio
    async def test_propagate_includes_path(self, engine):
        eng, _ = engine
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        nvidia_hit = next(r for r in results if r["entity_id"] == "nvidia")
        assert "path" in nvidia_hit
        assert nvidia_hit["depth"] == 1

    @pytest.mark.asyncio
    async def test_propagate_no_revisits(self, engine):
        eng, store = engine
        # Add cycle: AMD -> TSMC
        await store.create_edge("amd", "tsmc", "DEPENDS_ON",
                                {"weight": 0.5, "confidence": 0.7}, edge_id="e4")
        results = await eng.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        ids = [r["entity_id"] for r in results]
        # No duplicates
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_propagate_empty_for_isolated_entity(self, engine):
        eng, store = engine
        await store.create_entity("Company", {"name": "Isolated"}, entity_id="iso")
        results = await eng.propagate(trigger_entity_id="iso", impact_score=1.0)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_propagate_handles_storage_failure(self, engine):
        """If storage raises an exception, propagation should degrade gracefully."""
        from unittest.mock import AsyncMock, patch
        eng, store = engine

        original_find = store.find_edges
        call_count = 0

        async def failing_find(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:  # Fail on subsequent calls
                raise RuntimeError("Storage unavailable")
            return await original_find(*args, **kwargs)

        store.find_edges = failing_find
        eng_broken = type(eng)(store)
        # Should not raise, just return partial results
        results = await eng_broken.propagate(trigger_entity_id="tsmc", impact_score=1.0)
        # Should still work for the first call
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_propagate_with_relation_type_filter(self, engine):
        eng, _ = engine
        results = await eng.propagate(
            trigger_entity_id="tsmc", impact_score=1.0,
            relation_types=["SUPPLIES_TO"],
        )
        ids = [r["entity_id"] for r in results]
        assert "nvidia" in ids
        assert "apple" in ids
        # AMD is connected via COMPETES_WITH, should be excluded
        assert "amd" not in ids

    @pytest.mark.asyncio
    async def test_deep_propagation_chain(self, engine):
        """Test propagation through a chain of 10+ entities."""
        _, store = engine
        # Build chain: e0 -> e1 -> e2 -> ... -> e9
        prev = "chain0"
        await store.create_entity("Company", {"name": f"Chain-0"}, entity_id=prev)
        for i in range(1, 10):
            eid = f"chain{i}"
            await store.create_entity("Company", {"name": f"Chain-{i}"}, entity_id=eid)
            await store.create_edge(prev, eid, "DEPENDS_ON",
                                    {"weight": 0.9, "confidence": 0.9})
            prev = eid
        from mkg.domain.services.propagation_engine import PropagationEngine
        eng2 = PropagationEngine(store)
        results = await eng2.propagate("chain0", impact_score=1.0, max_depth=10)
        ids = [r["entity_id"] for r in results]
        assert "chain1" in ids
        assert "chain4" in ids
        # Impact should decay along the chain
        impacts = {r["entity_id"]: r["impact"] for r in results}
        assert impacts.get("chain1", 0) > impacts.get("chain4", 0)

    @pytest.mark.asyncio
    async def test_propagation_fan_out(self, engine):
        """Test entity with many outgoing edges."""
        _, store = engine
        hub_id = "hub"
        await store.create_entity("Company", {"name": "Hub"}, entity_id=hub_id)
        for i in range(20):
            eid = f"spoke-{i}"
            await store.create_entity("Company", {"name": f"Spoke-{i}"}, entity_id=eid)
            await store.create_edge(hub_id, eid, "SUPPLIES_TO",
                                    {"weight": 0.5, "confidence": 0.8})
        from mkg.domain.services.propagation_engine import PropagationEngine
        eng2 = PropagationEngine(store)
        results = await eng2.propagate(hub_id, impact_score=1.0)
        assert len(results) == 20
