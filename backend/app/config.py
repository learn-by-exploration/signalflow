"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SignalFlow application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    api_secret_key: str = ""  # Shared secret between frontend and backend
    allowed_hosts: str = ""  # Comma-separated allowed hosts for production

    # ── Database ──
    database_url: str = ""
    database_url_sync: str = ""

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── AI Engine ──
    anthropic_api_key: str = ""
    monthly_ai_budget_usd: float = 30.0
    claude_model: str = "claude-sonnet-4-20250514"

    # ── Market Data ──
    alpha_vantage_api_key: str = ""
    binance_api_key: str = ""
    binance_secret: str = ""
    coinmarketcap_api_key: str = ""

    # ── Telegram ──
    telegram_bot_token: str = ""
    telegram_default_chat_id: str = ""

    # ── Monitoring ──
    sentry_dsn: str = ""

    # ── Tracked Symbols ──
    tracked_stocks: list[str] = [
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "INFY.NS",
        "ITC.NS",
        "ICICIBANK.NS",
        "KOTAKBANK.NS",
        "LT.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "AXISBANK.NS",
        "WIPRO.NS",
        "HCLTECH.NS",
        "MARUTI.NS",
        "TATAMOTORS.NS",
    ]
    tracked_crypto: list[str] = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "DOTUSDT",
        "AVAXUSDT",
        "MATICUSDT",
    ]
    tracked_forex: list[str] = [
        "USD/INR",
        "EUR/USD",
        "GBP/JPY",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD",
    ]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
