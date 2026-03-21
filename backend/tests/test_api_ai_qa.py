"""Tests for /api/v1/ai/ask endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_ai_ask_fallback_when_no_budget(test_client):
    """When budget is exhausted, returns fallback answer."""
    with patch("app.api.ai_qa.CostTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.is_budget_available.return_value = False

        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "HDFCBANK.NS", "question": "Is this a good buy?"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["source"] == "fallback"
    assert "budget" in data["answer"].lower() or "exhausted" in data["answer"].lower()


@pytest.mark.asyncio
async def test_ai_ask_with_claude_success(test_client):
    """Successful Claude API call returns claude source."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "content": [{"text": "HDFC Bank shows strong fundamentals."}],
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }

    with (
        patch("app.api.ai_qa.CostTracker") as MockTracker,
        patch("app.api.ai_qa.httpx.AsyncClient") as MockClient,
    ):
        tracker_instance = MockTracker.return_value
        tracker_instance.is_budget_available.return_value = True
        tracker_instance.record_usage.return_value = 0.001

        # Create a proper async context manager mock
        client_ctx = AsyncMock()
        client_ctx.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=client_ctx)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "HDFCBANK", "question": "Technical outlook?"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["source"] == "claude"
    assert "HDFC" in data["answer"]


@pytest.mark.asyncio
async def test_ai_ask_fallback_on_api_error(test_client):
    """If Claude API raises an exception, returns fallback."""
    with (
        patch("app.api.ai_qa.CostTracker") as MockTracker,
        patch("app.api.ai_qa.httpx.AsyncClient") as MockClient,
    ):
        tracker_instance = MockTracker.return_value
        tracker_instance.is_budget_available.return_value = True

        client_instance = AsyncMock()
        client_instance.post.side_effect = Exception("API timeout")
        MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "BTCUSDT", "question": "What is the trend?"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["source"] == "fallback"


@pytest.mark.asyncio
async def test_ai_ask_crypto_symbol_detection(test_client):
    """Crypto symbols (ending in USDT) are detected correctly."""
    with patch("app.api.ai_qa.CostTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.is_budget_available.return_value = False

        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "ETHUSDT", "question": "Price outlook?"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ai_ask_forex_symbol_detection(test_client):
    """Forex symbols (containing /) are detected correctly."""
    with patch("app.api.ai_qa.CostTracker") as MockTracker:
        instance = MockTracker.return_value
        instance.is_budget_available.return_value = False

        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "EUR/USD", "question": "Direction?"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ai_ask_question_too_long(test_client):
    """Question exceeding max_length (500) rejected."""
    resp = await test_client.post(
        "/api/v1/ai/ask",
        json={"symbol": "TCS", "question": "x" * 501},
    )
    assert resp.status_code == 422
