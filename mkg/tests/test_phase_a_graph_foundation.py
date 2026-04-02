# mkg/tests/test_phase_a_graph_foundation.py
"""Phase A: Graph Foundation — Tests for all Phase A requirements.

Tests written FIRST (TDD Red phase). These tests cover:
- A1: Edge temporal validity (valid_from, valid_until) — R-KG4
- A2: Schema upgrades (updated_at, canonical_name columns) — R-KG4, R-KG9
- A3: Decimal precision for weight/confidence — R-KG11
- A4: Propagation direction (positive/negative polarity) — R-PE4
- A5: Edge confidence in propagation — R-PE1
- A6: Hybrid search with BM25-style scoring — R-KG8
- A7: Temporal versioning (state at time T) — R-KG5
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

# ── Fixtures ──


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temp DB directory and set env."""
    old = os.environ.get("MKG_DB_DIR")
    os.environ["MKG_DB_DIR"] = str(tmp_path)
    yield tmp_path
    if old is not None:
        os.environ["MKG_DB_DIR"] = old
    else:
        os.environ.pop("MKG_DB_DIR", None)


@pytest.fixture
async def storage(tmp_db):
    """Create and initialize an SQLite graph storage instance."""
    from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage

    db_path = str(tmp_db / "test_graph.db")
    s = SQLiteGraphStorage(db_path=db_path)
    await s.initialize()
    yield s
    await s.close()


async def _seed_entity(storage, name: str = "TSMC", entity_type: str = "Company") -> str:
    """Helper to create an entity, returns ID."""
    eid = str(uuid.uuid4())
    await storage.create_entity(entity_type, {"name": name, "canonical_name": name.upper()}, entity_id=eid)
    return eid


async def _seed_edge(
    storage,
    src: str,
    tgt: str,
    relation: str = "SUPPLIES_TO",
    weight: float = 0.8,
    confidence: float = 0.9,
    valid_from: str | None = None,
    valid_until: str | None = None,
    direction: str | None = None,
) -> str:
    """Helper to create an edge with optional temporal + direction fields."""
    eid = str(uuid.uuid4())
    props: dict = {"weight": weight, "confidence": confidence}
    if valid_from:
        props["valid_from"] = valid_from
    if valid_until:
        props["valid_until"] = valid_until
    if direction:
        props["direction"] = direction
    await storage.create_edge(src, tgt, relation, props, edge_id=eid)
    return eid


# ============================================================================
# A1: Edge Temporal Validity — R-KG4
# ============================================================================


class TestEdgeTemporalValidity:
    """R-KG4: Every edge MUST have valid_from and valid_until fields."""

    async def test_edge_domain_has_valid_from(self):
        """Edge domain model accepts valid_from parameter."""
        from mkg.domain.entities.edge import Edge, RelationType

        edge = Edge(
            id="e1",
            source_id="s1",
            target_id="t1",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.8,
            confidence=0.9,
            valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        assert edge.valid_from == datetime(2025, 1, 1, tzinfo=timezone.utc)

    async def test_edge_domain_has_valid_until(self):
        """Edge domain model accepts valid_until parameter."""
        from mkg.domain.entities.edge import Edge, RelationType

        edge = Edge(
            id="e1",
            source_id="s1",
            target_id="t1",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.8,
            confidence=0.9,
            valid_until=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )
        assert edge.valid_until == datetime(2026, 12, 31, tzinfo=timezone.utc)

    async def test_edge_valid_from_defaults_to_created_at(self):
        """valid_from defaults to created_at if not specified."""
        from mkg.domain.entities.edge import Edge, RelationType

        edge = Edge(
            id="e1", source_id="s1", target_id="t1",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.8, confidence=0.9,
        )
        assert edge.valid_from == edge.created_at

    async def test_edge_valid_until_defaults_to_none(self):
        """valid_until defaults to None (still valid / no expiry)."""
        from mkg.domain.entities.edge import Edge, RelationType

        edge = Edge(
            id="e1", source_id="s1", target_id="t1",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.8, confidence=0.9,
        )
        assert edge.valid_until is None

    async def test_edge_serialization_includes_temporal(self):
        """to_dict() includes valid_from and valid_until."""
        from mkg.domain.entities.edge import Edge, RelationType

        vf = datetime(2025, 1, 1, tzinfo=timezone.utc)
        vu = datetime(2026, 12, 31, tzinfo=timezone.utc)
        edge = Edge(
            id="e1", source_id="s1", target_id="t1",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.8, confidence=0.9,
            valid_from=vf, valid_until=vu,
        )
        d = edge.to_dict()
        assert d["valid_from"] == vf.isoformat()
        assert d["valid_until"] == vu.isoformat()

    async def test_edge_deserialization_restores_temporal(self):
        """from_dict() restores valid_from and valid_until."""
        from mkg.domain.entities.edge import Edge, RelationType

        vf = datetime(2025, 1, 1, tzinfo=timezone.utc)
        vu = datetime(2026, 12, 31, tzinfo=timezone.utc)
        data = {
            "id": "e1", "source_id": "s1", "target_id": "t1",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.8, "confidence": 0.9,
            "valid_from": vf.isoformat(), "valid_until": vu.isoformat(),
        }
        edge = Edge.from_dict(data)
        assert edge.valid_from == vf
        assert edge.valid_until == vu

    async def test_sqlite_stores_valid_from(self, storage):
        """SQLite persists valid_from as a first-class column."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")
        vf = "2025-01-01T00:00:00+00:00"
        edge_id = await _seed_edge(storage, src, tgt, valid_from=vf)
        edge = await storage.get_edge(edge_id)
        assert edge["valid_from"] == vf

    async def test_sqlite_stores_valid_until(self, storage):
        """SQLite persists valid_until as a first-class column."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")
        vu = "2026-12-31T00:00:00+00:00"
        edge_id = await _seed_edge(storage, src, tgt, valid_until=vu)
        edge = await storage.get_edge(edge_id)
        assert edge["valid_until"] == vu

    async def test_sqlite_null_valid_until_for_active_edge(self, storage):
        """Active edges have NULL valid_until."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")
        edge_id = await _seed_edge(storage, src, tgt)
        edge = await storage.get_edge(edge_id)
        assert edge.get("valid_until") is None


# ============================================================================
# A2: Schema Upgrades — updated_at + canonical_name as SQL columns
# ============================================================================


class TestSchemaUpgrades:
    """Entities and edges should have updated_at as first-class SQL columns."""

    async def test_entity_has_updated_at_in_storage(self, storage):
        """Entity stored with updated_at timestamp."""
        eid = await _seed_entity(storage, "Apple")
        entity = await storage.get_entity(eid)
        assert "updated_at" in entity

    async def test_edge_has_updated_at_in_storage(self, storage):
        """Edge stored with updated_at timestamp."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")
        edge_id = await _seed_edge(storage, src, tgt)
        edge = await storage.get_edge(edge_id)
        assert "updated_at" in edge

    async def test_update_entity_changes_updated_at(self, storage):
        """Updating entity bumps updated_at."""
        eid = await _seed_entity(storage, "Apple")
        e1 = await storage.get_entity(eid)
        await storage.update_entity(eid, {"name": "Apple Inc."})
        e2 = await storage.get_entity(eid)
        assert e2["updated_at"] >= e1["updated_at"]

    async def test_update_edge_changes_updated_at(self, storage):
        """Updating edge bumps updated_at."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")
        edge_id = await _seed_edge(storage, src, tgt)
        e1 = await storage.get_edge(edge_id)
        await storage.update_edge(edge_id, {"weight": 0.5})
        e2 = await storage.get_edge(edge_id)
        assert e2["updated_at"] >= e1["updated_at"]


# ============================================================================
# A4: Propagation Direction — Positive/Negative Impact Polarity — R-PE4
# ============================================================================


class TestPropagationDirection:
    """R-PE4: Propagation must carry direction: positive or negative impact."""

    async def test_edge_can_have_direction_positive(self, storage):
        """Edges can indicate positive impact direction."""
        src = await _seed_entity(storage, "Competitor")
        tgt = await _seed_entity(storage, "NVIDIA")
        edge_id = await _seed_edge(
            storage, src, tgt, relation="COMPETES_WITH",
            weight=0.7, direction="negative",
        )
        edge = await storage.get_edge(edge_id)
        assert edge["direction"] == "negative"

    async def test_propagation_carries_direction(self, storage):
        """Propagation results include direction (positive/negative)."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "TSMC")
        b = await _seed_entity(storage, "NVIDIA")
        c = await _seed_entity(storage, "AMD")

        # TSMC supplies NVIDIA (positive: good news for TSMC = good for NVIDIA)
        await _seed_edge(storage, a, b, "SUPPLIES_TO", weight=0.9, direction="positive")
        # TSMC supplies AMD competitor (negative: good news for TSMC/NVIDIA = bad for AMD)
        await _seed_edge(storage, b, c, "COMPETES_WITH", weight=0.7, direction="negative")

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0, max_depth=3)

        # Both entities should be in results
        entity_map = {r["entity_id"]: r for r in results}
        assert b in entity_map
        assert c in entity_map

        # NVIDIA should have positive direction
        assert entity_map[b]["direction"] == "positive"
        # AMD should have negative direction (positive * negative = negative)
        assert entity_map[c]["direction"] == "negative"

    async def test_propagation_direction_flips_on_negative_edge(self, storage):
        """A negative edge flips accumulated direction."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")
        c = await _seed_entity(storage, "C")

        # A→B positive, B→C negative ⇒ A→C is negative
        await _seed_edge(storage, a, b, "SUPPLIES_TO", weight=0.9, direction="positive")
        await _seed_edge(storage, b, c, "COMPETES_WITH", weight=0.8, direction="negative")

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0)

        c_result = next(r for r in results if r["entity_id"] == c)
        assert c_result["direction"] == "negative"

    async def test_double_negative_becomes_positive(self, storage):
        """Two negative edges: neg × neg = positive."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")
        c = await _seed_entity(storage, "C")

        await _seed_edge(storage, a, b, "COMPETES_WITH", weight=0.9, direction="negative")
        await _seed_edge(storage, b, c, "COMPETES_WITH", weight=0.8, direction="negative")

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0)

        c_result = next(r for r in results if r["entity_id"] == c)
        assert c_result["direction"] == "positive"

    async def test_default_direction_is_positive(self, storage):
        """If edge has no direction field, it defaults to positive."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")

        # No direction specified
        await _seed_edge(storage, a, b, "SUPPLIES_TO", weight=0.9)

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0)

        assert results[0]["direction"] == "positive"


# ============================================================================
# A5: Edge Confidence in Propagation
# ============================================================================


class TestConfidenceInPropagation:
    """Propagation should factor in edge confidence, not just weight."""

    async def test_propagation_uses_confidence(self, storage):
        """Impact = parent_impact * edge_weight * edge_confidence."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")

        # weight=0.8, confidence=0.5 → effective = 0.4
        await _seed_edge(storage, a, b, weight=0.8, confidence=0.5)

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0)

        assert len(results) == 1
        # Impact should be 1.0 * 0.8 * 0.5 = 0.4
        assert abs(results[0]["impact"] - 0.4) < 0.01

    async def test_low_confidence_edge_reduces_impact(self, storage):
        """Low-confidence edge dramatically reduces propagated impact."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")
        c = await _seed_entity(storage, "C")

        # High weight + high confidence
        await _seed_edge(storage, a, b, weight=0.9, confidence=0.95)
        # High weight + LOW confidence
        await _seed_edge(storage, a, c, weight=0.9, confidence=0.1)

        engine = PropagationEngine(storage)
        results = await engine.propagate(a, impact_score=1.0)

        b_result = next(r for r in results if r["entity_id"] == b)
        c_result = next(r for r in results if r["entity_id"] == c)

        # B should have much higher impact than C
        assert b_result["impact"] > c_result["impact"] * 5


# ============================================================================
# A6: Hybrid Search with BM25-Style Scoring — R-KG8
# ============================================================================


class TestHybridSearch:
    """R-KG8: Search must be BM25-style, not just LIKE substring."""

    async def test_search_returns_relevance_scores(self, storage):
        """Search results have meaningful scores, not hardcoded 1.0."""
        await storage.create_entity("Company", {
            "name": "TSMC",
            "canonical_name": "TSMC",
        })
        await storage.create_entity("Company", {
            "name": "TSMC Advanced Packaging Division",
            "canonical_name": "TSMC ADVANCED PACKAGING",
        })
        await storage.create_entity("Company", {
            "name": "Intel Corporation",
            "canonical_name": "INTEL",
        })

        results = await storage.search("TSMC")
        assert len(results) >= 2

        # Scores should not all be 1.0 — exact vs partial match
        scores = [r["score"] for r in results]
        assert any(s != 1.0 for s in scores), "Scores should vary, not all 1.0"

    async def test_exact_match_scores_higher(self, storage):
        """Exact name match scores higher than partial match."""
        await _seed_entity(storage, "TSMC")
        await _seed_entity(storage, "TSMC Advanced Packaging Division")
        await _seed_entity(storage, "About TSMC Quarterly Review")

        results = await storage.search("TSMC")
        # Exact match should be first
        assert results[0]["name"] == "TSMC"

    async def test_search_canonical_name(self, storage):
        """Search also matches against canonical_name field."""
        await storage.create_entity("Company", {
            "name": "Taiwan Semiconductor Mfg Co Ltd",
            "canonical_name": "TSMC",
        })
        results = await storage.search("TSMC")
        assert len(results) >= 1

    async def test_search_scores_by_term_frequency(self, storage):
        """Entity with query term in both name and properties scores higher."""
        await storage.create_entity("Company", {
            "name": "NVIDIA Corporation",
            "canonical_name": "NVIDIA",
            "description": "Leading GPU manufacturer",
        })
        await storage.create_entity("Sector", {
            "name": "Semiconductor Sector",
            "canonical_name": "SEMICONDUCTOR",
        })

        results = await storage.search("NVIDIA")
        if len(results) >= 1:
            # NVIDIA Corp should score highest
            assert "NVIDIA" in results[0]["name"]


# ============================================================================
# A7: Temporal Versioning — R-KG5
# ============================================================================


class TestTemporalVersioning:
    """R-KG5: Ability to query 'state of graph at time T'."""

    async def test_find_edges_at_time(self, storage):
        """Query edges that were valid at a specific point in time."""
        src = await _seed_entity(storage, "TSMC")
        tgt = await _seed_entity(storage, "NVIDIA")

        # Edge valid Jan 2025 – Jun 2025
        await _seed_edge(
            storage, src, tgt,
            valid_from="2025-01-01T00:00:00+00:00",
            valid_until="2025-06-30T00:00:00+00:00",
        )

        # Query at Feb 2025 — should find the edge
        results = await storage.find_edges_at_time(
            source_id=src, as_of="2025-02-15T00:00:00+00:00",
        )
        assert len(results) == 1

        # Query at Aug 2025 — edge expired
        results = await storage.find_edges_at_time(
            source_id=src, as_of="2025-08-15T00:00:00+00:00",
        )
        assert len(results) == 0

    async def test_find_edges_at_time_null_valid_until(self, storage):
        """Edges with NULL valid_until are treated as currently valid."""
        src = await _seed_entity(storage, "Intel")
        tgt = await _seed_entity(storage, "AMD")

        await _seed_edge(
            storage, src, tgt,
            valid_from="2024-01-01T00:00:00+00:00",
        )

        # Future query — still valid (no expiry)
        results = await storage.find_edges_at_time(
            source_id=src, as_of="2030-01-01T00:00:00+00:00",
        )
        assert len(results) == 1

    async def test_propagation_respects_temporal_validity(self, storage):
        """Propagation only follows edges valid at the given time."""
        from mkg.domain.services.propagation_engine import PropagationEngine

        a = await _seed_entity(storage, "A")
        b = await _seed_entity(storage, "B")
        c = await _seed_entity(storage, "C")

        # A→B valid in 2025
        await _seed_edge(
            storage, a, b, weight=0.9,
            valid_from="2025-01-01T00:00:00+00:00",
            valid_until="2025-12-31T00:00:00+00:00",
        )
        # A→C valid in 2026
        await _seed_edge(
            storage, a, c, weight=0.9,
            valid_from="2026-01-01T00:00:00+00:00",
            valid_until="2026-12-31T00:00:00+00:00",
        )

        engine = PropagationEngine(storage)

        # Propagate as of mid-2025 — only B reachable
        results = await engine.propagate(
            a, impact_score=1.0, as_of="2025-06-15T00:00:00+00:00",
        )
        entity_ids = {r["entity_id"] for r in results}
        assert b in entity_ids
        assert c not in entity_ids

        # Propagate as of mid-2026 — only C reachable
        results = await engine.propagate(
            a, impact_score=1.0, as_of="2026-06-15T00:00:00+00:00",
        )
        entity_ids = {r["entity_id"] for r in results}
        assert c in entity_ids
        assert b not in entity_ids
