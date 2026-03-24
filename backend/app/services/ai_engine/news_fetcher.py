"""News fetcher for AI sentiment analysis.

Fetches news headlines from multiple free sources:
1. Google News RSS (primary)
2. Bing News RSS (fallback)
3. Financial RSS feeds for Indian markets

Returns cleaned article headlines for Claude sentiment scoring.
"""

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Timeout for all HTTP requests
REQUEST_TIMEOUT = 10.0
# Maximum response size (5 MB) — prevent DoS from oversized responses
MAX_RESPONSE_SIZE = 5 * 1024 * 1024

# Market-specific financial RSS feeds
FINANCIAL_RSS_FEEDS: dict[str, list[str]] = {
    "stock": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/marketreports.xml",
    ],
    "crypto": [
        "https://cointelegraph.com/rss",
    ],
    "forex": [
        "https://www.forexlive.com/feed",
    ],
}


def _parse_rss_titles(xml_text: str) -> list[str]:
    """Extract article titles from RSS/Atom XML using regex.

    Handles both CDATA-wrapped and plain <title> tags,
    plus <entry><title> for Atom feeds.
    """
    # Try CDATA first
    items = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml_text, re.DOTALL)
    if not items:
        # Plain title tags inside <item> or <entry>
        items = re.findall(r"<item>.*?<title>(.*?)</title>", xml_text, re.DOTALL)
    if not items:
        items = re.findall(r"<entry>.*?<title>(.*?)</title>", xml_text, re.DOTALL)
    if not items:
        # Fallback: all <title> tags except the first (feed title)
        items = re.findall(r"<title>(.*?)</title>", xml_text)
        items = items[1:] if len(items) > 1 else items

    # Clean HTML entities
    cleaned = []
    for item in items:
        text = item.strip()
        text = re.sub(r"<[^>]+>", "", text)  # strip any inner HTML
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&#39;", "'").replace("&quot;", '"')
        if text and len(text) > 10:
            cleaned.append(text)

    return cleaned


async def fetch_google_news(query: str, max_articles: int = 10) -> list[str]:
    """Fetch news headlines from Google News RSS.

    Args:
        query: Search query string.
        max_articles: Maximum number of articles to return.

    Returns:
        List of headline strings.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                "https://news.google.com/rss/search",
                params={"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
            )
            resp.raise_for_status()
            if len(resp.content) > MAX_RESPONSE_SIZE:
                logger.warning("Google News response too large: %d bytes", len(resp.content))
                return []
            return _parse_rss_titles(resp.text)[:max_articles]
    except Exception:
        logger.debug("Google News RSS failed for query: %s", query)
        return []


async def fetch_bing_news(query: str, max_articles: int = 10) -> list[str]:
    """Fetch news headlines from Bing News RSS (fallback).

    Args:
        query: Search query string.
        max_articles: Maximum number of articles to return.

    Returns:
        List of headline strings.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                "https://www.bing.com/news/search",
                params={"q": query, "format": "rss"},
            )
            resp.raise_for_status()
            if len(resp.content) > MAX_RESPONSE_SIZE:
                logger.warning("Bing News response too large: %d bytes", len(resp.content))
                return []
            return _parse_rss_titles(resp.text)[:max_articles]
    except Exception:
        logger.debug("Bing News RSS failed for query: %s", query)
        return []


async def fetch_financial_rss(market_type: str, max_articles: int = 5) -> list[str]:
    """Fetch general market news from financial RSS feeds.

    Args:
        market_type: One of 'stock', 'crypto', 'forex'.
        max_articles: Maximum articles per feed.

    Returns:
        List of headline strings.
    """
    feeds = FINANCIAL_RSS_FEEDS.get(market_type, [])
    all_articles: list[str] = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for feed_url in feeds:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                if len(resp.content) > MAX_RESPONSE_SIZE:
                    logger.warning("RSS feed too large: %s (%d bytes)", feed_url, len(resp.content))
                    continue
                articles = _parse_rss_titles(resp.text)
                all_articles.extend(articles[:max_articles])
            except Exception:
                logger.debug("Financial RSS failed: %s", feed_url)
                continue

    return all_articles


def _build_search_query(symbol: str, market_type: str) -> str:
    """Build a search query from symbol and market type."""
    clean = symbol.replace(".NS", "").replace("USDT", "").replace("/", " ")

    queries = {
        "stock": f"{clean} NSE stock India market",
        "crypto": f"{clean} cryptocurrency price news",
        "forex": f"{symbol} forex exchange rate news",
    }
    return queries.get(market_type, f"{clean} market news")


async def fetch_news_for_symbol(
    symbol: str, market_type: str, max_articles: int = 10
) -> list[str]:
    """Fetch news articles for a specific symbol from multiple sources.

    Tries Google News first, falls back to Bing, supplements with
    market-specific financial RSS feeds.

    Args:
        symbol: Market symbol (e.g., RELIANCE.NS, BTCUSDT, EUR/USD).
        market_type: One of 'stock', 'crypto', 'forex'.
        max_articles: Maximum total articles to return.

    Returns:
        Deduplicated list of news headline strings.
    """
    query = _build_search_query(symbol, market_type)
    articles: list[str] = []

    # Primary: Google News
    google_articles = await fetch_google_news(query, max_articles)
    articles.extend(google_articles)

    # Fallback: Bing News (only if Google returned few results)
    if len(articles) < 3:
        bing_articles = await fetch_bing_news(query, max_articles)
        articles.extend(bing_articles)

    # Supplement: Market-specific financial RSS
    if len(articles) < max_articles:
        rss_articles = await fetch_financial_rss(market_type, max_articles=5)
        articles.extend(rss_articles)

    # Deduplicate (by lowercase normalized text)
    seen: set[str] = set()
    unique: list[str] = []
    for article in articles:
        key = article.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(article)

    return unique[:max_articles]
