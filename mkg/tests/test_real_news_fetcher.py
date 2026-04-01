# mkg/tests/test_real_news_fetcher.py
"""Tests for real news fetcher implementations (RSS + HTTP).

Iterations 16-20: Real news fetching with mocked HTTP responses.
All tests mock httpx — no real network calls.
"""

import pytest


class _MockResponse:
    """Mock httpx.Response."""

    def __init__(self, status_code: int, text: str = "", content: bytes = b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Financial News</title>
    <item>
      <title>TSMC Reports Record Revenue in Q3 2026</title>
      <link>https://news.example.com/tsmc-q3-2026</link>
      <description>TSMC posted record quarterly revenue driven by AI chip demand from NVIDIA and Apple.</description>
      <pubDate>Tue, 01 Apr 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Samsung Warns of Memory Chip Oversupply</title>
      <link>https://news.example.com/samsung-oversupply</link>
      <description>Samsung Electronics warned that DRAM oversupply could hurt margins in H2 2026.</description>
      <pubDate>Mon, 31 Mar 2026 14:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

_SAMPLE_HTML = """<html>
<head><title>NVIDIA Supply Chain Update</title></head>
<body>
<article>
<h1>NVIDIA Supply Chain Update</h1>
<p>NVIDIA has diversified its supply chain to include TSMC and Samsung foundries.</p>
<p>The move comes as demand for AI GPUs continues to surge.</p>
</article>
</body>
</html>"""


class TestRSSNewsFetcher:

    @pytest.fixture
    def fetcher(self):
        from mkg.infrastructure.external.real_news_fetcher import RSSNewsFetcher
        return RSSNewsFetcher(feed_urls=["https://example.com/feed.xml"])

    @pytest.mark.asyncio
    async def test_fetches_articles_from_rss(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        fetcher._http_get = mock_get
        articles = await fetcher.fetch()
        assert len(articles) == 2
        assert articles[0]["title"] == "TSMC Reports Record Revenue in Q3 2026"
        assert articles[0]["source"] == "rss"
        assert articles[0]["url"] == "https://news.example.com/tsmc-q3-2026"

    @pytest.mark.asyncio
    async def test_rss_articles_have_required_fields(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        fetcher._http_get = mock_get
        articles = await fetcher.fetch()
        for art in articles:
            assert "id" in art
            assert "title" in art
            assert "content" in art
            assert "source" in art
            assert "url" in art
            assert "published_at" in art

    @pytest.mark.asyncio
    async def test_rss_handles_http_failure(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(500, text="Internal Server Error")

        fetcher._http_get = mock_get
        articles = await fetcher.fetch()
        assert articles == []

    @pytest.mark.asyncio
    async def test_rss_handles_malformed_xml(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text="not xml at all")

        fetcher._http_get = mock_get
        articles = await fetcher.fetch()
        assert articles == []

    @pytest.mark.asyncio
    async def test_rss_filters_by_symbols(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        fetcher._http_get = mock_get
        articles = await fetcher.fetch(symbols=["TSMC"])
        assert len(articles) >= 1
        assert all("TSMC" in a["title"] or "TSMC" in a["content"] for a in articles)

    @pytest.mark.asyncio
    async def test_rss_multiple_feeds(self):
        from mkg.infrastructure.external.real_news_fetcher import RSSNewsFetcher
        fetcher = RSSNewsFetcher(feed_urls=[
            "https://example.com/feed1.xml",
            "https://example.com/feed2.xml",
        ])

        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        fetcher._http_get = mock_get
        articles = await fetcher.fetch()
        assert len(articles) == 4  # 2 per feed × 2 feeds


class TestHTTPArticleFetcher:

    @pytest.fixture
    def fetcher(self):
        from mkg.infrastructure.external.real_news_fetcher import HTTPArticleFetcher
        return HTTPArticleFetcher()

    @pytest.mark.asyncio
    async def test_fetches_article_from_url(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_HTML)

        fetcher._http_get = mock_get
        article = await fetcher.fetch_url("https://example.com/article")
        assert article is not None
        assert "NVIDIA" in article["title"]
        assert "supply chain" in article["content"].lower()

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(404, text="Not Found")

        fetcher._http_get = mock_get
        result = await fetcher.fetch_url("https://example.com/missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_article_has_required_fields(self, fetcher):
        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_HTML)

        fetcher._http_get = mock_get
        article = await fetcher.fetch_url("https://example.com/article")
        assert article is not None
        for field in ("id", "title", "content", "source", "url"):
            assert field in article


class TestRealMultiSourceFetcher:

    @pytest.mark.asyncio
    async def test_aggregates_multiple_sources(self):
        from mkg.infrastructure.external.real_news_fetcher import (
            RSSNewsFetcher,
            RealMultiSourceFetcher,
        )

        rss = RSSNewsFetcher(feed_urls=["https://example.com/feed.xml"])

        async def mock_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        rss._http_get = mock_get

        multi = RealMultiSourceFetcher(fetchers=[rss])
        articles = await multi.fetch_all()
        assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_aggregation_handles_partial_failure(self):
        from mkg.infrastructure.external.real_news_fetcher import (
            RSSNewsFetcher,
            RealMultiSourceFetcher,
        )

        good_rss = RSSNewsFetcher(feed_urls=["https://good.example.com/feed.xml"])
        bad_rss = RSSNewsFetcher(feed_urls=["https://bad.example.com/feed.xml"])

        async def good_get(url, **kwargs):
            return _MockResponse(200, text=_SAMPLE_RSS)

        async def bad_get(url, **kwargs):
            raise Exception("Connection refused")

        good_rss._http_get = good_get
        bad_rss._http_get = bad_get

        multi = RealMultiSourceFetcher(fetchers=[good_rss, bad_rss])
        articles = await multi.fetch_all()
        assert len(articles) == 2  # Good feed's articles still returned
