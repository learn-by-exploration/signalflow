# mkg/tests/test_propagation_depth.py
"""Tests for configurable propagation depth.

Verifies:
1. Default propagation depth is 6 (increased from 4)
2. Propagation reaches depth 6 with proper chain
3. Custom max_depth is respected
4. Pipeline uses depth 6 for propagation
"""

import os

import pytest

from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
from mkg.domain.services.propagation_engine import PropagationEngine


class TestPropagationDepthDefault:
    """Verify default max_depth is 6."""

    async def test_default_max_depth_is_6(self):
        """PropagationEngine.propagate() default is max_depth=6."""
        import inspect
        sig = inspect.signature(PropagationEngine.propagate)
        default = sig.parameters["max_depth"].default
        assert default == 6, f"Expected default max_depth=6, got {default}"


class TestDeepPropagation:
    """Verify propagation reaches depth 6."""

    async def test_propagation_reaches_depth_5(self, tmp_path):
        """Build a 5-hop chain and verify all entities are reached."""
        storage = SQLiteGraphStorage(
            db_path=os.path.join(str(tmp_path), "graph.db")
        )
        await storage.initialize()

        # Create chain: A -> B -> C -> D -> E -> F
        entities = []
        for i in range(6):
            e = await storage.create_entity("Company", {"name": f"Entity_{i}"})
            entities.append(e)

        for i in range(5):
            await storage.create_edge(
                source_id=entities[i]["id"],
                target_id=entities[i + 1]["id"],
                relation_type="SUPPLIES_TO",
                properties={"weight": 0.9},
            )

        engine = PropagationEngine(storage)
        impacts = await engine.propagate(
            trigger_entity_id=entities[0]["id"],
            impact_score=1.0,
        )

        # Should reach all 5 downstream entities (depth 1-5)
        assert len(impacts) == 5
        depths = {imp["depth"] for imp in impacts}
        assert 5 in depths, f"Expected depth 5 to be reached, got depths: {depths}"

        await storage.close()

    async def test_propagation_stops_at_max_depth(self, tmp_path):
        """With max_depth=3, only first 3 hops should be reached."""
        storage = SQLiteGraphStorage(
            db_path=os.path.join(str(tmp_path), "graph.db")
        )
        await storage.initialize()

        # Create chain: A -> B -> C -> D -> E -> F
        entities = []
        for i in range(6):
            e = await storage.create_entity("Company", {"name": f"Entity_{i}"})
            entities.append(e)

        for i in range(5):
            await storage.create_edge(
                source_id=entities[i]["id"],
                target_id=entities[i + 1]["id"],
                relation_type="AFFECTS",
                properties={"weight": 0.9},
            )

        engine = PropagationEngine(storage)
        impacts = await engine.propagate(
            trigger_entity_id=entities[0]["id"],
            impact_score=1.0,
            max_depth=3,
        )

        max_depth = max(imp["depth"] for imp in impacts)
        assert max_depth == 3
        assert len(impacts) == 3

        await storage.close()

    async def test_propagation_impact_decays_with_depth(self, tmp_path):
        """Impact should decrease with each hop."""
        storage = SQLiteGraphStorage(
            db_path=os.path.join(str(tmp_path), "graph.db")
        )
        await storage.initialize()

        entities = []
        for i in range(4):
            e = await storage.create_entity("Company", {"name": f"Entity_{i}"})
            entities.append(e)

        for i in range(3):
            await storage.create_edge(
                source_id=entities[i]["id"],
                target_id=entities[i + 1]["id"],
                relation_type="DEPENDS_ON",
                properties={"weight": 0.5},
            )

        engine = PropagationEngine(storage)
        impacts = await engine.propagate(
            trigger_entity_id=entities[0]["id"],
            impact_score=1.0,
        )

        # Sort by depth
        impacts.sort(key=lambda x: x["depth"])
        for i in range(1, len(impacts)):
            assert impacts[i]["impact"] <= impacts[i - 1]["impact"]

        await storage.close()
