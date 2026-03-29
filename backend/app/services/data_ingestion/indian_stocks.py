"""Indian stock data fetcher using yfinance."""

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from datetime import timezone
from decimal import Decimal

import yfinance as yf
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.market_data import MarketData
from app.services.data_ingestion.base import BaseFetcher
from app.services.data_ingestion.db import get_sync_engine
from app.services.data_ingestion.validators import validate_candle

logger = logging.getLogger(__name__)
settings = get_settings()

# Timeout for yfinance downloads (seconds)
YFINANCE_TIMEOUT = 30


class IndianStockFetcher(BaseFetcher):
    """Fetches OHLCV data for Indian stocks (NSE) via yfinance.

    Uses batch download to minimize API calls. Stores data in market_data table.
    """

    def __init__(self) -> None:
        self.symbols = settings.tracked_stocks
        self.engine = get_sync_engine()

    def fetch_all(self) -> dict:
        """Fetch latest 1-day candle for all tracked Indian stocks in a single batch."""
        fetched_symbols = []

        try:
            # Batch download with timeout — single API call for all symbols
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    yf.download,
                    tickers=self.symbols,
                    period="1d",
                    interval="1m",
                    group_by="ticker",
                    progress=False,
                    threads=True,
                )
                try:
                    data = future.result(timeout=YFINANCE_TIMEOUT)
                except FuturesTimeout:
                    logger.error("yfinance download timed out after %ds", YFINANCE_TIMEOUT)
                    return {"count": 0, "symbols": self.symbols, "error": "timeout"}

            if data.empty:
                logger.warning("yfinance returned empty data for Indian stocks")
                return {"count": 0, "symbols": []}

            with Session(self.engine) as session:
                for symbol in self.symbols:
                    try:
                        if len(self.symbols) > 1:
                            symbol_data = data[symbol].dropna()
                        else:
                            symbol_data = data.dropna()

                        if symbol_data.empty:
                            continue

                        # Take the latest row
                        latest = symbol_data.iloc[-1]
                        ts = symbol_data.index[-1]

                        candle = {
                            "open": latest["Open"],
                            "high": latest["High"],
                            "low": latest["Low"],
                            "close": latest["Close"],
                        }
                        valid, err = validate_candle(candle, symbol)
                        if not valid:
                            logger.warning("Invalid candle for %s: %s", symbol, err)
                            continue

                        record = MarketData(
                            symbol=symbol.replace(".NS", ""),
                            market_type="stock",
                            open=Decimal(str(latest["Open"])),
                            high=Decimal(str(latest["High"])),
                            low=Decimal(str(latest["Low"])),
                            close=Decimal(str(latest["Close"])),
                            volume=Decimal(str(latest["Volume"])) if latest["Volume"] else None,
                            timestamp=ts.to_pydatetime().replace(tzinfo=timezone.utc),
                        )
                        session.merge(record)
                        fetched_symbols.append(symbol)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue

                session.commit()

        except Exception as e:
            logger.error(f"Failed to fetch Indian stocks: {e}")
            return {"count": 0, "symbols": [], "error": str(e)}

        return {"count": len(fetched_symbols), "symbols": fetched_symbols}

    def fetch_symbol(self, symbol: str) -> dict | None:
        """Fetch data for a single Indian stock symbol."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            return {
                "symbol": symbol.replace(".NS", ""),
                "open": str(latest["Open"]),
                "high": str(latest["High"]),
                "low": str(latest["Low"]),
                "close": str(latest["Close"]),
                "volume": str(latest["Volume"]),
                "timestamp": hist.index[-1].isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            return None
