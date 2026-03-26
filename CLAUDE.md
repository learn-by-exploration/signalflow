# SignalFlow AI — Master Project Instructions

> **This file is the single source of truth for every Claude Code session and every Ruflo agent working on this project. Read it fully before writing any code.**

---

## Project Overview

**SignalFlow AI** is a personal, AI-powered trading signal platform that runs 24/7 and delivers actionable buy/sell/hold signals across three markets:

- **Indian Stocks** (NSE/BSE) — NIFTY 50 constituents and key mid-caps
- **Cryptocurrency** — BTC, ETH, SOL, and top 10 by market cap
- **Forex** — USD/INR, EUR/USD, GBP/JPY, and major pairs

### The User

The primary user is a **finance professional with an M.Com degree** who is beginning her active trading journey. She has strong theoretical knowledge but limited hands-on trading experience. Every feature must:

- Be **clear** — no jargon-heavy output; plain-English AI explanations
- Be **actionable** — every signal has entry, target, stop-loss, and timeframe
- Be **trustworthy** — confidence scores, transparent reasoning, full signal history
- Be **respectful of her time** — smart alerts, not noisy spam
- **Teach as it helps** — each signal is a learning opportunity

### Core Promise

Transform raw market noise into clear, actionable signals — backed by AI reasoning she can trust, understand, and learn from.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER LAYER                        │
│  ┌─────────────────┐    ┌────────────────────────┐  │
│  │  Next.js 14     │    │  Telegram Bot           │  │
│  │  Dashboard      │◄──►│  Alerts + Digests       │  │
│  │  (Dark Theme)   │    │  /start /signals /config │  │
│  └────────┬────────┘    └───────────┬────────────┘  │
│           │ WebSocket               │ Bot API        │
├───────────┼─────────────────────────┼────────────────┤
│           ▼                         ▼                │
│  ┌──────────────────────────────────────────────┐   │
│  │              FastAPI Backend                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ REST API │ │WebSocket │ │ Celery Tasks  │  │   │
│  │  │ /signals │ │ /ws/     │ │ Beat Schedule │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                            │
├─────────────────────────┼────────────────────────────┤
│                    SERVICE LAYER                      │
│  ┌──────────┐ ┌────────────┐ ┌───────────────────┐  │
│  │  Data    │ │ Technical  │ │   AI Engine        │  │
│  │ Ingest   │ │ Analysis   │ │  (Claude Sonnet)   │  │
│  │ ─────── │ │ ─────────  │ │  ──────────────    │  │
│  │ Stocks   │ │ RSI, MACD  │ │  News Sentiment    │  │
│  │ Crypto   │ │ Bollinger  │ │  Signal Reasoning  │  │
│  │ Forex    │ │ Volume,SMA │ │  Market Briefs     │  │
│  └────┬─────┘ └─────┬──────┘ └────────┬──────────┘  │
│       │              │                 │              │
│       ▼              ▼                 ▼              │
│  ┌─────────────┐ ┌───────┐ ┌──────────────────┐     │
│  │ Signal Gen  │ │ Redis │ │ Anthropic Claude  │     │
│  │ Algorithm   │ │ Cache │ │ API (Sonnet)      │     │
│  └──────┬──────┘ └───────┘ └──────────────────┘     │
│         │                                            │
│         ▼                                            │
│  ┌──────────────────────────────────┐                │
│  │  PostgreSQL + TimescaleDB        │                │
│  │  market_data | signals | alerts  │                │
│  └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend Framework | FastAPI | Latest (0.115+) |
| Language (Backend) | Python | 3.11+ |
| Task Queue | Celery + Redis | Celery 5.x |
| Database | PostgreSQL + TimescaleDB | PG 16, TS 2.x |
| Cache / PubSub | Redis | 7.x |
| AI Engine | Anthropic Claude API | claude-sonnet-4-20250514 |
| Frontend Framework | Next.js | 14.x (App Router) |
| Language (Frontend) | TypeScript | 5.x (strict mode) |
| Styling | Tailwind CSS | 3.x |
| State Management | Zustand | 4.x |
| Charts | Recharts + Lightweight Charts | Latest |
| Real-time | WebSocket (native FastAPI + client) | — |
| Alerts | python-telegram-bot | 20.x |
| Hosting | Railway | — |
| Monitoring | UptimeRobot + Sentry | — |

---

## Development Methodology

This project was built using **Claude Code** (Anthropic's AI coding agent) as the primary development engine. The developer acts as the **architect and orchestrator**, directing Claude through phased development.

### Workflow

1. **Architecture-first**: This CLAUDE.md serves as the master spec. All implementation follows the architecture defined here.
2. **Phase-based development**: Built in 5 phases (Foundation → Analysis → Dashboard → Integration → Polish), plus 10 iterative sprints.
3. **Test-driven**: Every feature includes tests. 480+ tests pass before each commit.
4. **Review cycles**: Multi-expert AI reviews (architect, UI experts, finance professionals, PMs) were used for UI iteration rounds.

### Development Commands

```bash
# Start all services
make init          # Build + start + migrate (first time)
make up            # Start services
make down          # Stop services

# Development
make test          # Run backend test suite
make lint          # Lint backend + frontend
make format        # Auto-format backend code
make logs          # Follow all logs
make backend-shell # Shell into backend container
make db-shell      # PostgreSQL interactive shell

# Database
make migrate                        # Apply migrations
make migrate-gen msg="description"  # Generate new migration

# Frontend
make frontend-dev     # Start Next.js dev server
make frontend-install # Install npm dependencies
```

### Pre-Commit Testing Rule (MANDATORY)

**Before every git commit, ALL existing tests must pass.** This is non-negotiable:

1. Run the full test suite before staging/committing any changes
2. If any existing test fails, fix before committing
3. New code must include corresponding tests
4. **Backend test command**: `python -m pytest tests/ -v --override-ini="asyncio_mode=auto"` (from `backend/` directory)
5. **Frontend test command**: `npx vitest run` (from `frontend/` directory)
6. **Docker build verification**: `docker compose build` must succeed — no TypeScript compilation errors, no broken imports
7. **Minimum bar**: All tests green (0 failures) AND Docker build clean before any commit

### Pre-Tag / Release Gate (MANDATORY)

**Before creating any git tag or version release, the FULL system must be verified end-to-end.** This is non-negotiable:

1. **All backend tests pass**: `python -m pytest tests/ -v --override-ini="asyncio_mode=auto"`
2. **All frontend tests pass**: `npx vitest run`
3. **Docker build succeeds**: `docker compose build` — all 5 services (db, redis, backend, celery, frontend) must build without errors
4. **Docker run verification**: `docker compose up -d` — all services must start and reach healthy state
5. **Health check passes**: `curl http://localhost:8000/health` returns 200
6. **Frontend loads**: `curl http://localhost:3000` returns 200
7. **Clean shutdown**: `docker compose down` after verification
8. **Never tag a broken build** — if any step above fails, fix it before tagging
9. **Tag command**: Only after all checks pass: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`

---

## Project Structure (as of v1.0.0)

```
signalflow/
├── CLAUDE.md                        # THIS FILE — master instructions
├── README.md                        # Project readme with setup guide
├── Makefile                         # Development shortcuts (make up/test/lint)
├── docker-compose.yml               # Local dev: 5 services
├── docker-compose.prod.yml          # Production overrides
├── railway.toml                     # Railway PaaS deployment config
├── start.sh                         # Service bootstrap script
├── .env.example                     # 19 environment variables template
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, health endpoint, rate limiting
│   │   ├── config.py                # Settings: 21 env vars + 31 tracked symbols
│   │   ├── database.py              # SQLAlchemy async (pool=20, overflow=10)
│   │   ├── rate_limit.py            # Slowapi rate limiting config
│   │   │
│   │   ├── models/                  # 8 SQLAlchemy ORM models
│   │   │   ├── market_data.py       # TimescaleDB hypertable (OHLCV)
│   │   │   ├── signal.py            # Signal + SignalHistory
│   │   │   ├── alert_config.py      # Alert preferences + watchlist
│   │   │   └── p3_models.py         # PriceAlert, Trade, SignalShare, BacktestRun
│   │   │
│   │   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   │   ├── signal.py            # Signal, History, Stats, TrackRecord, WeeklyTrend
│   │   │   ├── market.py            # MarketSnapshot, MarketOverview
│   │   │   ├── alert.py             # AlertConfig request/response
│   │   │   └── p3.py                # PriceAlert, Backtest, Portfolio schemas
│   │   │
│   │   ├── api/                     # ~25 REST endpoints + 1 WebSocket
│   │   │   ├── router.py            # Main router aggregator
│   │   │   ├── signals.py           # GET /signals, GET /signals/{id}
│   │   │   ├── markets.py           # GET /markets/overview
│   │   │   ├── alerts.py            # CRUD /alerts/config, watchlist
│   │   │   ├── history.py           # GET /signals/history, /stats, /track-record
│   │   │   ├── portfolio.py         # GET/POST /portfolio/trades, /summary
│   │   │   ├── price_alerts.py      # CRUD /price-alerts
│   │   │   ├── sharing.py           # POST /signals/{id}/share, GET /shared/{id}
│   │   │   ├── ai_qa.py             # POST /ai/ask
│   │   │   ├── backtest.py          # POST /backtest, GET /backtest/{id}
│   │   │   └── websocket.py         # WS /ws/signals
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── data_ingestion/      # 3 market fetchers + market hours
│   │   │   │   ├── base.py          # Abstract base fetcher
│   │   │   │   ├── indian_stocks.py # yfinance (15 NSE symbols)
│   │   │   │   ├── crypto.py        # Binance WebSocket (10 pairs)
│   │   │   │   ├── forex.py         # Alpha Vantage (6 pairs)
│   │   │   │   └── market_hours.py  # NSE/Forex/Crypto schedule awareness
│   │   │   │
│   │   │   ├── analysis/            # Technical indicators
│   │   │   │   ├── indicators.py    # TechnicalAnalyzer: RSI, MACD, BB, Vol, SMA, ATR
│   │   │   │   └── utils.py         # DataFrame validation
│   │   │   │
│   │   │   ├── ai_engine/           # Claude AI integration
│   │   │   │   ├── sentiment.py     # News → Claude → sentiment score (cached 15m)
│   │   │   │   ├── reasoner.py      # Signal reasoning generator
│   │   │   │   ├── briefing.py      # Morning/evening/weekly briefs
│   │   │   │   ├── news_fetcher.py  # Google/Bing/RSS news aggregation
│   │   │   │   ├── prompts.py       # All Claude prompts (centralized)
│   │   │   │   └── cost_tracker.py  # $30/month budget enforcement
│   │   │   │
│   │   │   ├── signal_gen/          # Signal generation pipeline
│   │   │   │   ├── generator.py     # SignalGenerator: data → analysis → AI → signal
│   │   │   │   ├── scorer.py        # Scoring: tech×0.6 + sentiment×0.4
│   │   │   │   └── targets.py       # ATR-based target/stop-loss (1:2 R:R)
│   │   │   │
│   │   │   └── alerts/              # Alert dispatch
│   │   │       ├── telegram_bot.py  # 10 commands (/start, /signals, /config, etc.)
│   │   │       ├── formatter.py     # 11 message formatters
│   │   │       └── dispatcher.py    # Alert routing + retry logic
│   │   │
│   │   └── tasks/                   # 12+ Celery scheduled tasks
│   │       ├── celery_app.py        # Celery app config
│   │       ├── scheduler.py         # Beat schedule definition
│   │       ├── data_tasks.py        # 3 market fetcher tasks
│   │       ├── analysis_tasks.py    # Technical analysis task
│   │       ├── ai_tasks.py          # Sentiment analysis task
│   │       ├── signal_tasks.py      # Signal generation + resolution
│   │       ├── alert_tasks.py       # Morning brief, evening wrap, weekly digest
│   │       ├── price_alert_tasks.py # Price alert checking
│   │       └── backtest_tasks.py    # On-demand backtesting
│   │
│   ├── migrations/                  # 3 Alembic migrations
│   │   └── versions/
│   │       ├── b0396d5bb542_initial_schema.py
│   │       ├── c4a8f2d1e3b5_add_watchlist_column.py
│   │       └── d5b9e3f4a6c7_add_p3_tables.py
│   │
│   ├── tests/                       # 40 test files, 480+ passing tests
│   │   ├── conftest.py              # Fixtures: test DB, test client, mocks
│   │   ├── test_indicators*.py      # Technical indicator tests
│   │   ├── test_signal_*.py         # Signal gen, scorer, resolution tests
│   │   ├── test_ai_*.py             # AI engine, budget, cost tracker tests
│   │   ├── test_api_*.py            # 10 endpoint test files
│   │   ├── test_websocket.py        # WebSocket delivery tests
│   │   ├── test_pipeline_*.py       # Integration pipeline tests
│   │   └── test_sprint*_*.py        # Sprint regression tests
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # 8 pages (Next.js App Router)
│   │   │   ├── layout.tsx           # Root layout (Outfit + JetBrains Mono fonts)
│   │   │   ├── page.tsx             # Dashboard: MarketOverview → WinRate → SignalFeed
│   │   │   ├── signal/[id]/page.tsx # Signal detail: chart, indicators, risk calc
│   │   │   ├── history/page.tsx     # Signal history with outcome filters
│   │   │   ├── portfolio/page.tsx   # Trade log, positions, P&L
│   │   │   ├── alerts/page.tsx      # Alert config, watchlist
│   │   │   ├── backtest/page.tsx    # Historical backtesting
│   │   │   ├── how-it-works/page.tsx# Educational guide
│   │   │   ├── shared/[id]/page.tsx # Public shared signal view
│   │   │   └── globals.css          # Tailwind + dark theme CSS vars
│   │   │
│   │   ├── components/              # 19 React components
│   │   │   ├── signals/             # SignalFeed, SignalCard, SignalBadge,
│   │   │   │                        # ConfidenceGauge, AIReasoningPanel,
│   │   │   │                        # TargetProgressBar, RiskCalculator,
│   │   │   │                        # WinRateCard, AccuracyChart, ShareButton, AskAI
│   │   │   ├── markets/             # MarketOverview, MarketHeatmap, Sparkline
│   │   │   ├── alerts/              # AlertTimeline, AlertConfig
│   │   │   └── shared/              # Navbar, WelcomeModal, ChatIdPrompt,
│   │   │                            # LoadingSpinner, ErrorBoundary,
│   │   │                            # KeyboardHelpModal, Toast, IndicatorPill
│   │   │
│   │   ├── hooks/                   # 4 custom hooks
│   │   │   ├── useSignals.ts        # REST signal fetching
│   │   │   ├── useMarketData.ts     # Market data fetching
│   │   │   ├── useWebSocket.ts      # WebSocket + auto-reconnect
│   │   │   └── useKeyboardShortcuts.ts # Global keyboard shortcuts
│   │   │
│   │   ├── store/                   # 3 Zustand stores
│   │   │   ├── signalStore.ts       # Signals, filters, unseen count
│   │   │   ├── marketStore.ts       # Market snapshots, WS status
│   │   │   └── userStore.ts         # Telegram chat ID (localStorage)
│   │   │
│   │   ├── lib/                     # Shared utilities
│   │   │   ├── api.ts               # REST client for /api/v1
│   │   │   ├── websocket.ts         # WebSocket client class
│   │   │   ├── types.ts             # 15+ TypeScript interfaces
│   │   │   └── constants.ts         # Colors, thresholds, badge labels
│   │   │
│   │   └── utils/
│   │       ├── formatters.ts        # Price, %, date, time formatting
│   │       └── market-hours.ts      # Market open/close detection
│   │
│   ├── package.json
│   ├── tsconfig.json                # strict: true, @/* path alias
│   ├── tailwind.config.ts           # Dark theme color tokens
│   └── Dockerfile
│
└── docs/
    ├── design/                      # Spec documents (v1–v4)
    ├── review/                      # Code review findings
    └── api.md                       # Full API reference
```

---

## Database Schema

### market_data (TimescaleDB Hypertable)

```sql
CREATE TABLE market_data (
    id              BIGSERIAL,
    symbol          VARCHAR(20) NOT NULL,
    market_type     VARCHAR(10) NOT NULL CHECK (market_type IN ('stock', 'crypto', 'forex')),
    open            DECIMAL(20, 8) NOT NULL,
    high            DECIMAL(20, 8) NOT NULL,
    low             DECIMAL(20, 8) NOT NULL,
    close           DECIMAL(20, 8) NOT NULL,
    volume          DECIMAL(20, 4),
    timestamp       TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('market_data', 'timestamp');

-- Index for fast symbol lookups
CREATE INDEX idx_market_data_symbol_time ON market_data (symbol, timestamp DESC);
```

### signals

```sql
CREATE TABLE signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(20) NOT NULL,
    market_type     VARCHAR(10) NOT NULL,
    signal_type     VARCHAR(15) NOT NULL CHECK (signal_type IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL')),
    confidence      INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    current_price   DECIMAL(20, 8) NOT NULL,
    target_price    DECIMAL(20, 8) NOT NULL,
    stop_loss       DECIMAL(20, 8) NOT NULL,
    timeframe       VARCHAR(50),
    ai_reasoning    TEXT NOT NULL,
    technical_data  JSONB NOT NULL,        -- {rsi: {value, signal}, macd: {...}, ...}
    sentiment_data  JSONB,                 -- {score, key_factors, source_count}
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_signals_active ON signals (is_active, created_at DESC);
CREATE INDEX idx_signals_symbol ON signals (symbol, created_at DESC);
```

### alert_configs

```sql
CREATE TABLE alert_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_chat_id BIGINT UNIQUE NOT NULL,
    username        VARCHAR(100),
    markets         JSONB DEFAULT '["stock", "crypto", "forex"]',
    min_confidence  INTEGER DEFAULT 60,
    signal_types    JSONB DEFAULT '["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]',
    quiet_hours     JSONB,                  -- {start: "23:00", end: "07:00"}
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### signal_history

```sql
CREATE TABLE signal_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id       UUID REFERENCES signals(id),
    outcome         VARCHAR(20) CHECK (outcome IN ('hit_target', 'hit_stop', 'expired', 'pending')),
    exit_price      DECIMAL(20, 8),
    return_pct      DECIMAL(8, 4),          -- percentage return
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_history_outcome ON signal_history (outcome, created_at DESC);
```

### Key Schema Rules

- **All prices are DECIMAL, never FLOAT** — financial data demands precision
- **Timestamps are always TIMESTAMPTZ** — we deal with IST, UTC, and market-specific timezones
- **JSONB for flexible data** — technical_data and sentiment_data are structured but may evolve
- **UUIDs for signal IDs** — safe for distributed systems and URL-friendly
- **TimescaleDB hypertable for market_data** — optimized for time-series queries

---

## Coding Standards

### Python (Backend)

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required on ALL function signatures — no exceptions
- **Models**: Pydantic v2 for schemas, SQLAlchemy 2.0 for ORM
- **Async**: ALL FastAPI endpoints and database operations must be async
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Imports**: stdlib → third-party → local (isort manages this)
- **Docstrings**: Required on all public functions and classes (Google style)
- **Error handling**: Never swallow exceptions silently. Log + re-raise or handle explicitly
- **Environment**: All secrets via environment variables. Never hardcode API keys
- **Decimal**: Use `decimal.Decimal` for all price/financial calculations. NEVER `float`

```python
# CORRECT
async def get_signal(signal_id: UUID) -> Signal:
    """Fetch a signal by ID.

    Args:
        signal_id: The UUID of the signal to retrieve.

    Returns:
        Signal object with all fields populated.

    Raises:
        SignalNotFoundError: If no signal exists with the given ID.
    """
    ...

# WRONG — missing types, no docstring, sync
def get_signal(id):
    ...
```

### TypeScript (Frontend)

- **Strict mode**: `"strict": true` in tsconfig.json — no `any` types allowed
- **Formatter**: Prettier (2-space indent, single quotes, trailing commas)
- **Components**: Functional components only. No class components
- **State**: Zustand for global state. React useState/useReducer for local
- **Naming**: camelCase for functions/variables, PascalCase for components and types
- **Props**: Always define explicit interfaces, never inline types
- **CSS**: Tailwind utility classes only. No inline styles. No CSS modules
- **Exports**: Named exports preferred. Default export only for page components

```typescript
// CORRECT
interface SignalCardProps {
  signal: Signal;
  isExpanded: boolean;
  onToggle: (id: string) => void;
}

export function SignalCard({ signal, isExpanded, onToggle }: SignalCardProps) {
  ...
}

// WRONG — any types, inline styles, no interface
export default function SignalCard({ signal, expanded, onToggle }: any) {
  return <div style={{color: 'red'}}>...</div>
}
```

### Shared Standards

- **Git commits**: Conventional Commits format — `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- **Branch naming**: `feature/signal-generation`, `fix/websocket-reconnect`, `test/indicator-coverage`
- **No commented-out code** — delete it, Git has history
- **No TODO comments without an associated GitHub issue**
- **All API responses must use consistent envelope**: `{ data: ..., meta: { timestamp, count } }`

### Pre-Commit Testing Rule (MANDATORY)

**Before every git commit, ALL existing tests must pass.** This is non-negotiable:

1. **Run the full test suite** before staging/committing any changes
2. **If any existing test fails**, fix the code or the test before committing — never commit with failing tests
3. **If new code is added**, write corresponding tests for it in the same commit
4. **If existing code is modified**, verify related tests still pass and update them if behavior changed intentionally
5. **New features without tests will not be committed** — every service, utility, and API endpoint must have test coverage
6. **Backend test command**: `python -m pytest tests/ -v --override-ini="asyncio_mode=auto"` (from `backend/` directory)
7. **Frontend test command**: `npx vitest run` (from `frontend/` directory)
8. **Docker build verification**: `docker compose build` must succeed — no TypeScript compilation errors, no broken imports
9. **Minimum bar**: All tests green (0 failures) AND Docker build clean before any commit is made

### Pre-Tag / Release Gate (MANDATORY)

**Before creating any git tag or version release, the FULL system must be verified end-to-end.** This is non-negotiable:

1. **All backend tests pass**: `python -m pytest tests/ -v --override-ini="asyncio_mode=auto"`
2. **All frontend tests pass**: `npx vitest run`
3. **Docker build succeeds**: `docker compose build` — all 5 services (db, redis, backend, celery, frontend) must build without errors
4. **Docker run verification**: `docker compose up -d` — all services must start and reach healthy state
5. **Health check passes**: `curl http://localhost:8000/health` returns 200
6. **Frontend loads**: `curl http://localhost:3000` returns 200
7. **Clean shutdown**: `docker compose down` after verification
8. **Never tag a broken build** — if any step above fails, fix it before tagging
9. **Tag command**: Only after all checks pass: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`

---

## API Contract

### REST Endpoints

| Method | Endpoint | Description | Response |
|--------|---------|------------|---------|
| GET | `/health` | Health check + system status | `{ status, uptime, last_data_fetch, active_signals_count }` |
| GET | `/api/v1/signals` | List active signals | `{ data: Signal[], meta }` |
| GET | `/api/v1/signals/{id}` | Signal detail | `{ data: Signal }` |
| GET | `/api/v1/signals/history` | Past signals with outcomes | `{ data: SignalHistory[], meta }` |
| GET | `/api/v1/markets/overview` | Live market snapshot | `{ data: { stocks, crypto, forex } }` |
| GET | `/api/v1/alerts/config` | Get alert preferences | `{ data: AlertConfig }` |
| POST | `/api/v1/alerts/config` | Create alert config | `{ data: AlertConfig }` |
| PUT | `/api/v1/alerts/config/{id}` | Update alert config | `{ data: AlertConfig }` |
| WS | `/ws/signals` | Real-time signal stream | Signal objects as they fire |

### Query Parameters (Signals)

- `market` — Filter: `stock`, `crypto`, `forex`, or omit for all
- `signal_type` — Filter: `STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL`
- `min_confidence` — Integer 0-100
- `limit` — Default 20, max 100
- `offset` — Pagination offset

### WebSocket Protocol

```json
// Client → Server (subscribe)
{ "type": "subscribe", "markets": ["stock", "crypto", "forex"] }

// Server → Client (new signal)
{
  "type": "signal",
  "data": {
    "id": "uuid",
    "symbol": "HDFCBANK",
    "market_type": "stock",
    "signal_type": "STRONG_BUY",
    "confidence": 92,
    "current_price": "1678.90",
    "target_price": "1780.00",
    "stop_loss": "1630.00",
    "timeframe": "2-4 weeks",
    "ai_reasoning": "Credit growth accelerating...",
    "technical_data": { ... },
    "created_at": "2026-03-20T10:30:00Z"
  }
}

// Server → Client (market update)
{
  "type": "market_update",
  "data": { "symbol": "BTC", "price": "97842.00", "change_pct": 3.87 }
}

// Server → Client (heartbeat — every 30s)
{ "type": "ping" }
// Client → Server
{ "type": "pong" }
```

---

## Signal Generation Algorithm

### Scoring Formula

```
technical_score = weighted_average([
    (rsi_signal,        0.20),
    (macd_signal,       0.25),
    (bollinger_signal,  0.15),
    (volume_signal,     0.15),
    (sma_crossover,     0.25),
])

ai_sentiment_score = claude_sentiment_analysis(symbol, recent_news)

final_confidence = (technical_score × 0.60) + (ai_sentiment_score × 0.40)
```

### Signal Thresholds

| Confidence Range | Signal Type |
|-----------------|-------------|
| 80–100 | STRONG_BUY |
| 65–79 | BUY |
| 36–64 | HOLD |
| 21–35 | SELL |
| 0–20 | STRONG_SELL |

### Target & Stop-Loss Calculation

```
ATR = Average True Range (14-period)

For BUY/STRONG_BUY:
  target    = current_price + (ATR × 2.0)
  stop_loss = current_price - (ATR × 1.0)

For SELL/STRONG_SELL:
  target    = current_price - (ATR × 2.0)
  stop_loss = current_price + (ATR × 1.0)

Risk:Reward ratio is always ≥ 1:2
```

---

## AI Engine — Claude Integration

### Model

Always use `claude-sonnet-4-20250514` for all AI calls. Sonnet gives the best cost-performance balance for financial text analysis.

### Prompts (Centralized in `backend/app/services/ai_engine/prompts.py`)

All Claude API prompts live in one file. Never hardcode prompts inline. This makes prompt iteration easy and keeps costs trackable.

### Sentiment Analysis Prompt Structure

```python
SENTIMENT_PROMPT = """You are a financial market analyst. Analyze the following news articles
about {symbol} ({market_type}).

Articles:
{articles_text}

Respond ONLY with valid JSON (no markdown, no preamble):
{{
  "sentiment_score": <0-100, where 0=extremely bearish, 100=extremely bullish>,
  "key_factors": ["factor1", "factor2", "factor3"],
  "market_impact": "<positive|negative|neutral>",
  "time_horizon": "<short_term|medium_term|long_term>",
  "confidence_in_analysis": <0-100>
}}"""
```

### Signal Reasoning Prompt Structure

```python
REASONING_PROMPT = """You are explaining a trading signal to an intelligent finance professional
who is learning active trading. She has an M.Com in Finance.

Symbol: {symbol}
Signal: {signal_type} (Confidence: {confidence}%)
Technical Data: {technical_summary}
Sentiment: {sentiment_summary}

Write a 2-3 sentence explanation of WHY this signal was generated.
- Be specific about which indicators and news drove the decision
- Use financial terminology she would know from her M.Com
- Include what to watch for (confirmation signals or risk factors)
- Be direct and actionable — no filler

Respond with the explanation text only, no JSON."""
```

### Cost Control Rules

- **Budget**: Maximum $30/month on Claude API calls
- **Batching**: News articles are batched per symbol (max 10 articles per call)
- **Caching**: Sentiment scores cached in Redis for 15 minutes
- **Rate limiting**: Maximum 100 Claude API calls per hour
- **Cost tracking**: Every API call logs token usage to `cost_tracker.py`
- **Fallback**: If API budget is exhausted, signals still generate from technical analysis only (confidence capped at 60%)

---

## Celery Task Schedule

```python
# backend/app/tasks/scheduler.py

CELERY_BEAT_SCHEDULE = {
    # ── Data Ingestion ──
    "fetch-indian-stocks": {
        "task": "tasks.data_tasks.fetch_indian_stocks",
        "schedule": 60.0,                               # Every 1 min (during NSE hours only)
    },
    "fetch-crypto-prices": {
        "task": "tasks.data_tasks.fetch_crypto",
        "schedule": 30.0,                               # Every 30 sec (24/7)
    },
    "fetch-forex-rates": {
        "task": "tasks.data_tasks.fetch_forex",
        "schedule": 60.0,                               # Every 1 min (24/5)
    },

    # ── Analysis ──
    "run-technical-analysis": {
        "task": "tasks.analysis_tasks.run_analysis",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── AI Engine ──
    "run-sentiment-analysis": {
        "task": "tasks.ai_tasks.run_sentiment",
        "schedule": 3600.0,                              # Every 1 hour
    },

    # ── Signal Generation ──
    "generate-signals": {
        "task": "tasks.signal_tasks.generate_signals",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── Digests ──
    "morning-brief": {
        "task": "tasks.alert_tasks.morning_brief",
        "schedule": crontab(hour=8, minute=0),          # 8:00 AM IST daily
    },
    "evening-wrap": {
        "task": "tasks.alert_tasks.evening_wrap",
        "schedule": crontab(hour=16, minute=0),         # 4:00 PM IST daily
    },

    # ── Signal Resolution ──
    "resolve-signals": {
        "task": "tasks.signal_tasks.resolve_signals",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── User Alerts ──
    "check-price-alerts": {
        "task": "tasks.price_alert_tasks.check_price_alerts",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── Digests (continued) ──
    "weekly-digest": {
        "task": "tasks.alert_tasks.weekly_digest",
        "schedule": crontab(hour=12, minute=30, day_of_week=0),  # Sun 6:00 PM IST
    },
}
```

### Market Hours Awareness

The data ingestion tasks must respect market hours:

| Market | Trading Hours (IST) | Data Fetch Active |
|--------|-------------------|------------------|
| NSE/BSE | 9:15 AM – 3:30 PM Mon-Fri | Only during market hours + 15 min buffer |
| Crypto | 24/7 | Always |
| Forex | 24/5 (Sun 5:30 PM IST – Sat 3:30 AM IST) | During forex market hours |

Tasks MUST check market hours before executing. If the market is closed, skip the fetch and log it. Never waste API calls on closed markets.

---

## Data Sources & API Keys

### Required Environment Variables

```bash
# .env.example

# ── Database ──
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/signalflow
REDIS_URL=redis://localhost:6379/0

# ── AI Engine ──
ANTHROPIC_API_KEY=sk-ant-...

# ── Market Data ──
ALPHA_VANTAGE_API_KEY=...            # Forex data (free: 5 calls/min)
BINANCE_API_KEY=...                   # Crypto (optional for public endpoints)
BINANCE_SECRET=...
COINMARKETCAP_API_KEY=...             # Crypto metadata (free tier)

# ── Alerts ──
TELEGRAM_BOT_TOKEN=...                # From @BotFather
TELEGRAM_DEFAULT_CHAT_ID=...          # Primary user's chat ID

# ── Monitoring ──
SENTRY_DSN=...

# ── App Config ──
ENVIRONMENT=development               # development | production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
MONTHLY_AI_BUDGET_USD=30
```

### API Rate Limits to Respect

| API | Free Tier Limit | Our Usage | Strategy |
|-----|----------------|-----------|---------|
| Alpha Vantage | 5 calls/min, 500/day | ~480 calls/day for forex | Queue calls with 12-sec spacing |
| Binance | 1200 req/min | WebSocket (1 connection) | Use WebSocket, not REST polling |
| CoinGecko | 30 calls/min | ~60 calls/hour | Cache aggressively, batch requests |
| Yahoo Finance | Unofficial, soft limits | ~100 calls/hour for stocks | Batch symbols in single call |
| Claude API | Token-based billing | ~2000 calls/day | Budget tracking + caching |
| Telegram | 30 msg/sec to same chat | ~50 msgs/day | Well within limits |

---

## Frontend Design System

### Theme

Dark trading terminal aesthetic. Think Bloomberg Terminal meets modern fintech.

```css
/* Color tokens */
--bg-primary: #0A0B0F;
--bg-secondary: #12131A;
--bg-card: rgba(255, 255, 255, 0.02);
--bg-card-hover: rgba(255, 255, 255, 0.04);

--text-primary: #F9FAFB;
--text-secondary: #9CA3AF;
--text-muted: #6B7280;

--accent-purple: #6366F1;
--signal-buy: #00E676;
--signal-sell: #FF5252;
--signal-hold: #FFD740;
--signal-strong: same as buy/sell but with higher opacity backgrounds

--border-default: rgba(255, 255, 255, 0.06);
--border-hover: rgba(255, 255, 255, 0.12);
```

### Typography

```css
/* Fonts (load from Google Fonts) */
--font-display: 'Outfit', sans-serif;          /* Headlines, labels */
--font-mono: 'JetBrains Mono', monospace;      /* Prices, percentages, data */
--font-body: 'Outfit', sans-serif;             /* Body text */
```

### Component Rules

- **Signal cards**: Expandable on click. Show confidence gauge, sparkline, signal badge in collapsed state. Show AI reasoning, indicators, targets in expanded state.
- **Confidence Gauge**: SVG circular progress bar. Color matches signal type.
- **Sparklines**: 20-point SVG polyline. Green for positive change, red for negative.
- **Animations**: Subtle fade-in for new signals (0.3s ease). No heavy animations.
- **Mobile-first**: The dashboard must be fully usable on mobile. She'll check it on her phone.
- **Loading states**: Skeleton screens, never blank white space.
- **Error states**: Friendly messages with retry buttons, never raw error dumps.

---

## Telegram Bot Specification

### Commands

| Command | Description | Response |
|---------|-----------|---------|
| `/start` | Connect to SignalFlow | Welcome message + store chat_id |
| `/signals` | Current active signals | Top 5 by confidence, formatted cards |
| `/config` | Alert preferences | Inline keyboard to set markets, min confidence |
| `/markets` | Quick market snapshot | NIFTY, BTC, EUR/USD with % changes |
| `/history` | Recent signal outcomes | Last 5 resolved signals with hit/miss status |
| `/stop` | Pause all alerts | Confirm + deactivate alerts |
| `/resume` | Resume alerts | Reactivate alerts |

### Signal Alert Format

```
🟢 STRONG BUY — HDFCBANK

💰 Price: ₹1,678.90 (+1.42%)
📊 Confidence: ████████░░ 92%

🎯 Target: ₹1,780  |  🛑 Stop: ₹1,630
⏱ Timeframe: 2-4 weeks

🤖 AI: Credit growth accelerating. NIM expansion
confirmed. AI model shows 92% probability of
uptrend continuation.

RSI: 62.7 | MACD: Strong Bullish | Vol: High
```

### Emoji Coding

- 🟢 STRONG_BUY / BUY
- 🔴 STRONG_SELL / SELL
- 🟡 HOLD
- 🤖 AI reasoning
- 📊 Confidence
- 🎯 Target
- 🛑 Stop-loss
- ⏱ Timeframe

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
│   ├── test_db              # In-memory SQLite or test PostgreSQL
│   ├── test_client           # FastAPI TestClient
│   ├── mock_claude_api       # Mocked Claude responses
│   ├── sample_market_data    # Fixture OHLCV DataFrames
│   └── sample_signals        # Pre-built signal objects
│
├── unit/
│   ├── test_rsi.py
│   ├── test_macd.py
│   ├── test_bollinger.py
│   ├── test_signal_scorer.py
│   ├── test_target_calculator.py
│   └── test_message_formatter.py
│
├── integration/
│   ├── test_data_to_signal_pipeline.py   # Full pipeline test
│   ├── test_api_endpoints.py
│   ├── test_websocket_delivery.py
│   └── test_telegram_dispatch.py
│
└── load/
    └── locustfile.py          # Load testing: 50 symbols × 1 min
```

### Test Rules

- **Coverage target**: ≥80% on backend services
- **Every indicator function** must have tests for: normal data, edge cases (insufficient data, all-zero volume), and expected signal output
- **Mock external APIs**: Claude API, Binance, Yahoo Finance — never call real APIs in tests
- **Integration tests** must test the full pipeline: data → indicators → AI → signal → delivery
- **Tester agent writes tests alongside features**, not after
- **Pre-commit gate**: The full test suite MUST pass before every commit. No exceptions. If code changes break existing tests, fix them before committing. If new code is added, include matching tests in the same commit. Docker build (`docker compose build`) must also succeed. See "Pre-Commit Testing Rule" under Coding Standards for details.
- **Pre-tag gate**: Before any git tag or release, the full system must be Docker-built, started, health-checked, and verified end-to-end. See "Pre-Tag / Release Gate" under Coding Standards for details.

### Identity & Auth Testing Rules (MANDATORY)

> **Lesson learned**: When the JWT auth system was added, all user-scoped endpoints (portfolio, watchlist, price alerts) continued using `telegram_chat_id` for queries. Web-registered users have `telegram_chat_id = NULL`, causing silent failures — "Failed to load portfolio" and "Failed to load watchlist." This was missed because test fixtures always injected `telegram_chat_id=12345`.

**Rules to prevent this class of bug:**

1. **Every user-scoped endpoint must be tested with BOTH identity types:**
   - `AuthContext(user_id="...", telegram_chat_id=12345)` — Telegram-connected user
   - `AuthContext(user_id="...", telegram_chat_id=None)` — Web-only user (no Telegram)
   - See `tests/test_web_user_identity.py` for the canonical pattern

2. **After any auth or identity model change:**
   - Verify ALL user-scoped endpoints still work (portfolio, watchlist, alerts, price alerts, trades)
   - Test with web-only user fixture (telegram_chat_id=None)
   - Run `pytest tests/test_web_user_identity.py` as a mandatory check

3. **When adding `user_id` to existing tables:**
   - Add nullable column (backward compat with Telegram-only users)
   - Update ALL queries to use `or_(Model.user_id == uid, Model.telegram_chat_id == chat_id)`
   - Update ALL create operations to store both `user_id` and `telegram_chat_id`
   - Update ALL ownership checks to compare both identity fields

4. **Test fixture rule:** Never rely on a single identity field. Both `test_client` (Telegram user) and `web_user_client` (web user) fixtures must exist and be used.

---

## Deployment

### Railway Configuration

```yaml
# railway.toml (Backend)
[build]
  builder = "dockerfile"
  dockerfilePath = "backend/Dockerfile"

[deploy]
  startCommand = "bash -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT & celery -A app.tasks.celery_app worker --beat --loglevel=info'"
  restartPolicyType = "always"
  healthcheckPath = "/health"
  healthcheckTimeout = 30
```

### Production Checklist

- [ ] All environment variables set in Railway
- [ ] Database migrations applied
- [ ] Celery Beat schedule verified (tasks firing on time)
- [ ] WebSocket connections stable over 24 hours
- [ ] Telegram bot responding to commands
- [ ] Sentry capturing errors (test with intentional error)
- [ ] UptimeRobot pinging /health every 60 seconds
- [ ] Claude API cost tracking working
- [ ] SSL/HTTPS configured on custom domain
- [ ] CORS configured for production frontend domain only

---

## Important Constraints & Rules

### Non-Negotiable

1. **This is NOT financial advice software.** Every signal must include the disclaimer that it's AI-generated and not investment advice. The Telegram welcome message and dashboard footer must include this.
2. **No auto-trading in MVP.** Signals are advisory only. The user makes all trade decisions manually.
3. **Every signal MUST have a stop-loss.** No signal is ever generated without a recommended exit point for limiting losses.
4. **All prices as Decimal.** Financial precision is non-negotiable.
5. **24/7 reliability.** The system must handle API outages, rate limits, and network interruptions gracefully without crashing.
6. **Claude API budget: $30/month max.** Implement hard budget limits with cost tracking.
7. **Privacy.** No user data is shared externally. Telegram chat IDs are stored only for alert delivery.

### Architecture Rules

1. **Services are independent.** Data ingestion doesn't depend on AI engine. If Claude API is down, technical signals still work.
2. **Fail gracefully.** If one market's data source is down, the other two markets continue normally.
3. **Idempotent tasks.** Celery tasks must be safe to retry. Duplicate data fetches should update, not duplicate rows.
4. **Log everything.** Structured logging with correlation IDs. Every signal generation should be traceable from data fetch to delivery.

---

## Quick Reference — File to Edit for Each Change

| I need to... | Edit this file |
|-------------|---------------|
| Add a new market/symbol | `backend/app/config.py` (TRACKED_SYMBOLS) |
| Add a new technical indicator | `backend/app/services/analysis/indicators.py` |
| Change signal scoring weights | `backend/app/services/signal_gen/scorer.py` |
| Modify a Claude AI prompt | `backend/app/services/ai_engine/prompts.py` |
| Add a new API endpoint | `backend/app/api/` + register in `router.py` |
| Change Celery task timing | `backend/app/tasks/scheduler.py` |
| Add a dashboard component | `frontend/src/components/` |
| Change WebSocket message format | `backend/app/api/websocket.py` + `frontend/src/lib/websocket.ts` |
| Add a Telegram command | `backend/app/services/alerts/telegram_bot.py` |
| Change Telegram message format | `backend/app/services/alerts/formatter.py` |
| Add a database table | `backend/app/models/` + create Alembic migration |
| Update project instructions | This file (CLAUDE.md) |

---

## Project History & Current State

### Version: v1.0.0 (Released 21 March 2026)

### Development Phases

| Phase | Commits | What Was Built |
|-------|---------|----------------|
| Phase 1 | `5ce7ea0` | Project scaffold, Docker, DB schema, 3 market fetchers, Celery Beat |
| Phase 2 | `550ce72` | TechnicalAnalyzer (RSI, MACD, BB, Vol, SMA, ATR), AI sentiment, signal pipeline |
| Phase 3 | `cb672d8` | Dashboard components, Telegram bot (10 commands), alert system |
| Phase 4 | `511aab6` | Integration testing, deployment config, end-to-end pipeline |
| Phase 5 P0 | `dfd3282` | Launch blockers: WebSocket fix, health endpoint, rate limiting |
| Phase 5 P1 | `c9a6ab7` | Trust features: signal history, win rate tracking, resolution |
| Phase 5 P2 | `c82bbfc` | Enhancements: market heatmap, accuracy charts, keyboard shortcuts |
| Phase 5 P3 | `4d83c10` | Future features: backtesting, AI Q&A, portfolio, signal sharing |
| Sprint 1–10 | `8cbc471`–`2cdf2dd` | 10 iterative sprints fixing UX, adding detail pages, mobile fixes |
| V1 UI | `dbec9da` | First UI simplification (20→8 data points per card) |
| V2 UI | `c3fe1ab` | Second UI simplification (8→6 data points, 3-section expand) |

### Key Metrics

| Metric | Count |
|--------|-------|
| Backend Python files | ~30 (6,000+ lines) |
| Frontend TypeScript files | 46 |
| API endpoints | ~25 REST + 1 WebSocket |
| Database tables | 8 |
| Tracked symbols | 31 (15 stocks, 10 crypto, 6 forex) |
| Test files | 40 |
| Passing tests | 480+ |
| React components | 19 |
| Zustand stores | 3 |
| Celery scheduled tasks | 12+ |
| Alembic migrations | 3 |
| Git tags | v0.0.1, v1.0.0 |

### Known Issues

- 4 test failures in `test_ai_engine.py` — related to environment config for AI budget checking, not functional bugs
- `origin/feature/phase4-integration-deploy` remote branch still exists (was GitHub default branch; needs manual GitHub settings change to delete)

---

*Last updated: 21 March 2026 | SignalFlow AI v1.0.0*
