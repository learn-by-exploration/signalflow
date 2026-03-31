# mkg/domain/services/seed_loader.py
"""SeedDataLoader — loads initial graph data from structured dicts.

Populates the knowledge graph with foundational entities and
relationships for the semiconductor supply chain and markets.
"""

import logging
from typing import Any

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)


class SeedDataLoader:
    """Loads seed data into a GraphStorage backend."""

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def load_entities(self, entities: list[dict[str, Any]]) -> int:
        """Load entities, returning count of successfully loaded."""
        count = 0
        for entity_data in entities:
            name = entity_data.get("name", "")
            if not name:
                logger.warning("Skipping entity with empty name: %s", entity_data)
                continue
            entity_id = entity_data.get("id")
            entity_type = entity_data.get("entity_type", "Company")
            canonical = entity_data.get("canonical_name", name)
            properties = {
                "name": name,
                "canonical_name": canonical,
            }
            # Copy extra properties
            for key in entity_data:
                if key not in ("id", "entity_type", "name", "canonical_name"):
                    properties[key] = entity_data[key]

            await self._storage.merge_entity(
                entity_type=entity_type,
                match_properties={"canonical_name": canonical},
                properties=properties,
            )
            # Ensure entity has the right ID if specified
            if entity_id:
                existing = await self._storage.find_entities(
                    filters={"canonical_name": canonical}
                )
                if existing and existing[0].get("id") != entity_id:
                    # For in-memory: re-create with explicit ID
                    await self._storage.delete_entity(existing[0]["id"])
                    await self._storage.create_entity(
                        entity_type=entity_type,
                        properties=properties,
                        entity_id=entity_id,
                    )
            count += 1
        return count

    async def load_edges(self, edges: list[dict[str, Any]]) -> int:
        """Load edges, returning count of successfully loaded."""
        count = 0
        for edge_data in edges:
            source_id = edge_data["source_id"]
            target_id = edge_data["target_id"]
            relation_type = edge_data["relation_type"]
            properties = {
                "weight": edge_data.get("weight", 0.5),
                "confidence": edge_data.get("confidence", 0.5),
            }
            for key in edge_data:
                if key not in ("source_id", "target_id", "relation_type", "weight", "confidence", "id"):
                    properties[key] = edge_data[key]
            await self._storage.create_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                properties=properties,
                edge_id=edge_data.get("id"),
            )
            count += 1
        return count

    async def load(self, seed_data: dict[str, Any]) -> dict[str, int]:
        """Load full seed data (entities + edges)."""
        entities_loaded = await self.load_entities(seed_data.get("entities", []))
        edges_loaded = await self.load_edges(seed_data.get("edges", []))
        return {
            "entities_loaded": entities_loaded,
            "edges_loaded": edges_loaded,
        }


def get_default_seed_data() -> dict[str, Any]:
    """Return default semiconductor supply chain seed data."""
    return {
        "entities": [
            {"id": "tsmc", "entity_type": "Company", "name": "TSMC", "canonical_name": "TSMC"},
            {"id": "nvidia", "entity_type": "Company", "name": "NVIDIA", "canonical_name": "NVIDIA"},
            {"id": "amd", "entity_type": "Company", "name": "AMD", "canonical_name": "AMD"},
            {"id": "intel", "entity_type": "Company", "name": "Intel", "canonical_name": "INTEL"},
            {"id": "apple", "entity_type": "Company", "name": "Apple", "canonical_name": "APPLE"},
            {"id": "samsung", "entity_type": "Company", "name": "Samsung", "canonical_name": "SAMSUNG"},
            {"id": "taiwan", "entity_type": "Country", "name": "Taiwan", "canonical_name": "TAIWAN"},
            {"id": "usa", "entity_type": "Country", "name": "United States", "canonical_name": "USA"},
            {"id": "semiconductors", "entity_type": "Sector", "name": "Semiconductors", "canonical_name": "SEMICONDUCTORS"},
        ],
        "edges": [
            {"source_id": "tsmc", "target_id": "nvidia", "relation_type": "SUPPLIES_TO", "weight": 0.90, "confidence": 0.95},
            {"source_id": "tsmc", "target_id": "apple", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.95},
            {"source_id": "tsmc", "target_id": "amd", "relation_type": "SUPPLIES_TO", "weight": 0.80, "confidence": 0.90},
            {"source_id": "nvidia", "target_id": "amd", "relation_type": "COMPETES_WITH", "weight": 0.75, "confidence": 0.90},
            {"source_id": "tsmc", "target_id": "taiwan", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
            {"source_id": "intel", "target_id": "usa", "relation_type": "OPERATES_IN", "weight": 0.90, "confidence": 1.0},
            {"source_id": "tsmc", "target_id": "semiconductors", "relation_type": "OPERATES_IN", "weight": 0.95, "confidence": 1.0},
        ],
    }
