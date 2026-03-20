"""Shared analysis utilities."""

import pandas as pd


def ensure_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase ohlcv standard.

    Handles common variations like 'Close' → 'close', 'Vol' → 'volume'.
    """
    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Vol": "volume",
        "Adj Close": "adj_close",
    }
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
