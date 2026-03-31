# mkg/domain/entities/node.py
"""Entity (node) domain model for the Market Knowledge Graph.

Represents typed entities: Company, Product, Facility, Person,
Country, Regulation, Sector, Event.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EntityType(Enum):
    """Valid entity node types in the knowledge graph."""

    COMPANY = "Company"
    PRODUCT = "Product"
    FACILITY = "Facility"
    PERSON = "Person"
    COUNTRY = "Country"
    REGULATION = "Regulation"
    SECTOR = "Sector"
    EVENT = "Event"


class Entity:
    """Domain model for a knowledge graph entity node.

    Attributes:
        id: Unique entity identifier.
        entity_type: Typed category (Company, Person, etc.).
        name: Display name.
        canonical_name: Normalized name for dedup matching.
        confidence: Extraction confidence [0.0, 1.0].
        metadata: Arbitrary typed properties.
        source: Attribution to the source document/extraction.
        created_at: When this entity was first created.
        updated_at: When this entity was last modified.
    """

    __slots__ = (
        "id", "entity_type", "name", "canonical_name",
        "confidence", "metadata", "source", "created_at", "updated_at",
    )

    def __init__(
        self,
        id: str,
        entity_type: EntityType,
        name: str,
        canonical_name: str,
        confidence: float = 1.0,
        metadata: Optional[dict[str, Any]] = None,
        source: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if not name:
            raise ValueError("Entity name cannot be empty")
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        self.id = id
        self.entity_type = entity_type
        self.name = name
        self.canonical_name = canonical_name
        self.confidence = confidence
        self.metadata = metadata or {}
        self.source = source
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for storage/API."""
        return {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Entity:
        """Deserialize from a plain dict."""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data["id"],
            entity_type=EntityType(data["entity_type"]),
            name=data["name"],
            canonical_name=data.get("canonical_name", data["name"]),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            source=data.get("source"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __repr__(self) -> str:
        return f"Entity(id={self.id!r}, type={self.entity_type.value}, name={self.name!r})"
