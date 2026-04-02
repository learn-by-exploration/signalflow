# mkg/infrastructure/llm/regex_extractor.py
"""RegexExtractor — Tier 3 fallback NER/RE via regex patterns.

R-EX3: Pattern-based extraction when no LLM is available.
Lower quality but zero cost and zero latency.
Supports 5 languages: English, Chinese, Japanese, Korean, Hindi.
"""

import re
import unicodedata
from typing import Any

from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

# Known company names for pattern matching (English)
_KNOWN_COMPANIES = {
    "TSMC", "NVIDIA", "AMD", "Intel", "Apple", "Samsung", "Google",
    "Microsoft", "Amazon", "Meta", "Tesla", "Qualcomm", "Broadcom",
    "ASML", "ARM", "Reliance", "TCS", "Infosys", "HDFC", "SBI",
}

# Multilingual company names: {native_name: (canonical_english, entity_type)}
_MULTILINGUAL_COMPANIES: dict[str, tuple[str, str]] = {
    # Chinese (Simplified + Traditional)
    "台積電": ("TSMC", "Company"),
    "台积电": ("TSMC", "Company"),
    "英偉達": ("NVIDIA", "Company"),
    "英伟达": ("NVIDIA", "Company"),
    "三星電子": ("Samsung", "Company"),
    "三星电子": ("Samsung", "Company"),
    "蘋果": ("Apple", "Company"),
    "苹果": ("Apple", "Company"),
    "英特爾": ("Intel", "Company"),
    "英特尔": ("Intel", "Company"),
    "超微": ("AMD", "Company"),
    "華為": ("Huawei", "Company"),
    "华为": ("Huawei", "Company"),
    # Japanese
    "ソニー": ("Sony", "Company"),
    "トヨタ": ("Toyota", "Company"),
    "トヨタ自動車": ("Toyota", "Company"),
    "任天堂": ("Nintendo", "Company"),
    "ソフトバンク": ("SoftBank", "Company"),
    "東芝": ("Toshiba", "Company"),
    "パナソニック": ("Panasonic", "Company"),
    "日立": ("Hitachi", "Company"),
    # Korean
    "삼성전자": ("Samsung", "Company"),
    "삼성": ("Samsung", "Company"),
    "SK하이닉스": ("SK Hynix", "Company"),
    "LG전자": ("LG Electronics", "Company"),
    "현대": ("Hyundai", "Company"),
    "카카오": ("Kakao", "Company"),
    # Hindi (Devanagari)
    "रिलायंस": ("Reliance", "Company"),
    "रिलायंस इंडस्ट्रीज": ("Reliance", "Company"),
    "टीसीएस": ("TCS", "Company"),
    "इंफोसिस": ("Infosys", "Company"),
    "एचडीएफसी": ("HDFC", "Company"),
    "टाटा": ("Tata", "Company"),
    "विप्रो": ("Wipro", "Company"),
}

# Regex patterns
_MONEY_PATTERN = re.compile(r"\$[\d,.]+\s*(?:billion|million|trillion|B|M|T)?", re.IGNORECASE)
_PERCENT_PATTERN = re.compile(r"[\d.]+\s*%")
_ORG_SUFFIX_PATTERN = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+(?:Inc|Corp|Ltd|Co|Group|Holdings|Technologies|Semiconductor|Electronics)\.?))\b")

# Supply chain relation keywords
_SUPPLY_KEYWORDS = re.compile(r"(?:supplies?|provides?|delivers?|ships?)\s+(?:to|for)\s+", re.IGNORECASE)
_COMPETE_KEYWORDS = re.compile(r"(?:competes?|rivals?|against)\s+(?:with)?\s*", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Detect the primary language of text based on Unicode script analysis.

    Returns ISO 639-1 code: en, zh, ja, ko, hi.
    """
    if not text:
        return "en"

    # Count characters by script
    scripts: dict[str, int] = {
        "CJK": 0,
        "HIRAGANA": 0,
        "KATAKANA": 0,
        "HANGUL": 0,
        "DEVANAGARI": 0,
        "LATIN": 0,
    }

    for char in text:
        try:
            name = unicodedata.name(char, "")
        except ValueError:
            continue
        name_upper = name.upper()
        if "CJK" in name_upper:
            scripts["CJK"] += 1
        elif "HIRAGANA" in name_upper:
            scripts["HIRAGANA"] += 1
        elif "KATAKANA" in name_upper:
            scripts["KATAKANA"] += 1
        elif "HANGUL" in name_upper:
            scripts["HANGUL"] += 1
        elif "DEVANAGARI" in name_upper:
            scripts["DEVANAGARI"] += 1
        elif "LATIN" in name_upper:
            scripts["LATIN"] += 1

    # Japanese uses Hiragana/Katakana + CJK
    japanese = scripts["HIRAGANA"] + scripts["KATAKANA"]
    if japanese > 0 and japanese >= scripts["CJK"]:
        return "ja"
    if scripts["HANGUL"] > 0:
        return "ko"
    if scripts["DEVANAGARI"] > 0:
        return "hi"
    if scripts["CJK"] > 0:
        return "zh"
    return "en"


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

        # Known English companies
        for company in _KNOWN_COMPANIES:
            if company.lower() in text.lower() and company not in seen:
                entities.append({
                    "name": company,
                    "entity_type": "Company",
                    "confidence": 0.7,
                })
                seen.add(company)

        # Multilingual company names
        for native_name, (canonical, etype) in _MULTILINGUAL_COMPANIES.items():
            if native_name in text and canonical not in seen:
                entities.append({
                    "name": canonical,
                    "entity_type": etype,
                    "confidence": 0.65,
                    "metadata": {"source_name": native_name, "language": detect_language(native_name)},
                })
                seen.add(canonical)

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
