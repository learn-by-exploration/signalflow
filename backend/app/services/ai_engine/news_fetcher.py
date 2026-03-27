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
        "https://www.livemint.com/rss/markets",
    ],
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ],
    "forex": [
        "https://www.forexlive.com/feed",
        "https://www.fxstreet.com/rss",
    ],
}

# Central bank and institutional feeds (highest quality, free)
CENTRAL_BANK_FEEDS: list[str] = [
    "https://www.rbi.org.in/pressreleases_rss.xml",
    "https://www.federalreserve.gov/feeds/press_all.xml",
]

# Source quality weights for credibility scoring
SOURCE_WEIGHTS: dict[str, float] = {
    "rbi.org.in": 1.0,
    "federalreserve.gov": 1.0,
    "reuters": 0.95,
    "economictimes": 0.80,
    "livemint": 0.80,
    "moneycontrol": 0.65,
    "coindesk": 0.80,
    "cointelegraph": 0.70,
    "forexlive": 0.75,
    "fxstreet": 0.70,
    "google": 0.50,
    "bing": 0.45,
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


def _parse_rss_items(xml_text: str, source_name: str = "unknown") -> list[dict[str, str]]:
    """Extract structured article data from RSS XML.

    Returns list of dicts with: headline, source, source_url, published_at.
    """
    items: list[dict[str, str]] = []

    # Extract items with their metadata
    item_blocks = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    if not item_blocks:
        item_blocks = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)

    for block in item_blocks:
        # Title
        title_match = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", block, re.DOTALL)
        if not title_match:
            title_match = re.search(r"<title>(.*?)</title>", block, re.DOTALL)
        if not title_match:
            continue

        title = title_match.group(1).strip()
        title = re.sub(r"<[^>]+>", "", title)
        title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        title = title.replace("&#39;", "'").replace("&quot;", '"')

        if not title or len(title) < 10:
            continue

        # Link
        link_match = re.search(r"<link>(.*?)</link>", block)
        if not link_match:
            link_match = re.search(r'<link[^>]*href="([^"]*)"', block)
        link = link_match.group(1).strip() if link_match else None

        # Published date
        pub_match = re.search(r"<pubDate>(.*?)</pubDate>", block)
        if not pub_match:
            pub_match = re.search(r"<published>(.*?)</published>", block)
        if not pub_match:
            pub_match = re.search(r"<updated>(.*?)</updated>", block)
        pub_date = pub_match.group(1).strip() if pub_match else None

        items.append({
            "headline": title,
            "source": source_name,
            "source_url": link,
            "published_at": pub_date,
        })

    # Fallback: just titles
    if not items:
        titles = _parse_rss_titles(xml_text)
        for t in titles:
            items.append({"headline": t, "source": source_name, "source_url": None, "published_at": None})

    return items


async def fetch_google_news(query: str, max_articles: int = 10) -> list[dict[str, str]]:
    """Fetch news headlines from Google News RSS.

    Args:
        query: Search query string.
        max_articles: Maximum number of articles to return.

    Returns:
        List of article dicts with headline, source, source_url, published_at.
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
            return _parse_rss_items(resp.text, "google_news")[:max_articles]
    except Exception:
        logger.debug("Google News RSS failed for query: %s", query)
        return []


async def fetch_bing_news(query: str, max_articles: int = 10) -> list[dict[str, str]]:
    """Fetch news headlines from Bing News RSS (fallback).

    Args:
        query: Search query string.
        max_articles: Maximum number of articles to return.

    Returns:
        List of article dicts with headline, source, source_url, published_at.
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
            return _parse_rss_items(resp.text, "bing_news")[:max_articles]
    except Exception:
        logger.debug("Bing News RSS failed for query: %s", query)
        return []


async def fetch_financial_rss(market_type: str, max_articles: int = 5) -> list[dict[str, str]]:
    """Fetch general market news from financial RSS feeds.

    Args:
        market_type: One of 'stock', 'crypto', 'forex'.
        max_articles: Maximum articles per feed.

    Returns:
        List of article dicts.
    """
    feeds = FINANCIAL_RSS_FEEDS.get(market_type, [])
    all_articles: list[dict[str, str]] = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for feed_url in feeds:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                if len(resp.content) > MAX_RESPONSE_SIZE:
                    logger.warning("RSS feed too large: %s (%d bytes)", feed_url, len(resp.content))
                    continue
                # Infer source name from URL
                source = _infer_source_name(feed_url)
                articles = _parse_rss_items(resp.text, source)
                all_articles.extend(articles[:max_articles])
            except Exception:
                logger.debug("Financial RSS failed: %s", feed_url)
                continue

    return all_articles


async def fetch_central_bank_news(max_articles: int = 5) -> list[dict[str, str]]:
    """Fetch news from central bank RSS feeds (RBI, Fed, ECB).

    These are highest-quality sources for macro policy events.

    Returns:
        List of article dicts.
    """
    all_articles: list[dict[str, str]] = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for feed_url in CENTRAL_BANK_FEEDS:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                if len(resp.content) > MAX_RESPONSE_SIZE:
                    continue
                source = _infer_source_name(feed_url)
                articles = _parse_rss_items(resp.text, source)
                all_articles.extend(articles[:max_articles])
            except Exception:
                logger.debug("Central bank RSS failed: %s", feed_url)
                continue

    return all_articles


def _infer_source_name(url: str) -> str:
    """Infer a human-readable source name from a URL."""
    if "rbi.org.in" in url:
        return "RBI"
    if "federalreserve.gov" in url:
        return "US Federal Reserve"
    if "economictimes" in url:
        return "Economic Times"
    if "moneycontrol" in url:
        return "Moneycontrol"
    if "livemint" in url:
        return "LiveMint"
    if "cointelegraph" in url:
        return "CoinTelegraph"
    if "coindesk" in url:
        return "CoinDesk"
    if "forexlive" in url:
        return "ForexLive"
    if "fxstreet" in url:
        return "FXStreet"
    return "Financial News"


def get_source_weight(source: str) -> float:
    """Get credibility weight for a news source."""
    source_lower = source.lower()
    for key, weight in SOURCE_WEIGHTS.items():
        if key in source_lower:
            return weight
    return 0.50


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
    market-specific financial RSS feeds and central bank feeds.

    Args:
        symbol: Market symbol (e.g., RELIANCE.NS, BTCUSDT, EUR/USD).
        market_type: One of 'stock', 'crypto', 'forex'.
        max_articles: Maximum total articles to return.

    Returns:
        Deduplicated list of news headline strings (backward compatible).
    """
    structured = await fetch_news_for_symbol_structured(symbol, market_type, max_articles)
    return [a["headline"] for a in structured]


async def fetch_news_for_symbol_structured(
    symbol: str, market_type: str, max_articles: int = 10
) -> list[dict[str, str]]:
    """Fetch news articles with full metadata for a specific symbol.

    Returns structured article dicts with headline, source, source_url, published_at.
    """
    query = _build_search_query(symbol, market_type)
    articles: list[dict[str, str]] = []

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

    # Supplement: Central bank feeds (for stocks and forex)
    if market_type in ("stock", "forex") and len(articles) < max_articles:
        cb_articles = await fetch_central_bank_news(max_articles=3)
        articles.extend(cb_articles)

    # Deduplicate (by lowercase normalized headline)
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for article in articles:
        key = article["headline"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(article)

    # Semantic deduplication (removes near-duplicate articles)
    from app.services.ai_engine.dedup import deduplicate_articles
    unique = deduplicate_articles(unique)

    return unique[:max_articles]
