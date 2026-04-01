# mkg/tests/test_sqlite_graph_storage.py
"""Tests for SQLiteGraphStorage — persistent graph storage via aiosqlite.

Iterations 6-10: Full GraphStorage interface compliance with SQLite backend.
Tests mirror InMemoryGraphStorage behavior but with persistence.
"""

import os
import tempfile

import pytest


@pytest.fixture
async def storage():
    """Create a SQLiteGraphStorage with a temporary database."""
    from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    store = SQLiteGraphStorage(db_path=db_path)
    await store.initialize()
    yield store
    await store.close()
    os.unlink(db_path)


class TestSQLiteEntityCRUD:
    """Entity create, read, update, delete."""

    @pytest.mark.asyncio
    async def test_create_entity(self, storage):
        entity = await storage.create_entity(
            "Company", {"name": "TSMC", "canonical_name": "tsmc"}
        )
        assert entity["id"]
        assert entity["entity_type"] == "Company"
        assert entity["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_create_entity_with_explicit_id(self, storage):
        entity = await storage.create_entity(
            "Company", {"name": "NVIDIA"}, entity_id="nvidia-001"
        )
        assert entity["id"] == "nvidia-001"

    @pytest.mark.asyncio
    async def test_get_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        found = await storage.get_entity(created["id"])
        assert found is not None
        assert found["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(self, storage):
        result = await storage.get_entity("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        updated = await storage.update_entity(created["id"], {"name": "TSMC Ltd"})
        assert updated["name"] == "TSMC Ltd"

    @pytest.mark.asyncio
    async def test_update_nonexistent_entity(self, storage):
        result = await storage.update_entity("nope", {"name": "X"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        assert await storage.delete_entity(created["id"]) is True
        assert await storage.get_entity(created["id"]) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self, storage):
        assert await storage.delete_entity("nope") is False

    @pytest.mark.asyncio
    async def test_delete_entity_cascades_edges(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5}
        )
        await storage.delete_entity(e1["id"])
        assert await storage.get_edge(edge["id"]) is None

    @pytest.mark.asyncio
    async def test_find_entities_by_type(self, storage):
        await storage.create_entity("Company", {"name": "TSMC"})
        await storage.create_entity("Company", {"name": "NVIDIA"})
        await storage.create_entity("Person", {"name": "Jensen Huang"})
        companies = await storage.find_entities(entity_type="Company")
        assert len(companies) == 2

    @pytest.mark.asyncio
    async def test_find_entities_with_filters(self, storage):
        await storage.create_entity("Company", {"name": "TSMC"})
        await storage.create_entity("Company", {"name": "NVIDIA"})
        results = await storage.find_entities(filters={"name": "TSMC"})
        assert len(results) == 1
        assert results[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_find_entities_with_limit_offset(self, storage):
        for i in range(10):
            await storage.create_entity("Company", {"name": f"Corp-{i}"})
        page1 = await storage.find_entities(limit=3, offset=0)
        page2 = await storage.find_entities(limit=3, offset=3)
        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0]["name"] != page2[0]["name"]


class TestSQLiteEdgeCRUD:
    """Edge create, read, update, delete."""

    @pytest.mark.asyncio
    async def test_create_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        edge = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
        )
        assert edge["id"]
        assert edge["source_id"] == e1["id"]
        assert edge["target_id"] == e2["id"]
        assert edge["relation_type"] == "SUPPLIES_TO"

    @pytest.mark.asyncio
    async def test_create_edge_validates_source(self, storage):
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        with pytest.raises(ValueError, match="source"):
            await storage.create_edge("nonexistent", e2["id"], "SUPPLIES_TO", {})

    @pytest.mark.asyncio
    async def test_create_edge_validates_target(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        with pytest.raises(ValueError, match="target"):
            await storage.create_edge(e1["id"], "nonexistent", "SUPPLIES_TO", {})

    @pytest.mark.asyncio
    async def test_get_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        created = await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5})
        found = await storage.get_edge(created["id"])
        assert found is not None
        assert found["relation_type"] == "SUPPLIES_TO"

    @pytest.mark.asyncio
    async def test_update_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5})
        updated = await storage.update_edge(edge["id"], {"weight": 0.9})
        assert updated["weight"] == 0.9

    @pytest.mark.asyncio
    async def test_delete_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {})
        assert await storage.delete_edge(edge["id"]) is True
        assert await storage.get_edge(edge["id"]) is None

    @pytest.mark.asyncio
    async def test_find_edges_by_source(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        e3 = await storage.create_entity("Company", {"name": "C"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5})
        await storage.create_edge(e1["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.6})
        edges = await storage.find_edges(source_id=e1["id"])
        assert len(edges) == 2

    @pytest.mark.asyncio
    async def test_find_edges_by_relation_type(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {})
        await storage.create_edge(e1["id"], e2["id"], "COMPETES_WITH", {})
        edges = await storage.find_edges(relation_type="SUPPLIES_TO")
        assert len(edges) == 1


class TestSQLiteTraversal:
    """Graph traversal: neighbors, subgraph, BFS traverse."""

    @pytest.mark.asyncio
    async def test_get_neighbors_outgoing(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e3 = await storage.create_entity("Company", {"name": "Apple"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.8})
        await storage.create_edge(e1["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.7})
        neighbors = await storage.get_neighbors(e1["id"], direction="outgoing")
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_incoming(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.8})
        neighbors = await storage.get_neighbors(e2["id"], direction="incoming")
        assert len(neighbors) == 1
        assert neighbors[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_get_neighbors_both(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        e3 = await storage.create_entity("Company", {"name": "C"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5})
        await storage.create_edge(e3["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5})
        neighbors = await storage.get_neighbors(e2["id"], direction="both")
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_subgraph(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e3 = await storage.create_entity("Company", {"name": "Apple"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.8})
        await storage.create_edge(e2["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.7})
        subgraph = await storage.get_subgraph(e1["id"], max_depth=2)
        assert len(subgraph["nodes"]) == 3
        assert len(subgraph["edges"]) >= 2

    @pytest.mark.asyncio
    async def test_traverse_bfs(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e3 = await storage.create_entity("Company", {"name": "Apple"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.9})
        await storage.create_edge(e2["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.8})
        results = await storage.traverse(e1["id"], max_depth=3)
        assert len(results) == 2
        # First result should be NVIDIA (depth 1, higher cumulative weight)
        assert results[0]["depth"] == 1

    @pytest.mark.asyncio
    async def test_traverse_respects_min_weight(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        e3 = await storage.create_entity("Company", {"name": "C"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.9})
        await storage.create_edge(e1["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.1})
        results = await storage.traverse(e1["id"], min_weight=0.5)
        assert len(results) == 1
        assert results[0]["entity"]["name"] == "B"


class TestSQLiteSearch:
    """Keyword search."""

    @pytest.mark.asyncio
    async def test_search_by_name(self, storage):
        await storage.create_entity("Company", {"name": "TSMC Semiconductor"})
        await storage.create_entity("Company", {"name": "NVIDIA Graphics"})
        results = await storage.search("TSMC")
        assert len(results) >= 1
        assert any("TSMC" in r["name"] for r in results)

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, storage):
        await storage.create_entity("Company", {"name": "NVIDIA"})
        results = await storage.search("nvidia")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_with_type_filter(self, storage):
        await storage.create_entity("Company", {"name": "TSMC"})
        await storage.create_entity("Person", {"name": "TSMC CEO"})
        results = await storage.search("TSMC", entity_type="Company")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, storage):
        for i in range(20):
            await storage.create_entity("Company", {"name": f"Corp-{i}"})
        results = await storage.search("Corp", limit=5)
        assert len(results) == 5


class TestSQLiteMerge:
    """Entity merge/upsert."""

    @pytest.mark.asyncio
    async def test_merge_creates_new(self, storage):
        result = await storage.merge_entity(
            "Company", {"canonical_name": "tsmc"}, {"name": "TSMC"}
        )
        assert result["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_merge_updates_existing(self, storage):
        await storage.create_entity(
            "Company", {"name": "TSMC", "canonical_name": "tsmc"}
        )
        result = await storage.merge_entity(
            "Company", {"canonical_name": "tsmc"}, {"name": "TSMC Ltd", "revenue": "50B"}
        )
        assert result["name"] == "TSMC Ltd"


class TestSQLitePersistence:
    """Verify data survives close + reopen."""

    @pytest.mark.asyncio
    async def test_data_persists_across_sessions(self):
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Session 1: create data
            store1 = SQLiteGraphStorage(db_path=db_path)
            await store1.initialize()
            entity = await store1.create_entity("Company", {"name": "TSMC"})
            entity_id = entity["id"]
            await store1.close()

            # Session 2: verify data persists
            store2 = SQLiteGraphStorage(db_path=db_path)
            await store2.initialize()
            found = await store2.get_entity(entity_id)
            assert found is not None
            assert found["name"] == "TSMC"
            await store2.close()
        finally:
            os.unlink(db_path)


class TestSQLiteHealthAndBackup:
    """Health check and backup."""

    @pytest.mark.asyncio
    async def test_health_check(self, storage):
        health = await storage.health_check()
        assert health["status"] == "healthy"
        assert health["backend"] == "sqlite"

    @pytest.mark.asyncio
    async def test_backup(self, storage):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backup_path = f.name
        try:
            await storage.create_entity("Company", {"name": "TSMC"})
            result = await storage.backup(backup_path)
            assert result is True
            assert os.path.getsize(backup_path) > 0
        finally:
            os.unlink(backup_path)
