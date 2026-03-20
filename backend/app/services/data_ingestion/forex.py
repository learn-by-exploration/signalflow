"""Forex data fetcher using Twelve Data (primary) and Alpha Vantage (fallback).

Twelve Data offers 800 free API calls/day vs Alpha Vantage's reduced 25/day,
making it the better primary source for forex data.
"""

import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.market_data import MarketData
from app.services.data_ingestion.base import BaseFetcher

logger = logging.getLogger(__name__)
settings = get_settings()

TWELVE_DATA_URL = "https://api.twelvedata.com/time_series"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


class ForexFetcher(BaseFetcher):
    """Fetches forex rates from Twelve Data with Alpha Vantage fallback.

    Respects rate limits: Twelve Data (8 calls/min free), Alpha Vantage (5 calls/min).
    """

    def __init__(self) -> None:
        self.symbols = settings.tracked_forex
        self.engine = create_engine(settings.database_url_sync)

    def fetch_all(self) -> dict:
        """Fetch latest data for all tracked forex pairs."""
        fetched_symbols = []

        with Session(self.engine) as session:
            for i, symbol in enumerate(self.symbols):
                result = self._fetch_from_twelve_data(symbol)

                if result is None:
                    result = self._fetch_from_alpha_vantage(symbol)

                if result is not None:
                    record = MarketData(
                        symbol=symbol,
                        market_type="forex",
                        open=Decimal(str(result["open"])),
                        high=Decimal(str(result["high"])),
                        low=Decimal(str(result["low"])),
                        close=Decimal(str(result["close"])),
                        volume=None,
                        timestamp=result["timestamp"],
                    )
                    session.merge(record)
                    fetched_symbols.append(symbol)

                # Rate limit spacing: ~8 sec between calls for Twelve Data free tier
                if i < len(self.symbols) - 1:
                    time.sleep(8)

            session.commit()

        return {"count": len(fetched_symbols), "symbols": fetched_symbols}

    def fetch_symbol(self, symbol: str) -> dict | None:
        """Fetch data for a single forex pair."""
        result = self._fetch_from_twelve_data(symbol)
        if result is None:
            result = self._fetch_from_alpha_vantage(symbol)
        return result

    def _fetch_from_twelve_data(self, symbol: str) -> dict | None:
        """Fetch latest candle from Twelve Data API."""
        try:
            # Twelve Data uses slash format: EUR/USD
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    TWELVE_DATA_URL,
                    params={
                        "symbol": symbol,
                        "interval": "1min",
                        "outputsize": 1,
                        "apikey": settings.alpha_vantage_api_key,  # Shared key or separate
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            if "values" not in data or not data["values"]:
                return None

            candle = data["values"][0]
            return {
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "timestamp": datetime.fromisoformat(candle["datetime"]).replace(
                    tzinfo=timezone.utc
                ),
            }
        except Exception as e:
            logger.warning(f"Twelve Data fetch failed for {symbol}: {e}")
            return None

    def _fetch_from_alpha_vantage(self, symbol: str) -> dict | None:
        """Fallback: fetch from Alpha Vantage FX_INTRADAY."""
        if not settings.alpha_vantage_api_key:
            return None

        try:
            from_currency, to_currency = symbol.split("/")

            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    ALPHA_VANTAGE_URL,
                    params={
                        "function": "FX_INTRADAY",
                        "from_symbol": from_currency,
                        "to_symbol": to_currency,
                        "interval": "1min",
                        "outputsize": "compact",
                        "apikey": settings.alpha_vantage_api_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            ts_key = "Time Series FX (Intraday)"
            if ts_key not in data:
                return None

            latest_ts = sorted(data[ts_key].keys())[-1]
            candle = data[ts_key][latest_ts]

            return {
                "open": candle["1. open"],
                "high": candle["2. high"],
                "low": candle["3. low"],
                "close": candle["4. close"],
                "timestamp": datetime.fromisoformat(latest_ts).replace(tzinfo=timezone.utc),
            }
        except Exception as e:
            logger.warning(f"Alpha Vantage fetch failed for {symbol}: {e}")
            return None
