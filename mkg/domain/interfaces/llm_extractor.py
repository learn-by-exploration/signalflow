# mkg/domain/interfaces/llm_extractor.py
"""LLMExtractor — abstract interface for NER/RE extraction from text.

R-EX1 through R-EX5: Tiered extraction (Claude → Ollama → Regex).
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ExtractionTier(Enum):
    """Extraction tier levels."""

    TIER_1 = "tier_1_cloud"    # Claude Sonnet (highest quality)
    TIER_2 = "tier_2_local"    # Ollama local (fallback)
    TIER_3 = "tier_3_regex"    # Regex patterns (last resort)


class LLMExtractor(ABC):
    """Abstract interface for entity/relation extraction from text.

    Implementations: ClaudeExtractor (Tier 1), OllamaExtractor (Tier 2),
    RegexExtractor (Tier 3).
    """

    @abstractmethod
    async def extract_entities(
        self, text: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Extract named entities from text.

        Returns list of dicts with: name, entity_type, confidence, span.
        """
        ...

    @abstractmethod
    async def extract_relations(
        self, text: str, entities: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Extract relations between entities from text.

        Returns list of dicts with: source, target, relation_type, weight, confidence.
        """
        ...

    @abstractmethod
    async def extract_all(
        self, text: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Extract both entities and relations in a single pass.

        Returns dict with 'entities' and 'relations' lists.
        """
        ...

    @abstractmethod
    def get_tier(self) -> ExtractionTier:
        """Return the extraction tier of this implementation."""
        ...

    @abstractmethod
    def get_cost_estimate(self, text_length: int) -> float:
        """Estimate cost in USD for extracting from text of given length."""
        ...
