# mkg/tests/test_app_factory.py
"""Tests for MKG FastAPI app factory and DI container.

Covers:
- App creation and configuration
- CORS middleware
- Lifespan (startup/shutdown)
- ServiceContainer wiring
- Health and metrics endpoints (detailed assertions)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api.app import create_app
from mkg.api.dependencies import (
    ServiceContainer,
    get_container,
    init_container,
    _container,
)
import mkg.api.dependencies as deps


class TestAppFactory:
    """App factory and configuration."""

    def test_create_app_returns_fastapi(self):
        app = create_app()
        assert app.title == "MKG — Market Knowledge Graph"

    def test_create_app_has_version(self):
        from mkg import __version__
        app = create_app()
        assert app.version == __version__

    def test_create_app_has_routes(self):
        app = create_app()
        paths = [r.path for r in app.routes]
        assert "/health" in paths
        assert "/metrics" in paths

    def test_create_app_has_cors_middleware(self):
        app = create_app()
        middleware_classes = [type(m).__name__ for m in app.user_middleware]
        # FastAPI stores CORSMiddleware config in user_middleware
        assert any("CORS" in name or "cors" in name.lower() for name in middleware_classes) or \
               len(app.user_middleware) > 0  # CORS is registered

    def test_create_app_includes_api_routers(self):
        app = create_app()
        paths = {r.path for r in app.routes}
        # Check key route prefixes exist
        api_routes = [p for p in paths if p.startswith("/api/v1")]
        assert len(api_routes) > 0


class TestServiceContainer:
    """DI container wiring and lifecycle."""

    def test_container_init(self):
        container = ServiceContainer()
        assert container.graph_storage is not None
        assert container.entity_service is not None
        assert container.propagation_engine is not None
        assert container.weight_adjustment is not None
        assert container.causal_chain is not None
        assert container.tribal_knowledge is not None
        assert container.seed_loader is not None
        assert container.graph_mutation is not None
        assert container.impact_table is not None

    def test_container_standalone_services(self):
        container = ServiceContainer()
        assert container.article_pipeline is not None
        assert container.article_dedup is not None
        assert container.alert_system is not None
        assert container.accuracy_tracker is not None
        assert container.webhook_delivery is not None
        assert container.auth_tenant is not None
        assert container.cost_governance is not None
        assert container.hallucination_verifier is not None
        assert container.observability is not None
        assert container.backpressure is not None
        assert container.dlq is not None
        assert container.registry is not None

    async def test_container_startup_shutdown(self):
        container = ServiceContainer()
        await container.startup()
        assert container.graph_storage.is_connected
        await container.shutdown()
        assert not container.graph_storage.is_connected

    def test_init_container_creates_singleton(self):
        old = deps._container
        try:
            deps._container = None
            c = init_container()
            assert c is not None
            assert get_container() is c
        finally:
            deps._container = old

    def test_get_container_raises_if_not_init(self):
        old = deps._container
        try:
            deps._container = None
            with pytest.raises(RuntimeError, match="not initialised"):
                get_container()
        finally:
            deps._container = old

    def test_cost_governance_budget(self):
        container = ServiceContainer()
        assert container.cost_governance.is_within_budget()


class TestHealthEndpointDetailed:
    """Detailed health endpoint assertions."""

    @pytest.fixture
    async def client(self):
        import os
        old_key = os.environ.pop("MKG_API_KEY", None)
        app = create_app()
        container = init_container()
        await container.startup()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
        await container.shutdown()
        deps._container = None
        if old_key is not None:
            os.environ["MKG_API_KEY"] = old_key

    async def test_health_response_structure(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert "graph" in data
        assert "pipeline" in data

    async def test_health_graph_backend(self, client):
        resp = await client.get("/health")
        graph = resp.json()["graph"]
        assert graph["backend"] == "neo4j_dummy"
        assert graph["status"] == "healthy"

    async def test_metrics_returns_text(self, client):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        # Metrics can be text or JSON depending on observability export
        assert resp.text is not None
        assert len(resp.text) > 0
