# mkg/tasks/analysis_tasks.py
"""Graph analysis and maintenance Celery tasks.

Weight decay, propagation triggers, accuracy calibration.
"""

import asyncio
import logging
import os
from typing import Any

from mkg.tasks.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="mkg.tasks.run_weight_decay")
def run_weight_decay(half_life_days: float = 90.0) -> dict[str, Any]:
    """Apply time-based weight decay to all edges.

    Dummy: logs the operation. Real version would call
    WeightAdjustmentService.batch_decay().
    """
    logger.info("DUMMY run_weight_decay: half_life=%.1f days", half_life_days)
    return {
        "status": "dummy",
        "half_life_days": half_life_days,
        "edges_decayed": 0,
        "message": "Dummy decay — would process all edges",
    }


@app.task(name="mkg.tasks.resolve_predictions")
def resolve_predictions() -> dict[str, Any]:
    """Check pending predictions against actual market outcomes.

    Dummy: logs the check. Real version would compare predictions
    to actual price movements and call AccuracyTracker.record_outcome().
    """
    logger.info("DUMMY resolve_predictions: would check pending predictions")
    return {
        "status": "dummy",
        "predictions_resolved": 0,
        "message": "Dummy resolution — no market data connected",
    }


@app.task(name="mkg.tasks.health_check")
def health_check() -> dict[str, Any]:
    """Pipeline health check task.

    Dummy: returns healthy. Real version would verify
    Neo4j, Redis, and LLM API connectivity.
    """
    logger.info("DUMMY health_check: all systems nominal (dummy)")
    return {
        "status": "healthy",
        "backend": "dummy",
        "neo4j": "not_connected",
        "redis": "not_connected",
        "llm": "not_connected",
    }


def run_weight_decay_real(half_life_days: float = 90.0, db_dir: str | None = None) -> dict[str, Any]:
    """Apply time-based weight decay to all edges using real graph storage.

    Args:
        half_life_days: Half-life for edge weight decay.
        db_dir: Directory for SQLite databases.

    Returns:
        Result dict with status and edges_decayed count.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    os.makedirs(db_dir, exist_ok=True)

    try:
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService

        storage = SQLiteGraphStorage(db_path=os.path.join(db_dir, "graph.db"))
        asyncio.get_event_loop().run_until_complete(storage.initialize())

        weight_svc = WeightAdjustmentService(storage)
        edges = asyncio.get_event_loop().run_until_complete(storage.find_edges())
        decayed = 0
        for edge in edges:
            edge_id = edge.get("id", "")
            if edge_id:
                asyncio.get_event_loop().run_until_complete(
                    weight_svc.apply_time_decay(edge_id, half_life_days=half_life_days)
                )
                decayed += 1

        asyncio.get_event_loop().run_until_complete(storage.close())
        return {"status": "completed", "edges_decayed": decayed}
    except Exception as exc:
        logger.error("run_weight_decay_real failed: %s", exc)
        return {"status": "error", "error": str(exc)}


def health_check_real(db_dir: str | None = None) -> dict[str, Any]:
    """Real health check that verifies SQLite connectivity.

    Args:
        db_dir: Directory for SQLite databases.

    Returns:
        Result dict with component statuses.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    os.makedirs(db_dir, exist_ok=True)

    try:
        from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        # Check SQLite graph storage
        storage = SQLiteGraphStorage(db_path=os.path.join(db_dir, "graph.db"))
        asyncio.get_event_loop().run_until_complete(storage.initialize())
        asyncio.get_event_loop().run_until_complete(storage.close())

        # Check audit logger
        audit = PersistentAuditLogger(db_path=os.path.join(db_dir, "audit.db"))
        entries = audit.get_entries()

        return {
            "status": "healthy",
            "sqlite": "connected",
            "audit_entries": len(entries),
        }
    except Exception as exc:
        logger.error("health_check_real failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}
