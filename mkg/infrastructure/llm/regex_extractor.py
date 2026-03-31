# mkg/infrastructure/llm/regex_extractor.py
"""RegexExtractor — Tier 3 fallback NER/RE via regex patterns.

R-EX3: Pattern-based extraction when no LLM is available.
Lower quality but zero cost and zero latency.
"""

import re
from typing import Any

from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

# Known company names for pattern matching
_KNOWN_COMPANIES = {
    "TSMC", "NVIDIA", "AMD", "Intel", "Apple", "Samsung", "Google",
    "Microsoft", "Amazon", "Meta", "Tesla", "Qualcomm", "Broadcom",
    "ASML", "ARM", "Reliance", "TCS", "Infosys", "HDFC", "SBI",
}

# Regex patterns
_MONEY_PATTERN = re.compile(r"\$[\d,.]+\s*(?:billion|million|trillion|B|M|T)?", re.IGNORECASE)
_PERCENT_PATTERN = re.compile(r"[\d.]+\s*%")
_ORG_SUFFIX_PATTERN = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+(?:Inc|Corp|Ltd|Co|Group|Holdings|Technologies|Semiconductor|Electronics)\.?))\b")

# Supply chain relation keywords
_SUPPLY_KEYWORDS = re.compile(r"(?:supplies?|provides?|delivers?|ships?)\s+(?:to|for)\s+", re.IGNORECASE)
_COMPETE_KEYWORDS = re.compile(r"(?:competes?|rivals?|against)\s+(?:with)?\s*", re.IGNORECASE)


class RegexExtractor(LLMExtractor):
    """Tier 3 extraction using regex patterns."""

    def get_tier(self) -> ExtractionTier:
        return ExtractionTier.TIER_3

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0

    async def extract_entities(
        self, text: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if not text:
            return []
        entities = []
        seen: set[str] = set()

        # Known companies
        for company in _KNOWN_COMPANIES:
            if company.lower() in text.lower() and company not in seen:
                entities.append({
                    "name": company,
                    "entity_type": "Company",
                    "confidence": 0.7,
                })
                seen.add(company)

        # Org suffixes (Inc, Corp, Ltd, etc.)
        for match in _ORG_SUFFIX_PATTERN.finditer(text):
            name = match.group(1).strip()
            if name not in seen:
                entities.append({
                    "name": name,
                    "entity_type": "Company",
                    "confidence": 0.5,
                })
                seen.add(name)

        # Money amounts
        for match in _MONEY_PATTERN.finditer(text):
            entities.append({
                "name": match.group(),
                "entity_type": "Event",
                "confidence": 0.6,
                "metadata": {"type": "monetary_value"},
            })

        return entities

    async def extract_relations(
        self, text: str, entities: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not text or not entities:
            return []
        relations = []
        entity_names = [e["name"] for e in entities]

        # Simple pattern: "A supplies to B"
        for src in entity_names:
            for tgt in entity_names:
                if src == tgt:
                    continue
                if _SUPPLY_KEYWORDS.search(text) and src in text and tgt in text:
                    src_pos = text.find(src)
                    tgt_pos = text.find(tgt)
                    if src_pos >= 0 and tgt_pos >= 0 and src_pos < tgt_pos:
                        relations.append({
                            "source": src, "target": tgt,
                            "relation_type": "SUPPLIES_TO",
                            "weight": 0.5, "confidence": 0.4,
                        })

        return relations

    async def extract_all(
        self, text: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        entities = await self.extract_entities(text, context)
        relations = await self.extract_relations(text, entities, context)
        return {"entities": entities, "relations": relations}
