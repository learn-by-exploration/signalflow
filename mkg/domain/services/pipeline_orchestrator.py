# mkg/domain/services/pipeline_orchestrator.py
"""PipelineOrchestrator — end-to-end article processing pipeline.

Wires together: dedup → extract → verify → mutate → propagate → chain → alert → impact.
This is the central coordinator that makes MKG "work."
"""

import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the full MKG article processing pipeline.

    Flow:
    1. Deduplication check
    2. Entity/relation extraction (tiered)
    3. Hallucination verification
    4. Graph mutation (entities + edges)
    5. Impact propagation (optional)
    6. Causal chain building
    7. Alert generation
    8. Impact table construction
    """

    def __init__(
        self,
        graph_storage: Any,
        extraction_orchestrator: Any,
        hallucination_verifier: Any,
        graph_mutation: Any,
        propagation_engine: Any,
        causal_chain_builder: Any,
        alert_system: Any,
        impact_table_builder: Any,
        article_dedup: Any | None = None,
    ) -> None:
        self._storage = graph_storage
        self._extraction = extraction_orchestrator
        self._verifier = hallucination_verifier
        self._mutation = graph_mutation
        self._propagation = propagation_engine
        self._chain_builder = causal_chain_builder
        self._alerts = alert_system
        self._impact_table = impact_table_builder
        self._dedup = article_dedup
        self._processed_urls: set[str] = set()

    async def process_article(
        self,
        title: str,
        content: str,
        source: str = "unknown",
        url: str | None = None,
        trigger_propagation: bool = False,
        trigger_entity_name: str | None = None,
        trigger_event: str | None = None,
    ) -> dict[str, Any]:
        """Process a single article through the full MKG pipeline.

        Args:
            title: Article title.
            content: Article text content.
            source: Source name (reuters, rss, etc.).
            url: Article URL.
            trigger_propagation: Whether to run impact propagation.
            trigger_entity_name: Entity name that triggered the event.
            trigger_event: Description of the triggering event.

        Returns:
            Processing result dict with status, entities, relations, impacts, etc.
        """
        start_time = time.time()
        article_id = str(uuid.uuid4())

        # Validate input
        if not content:
            return self._result(article_id, "failed", start_time, error="Empty content")

        # Step 1: Deduplication
        if url and url in self._processed_urls:
            return self._result(article_id, "duplicate", start_time)

        if self._dedup and url:
            is_dup = await self._check_dedup(content, url)
            if is_dup:
                return self._result(article_id, "duplicate", start_time)

        # Step 2: Extract entities and relations
        extraction = await self._extraction.extract(
            content, article_id=article_id
        )
        tier_used = extraction.get("tier_used", "none")
        raw_entities = extraction.get("entities", [])
        raw_relations = extraction.get("relations", [])

        if not raw_entities:
            logger.info("No entities extracted for article %s", article_id)
            if url:
                self._processed_urls.add(url)
            return self._result(
                article_id, "completed", start_time,
                tier_used=tier_used,
                entities_created=0, relations_created=0,
            )

        # Step 3: Hallucination verification
        verified = self._verifier.verify_result(
            {"entities": raw_entities, "relations": raw_relations},
            content,
        )
        verified_entities = verified.get("verified_entities", raw_entities)
        verified_relations = verified.get("verified_relations", raw_relations)

        # Step 4: Graph mutation
        entity_result = await self._mutation.apply_entities(
            verified_entities, source=source
        )
        relation_result = await self._mutation.apply_relations(
            verified_relations, source=source
        )

        entities_created = entity_result.get("created", 0) + entity_result.get("updated", 0)
        relations_created = relation_result.get("created", 0)

        # Mark URL as processed
        if url:
            self._processed_urls.add(url)

        # Step 5-8: Propagation (optional)
        impacts: list[dict] = []
        causal_chains: list[dict] = []
        alerts: list[dict] = []
        impact_table: dict = {}
        propagation_ran = False

        if trigger_propagation and trigger_entity_name:
            propagation_ran = True
            trigger_entity_id = await self._find_entity_id(trigger_entity_name)

            if trigger_entity_id:
                # Step 5: Propagation
                impacts = await self._propagation.propagate(
                    trigger_entity_id=trigger_entity_id,
                    impact_score=1.0,
                    max_depth=4,
                )

                # Step 6: Causal chains
                if impacts:
                    causal_chains = await self._chain_builder.build_chains(
                        trigger_entity_id=trigger_entity_id,
                        trigger_event=trigger_event or "market event",
                        propagation_results=impacts,
                    )

                # Step 7: Alerts
                if causal_chains:
                    alerts = self._alerts.generate_alerts(causal_chains)

                # Step 8: Impact table
                if impacts:
                    impact_table = await self._impact_table.build(
                        impacts, trigger_name=trigger_entity_name
                    )

        elapsed = time.time() - start_time
        logger.info(
            "Pipeline completed for article %s: %d entities, %d relations, "
            "%d impacts, %.2fs",
            article_id, entities_created, relations_created,
            len(impacts), elapsed,
        )

        return {
            "article_id": article_id,
            "status": "completed",
            "tier_used": tier_used,
            "entities_created": entities_created,
            "relations_created": relations_created,
            "propagation_ran": propagation_ran,
            "impacts": impacts,
            "causal_chains": causal_chains,
            "alerts": alerts,
            "impact_table": impact_table,
            "elapsed_seconds": elapsed,
        }

    async def _find_entity_id(self, name: str) -> str | None:
        """Find entity ID by name in the graph."""
        results = await self._storage.search(name, limit=1)
        if results:
            return results[0]["id"]
        # Try find_entities as fallback
        entities = await self._storage.find_entities(
            filters={"name": name}
        )
        if entities:
            return entities[0]["id"]
        logger.warning("Trigger entity '%s' not found in graph", name)
        return None

    async def _check_dedup(self, content: str, url: str) -> bool:
        """Check if article is a duplicate."""
        try:
            is_dup = self._dedup.is_duplicate_content(content)
            if not is_dup:
                self._dedup.mark_seen_content(content)
            return is_dup
        except Exception:
            return False

    def _result(
        self,
        article_id: str,
        status: str,
        start_time: float,
        tier_used: str = "none",
        error: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "article_id": article_id,
            "status": status,
            "tier_used": tier_used,
            "error": error,
            "elapsed_seconds": time.time() - start_time,
            "entities_created": 0,
            "relations_created": 0,
            "propagation_ran": False,
            "impacts": [],
            "causal_chains": [],
            "alerts": [],
            "impact_table": {},
            **kwargs,
        }
