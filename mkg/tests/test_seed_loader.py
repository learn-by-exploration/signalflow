# mkg/tests/test_seed_loader.py
"""Tests for SeedDataLoader — loads initial graph data from YAML/dict.

Populates the knowledge graph with foundational entities and relationships
for the semiconductor supply chain, Indian markets, etc.
"""

import pytest

from mkg.domain.entities.node import EntityType


class TestSeedDataLoaderBasics:
    """Test basic seed loading operations."""

    @pytest.fixture
    def loader(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.seed_loader import SeedDataLoader
        store = InMemoryGraphStorage()
        return SeedDataLoader(store), store

    @pytest.mark.asyncio
    async def test_load_entities_from_list(self, loader):
        seed_loader, store = loader
        entities_data = [
            {"entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
            {"entity_type": "Company", "name": "NVIDIA", "canonical_name": "NVIDIA"},
        ]
        count = await seed_loader.load_entities(entities_data)
        assert count == 2

    @pytest.mark.asyncio
    async def test_loaded_entities_are_in_store(self, loader):
        seed_loader, store = loader
        entities_data = [
            {"entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
        ]
        await seed_loader.load_entities(entities_data)
        results = await store.find_entities(entity_type="Company")
        assert len(results) == 1
        assert results[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_load_edges_from_list(self, loader):
        seed_loader, store = loader
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia")
        edges_data = [
            {"source_id": "tsmc", "target_id": "nvidia", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9},
        ]
        count = await seed_loader.load_edges(edges_data)
        assert count == 1

    @pytest.mark.asyncio
    async def test_load_full_seed_data(self, loader):
        seed_loader, store = loader
        seed_data = {
            "entities": [
                {"id": "tsmc", "entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
                {"id": "nvidia", "entity_type": "Company", "name": "NVIDIA", "canonical_name": "NVIDIA"},
                {"id": "taiwan", "entity_type": "Country", "name": "Taiwan", "canonical_name": "TAIWAN"},
            ],
            "edges": [
                {"source_id": "tsmc", "target_id": "nvidia", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9},
                {"source_id": "tsmc", "target_id": "taiwan", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            ],
        }
        result = await seed_loader.load(seed_data)
        assert result["entities_loaded"] == 3
        assert result["edges_loaded"] == 2

    @pytest.mark.asyncio
    async def test_load_skips_invalid_entities(self, loader):
        seed_loader, store = loader
        entities_data = [
            {"entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
            {"entity_type": "Company", "name": "", "canonical_name": ""},  # invalid — empty name
        ]
        count = await seed_loader.load_entities(entities_data)
        assert count == 1  # only valid entity loaded

    @pytest.mark.asyncio
    async def test_load_is_idempotent(self, loader):
        seed_loader, store = loader
        seed_data = {
            "entities": [
                {"id": "tsmc", "entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
            ],
            "edges": [],
        }
        await seed_loader.load(seed_data)
        await seed_loader.load(seed_data)  # second load
        # Should still have just 1 entity (idempotent via merge)
        entities = await store.find_entities()
        assert len(entities) == 1


class TestDefaultSeedData:
    """Test that default semiconductor supply chain seed data exists."""

    def test_get_default_seed_data_returns_dict(self):
        from mkg.domain.services.seed_loader import get_default_seed_data
        data = get_default_seed_data()
        assert "entities" in data
        assert "edges" in data

    def test_default_seed_has_companies(self):
        from mkg.domain.services.seed_loader import get_default_seed_data
        data = get_default_seed_data()
        company_names = [e["name"] for e in data["entities"] if e["entity_type"] == "Company"]
        assert "TSMC" in company_names
        assert "NVIDIA" in company_names

    def test_default_seed_has_supply_chain_edges(self):
        from mkg.domain.services.seed_loader import get_default_seed_data
        data = get_default_seed_data()
        relation_types = [e["relation_type"] for e in data["edges"]]
        assert "SUPPLIES_TO" in relation_types

    @pytest.mark.asyncio
    async def test_load_defaults_populates_graph(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.seed_loader import SeedDataLoader, get_default_seed_data
        store = InMemoryGraphStorage()
        loader = SeedDataLoader(store)
        result = await loader.load(get_default_seed_data())
        assert result["entities_loaded"] >= 5
        assert result["edges_loaded"] >= 3
