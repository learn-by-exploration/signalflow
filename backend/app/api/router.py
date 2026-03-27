"""Main API router aggregating all sub-routers."""

from fastapi import APIRouter, Depends

from app.auth import require_auth
from app.api.signals import router as signals_router
from app.api.markets import router as markets_router
from app.api.alerts import router as alerts_router
from app.api.history import router as history_router
from app.api.price_alerts import router as price_alerts_router
from app.api.portfolio import router as portfolio_router
from app.api.sharing import router as sharing_router
from app.api.ai_qa import router as ai_qa_router
from app.api.backtest import router as backtest_router
from app.api.feedback import router as feedback_router
from app.api.news import router as news_router
from app.api.auth_routes import router as auth_router
from app.api.signal_feedback import router as signal_feedback_router
from app.api.payments import router as payments_router
from app.api.seo import router as seo_router
from app.api.admin import router as admin_router

# Protected routes — require API key or JWT
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])
# History must come before signals so /signals/history isn't caught by /signals/{signal_id}
api_router.include_router(history_router)
api_router.include_router(signals_router)
api_router.include_router(markets_router)
api_router.include_router(alerts_router)
api_router.include_router(price_alerts_router)
api_router.include_router(portfolio_router)
api_router.include_router(ai_qa_router)
api_router.include_router(backtest_router)
api_router.include_router(feedback_router)
api_router.include_router(news_router)
api_router.include_router(signal_feedback_router)
api_router.include_router(payments_router)
api_router.include_router(admin_router)

# Public routes — no API key required (shared signal view)
# Sharing router has both public (GET /shared) and protected (POST /share) routes
# so we register it on the protected router
api_router.include_router(sharing_router)

# Auth routes — public (no auth required)
public_router = APIRouter(prefix="/api/v1")
public_router.include_router(auth_router)
public_router.include_router(seo_router)
