# Environment Variables Reference

All configuration for SignalFlow AI is managed via environment variables.  
Copy `.env.example` to `.env` and fill in values before starting.

---

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async PostgreSQL connection string. Format: `postgresql+asyncpg://user:pass@host:5432/signalflow` |
| `DATABASE_URL_SYNC` | Yes | — | Sync PostgreSQL connection string (used by data fetchers). Format: `postgresql://user:pass@host:5432/signalflow` |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL for caching and Celery broker |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password (used by Docker Compose) |
| `POSTGRES_USER` | No | `postgres` | PostgreSQL username |
| `POSTGRES_DB` | No | `signalflow` | PostgreSQL database name |
| `REDIS_PASSWORD` | No | — | Redis password (set for production) |

## AI Engine

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | — | Anthropic API key for Claude. Starts with `sk-ant-`. *System functions without it but AI features disabled. |
| `MONTHLY_AI_BUDGET_USD` | No | `30` | Monthly spending cap for Claude API calls in USD |

## Market Data

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALPHA_VANTAGE_API_KEY` | No | — | Alpha Vantage API key for forex fallback. Free tier: 25 calls/day |
| `BINANCE_API_KEY` | No | — | Binance API key. Optional — public endpoints used by default |
| `BINANCE_SECRET` | No | — | Binance API secret |
| `COINMARKETCAP_API_KEY` | No | — | CoinMarketCap API key for crypto metadata |

## Telegram Alerts

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes* | — | Bot token from @BotFather. *Required for Telegram alerts. |
| `TELEGRAM_DEFAULT_CHAT_ID` | No | — | Primary user's Telegram chat ID for direct alerts |

## Monitoring

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | No | — | Sentry DSN for error tracking. Recommended for production |

## Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | `development` or `production`. Controls CORS, logging, debug mode |
| `LOG_LEVEL` | No | `INFO` | Python logging level: DEBUG, INFO, WARNING, ERROR |
| `API_HOST` | No | `0.0.0.0` | Backend API bind address |
| `API_PORT` | No | `8000` | Backend API port |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for CORS origin |
| `ALLOWED_HOSTS` | No | — | Comma-separated allowed hosts for production CORS |

## Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_SECRET_KEY` | Yes | — | Shared secret for API key auth. Generate: `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | Yes | — | JWT signing key. Generate: `openssl rand -base64 64` |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime in days |

## Frontend Auth (NextAuth)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXTAUTH_SECRET` | Yes | — | NextAuth.js encryption secret. Generate: `openssl rand -base64 32` |
| `ADMIN_EMAIL` | No | `admin@signalflow.ai` | Admin user email for seeding |
| `ADMIN_PASSWORD` | No | — | Admin user password |
| `DEMO_EMAIL` | No | `demo@signalflow.ai` | Demo account email |
| `DEMO_PASSWORD` | No | — | Demo account password |

---

## Environment-Specific Notes

### Development
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/signalflow
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000
```

### Production (Railway)
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://... (Railway provisioned)
REDIS_URL=redis://... (Railway provisioned)
FRONTEND_URL=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
SENTRY_DSN=https://...@sentry.io/...
```

### Generating Secrets
```bash
# API secret key
openssl rand -base64 32

# JWT secret key (longer for security)
openssl rand -base64 64

# NextAuth secret
openssl rand -base64 32
```
