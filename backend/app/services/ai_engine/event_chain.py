"""Event extraction and causal chain analysis using Claude AI.

Replaces simple sentiment scoring with structured event extraction
that maps causal chains from news articles to market impacts.
"""

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.services.ai_engine.prompts import EVENT_CHAIN_PROMPT

logger = logging.getLogger(__name__)

# Event category → expiry duration mapping
EVENT_EXPIRY_HOURS: dict[str, int] = {
    "macro_policy": 6 * 7 * 24,  # 6 weeks
    "earnings": 2 * 7 * 24,  # 2 weeks
    "regulatory": 4 * 7 * 24,  # 4 weeks
    "geopolitical": 7 * 24,  # 1 week
    "sector": 2 * 7 * 24,  # 2 weeks
    "commodity": 3 * 7 * 24,  # 3 weeks
    "technical": 3 * 24,  # 3 days
}

# Temporal decay half-lives in hours by category
DECAY_HALF_LIVES: dict[str, float] = {
    "macro_policy": 2 * 7 * 24,  # 2 weeks
    "earnings": 60,  # ~2.5 days
    "regulatory": 3 * 7 * 24,  # 3 weeks
    "geopolitical": 36,  # 1.5 days
    "sector": 2 * 7 * 24,  # 2 weeks
    "commodity": 2 * 7 * 24,  # 2 weeks
    "technical": 18,  # 18 hours
}

# Sector → symbol mapping for cross-symbol chain propagation
SECTOR_SYMBOLS: dict[str, list[str]] = {
    "banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "it": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "auto": ["MARUTI.NS", "TATAMOTORS.NS"],
    "telecom": ["BHARTIARTL.NS"],
    "energy": ["RELIANCE.NS"],
    "fmcg": ["ITC.NS"],
    "infrastructure": ["LT.NS"],
    "crypto_major": ["BTCUSDT", "ETHUSDT"],
    "crypto_alt": ["SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT"],
    "forex_major": ["EUR/USD", "GBP/JPY", "GBP/USD"],
    "forex_inr": ["USD/INR"],
}


def compute_event_impact(
    magnitude: float,
    hours_since_event: float,
    category: str,
) -> float:
    """Compute current impact of an event using exponential decay.

    I(t) = I_0 * e^(-λt)
    where λ = ln(2) / half_life

    Args:
        magnitude: Initial impact magnitude (0-1 scale).
        hours_since_event: Hours since event occurred.
        category: Event category for half-life lookup.

    Returns:
        Current impact value (0-1 scale, decayed).
    """
    half_life = DECAY_HALF_LIVES.get(category, 48)
    decay_rate = math.log(2) / half_life
    return magnitude * math.exp(-decay_rate * hours_since_event)


def compute_chain_score(
    chain_events: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Compute aggregate chain score from a list of event chain steps.

    Returns features for signal scoring:
    - chain_net_direction: [-1, 1] net bullish/bearish pressure
    - chain_confidence: [0, 1] confidence-weighted average
    - chain_count: number of active chains
    - chain_consensus: [0, 1] agreement between chains
    - chain_max_magnitude: strongest single chain impact

    Args:
        chain_events: List of dicts with keys: direction, magnitude, confidence,
                     category, hours_since.
        now: Current time (defaults to UTC now).

    Returns:
        Dict with chain features for scoring.
    """
    if not chain_events:
        return {
            "chain_net_direction": 0.0,
            "chain_confidence": 0.0,
            "chain_count": 0,
            "chain_consensus": 0.0,
            "chain_max_magnitude": 0.0,
            "chain_score": 50,  # neutral
        }

    if now is None:
        now = datetime.now(timezone.utc)

    direction_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0, "mixed": 0.0}

    total_impact = 0.0
    weighted_direction = 0.0
    weighted_confidence = 0.0
    max_magnitude = 0.0
    bullish_count = 0
    bearish_count = 0

    for evt in chain_events:
        direction_sign = direction_map.get(evt.get("direction", "neutral"), 0.0)
        magnitude = float(evt.get("magnitude", 0.5))
        confidence = float(evt.get("confidence", 50)) / 100.0
        hours_since = float(evt.get("hours_since", 0))
        category = evt.get("category", "sector")

        current_impact = compute_event_impact(magnitude, hours_since, category)
        abs_impact = abs(current_impact)

        weighted_direction += direction_sign * abs_impact
        weighted_confidence += confidence * abs_impact
        total_impact += abs_impact
        max_magnitude = max(max_magnitude, abs_impact)

        if direction_sign > 0:
            bullish_count += 1
        elif direction_sign < 0:
            bearish_count += 1

    chain_count = len(chain_events)

    if total_impact > 0:
        net_direction = weighted_direction / total_impact
        avg_confidence = weighted_confidence / total_impact
    else:
        net_direction = 0.0
        avg_confidence = 0.0

    # Consensus: 1.0 if all in same direction, 0.0 if evenly split
    total_directional = bullish_count + bearish_count
    if total_directional > 0:
        consensus = abs(bullish_count - bearish_count) / total_directional
    else:
        consensus = 0.0

    # Chain score: 50 + 50 * tanh(α * net_direction * confidence * consensus)
    alpha = 2.0
    raw = alpha * net_direction * avg_confidence * max(consensus, 0.3)
    chain_score = 50 + 50 * math.tanh(raw)

    return {
        "chain_net_direction": round(net_direction, 4),
        "chain_confidence": round(avg_confidence, 4),
        "chain_count": chain_count,
        "chain_consensus": round(consensus, 4),
        "chain_max_magnitude": round(max_magnitude, 4),
        "chain_score": max(0, min(100, int(round(chain_score)))),
    }


def get_sectors_for_symbol(symbol: str) -> list[str]:
    """Get sector names that a symbol belongs to."""
    sectors = []
    for sector, symbols in SECTOR_SYMBOLS.items():
        if symbol in symbols:
            sectors.append(sector)
    return sectors


def get_symbols_in_sector(sector: str) -> list[str]:
    """Get all symbols in a given sector."""
    return SECTOR_SYMBOLS.get(sector, [])


def propagate_event_to_symbols(
    affected_sectors: list[str],
    origin_symbol: str,
) -> list[str]:
    """Given affected sectors, return all symbols that should receive the event.

    Excludes the origin symbol to avoid double-counting.
    """
    symbols: set[str] = set()
    for sector in affected_sectors:
        for s in get_symbols_in_sector(sector):
            if s != origin_symbol:
                symbols.add(s)
    return list(symbols)


def get_event_expiry(category: str, occurred_at: datetime) -> datetime:
    """Calculate when an event should expire based on its category."""
    hours = EVENT_EXPIRY_HOURS.get(category, 7 * 24)
    return occurred_at + timedelta(hours=hours)


def parse_event_chain_response(response_text: str) -> dict[str, Any] | None:
    """Parse Claude's event chain JSON response.

    Args:
        response_text: Raw text from Claude API.

    Returns:
        Parsed dict or None if parsing fails.
    """
    try:
        # Strip markdown code fences if present
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        logger.error("Failed to parse event chain response: %s", response_text[:200])
        return None
