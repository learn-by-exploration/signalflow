# mkg/domain/services/alert_system.py
"""AlertSystem — generates alerts from causal chain analysis.

R-AL1 through R-AL5: Threshold-based alerting with severity levels,
deduplication, and filtering.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional


# Severity order for filtering
_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


class AlertSystem:
    """Generates alerts from causal chain results.

    Uses configurable impact thresholds to classify severity.
    Deduplicates by (trigger, affected_entity, event) to prevent spam.
    """

    def __init__(
        self,
        impact_thresholds: Optional[dict[str, float]] = None,
    ) -> None:
        self._thresholds = impact_thresholds or {
            "critical": 0.8,
            "high": 0.6,
            "medium": 0.3,
        }
        # Validate thresholds are in [0, 1] and properly ordered
        for key in ("critical", "high", "medium"):
            val = self._thresholds.get(key)
            if val is not None and not 0.0 <= val <= 1.0:
                raise ValueError(f"Threshold '{key}' must be in [0, 1], got {val}")
        self._seen: set[str] = set()
        self._history: list[dict[str, Any]] = []

    def _classify_severity(self, impact_score: float) -> str:
        """Map impact score to severity level."""
        if impact_score >= self._thresholds.get("critical", 0.8):
            return "critical"
        if impact_score >= self._thresholds.get("high", 0.6):
            return "high"
        if impact_score >= self._thresholds.get("medium", 0.3):
            return "medium"
        return "low"

    def _dedup_key(self, chain: dict[str, Any]) -> str:
        """Generate dedup key from chain."""
        return f"{chain.get('trigger')}:{chain.get('affected_entity')}:{chain.get('trigger_event')}"

    def generate_alert(
        self,
        chain: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Generate an alert from a causal chain, with dedup.

        Args:
            chain: Causal chain dict from CausalChainBuilder.

        Returns:
            Alert dict or None if deduplicated.
        """
        key = self._dedup_key(chain)
        if key in self._seen:
            return None
        self._seen.add(key)

        severity = self._classify_severity(chain["impact_score"])
        alert = {
            "id": str(uuid.uuid4()),
            "severity": severity,
            "title": f"{severity.upper()}: {chain.get('trigger_name', 'Unknown')} → {chain.get('affected_name', 'Unknown')}",
            "message": chain.get("narrative", ""),
            "impact_score": chain["impact_score"],
            "source_chain": chain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(alert)
        return alert

    def generate_alerts(
        self,
        chains: list[dict[str, Any]],
        min_severity: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Generate alerts for multiple chains with optional severity filter.

        Args:
            chains: List of causal chain dicts.
            min_severity: Minimum severity to include (critical, high, medium, low).

        Returns:
            List of generated alerts (deduped and filtered).
        """
        min_level = _SEVERITY_ORDER.get(min_severity or "low", 1)
        alerts: list[dict[str, Any]] = []

        for chain in chains:
            alert = self.generate_alert(chain)
            if alert is None:
                continue
            if _SEVERITY_ORDER.get(alert["severity"], 0) >= min_level:
                alerts.append(alert)

        return alerts

    def get_recent_alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent alerts.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            Most recent alerts, newest first.
        """
        return list(reversed(self._history[-limit:]))

    def clear_dedup(self) -> None:
        """Clear the dedup cache to allow re-alerting."""
        self._seen.clear()
