"""Tests for config and settings."""

from unittest.mock import patch

import pytest

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
        assert s.environment == "development"
        assert s.api_host == "0.0.0.0"
        assert s.api_port == 8000
        assert s.monthly_ai_budget_usd == 30.0
        assert s.claude_model == "claude-sonnet-4-20250514"

    def test_tracked_stocks_default(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
        assert "RELIANCE.NS" in s.tracked_stocks
        assert "HDFCBANK.NS" in s.tracked_stocks
        assert len(s.tracked_stocks) == 15

    def test_tracked_crypto_default(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
        assert "BTCUSDT" in s.tracked_crypto
        assert "ETHUSDT" in s.tracked_crypto
        assert len(s.tracked_crypto) == 10

    def test_tracked_forex_default(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
        assert "USD/INR" in s.tracked_forex
        assert "EUR/USD" in s.tracked_forex
        assert len(s.tracked_forex) == 6

    def test_env_override(self):
        with patch.dict("os.environ", {"ENVIRONMENT": "production", "API_PORT": "9000"}):
            s = Settings()
        assert s.environment == "production"
        assert s.api_port == 9000

    def test_empty_api_keys_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
        assert s.anthropic_api_key == ""
        assert s.telegram_bot_token == ""
        assert s.sentry_dsn == ""
