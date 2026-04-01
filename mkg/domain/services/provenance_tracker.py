# mkg/domain/services/provenance_tracker.py
"""ProvenanceTracker — full pipeline traceability for compliance.

Records every pipeline step, entity origin, edge origin, and propagation
event so that any output can be traced back to its source article(s).

SEBI IA Regulations 2013 require disclosure of data sources used in
generating investment research. This service provides that traceability.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ProvenanceTracker:
    """Tracks provenance (lineage) of all MKG pipeline outputs.

    Three tracking dimensions:
    1. Pipeline steps: article → dedup → extract → verify → mutate → propagate
    2. Entity origins: entity_id → article_id(s) + extraction tier + confidence
    3. Edge origins: edge_id → article_id + relation metadata
    4. Propagation events: trigger → impacts → chains

    All records are timestamped for audit trail purposes.
    """

    def __init__(self) -> None:
        # Pipeline step records keyed by article_id
        self._steps: dict[str, list[dict[str, Any]]] = {}
        # Entity origin records keyed by entity_id (list: multiple articles can contribute)
        self._entity_origins: dict[str, list[dict[str, Any]]] = {}
        # Edge origin records keyed by edge_id
        self._edge_origins: dict[str, dict[str, Any]] = {}
        # Propagation event records keyed by trigger_entity_id
        self._propagations: dict[str, list[dict[str, Any]]] = {}

    def record_step(
        self,
        article_id: str,
        step: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:
        """Record a pipeline processing step.

        Args:
            article_id: The article being processed.
            step: Step name (dedup, extraction, verification, mutation, propagation).
            inputs: Step input parameters.
            outputs: Step output results.
        """
        record = {
            "article_id": article_id,
            "step": step,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._steps.setdefault(article_id, []).append(record)
        logger.debug("Provenance: article=%s step=%s", article_id, step)

    def get_records(self, article_id: str) -> list[dict[str, Any]]:
        """Get all pipeline step records for an article."""
        return list(self._steps.get(article_id, []))

    def record_entity_origin(
        self,
        entity_id: str,
        entity_name: str,
        article_id: str,
        extraction_tier: str,
        confidence: float,
    ) -> None:
        """Record the origin of an entity — which article created it.

        Multiple articles can contribute to the same entity (e.g., updates).

        Args:
            entity_id: The entity's unique identifier.
            entity_name: Display name of the entity.
            article_id: The article that produced this entity.
            extraction_tier: Which extraction tier was used.
            confidence: Extraction confidence score.
        """
        record = {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "article_id": article_id,
            "extraction_tier": extraction_tier,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._entity_origins.setdefault(entity_id, []).append(record)

    def get_entity_origin(self, entity_id: str) -> Optional[dict[str, Any]]:
        """Get the first (original) origin record for an entity."""
        origins = self._entity_origins.get(entity_id, [])
        return origins[0] if origins else None

    def get_entity_articles(self, entity_id: str) -> list[dict[str, Any]]:
        """Get all articles that contributed to an entity."""
        return list(self._entity_origins.get(entity_id, []))

    def record_edge_origin(
        self,
        edge_id: str,
        source_entity: str,
        target_entity: str,
        relation_type: str,
        article_id: str,
        confidence: float,
    ) -> None:
        """Record the origin of an edge — which article created it.

        Args:
            edge_id: The edge's unique identifier.
            source_entity: Source entity name.
            target_entity: Target entity name.
            relation_type: Relationship type.
            article_id: The article that produced this edge.
            confidence: Extraction confidence.
        """
        self._edge_origins[edge_id] = {
            "edge_id": edge_id,
            "source_entity": source_entity,
            "target_entity": target_entity,
            "relation_type": relation_type,
            "article_id": article_id,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_edge_origin(self, edge_id: str) -> Optional[dict[str, Any]]:
        """Get the origin record for an edge."""
        return self._edge_origins.get(edge_id)

    def record_propagation(
        self,
        trigger_entity_id: str,
        trigger_event: str,
        article_id: str,
        impacts_count: int,
        max_depth: int,
        chains_count: int,
    ) -> None:
        """Record a propagation event for traceability.

        Args:
            trigger_entity_id: The entity that triggered propagation.
            trigger_event: Description of the trigger event.
            article_id: Source article that triggered propagation.
            impacts_count: Number of impacted entities found.
            max_depth: Maximum depth reached in BFS.
            chains_count: Number of causal chains built.
        """
        record = {
            "trigger_entity_id": trigger_entity_id,
            "trigger_event": trigger_event,
            "article_id": article_id,
            "impacts_count": impacts_count,
            "max_depth": max_depth,
            "chains_count": chains_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._propagations.setdefault(trigger_entity_id, []).append(record)

    def get_propagation_records(
        self, trigger_entity_id: str
    ) -> list[dict[str, Any]]:
        """Get all propagation events for a trigger entity."""
        return list(self._propagations.get(trigger_entity_id, []))

    def get_article_lineage(self, article_id: str) -> dict[str, Any]:
        """Get the full lineage for an article — all steps, entities, edges.

        Returns a structured report showing what the article produced.
        """
        steps = self.get_records(article_id)
        entities = [
            origin
            for origins in self._entity_origins.values()
            for origin in origins
            if origin["article_id"] == article_id
        ]
        edges = [
            origin
            for origin in self._edge_origins.values()
            if origin["article_id"] == article_id
        ]
        return {
            "article_id": article_id,
            "steps": steps,
            "entities_created": entities,
            "edges_created": edges,
        }

    def get_all_data_sources(self) -> list[dict[str, Any]]:
        """List all unique data sources used across all provenance records.

        Returns list of {source, url, article_id} dicts.
        """
        sources: list[dict[str, Any]] = []
        seen: set[str] = set()
        for article_id, steps in self._steps.items():
            for step in steps:
                inputs = step.get("inputs", {})
                source = inputs.get("source")
                url = inputs.get("url")
                key = f"{source}:{url}:{article_id}"
                if source and key not in seen:
                    seen.add(key)
                    sources.append({
                        "source": source,
                        "url": url,
                        "article_id": article_id,
                    })
        return sources

    def get_summary(self) -> dict[str, Any]:
        """Compliance summary report.

        Returns aggregate stats for audit purposes.
        """
        total_articles = len(self._steps)
        total_steps = sum(len(steps) for steps in self._steps.values())
        total_entities = len(self._entity_origins)
        total_edges = len(self._edge_origins)
        total_propagations = sum(
            len(props) for props in self._propagations.values()
        )

        return {
            "total_articles_processed": total_articles,
            "total_steps_recorded": total_steps,
            "total_entities_tracked": total_entities,
            "total_edges_tracked": total_edges,
            "total_propagations": total_propagations,
        }
