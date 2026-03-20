"""Main API router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.signals import router as signals_router
from app.api.markets import router as markets_router
from app.api.alerts import router as alerts_router
from app.api.history import router as history_router

api_router = APIRouter(prefix="/api/v1")
# History must come before signals so /signals/history isn't caught by /signals/{signal_id}
api_router.include_router(history_router)
api_router.include_router(signals_router)
api_router.include_router(markets_router)
api_router.include_router(alerts_router)
