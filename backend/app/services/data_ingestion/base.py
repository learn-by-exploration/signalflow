"""Abstract base class for all market data fetchers."""

from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    """Base fetcher interface for market data ingestion."""

    @abstractmethod
    def fetch_all(self) -> dict:
        """Fetch data for all tracked symbols.

        Returns:
            Dict with 'count' (int) and 'symbols' (list of fetched symbols).
        """
        ...

    @abstractmethod
    def fetch_symbol(self, symbol: str) -> dict | None:
        """Fetch data for a single symbol.

        Args:
            symbol: The ticker symbol to fetch.

        Returns:
            Dict with OHLCV data, or None if fetch failed.
        """
        ...
