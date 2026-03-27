"""Crypto data fetcher using Binance REST API and CoinGecko fallback."""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.market_data import MarketData
from app.services.data_ingestion.base import BaseFetcher
from app.services.data_ingestion.validators import validate_candle

logger = logging.getLogger(__name__)
settings = get_settings()

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
COINGECKO_SIMPLE_URL = "https://api.coingecko.com/api/v3/simple/price"

# Map Binance pair to CoinGecko ID for fallback
COINGECKO_IDS = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
    "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin",
    "DOTUSDT": "polkadot",
    "AVAXUSDT": "avalanche-2",
    "POLUSDT": "polygon-ecosystem-token",
}


class CryptoFetcher(BaseFetcher):
    """Fetches crypto OHLCV data from Binance REST API with CoinGecko fallback.

    Uses the public klines endpoint (no API key required for basic access).
    """

    def __init__(self, timeframe: str = "1d") -> None:
        self.symbols = settings.tracked_crypto
        self.engine = create_engine(settings.database_url_sync)
        self.timeframe = timeframe
        # Map our timeframe labels to Binance intervals
        self._binance_interval_map = {
            "1d": "1d",
            "4h": "4h",
            "1h": "1h",
        }

    def fetch_all(self) -> dict:
        """Fetch latest candle data for all tracked crypto pairs."""
        fetched_symbols = []

        with Session(self.engine) as session:
            for symbol in self.symbols:
                result = self._fetch_from_binance(symbol)

                if result is None:
                    result = self._fetch_from_coingecko(symbol)

                if result is not None:
                    candle = {
                        "open": result["open"],
                        "high": result["high"],
                        "low": result["low"],
                        "close": result["close"],
                    }
                    valid, err = validate_candle(candle, symbol)
                    if not valid:
                        logger.warning("Invalid candle for %s: %s", symbol, err)
                        continue

                    record = MarketData(
                        symbol=symbol,
                        market_type="crypto",
                        open=Decimal(str(result["open"])),
                        high=Decimal(str(result["high"])),
                        low=Decimal(str(result["low"])),
                        close=Decimal(str(result["close"])),
                        volume=Decimal(str(result["volume"])) if result.get("volume") else None,
                        timeframe=self.timeframe,
                        timestamp=result["timestamp"],
                    )
                    session.merge(record)
                    fetched_symbols.append(symbol)

            session.commit()

        return {"count": len(fetched_symbols), "symbols": fetched_symbols}

    def fetch_symbol(self, symbol: str) -> dict | None:
        """Fetch data for a single crypto symbol."""
        result = self._fetch_from_binance(symbol)
        if result is None:
            result = self._fetch_from_coingecko(symbol)
        return result

    def _fetch_from_binance(self, symbol: str) -> dict | None:
        """Fetch latest kline from Binance public API."""
        try:
            interval = self._binance_interval_map.get(self.timeframe, "1d")
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    BINANCE_KLINES_URL,
                    params={"symbol": symbol, "interval": interval, "limit": 2},
                )
                resp.raise_for_status()
                data = resp.json()

            if not data:
                return None

            # Use last complete candle (second-to-last if 2 returned, first if only 1)
            kline = data[0] if len(data) >= 2 else data[0]
            return {
                "open": kline[1],
                "high": kline[2],
                "low": kline[3],
                "close": kline[4],
                "volume": kline[5],
                "timestamp": datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
            }
        except Exception as e:
            logger.warning(f"Binance fetch failed for {symbol}: {e}")
            return None

    def _fetch_from_coingecko(self, symbol: str) -> dict | None:
        """Fallback: fetch current price from CoinGecko."""
        coin_id = COINGECKO_IDS.get(symbol)
        if not coin_id:
            return None

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    COINGECKO_SIMPLE_URL,
                    params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_vol": "true"},
                )
                resp.raise_for_status()
                data = resp.json()

            if coin_id not in data:
                return None

            price = data[coin_id]["usd"]
            volume = data[coin_id].get("usd_24h_vol", 0)

            # CoinGecko returns only current price, not real OHLCV
            # Mark as spot-only so technical analysis is skipped
            return {
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume,
                "timestamp": datetime.now(timezone.utc),
                "is_spot_only": True,
            }
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed for {symbol}: {e}")
            return None
