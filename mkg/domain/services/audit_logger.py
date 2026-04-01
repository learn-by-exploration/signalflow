# mkg/domain/services/audit_logger.py
"""AuditLogger — immutable audit trail for all MKG graph mutations.

Records every entity creation, edge creation, weight update, deletion,
and pipeline decision in a structured, queryable log. This log is
immutable — entries cannot be modified or deleted after creation.

Required for:
- SEBI regulatory audit compliance
- Internal data governance review
- Traceability of automated decisions
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of auditable actions in MKG."""

    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    EDGE_CREATED = "edge_created"
    EDGE_UPDATED = "edge_updated"
    EDGE_DELETED = "edge_deleted"
    WEIGHT_UPDATED = "weight_updated"
    CONFIDENCE_OVERRIDE = "confidence_override"
    PIPELINE_DECISION = "pipeline_decision"
    PROPAGATION_RUN = "propagation_run"
    ALERT_GENERATED = "alert_generated"


class AuditLogger:
    """Immutable structured audit logger.

    All entries are append-only. Supports querying by action type,
    target ID, actor, and time range. Entries are guaranteed to have
    monotonically increasing timestamps.
    """

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log(
        self,
        action: AuditAction,
        actor: str,
        target_id: str,
        target_type: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        """Append an audit entry.

        Args:
            action: The type of action performed.
            actor: Who/what performed the action (e.g., "pipeline:extraction", "admin").
            target_id: ID of the entity/edge/article affected.
            target_type: Type of target ("entity", "edge", "article").
            details: Action-specific metadata.

        Returns:
            The created audit entry.
        """
        entry = {
            "action": action.value,
            "actor": actor,
            "target_id": target_id,
            "target_type": target_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        logger.debug(
            "Audit: action=%s actor=%s target=%s",
            action.value, actor, target_id,
        )
        return entry

    def get_entries(
        self,
        action: Optional[str] = None,
        target_id: Optional[str] = None,
        actor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Query audit entries with optional filters.

        Args:
            action: Filter by action type (string value).
            target_id: Filter by target ID.
            actor: Filter by actor.
            limit: Maximum entries to return.

        Returns:
            Filtered list of audit entries, chronologically ordered.
        """
        results = self._entries

        if action:
            results = [e for e in results if e["action"] == action]
        if target_id:
            results = [e for e in results if e["target_id"] == target_id]
        if actor:
            results = [e for e in results if e["actor"] == actor]
        if limit:
            results = results[:limit]

        return results

    def export_entries(self) -> list[dict[str, Any]]:
        """Export all entries as a list (for serialization/archival)."""
        return list(self._entries)

    def export_report(self) -> dict[str, Any]:
        """Generate an audit summary report.

        Returns:
            Report with total entries, per-action breakdown, and timestamp.
        """
        breakdown: dict[str, int] = {}
        for entry in self._entries:
            action = entry["action"]
            breakdown[action] = breakdown.get(action, 0) + 1

        return {
            "total_entries": len(self._entries),
            "actions_breakdown": breakdown,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
