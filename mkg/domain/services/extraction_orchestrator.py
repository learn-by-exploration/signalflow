# mkg/domain/services/extraction_orchestrator.py
"""ExtractionOrchestrator — tier cascade with cost governance.

R-EX1–R-EX5: Cascades through extraction tiers (Claude → Regex),
respecting budget limits and routing failures to DLQ.
"""

import logging
import uuid
from typing import Any, Optional

from mkg.domain.interfaces.llm_extractor import LLMExtractor

logger = logging.getLogger(__name__)


class ExtractionOrchestrator:
    """Cascades through extraction tiers with cost governance.

    Tries extractors in order. Skips if budget insufficient.
    Falls back on failure. Routes exhausted failures to DLQ.
    """

    def __init__(
        self,
        extractors: list[LLMExtractor],
        cost_governance: Any,
        dlq: Any | None = None,
    ) -> None:
        self._extractors = extractors
        self._cost_governance = cost_governance
        self._dlq = dlq

    async def extract(
        self,
        text: str,
        article_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract entities and relations with tier cascading.

        Args:
            text: Article text to process.
            article_id: Optional article ID for tracking.
            context: Optional extraction context.

        Returns:
            Dict with entities, relations, tier_used, article_id.
        """
        if not text:
            return self._empty_result(article_id)

        article_id = article_id or str(uuid.uuid4())

        for extractor in self._extractors:
            tier = extractor.get_tier()
            tier_name = tier.value

            # Check budget before expensive tiers
            estimated_cost = extractor.get_cost_estimate(len(text))
            if estimated_cost > 0 and not self._cost_governance.can_afford(estimated_cost):
                logger.info(
                    "Skipping %s — budget insufficient (need $%.6f, have $%.2f)",
                    tier_name, estimated_cost, self._cost_governance.budget_remaining,
                )
                continue

            try:
                result = await extractor.extract_all(text, context)
                entities = result.get("entities", [])
                relations = result.get("relations", [])

                # Record cost for paid tiers
                if estimated_cost > 0:
                    self._cost_governance.record_cost(
                        estimated_cost, tier_name, article_id
                    )

                logger.info(
                    "Extraction via %s: %d entities, %d relations for article %s",
                    tier_name, len(entities), len(relations), article_id,
                )

                return {
                    "entities": entities,
                    "relations": relations,
                    "tier_used": tier_name,
                    "article_id": article_id,
                }

            except Exception as e:
                logger.warning(
                    "Extraction failed for %s: %s — cascading to next tier",
                    tier_name, e,
                )
                continue

        # All tiers failed
        logger.error(
            "All extraction tiers failed for article %s", article_id
        )
        if self._dlq:
            await self._dlq.add(
                item_id=article_id,
                reason="All extraction tiers failed",
                metadata={"text_length": len(text)},
            )

        return self._empty_result(article_id, tier_used="none")

    def _empty_result(
        self, article_id: str | None = None, tier_used: str = "none"
    ) -> dict[str, Any]:
        return {
            "entities": [],
            "relations": [],
            "tier_used": tier_used,
            "article_id": article_id or "",
        }
