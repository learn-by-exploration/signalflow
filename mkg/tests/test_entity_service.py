# mkg/tests/test_entity_service.py
"""Tests for EntityService — domain service for entity/edge CRUD.

Wraps GraphStorage with domain model validation and business logic.
Uses InMemoryGraphStorage as the test double.
"""

import pytest

from mkg.domain.entities.edge import RelationType
from mkg.domain.entities.node import EntityType


class TestEntityServiceCreate:
    """Test entity creation through the service layer."""

    @pytest.fixture
    def service(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        return EntityService(store)

    @pytest.mark.asyncio
    async def test_create_entity_returns_entity_model(self, service):
        entity = await service.create_entity(
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        from mkg.domain.entities.node import Entity
        assert isinstance(entity, Entity)
        assert entity.name == "TSMC"
        assert entity.entity_type == EntityType.COMPANY

    @pytest.mark.asyncio
    async def test_create_entity_with_metadata(self, service):
        entity = await service.create_entity(
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            metadata={"ticker": "TSM", "sector": "Semiconductors"},
        )
        assert entity.metadata["ticker"] == "TSM"

    @pytest.mark.asyncio
    async def test_create_entity_with_explicit_id(self, service):
        entity = await service.create_entity(
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            entity_id="tsmc-001",
        )
        assert entity.id == "tsmc-001"

    @pytest.mark.asyncio
    async def test_create_entity_generates_id(self, service):
        entity = await service.create_entity(
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.id is not None
        assert len(entity.id) > 0

    @pytest.mark.asyncio
    async def test_create_entity_rejects_empty_name(self, service):
        with pytest.raises(ValueError, match="name"):
            await service.create_entity(
                entity_type=EntityType.COMPANY,
                name="",
                canonical_name="TSMC",
            )


class TestEntityServiceGet:
    """Test entity retrieval."""

    @pytest.fixture
    async def service_with_data(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        await svc.create_entity(EntityType.COMPANY, "TSMC", "TSMC", entity_id="tsmc-001")
        await svc.create_entity(EntityType.PERSON, "Jensen Huang", "JENSEN_HUANG", entity_id="jensen-001")
        return svc

    @pytest.mark.asyncio
    async def test_get_entity_by_id(self, service_with_data):
        svc = service_with_data
        entity = await svc.get_entity("tsmc-001")
        assert entity is not None
        assert entity.name == "TSMC"

    @pytest.mark.asyncio
    async def test_get_entity_returns_none_for_missing(self, service_with_data):
        svc = service_with_data
        entity = await svc.get_entity("nonexistent")
        assert entity is None

    @pytest.mark.asyncio
    async def test_find_entities_all(self, service_with_data):
        svc = service_with_data
        entities = await svc.find_entities()
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_find_entities_by_type(self, service_with_data):
        svc = service_with_data
        entities = await svc.find_entities(entity_type=EntityType.COMPANY)
        assert len(entities) == 1
        assert entities[0].entity_type == EntityType.COMPANY


class TestEntityServiceUpdate:
    """Test entity update operations."""

    @pytest.fixture
    async def service_with_entity(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        await svc.create_entity(
            EntityType.COMPANY, "TSMC", "TSMC",
            entity_id="tsmc-001",
            metadata={"sector": "Semiconductors"},
        )
        return svc

    @pytest.mark.asyncio
    async def test_update_entity_metadata(self, service_with_entity):
        svc = service_with_entity
        updated = await svc.update_entity("tsmc-001", metadata={"sector": "Chips", "country": "Taiwan"})
        assert updated is not None
        assert updated.metadata["country"] == "Taiwan"

    @pytest.mark.asyncio
    async def test_update_entity_name(self, service_with_entity):
        svc = service_with_entity
        updated = await svc.update_entity("tsmc-001", name="TSMC Ltd")
        assert updated.name == "TSMC Ltd"

    @pytest.mark.asyncio
    async def test_update_entity_returns_none_for_missing(self, service_with_entity):
        svc = service_with_entity
        result = await svc.update_entity("nonexistent", name="X")
        assert result is None


class TestEntityServiceDelete:
    """Test entity deletion."""

    @pytest.fixture
    async def service_with_entity(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        await svc.create_entity(EntityType.COMPANY, "TSMC", "TSMC", entity_id="tsmc-001")
        return svc

    @pytest.mark.asyncio
    async def test_delete_entity(self, service_with_entity):
        svc = service_with_entity
        result = await svc.delete_entity("tsmc-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_entity_returns_false_for_missing(self, service_with_entity):
        svc = service_with_entity
        result = await svc.delete_entity("nonexistent")
        assert result is False


class TestEdgeServiceCreate:
    """Test edge creation through the service layer."""

    @pytest.fixture
    async def service_with_entities(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        await svc.create_entity(EntityType.COMPANY, "TSMC", "TSMC", entity_id="tsmc-001")
        await svc.create_entity(EntityType.COMPANY, "NVIDIA", "NVIDIA", entity_id="nvidia-001")
        return svc

    @pytest.mark.asyncio
    async def test_create_edge_returns_edge_model(self, service_with_entities):
        svc = service_with_entities
        from mkg.domain.entities.edge import Edge
        edge = await svc.create_edge(
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        assert isinstance(edge, Edge)
        assert edge.source_id == "tsmc-001"
        assert edge.relation_type == RelationType.SUPPLIES_TO

    @pytest.mark.asyncio
    async def test_create_edge_validates_source_exists(self, service_with_entities):
        svc = service_with_entities
        with pytest.raises(ValueError):
            await svc.create_edge(
                source_id="nonexistent",
                target_id="nvidia-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=0.85,
                confidence=0.92,
            )

    @pytest.mark.asyncio
    async def test_create_edge_rejects_self_loop(self, service_with_entities):
        svc = service_with_entities
        with pytest.raises(ValueError, match="same"):
            await svc.create_edge(
                source_id="tsmc-001",
                target_id="tsmc-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=0.85,
                confidence=0.92,
            )

    @pytest.mark.asyncio
    async def test_create_edge_with_metadata(self, service_with_entities):
        svc = service_with_entities
        edge = await svc.create_edge(
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
            metadata={"product": "A100 chips"},
        )
        assert edge.metadata["product"] == "A100 chips"


class TestEdgeServiceGetAndFind:
    """Test edge retrieval operations."""

    @pytest.fixture
    async def service_with_edges(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        await svc.create_entity(EntityType.COMPANY, "TSMC", "TSMC", entity_id="tsmc-001")
        await svc.create_entity(EntityType.COMPANY, "NVIDIA", "NVIDIA", entity_id="nvidia-001")
        await svc.create_entity(EntityType.COMPANY, "Apple", "APPLE", entity_id="apple-001")
        await svc.create_edge("tsmc-001", "nvidia-001", RelationType.SUPPLIES_TO, 0.85, 0.92, edge_id="e1")
        await svc.create_edge("tsmc-001", "apple-001", RelationType.SUPPLIES_TO, 0.75, 0.85, edge_id="e2")
        return svc

    @pytest.mark.asyncio
    async def test_get_edge_by_id(self, service_with_edges):
        svc = service_with_edges
        edge = await svc.get_edge("e1")
        assert edge is not None
        assert edge.source_id == "tsmc-001"

    @pytest.mark.asyncio
    async def test_get_edge_returns_none_for_missing(self, service_with_edges):
        svc = service_with_edges
        edge = await svc.get_edge("nonexistent")
        assert edge is None

    @pytest.mark.asyncio
    async def test_find_edges_by_source(self, service_with_edges):
        svc = service_with_edges
        edges = await svc.find_edges(source_id="tsmc-001")
        assert len(edges) == 2

    @pytest.mark.asyncio
    async def test_find_edges_by_relation_type(self, service_with_edges):
        svc = service_with_edges
        edges = await svc.find_edges(relation_type=RelationType.SUPPLIES_TO)
        assert len(edges) == 2


class TestServiceDependencyInjection:
    """Verify service follows dependency inversion."""

    def test_service_accepts_any_graph_storage(self):
        from mkg.domain.services.entity_service import EntityService
        from mkg.domain.interfaces.graph_storage import GraphStorage

        # Service constructor should accept GraphStorage, not a specific impl
        import inspect
        sig = inspect.signature(EntityService.__init__)
        params = list(sig.parameters.keys())
        assert "storage" in params or "graph_storage" in params
