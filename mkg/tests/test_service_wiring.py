# mkg/tests/test_service_wiring.py
"""Tests for service wiring — verifying ServiceContainer and ServiceFactory
have all compliance/traceability services properly connected.

Iterations 1-2: These tests verify the ROOT CAUSE fix — services must be
wired into the composition roots, not just built as orphan code.
"""

import pytest


class TestServiceContainerWiring:
    """ServiceContainer must expose all compliance/audit services."""

    def test_container_has_provenance_tracker(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "provenance_tracker")
        assert c.provenance_tracker is not None

    def test_container_has_audit_logger(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "audit_logger")
        assert c.audit_logger is not None

    def test_container_has_compliance_manager(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "compliance_manager")
        assert c.compliance_manager is not None

    def test_container_has_lineage_tracer(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "lineage_tracer")
        assert c.lineage_tracer is not None

    def test_container_has_retention_policy(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "retention_policy")
        assert c.retention_policy is not None

    def test_container_has_pii_detector(self):
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert hasattr(c, "pii_detector")
        assert c.pii_detector is not None

    def test_lineage_tracer_uses_provenance(self):
        """LineageTracer must be wired to the same ProvenanceTracker."""
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert c.lineage_tracer._provenance is c.provenance_tracker

    def test_lineage_tracer_uses_compliance(self):
        """LineageTracer must be wired to the same ComplianceManager."""
        from mkg.api.dependencies import ServiceContainer
        c = ServiceContainer()
        assert c.lineage_tracer._compliance is c.compliance_manager


class TestServiceFactoryWiring:
    """ServiceFactory must pass provenance/audit to PipelineOrchestrator."""

    @pytest.mark.asyncio
    async def test_factory_pipeline_has_provenance(self):
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir="/tmp/mkg_test_wiring")
        await factory.initialize()
        try:
            pipeline = factory.create_pipeline_orchestrator()
            assert pipeline._provenance is not None
        finally:
            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_factory_pipeline_has_audit(self):
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir="/tmp/mkg_test_wiring")
        await factory.initialize()
        try:
            pipeline = factory.create_pipeline_orchestrator()
            assert pipeline._audit is not None
        finally:
            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_factory_has_signal_bridge_with_compliance(self):
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir="/tmp/mkg_test_wiring")
        await factory.initialize()
        try:
            bridge = factory.create_signal_bridge()
            assert bridge._compliance is not None
            assert bridge._lineage is not None
        finally:
            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_factory_provenance_shared_across_services(self):
        """Provenance tracker should be shared between pipeline and bridge."""
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir="/tmp/mkg_test_wiring")
        await factory.initialize()
        try:
            pt = factory.provenance_tracker
            assert pt is not None
            # Verify same instance used
            pipeline = factory.create_pipeline_orchestrator()
            assert pipeline._provenance is pt
        finally:
            await factory.shutdown()
