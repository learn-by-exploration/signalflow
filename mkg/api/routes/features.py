# mkg/api/routes/features.py
"""MKG feature catalog, competitive positioning, and about endpoints.

Serves embedded documentation about MKG's capabilities, competitive
advantages, application domains, and MiroFish integration status.

Endpoints:
- GET /about — identity, power statement, thesis
- GET /about/features — full feature catalog by category
- GET /about/novel — capabilities unique to MKG (zero competitors)
- GET /about/competitors — competitive landscape
- GET /about/market — market sizing and buyer data
- GET /about/applications — financial markets and supply chain use cases
- GET /about/tribal-knowledge — six types of tribal knowledge MKG encodes
- GET /about/mirofish — MiroFish integration status and roadmap
- GET /about/complete — full profile (all of the above)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from mkg.domain.features import (
    APPLICATION_DOMAINS,
    COMPETITORS,
    MARKET_DATA,
    MIROFISH_INTEGRATION,
    NOT_MKG,
    ONE_LINE_NICHE,
    POWER_STATEMENT,
    THREE_SPEED_THESIS,
    TAGLINE,
    TRIBAL_KNOWLEDGE_STATEMENT,
    TRIBAL_KNOWLEDGE_TYPES,
    get_features_by_category,
    get_full_profile,
    get_novel_features,
)

router = APIRouter()


@router.get("/about")
async def about() -> dict[str, Any]:
    """MKG identity, power statement, and three-speed thesis."""
    return {
        "data": {
            "tagline": TAGLINE,
            "one_line_niche": ONE_LINE_NICHE,
            "power_statement": POWER_STATEMENT,
            "tribal_knowledge_statement": TRIBAL_KNOWLEDGE_STATEMENT,
            "three_speed_thesis": THREE_SPEED_THESIS,
            "not_mkg": NOT_MKG,
        }
    }


@router.get("/about/features")
async def features() -> dict[str, Any]:
    """Full feature catalog grouped by category."""
    by_category = get_features_by_category()
    novel = get_novel_features()
    return {
        "data": {
            "categories": by_category,
            "total_features": sum(len(v) for v in by_category.values()),
            "novel_count": len(novel),
        }
    }


@router.get("/about/novel")
async def novel_capabilities() -> dict[str, Any]:
    """Capabilities that exist in zero commercial platforms."""
    novel = get_novel_features()
    return {
        "data": {
            "novel_capabilities": novel,
            "count": len(novel),
            "statement": (
                f"MKG has {len(novel)} capabilities that exist in zero "
                "commercial platforms — Bloomberg, LSEG, FactSet, Capital IQ, "
                "AlphaSense, RavenPack, Palantir, Interos, or FinDKG."
            ),
        }
    }


@router.get("/about/competitors")
async def competitors() -> dict[str, Any]:
    """Competitive landscape with gap analysis."""
    return {
        "data": {
            "competitors": [
                {
                    "name": c.name,
                    "tier": c.tier,
                    "revenue": c.revenue,
                    "users": c.users,
                    "price_per_seat": c.price_per_seat,
                    "strengths": c.strengths,
                    "weaknesses": c.weaknesses,
                    "threat_to_mkg": c.threat_to_mkg,
                    "threat_timeline": c.threat_timeline,
                }
                for c in COMPETITORS
            ],
            "count": len(COMPETITORS),
        }
    }


@router.get("/about/market")
async def market() -> dict[str, Any]:
    """Market sizing, segments, and buyer spending data."""
    return {"data": MARKET_DATA}


@router.get("/about/applications")
async def applications() -> dict[str, Any]:
    """Application domains — financial markets and supply chain."""
    return {
        "data": {
            "domains": APPLICATION_DOMAINS,
            "count": len(APPLICATION_DOMAINS),
        }
    }


@router.get("/about/tribal-knowledge")
async def tribal_knowledge() -> dict[str, Any]:
    """Six types of tribal knowledge MKG encodes in the graph."""
    return {
        "data": {
            "types": TRIBAL_KNOWLEDGE_TYPES,
            "count": len(TRIBAL_KNOWLEDGE_TYPES),
        }
    }


@router.get("/about/mirofish")
async def mirofish() -> dict[str, Any]:
    """MiroFish integration status, reused components, and roadmap."""
    return {"data": MIROFISH_INTEGRATION}


@router.get("/about/complete")
async def complete_profile() -> dict[str, Any]:
    """Complete MKG profile — all features, competitors, market, applications."""
    return {"data": get_full_profile()}
