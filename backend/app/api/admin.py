"""Admin API endpoints for revenue tracking and system metrics.

Protected by admin-level auth (requires internal API key).
"""

import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(request: Request) -> None:
    """Verify admin access via internal API key."""
    settings = get_settings()
    api_key = request.headers.get("X-API-Key", "")

    if not settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Admin access not configured")

    if not hmac.compare_digest(api_key, settings.internal_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.get("/revenue", response_model=dict)
async def get_revenue_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revenue metrics dashboard.

    Returns MRR, subscription counts, churn rate.
    Requires internal API key.
    """
    _require_admin(request)

    from app.services.revenue import get_revenue_metrics

    metrics = await get_revenue_metrics(db)
    return {"data": metrics}


@router.get("/shadow-mode", response_model=dict)
async def get_shadow_results(request: Request) -> dict:
    """Shadow mode comparison results.

    Returns aggregated v1.3 vs v1.4 pipeline comparison.
    Requires internal API key.
    """
    _require_admin(request)

    try:
        import redis

        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        from app.services.signal_gen.shadow_mode import get_shadow_summary

        summary = get_shadow_summary(r)
        r.close()
        return {"data": summary}
    except Exception as e:
        return {"data": {"error": str(e)}}
