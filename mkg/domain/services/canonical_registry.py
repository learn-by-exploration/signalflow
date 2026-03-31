# mkg/domain/services/canonical_registry.py
"""CanonicalEntityRegistry — entity dedup via canonical name resolution.

R-KG7: Maps variant names/aliases to a canonical name so the same
real-world entity is not duplicated in the knowledge graph.
"""

import re
from typing import Any, Optional

from mkg.domain.entities.node import EntityType
from mkg.domain.interfaces.graph_storage import GraphStorage

# Legal suffixes to strip from company names
_LEGAL_SUFFIXES = re.compile(
    r"\s*\b(Corporation|Corp\.?|Incorporated|Inc\.?|Limited|Ltd\.?|"
    r"Co\.,?\s*Ltd\.?|Company|Co\.?|PLC|AG|SA|SE|NV|GmbH|LLC|LP|LLP)\s*\.?\s*$",
    re.IGNORECASE,
)

# Default well-known aliases
_DEFAULT_ALIASES: dict[str, str] = {
    "Taiwan Semiconductor Manufacturing Company": "TSMC",
    "Taiwan Semiconductor": "TSMC",
    "台積電": "TSMC",
    "TSM": "TSMC",
    "Alphabet": "ALPHABET",
    "Google": "ALPHABET",
    "GOOGL": "ALPHABET",
    "Meta Platforms": "META",
    "Facebook": "META",
    "Advanced Micro Devices": "AMD",
}


class CanonicalEntityRegistry:
    """Registry for canonical name resolution and entity dedup.

    Attributes:
        _aliases: Maps raw name (lowercased) -> canonical name.
        _reverse: Maps canonical name -> set of known aliases.
    """

    def __init__(self, load_defaults: bool = False) -> None:
        self._aliases: dict[str, str] = {}
        self._reverse: dict[str, set[str]] = {}
        if load_defaults:
            for alias, canonical in _DEFAULT_ALIASES.items():
                self.register_alias(alias, canonical)

    def normalize(self, name: str) -> str:
        """Normalize a name to canonical form.

        Strips whitespace, removes legal suffixes, uppercases.
        """
        name = name.strip()
        name = _LEGAL_SUFFIXES.sub("", name).strip()
        return name.upper()

    def register_alias(self, alias: str, canonical_name: str) -> None:
        """Register a name alias pointing to a canonical name."""
        key = alias.lower().strip()
        self._aliases[key] = canonical_name
        if canonical_name not in self._reverse:
            self._reverse[canonical_name] = set()
        self._reverse[canonical_name].add(alias)

    def resolve(self, name: str) -> str:
        """Resolve a name to its canonical form.

        First checks registered aliases, then falls back to normalization.
        """
        key = name.lower().strip()
        if key in self._aliases:
            return self._aliases[key]
        return self.normalize(name)

    def get_aliases(self, canonical_name: str) -> list[str]:
        """Get all known aliases for a canonical name."""
        return list(self._reverse.get(canonical_name, set()))

    async def merge_or_create(
        self,
        storage: GraphStorage,
        entity_type: EntityType,
        name: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Merge-or-create an entity using canonical name resolution.

        R-KG7: If an entity with the resolved canonical name exists,
        update it. Otherwise, create a new one.
        """
        canonical = self.resolve(name)
        props = dict(properties or {})
        props["name"] = name
        props["canonical_name"] = canonical

        return await storage.merge_entity(
            entity_type=entity_type.value,
            match_properties={"canonical_name": canonical},
            properties=props,
        )
