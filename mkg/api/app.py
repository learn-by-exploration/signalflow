# mkg/api/app.py
"""MKG FastAPI application.

Root application factory with lifespan management, health endpoint,
router registration, and production middleware.
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mkg import __version__
from mkg.api.dependencies import get_container, init_container
from mkg.api.errors import register_error_handlers
from mkg.api.middleware import (
    APIKeyAuthMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    setup_rate_limiting,
)

# Initialize Sentry if DSN is configured
_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.environ.get("MKG_ENV", "development"),
        )
    except Exception:
        pass  # Sentry is optional

_start_time: float = 0.0

# OpenAPI tags for organized docs
TAGS_METADATA = [
    {"name": "system", "description": "Health checks and system metrics"},
    {"name": "entities", "description": "Entity and Edge CRUD operations"},
    {"name": "graph", "description": "Graph traversal, search, and seeding"},
    {"name": "propagation", "description": "Event propagation, weight adjustment, accuracy tracking"},
    {"name": "articles", "description": "Article ingestion pipeline and NER/RE extraction"},
    {"name": "alerts", "description": "Alert system, webhook delivery, and observability"},
    {"name": "tribal-knowledge", "description": "Expert-asserted entities, edges, and annotations"},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: wire services. Shutdown: close connections."""
    global _start_time
    _start_time = time.time()
    container = init_container()
    await container.startup()
    yield
    await container.shutdown()


def create_app() -> FastAPI:
    """Build the MKG FastAPI application."""
    app = FastAPI(
        title="MKG — Market Knowledge Graph",
        description=(
            "Dynamic relationship intelligence API for supply chain analysis. "
            "Provides entity/edge management, event propagation, causal chain "
            "analysis, and AI-powered article extraction."
        ),
        version=__version__,
        lifespan=lifespan,
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- Middleware (order matters: outermost first) ---
    # 1. Request ID — must be first so all other middleware can access it
    app.add_middleware(RequestIDMiddleware)
    # 2. Request logging — logs method, path, status, duration
    app.add_middleware(RequestLoggingMiddleware)
    # 3. API key auth — blocks unauthenticated requests to /api/*
    app.add_middleware(APIKeyAuthMiddleware)
    # 4. CORS — cross-origin access control
    allowed_origins = os.environ.get("MKG_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Error handlers ---
    register_error_handlers(app)

    # --- Rate limiting ---
    setup_rate_limiting(app)

    # --- Health ---
    @app.get("/health", tags=["system"])
    async def health() -> dict[str, Any]:
        container = get_container()
        graph_health = await container.graph_storage.health_check()
        obs_health = container.observability.health_check()
        return {
            "status": "healthy",
            "version": __version__,
            "uptime_seconds": round(time.time() - _start_time, 1),
            "graph": graph_health,
            "pipeline": obs_health,
        }

    # --- Metrics ---
    @app.get("/metrics", tags=["system"])
    async def metrics() -> str:
        container = get_container()
        return container.observability.export_prometheus()

    # Register route modules
    from mkg.api.routes import (
        alerts,
        articles,
        compliance,
        entities,
        features,
        graph,
        propagation,
        tribal,
    )

    app.include_router(entities.router, prefix="/api/v1", tags=["entities"])
    app.include_router(graph.router, prefix="/api/v1", tags=["graph"])
    app.include_router(propagation.router, prefix="/api/v1", tags=["propagation"])
    app.include_router(articles.router, prefix="/api/v1", tags=["articles"])
    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
    app.include_router(tribal.router, prefix="/api/v1", tags=["tribal-knowledge"])
    app.include_router(compliance.router, prefix="/api/v1", tags=["compliance"])
    app.include_router(features.router, prefix="/api/v1", tags=["about"])

    # --- Static files: MKG Research Intelligence Library ---
    # Serve core/ research documents at /research/
    # These are the intellectual moat documents (competitive analysis, niche
    # definition, problem definition, etc.)
    research_dir = Path(__file__).resolve().parent.parent.parent / "core"
    if research_dir.is_dir():
        app.mount(
            "/research",
            StaticFiles(directory=str(research_dir), html=True),
            name="research",
        )

    return app


app = create_app()
