# mkg/tests/test_neo4j_graph_storage.py
"""Tests for Neo4jGraphStorage dummy connector.

Verifies it implements the full GraphStorage interface using
the in-memory delegate, and that connection lifecycle works.
"""

import pytest

from mkg.infrastructure.neo4j.graph_storage import Neo4jGraphStorage


class TestNeo4jGraphStorageLifecycle:
    """Connection lifecycle tests."""

    @pytest.fixture
    def storage(self):
        return Neo4jGraphStorage(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="test",
            database="test_mkg",
        )

    async def test_initial_state_not_connected(self, storage):
        assert storage.is_connected is False

    async def test_connect(self, storage):
        await storage.connect()
        assert storage.is_connected is True

    async def test_close(self, storage):
        await storage.connect()
        await storage.close()
        assert storage.is_connected is False


class TestNeo4jGraphStorageEntityCRUD:
    """Entity operations via dummy connector."""

    @pytest.fixture
    async def storage(self):
        s = Neo4jGraphStorage()
        await s.connect()
        return s

    async def test_create_entity(self, storage):
        entity = await storage.create_entity(
            "Company", {"name": "TSMC", "canonical_name": "TSMC"}, entity_id="tsmc-001"
        )
        assert entity["id"] == "tsmc-001"
        assert entity["name"] == "TSMC"
        assert entity["entity_type"] == "Company"

    async def test_get_entity(self, storage):
        await storage.create_entity(
            "Company", {"name": "NVIDIA"}, entity_id="nvda-001"
        )
        result = await storage.get_entity("nvda-001")
        assert result is not None
        assert result["name"] == "NVIDIA"

    async def test_get_entity_not_found(self, storage):
        result = await storage.get_entity("nonexistent")
        assert result is None

    async def test_update_entity(self, storage):
        await storage.create_entity(
            "Company", {"name": "AMD"}, entity_id="amd-001"
        )
        updated = await storage.update_entity("amd-001", {"sector": "Semiconductors"})
        assert updated is not None
        assert updated["sector"] == "Semiconductors"

    async def test_delete_entity(self, storage):
        await storage.create_entity(
            "Company", {"name": "Intel"}, entity_id="intc-001"
        )
        assert await storage.delete_entity("intc-001") is True
        assert await storage.get_entity("intc-001") is None

    async def test_find_entities(self, storage):
        await storage.create_entity("Company", {"name": "A"}, entity_id="a")
        await storage.create_entity("Product", {"name": "B"}, entity_id="b")
        companies = await storage.find_entities(entity_type="Company")
        assert len(companies) == 1
        assert companies[0]["name"] == "A"


class TestNeo4jGraphStorageEdgeCRUD:
    """Edge operations via dummy connector."""

    @pytest.fixture
    async def storage(self):
        s = Neo4jGraphStorage()
        await s.connect()
        await s.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await s.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvda")
        return s

    async def test_create_edge(self, storage):
        edge = await storage.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="e1",
        )
        assert edge["id"] == "e1"
        assert edge["source_id"] == "tsmc"
        assert edge["relation_type"] == "SUPPLIES_TO"

    async def test_create_edge_missing_source(self, storage):
        with pytest.raises(ValueError, match="source entity"):
            await storage.create_edge(
                "nonexistent", "nvda", "SUPPLIES_TO",
                {"weight": 0.5, "confidence": 0.5},
            )

    async def test_get_edge(self, storage):
        await storage.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="e1",
        )
        result = await storage.get_edge("e1")
        assert result is not None
        assert result["weight"] == 0.85

    async def test_update_edge(self, storage):
        await storage.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="e1",
        )
        updated = await storage.update_edge("e1", {"weight": 0.95})
        assert updated is not None
        assert updated["weight"] == 0.95

    async def test_delete_edge(self, storage):
        await storage.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO",
            {"weight": 0.5, "confidence": 0.5},
            edge_id="e1",
        )
        assert await storage.delete_edge("e1") is True
        assert await storage.get_edge("e1") is None

    async def test_find_edges(self, storage):
        await storage.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO",
            {"weight": 0.8, "confidence": 0.9},
        )
        edges = await storage.find_edges(source_id="tsmc")
        assert len(edges) == 1
        assert edges[0]["relation_type"] == "SUPPLIES_TO"


class TestNeo4jGraphStorageTraversal:
    """Traversal and search via dummy connector."""

    @pytest.fixture
    async def storage(self):
        s = Neo4jGraphStorage()
        await s.connect()
        await s.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await s.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvda")
        await s.create_entity("Company", {"name": "AWS"}, entity_id="aws")
        await s.create_edge(
            "tsmc", "nvda", "SUPPLIES_TO", {"weight": 0.9, "confidence": 0.95}
        )
        await s.create_edge(
            "nvda", "aws", "SUPPLIES_TO", {"weight": 0.7, "confidence": 0.8}
        )
        return s

    async def test_get_neighbors(self, storage):
        neighbors = await storage.get_neighbors("tsmc", direction="outgoing")
        assert len(neighbors) == 1
        assert neighbors[0]["name"] == "NVIDIA"

    async def test_get_subgraph(self, storage):
        subgraph = await storage.get_subgraph("tsmc", max_depth=2)
        assert len(subgraph["nodes"]) == 3
        assert len(subgraph["edges"]) >= 2

    async def test_traverse(self, storage):
        results = await storage.traverse("tsmc", max_depth=3)
        assert len(results) >= 2
        entity_names = [r["entity"]["name"] for r in results]
        assert "NVIDIA" in entity_names
        assert "AWS" in entity_names

    async def test_search(self, storage):
        results = await storage.search("TSMC")
        assert len(results) >= 1
        assert results[0]["name"] == "TSMC"

    async def test_merge_entity(self, storage):
        merged = await storage.merge_entity(
            "Company",
            {"canonical_name": "TSMC"},
            {"name": "TSMC", "canonical_name": "TSMC", "sector": "Semis"},
        )
        assert merged["name"] == "TSMC"

    async def test_backup(self, storage):
        assert await storage.backup("/tmp/test_backup") is True

    async def test_health_check(self, storage):
        health = await storage.health_check()
        assert health["status"] == "healthy"
        assert health["backend"] == "neo4j_dummy"
        assert health["connected"] is True
        assert health["entity_count"] >= 3
