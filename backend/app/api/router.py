"""Main API router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.signals import router as signals_router
from app.api.markets import router as markets_router
from app.api.alerts import router as alerts_router
from app.api.history import router as history_router
from app.api.price_alerts import router as price_alerts_router
from app.api.portfolio import router as portfolio_router
from app.api.sharing import router as sharing_router
from app.api.ai_qa import router as ai_qa_router
from app.api.backtest import router as backtest_router

api_router = APIRouter(prefix="/api/v1")
# History must come before signals so /signals/history isn't caught by /signals/{signal_id}
api_router.include_router(history_router)
# Sharing must come before signals so /signals/shared/{id} isn't caught by /signals/{signal_id}
api_router.include_router(sharing_router)
api_router.include_router(signals_router)
api_router.include_router(markets_router)
api_router.include_router(alerts_router)
api_router.include_router(price_alerts_router)
api_router.include_router(portfolio_router)
api_router.include_router(ai_qa_router)
api_router.include_router(backtest_router)
