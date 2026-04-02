# mkg/infrastructure/external/real_news_fetcher.py
"""Real news fetcher implementations — RSS feeds and HTTP article scraping.

Uses httpx for HTTP and lxml for XML/HTML parsing.
No external API keys required.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import httpx
from lxml import etree

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30
_DEFAULT_FINANCIAL_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^NSEI&region=IN&lang=en-IN",
    "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best",
]


def get_default_feeds() -> list[dict[str, Any]]:
    """Return the default 12-feed configuration across 5 categories.

    Each feed has: url, category, language, credibility_score.
    Categories: equities, crypto, forex, macro, commodities.
    """
    return [
        # ── Equities ──
        {"url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^NSEI&region=IN&lang=en-IN",
         "category": "equities", "language": "en", "credibility_score": 0.75},
        {"url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best",
         "category": "equities", "language": "en", "credibility_score": 0.95},
        {"url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
         "category": "equities", "language": "en", "credibility_score": 0.72},
        # ── Crypto ──
        {"url": "https://cointelegraph.com/rss",
         "category": "crypto", "language": "en", "credibility_score": 0.65},
        {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
         "category": "crypto", "language": "en", "credibility_score": 0.70},
        # ── Forex ──
        {"url": "https://www.forexfactory.com/rss.php",
         "category": "forex", "language": "en", "credibility_score": 0.68},
        {"url": "https://www.fxstreet.com/rss/news",
         "category": "forex", "language": "en", "credibility_score": 0.65},
        # ── Macro ──
        {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",
         "category": "macro", "language": "en", "credibility_score": 0.80},
        {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
         "category": "macro", "language": "en", "credibility_score": 0.78},
        {"url": "https://www.livemint.com/rss/economy",
         "category": "macro", "language": "en", "credibility_score": 0.70},
        # ── Commodities ──
        {"url": "https://www.kitco.com/rss/gold.xml",
         "category": "commodities", "language": "en", "credibility_score": 0.72},
        {"url": "https://oilprice.com/rss/main",
         "category": "commodities", "language": "en", "credibility_score": 0.65},
    ]


class RSSNewsFetcher:
    """Fetches articles from RSS/Atom feeds using httpx + lxml."""

    def __init__(
        self,
        feed_urls: list[str] | None = None,
        feed_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._feed_urls = feed_urls or [f["url"] for f in get_default_feeds()]
        self._feed_metadata = feed_metadata or {
            f["url"]: f for f in get_default_feeds()
        }
        self._http_get: Callable = self._default_http_get

    def source_name(self) -> str:
        return "rss"

    async def fetch(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        """Fetch articles from all configured RSS feeds."""
        all_articles: list[dict[str, Any]] = []

        for url in self._feed_urls:
            try:
                response = await self._http_get(url, timeout=_DEFAULT_TIMEOUT)
                if response.status_code != 200:
                    logger.warning("RSS feed %s returned %d", url, response.status_code)
                    continue

                articles = self._parse_rss(response.text, url)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning("Failed to fetch RSS feed %s: %s", url, e)

        # Filter by symbols if provided
        if symbols:
            all_articles = [
                a for a in all_articles
                if any(
                    s.lower() in a.get("title", "").lower()
                    or s.lower() in a.get("content", "").lower()
                    for s in symbols
                )
            ]

        return all_articles

    def _parse_rss(self, xml_text: str, feed_url: str) -> list[dict[str, Any]]:
        """Parse RSS XML into article dicts."""
        try:
            root = etree.fromstring(xml_text.encode("utf-8"))
        except etree.XMLSyntaxError:
            logger.warning("Failed to parse RSS XML from %s", feed_url)
            return []

        articles: list[dict[str, Any]] = []

        # Handle RSS 2.0
        for item in root.iter("item"):
            title = self._text(item, "title")
            link = self._text(item, "link")
            description = self._text(item, "description")
            pub_date = self._text(item, "pubDate")

            if not title:
                continue

            articles.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "content": description or "",
                "source": self.source_name(),
                "url": link or feed_url,
                "published_at": pub_date or datetime.now(timezone.utc).isoformat(),
                "metadata": {"feed_url": feed_url},
            })

        # Handle Atom feeds
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title = self._text(entry, "{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
            summary = self._text(entry, "{http://www.w3.org/2005/Atom}summary")

            if not title:
                continue

            articles.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "content": summary or "",
                "source": self.source_name(),
                "url": link,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {"feed_url": feed_url},
            })

        return articles

    @staticmethod
    def _text(element: Any, tag: str) -> str:
        """Get text content of a child element."""
        child = element.find(tag)
        return (child.text or "").strip() if child is not None else ""

    @staticmethod
    async def _default_http_get(url: str, **kwargs: Any) -> Any:
        timeout = kwargs.pop("timeout", _DEFAULT_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.get(url, **kwargs)


class HTTPArticleFetcher:
    """Fetches and extracts article content from a URL using httpx + lxml."""

    def __init__(self) -> None:
        self._http_get: Callable = self._default_http_get

    async def fetch_url(self, url: str) -> Optional[dict[str, Any]]:
        """Fetch and extract article content from a URL."""
        try:
            response = await self._http_get(url, timeout=_DEFAULT_TIMEOUT)
            if response.status_code != 200:
                return None

            return self._extract_article(response.text, url)
        except Exception as e:
            logger.warning("Failed to fetch article from %s: %s", url, e)
            return None

    def _extract_article(self, html: str, url: str) -> dict[str, Any]:
        """Extract title and main content from HTML."""
        try:
            tree = etree.HTML(html)
        except Exception:
            return {
                "id": str(uuid.uuid4()),
                "title": "Unknown",
                "content": html[:2000],
                "source": "http",
                "url": url,
            }

        # Extract title
        title = ""
        for tag in ["//h1", "//title"]:
            elements = tree.xpath(tag)
            if elements:
                title = (elements[0].text or "").strip()
                if title:
                    break

        # Extract main content from article/main/body paragraphs
        paragraphs = []
        for selector in ["//article//p", "//main//p", "//body//p"]:
            elements = tree.xpath(selector)
            if elements:
                paragraphs = [
                    (el.text or "").strip()
                    for el in elements
                    if el.text and el.text.strip()
                ]
                if paragraphs:
                    break

        content = " ".join(paragraphs) if paragraphs else html[:2000]

        return {
            "id": str(uuid.uuid4()),
            "title": title or "Unknown",
            "content": content,
            "source": "http",
            "url": url,
        }

    @staticmethod
    async def _default_http_get(url: str, **kwargs: Any) -> Any:
        timeout = kwargs.pop("timeout", _DEFAULT_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.get(url, **kwargs)


class RealMultiSourceFetcher:
    """Aggregates multiple real news fetchers."""

    def __init__(self, fetchers: list[Any] | None = None) -> None:
        self._fetchers = fetchers or [RSSNewsFetcher()]

    async def fetch_all(
        self, symbols: list[str] | None = None
    ) -> list[dict[str, Any]]:
        all_articles: list[dict[str, Any]] = []
        for fetcher in self._fetchers:
            try:
                articles = await fetcher.fetch(symbols)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(
                    "Fetcher %s failed: %s", type(fetcher).__name__, e
                )
        return all_articles
