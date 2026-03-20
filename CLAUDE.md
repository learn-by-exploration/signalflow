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

## Development Methodology — Ruflo Multi-Agent Swarm

This project is built using **Ruflo (v3.5+)** for multi-agent orchestration and **Claude Code** as the primary coding engine. The developer acts as the **architect and orchestrator**, not a line-by-line coder.

### Ruflo Setup

```bash
# Initialize Ruflo in project root
npx ruflo@latest init

# Verify installation
npx ruflo doctor

# Initialize hierarchical swarm
npx ruflo swarm init \
  --topology hierarchical \
  --max-agents 6 \
  --strategy specialized
```

### Agent Swarm Definition

We use a **hierarchical swarm** with 1 queen (Architect) and 5 specialized workers:

| Agent Name | Ruflo Type | Role | File Scope |
|-----------|-----------|------|-----------|
| `sf-architect` | architect | Queen — decomposes tasks, coordinates agents, resolves conflicts | CLAUDE.md, architecture decisions, API contracts |
| `sf-backend` | coder | FastAPI, services, models, Celery tasks, database | `backend/**` |
| `sf-frontend` | coder | Next.js dashboard, React components, Tailwind, Zustand | `frontend/**` |
| `sf-ai-engineer` | coder | Claude API integration, prompts, sentiment pipeline | `backend/app/services/ai_engine/**` |
| `sf-tester` | tester | Unit tests, integration tests, API tests, load tests | `backend/app/tests/**`, `frontend/**/*.test.*` |
| `sf-reviewer` | reviewer | Code review, security audit, performance checks | All files (read-only review) |

### Spawning the Swarm

```bash
npx ruflo agent spawn -t architect --name sf-architect
npx ruflo agent spawn -t coder --name sf-backend
npx ruflo agent spawn -t coder --name sf-frontend
npx ruflo agent spawn -t coder --name sf-ai-engineer
npx ruflo agent spawn -t tester --name sf-tester
npx ruflo agent spawn -t reviewer --name sf-reviewer
```

### Agent Coordination Rules

1. **Handoff protocol**: When `sf-backend` completes an API endpoint → `sf-tester` auto-receives it for test writing → `sf-reviewer` checks both implementation and tests.
2. **Shared context**: All agents read this CLAUDE.md file. Schema changes by `sf-backend` must be reflected here immediately so `sf-frontend` stays in sync.
3. **File scope enforcement**: `sf-backend` ONLY modifies files in `backend/`. `sf-frontend` ONLY modifies files in `frontend/`. Cross-boundary changes require `sf-architect` coordination.
4. **Conflict resolution**: If two agents need to modify the same file, `sf-architect` arbitrates. In practice, clear scope boundaries prevent this.
5. **Human checkpoints**: After each phase milestone, the human developer reviews all swarm output before greenlighting the next phase.
6. **Memory persistence**: Successful patterns are stored in Ruflo's AgentDB. If an agent discovers how to handle a Binance WebSocket reconnection, that pattern persists for future sessions.

### Swarm Commands Reference

```bash
# Check swarm status
npx ruflo hive-mind status

# Spawn a task to the swarm
npx ruflo hive-mind spawn "Build the RSI indicator service" --queen-type strategic

# Check agent performance metrics
npx ruflo hive-mind metrics

# Store a learning in AgentDB
npx ruflo memory store binance_ws "Use ping/pong frames every 30s to keep Binance WebSocket alive" \
  --namespace backend --reasoningbank

# Query agent memory
npx ruflo memory query "Binance WebSocket" --namespace backend --reasoningbank
```

### Custom Slash Commands

Create these in `.claude/commands/` for rapid iteration:

| Command | What It Does |
|---------|-------------|
| `/signal-test <symbol>` | Run the full signal generation pipeline for one symbol end-to-end |
| `/swarm-status` | Check all agent statuses and current tasks |
| `/deploy` | Trigger Railway deployment from current branch |
| `/db-reset` | Reset local dev database and re-run migrations |
| `/run-all-tests` | Execute full backend + frontend test suite |
| `/fetch-check` | Verify all three market data fetchers are pulling live data |
| `/ai-cost` | Check current month's Claude API usage and cost |

---

## Project Structure

```
signalflow-ai/
├── .claude/                        # Ruflo agent configs
│   ├── agents/                     # Agent definitions
│   │   ├── sf-architect.json
│   │   ├── sf-backend.json
│   │   ├── sf-frontend.json
│   │   ├── sf-ai-engineer.json
│   │   ├── sf-tester.json
│   │   └── sf-reviewer.json
│   ├── commands/                   # Custom slash commands
│   │   ├── signal-test.md
│   │   ├── swarm-status.md
│   │   ├── deploy.md
│   │   └── run-all-tests.md
│   └── settings.json               # Ruflo settings, hooks, learning
│
├── CLAUDE.md                        # THIS FILE — master instructions
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, CORS, lifespan, routers
│   │   ├── config.py                # pydantic-settings, all env vars
│   │   ├── database.py              # SQLAlchemy async engine + session
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py       # TimescaleDB hypertable
│   │   │   ├── signal.py            # Signal model
│   │   │   ├── alert_config.py      # User alert preferences
│   │   │   └── signal_history.py    # Signal outcome tracking
│   │   │
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── signal.py
│   │   │   ├── market.py
│   │   │   └── alert.py
│   │   │
│   │   ├── api/                     # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # Main router aggregator
│   │   │   ├── signals.py           # GET /signals, GET /signals/{id}
│   │   │   ├── markets.py           # GET /markets/overview
│   │   │   ├── alerts.py            # GET/POST/PUT /alerts/config
│   │   │   ├── history.py           # GET /signals/history
│   │   │   └── websocket.py         # WS /ws/signals
│   │   │
│   │   ├── services/                # Business logic (core of the app)
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── data_ingestion/      # Market data fetchers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py          # Abstract base fetcher
│   │   │   │   ├── indian_stocks.py # yfinance + NSE APIs
│   │   │   │   ├── crypto.py        # Binance WS + CoinGecko REST
│   │   │   │   └── forex.py         # Alpha Vantage + Twelve Data
│   │   │   │
│   │   │   ├── analysis/            # Technical indicators
│   │   │   │   ├── __init__.py
│   │   │   │   ├── indicators.py    # TechnicalAnalyzer class
│   │   │   │   └── utils.py         # Shared analysis utilities
│   │   │   │
│   │   │   ├── ai_engine/           # Claude AI integration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sentiment.py     # News sentiment scoring
│   │   │   │   ├── reasoner.py      # Signal reasoning generator
│   │   │   │   ├── briefing.py      # Morning/evening digest
│   │   │   │   ├── prompts.py       # All Claude prompts (centralized)
│   │   │   │   └── cost_tracker.py  # API cost monitoring
│   │   │   │
│   │   │   ├── signal_gen/          # Signal generation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── generator.py     # SignalGenerator class
│   │   │   │   ├── scorer.py        # Scoring algorithm
│   │   │   │   └── targets.py       # Target/stop-loss calculator
│   │   │   │
│   │   │   └── alerts/              # Alert dispatch
│   │   │       ├── __init__.py
│   │   │       ├── telegram_bot.py  # Telegram bot + commands
│   │   │       ├── formatter.py     # Message formatting
│   │   │       └── dispatcher.py    # Alert routing logic
│   │   │
│   │   └── tasks/                   # Celery tasks
│   │       ├── __init__.py
│   │       ├── celery_app.py        # Celery app config
│   │       ├── scheduler.py         # Beat schedule definition
│   │       ├── data_tasks.py        # Fetch market data tasks
│   │       ├── analysis_tasks.py    # Run indicators task
│   │       ├── ai_tasks.py          # Sentiment analysis task
│   │       ├── signal_tasks.py      # Signal generation task
│   │       └── alert_tasks.py       # Morning brief, evening wrap
│   │
│   ├── migrations/                  # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── tests/                       # Backend test suite
│   │   ├── conftest.py              # Fixtures: test DB, test client, mocks
│   │   ├── test_indicators.py       # Unit tests for each indicator
│   │   ├── test_signal_gen.py       # Signal generation tests
│   │   ├── test_ai_engine.py        # AI engine tests (mocked Claude API)
│   │   ├── test_api_signals.py      # API endpoint integration tests
│   │   ├── test_api_markets.py
│   │   ├── test_websocket.py        # WebSocket delivery tests
│   │   └── test_telegram.py         # Telegram bot tests
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   │   ├── layout.tsx           # Root layout (fonts, theme)
│   │   │   ├── page.tsx             # Dashboard page
│   │   │   ├── history/
│   │   │   │   └── page.tsx         # Signal history page
│   │   │   └── globals.css          # Tailwind + custom CSS vars
│   │   │
│   │   ├── components/
│   │   │   ├── signals/
│   │   │   │   ├── SignalFeed.tsx        # Main signal list with filters
│   │   │   │   ├── SignalCard.tsx        # Expandable signal card
│   │   │   │   ├── SignalBadge.tsx       # BUY/SELL/HOLD badge
│   │   │   │   ├── ConfidenceGauge.tsx   # Circular SVG gauge
│   │   │   │   └── AIReasoningPanel.tsx  # Expandable AI explanation
│   │   │   │
│   │   │   ├── markets/
│   │   │   │   ├── MarketOverview.tsx    # Sticky top bar with live prices
│   │   │   │   └── Sparkline.tsx         # Mini price chart
│   │   │   │
│   │   │   ├── alerts/
│   │   │   │   ├── AlertTimeline.tsx     # Chronological alert feed
│   │   │   │   └── AlertConfig.tsx       # Settings modal
│   │   │   │
│   │   │   └── shared/
│   │   │       ├── IndicatorPill.tsx     # RSI/MACD/Volume display
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts          # WebSocket connection + reconnect
│   │   │   ├── useSignals.ts            # Signal data fetching
│   │   │   └── useMarketData.ts         # Market overview data
│   │   │
│   │   ├── store/
│   │   │   ├── signalStore.ts           # Zustand: signals state
│   │   │   ├── marketStore.ts           # Zustand: market overview
│   │   │   └── alertStore.ts            # Zustand: alert config
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                   # Axios/fetch client for REST API
│   │   │   ├── websocket.ts             # WebSocket client class
│   │   │   ├── types.ts                 # Shared TypeScript types
│   │   │   └── constants.ts             # Colors, thresholds, market config
│   │   │
│   │   └── utils/
│   │       ├── formatters.ts            # Price, percentage, date formatting
│   │       └── market-hours.ts          # Market open/close logic
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── Dockerfile
│
├── docker-compose.yml               # Local dev: all services
├── docker-compose.prod.yml          # Production overrides
├── .env.example                     # Template for environment variables
├── .gitignore
├── Makefile                         # Common commands shortcut
└── README.md
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
        "schedule": 900.0,                              # Every 15 min
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

    # ── Maintenance ──
    "resolve-expired-signals": {
        "task": "tasks.signal_tasks.resolve_expired",
        "schedule": 3600.0,                             # Every 1 hour
    },
    "health-check": {
        "task": "tasks.health_check",
        "schedule": 300.0,                              # Every 5 min
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

## Ruflo Phase Execution Plan

Use these commands to execute each development phase via the swarm:

### Phase 1: Foundation (Days 1-4)
```bash
npx ruflo hive-mind spawn \
  "Phase 1 - Foundation: Bootstrap FastAPI + Next.js project, set up Docker, create database schema, build all three market data fetchers (Indian stocks via yfinance, Crypto via Binance WebSocket, Forex via Alpha Vantage), implement Celery Beat scheduler. See CLAUDE.md for full architecture and schema." \
  --queen-type strategic
```

### Phase 2: Analysis Engine (Days 5-8)
```bash
npx ruflo hive-mind spawn \
  "Phase 2 - Analysis: Build TechnicalAnalyzer class with RSI, MACD, Bollinger Bands, Volume analysis, SMA crossovers, ATR. Then build Claude AI sentiment engine with news fetching, sentiment scoring, and signal reasoning generation. Finally build the signal generation algorithm with the scoring formula from CLAUDE.md." \
  --queen-type strategic
```

### Phase 3: Dashboard & Alerts (Days 9-14)
```bash
npx ruflo hive-mind spawn \
  "Phase 3 - Dashboard & Alerts: Build Next.js dashboard with dark trading terminal theme (see CLAUDE.md design system). Components: MarketOverview, SignalFeed, SignalCard, ConfidenceGauge, AlertTimeline, AlertConfig. Build Telegram bot with all commands. Wire WebSocket real-time delivery. See CLAUDE.md for full component specs and Telegram message format." \
  --queen-type strategic
```

### Phase 4: Integration & Deploy (Days 15-21)
```bash
npx ruflo hive-mind spawn \
  "Phase 4 - Integration: Run full end-to-end tests (data → analysis → AI → signals → dashboard + Telegram). Fix any integration issues. Build comprehensive test suite. Prepare Railway deployment config. See CLAUDE.md for testing strategy and deployment checklist." \
  --queen-type strategic
```

---

*Last updated: March 2026 | SignalFlow AI v1.0 MVP*
