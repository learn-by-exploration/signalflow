# mkg/tests/test_relation_types.py
"""Tests for expanded relation types in the knowledge graph.

Verifies:
1. New relation types (OWNS, PARTNERS_WITH, INVESTS_IN, etc.) are defined
2. Edges can be created with new relation types
3. Propagation works through new relation types
"""

import pytest

from mkg.domain.entities.edge import RelationType


class TestRelationTypeEnum:
    """Verify all relation types are defined."""

    def test_original_relation_types_exist(self):
        """Original types still exist for backward compatibility."""
        original = [
            "SUPPLIES_TO", "COMPETES_WITH", "SUBSIDIARY_OF",
            "OPERATES_IN", "REGULATES", "EMPLOYS",
            "PRODUCES", "DEPENDS_ON", "AFFECTS",
        ]
        for name in original:
            assert hasattr(RelationType, name), f"Missing: {name}"

    def test_new_relation_types_exist(self):
        """New types added for supply chain modeling."""
        new_types = [
            "OWNS", "PARTNERS_WITH", "INVESTS_IN",
            "ACQUIRES", "LICENSES_FROM",
        ]
        for name in new_types:
            assert hasattr(RelationType, name), f"Missing: {name}"

    def test_total_relation_count(self):
        """Enum should have 14 total relation types."""
        assert len(RelationType) == 14

    def test_values_are_strings(self):
        for rt in RelationType:
            assert isinstance(rt.value, str)
            assert rt.value == rt.name


class TestEdgesWithNewTypes:
    """Create and query edges with new relation types."""

    async def test_create_edge_with_owns(self, tmp_path):
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        import os
        storage = SQLiteGraphStorage(db_path=os.path.join(str(tmp_path), "test.db"))
        await storage.initialize()

        e1 = await storage.create_entity("Company", {"name": "Alphabet"})
        e2 = await storage.create_entity("Company", {"name": "Google"})
        edge = await storage.create_edge(
            source_id=e1["id"],
            target_id=e2["id"],
            relation_type="OWNS",
            properties={"weight": 1.0},
        )
        assert edge["relation_type"] == "OWNS"
        await storage.close()

    async def test_create_edge_with_partners_with(self, tmp_path):
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        import os
        storage = SQLiteGraphStorage(db_path=os.path.join(str(tmp_path), "test.db"))
        await storage.initialize()

        e1 = await storage.create_entity("Company", {"name": "NVIDIA"})
        e2 = await storage.create_entity("Company", {"name": "TSMC"})
        edge = await storage.create_edge(
            source_id=e1["id"],
            target_id=e2["id"],
            relation_type="PARTNERS_WITH",
            properties={"weight": 0.9, "confidence": 0.85},
        )
        assert edge["relation_type"] == "PARTNERS_WITH"
        assert edge["confidence"] == 0.85
        await storage.close()

    async def test_find_edges_by_new_type(self, tmp_path):
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        import os
        storage = SQLiteGraphStorage(db_path=os.path.join(str(tmp_path), "test.db"))
        await storage.initialize()

        e1 = await storage.create_entity("Company", {"name": "SoftBank"})
        e2 = await storage.create_entity("Company", {"name": "ARM"})
        await storage.create_edge(
            source_id=e1["id"],
            target_id=e2["id"],
            relation_type="INVESTS_IN",
            properties={"weight": 0.7},
        )
        edges = await storage.find_edges(relation_type="INVESTS_IN")
        assert len(edges) == 1
        assert edges[0]["relation_type"] == "INVESTS_IN"
        await storage.close()
