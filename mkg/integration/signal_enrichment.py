# mkg/integration/signal_enrichment.py
"""MKG Signal Enrichment — bridges MKG analysis to backend signal generation.

This module provides the public API for the backend's SignalGenerator to
call MKG for supply chain risk enrichment. It:
1. Initializes a ServiceFactory (or reuses cached one)
2. Queries the graph for entities related to a symbol
3. Returns enrichment data (supply chain risk, confidence adjustment, disclaimers)

The backend calls `enrich_signal_for_symbol()` during signal generation.
If MKG has no data for a symbol, it returns an empty enrichment (no-op).
"""

import asyncio
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level cached factory (reused across calls)
_factory: Any = None
_initialized = False


def _get_factory() -> Any:
    """Get or create a ServiceFactory singleton for backend integration."""
    global _factory, _initialized
    if _initialized and _factory is not None:
        return _factory

    from mkg.service_factory import ServiceFactory
    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    _factory = ServiceFactory(db_dir=db_dir)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_factory.initialize())
    finally:
        loop.close()
    _initialized = True
    return _factory


def enrich_signal_for_symbol(
    symbol: str,
    market_type: str = "stock",
    include_compliance: bool = True,
) -> dict[str, Any]:
    """Enrich a signal with MKG supply chain analysis.

    Called by the backend's SignalGenerator to get MKG data for a symbol.
    Returns enrichment data that can be merged into signal output.

    Args:
        symbol: Trading symbol (e.g., "NVDA", "RELIANCE.NS", "BTCUSDT").
        market_type: Market type (stock, crypto, forex).
        include_compliance: Whether to include disclaimers/classification.

    Returns:
        Enrichment dict with supply_chain_risk, confidence_adjustment,
        risk_factors, affected_companies, reasoning_context, disclaimers.
        Returns empty enrichment if MKG has no relevant data.
    """
    try:
        factory = _get_factory()
        bridge = factory.create_signal_bridge()

        # Query graph for entities matching the symbol
        loop = asyncio.new_event_loop()
        try:
            graph_data = loop.run_until_complete(
                _query_graph_for_symbol(factory, symbol)
            )
        finally:
            loop.close()

        if not graph_data or not graph_data.get("entities"):
            return _empty_enrichment()

        # Build a synthetic pipeline result from graph data
        pipeline_result = _graph_data_to_pipeline_result(graph_data)

        if include_compliance:
            enrichment = bridge.enrich_signal_with_compliance(symbol, pipeline_result)
        else:
            enrichment = bridge.enrich_signal(symbol, pipeline_result)

        return enrichment

    except Exception as e:
        logger.error("MKG enrichment failed for %s: %s", symbol, e)
        return _empty_enrichment()


async def enrich_signal_for_symbol_async(
    symbol: str,
    market_type: str = "stock",
    include_compliance: bool = True,
) -> dict[str, Any]:
    """Async version of enrich_signal_for_symbol.

    For use in async contexts like FastAPI endpoints.
    """
    try:
        factory = _get_factory()
        bridge = factory.create_signal_bridge()

        graph_data = await _query_graph_for_symbol(factory, symbol)

        if not graph_data or not graph_data.get("entities"):
            return _empty_enrichment()

        pipeline_result = _graph_data_to_pipeline_result(graph_data)

        if include_compliance:
            return bridge.enrich_signal_with_compliance(symbol, pipeline_result)
        return bridge.enrich_signal(symbol, pipeline_result)

    except Exception as e:
        logger.error("MKG enrichment failed for %s: %s", symbol, e)
        return _empty_enrichment()


async def _query_graph_for_symbol(
    factory: Any,
    symbol: str,
) -> dict[str, Any]:
    """Query the MKG graph for entities and edges related to a symbol.

    Searches for the symbol as an entity name, then gets its subgraph.
    """
    storage = factory.graph_storage

    # Normalize symbol for search (strip .NS suffix, USDT suffix)
    search_name = symbol.replace(".NS", "").replace("USDT", "")

    # Search for matching entities
    entities = await storage.search(query=search_name, limit=5)

    if not entities:
        return {"entities": [], "edges": []}

    # Get subgraph around the first match
    primary_entity = entities[0]
    subgraph = await storage.get_subgraph(
        entity_id=primary_entity["id"],
        max_depth=2,
    )

    return {
        "entities": subgraph.get("nodes", []),
        "edges": subgraph.get("edges", []),
        "primary_entity": primary_entity,
    }


def _graph_data_to_pipeline_result(
    graph_data: dict[str, Any],
) -> dict[str, Any]:
    """Convert graph query results to a pipeline-compatible result dict.

    The SignalBridge expects pipeline output format with impacts and chains.
    """
    entities = graph_data.get("entities", [])
    edges = graph_data.get("edges", [])

    # Build impacts from connected entities
    impacts = []
    for entity in entities:
        if entity.get("id") == graph_data.get("primary_entity", {}).get("id"):
            continue  # Skip the primary entity itself
        impact_score = 0.0
        # Find edge connecting to this entity
        for edge in edges:
            if edge.get("target_id") == entity.get("id") or edge.get("source_id") == entity.get("id"):
                impact_score = max(impact_score, edge.get("weight", 0.1))
        impacts.append({
            "entity_id": entity.get("id"),
            "entity_name": entity.get("name", "Unknown"),
            "impact": impact_score,
            "depth": 1,
        })

    # Build simple causal chains
    causal_chains = []
    primary_name = graph_data.get("primary_entity", {}).get("name", "Unknown")
    for impact in impacts:
        if impact["impact"] >= 0.05:
            causal_chains.append({
                "trigger_name": primary_name,
                "affected_name": impact["entity_name"],
                "impact": impact["impact"],
                "chain_length": 1,
            })

    return {
        "status": "completed",
        "impacts": impacts,
        "causal_chains": causal_chains,
        "impact_table": {
            "entities": len(entities),
            "edges": len(edges),
        },
    }


def _empty_enrichment() -> dict[str, Any]:
    """Return empty enrichment when MKG has no data."""
    return {
        "supply_chain_risk": 0.0,
        "confidence_adjustment": 0,
        "risk_factors": [],
        "affected_companies": [],
        "reasoning_context": "",
        "has_material_impact": False,
        "impact_count": 0,
        "max_impact": 0.0,
    }


def shutdown() -> None:
    """Shutdown the cached factory. Call on app shutdown."""
    global _factory, _initialized
    if _factory is not None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_factory.shutdown())
        finally:
            loop.close()
    _factory = None
    _initialized = False
