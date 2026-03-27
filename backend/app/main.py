"""FastAPI application entrypoint."""

import hmac
import logging
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router, public_router
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

    # Validate required configuration
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    # Sentry init (if DSN provided)
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    # Start PubSub broadcaster for multi-worker WebSocket support
    _pubsub_broadcaster = None
    if settings.redis_url:
        try:
            from app.api.websocket import manager as ws_manager
            from app.services.pubsub import PubSubBroadcaster
            _pubsub_broadcaster = PubSubBroadcaster(settings.redis_url, ws_manager)
            await _pubsub_broadcaster.start()
            app.state.pubsub_broadcaster = _pubsub_broadcaster
        except Exception:
            logger.warning("pubsub_broadcaster_start_failed")

    yield

    # Graceful shutdown: stop PubSub, drain connections
    logger.info("signalflow_shutting_down")

    if _pubsub_broadcaster:
        try:
            await _pubsub_broadcaster.stop()
        except Exception:
            logger.warning("pubsub_broadcaster_stop_failed")

    try:
        from app.database import engine as async_engine
        await async_engine.dispose()
        logger.info("database_connections_closed")
    except Exception:
        logger.warning("failed_to_close_database_connections")


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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Chat-ID", "X-Request-ID"],
)

# ── Trusted Host middleware (production only) ──
if settings.environment == "production" and settings.allowed_hosts:
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts.split(","),
    )


# ── Correlation ID middleware ──
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Attach a unique request_id to every request for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Content Security Policy
    backend_host = settings.api_host if settings.environment == "production" else "localhost"
    csp_directives = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        f"connect-src 'self' {settings.frontend_url} wss://{backend_host}",
        "font-src 'self' https://fonts.gstatic.com",
        "frame-ancestors 'none'",
        "object-src 'none'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # No-index for shared signal views
    if request.url.path.startswith("/api/v1/shared/"):
        response.headers["X-Robots-Tag"] = "noindex"
    return response


# ── Request body size limiter ──
@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    """Reject requests with bodies larger than max_request_body_bytes (1MB default)."""
    max_bytes = settings.max_request_body_bytes
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_bytes:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large. Maximum size: {max_bytes} bytes"},
        )
    return await call_next(request)


# ── Routers ──
app.include_router(api_router)
app.include_router(public_router)
app.include_router(ws_router)

# ── Rate limiting ──
app.state.limiter = limiter


def _rate_limit_exceeded_with_logging(request, exc):
    """Log rate limit violations and return 429."""
    logger.warning(
        "rate_limit_exceeded",
        client_ip=request.client.host if request.client else "unknown",
        path=request.url.path,
    )
    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_with_logging)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — log details but return sanitized message."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/metrics")
async def metrics_endpoint(request: Request) -> JSONResponse:
    """Prometheus-compatible metrics endpoint.

    Protected: only accessible from localhost or with internal API key.
    """
    # Allow localhost and internal API key only
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "")
    internal_key = settings.internal_api_key

    is_local = client_ip in ("127.0.0.1", "::1", "localhost")
    is_internal = internal_key and hmac.compare_digest(api_key, internal_key)

    if not is_local and not is_internal:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    from app.services.metrics import get_metrics_text
    from starlette.responses import Response
    return Response(content=get_metrics_text(), media_type="text/plain; charset=utf-8")


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
        from app.database import engine as async_engine, async_session
        from sqlalchemy import text as sql_text
        async with async_engine.connect() as conn:
            await conn.execute(sql_text("SELECT 1"))
        status["db_status"] = "ok"

        # Active signals count + last data fetch
        try:
            from sqlalchemy import func, select
            from app.models.signal import Signal
            from app.models.market_data import MarketData
            async with async_session() as db:
                sig_count = await db.execute(
                    select(func.count()).select_from(Signal).where(Signal.is_active.is_(True))
                )
                status["active_signals_count"] = sig_count.scalar() or 0

                last_fetch = await db.execute(
                    select(func.max(MarketData.timestamp))
                )
                last_ts = last_fetch.scalar()
                status["last_data_fetch"] = last_ts.isoformat() if last_ts else None

                # Mark degraded if data is stale (>10 min)
                if last_ts:
                    from datetime import timedelta
                    age = datetime.now(timezone.utc) - last_ts.replace(tzinfo=timezone.utc) if last_ts.tzinfo is None else datetime.now(timezone.utc) - last_ts
                    if age > timedelta(minutes=10):
                        status["status"] = "degraded"
                        status["data_status"] = "stale"
        except Exception:
            status["active_signals_count"] = "error"
            status["last_data_fetch"] = "error"

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

    # PubSub status
    pubsub = getattr(app.state, "pubsub_broadcaster", None)
    status["pubsub_status"] = "connected" if pubsub and pubsub.is_connected else "disconnected"

    # AI budget check
    try:
        from app.services.ai_engine.cost_tracker import CostTracker
        tracker = CostTracker()
        summary = tracker.get_usage_summary()
        budget = float(settings.monthly_ai_budget_usd)
        spent = summary.get("total_cost_usd", 0)
        status["ai_budget_remaining_pct"] = round((1 - spent / budget) * 100, 1) if budget > 0 else 100.0
    except Exception:
        pass

    return status
