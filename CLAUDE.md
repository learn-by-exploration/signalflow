# SignalFlow AI — Master Project Instructions

> **This file is the single source of truth for every Claude Code session and every agent working on this project. Read it fully before writing any code.**

---

## Project Overview

**SignalFlow AI** is a personal, AI-powered trading signal platform delivering actionable buy/sell/hold signals across Indian Stocks (NSE/BSE), Cryptocurrency (top 10), and Forex (major pairs).

### The User

A **finance professional with an M.Com degree** beginning her active trading journey. Every feature must be:
- **Clear** — no jargon; plain-English AI explanations
- **Actionable** — every signal has entry, target, stop-loss, and timeframe
- **Trustworthy** — confidence scores, transparent reasoning, full history
- **Teach as it helps** — each signal is a learning opportunity

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER LAYER                        │
│  ┌─────────────────┐    ┌────────────────────────┐  │
│  │  Next.js 14     │    │  Telegram Bot           │  │
│  │  Dashboard      │◄──►│  Alerts + Digests       │  │
│  └────────┬────────┘    └───────────┬────────────┘  │
├───────────┼─────────────────────────┼────────────────┤
│           ▼                         ▼                │
│  ┌──────────────────────────────────────────────┐   │
│  │              FastAPI Backend                   │   │
│  │  REST API · WebSocket · Celery Tasks           │   │
│  └──────────────────────┬───────────────────────┘   │
├─────────────────────────┼────────────────────────────┤
│                    SERVICE LAYER                      │
│  ┌──────────┐ ┌────────────┐ ┌───────────────────┐  │
│  │  Data    │ │ Technical  │ │   AI Engine        │  │
│  │ Ingest   │ │ Analysis   │ │  (Claude Sonnet)   │  │
│  └────┬─────┘ └─────┬──────┘ └────────┬──────────┘  │
│       └──────────────┴─────────────────┘             │
│                       ▼                              │
│  ┌─────────────┐ ┌───────┐ ┌──────────────────┐    │
│  │ Signal Gen  │ │ Redis │ │ Anthropic Claude  │    │
│  └──────┬──────┘ └───────┘ └──────────────────┘    │
│         ▼                                            │
│  ┌──────────────────────────────────┐               │
│  │  PostgreSQL + TimescaleDB        │               │
│  └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI + Python | 0.115+ / 3.11+ |
| Task Queue | Celery + Redis | 5.x / 7.x |
| Database | PostgreSQL + TimescaleDB | PG 16, TS 2.x |
| AI | Anthropic Claude API | claude-sonnet-4-20250514 |
| Frontend | Next.js + TypeScript | 14.x App Router / 5.x strict |
| Styling | Tailwind CSS | 3.x |
| State | Zustand | 4.x |
| Charts | Recharts + Lightweight Charts | latest |
| Alerts | python-telegram-bot | 20.x |
| Hosting | Railway | — |

---

## Development Methodology

### Core Directives (MANDATORY for ALL Sessions)

**Directive 1 — TDD is Non-Negotiable**
- ALL features begin with a failing test. Red → Green → Refactor strictly.

**Directive 2 — Multi-Stakeholder Alignment**
Before major architectural changes or adding libraries, check: PM (delays?), Banker (costs?), QA (harder to test?). Present tradeoffs if any check fails.

**Directive 3 — Code Quality**
- Simplicity over cleverness. SOLID principles. Security-first (sanitize all inputs).

**Directive 4 — Output Formatting**
- Minimal filler. Always include file path at top of code blocks. Explain *why* when refactoring.

**Directive 5 — GAN Protocol for MKG**
MKG components use Generator (writes tests → code) + Discriminator (adversarial review) loop. Both `[PASS]` required before presenting a component. See git history for pattern.

### Development Commands

```bash
make init          # Build + start + migrate (first time)
make up / down     # Start / stop services
make test          # Backend pytest
make lint          # Lint backend + frontend
make frontend-dev  # Next.js dev server
make migrate       # Apply Alembic migrations
make logs          # Follow all logs
```

### Pre-Commit Gate (MANDATORY)

Before every commit — ALL must pass:
1. `python -m pytest tests/ -v --override-ini="asyncio_mode=auto"` (from `backend/`)
2. `npx vitest run` (from `frontend/`)
3. `docker compose build` — no TypeScript errors, no broken imports

### Pre-Tag / Release Gate (MANDATORY)

Before any `git tag`: backend tests + frontend tests + `docker compose build` + `docker compose up -d` + `curl http://localhost:8000/health` (200) + `curl http://localhost:3000` (200) + `docker compose down`. Never tag a broken build.

---

## Project Structure

```
signalflow/
├── backend/
│   ├── app/
│   │   ├── main.py · auth.py · config.py · database.py · rate_limit.py
│   │   ├── models/          18 SQLAlchemy ORM models
│   │   ├── schemas/         Pydantic v2 schemas (signal, market, alert, auth, news, p3)
│   │   ├── api/             57 REST endpoints + 1 WebSocket (router.py aggregates)
│   │   ├── services/
│   │   │   ├── data_ingestion/   indian_stocks · crypto · forex · market_hours · validators
│   │   │   ├── analysis/         indicators.py (TechnicalAnalyzer) · utils.py
│   │   │   ├── ai_engine/        sentiment · reasoner · briefing · news_fetcher · prompts
│   │   │   │                     cost_tracker · dedup · event_chain · sanitizer
│   │   │   ├── signal_gen/       generator · scorer · targets · calibration · feedback
│   │   │   │                     mtf_confirmation · risk_guard · shadow_mode · streak_protection
│   │   │   ├── alerts/           telegram_bot · formatter · dispatcher
│   │   │   └── payment/          razorpay_service.py
│   │   └── tasks/           20 Celery tasks (scheduler.py defines beat schedule)
│   ├── migrations/          11 Alembic migrations
│   └── tests/               65 test files · 1,241 backend tests
├── frontend/
│   └── src/
│       ├── app/             20 pages (Next.js App Router)
│       ├── components/      55 React components (signals · markets · charts · alerts · shared)
│       ├── hooks/           5 custom hooks (useSignals · useMarketData · useWebSocket · ...)
│       ├── store/           5 Zustand stores (signalStore · marketStore · userStore · ...)
│       ├── lib/             api.ts · types.ts · websocket.ts · constants.ts · tiers.ts
│       └── __tests__/       79 test files · 741 frontend tests
├── external/ai-powerhouse   git submodule (279 agents · 365 skills)
├── .claude/
│   ├── agents/signalflow/   6 domain agents (backend · ai-engine · signal · data · frontend · security · reviewer)
│   ├── helpers/             hook-handler · router · session · intelligence
│   └── skills/              signalflow-architecture/SKILL.md
└── docs/                    compliance · decisions · design · guides · operations · reference · security · sprints
```

---

## Database Schema

**Tables:** `market_data` (TimescaleDB hypertable) · `signals` · `alert_configs` · `signal_history` · `signal_feedback` · `signal_share` · `signal_news_link` · `price_alerts` · `trades` · `backtest_runs` · `users` · `refresh_tokens` · `subscriptions` · `news_events` · `event_entities` · `causal_links` · `event_calendar` · `confidence_calibration` · `seo_pages`

**Key Schema Rules:**
- All prices: `DECIMAL(20, 8)` — never `FLOAT`
- All timestamps: `TIMESTAMPTZ` — never naive datetime
- Signal IDs: `UUID` (URL-safe, distributed-safe)
- Flexible data: `JSONB` for `technical_data` and `sentiment_data`
- `market_data` is a TimescaleDB hypertable on `timestamp`; indexed on `(symbol, timestamp DESC)`

Full SQL DDL: `docs/reference/database-schema.md`

---

## Coding Standards

### Python (Backend)

- Black (line length 100) + Ruff; type hints on ALL signatures; Google-style docstrings on all public functions
- `async def` on ALL FastAPI endpoints and DB operations — no sync functions in the request path
- `decimal.Decimal` for all prices — `float` is forbidden
- Never swallow exceptions silently — log + re-raise or handle explicitly
- All secrets via environment variables — no hardcoded keys

### TypeScript (Frontend)

- `"strict": true` — no `any` types; Prettier (2-space, single quotes, trailing commas)
- Functional components only; Zustand for global state; `useState`/`useReducer` for local
- Explicit `interface` props — never inline types; Tailwind only — no inline styles

### Shared Standards

- Conventional Commits: `feat:` `fix:` `test:` `docs:` `refactor:` `perf:` `ci:`
- No commented-out code; no TODO without a GitHub issue
- All API responses: `{ data: ..., meta: { timestamp, count } }`

---

## API Contract

**57 REST endpoints + 1 WebSocket.** Full table: `docs/reference/api.md`

| Category | Endpoints | Key paths |
|----------|-----------|-----------|
| Signals | 7 | `GET /api/v1/signals` · `GET /api/v1/signals/{id}` · feedback · share |
| History & Analytics | 7 | `/signals/history` · `/signals/stats` · `/signals/calibration` |
| Markets | 1 | `GET /api/v1/markets/overview` |
| Alerts | 5 | CRUD `/alerts/config` · `/alerts/watchlist` |
| Price Alerts | 3 | CRUD `/price-alerts` |
| Portfolio | 3 | `/portfolio/trades` · `/portfolio/summary` |
| Auth | 8 | register · login · refresh · logout · profile · password · delete |
| AI | 1 | `POST /api/v1/ai/ask` |
| News & Events | 7 | news · events · chains · calendar |
| Payments | 5 | subscription · plans · trial · subscribe · webhook |
| Backtest | 2 | run · result |
| Feedback | 3 | accuracy · weights · indicators |
| Admin | 2 | revenue · shadow-mode |
| SEO | 2 | list · slug |
| WebSocket | 2 | `POST /ws/ticket` · `WS /ws/signals` |

**Signal query params:** `market` · `signal_type` · `min_confidence` · `limit` (default 20, max 100) · `offset`

**WebSocket protocol:** client sends `{ type: "subscribe", markets: [...] }`; server streams `{ type: "signal"|"market_update"|"ping", data: {...} }`; client replies `{ type: "pong" }` to heartbeats.

---

## Signal Generation Algorithm

```
technical_score = weighted_avg([
  rsi_signal        × 0.20,
  macd_signal       × 0.25,
  bollinger_signal  × 0.15,
  volume_signal     × 0.15,
  sma_crossover     × 0.25,
])

final_confidence = (technical_score × 0.60) + (claude_sentiment × 0.40)
```

| Range | Signal |
|-------|--------|
| 80–100 | STRONG_BUY |
| 65–79 | BUY |
| 36–64 | HOLD |
| 21–35 | SELL |
| 0–20 | STRONG_SELL |

**ATR targets (14-period):** BUY → target = price + ATR×2, stop = price − ATR×1. SELL → inverse. R:R always ≥ 1:2.

---

## AI Engine — Claude Integration

- **Model:** `claude-sonnet-4-20250514` for all calls
- **All prompts in `services/ai_engine/prompts.py`** — never inline. Sentiment prompt returns JSON `{sentiment_score, key_factors, market_impact, time_horizon, confidence_in_analysis}`. Reasoning prompt returns plain text.
- **Budget:** $30/month hard cap via `cost_tracker.py` — wraps every API call
- **Caching:** sentiment scores cached in Redis 15 min; max 100 calls/hour
- **Fallback:** if budget exhausted, signals use technical analysis only (confidence capped at 60%)
- **Batching:** max 10 news articles per Claude call

---

## Celery Task Schedule

20 scheduled tasks defined in `backend/app/tasks/scheduler.py`.

| Task | Schedule | File |
|------|----------|------|
| fetch-indian-stocks | Every 1 min (NSE hours) | data_tasks.py |
| fetch-crypto-prices | Every 30 sec (24/7) | data_tasks.py |
| fetch-forex-rates | Every 1 min (24/5) | data_tasks.py |
| fetch-crypto-daily / fetch-forex-4h | 1h / 15min | data_tasks.py |
| run-technical-analysis | Every 5 min | analysis_tasks.py |
| run-sentiment-analysis | Every 1 hour | ai_tasks.py |
| generate-signals | Every 5 min | signal_tasks.py |
| resolve-signals | Every 15 min | signal_tasks.py |
| check-price-alerts | Every 1 min | price_alert_tasks.py |
| morning-brief / evening-wrap | 8:00 AM / 4:00 PM IST | alert_tasks.py |
| weekly-digest | Sunday 6 PM IST | alert_tasks.py |
| health-check / pipeline-health | 5 min / 15 min | data_tasks · alert_tasks |
| expire-stale-events | Every 1 hour | ai_tasks.py |
| seed-calendar-events | 6:00 AM IST daily | calendar_tasks.py |
| check-expired-subscriptions | Every 1 hour | subscription_tasks.py |
| generate-seo-pages | 8:30 AM IST daily | seo_tasks.py |
| free-tier-digest / reengagement | Sun 6:30 PM / Wed 10 AM | engagement_tasks.py |

**Market hours:** NSE/BSE 9:15–15:30 IST Mon–Fri. Crypto 24/7. Forex 24/5. Tasks skip fetches when market is closed.

---

## Data Sources & API Keys

See `.env.example` for all variables. Key groups:
- **DB:** `DATABASE_URL` · `REDIS_URL`
- **AI:** `ANTHROPIC_API_KEY` · `MONTHLY_AI_BUDGET_USD=30`
- **Market data:** `ALPHA_VANTAGE_API_KEY` · `BINANCE_API_KEY/SECRET` · `COINMARKETCAP_API_KEY`
- **Alerts:** `TELEGRAM_BOT_TOKEN` · `TELEGRAM_DEFAULT_CHAT_ID`
- **Auth:** `JWT_SECRET_KEY` · `JWT_ALGORITHM=HS256` · expire 30min/7days
- **Payments:** `RAZORPAY_KEY_ID/SECRET/WEBHOOK_SECRET` + plan IDs (₹499/mo, ₹4999/yr)
- **App:** `ENVIRONMENT` · `SENTRY_DSN` · `API_SECRET_KEY` · `INTERNAL_API_KEY`

**Rate limit strategies:** Alpha Vantage → 12-sec spacing; Binance → WebSocket not REST; Yahoo Finance → batch symbols; Claude → budget tracking + cache.

---

## Frontend Design System

**Theme:** Dark trading terminal. Bloomberg meets fintech.
- Colors: bg `#0A0B0F` / `#12131A`; signal-buy `#00E676`; signal-sell `#FF5252`; signal-hold `#FFD740`; accent `#6366F1`
- Fonts: Outfit (display/body) + JetBrains Mono (prices, data)

**Component rules:**
- Signal cards: expandable. Collapsed = gauge + sparkline + badge. Expanded = AI reasoning + indicators + targets.
- Confidence Gauge: SVG circular progress, color matches signal type
- Animations: 0.3s fade-in for new signals only
- Mobile-first — fully usable on phone
- Loading: skeleton screens; Errors: friendly + retry button

---

## Telegram Bot

| Command | Response |
|---------|---------|
| `/start` | Welcome + store chat_id |
| `/signals` | Top 5 by confidence |
| `/config` | Inline keyboard for markets/min-confidence |
| `/markets` | NIFTY · BTC · EUR/USD snapshots |
| `/history` | Last 5 resolved signals |
| `/stop` / `/resume` | Pause / resume alerts |

Alert format: `🟢/🔴/🟡 SIGNAL_TYPE — SYMBOL`, price, confidence bar, targets, timeframe, AI reasoning, indicator summary.

---

## Testing Strategy

**Coverage target:** ≥80% on backend services.

**Key rules:**
- Mock all external APIs (Claude, Binance, Yahoo Finance) — never call real APIs in tests
- Test the full pipeline integration: data → indicators → AI → signal → delivery
- Write tests alongside features, not after
- Pre-commit: full suite must be green + Docker build must succeed

### Identity & Auth Testing (MANDATORY)

> **Lesson learned:** JWT auth was added but user-scoped endpoints kept querying by `telegram_chat_id`. Web users have `telegram_chat_id = NULL` → silent failures ("Failed to load portfolio"). Missed because fixtures always injected `telegram_chat_id=12345`.

**Rules to prevent recurrence:**

1. Every user-scoped endpoint tested with BOTH identities:
   - `AuthContext(user_id="...", telegram_chat_id=12345)` — Telegram user
   - `AuthContext(user_id="...", telegram_chat_id=None)` — web-only user
   - See `tests/test_web_user_identity.py` for canonical pattern

2. After any auth/identity model change: run `pytest tests/test_web_user_identity.py` and verify portfolio, watchlist, alerts, price alerts, trades all work with web-only user.

3. When adding `user_id` to existing tables: nullable column + update ALL queries to `or_(Model.user_id == uid, Model.telegram_chat_id == chat_id)`.

---

## Deployment

Railway hosts backend in single container via `supervisord.conf`:
1. `migrate` — `alembic upgrade head` once at startup
2. `web` — uvicorn on `$PORT`
3. `celery-worker` — 2 concurrent workers
4. `celery-beat` — scheduler

**Production checklist:** env vars set · migrations applied · Celery Beat firing · WebSocket stable · Telegram bot responding · Sentry configured · UptimeRobot on `/health` · Claude cost tracking active · CORS locked to prod domain.

---

## Important Constraints & Rules

### Non-Negotiable

1. **NOT financial advice.** Every signal includes AI-generated disclaimer. Telegram welcome + dashboard footer must show it.
2. **No auto-trading.** Signals are advisory only.
3. **Every signal MUST have a stop-loss.** R:R ≥ 1:2 always.
4. **All prices as `decimal.Decimal`.** Never `float`.
5. **$30/month Claude budget.** Hard cap enforced by `cost_tracker.py`.
6. **Services are independent.** If Claude API is down, technical signals still work. If one market source is down, others continue.
7. **Idempotent Celery tasks.** Safe to retry; duplicate fetches update, not duplicate rows.
8. **All prompts in `prompts.py`.** Never inline.
9. **TIMESTAMPTZ everywhere.** No naive datetimes.
10. **Identity dual test.** Every user-scoped endpoint tested with both Telegram user and web-only user.

---

## Quick Reference — File to Edit for Each Change

| I need to... | Edit this file |
|-------------|---------------|
| Add symbol | `backend/app/config.py` |
| Add indicator | `services/analysis/indicators.py` |
| Change scoring weights | `services/signal_gen/scorer.py` |
| Edit a Claude prompt | `services/ai_engine/prompts.py` |
| Add API endpoint | `backend/app/api/<domain>.py` + `router.py` |
| Change task schedule | `backend/app/tasks/scheduler.py` |
| Add DB table | `backend/app/models/` + alembic migration |
| Change alert format | `services/alerts/formatter.py` |
| Add Telegram command | `services/alerts/telegram_bot.py` |
| Change auth/JWT | `backend/app/auth.py` |
| Change tier gating | `services/tier_gating.py` + `frontend/src/lib/tiers.ts` |
| Add frontend page | `frontend/src/app/<route>/page.tsx` |
| Add component | `frontend/src/components/<domain>/` |
| Update project instructions | This file (CLAUDE.md) |

---

## Project History & Current State

**Latest tag:** v1.3.0 (27 March 2026). HEAD ahead with nav reorganization + v1.5 audit fixes (unreleased). CHANGELOG missing v1.2.0 and v1.3.0 entries.

### Key Metrics

| Metric | Count |
|--------|-------|
| Backend Python files | 99 (14,400+ lines) |
| Frontend TypeScript files | 98 (12,500+ lines) |
| API endpoints | 57 REST + 1 WebSocket |
| DB model files | 18 |
| Tracked symbols | 31 (15 stocks · 10 crypto · 6 forex) |
| Backend tests | 65 files · 1,241 collected |
| Frontend tests | 79 files · 741 passing |
| React components | 55 |
| Pages | 20 |
| Zustand stores / hooks | 5 / 5 |
| Celery tasks | 20 |
| Alembic migrations | 11 |
| Git tags | v0.0.1–v0.0.3 · v1.0.0–v1.3.0 |

### Known Issues

- `origin/feature/phase4-integration-deploy` remote branch still exists (needs GitHub settings to delete)
- CHANGELOG.md missing v1.2.0 and v1.3.0 entries

---

## AI Powerhouse Integration

> **Submodule:** `external/ai-powerhouse` (fully initialized)
> **Installed:** 279 agents · 365 skills · 280 commands in `~/.claude` (2026-04-11)
> **Rule:** The `UserPromptSubmit` hook auto-routes every prompt — watch for `[ROUTE]` output.

### Two-Tier Agent System

**Tier 1 — Project agents** (`.claude/agents/signalflow/`): SignalFlow architecture context.
**Tier 2 — Specialist agents** (`~/.claude/agents/`): deep technical expertise.

### Routing Table

| Domain | Project Agent | Specialist Agents |
|--------|--------------|-------------------|
| FastAPI endpoints | `signalflow-backend` | `ws-api-scaffolding-fastapi-pro` |
| Celery / Redis tasks | `signalflow-backend` | `ws-python-development-python-pro` |
| PostgreSQL / TimescaleDB / Alembic | `signalflow-backend` | `ws-database-design-sql-pro` · `ws-database-migrations-database-admin` |
| Claude API / AI engine / prompts | `signalflow-ai-engine` | `ws-llm-application-dev-ai-engineer` |
| Signal scoring / pipeline | `signalflow-signal` | `ws-backend-development-tdd-orchestrator` |
| Market data / indicators | `signalflow-data` | `ws-python-development-python-pro` |
| JWT / auth / Razorpay | `signalflow-security` | `ecc-security-reviewer` |
| Next.js / React / Tailwind | `signalflow-frontend` | `ecc-typescript-reviewer` |
| MKG knowledge graph | `signalflow-backend` | `ws-backend-development-backend-architect` |
| TDD / test writing | — | `ecc-tdd-guide` · `ws-backend-development-tdd-orchestrator` |
| Code review | — | `ecc-code-reviewer` · `ecc-python-reviewer` · `superpowers-code-reviewer` |
| Security audit | — | `ecc-security-reviewer` · `gsd-security-auditor` |
| Performance | — | `ecc-performance-optimizer` · `ws-backend-development-performance-engineer` |
| Debugging | — | `gsd-debugger` · `ws-error-debugging-error-detective` |
| Refactor | — | `ecc-refactor-cleaner` · `sc-refactoring-expert` |
| Observability | — | `ws-observability-monitoring-observability-engineer` |
| Architecture | — | `ecc-architect` · `sc-system-architect` |
| Build errors | — | `ecc-build-error-resolver` |
| DevOps / Docker | — | `ws-cicd-automation-deployment-engineer` |

### Key Skills

```
ecc-python-patterns · ecc-python-testing · ecc-postgres-patterns · ecc-database-migrations
ecc-claude-api · ecc-cost-aware-llm-pipeline · ecc-llm-trading-agent-security
ws-fastapi-templates · ws-async-python-patterns · ws-python-background-jobs
ws-postgresql · ws-python-testing-patterns · ws-python-observability · ws-llm-evaluation
```

### Key Commands

```bash
/ecc-tdd           # TDD workflow (tests first)
/ecc-python-review # Python code quality review
/ecc-code-review   # General quality review
/ecc-plan          # Implementation planning
/ecc-verify        # Pre-commit checklist
/gsd-debug         # Structured debugging
/gsd-code-review   # Structured code review
```

### Daily Workflow

```
1. Before any new work  → check memory for prior patterns
2. For any feature      → /ecc-plan → ecc-tdd-guide → ecc-python-reviewer
                          (+ ecc-security-reviewer if touching auth/payments/AI)
3. Before commit        → /ecc-verify → tests green + docker build clean
4. For AI engine work   → ecc-claude-api + ecc-cost-aware-llm-pipeline skills
```

### Updating the Submodule

```bash
cd external/ai-powerhouse && git submodule update --remote --merge
cd ../.. && git add external/ai-powerhouse
git commit -m "chore: update ai-powerhouse submodule"
bash external/ai-powerhouse/master/install.sh
```

---

*Last updated: 12 April 2026 | SignalFlow AI v1.3.0 + unreleased*
