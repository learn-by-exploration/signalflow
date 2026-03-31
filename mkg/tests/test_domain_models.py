# mkg/tests/test_domain_models.py
"""Tests for Entity and Edge domain models.

Verifies rich domain models with validation, immutability, and
typed entity/edge types per R-KG1 through R-KG4, R-KG7, R-KG9.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest


class TestEntityTypes:
    """Verify the EntityType enum covers all required node labels."""

    def test_entity_type_has_company(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.COMPANY.value == "Company"

    def test_entity_type_has_product(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.PRODUCT.value == "Product"

    def test_entity_type_has_facility(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.FACILITY.value == "Facility"

    def test_entity_type_has_person(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.PERSON.value == "Person"

    def test_entity_type_has_country(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.COUNTRY.value == "Country"

    def test_entity_type_has_regulation(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.REGULATION.value == "Regulation"

    def test_entity_type_has_sector(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.SECTOR.value == "Sector"

    def test_entity_type_has_event(self):
        from mkg.domain.entities.node import EntityType
        assert EntityType.EVENT.value == "Event"

    def test_all_entity_types_count(self):
        from mkg.domain.entities.node import EntityType
        assert len(EntityType) >= 8


class TestRelationTypes:
    """Verify the RelationType enum covers all required edge labels."""

    def test_relation_type_has_supplies_to(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.SUPPLIES_TO.value == "SUPPLIES_TO"

    def test_relation_type_has_competes_with(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.COMPETES_WITH.value == "COMPETES_WITH"

    def test_relation_type_has_subsidiary_of(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.SUBSIDIARY_OF.value == "SUBSIDIARY_OF"

    def test_relation_type_has_operates_in(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.OPERATES_IN.value == "OPERATES_IN"

    def test_relation_type_has_regulates(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.REGULATES.value == "REGULATES"

    def test_relation_type_has_employs(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.EMPLOYS.value == "EMPLOYS"

    def test_relation_type_has_produces(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.PRODUCES.value == "PRODUCES"

    def test_relation_type_has_depends_on(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.DEPENDS_ON.value == "DEPENDS_ON"

    def test_relation_type_has_affects(self):
        from mkg.domain.entities.edge import RelationType
        assert RelationType.AFFECTS.value == "AFFECTS"

    def test_all_relation_types_count(self):
        from mkg.domain.entities.edge import RelationType
        assert len(RelationType) >= 9


class TestEntity:
    """Test the Entity domain model."""

    def test_create_entity_with_required_fields(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.id == "tsmc-001"
        assert entity.entity_type == EntityType.COMPANY
        assert entity.name == "TSMC"

    def test_entity_has_canonical_name(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="Taiwan Semiconductor Manufacturing Company",
            canonical_name="TSMC",
        )
        assert entity.canonical_name == "TSMC"

    def test_entity_has_metadata_dict(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            metadata={"ticker": "TSM", "sector": "Semiconductors"},
        )
        assert entity.metadata["ticker"] == "TSM"

    def test_entity_has_created_at_timestamp(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.created_at is not None
        assert isinstance(entity.created_at, datetime)

    def test_entity_has_updated_at_timestamp(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.updated_at is not None

    def test_entity_has_confidence_score(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            confidence=0.95,
        )
        assert entity.confidence == 0.95

    def test_entity_confidence_defaults_to_one(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.confidence == 1.0

    def test_entity_confidence_must_be_between_0_and_1(self):
        from mkg.domain.entities.node import Entity, EntityType
        with pytest.raises(ValueError):
            Entity(
                id="tsmc-001",
                entity_type=EntityType.COMPANY,
                name="TSMC",
                canonical_name="TSMC",
                confidence=1.5,
            )

    def test_entity_confidence_rejects_negative(self):
        from mkg.domain.entities.node import Entity, EntityType
        with pytest.raises(ValueError):
            Entity(
                id="tsmc-001",
                entity_type=EntityType.COMPANY,
                name="TSMC",
                canonical_name="TSMC",
                confidence=-0.1,
            )

    def test_entity_name_cannot_be_empty(self):
        from mkg.domain.entities.node import Entity, EntityType
        with pytest.raises(ValueError):
            Entity(
                id="tsmc-001",
                entity_type=EntityType.COMPANY,
                name="",
                canonical_name="TSMC",
            )

    def test_entity_to_dict(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            metadata={"ticker": "TSM"},
        )
        d = entity.to_dict()
        assert d["id"] == "tsmc-001"
        assert d["entity_type"] == "Company"
        assert d["name"] == "TSMC"
        assert d["metadata"]["ticker"] == "TSM"

    def test_entity_from_dict(self):
        from mkg.domain.entities.node import Entity, EntityType
        d = {
            "id": "tsmc-001",
            "entity_type": "Company",
            "name": "TSMC",
            "canonical_name": "TSMC",
            "metadata": {"ticker": "TSM"},
            "confidence": 0.95,
        }
        entity = Entity.from_dict(d)
        assert entity.id == "tsmc-001"
        assert entity.entity_type == EntityType.COMPANY
        assert entity.confidence == 0.95

    def test_entity_has_source_attribution(self):
        """R-KG9: Every node should track its source."""
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
            source="reuters-article-12345",
        )
        assert entity.source == "reuters-article-12345"

    def test_entity_source_default_none(self):
        from mkg.domain.entities.node import Entity, EntityType
        entity = Entity(
            id="tsmc-001",
            entity_type=EntityType.COMPANY,
            name="TSMC",
            canonical_name="TSMC",
        )
        assert entity.source is None


class TestEdge:
    """Test the Edge domain model."""

    def test_create_edge_with_required_fields(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        assert edge.id == "edge-001"
        assert edge.source_id == "tsmc-001"
        assert edge.target_id == "nvidia-001"

    def test_edge_has_weight(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        assert edge.weight == 0.85

    def test_edge_weight_must_be_between_0_and_1(self):
        from mkg.domain.entities.edge import Edge, RelationType
        with pytest.raises(ValueError):
            Edge(
                id="edge-001",
                source_id="tsmc-001",
                target_id="nvidia-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=1.5,
                confidence=0.92,
            )

    def test_edge_weight_rejects_negative(self):
        from mkg.domain.entities.edge import Edge, RelationType
        with pytest.raises(ValueError):
            Edge(
                id="edge-001",
                source_id="tsmc-001",
                target_id="nvidia-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=-0.1,
                confidence=0.92,
            )

    def test_edge_has_confidence(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        assert edge.confidence == 0.92

    def test_edge_confidence_must_be_between_0_and_1(self):
        from mkg.domain.entities.edge import Edge, RelationType
        with pytest.raises(ValueError):
            Edge(
                id="edge-001",
                source_id="tsmc-001",
                target_id="nvidia-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=0.85,
                confidence=1.1,
            )

    def test_edge_has_metadata(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
            metadata={"product_category": "Advanced Logic Chips"},
        )
        assert edge.metadata["product_category"] == "Advanced Logic Chips"

    def test_edge_has_timestamps(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        assert edge.created_at is not None
        assert edge.updated_at is not None

    def test_edge_has_source_attribution(self):
        """R-KG9: Every edge should track its source."""
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
            source="claude-extraction-abc123",
        )
        assert edge.source == "claude-extraction-abc123"

    def test_edge_to_dict(self):
        from mkg.domain.entities.edge import Edge, RelationType
        edge = Edge(
            id="edge-001",
            source_id="tsmc-001",
            target_id="nvidia-001",
            relation_type=RelationType.SUPPLIES_TO,
            weight=0.85,
            confidence=0.92,
        )
        d = edge.to_dict()
        assert d["id"] == "edge-001"
        assert d["relation_type"] == "SUPPLIES_TO"
        assert d["weight"] == 0.85

    def test_edge_from_dict(self):
        from mkg.domain.entities.edge import Edge, RelationType
        d = {
            "id": "edge-001",
            "source_id": "tsmc-001",
            "target_id": "nvidia-001",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.85,
            "confidence": 0.92,
        }
        edge = Edge.from_dict(d)
        assert edge.id == "edge-001"
        assert edge.relation_type == RelationType.SUPPLIES_TO

    def test_edge_source_and_target_cannot_be_same(self):
        from mkg.domain.entities.edge import Edge, RelationType
        with pytest.raises(ValueError):
            Edge(
                id="edge-001",
                source_id="tsmc-001",
                target_id="tsmc-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=0.85,
                confidence=0.92,
            )

    def test_edge_source_id_cannot_be_empty(self):
        from mkg.domain.entities.edge import Edge, RelationType
        with pytest.raises(ValueError):
            Edge(
                id="edge-001",
                source_id="",
                target_id="nvidia-001",
                relation_type=RelationType.SUPPLIES_TO,
                weight=0.85,
                confidence=0.92,
            )
