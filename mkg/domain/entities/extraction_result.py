# mkg/domain/entities/extraction_result.py
"""ExtractionResult — structured output from the NER/RE extraction pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


class ExtractionResult:
    """Structured result from entity/relation extraction.

    Attributes:
        article_id: Source article that was processed.
        extractor_tier: Which tier produced this result.
        entities: List of extracted entity dicts.
        relations: List of extracted relation dicts.
        metadata: Extraction metadata (tokens, cost, timing).
        created_at: When extraction was performed.
    """

    __slots__ = (
        "article_id", "extractor_tier", "entities", "relations",
        "metadata", "created_at",
    )

    def __init__(
        self,
        article_id: str,
        extractor_tier: str,
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        metadata: Optional[dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        self.article_id = article_id
        self.extractor_tier = extractor_tier
        self.entities = entities
        self.relations = relations
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        return len(self.relations)

    @property
    def is_empty(self) -> bool:
        return self.entity_count == 0 and self.relation_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "extractor_tier": self.extractor_tier,
            "entities": list(self.entities),
            "relations": list(self.relations),
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionResult:
        return cls(
            article_id=data["article_id"],
            extractor_tier=data["extractor_tier"],
            entities=data.get("entities", []),
            relations=data.get("relations", []),
            metadata=data.get("metadata", {}),
        )
