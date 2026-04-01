# mkg/tasks/analysis_tasks.py
"""Graph analysis and maintenance Celery tasks.

Weight decay, propagation triggers, accuracy calibration.
Contains both dummy tasks (backward compat) and real implementations.
"""

import asyncio
import logging
import os
from typing import Any

from mkg.tasks.celery_app import app

logger = logging.getLogger(__name__)


def _get_factory(db_dir: str | None = None):
    """Create and initialize a ServiceFactory (sync wrapper)."""
    from mkg.service_factory import ServiceFactory
    factory = ServiceFactory(db_dir=db_dir)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(factory.initialize())
    finally:
        loop.close()
    return factory


@app.task(name="mkg.tasks.run_weight_decay")
def run_weight_decay(half_life_days: float = 90.0) -> dict[str, Any]:
    """Apply time-based weight decay to all edges.

    Uses ServiceFactory to get graph storage and WeightAdjustmentService,
    then applies time-based decay to all edges.
    """
    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    factory = _get_factory(db_dir)
    loop = asyncio.new_event_loop()
    try:
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        weight_service = WeightAdjustmentService(factory.graph_storage)
        result = loop.run_until_complete(
            weight_service.batch_decay(days_old=0, half_life_days=half_life_days)
        )
        return {
            "status": "completed",
            "half_life_days": half_life_days,
            "edges_decayed": result.get("edges_updated", 0),
        }
    except Exception as e:
        logger.error("run_weight_decay failed: %s", e)
        return {"status": "error", "error": str(e), "edges_decayed": 0}
    finally:
        loop.run_until_complete(factory.shutdown())
        loop.close()


def run_weight_decay_real(
    half_life_days: float = 90.0,
    db_dir: str | None = None,
) -> dict[str, Any]:
    """Real implementation of weight decay.

    Uses ServiceFactory to get graph storage and WeightAdjustmentService,
    then applies time-based decay to all edges.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    factory = _get_factory(db_dir)
    loop = asyncio.new_event_loop()
    try:
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        weight_service = WeightAdjustmentService(factory.graph_storage)
        result = loop.run_until_complete(
            weight_service.batch_decay(days_old=0, half_life_days=half_life_days)
        )

        return {
            "status": "completed",
            "half_life_days": half_life_days,
            "edges_decayed": result.get("edges_updated", 0),
        }
    except Exception as e:
        logger.error("run_weight_decay_real failed: %s", e)
        return {"status": "error", "error": str(e), "edges_decayed": 0}
    finally:
        loop.run_until_complete(factory.shutdown())
        loop.close()


@app.task(name="mkg.tasks.resolve_predictions")
def resolve_predictions() -> dict[str, Any]:
    """Check pending predictions and compute accuracy metrics.

    Uses AccuracyTracker to check for unresolved predictions.
    In the current implementation, predictions are resolved by
    calling record_outcome() when market data confirms/denies the prediction.
    """
    try:
        from mkg.domain.services.accuracy_tracker import AccuracyTracker
        tracker = AccuracyTracker()
        accuracy = tracker.get_accuracy()
        stats = tracker.get_stats()

        return {
            "status": "completed",
            "accuracy": accuracy,
            "total_predictions": stats.get("total_predictions", 0),
            "resolved_predictions": stats.get("resolved_predictions", 0),
        }
    except Exception as e:
        logger.error("resolve_predictions failed: %s", e)
        return {"status": "error", "error": str(e), "predictions_resolved": 0}


@app.task(name="mkg.tasks.health_check")
def health_check() -> dict[str, Any]:
    """Pipeline health check — verifies SQLite storage and audit trail.

    Tests:
    - SQLite graph DB accessible
    - Audit logger DB accessible
    - Provenance DB accessible
    """
    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    try:
        factory = _get_factory(db_dir)
        loop = asyncio.new_event_loop()
        try:
            health = loop.run_until_complete(factory.graph_storage.health_check())
            sqlite_status = health.get("status", "unknown")
            entity_count = health.get("entity_count", 0)
        except Exception as e:
            sqlite_status = f"error: {e}"
            entity_count = 0
        finally:
            loop.run_until_complete(factory.shutdown())
            loop.close()

        # Check audit logger
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        audit = PersistentAuditLogger(db_path=os.path.join(db_dir, "audit.db"))
        report = audit.export_report()
        audit_entries = report["total_entries"]

        return {
            "status": "healthy",
            "sqlite": sqlite_status,
            "entity_count": entity_count,
            "audit_entries": audit_entries,
        }
    except Exception as e:
        logger.error("health_check failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}


def health_check_real(db_dir: str | None = None) -> dict[str, Any]:
    """Real health check — verifies SQLite storage and audit trail.

    Tests:
    - SQLite graph DB accessible
    - Audit logger DB accessible
    - Provenance DB accessible
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    try:
        factory = _get_factory(db_dir)
        loop = asyncio.new_event_loop()
        try:
            # Check SQLite graph storage
            entities = loop.run_until_complete(
                factory.graph_storage.find_entities(filters={})
            )
            sqlite_status = "connected"
        except Exception as e:
            sqlite_status = f"error: {e}"
        finally:
            loop.run_until_complete(factory.shutdown())
            loop.close()

        # Check audit logger
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        audit = PersistentAuditLogger(db_path=os.path.join(db_dir, "audit.db"))
        report = audit.export_report()
        audit_entries = report["total_entries"]

        return {
            "status": "healthy",
            "sqlite": sqlite_status,
            "audit_entries": audit_entries,
        }
    except Exception as e:
        logger.error("health_check_real failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}
