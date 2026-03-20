"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.api.websocket import router as ws_router
from app.config import get_settings
from app.rate_limit import limiter

settings = get_settings()

# ── Structured logging ──
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.environment == "development"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.log_level)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# ── Track startup time ──
_startup_time: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    global _startup_time
    _startup_time = datetime.now(timezone.utc)
    logger.info("signalflow_starting", environment=settings.environment)

    # Sentry init (if DSN provided)
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    yield

    logger.info("signalflow_shutting_down")


app = FastAPI(
    title="SignalFlow AI",
    description="AI-Powered Trading Signal Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
_cors_origins = (
    [settings.frontend_url]
    if settings.environment == "development"
    else [settings.frontend_url] if settings.frontend_url else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(api_router)
app.include_router(ws_router)

# ── Rate limiting ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint with system status."""
    status = {
        "status": "healthy",
        "uptime": str(datetime.now(timezone.utc) - _startup_time) if _startup_time else "unknown",
        "environment": settings.environment,
        "disclaimer": "SignalFlow AI generates AI-powered signals for educational purposes. Not financial advice.",
    }

    # Database check
    try:
        from app.database import async_engine
        from sqlalchemy import text as sql_text
        async with async_engine.connect() as conn:
            await conn.execute(sql_text("SELECT 1"))
        status["db_status"] = "ok"
    except Exception:
        status["db_status"] = "error"
        status["status"] = "degraded"

    # Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        status["redis_status"] = "ok"
    except Exception:
        status["redis_status"] = "error"
        status["status"] = "degraded"

    return status
