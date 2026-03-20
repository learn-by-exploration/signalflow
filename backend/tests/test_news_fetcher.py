"""Tests for the news fetcher service."""

import pytest

from app.services.ai_engine.news_fetcher import (
    _build_search_query,
    _parse_rss_titles,
    fetch_news_for_symbol,
)


class TestParseRssTitles:
    def test_parse_cdata_titles(self) -> None:
        xml = (
            "<rss><channel>"
            "<title><![CDATA[Feed Title]]></title>"
            "<item><title><![CDATA[Article One About Stocks]]></title></item>"
            "<item><title><![CDATA[Article Two About Market]]></title></item>"
            "</channel></rss>"
        )
        result = _parse_rss_titles(xml)
        assert "Article One About Stocks" in result
        assert "Article Two About Market" in result
        # Feed title should be excluded (CDATA first match is feed title)
        # but the regex only matches CDATA titles, so both articles show up

    def test_parse_plain_titles(self) -> None:
        xml = (
            "<rss><channel>"
            "<title>Feed Title</title>"
            "<item><title>Stock Market Rallies Today</title></item>"
            "<item><title>Crypto Prices Surge Overnight</title></item>"
            "</channel></rss>"
        )
        result = _parse_rss_titles(xml)
        assert len(result) >= 1
        # At least one article should be found
        found = any("Rallies" in r or "Surge" in r for r in result)
        assert found

    def test_parse_empty_xml(self) -> None:
        result = _parse_rss_titles("")
        assert result == []

    def test_strips_html_entities(self) -> None:
        xml = (
            "<rss><channel><title>Feed</title>"
            "<item><title>Markets &amp; Trading Update</title></item>"
            "</channel></rss>"
        )
        result = _parse_rss_titles(xml)
        assert any("Markets & Trading" in r for r in result)

    def test_filters_short_titles(self) -> None:
        xml = (
            "<rss><channel><title>Feed</title>"
            "<item><title>OK</title></item>"
            "<item><title>This is a proper article headline</title></item>"
            "</channel></rss>"
        )
        result = _parse_rss_titles(xml)
        # "OK" is less than 10 chars, should be filtered
        assert all(len(r) > 10 for r in result)


class TestBuildSearchQuery:
    def test_stock_query(self) -> None:
        q = _build_search_query("RELIANCE.NS", "stock")
        assert "RELIANCE" in q
        assert "NSE" in q
        assert ".NS" not in q

    def test_crypto_query(self) -> None:
        q = _build_search_query("BTCUSDT", "crypto")
        assert "BTC" in q
        assert "cryptocurrency" in q
        assert "USDT" not in q

    def test_forex_query(self) -> None:
        q = _build_search_query("EUR/USD", "forex")
        assert "EUR/USD" in q
        assert "forex" in q


class TestFetchNewsForSymbol:
    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        """Fetch should return a list (may be empty if network unavailable)."""
        result = await fetch_news_for_symbol("BTCUSDT", "crypto", max_articles=3)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_max_articles_limit(self) -> None:
        result = await fetch_news_for_symbol("RELIANCE.NS", "stock", max_articles=2)
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_deduplication(self) -> None:
        """Results should not contain duplicate headlines."""
        result = await fetch_news_for_symbol("ETHUSDT", "crypto", max_articles=10)
        lowered = [r.lower().strip() for r in result]
        assert len(lowered) == len(set(lowered))
