# mkg/tests/test_graph_mutation.py
"""Tests for GraphMutationService — applies extraction results to the graph."""

import pytest
from mkg.domain.entities.node import EntityType


class TestGraphMutationService:

    @pytest.fixture
    async def service(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.graph_mutation import GraphMutationService
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        store = InMemoryGraphStorage()
        registry = CanonicalEntityRegistry(load_defaults=True)
        return GraphMutationService(store, registry), store

    @pytest.mark.asyncio
    async def test_apply_entities(self, service):
        svc, store = service
        entities = [
            {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
            {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.90},
        ]
        result = await svc.apply_entities(entities, source="article-001")
        assert result["created"] + result["updated"] == 2

    @pytest.mark.asyncio
    async def test_apply_relations(self, service):
        svc, store = service
        # First create entities
        await store.create_entity("Company", {"name": "TSMC", "canonical_name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA", "canonical_name": "NVIDIA"}, entity_id="nvidia")
        relations = [
            {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9},
        ]
        result = await svc.apply_relations(relations, source="article-001")
        assert result["created"] == 1

    @pytest.mark.asyncio
    async def test_apply_extraction_result(self, service):
        svc, store = service
        extraction = {
            "entities": [
                {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
                {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.90},
            ],
            "relations": [
                {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9},
            ],
        }
        result = await svc.apply(extraction, source="article-001")
        assert "entities" in result
        assert "relations" in result

    @pytest.mark.asyncio
    async def test_deduplicates_entities_on_apply(self, service):
        svc, store = service
        entities = [
            {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
        ]
        await svc.apply_entities(entities, source="art-001")
        await svc.apply_entities(entities, source="art-002")
        all_entities = await store.find_entities(entity_type="Company")
        tsmc_count = sum(1 for e in all_entities if e.get("canonical_name") == "TSMC")
        assert tsmc_count == 1

    @pytest.mark.asyncio
    async def test_skips_invalid_entities(self, service):
        svc, store = service
        entities = [
            {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
            {"name": "", "entity_type": "Company", "confidence": 0.5},  # invalid
        ]
        result = await svc.apply_entities(entities, source="art-001")
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_skips_invalid_entity_type(self, service):
        svc, store = service
        entities = [
            {"name": "X", "entity_type": "InvalidType", "confidence": 0.5},
        ]
        result = await svc.apply_entities(entities, source="art-001")
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_skips_invalid_relation_type(self, service):
        svc, store = service
        await store.create_entity("Company", {"name": "A", "canonical_name": "A"}, entity_id="a")
        await store.create_entity("Company", {"name": "B", "canonical_name": "B"}, entity_id="b")
        relations = [
            {"source": "A", "target": "B", "relation_type": "INVALID_REL"},
        ]
        result = await svc.apply_relations(relations, source="art-001")
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_apply_empty_extraction(self, service):
        svc, _ = service
        result = await svc.apply({}, source="art-001")
        assert result["entities"]["created"] == 0
        assert result["relations"]["created"] == 0
