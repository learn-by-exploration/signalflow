# mkg/domain/services/entity_resolver.py
"""EntityResolver — cross-graph entity resolution.

D2: Maps MKG entity IDs to external system identifiers
(Bloomberg, Reuters, Yahoo Finance, etc.) and provides reverse lookup.
"""

from typing import Any, Optional


class EntityResolver:
    """Maps MKG entities to external system identifiers."""

    def __init__(self) -> None:
        # {mkg_entity_id: {external_system: external_id}}
        self._forward: dict[str, dict[str, str]] = {}
        # {(external_system, external_id): mkg_entity_id}
        self._reverse: dict[tuple[str, str], str] = {}

    def register(
        self,
        mkg_entity_id: str,
        external_system: str,
        external_id: str,
    ) -> None:
        """Register a mapping between MKG entity and external identifier.

        Args:
            mkg_entity_id: MKG entity ID.
            external_system: External system name (e.g., 'bloomberg', 'reuters').
            external_id: External identifier (e.g., 'TSM:US', '2330.TW').
        """
        if mkg_entity_id not in self._forward:
            self._forward[mkg_entity_id] = {}
        self._forward[mkg_entity_id][external_system] = external_id
        self._reverse[(external_system, external_id)] = mkg_entity_id

    def resolve(
        self,
        mkg_entity_id: str,
        external_system: str,
    ) -> Optional[str]:
        """Resolve MKG entity to external identifier.

        Returns None if no mapping exists.
        """
        return self._forward.get(mkg_entity_id, {}).get(external_system)

    def reverse_lookup(
        self,
        external_system: str,
        external_id: str,
    ) -> Optional[str]:
        """Look up MKG entity ID from external identifier.

        Returns None if no mapping exists.
        """
        return self._reverse.get((external_system, external_id))

    def list_mappings(self, mkg_entity_id: str) -> list[dict[str, str]]:
        """List all external mappings for an MKG entity."""
        mappings = self._forward.get(mkg_entity_id, {})
        return [
            {"system": system, "external_id": ext_id}
            for system, ext_id in mappings.items()
        ]
