# mkg/domain/services/service_factory.py
"""ServiceFactory — creates and wires all MKG services.

Single factory for constructing the full service dependency graph.
Used by both Celery tasks and API dependencies.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Creates and wires MKG services with persistent storage."""

    def __init__(
        self,
        db_dir: str | None = None,
        anthropic_api_key: str | None = None,
    ) -> None:
        self._db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
        self._api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._initialized = False
        self._graph_storage: Any = None
        self._article_storage: Any = None

    async def initialize(self) -> None:
        """Initialize storage backends.

        Set MKG_GRAPH_BACKEND=postgres and MKG_DATABASE_URL to use
        PostgreSQL graph storage. Defaults to sqlite.
        """
        os.makedirs(self._db_dir, exist_ok=True)

        graph_backend = os.environ.get("MKG_GRAPH_BACKEND", "sqlite").lower()

        if graph_backend == "postgres":
            from mkg.infrastructure.postgres.graph_storage import PostgresGraphStorage

            database_url = os.environ.get(
                "MKG_DATABASE_URL",
                os.environ.get("DATABASE_URL", ""),
            )
            if not database_url:
                raise ValueError(
                    "MKG_GRAPH_BACKEND=postgres requires MKG_DATABASE_URL or DATABASE_URL"
                )
            self._graph_storage = PostgresGraphStorage(database_url=database_url)
        else:
            from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage

            self._graph_storage = SQLiteGraphStorage(
                db_path=os.path.join(self._db_dir, "graph.db")
            )

        await self._graph_storage.initialize()

        from mkg.infrastructure.sqlite.article_storage import SQLiteArticleStorage

        self._article_storage = SQLiteArticleStorage(
            db_path=os.path.join(self._db_dir, "articles.db")
        )
        await self._article_storage.initialize()

        # Compliance & traceability services (SQLite-backed for persistence)
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        from mkg.domain.services.compliance_manager import ComplianceManager
        from mkg.domain.services.lineage_tracer import LineageTracer

        self._provenance_tracker = PersistentProvenanceTracker(
            db_path=os.path.join(self._db_dir, "provenance.db")
        )
        self._audit_logger = PersistentAuditLogger(
            db_path=os.path.join(self._db_dir, "audit.db")
        )
        self._compliance_manager = ComplianceManager()
        self._lineage_tracer = LineageTracer(
            provenance_tracker=self._provenance_tracker,
            compliance_manager=self._compliance_manager,
        )

        self._initialized = True
        logger.info("MKG ServiceFactory initialized: db_dir=%s", self._db_dir)

    async def shutdown(self) -> None:
        """Close all connections."""
        if self._graph_storage:
            await self._graph_storage.close()
        if self._article_storage:
            await self._article_storage.close()
        self._initialized = False

    @property
    def graph_storage(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._graph_storage

    @property
    def article_storage(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._article_storage

    @property
    def provenance_tracker(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._provenance_tracker

    @property
    def audit_logger(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._audit_logger

    @property
    def compliance_manager(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._compliance_manager

    @property
    def lineage_tracer(self) -> Any:
        assert self._initialized, "Call initialize() first"
        return self._lineage_tracer

    def create_extraction_orchestrator(self) -> Any:
        """Create the ExtractionOrchestrator with tiered extractors."""
        from mkg.domain.services.cost_governance import CostGovernance
        from mkg.domain.services.dlq import DeadLetterQueue
        from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
        from mkg.infrastructure.llm.claude_extractor import ClaudeExtractor
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        extractors = []
        if self._api_key:
            extractors.append(ClaudeExtractor(api_key=self._api_key))
        extractors.append(RegexExtractor())

        return ExtractionOrchestrator(
            extractors=extractors,
            cost_governance=CostGovernance(
                monthly_budget_usd=float(
                    os.environ.get("MONTHLY_AI_BUDGET_USD", "30")
                )
            ),
            dlq=DeadLetterQueue(),
        )

    def create_pipeline_orchestrator(self) -> Any:
        """Create the full PipelineOrchestrator with all services wired."""
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.article_dedup import ArticleDedup
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        from mkg.domain.services.graph_mutation import GraphMutationService
        from mkg.domain.services.hallucination_verifier import HallucinationVerifier
        from mkg.domain.services.impact_table import ImpactTableBuilder
        from mkg.domain.services.pii_detector import PIIDetector
        from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
        from mkg.domain.services.propagation_engine import PropagationEngine

        storage = self.graph_storage
        registry = CanonicalEntityRegistry(load_defaults=True)

        return PipelineOrchestrator(
            graph_storage=storage,
            extraction_orchestrator=self.create_extraction_orchestrator(),
            hallucination_verifier=HallucinationVerifier(),
            graph_mutation=GraphMutationService(storage, registry),
            propagation_engine=PropagationEngine(storage),
            causal_chain_builder=CausalChainBuilder(storage),
            alert_system=AlertSystem(),
            impact_table_builder=ImpactTableBuilder(storage),
            article_dedup=ArticleDedup(),
            provenance_tracker=self._provenance_tracker,
            audit_logger=self._audit_logger,
            pii_detector=PIIDetector(),
        )

    def create_signal_bridge(self) -> Any:
        """Create SignalBridge with compliance wiring."""
        from mkg.domain.services.signal_bridge import SignalBridge

        return SignalBridge(
            compliance_manager=self._compliance_manager,
            lineage_tracer=self._lineage_tracer,
        )

    def create_news_fetcher(self) -> Any:
        """Create the multi-source news fetcher."""
        from mkg.infrastructure.external.real_news_fetcher import (
            RSSNewsFetcher,
            RealMultiSourceFetcher,
        )
        return RealMultiSourceFetcher(fetchers=[RSSNewsFetcher()])
