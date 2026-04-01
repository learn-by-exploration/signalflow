# mkg/infrastructure/llm/claude_extractor.py
"""ClaudeExtractor — Tier 1 cloud NER/RE extraction via Claude API.

R-EX1: Highest-quality extraction using claude-sonnet-4-20250514.
Uses httpx for HTTP calls to the Anthropic Messages API.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import httpx

from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

logger = logging.getLogger(__name__)

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"
_MAX_TOKENS = 4096
_TIMEOUT_SECONDS = 60
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 529}

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
        self._http_post: Callable = self._default_http_post
        self.last_usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

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

    async def _real_api_call(self, prompt: str, max_retries: int = 3, **kwargs: Any) -> str:
        """Call the Anthropic Messages API via httpx with retry logic.

        Args:
            prompt: The user message to send to Claude.
            max_retries: Max retry attempts for retryable errors (429, 5xx).

        Returns:
            The text content from Claude's response.

        Raises:
            Exception: On non-retryable HTTP errors or after retries exhausted.
        """
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }
        body = {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = await self._http_post(
                    _API_URL, headers=headers, json=body, timeout=_TIMEOUT_SECONDS
                )

                if response.status_code == 200:
                    data = response.json()
                    # Track token usage
                    usage = data.get("usage", {})
                    self.last_usage = {
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    }
                    # Extract text content
                    content = data.get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", "")
                    return ""

                # Non-retryable client errors (400, 401, 403, 404)
                if response.status_code < 500 and response.status_code not in _RETRYABLE_STATUS_CODES:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except Exception:
                        pass
                    error_type = error_data.get("error", {}).get("type", f"http_{response.status_code}")
                    raise Exception(
                        f"Claude API error {response.status_code}: {error_type}"
                    )

                # Retryable errors — will retry
                last_error = Exception(
                    f"Claude API error {response.status_code}: "
                    + response.text[:200]
                )
                if attempt < max_retries:
                    wait = min(2 ** attempt * 0.5, 10.0)
                    logger.warning(
                        "Claude API %d, retrying in %.1fs (attempt %d/%d)",
                        response.status_code, wait, attempt + 1, max_retries,
                    )
                    await asyncio.sleep(wait)

            except Exception as e:
                if "Claude API error" in str(e):
                    raise  # Re-raise our own errors (non-retryable)
                last_error = e
                if attempt < max_retries:
                    wait = min(2 ** attempt * 0.5, 10.0)
                    logger.warning(
                        "Claude API call failed: %s, retrying in %.1fs", e, wait
                    )
                    await asyncio.sleep(wait)

        raise last_error or Exception("Claude API call failed after retries")

    @staticmethod
    async def _default_http_post(url: str, **kwargs: Any) -> Any:
        """Default HTTP POST using httpx.AsyncClient."""
        timeout = kwargs.pop("timeout", _TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(url, **kwargs)

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
