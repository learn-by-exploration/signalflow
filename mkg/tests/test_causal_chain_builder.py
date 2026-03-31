# mkg/tests/test_causal_chain_builder.py
"""Tests for CausalChainBuilder — builds narrative causal chains from propagation results.

R-CC1 through R-CC5: Translates raw propagation paths into human-readable
causal chains with evidence links and impact summaries.
"""

import pytest


class TestCausalChainBuilder:

    @pytest.fixture
    async def builder(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        store = InMemoryGraphStorage()
        # Build supply chain graph
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Company", {"name": "AMD"}, entity_id="amd")
        await store.create_entity("Sector", {"name": "Semiconductors"}, entity_id="semi")
        await store.create_edge("tsmc", "nvidia", "SUPPLIES_TO",
                                {"weight": 0.9, "confidence": 0.9}, edge_id="e1")
        await store.create_edge("tsmc", "amd", "SUPPLIES_TO",
                                {"weight": 0.7, "confidence": 0.8}, edge_id="e2")
        await store.create_edge("nvidia", "semi", "OPERATES_IN",
                                {"weight": 0.6, "confidence": 0.7}, edge_id="e3")
        return CausalChainBuilder(store), store

    @pytest.mark.asyncio
    async def test_build_chains_from_propagation(self, builder):
        bld, _ = builder
        propagation_results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
            {"entity_id": "amd", "impact": 0.7, "depth": 1, "path": ["tsmc", "amd"]},
        ]
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC factory fire",
            propagation_results=propagation_results,
        )
        assert len(chains) == 2

    @pytest.mark.asyncio
    async def test_chain_has_required_fields(self, builder):
        bld, _ = builder
        propagation_results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC capacity cut",
            propagation_results=propagation_results,
        )
        chain = chains[0]
        assert "trigger" in chain
        assert "affected_entity" in chain
        assert "impact_score" in chain
        assert "hops" in chain
        assert "edge_labels" in chain

    @pytest.mark.asyncio
    async def test_chain_captures_edge_labels(self, builder):
        bld, _ = builder
        propagation_results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC supply issue",
            propagation_results=propagation_results,
        )
        assert "SUPPLIES_TO" in chains[0]["edge_labels"]

    @pytest.mark.asyncio
    async def test_multi_hop_chain(self, builder):
        bld, _ = builder
        propagation_results = [
            {"entity_id": "semi", "impact": 0.54, "depth": 2,
             "path": ["tsmc", "nvidia", "semi"]},
        ]
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC disruption",
            propagation_results=propagation_results,
        )
        chain = chains[0]
        assert chain["hops"] == 2
        assert len(chain["edge_labels"]) == 2

    @pytest.mark.asyncio
    async def test_empty_propagation_returns_empty_chains(self, builder):
        bld, _ = builder
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="Minor event",
            propagation_results=[],
        )
        assert chains == []

    @pytest.mark.asyncio
    async def test_build_narrative(self, builder):
        """A narrative string should describe the causal chain."""
        bld, _ = builder
        propagation_results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        chains = await bld.build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC fire",
            propagation_results=propagation_results,
        )
        assert "narrative" in chains[0]
        assert len(chains[0]["narrative"]) > 0
