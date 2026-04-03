# mkg/api/dependencies.py
"""Dependency injection for MKG FastAPI application.

Provides singleton service instances wired to the Neo4j dummy connector.
All services are constructed once at startup and injected via FastAPI Depends().
"""

from __future__ import annotations

from mkg.domain.services.accuracy_tracker import AccuracyTracker
from mkg.domain.services.alert_system import AlertSystem
from mkg.domain.services.article_dedup import ArticleDedup
from mkg.domain.services.article_pipeline import ArticleIngestionPipeline
from mkg.domain.services.audit_logger import AuditLogger
from mkg.domain.services.auth_tenant import AuthTenantService
from mkg.domain.services.backpressure import BackpressureManager
from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
from mkg.domain.services.causal_chain_builder import CausalChainBuilder
from mkg.domain.services.compliance_manager import ComplianceManager
from mkg.domain.services.cost_governance import CostGovernance
from mkg.domain.services.dlq import DeadLetterQueue
from mkg.domain.services.entity_service import EntityService
from mkg.domain.services.graph_mutation import GraphMutationService
from mkg.domain.services.hallucination_verifier import HallucinationVerifier
from mkg.domain.services.impact_table import ImpactTableBuilder
from mkg.domain.services.lineage_tracer import LineageTracer
from mkg.domain.services.pii_detector import PIIDetector
from mkg.domain.services.pipeline_observability import PipelineObservability
from mkg.domain.services.propagation_engine import PropagationEngine
from mkg.domain.services.provenance_tracker import ProvenanceTracker
from mkg.domain.services.retention_policy import RetentionPolicy
from mkg.domain.services.seed_loader import SeedDataLoader
from mkg.domain.services.signal_bridge import SignalBridge
from mkg.domain.services.tribal_knowledge import TribalKnowledgeInput
from mkg.domain.services.webhook_delivery import WebhookDelivery
from mkg.domain.services.weight_adjustment import WeightAdjustmentService
from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


class ServiceContainer:
    """Holds all MKG service singletons.

    Created once at app startup. Access individual services via properties.
    """

    def __init__(self) -> None:
        import os
        self._db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
        os.makedirs(self._db_dir, exist_ok=True)

        # Core storage — SQLite for persistence
        self.graph_storage = SQLiteGraphStorage(
            db_path=os.path.join(self._db_dir, "graph.db")
        )
        self.registry = CanonicalEntityRegistry(load_defaults=True)

        # Domain services (graph-dependent)
        self.entity_service = EntityService(self.graph_storage)
        self.propagation_engine = PropagationEngine(self.graph_storage)
        self.weight_adjustment = WeightAdjustmentService(self.graph_storage)
        self.causal_chain = CausalChainBuilder(self.graph_storage)
        self.tribal_knowledge = TribalKnowledgeInput(self.graph_storage)
        self.seed_loader = SeedDataLoader(self.graph_storage)
        self.graph_mutation = GraphMutationService(self.graph_storage, self.registry)
        self.impact_table = ImpactTableBuilder(self.graph_storage)

        # Standalone services
        self.article_pipeline = ArticleIngestionPipeline()
        self.article_dedup = ArticleDedup()
        self.alert_system = AlertSystem()
        self.accuracy_tracker = AccuracyTracker()
        self.webhook_delivery = WebhookDelivery()
        self.auth_tenant = AuthTenantService()
        self.cost_governance = CostGovernance(monthly_budget_usd=30.0)
        self.hallucination_verifier = HallucinationVerifier()
        self.observability = PipelineObservability()
        self.backpressure = BackpressureManager()
        self.dlq = DeadLetterQueue()

        # Compliance & traceability services (persistent backends)
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        self.compliance_manager = ComplianceManager()
        self.audit_logger = PersistentAuditLogger(
            db_path=os.path.join(self._db_dir, "audit.db")
        )
        self.pii_detector = PIIDetector()
        self.provenance_tracker = PersistentProvenanceTracker(
            db_path=os.path.join(self._db_dir, "provenance.db")
        )
        self.retention_policy = RetentionPolicy()
        self.lineage_tracer = LineageTracer(
            provenance_tracker=self.provenance_tracker,
            compliance_manager=self.compliance_manager,
        )

        # Signal bridge (connects MKG analysis to SignalFlow)
        self.signal_bridge = SignalBridge(
            compliance_manager=self.compliance_manager,
            lineage_tracer=self.lineage_tracer,
        )

    async def startup(self) -> None:
        """Initialize storage and seed default data."""
        await self.graph_storage.initialize()

    async def shutdown(self) -> None:
        """Close all storage connections."""
        await self.graph_storage.close()
        # Close persistent SQLite backends
        if hasattr(self.audit_logger, '_conn') and self.audit_logger._conn:
            try:
                self.audit_logger._conn.close()
            except Exception:
                pass
        if hasattr(self.provenance_tracker, '_conn') and self.provenance_tracker._conn:
            try:
                self.provenance_tracker._conn.close()
            except Exception:
                pass


# Module-level singleton — initialised when the app starts
_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get the global ServiceContainer. Must be initialised first."""
    if _container is None:
        raise RuntimeError("ServiceContainer not initialised — call init_container() first")
    return _container


def init_container() -> ServiceContainer:
    """Create and store the global ServiceContainer."""
    global _container
    _container = ServiceContainer()
    return _container
