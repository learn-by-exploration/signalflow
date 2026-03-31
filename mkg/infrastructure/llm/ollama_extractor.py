# mkg/infrastructure/llm/ollama_extractor.py
"""OllamaExtractor — Tier 2 local NER/RE extraction via Ollama.

R-EX2: Local fallback when Claude budget is exhausted.
"""

import json
import logging
from typing import Any, Callable

from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

logger = logging.getLogger(__name__)

_ENTITY_PROMPT = """Extract named entities from this text. Types: Company, Product, Facility, Person, Country, Regulation, Sector, Event.
Text: "{text}"
Respond with JSON only: {{"entities": [{{"name": "...", "entity_type": "...", "confidence": 0.0-1.0}}]}}"""


class OllamaExtractor(LLMExtractor):
    """Tier 2 extraction via local Ollama instance."""

    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434") -> None:
        self._model = model
        self._base_url = base_url
        self._call_api: Callable = self._real_api_call

    def get_tier(self) -> ExtractionTier:
        return ExtractionTier.TIER_2

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0  # Local — no API cost

    async def extract_entities(self, text: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not text:
            return []
        prompt = _ENTITY_PROMPT.format(text=text)
        response = await self._call_api(prompt)
        try:
            return json.loads(response).get("entities", [])
        except (json.JSONDecodeError, KeyError):
            return []

    async def extract_relations(self, text: str, entities: list[dict[str, Any]], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not text or not entities:
            return []
        prompt = f'Extract relations from: "{text}" between entities: {[e["name"] for e in entities]}. Respond with JSON: {{"relations": [...]}}'
        response = await self._call_api(prompt)
        try:
            return json.loads(response).get("relations", [])
        except (json.JSONDecodeError, KeyError):
            return []

    async def extract_all(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if not text:
            return {"entities": [], "relations": []}
        entities = await self.extract_entities(text, context)
        relations = await self.extract_relations(text, entities, context) if entities else []
        return {"entities": entities, "relations": relations}

    async def _real_api_call(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError("Real Ollama call requires httpx")
