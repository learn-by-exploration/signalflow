# mkg/domain/entities/edge.py
"""Edge (relationship) domain model for the Market Knowledge Graph.

Represents typed edges: SUPPLIES_TO, COMPETES_WITH, SUBSIDIARY_OF, etc.
Each edge has a weight [0, 1] and confidence [0, 1].
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class RelationType(Enum):
    """Valid relationship types in the knowledge graph."""

    SUPPLIES_TO = "SUPPLIES_TO"
    COMPETES_WITH = "COMPETES_WITH"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    OPERATES_IN = "OPERATES_IN"
    REGULATES = "REGULATES"
    EMPLOYS = "EMPLOYS"
    PRODUCES = "PRODUCES"
    DEPENDS_ON = "DEPENDS_ON"
    AFFECTS = "AFFECTS"
    OWNS = "OWNS"
    PARTNERS_WITH = "PARTNERS_WITH"
    INVESTS_IN = "INVESTS_IN"
    ACQUIRES = "ACQUIRES"
    LICENSES_FROM = "LICENSES_FROM"


class Edge:
    """Domain model for a knowledge graph edge (relationship).

    Attributes:
        id: Unique edge identifier.
        source_id: Source entity ID.
        target_id: Target entity ID.
        relation_type: Typed relationship label.
        weight: Impact weight [0.0, 1.0] — used by propagation engine.
        confidence: Extraction confidence [0.0, 1.0].
        metadata: Arbitrary typed properties.
        source: Attribution to the source document/extraction.
        created_at: When this edge was first created.
        updated_at: When this edge was last modified.
    """

    __slots__ = (
        "id", "source_id", "target_id", "relation_type",
        "weight", "confidence", "metadata", "source",
        "created_at", "updated_at", "valid_from", "valid_until",
    )

    def __init__(
        self,
        id: str,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float,
        confidence: float,
        metadata: Optional[dict[str, Any]] = None,
        source: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
    ) -> None:
        if not source_id:
            raise ValueError("source_id cannot be empty")
        if not target_id:
            raise ValueError("target_id cannot be empty")
        if source_id == target_id:
            raise ValueError("source_id and target_id cannot be the same (self-loops not allowed)")
        if weight < 0.0 or weight > 1.0:
            raise ValueError(f"weight must be between 0.0 and 1.0, got {weight}")
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        self.id = id
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.weight = weight
        self.confidence = confidence
        self.metadata = metadata or {}
        self.source = source
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.valid_from = valid_from if valid_from is not None else self.created_at
        self.valid_until = valid_until

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for storage/API."""
        d = {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        }
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        """Deserialize from a plain dict."""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        valid_from = data.get("valid_from")
        valid_until = data.get("valid_until")
        if isinstance(valid_from, str):
            valid_from = datetime.fromisoformat(valid_from)
        if isinstance(valid_until, str):
            valid_until = datetime.fromisoformat(valid_until)

        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data["relation_type"]),
            weight=data["weight"],
            confidence=data["confidence"],
            metadata=data.get("metadata", {}),
            source=data.get("source"),
            created_at=created_at,
            updated_at=updated_at,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    def __repr__(self) -> str:
        return (
            f"Edge(id={self.id!r}, {self.source_id} "
            f"-[{self.relation_type.value}]-> {self.target_id}, "
            f"w={self.weight})"
        )
