"""MKG test configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "id": "tsmc-001",
        "name": "Taiwan Semiconductor Manufacturing Company",
        "canonical_name": "TSMC",
        "entity_type": "Company",
        "properties": {
            "ticker": "TSM",
            "sector": "Semiconductors",
            "country": "Taiwan",
            "market_cap_usd": 800_000_000_000,
        },
    }


@pytest.fixture
def sample_edge_data():
    """Sample edge data for testing."""
    return {
        "source_id": "tsmc-001",
        "target_id": "nvidia-001",
        "relation_type": "SUPPLIES_TO",
        "weight": 0.85,
        "confidence": 0.92,
        "properties": {
            "product_category": "Advanced Logic Chips",
            "volume_pct": 0.25,
        },
    }
