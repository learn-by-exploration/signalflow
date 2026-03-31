# mkg/infrastructure/llm/claude_extractor.py
"""ClaudeExtractor — Tier 1 cloud NER/RE extraction via Claude API.

R-EX1: Highest-quality extraction using claude-sonnet-4-20250514.
"""

import json
import logging
from typing import Any, Callable, Optional

from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

logger = logging.getLogger(__name__)

_ENTITY_PROMPT = """You are an expert financial NER system. Extract all named entities from:

"{text}"

Entity types: Company, Product, Facility, Person, Country, Regulation, Sector, Event.

Respond ONLY with valid JSON:
{{"entities": [{{"name": "...", "entity_type": "...", "confidence": 0.0-1.0}}]}}"""

_RELATION_PROMPT = """You are an expert financial relation extraction system.
Given these entities: {entities}

Extract relationships from: "{text}"

Relation types: SUPPLIES_TO, COMPETES_WITH, SUBSIDIARY_OF, OPERATES_IN, REGULATES, EMPLOYS, PRODUCES, DEPENDS_ON, AFFECTS.

Respond ONLY with valid JSON:
{{"relations": [{{"source": "...", "target": "...", "relation_type": "...", "weight": 0.0-1.0, "confidence": 0.0-1.0}}]}}"""

_ALL_PROMPT = """You are an expert financial NER+RE system. Extract all entities and relationships from:

"{text}"

Entity types: Company, Product, Facility, Person, Country, Regulation, Sector, Event.
Relation types: SUPPLIES_TO, COMPETES_WITH, SUBSIDIARY_OF, OPERATES_IN, REGULATES, EMPLOYS, PRODUCES, DEPENDS_ON, AFFECTS.

Respond ONLY with valid JSON:
{{"entities": [{{"name": "...", "entity_type": "...", "confidence": 0.0-1.0}}], "relations": [{{"source": "...", "target": "...", "relation_type": "...", "weight": 0.0-1.0, "confidence": 0.0-1.0}}]}}"""

# Cost: ~$3/MTok input, ~$15/MTok output for Sonnet
_COST_PER_CHAR_USD = 0.000004


class ClaudeExtractor(LLMExtractor):
    """Tier 1 extraction via Claude Sonnet API."""

    def __init__(
        self, api_key: str, model: str = "claude-sonnet-4-20250514"
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._call_api: Callable = self._real_api_call

    def get_tier(self) -> ExtractionTier:
        return ExtractionTier.TIER_1

    def get_cost_estimate(self, text_length: int) -> float:
        return text_length * _COST_PER_CHAR_USD

    def _build_entity_prompt(self, text: str) -> str:
        return _ENTITY_PROMPT.format(text=text)

    async def extract_entities(
        self, text: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if not text:
            return []
        prompt = self._build_entity_prompt(text)
        response = await self._call_api(prompt)
        return self._parse_entities(response)

    async def extract_relations(
        self, text: str, entities: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not text or not entities:
            return []
        entity_names = [e.get("name", "") for e in entities]
        prompt = _RELATION_PROMPT.format(text=text, entities=entity_names)
        response = await self._call_api(prompt)
        return self._parse_relations(response)

    async def extract_all(
        self, text: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not text:
            return {"entities": [], "relations": []}
        prompt = _ALL_PROMPT.format(text=text)
        response = await self._call_api(prompt)
        return self._parse_all(response)

    async def _real_api_call(self, prompt: str, **kwargs: Any) -> str:
        """Real Claude API call — replaced in tests with mock."""
        raise NotImplementedError("Real API call requires anthropic library")

    @staticmethod
    def _parse_entities(response: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(response)
            return data.get("entities", [])
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse entity response: %s", response[:200])
            return []

    @staticmethod
    def _parse_relations(response: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(response)
            return data.get("relations", [])
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse relation response: %s", response[:200])
            return []

    @staticmethod
    def _parse_all(response: str) -> dict[str, Any]:
        try:
            data = json.loads(response)
            return {
                "entities": data.get("entities", []),
                "relations": data.get("relations", []),
            }
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse response: %s", response[:200])
            return {"entities": [], "relations": []}
