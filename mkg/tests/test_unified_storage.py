# mkg/tests/test_unified_storage.py
"""Tests for unified SQLite storage in ServiceContainer.

Verifies:
1. ServiceContainer uses SQLiteGraphStorage (not Neo4j dummy)
2. Graph data persists across ServiceContainer recreation (restart simulation)
3. API and task layers use the same storage backend
4. No storage divergence between ServiceContainer and ServiceFactory
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


class TestServiceContainerUsesSQLite:
    """Verify ServiceContainer now uses SQLite, not Neo4j dummy."""

    @pytest.fixture(autouse=True)
    def _set_db_dir(self, tmp_path):
        old = os.environ.get("MKG_DB_DIR")
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        yield
        if old is not None:
            os.environ["MKG_DB_DIR"] = old
        else:
            os.environ.pop("MKG_DB_DIR", None)

    def test_graph_storage_is_sqlite(self):
        from mkg.api.dependencies import ServiceContainer
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        c = ServiceContainer()
        assert isinstance(c.graph_storage, SQLiteGraphStorage)

    def test_graph_storage_not_neo4j(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert type(c.graph_storage).__name__ == "SQLiteGraphStorage"

    async def test_health_reports_sqlite(self, tmp_path):
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        from mkg.api.app import create_app
        app = create_app()
        container = deps.init_container()
        await container.startup()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["graph"]["backend"] == "sqlite"
        await container.shutdown()
        deps._container = None


class TestGraphPersistenceAcrossRestarts:
    """Simulate process restart — data should survive."""

    async def test_entity_persists_across_container_recreations(self, tmp_path):
        """Create entity → shutdown → recreate container → entity still there."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        # Container 1: create entity
        c1 = deps.ServiceContainer()
        await c1.startup()
        entity = await c1.graph_storage.create_entity(
            entity_type="Company",
            properties={"name": "TSMC"},
        )
        entity_id = entity["id"]
        await c1.shutdown()

        # Container 2: query entity
        c2 = deps.ServiceContainer()
        await c2.startup()
        found = await c2.graph_storage.get_entity(entity_id)
        assert found is not None
        assert found["name"] == "TSMC"
        await c2.shutdown()
        os.environ.pop("MKG_DB_DIR", None)

    async def test_edge_persists_across_restarts(self, tmp_path):
        """Create entities and edge → restart → edge still there."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        c1 = deps.ServiceContainer()
        await c1.startup()
        e1 = await c1.graph_storage.create_entity("Company", {"name": "TSMC"})
        e2 = await c1.graph_storage.create_entity("Company", {"name": "NVIDIA"})
        edge = await c1.graph_storage.create_edge(
            source_id=e1["id"],
            target_id=e2["id"],
            relation_type="SUPPLIES_TO",
            properties={"weight": 0.9},
        )
        edge_id = edge["id"]
        await c1.shutdown()

        c2 = deps.ServiceContainer()
        await c2.startup()
        found_edge = await c2.graph_storage.get_edge(edge_id)
        assert found_edge is not None
        assert found_edge["relation_type"] == "SUPPLIES_TO"
        assert found_edge["weight"] == 0.9
        await c2.shutdown()
        os.environ.pop("MKG_DB_DIR", None)

    async def test_multiple_entities_survive_restart(self, tmp_path):
        """Create 10 entities → restart → all 10 still there."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        c1 = deps.ServiceContainer()
        await c1.startup()
        for i in range(10):
            await c1.graph_storage.create_entity(
                "Company", {"name": f"Company_{i}"}
            )
        await c1.shutdown()

        c2 = deps.ServiceContainer()
        await c2.startup()
        entities = await c2.graph_storage.find_entities()
        assert len(entities) == 10
        await c2.shutdown()
        os.environ.pop("MKG_DB_DIR", None)


class TestStorageConsistency:
    """Verify ServiceContainer and ServiceFactory use same storage format."""

    async def test_both_use_sqlite_at_same_path(self, tmp_path):
        """Both composition roots should read from the same graph.db."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        # Write via ServiceFactory
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir=str(tmp_path))
        await factory.initialize()
        entity = await factory.graph_storage.create_entity(
            "Company", {"name": "SharedEntity"}
        )
        entity_id = entity["id"]
        await factory.shutdown()

        # Read via ServiceContainer
        container = deps.ServiceContainer()
        await container.startup()
        found = await container.graph_storage.get_entity(entity_id)
        assert found is not None
        assert found["name"] == "SharedEntity"
        await container.shutdown()
        os.environ.pop("MKG_DB_DIR", None)

    async def test_container_writes_visible_from_factory(self, tmp_path):
        """Write via ServiceContainer, read via ServiceFactory."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        container = deps.ServiceContainer()
        await container.startup()
        entity = await container.graph_storage.create_entity(
            "Company", {"name": "ContainerEntity"}
        )
        entity_id = entity["id"]
        await container.shutdown()

        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir=str(tmp_path))
        await factory.initialize()
        found = await factory.graph_storage.get_entity(entity_id)
        assert found is not None
        assert found["name"] == "ContainerEntity"
        await factory.shutdown()
        os.environ.pop("MKG_DB_DIR", None)
