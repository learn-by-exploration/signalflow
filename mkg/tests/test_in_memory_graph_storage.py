# mkg/tests/test_in_memory_graph_storage.py
"""Tests for InMemoryGraphStorage — the test double for GraphStorage.

Validates that the in-memory implementation correctly implements
the full GraphStorage contract (R-PLAT-20, R-MF6) so it can be
used as a reliable test double for all domain/service tests.
"""

import pytest

from mkg.domain.interfaces.graph_storage import GraphStorage


class TestInMemoryGraphStorageInstantiation:
    """Verify InMemoryGraphStorage is a valid GraphStorage implementation."""

    def test_is_subclass_of_graph_storage(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        assert issubclass(InMemoryGraphStorage, GraphStorage)

    def test_can_be_instantiated(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        assert store is not None

    def test_starts_with_empty_entities(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        assert store._entities == {}

    def test_starts_with_empty_edges(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        assert store._edges == {}


class TestEntityCRUD:
    """Test entity create, read, update, delete operations."""

    @pytest.fixture
    def store(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        return InMemoryGraphStorage()

    @pytest.mark.asyncio
    async def test_create_entity_returns_dict_with_id(self, store):
        result = await store.create_entity("Company", {"name": "TSMC", "sector": "Semiconductors"})
        assert "id" in result
        assert result["name"] == "TSMC"
        assert result["sector"] == "Semiconductors"

    @pytest.mark.asyncio
    async def test_create_entity_with_explicit_id(self, store):
        result = await store.create_entity(
            "Company", {"name": "TSMC"}, entity_id="tsmc-001"
        )
        assert result["id"] == "tsmc-001"

    @pytest.mark.asyncio
    async def test_create_entity_auto_generates_id(self, store):
        result = await store.create_entity("Company", {"name": "TSMC"})
        assert result["id"] is not None
        assert len(result["id"]) > 0

    @pytest.mark.asyncio
    async def test_create_entity_stores_entity_type(self, store):
        result = await store.create_entity("Company", {"name": "TSMC"})
        assert result["entity_type"] == "Company"

    @pytest.mark.asyncio
    async def test_get_entity_returns_existing(self, store):
        created = await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc-001")
        fetched = await store.get_entity("tsmc-001")
        assert fetched is not None
        assert fetched["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_get_entity_returns_none_for_missing(self, store):
        result = await store.get_entity("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entity_merges_properties(self, store):
        await store.create_entity("Company", {"name": "TSMC", "sector": "Semiconductors"}, entity_id="tsmc-001")
        updated = await store.update_entity("tsmc-001", {"sector": "Chips", "country": "Taiwan"})
        assert updated is not None
        assert updated["name"] == "TSMC"  # preserved
        assert updated["sector"] == "Chips"  # updated
        assert updated["country"] == "Taiwan"  # added

    @pytest.mark.asyncio
    async def test_update_entity_returns_none_for_missing(self, store):
        result = await store.update_entity("nonexistent-id", {"name": "X"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity_returns_true(self, store):
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc-001")
        result = await store.delete_entity("tsmc-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_entity_removes_from_store(self, store):
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc-001")
        await store.delete_entity("tsmc-001")
        result = await store.get_entity("tsmc-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity_returns_false_for_missing(self, store):
        result = await store.delete_entity("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_entity_cascades_to_edges(self, store):
        """When an entity is deleted, all connected edges must be removed."""
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc-001")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia-001")
        edge = await store.create_edge("tsmc-001", "nvidia-001", "SUPPLIES_TO", {"weight": 0.85, "confidence": 0.9})
        await store.delete_entity("tsmc-001")
        edge_result = await store.get_edge(edge["id"])
        assert edge_result is None

    @pytest.mark.asyncio
    async def test_find_entities_returns_all_when_no_filter(self, store):
        await store.create_entity("Company", {"name": "TSMC"})
        await store.create_entity("Company", {"name": "NVIDIA"})
        results = await store.find_entities()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_entities_filters_by_type(self, store):
        await store.create_entity("Company", {"name": "TSMC"})
        await store.create_entity("Person", {"name": "Jensen Huang"})
        results = await store.find_entities(entity_type="Company")
        assert len(results) == 1
        assert results[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_find_entities_filters_by_properties(self, store):
        await store.create_entity("Company", {"name": "TSMC", "sector": "Semiconductors"})
        await store.create_entity("Company", {"name": "Apple", "sector": "Consumer Electronics"})
        results = await store.find_entities(filters={"sector": "Semiconductors"})
        assert len(results) == 1
        assert results[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_find_entities_respects_limit(self, store):
        for i in range(5):
            await store.create_entity("Company", {"name": f"Company-{i}"})
        results = await store.find_entities(limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_find_entities_respects_offset(self, store):
        for i in range(5):
            await store.create_entity("Company", {"name": f"Company-{i}"}, entity_id=f"c-{i}")
        all_results = await store.find_entities()
        offset_results = await store.find_entities(offset=2)
        assert len(offset_results) == 3
        assert offset_results[0]["id"] == all_results[2]["id"]


class TestEdgeCRUD:
    """Test edge create, read, update, delete operations."""

    @pytest.fixture
    async def store_with_entities(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc-001")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia-001")
        await store.create_entity("Company", {"name": "Apple"}, entity_id="apple-001")
        return store

    @pytest.mark.asyncio
    async def test_create_edge_returns_dict_with_id(self, store_with_entities):
        store = store_with_entities
        result = await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9}
        )
        assert "id" in result
        assert result["source_id"] == "tsmc-001"
        assert result["target_id"] == "nvidia-001"
        assert result["relation_type"] == "SUPPLIES_TO"

    @pytest.mark.asyncio
    async def test_create_edge_with_explicit_id(self, store_with_entities):
        store = store_with_entities
        result = await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="edge-001"
        )
        assert result["id"] == "edge-001"

    @pytest.mark.asyncio
    async def test_create_edge_validates_source_exists(self, store_with_entities):
        store = store_with_entities
        with pytest.raises(ValueError, match="source"):
            await store.create_edge(
                "nonexistent", "nvidia-001", "SUPPLIES_TO",
                {"weight": 0.85, "confidence": 0.9}
            )

    @pytest.mark.asyncio
    async def test_create_edge_validates_target_exists(self, store_with_entities):
        store = store_with_entities
        with pytest.raises(ValueError, match="target"):
            await store.create_edge(
                "tsmc-001", "nonexistent", "SUPPLIES_TO",
                {"weight": 0.85, "confidence": 0.9}
            )

    @pytest.mark.asyncio
    async def test_get_edge_returns_existing(self, store_with_entities):
        store = store_with_entities
        created = await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="edge-001"
        )
        fetched = await store.get_edge("edge-001")
        assert fetched is not None
        assert fetched["source_id"] == "tsmc-001"

    @pytest.mark.asyncio
    async def test_get_edge_returns_none_for_missing(self, store_with_entities):
        store = store_with_entities
        result = await store.get_edge("nonexistent-edge")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_edge_merges_properties(self, store_with_entities):
        store = store_with_entities
        await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="edge-001"
        )
        updated = await store.update_edge("edge-001", {"weight": 0.95, "notes": "updated"})
        assert updated is not None
        assert updated["weight"] == 0.95
        assert updated["confidence"] == 0.9  # preserved
        assert updated["notes"] == "updated"  # added

    @pytest.mark.asyncio
    async def test_update_edge_returns_none_for_missing(self, store_with_entities):
        store = store_with_entities
        result = await store.update_edge("nonexistent-edge", {"weight": 0.5})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_edge_returns_true(self, store_with_entities):
        store = store_with_entities
        await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="edge-001"
        )
        result = await store.delete_edge("edge-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_edge_removes_from_store(self, store_with_entities):
        store = store_with_entities
        await store.create_edge(
            "tsmc-001", "nvidia-001", "SUPPLIES_TO",
            {"weight": 0.85, "confidence": 0.9},
            edge_id="edge-001"
        )
        await store.delete_edge("edge-001")
        result = await store.get_edge("edge-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_edge_returns_false_for_missing(self, store_with_entities):
        store = store_with_entities
        result = await store.delete_edge("nonexistent-edge")
        assert result is False

    @pytest.mark.asyncio
    async def test_find_edges_by_source(self, store_with_entities):
        store = store_with_entities
        await store.create_edge("tsmc-001", "nvidia-001", "SUPPLIES_TO", {"weight": 0.85, "confidence": 0.9})
        await store.create_edge("tsmc-001", "apple-001", "SUPPLIES_TO", {"weight": 0.75, "confidence": 0.8})
        results = await store.find_edges(source_id="tsmc-001")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_edges_by_target(self, store_with_entities):
        store = store_with_entities
        await store.create_edge("tsmc-001", "nvidia-001", "SUPPLIES_TO", {"weight": 0.85, "confidence": 0.9})
        await store.create_edge("apple-001", "nvidia-001", "COMPETES_WITH", {"weight": 0.5, "confidence": 0.7})
        results = await store.find_edges(target_id="nvidia-001")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_edges_by_relation_type(self, store_with_entities):
        store = store_with_entities
        await store.create_edge("tsmc-001", "nvidia-001", "SUPPLIES_TO", {"weight": 0.85, "confidence": 0.9})
        await store.create_edge("apple-001", "nvidia-001", "COMPETES_WITH", {"weight": 0.5, "confidence": 0.7})
        results = await store.find_edges(relation_type="SUPPLIES_TO")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_find_edges_respects_limit(self, store_with_entities):
        store = store_with_entities
        for i in range(5):
            await store.create_entity("Company", {"name": f"Target-{i}"}, entity_id=f"t-{i}")
            await store.create_edge("tsmc-001", f"t-{i}", "SUPPLIES_TO", {"weight": 0.5, "confidence": 0.5})
        results = await store.find_edges(limit=3)
        assert len(results) == 3


class TestTraversal:
    """Test graph traversal operations."""

    @pytest.fixture
    async def store_with_graph(self):
        """Build a small supply chain graph:
        TSMC --SUPPLIES_TO--> NVIDIA --SUPPLIES_TO--> Dell
        TSMC --SUPPLIES_TO--> Apple
        """
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Company", {"name": "Dell"}, entity_id="dell")
        await store.create_entity("Company", {"name": "Apple"}, entity_id="apple")
        await store.create_edge("tsmc", "nvidia", "SUPPLIES_TO", {"weight": 0.85, "confidence": 0.9})
        await store.create_edge("nvidia", "dell", "SUPPLIES_TO", {"weight": 0.70, "confidence": 0.8})
        await store.create_edge("tsmc", "apple", "SUPPLIES_TO", {"weight": 0.75, "confidence": 0.85})
        return store

    @pytest.mark.asyncio
    async def test_get_neighbors_outgoing(self, store_with_graph):
        store = store_with_graph
        neighbors = await store.get_neighbors("tsmc", direction="outgoing")
        names = [n["name"] for n in neighbors]
        assert "NVIDIA" in names
        assert "Apple" in names
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_incoming(self, store_with_graph):
        store = store_with_graph
        neighbors = await store.get_neighbors("nvidia", direction="incoming")
        assert len(neighbors) == 1
        assert neighbors[0]["name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_get_neighbors_both(self, store_with_graph):
        store = store_with_graph
        neighbors = await store.get_neighbors("nvidia", direction="both")
        names = [n["name"] for n in neighbors]
        assert "TSMC" in names
        assert "Dell" in names

    @pytest.mark.asyncio
    async def test_get_neighbors_filter_by_relation(self, store_with_graph):
        store = store_with_graph
        neighbors = await store.get_neighbors("tsmc", relation_type="SUPPLIES_TO")
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_empty_for_leaf(self, store_with_graph):
        store = store_with_graph
        neighbors = await store.get_neighbors("dell", direction="outgoing")
        assert len(neighbors) == 0

    @pytest.mark.asyncio
    async def test_get_subgraph_depth_1(self, store_with_graph):
        store = store_with_graph
        subgraph = await store.get_subgraph("tsmc", max_depth=1)
        assert "nodes" in subgraph
        assert "edges" in subgraph
        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "tsmc" in node_ids
        assert "nvidia" in node_ids
        assert "apple" in node_ids
        assert "dell" not in node_ids  # depth 2

    @pytest.mark.asyncio
    async def test_get_subgraph_depth_2(self, store_with_graph):
        store = store_with_graph
        subgraph = await store.get_subgraph("tsmc", max_depth=2)
        node_ids = [n["id"] for n in subgraph["nodes"]]
        assert "dell" in node_ids  # now reachable at depth 2

    @pytest.mark.asyncio
    async def test_traverse_returns_paths(self, store_with_graph):
        store = store_with_graph
        paths = await store.traverse("tsmc", max_depth=4)
        assert len(paths) > 0
        for path in paths:
            assert "entity" in path
            assert "depth" in path
            assert "path" in path
            assert "cumulative_weight" in path

    @pytest.mark.asyncio
    async def test_traverse_respects_max_depth(self, store_with_graph):
        store = store_with_graph
        paths_depth1 = await store.traverse("tsmc", max_depth=1)
        paths_depth2 = await store.traverse("tsmc", max_depth=2)
        depths_1 = [p["depth"] for p in paths_depth1]
        depths_2 = [p["depth"] for p in paths_depth2]
        assert all(d <= 1 for d in depths_1)
        assert max(depths_2) == 2

    @pytest.mark.asyncio
    async def test_traverse_respects_min_weight(self, store_with_graph):
        store = store_with_graph
        paths = await store.traverse("tsmc", max_depth=2, min_weight=0.80)
        # Only TSMC->NVIDIA (0.85) passes, NVIDIA->Dell (0.70) doesn't
        entity_ids = [p["entity"]["id"] for p in paths]
        assert "nvidia" in entity_ids
        assert "dell" not in entity_ids

    @pytest.mark.asyncio
    async def test_traverse_filters_by_relation_type(self, store_with_graph):
        store = store_with_graph
        paths = await store.traverse("tsmc", relation_types=["SUPPLIES_TO"])
        assert len(paths) > 0

    @pytest.mark.asyncio
    async def test_traverse_cumulative_weight_decreases(self, store_with_graph):
        store = store_with_graph
        paths = await store.traverse("tsmc", max_depth=2)
        depth_1_weights = [p["cumulative_weight"] for p in paths if p["depth"] == 1]
        depth_2_weights = [p["cumulative_weight"] for p in paths if p["depth"] == 2]
        if depth_2_weights:
            assert max(depth_2_weights) <= max(depth_1_weights)


class TestSearchAndMerge:
    """Test search and merge/dedup operations."""

    @pytest.fixture
    async def store_with_data(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        store = InMemoryGraphStorage()
        await store.create_entity("Company", {"name": "Taiwan Semiconductor Manufacturing Company", "canonical_name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA Corporation", "canonical_name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Person", {"name": "Jensen Huang", "role": "CEO"}, entity_id="jensen")
        return store

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, store_with_data):
        store = store_with_data
        results = await store.search("TSMC")
        assert len(results) >= 1
        assert any("TSMC" in str(r.get("name", "") + r.get("canonical_name", "")) for r in results)

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, store_with_data):
        store = store_with_data
        results = await store.search("Company", limit=1)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_filters_by_entity_type(self, store_with_data):
        store = store_with_data
        results = await store.search("Jensen", entity_type="Person")
        assert len(results) >= 1
        assert all(r.get("entity_type") == "Person" for r in results)

    @pytest.mark.asyncio
    async def test_search_returns_relevance_scores(self, store_with_data):
        store = store_with_data
        results = await store.search("NVIDIA")
        for r in results:
            assert "score" in r

    @pytest.mark.asyncio
    async def test_merge_entity_creates_when_no_match(self, store_with_data):
        store = store_with_data
        before_count = len(await store.find_entities())
        result = await store.merge_entity(
            "Company",
            {"canonical_name": "AMD"},
            {"name": "Advanced Micro Devices", "canonical_name": "AMD", "sector": "Semiconductors"}
        )
        after_count = len(await store.find_entities())
        assert after_count == before_count + 1
        assert result["canonical_name"] == "AMD"

    @pytest.mark.asyncio
    async def test_merge_entity_updates_when_match_exists(self, store_with_data):
        store = store_with_data
        before_count = len(await store.find_entities())
        result = await store.merge_entity(
            "Company",
            {"canonical_name": "TSMC"},
            {"name": "TSMC Ltd", "canonical_name": "TSMC", "updated": True}
        )
        after_count = len(await store.find_entities())
        assert after_count == before_count  # no new entity
        assert result["updated"] is True
        assert result["canonical_name"] == "TSMC"


class TestBackupAndHealth:
    """Test backup and health check operations."""

    @pytest.fixture
    def store(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        return InMemoryGraphStorage()

    @pytest.mark.asyncio
    async def test_backup_returns_true(self, store):
        result = await store.backup("/tmp/test_backup")
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, store):
        result = await store.health_check()
        assert result["status"] == "healthy"
        assert "entity_count" in result
        assert "edge_count" in result

    @pytest.mark.asyncio
    async def test_health_check_reflects_data_counts(self, store):
        await store.create_entity("Company", {"name": "TSMC"})
        await store.create_entity("Company", {"name": "NVIDIA"})
        health = await store.health_check()
        assert health["entity_count"] == 2
        assert health["edge_count"] == 0
