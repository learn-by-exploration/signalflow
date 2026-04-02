# mkg/domain/services/mirofish_client.py
"""MiroFish sidecar client — REST bridge between MKG and MiroFish.

D1: Coordinates with MiroFish for simulation, calibration, and
propagation result delivery.
"""

from typing import Any, Optional


class MiroFishClient:
    """Client for communicating with a MiroFish sidecar service."""

    def __init__(
        self,
        base_url: str = "http://localhost:9000",
        timeout_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def format_propagation(
        self,
        trigger_entity_id: str,
        trigger_event: str,
        impact_score: float,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Format propagation results for MiroFish consumption.

        Args:
            trigger_entity_id: The entity where the event started.
            trigger_event: Human-readable event description.
            impact_score: Initial impact magnitude.
            results: PropagationEngine output.

        Returns:
            Structured payload ready for MiroFish REST API.
        """
        return {
            "trigger": {
                "entity_id": trigger_entity_id,
                "event": trigger_event,
                "impact_score": impact_score,
            },
            "affected": [
                {
                    "entity_id": r["entity_id"],
                    "impact": r.get("impact", 0.0),
                    "depth": r.get("depth", 0),
                    "direction": r.get("direction", "positive"),
                    "path": r.get("path", []),
                }
                for r in results
            ],
            "metadata": {
                "source": "mkg",
                "version": "1.0",
                "entity_count": len(results),
            },
        }

    async def submit_propagation(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit propagation results to MiroFish (stub).

        In production, this would POST to {base_url}/api/v1/propagation.
        """
        # Stub: return acceptance response
        return {
            "status": "accepted",
            "payload_size": len(payload.get("affected", [])),
        }

    async def get_status(self) -> dict[str, Any]:
        """Check MiroFish sidecar health (stub)."""
        return {
            "status": "unavailable",
            "base_url": self._base_url,
            "message": "MiroFish sidecar not connected (stub mode)",
        }

    async def simulate(
        self,
        scenario: dict[str, Any],
    ) -> dict[str, Any]:
        """Request MiroFish to run a simulation (stub)."""
        return {
            "status": "accepted",
            "simulation_id": "stub-sim-001",
            "scenario": scenario,
        }
