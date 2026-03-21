"""Tests for AI engine prompts — verify template variables and format."""

import pytest

from app.services.ai_engine.prompts import (
    EVENING_WRAP_PROMPT,
    MORNING_BRIEF_PROMPT,
    REASONING_PROMPT,
    SENTIMENT_PROMPT,
    SYMBOL_QA_PROMPT,
)


class TestSentimentPrompt:
    def test_contains_required_placeholders(self):
        assert "{symbol}" in SENTIMENT_PROMPT
        assert "{market_type}" in SENTIMENT_PROMPT
        assert "{articles_text}" in SENTIMENT_PROMPT

    def test_format_succeeds(self):
        result = SENTIMENT_PROMPT.format(
            symbol="BTCUSDT", market_type="crypto",
            articles_text="Bitcoin hits new high."
        )
        assert "BTCUSDT" in result
        assert "crypto" in result

    def test_requests_json_output(self):
        assert "JSON" in SENTIMENT_PROMPT
        assert "sentiment_score" in SENTIMENT_PROMPT


class TestReasoningPrompt:
    def test_contains_required_placeholders(self):
        assert "{symbol}" in REASONING_PROMPT
        assert "{signal_type}" in REASONING_PROMPT
        assert "{confidence}" in REASONING_PROMPT
        assert "{technical_summary}" in REASONING_PROMPT
        assert "{sentiment_summary}" in REASONING_PROMPT

    def test_format_succeeds(self):
        result = REASONING_PROMPT.format(
            symbol="HDFCBANK.NS", signal_type="STRONG_BUY",
            confidence=92, technical_summary="RSI: 62.7",
            sentiment_summary="Positive news",
        )
        assert "HDFCBANK.NS" in result


class TestMorningBriefPrompt:
    def test_contains_required_placeholders(self):
        assert "{date}" in MORNING_BRIEF_PROMPT
        assert "{day_of_week}" in MORNING_BRIEF_PROMPT
        assert "{market_data}" in MORNING_BRIEF_PROMPT
        assert "{signals_summary}" in MORNING_BRIEF_PROMPT


class TestEveningWrapPrompt:
    def test_contains_required_placeholders(self):
        assert "{date}" in EVENING_WRAP_PROMPT
        assert "{performance_data}" in EVENING_WRAP_PROMPT
        assert "{signal_outcomes}" in EVENING_WRAP_PROMPT


class TestSymbolQAPrompt:
    def test_contains_required_placeholders(self):
        assert "{symbol}" in SYMBOL_QA_PROMPT
        assert "{market_type}" in SYMBOL_QA_PROMPT
        assert "{market_data}" in SYMBOL_QA_PROMPT
        assert "{signals_info}" in SYMBOL_QA_PROMPT
        assert "{question}" in SYMBOL_QA_PROMPT

    def test_format_succeeds(self):
        result = SYMBOL_QA_PROMPT.format(
            symbol="EUR/USD", market_type="forex",
            market_data="Price: 1.0854", signals_info="No signals",
            question="What direction?",
        )
        assert "EUR/USD" in result
        assert "What direction?" in result
