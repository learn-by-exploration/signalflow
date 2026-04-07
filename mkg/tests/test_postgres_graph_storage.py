# mkg/tests/test_postgres_graph_storage.py
"""Tests for PostgresGraphStorage — production graph storage via asyncpg.

Requires a live PostgreSQL database. Tests are skipped when no database is
available. Set MKG_TEST_DATABASE_URL to enable.

The test suite mirrors test_sqlite_graph_storage.py for interface parity,
plus additional tag-specific and recursive CTE tests.
"""

import json
import os
import tempfile

import pytest

# Skip entire module if asyncpg not installed or no DB URL
asyncpg = pytest.importorskip("asyncpg")

MKG_TEST_DB_URL = os.environ.get(
    "MKG_TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", ""),
)

pytestmark = pytest.mark.skipif(
    not MKG_TEST_DB_URL,
    reason="MKG_TEST_DATABASE_URL / DATABASE_URL not set",
)


@pytest.fixture
async def storage():
    """Create a PostgresGraphStorage, initialize schema, yield, then clean up."""
    from mkg.infrastructure.postgres.graph_storage import PostgresGraphStorage

    store = PostgresGraphStorage(database_url=MKG_TEST_DB_URL, min_pool=1, max_pool=3)
    await store.initialize()

    # Clean tables before each test
    pool = store._pool
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM mkg_edges")
        await conn.execute("DELETE FROM mkg_entities")

    yield store
    await store.close()


# ── Entity CRUD ──


class TestPostgresEntityCRUD:
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
    async def test_get_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        found = await storage.get_entity(created["id"])
        assert found is not None
        assert found["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(self, storage):
        import uuid
        result = await storage.get_entity(str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        updated = await storage.update_entity(created["id"], {"name": "TSMC Ltd"})
        assert updated["name"] == "TSMC Ltd"

    @pytest.mark.asyncio
    async def test_update_nonexistent_entity(self, storage):
        import uuid
        result = await storage.update_entity(str(uuid.uuid4()), {"name": "X"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity(self, storage):
        created = await storage.create_entity("Company", {"name": "TSMC"})
        assert await storage.delete_entity(created["id"]) is True
        assert await storage.get_entity(created["id"]) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self, storage):
        import uuid
        assert await storage.delete_entity(str(uuid.uuid4())) is False

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
        names1 = {e["name"] for e in page1}
        names2 = {e["name"] for e in page2}
        assert names1.isdisjoint(names2)


# ── Tags (new for Postgres) ──


class TestPostgresEntityTags:
    """Tags on entities — stored as TEXT[] with GIN index."""

    @pytest.mark.asyncio
    async def test_create_entity_with_tags(self, storage):
        entity = await storage.create_entity(
            "Company",
            {"name": "TSMC", "tags": ["semiconductor", "foundry", "taiwan"]},
        )
        assert "semiconductor" in entity["tags"]
        assert "foundry" in entity["tags"]

    @pytest.mark.asyncio
    async def test_update_entity_tags(self, storage):
        entity = await storage.create_entity(
            "Company", {"name": "TSMC", "tags": ["semiconductor"]}
        )
        updated = await storage.update_entity(
            entity["id"], {"tags": ["semiconductor", "critical"]}
        )
        assert "critical" in updated["tags"]

    @pytest.mark.asyncio
    async def test_find_entities_by_tags(self, storage):
        await storage.create_entity(
            "Company", {"name": "TSMC", "tags": ["semiconductor", "foundry"]}
        )
        await storage.create_entity(
            "Company", {"name": "NVIDIA", "tags": ["semiconductor", "gpu"]}
        )
        await storage.create_entity(
            "Company", {"name": "Ford", "tags": ["automotive"]}
        )
        results = await storage.find_entities(
            filters={"tags": ["semiconductor"]}
        )
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert "TSMC" in names
        assert "NVIDIA" in names


# ── Edge CRUD ──


class TestPostgresEdgeCRUD:
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
        import uuid
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        with pytest.raises(ValueError, match="source"):
            await storage.create_edge(str(uuid.uuid4()), e2["id"], "SUPPLIES_TO", {})

    @pytest.mark.asyncio
    async def test_create_edge_validates_target(self, storage):
        import uuid
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        with pytest.raises(ValueError, match="target"):
            await storage.create_edge(e1["id"], str(uuid.uuid4()), "SUPPLIES_TO", {})

    @pytest.mark.asyncio
    async def test_get_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        created = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5}
        )
        found = await storage.get_edge(created["id"])
        assert found is not None
        assert found["relation_type"] == "SUPPLIES_TO"

    @pytest.mark.asyncio
    async def test_update_edge(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.5}
        )
        updated = await storage.update_edge(edge["id"], {"weight": 0.9})
        assert updated["weight"] == pytest.approx(0.9, abs=0.01)

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


# ── Edge Tags ──


class TestPostgresEdgeTags:
    """Tags on edges — stored as TEXT[] with GIN index."""

    @pytest.mark.asyncio
    async def test_create_edge_with_tags(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO",
            {"weight": 0.8, "tags": ["critical", "semiconductor"]},
        )
        assert "critical" in edge["tags"]
        assert "semiconductor" in edge["tags"]

    @pytest.mark.asyncio
    async def test_update_edge_tags(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        edge = await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO",
            {"weight": 0.8, "tags": ["critical"]},
        )
        updated = await storage.update_edge(
            edge["id"], {"tags": ["critical", "tier-1"]}
        )
        assert "tier-1" in updated["tags"]


# ── Traversal ──


class TestPostgresTraversal:
    """Graph traversal with recursive CTEs."""

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
    async def test_get_subgraph_with_relation_filter(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e3 = await storage.create_entity("Company", {"name": "AMD"})
        await storage.create_edge(e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.8})
        await storage.create_edge(e2["id"], e3["id"], "COMPETES_WITH", {"weight": 0.9})
        subgraph = await storage.get_subgraph(
            e1["id"], max_depth=2, relation_types=["SUPPLIES_TO"]
        )
        assert len(subgraph["nodes"]) == 2  # Only TSMC and NVIDIA
        assert len(subgraph["edges"]) == 1

    @pytest.mark.asyncio
    async def test_traverse_bfs(self, storage):
        e1 = await storage.create_entity("Company", {"name": "TSMC"})
        e2 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e3 = await storage.create_entity("Company", {"name": "Apple"})
        await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.9, "confidence": 1.0}
        )
        await storage.create_edge(
            e2["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.8, "confidence": 1.0}
        )
        results = await storage.traverse(e1["id"], max_depth=3)
        assert len(results) == 2
        depths = {r["depth"] for r in results}
        assert 1 in depths
        assert 2 in depths

    @pytest.mark.asyncio
    async def test_traverse_respects_min_weight(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        e3 = await storage.create_entity("Company", {"name": "C"})
        await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.9, "confidence": 1.0}
        )
        await storage.create_edge(
            e1["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.1, "confidence": 1.0}
        )
        results = await storage.traverse(e1["id"], min_weight=0.5)
        assert len(results) == 1
        assert results[0]["entity"]["name"] == "B"

    @pytest.mark.asyncio
    async def test_traverse_avoids_cycles(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        e3 = await storage.create_entity("Company", {"name": "C"})
        await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO", {"weight": 0.9, "confidence": 1.0}
        )
        await storage.create_edge(
            e2["id"], e3["id"], "SUPPLIES_TO", {"weight": 0.8, "confidence": 1.0}
        )
        # Cycle: C -> A
        await storage.create_edge(
            e3["id"], e1["id"], "SUPPLIES_TO", {"weight": 0.7, "confidence": 1.0}
        )
        results = await storage.traverse(e1["id"], max_depth=10)
        # Should terminate despite cycle
        entity_ids = {r["entity"]["id"] for r in results}
        assert len(entity_ids) <= 3


# ── Search ──


class TestPostgresSearch:
    """Entity search (pg_trgm or ILIKE fallback)."""

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
        assert len(results) >= 1

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


# ── Temporal edges ──


class TestPostgresTemporalEdges:
    """Temporal edge queries with valid_from/valid_until."""

    @pytest.mark.asyncio
    async def test_find_edges_at_time(self, storage):
        e1 = await storage.create_entity("Company", {"name": "A"})
        e2 = await storage.create_entity("Company", {"name": "B"})
        await storage.create_edge(
            e1["id"], e2["id"], "SUPPLIES_TO",
            {
                "weight": 0.8,
                "valid_from": "2024-01-01T00:00:00+00:00",
                "valid_until": "2025-01-01T00:00:00+00:00",
            },
        )
        # Within range
        results = await storage.find_edges_at_time(
            "2024-06-15T00:00:00+00:00", source_id=e1["id"]
        )
        assert len(results) == 1

        # Outside range
        results = await storage.find_edges_at_time(
            "2025-06-15T00:00:00+00:00", source_id=e1["id"]
        )
        assert len(results) == 0


# ── Merge ──


class TestPostgresMerge:
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
            "Company",
            {"canonical_name": "tsmc"},
            {"name": "TSMC Ltd", "revenue": "50B"},
        )
        assert result["name"] == "TSMC Ltd"


# ── Health & Backup ──


class TestPostgresHealthAndBackup:
    """Health check and JSON backup."""

    @pytest.mark.asyncio
    async def test_health_check(self, storage):
        health = await storage.health_check()
        assert health["status"] == "healthy"
        assert health["backend"] == "postgres"

    @pytest.mark.asyncio
    async def test_backup_json(self, storage):
        await storage.create_entity("Company", {"name": "TSMC"})
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            backup_path = f.name
        try:
            result = await storage.backup(backup_path)
            assert result is True
            with open(backup_path) as f:
                data = json.load(f)
            assert len(data["entities"]) == 1
            assert data["entities"][0]["name"] == "TSMC"
        finally:
            os.unlink(backup_path)
