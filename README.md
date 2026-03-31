# SignalFlow AI

**AI-powered trading signal platform** — generates actionable buy/sell/hold signals across Indian Stocks (NSE), Cryptocurrency, and Forex, backed by technical analysis and Claude AI sentiment scoring.

[![Release](https://img.shields.io/badge/release-v1.0.0-purple)](https://github.com/learn-by-exploration/signalflow)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/next.js-14-black)](https://nextjs.org)
[![Tests](https://img.shields.io/badge/tests-480%20passing-green)](backend/tests/)
[![License](https://img.shields.io/badge/license-private-gray)]()

---

## What It Does

SignalFlow AI continuously monitors 31 symbols across three markets and delivers clear trading signals with:

- **Signal Strength scores** (0–100%) combining technical indicators + AI sentiment
- **Entry, target, and stop-loss prices** for every signal (1:2 risk:reward minimum)
- **Plain-English AI reasoning** explaining why each signal was generated
- **Real-time delivery** via web dashboard + Telegram bot
- **Performance tracking** — win rates, average returns, signal history

### Markets Covered

| Market | Symbols | Data Source | Update Frequency |
|--------|---------|-------------|------------------|
| **Indian Stocks** | RELIANCE, TCS, HDFCBANK, INFY + 11 more | yfinance (NSE) | Every 60s (market hours) |
| **Cryptocurrency** | BTC, ETH, SOL, BNB + 6 more | Binance WebSocket | Every 30s (24/7) |
| **Forex** | USD/INR, EUR/USD, GBP/JPY + 3 more | Alpha Vantage | Every 60s (market hours) |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER LAYER                        │
│  ┌─────────────────┐    ┌────────────────────────┐  │
│  │  Next.js 14     │    │  Telegram Bot           │  │
│  │  Dashboard      │◄──►│  /signals /config       │  │
│  │  (Dark Theme)   │    │  Morning & Evening      │  │
│  └────────┬────────┘    └───────────┬────────────┘  │
│           │ WebSocket               │ Bot API        │
├───────────┼─────────────────────────┼────────────────┤
│  ┌──────────────────────────────────────────────┐   │
│  │              FastAPI Backend                   │   │
│  │  REST API (/api/v1) + WebSocket (/ws/signals) │   │
│  │  25 endpoints · Rate limited · Health checked  │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                            │
│  ┌──────────┐ ┌────────────┐ ┌───────────────────┐  │
│  │  Data    │ │ Technical  │ │   AI Engine        │  │
│  │ Ingest   │ │ Analysis   │ │  Claude Sonnet     │  │
│  │ (Celery) │ │ RSI, MACD  │ │  News Sentiment    │  │
│  │ 3 market │ │ Bollinger  │ │  Signal Reasoning  │  │
│  │ fetchers │ │ Vol, SMA   │ │  Daily Briefs      │  │
│  └────┬─────┘ └─────┬──────┘ └────────┬──────────┘  │
│       ▼              ▼                 ▼              │
│  ┌─────────────┐ ┌───────┐ ┌──────────────────┐     │
│  │ PostgreSQL  │ │ Redis │ │ Anthropic Claude  │     │
│  │ TimescaleDB │ │ Cache │ │ ($30/mo budget)   │     │
│  └─────────────┘ └───────┘ └──────────────────┘     │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI · Python 3.11+ · Celery + Redis · SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 + TimescaleDB · Alembic migrations |
| AI | Anthropic Claude (claude-sonnet-4-20250514) |
| Frontend | Next.js 14 (App Router) · TypeScript strict · Tailwind CSS · Zustand |
| Charts | Recharts · Custom SVG sparklines |
| Alerts | python-telegram-bot 20.x |
| Deployment | Docker Compose · Railway |
| Monitoring | Sentry · Structured logging (structlog) |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys (see [.env.example](.env.example))

### Setup

```bash
# 1. Clone the repository
git clone git@github.com:learn-by-exploration/signalflow.git
cd signalflow

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (Anthropic, Alpha Vantage, Telegram, etc.)

# 3. Start everything (build + start + migrate)
make init
```

### Service URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## Development

### Common Commands

```bash
# Docker
make up              # Start all services in background
make down            # Stop all services
make build           # Rebuild Docker images
make logs            # Follow all service logs
make logs-backend    # Follow backend + celery logs only

# Database
make migrate                        # Run pending migrations
make migrate-gen msg="add column"   # Auto-generate new migration
make db-shell                       # Open psql shell

# Testing
make test            # Run all backend tests
make test-cov        # Run tests with coverage report

# Code Quality
make lint            # Lint backend (ruff) + frontend (eslint)
make format          # Format backend (black + ruff fix)

# Local Frontend Dev
make frontend-dev    # Start Next.js dev server (hot reload)
make frontend-install # Install npm dependencies

# Shell Access
make backend-shell   # Bash into backend container
```

### Running Tests Locally (without Docker)

```bash
# Activate virtualenv
source .venv/bin/activate

# Run from backend directory
cd backend
python -m pytest tests/ -v --override-ini="asyncio_mode=auto"
```

### Project Structure

```
signalflow/
├── CLAUDE.md                    # Master project instructions & architecture
├── README.md                    # This file
├── Makefile                     # Development shortcuts
├── docker-compose.yml           # Local dev: all 5 services
├── docker-compose.prod.yml      # Production overrides
├── railway.toml                 # Railway deployment config
├── .env.example                 # Environment variable template
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, health check
│   │   ├── config.py            # Settings (21 env vars, symbol lists)
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # 8 SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── api/                 # 25 REST endpoints + WebSocket
│   │   ├── services/
│   │   │   ├── data_ingestion/  # Stock/crypto/forex fetchers
│   │   │   ├── analysis/        # RSI, MACD, Bollinger, Volume, SMA, ATR
│   │   │   ├── ai_engine/       # Claude sentiment, reasoning, briefs
│   │   │   ├── signal_gen/      # Signal generator, scorer, targets
│   │   │   └── alerts/          # Telegram bot, formatter, dispatcher
│   │   └── tasks/               # 10+ Celery scheduled tasks
│   ├── migrations/              # Alembic (3 migrations)
│   ├── tests/                   # 40 test files, 480+ passing
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # 8 pages (Next.js App Router)
│   │   ├── components/          # 19 React components
│   │   ├── hooks/               # 4 custom hooks (signals, markets, ws, keyboard)
│   │   ├── store/               # 3 Zustand stores
│   │   ├── lib/                 # API client, WebSocket, types, constants
│   │   └── utils/               # Formatters, market hours
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
└── docs/
    ├── design/                  # Spec documents (v1–v4)
    ├── review/                  # Code review findings
    └── api.md                   # API reference
```

---

## API Overview

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|---------|------------|
| GET | `/signals` | List active signals (filter by market, type, confidence) |
| GET | `/signals/{id}` | Signal detail |
| GET | `/signals/history` | Past signals with outcomes |
| GET | `/signals/stats` | Aggregate performance (win rate, avg return) |
| GET | `/markets/overview` | Live market snapshot (stocks, crypto, forex) |
| POST | `/ai/ask` | Ask Claude about a symbol |
| POST | `/backtest` | Run historical backtest |
| GET | `/portfolio/summary` | Portfolio positions and P&L |
| WS | `/ws/signals` | Real-time signal stream |

See [docs/api.md](docs/api.md) for the full API reference with request/response examples.

---

## Signal Generation

### How Signals Are Scored

```
technical_score = weighted_average([
    RSI (14-period)         × 0.20
    MACD                    × 0.25
    Bollinger Bands         × 0.15
    Volume Analysis         × 0.15
    SMA Crossover           × 0.25
])

sentiment_score = Claude AI analysis of recent news

final_confidence = (technical × 0.60) + (sentiment × 0.40)
```

### Signal Thresholds

| Confidence | Signal |
|------------|--------|
| 80–100% | STRONG BUY |
| 65–79% | BUY |
| 36–64% | HOLD |
| 21–35% | SELL |
| 0–20% | STRONG SELL |

### Target & Stop-Loss

- Calculated using ATR (14-period Average True Range)
- **BUY**: Target = price + 2×ATR, Stop = price − 1×ATR
- **SELL**: Target = price − 2×ATR, Stop = price + 1×ATR
- Minimum 1:2 risk:reward ratio enforced

---

## Telegram Bot

Connect via [@YourBotName](https://t.me/YourBotName) (replace with actual bot handle).

| Command | Description |
|---------|------------|
| `/start` | Connect and register |
| `/signals` | Top 5 active signals |
| `/markets` | Quick market snapshot |
| `/config` | Set alert preferences (markets, min confidence) |
| `/history` | Recent signal outcomes |
| `/tutorial` | How to use signals |
| `/stop` / `/resume` | Pause/resume alerts |

### Alert Format

```
🟢 STRONG BUY — HDFCBANK

💰 Price: ₹1,678.90 (+1.42%)
📊 Confidence: ████████░░ 92%

🎯 Target: ₹1,780  |  🛑 Stop: ₹1,630
⏱ Timeframe: 2-4 weeks

🤖 AI: Credit growth accelerating. NIM expansion
confirmed. Strong uptrend continuation likely.
```

---

## Scheduled Tasks

| Task | Frequency | Description |
|------|-----------|-------------|
| Fetch Indian stocks | 60s | OHLCV data via yfinance (market hours only) |
| Fetch crypto | 30s | Binance WebSocket candles (24/7) |
| Fetch forex | 60s | Alpha Vantage rates (forex hours only) |
| Technical analysis | 5 min | RSI, MACD, Bollinger, Volume, SMA for all symbols |
| Sentiment analysis | 1 hour | Claude AI news analysis |
| Signal generation | 5 min | Combine tech + sentiment → signals |
| Signal resolution | 5 min | Check if signals hit target/stop |
| Price alert check | 5 min | Check user-defined price alerts |
| Morning brief | 8:00 AM IST | Daily trading brief via Telegram |
| Evening wrap | 4:00 PM IST | Daily summary via Telegram |
| Weekly digest | Sun 6:00 PM IST | Weekly performance via Telegram |

---

## Database Schema

8 tables on PostgreSQL 16 + TimescaleDB:

| Table | Purpose |
|-------|---------|
| `market_data` | OHLCV time-series (TimescaleDB hypertable) |
| `signals` | Generated signals with technical/sentiment data (JSONB) |
| `signal_history` | Signal outcomes (hit_target, hit_stop, expired) |
| `alert_configs` | User alert preferences (markets, confidence, quiet hours) |
| `price_alerts` | User-defined price thresholds |
| `trades` | Manual trade log (BUY/SELL with P&L tracking) |
| `signal_shares` | Public shareable signal links (7-day expiry) |
| `backtest_runs` | Historical backtesting results |

---

## Environment Variables

See [.env.example](.env.example) for the full template. Required keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection (asyncpg) |
| `REDIS_URL` | Yes | Redis for cache + Celery broker |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI analysis |
| `ALPHA_VANTAGE_API_KEY` | Yes | Forex data (free tier: 5 calls/min) |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot (from @BotFather) |
| `TELEGRAM_DEFAULT_CHAT_ID` | No | Primary user's Telegram chat ID |
| `BINANCE_API_KEY` | No | Optional for public endpoints |
| `SENTRY_DSN` | No | Error monitoring |

---

## Deployment

### Railway (Production)

Configured via [railway.toml](railway.toml):

```bash
# Build
builder = "dockerfile"
dockerfilePath = "backend/Dockerfile"

# Deploy
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

### Docker Compose (Production)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Release History

| Version | Date | Highlights |
|---------|------|-----------|
| **v1.3.51** | 31 Mar 2026 | MKG expert panel review (10 experts, 183 requirements) + System Requirements Document |
| v1.3.50 | 31 Mar 2026 | Final security audit (OWASP Top 10) |
| **v1.0.0** | 21 Mar 2026 | MVP release — full signal pipeline, dashboard, Telegram bot, 480+ tests |
| v0.0.1 | 20 Mar 2026 | Feature-complete with testing and Docker setup |

---

## Contributing

This is a personal project. The codebase uses:

- **Python**: Black formatter, Ruff linter, type hints required
- **TypeScript**: Prettier, ESLint, strict mode, no `any`
- **Git**: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`)
- **Testing**: All tests must pass before commit (`make test`)

See [CLAUDE.md](CLAUDE.md) for complete coding standards and architecture decisions.

---

## Disclaimer

**This is AI-generated analysis, not financial advice.** SignalFlow AI generates signals for educational and informational purposes only. Always do your own research before making investment decisions. Past signal performance does not guarantee future results.

---

*Built with FastAPI, Next.js, Claude AI, and a lot of market data.*
