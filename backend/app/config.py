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
    internal_api_key: str = ""  # Internal-only key for Celery/bot calls (separate from user-facing)
    allowed_hosts: str = ""  # Comma-separated allowed hosts for production
    max_request_body_bytes: int = 1_048_576  # 1MB default max payload size

    # ── JWT Auth ──
    jwt_secret_key: str = ""  # HMAC signing key for JWT tokens
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

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

    # ── Payments (Razorpay) ──
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_monthly_plan_id: str = ""  # Razorpay Plan ID for ₹499/mo
    razorpay_annual_plan_id: str = ""   # Razorpay Plan ID for ₹4999/yr
    pro_trial_days: int = 7             # 7-day free Pro trial
    payment_grace_days: int = 3         # Grace period before downgrade on failed payment

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

    # ── Sector Map (for portfolio risk controls) ──
    sector_map: dict[str, str] = {
        "HDFCBANK.NS": "banking", "ICICIBANK.NS": "banking", "SBIN.NS": "banking",
        "KOTAKBANK.NS": "banking", "AXISBANK.NS": "banking",
        "TCS.NS": "it", "INFY.NS": "it", "WIPRO.NS": "it", "HCLTECH.NS": "it",
        "RELIANCE.NS": "energy", "ITC.NS": "fmcg",
        "BHARTIARTL.NS": "telecom", "MARUTI.NS": "auto", "TATAMOTORS.NS": "auto",
        "LT.NS": "infra",
    }

    # ── Risk Limits ──
    max_concurrent_per_sector: int = 2
    max_concurrent_per_market: int = 5
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
        "POLUSDT",
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
