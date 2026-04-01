# mkg/tests/test_news_fetcher.py
"""Tests for dummy news fetcher implementations."""

import pytest

from mkg.infrastructure.external.news_fetcher import (
    DummyNewsApiFetcher,
    DummyRssFetcher,
    DummySecFilingFetcher,
    MultiSourceFetcher,
)


class TestDummyNewsApiFetcher:
    async def test_fetch_returns_articles(self):
        fetcher = DummyNewsApiFetcher()
        articles = await fetcher.fetch()
        assert len(articles) == 1
        assert articles[0]["source"] == "dummy_news_api"
        assert articles[0]["metadata"]["dummy"] is True

    async def test_fetch_with_symbols(self):
        fetcher = DummyNewsApiFetcher()
        articles = await fetcher.fetch(symbols=["TSMC"])
        assert "TSMC" in articles[0]["title"]

    def test_source_name(self):
        assert DummyNewsApiFetcher().source_name() == "dummy_news_api"


class TestDummySecFilingFetcher:
    async def test_fetch_returns_filing(self):
        fetcher = DummySecFilingFetcher()
        articles = await fetcher.fetch()
        assert len(articles) == 1
        assert articles[0]["source"] == "dummy_sec_edgar"
        assert articles[0]["metadata"]["filing_type"] == "10-K"

    async def test_fetch_with_symbol(self):
        fetcher = DummySecFilingFetcher()
        articles = await fetcher.fetch(symbols=["NVIDIA"])
        assert "NVIDIA" in articles[0]["title"]

    def test_source_name(self):
        assert DummySecFilingFetcher().source_name() == "dummy_sec_edgar"


class TestDummyRssFetcher:
    async def test_fetch_returns_article(self):
        fetcher = DummyRssFetcher()
        articles = await fetcher.fetch()
        assert len(articles) == 1
        assert articles[0]["source"] == "dummy_rss"

    def test_source_name(self):
        assert DummyRssFetcher().source_name() == "dummy_rss"


class TestMultiSourceFetcher:
    async def test_fetch_all_default(self):
        fetcher = MultiSourceFetcher()
        articles = await fetcher.fetch_all()
        assert len(articles) == 3  # one from each dummy source
        sources = {a["source"] for a in articles}
        assert "dummy_news_api" in sources
        assert "dummy_sec_edgar" in sources
        assert "dummy_rss" in sources

    async def test_fetch_all_with_symbols(self):
        fetcher = MultiSourceFetcher()
        articles = await fetcher.fetch_all(symbols=["ASML"])
        assert len(articles) == 3

    def test_source_count(self):
        assert MultiSourceFetcher().source_count == 3

    async def test_custom_fetchers(self):
        fetcher = MultiSourceFetcher(fetchers=[DummyNewsApiFetcher()])
        articles = await fetcher.fetch_all()
        assert len(articles) == 1
        assert fetcher.source_count == 1

    async def test_resilient_to_failure(self):
        """If one fetcher fails, others still return results."""

        class FailingFetcher(DummyNewsApiFetcher):
            async def fetch(self, symbols=None):
                raise ConnectionError("API down")

        fetcher = MultiSourceFetcher(
            fetchers=[FailingFetcher(), DummyRssFetcher()]
        )
        articles = await fetcher.fetch_all()
        assert len(articles) == 1  # only RSS succeeded
