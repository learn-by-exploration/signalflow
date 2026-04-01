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
3. **Test-driven**: Every feature includes tests. 1,980+ tests pass before each commit.
4. **Review cycles**: Multi-expert AI reviews (architect, UI experts, finance professionals, PMs) were used for UI iteration rounds.

### GAN-Based TDD Protocol (MANDATORY for MKG Development)

All MKG implementation follows a **Generative Adversarial Network (GAN)** protocol where two personas operate in a strict loop for every component:

**Persona A — The Generator (Lead Developer):**
- Follows strict TDD: writes failing tests first (Red), writes minimal production code to pass (Green), then refactors (Refactor)
- Produces test suites and implementation code

**Persona B — The Discriminator (Adversarial Reviewer & QA Lead):**
- Acts as a ruthless critic — sole goal is finding flaws, edge cases, security vulnerabilities, or SOLID violations
- Issues `[PASS]` or `[REJECT]` with specific bullet points for each review

**Execution Loop for EVERY Component:**

```
1. [GENERATOR - TEST]    → Generator writes test suite for current component
2. [DISCRIMINATOR - REVIEW] → Reviews tests for completeness and edge cases
   → [REJECT] → Generator rewrites tests
   → [PASS]   → Proceed to code
3. [GENERATOR - CODE]    → Generator writes production code to satisfy tests
4. [DISCRIMINATOR - REVIEW] → Attacks code for performance, coupling, security
   → [REJECT] → Generator rewrites code (with specific fixes)
   → [PASS]   → Component complete, present to user for approval
```

**Rules:**
- Both test [PASS] and code [PASS] required before presenting a component
- The REJECT/PASS dialogue must be shown for each component
- No component moves forward until the Discriminator is satisfied
- Each component requires explicit user approval before the next one starts

### Core Project Directives (MANDATORY for ALL AI Agent Sessions)

**These directives apply to every coding session, not just MKG. All AI agents must follow them.**

#### Directive 1: TDD is Non-Negotiable
- ALL feature development must begin with a test
- Writing production logic without first providing the unit/integration test that expects it is forbidden
- Follow **Red → Green → Refactor** strictly

#### Directive 2: Multi-Stakeholder Alignment
Before suggesting major architectural changes or adding new libraries, silently check against three personas:
- **PM:** Does this delay the launch?
- **Banker:** Does this increase infrastructure costs?
- **QA:** Does this make the system harder to test?

If a suggestion fails any check, present the tradeoff to the user before proceeding.

#### Directive 3: Code Quality & Standards
- **Simplicity over cleverness:** Write readable, maintainable code
- **SOLID Principles:** Adhere to single responsibility and dependency inversion
- **Security First:** Always sanitize inputs and assume hostile user behavior

#### Directive 4: Output Formatting
- Keep conversational filler to an absolute minimum
- When providing code, always provide the file path at the top of the code block
- When refactoring, explain *why* the refactor is necessary (e.g., performance, readability, DRY)

#### Directive 5: State Management & Check-ins
- If the context gets too long, summarize the current state of the application before writing the next test
- Always end your response by asking for confirmation to proceed to the next logical step

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

## Project Structure (as of v1.3.0)

```
signalflow/
├── CLAUDE.md                        # THIS FILE — master instructions
├── CHANGELOG.md                     # Version changelog
├── CONTRIBUTING.md                  # Contributor guidelines
├── README.md                        # Project readme with setup guide
├── SECURITY.md                      # Security policy
├── Makefile                         # Development shortcuts (make up/test/lint)
├── docker-compose.yml               # Local dev: 6 services (db, redis, backend, celery, flower, frontend)
├── docker-compose.prod.yml          # Production overrides
├── railway.toml                     # Railway PaaS deployment config
├── supervisord.conf                 # Process manager: web + celery-worker + celery-beat + migrate
├── start.sh                         # Service bootstrap script
├── .env.example                     # Environment variables template
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, health, metrics, rate limiting
│   │   ├── auth.py                  # JWT authentication, AuthContext, token management
│   │   ├── config.py                # Settings: 40+ env vars + 31 tracked symbols
│   │   ├── database.py              # SQLAlchemy async (pool=20, overflow=10)
│   │   ├── rate_limit.py            # Slowapi rate limiting config
│   │   │
│   │   ├── models/                  # 18 SQLAlchemy ORM model files
│   │   │   ├── market_data.py       # TimescaleDB hypertable (OHLCV)
│   │   │   ├── signal.py            # Signal model
│   │   │   ├── signal_history.py    # Signal outcome tracking
│   │   │   ├── signal_feedback.py   # User feedback (took/watching/skipped)
│   │   │   ├── signal_share.py      # Signal sharing with public URLs
│   │   │   ├── signal_news_link.py  # Signal ↔ news article links
│   │   │   ├── alert_config.py      # Alert preferences + watchlist
│   │   │   ├── price_alert.py       # Price-triggered alerts
│   │   │   ├── trade.py             # Portfolio trade log
│   │   │   ├── backtest.py          # Backtest run results
│   │   │   ├── user.py              # User accounts (JWT auth)
│   │   │   ├── subscription.py      # Razorpay subscriptions + tiers
│   │   │   ├── news_event.py        # News articles
│   │   │   ├── event_entity.py      # Extracted entities from news
│   │   │   ├── event_calendar.py    # Earnings/macro event calendar
│   │   │   ├── causal_link.py       # Causal chains between events
│   │   │   ├── confidence_calibration.py # Calibration tracking
│   │   │   └── seo_page.py          # Generated SEO content
│   │   │
│   │   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   │   ├── signal.py            # Signal, History, Stats, TrackRecord, WeeklyTrend
│   │   │   ├── market.py            # MarketSnapshot, MarketOverview
│   │   │   ├── alert.py             # AlertConfig request/response
│   │   │   ├── auth.py              # Register, Login, Token schemas
│   │   │   ├── news.py              # NewsEvent, EventEntity schemas
│   │   │   └── p3.py                # PriceAlert, Backtest, Portfolio schemas
│   │   │
│   │   ├── api/                     # ~57 REST endpoints + 1 WebSocket
│   │   │   ├── router.py            # Main router aggregator
│   │   │   ├── signals.py           # GET /signals, GET /signals/{id}
│   │   │   ├── markets.py           # GET /markets/overview
│   │   │   ├── alerts.py            # CRUD /alerts/config, watchlist
│   │   │   ├── history.py           # GET /signals/history, /stats, /track-record, /calibration
│   │   │   ├── portfolio.py         # GET/POST /portfolio/trades, /summary
│   │   │   ├── price_alerts.py      # CRUD /price-alerts
│   │   │   ├── sharing.py           # POST /signals/{id}/share, GET /shared/{id}
│   │   │   ├── ai_qa.py             # POST /ai/ask
│   │   │   ├── backtest.py          # POST /backtest, GET /backtest/{id}
│   │   │   ├── auth_routes.py       # POST /auth/register, /login, /refresh, /logout, etc.
│   │   │   ├── admin.py             # GET /admin/revenue, /shadow-mode
│   │   │   ├── feedback.py          # GET /feedback/accuracy, /weights, /indicators
│   │   │   ├── news.py              # GET /news, /events, /chains, /calendar
│   │   │   ├── payments.py          # GET/POST /payments/subscription, /trial, /webhook
│   │   │   ├── seo.py               # GET /seo/, /seo/{slug}
│   │   │   ├── signal_feedback.py   # POST/GET /signals/{id}/feedback
│   │   │   └── websocket.py         # WS /ws/signals + POST /ws/ticket
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── cache.py             # Redis caching utilities
│   │   │   ├── metrics.py           # Prometheus metric collectors
│   │   │   ├── pubsub.py            # Redis pub/sub for real-time events
│   │   │   ├── revenue.py           # Revenue tracking & reporting
│   │   │   ├── seo.py               # SEO page generation
│   │   │   ├── tier_gating.py       # Feature gating by subscription tier
│   │   │   ├── earnings_calendar.py # Earnings date tracking
│   │   │   │
│   │   │   ├── data_ingestion/      # 3 market fetchers + market hours
│   │   │   │   ├── base.py          # Abstract base fetcher
│   │   │   │   ├── indian_stocks.py # yfinance (15 NSE symbols)
│   │   │   │   ├── crypto.py        # Binance WebSocket (10 pairs)
│   │   │   │   ├── forex.py         # Alpha Vantage (6 pairs)
│   │   │   │   ├── market_hours.py  # NSE/Forex/Crypto schedule awareness
│   │   │   │   └── validators.py    # Data quality validation
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
│   │   │   │   ├── cost_tracker.py  # $30/month budget enforcement
│   │   │   │   ├── dedup.py         # News deduplication
│   │   │   │   ├── event_chain.py   # Causal event chain analysis
│   │   │   │   ├── finbert_eval.py  # FinBERT evaluation utilities
│   │   │   │   └── sanitizer.py     # Prompt injection prevention
│   │   │   │
│   │   │   ├── signal_gen/          # Signal generation pipeline
│   │   │   │   ├── generator.py     # SignalGenerator: data → analysis → AI → signal
│   │   │   │   ├── scorer.py        # Scoring: tech×0.6 + sentiment×0.4
│   │   │   │   ├── targets.py       # ATR-based target/stop-loss (1:2 R:R)
│   │   │   │   ├── calibration.py   # Confidence calibration from historical accuracy
│   │   │   │   ├── feedback.py      # Adaptive feedback loop
│   │   │   │   ├── mtf_confirmation.py  # Multi-timeframe signal confirmation
│   │   │   │   ├── risk_guard.py    # Per-sector/market position limits
│   │   │   │   ├── shadow_mode.py   # Shadow mode for testing new strategies
│   │   │   │   └── streak_protection.py # Consecutive loss protection
│   │   │   │
│   │   │   ├── alerts/              # Alert dispatch
│   │   │   │   ├── telegram_bot.py  # Telegram commands (/start, /signals, /config, etc.)
│   │   │   │   ├── formatter.py     # Message formatters
│   │   │   │   └── dispatcher.py    # Alert routing + retry logic
│   │   │   │
│   │   │   └── payment/             # Payment integration
│   │   │       └── razorpay_service.py  # Razorpay subscription management
│   │   │
│   │   └── tasks/                   # 20 Celery scheduled tasks
│   │       ├── _engine.py           # Shared task engine utilities
│   │       ├── celery_app.py        # Celery app config
│   │       ├── scheduler.py         # Beat schedule definition
│   │       ├── data_tasks.py        # Market fetcher tasks (stocks, crypto, forex + MTF)
│   │       ├── analysis_tasks.py    # Technical analysis task
│   │       ├── ai_tasks.py          # Sentiment analysis + event chain expiry
│   │       ├── signal_tasks.py      # Signal generation + resolution
│   │       ├── alert_tasks.py       # Morning brief, evening wrap, weekly digest, pipeline health
│   │       ├── price_alert_tasks.py # Price alert checking
│   │       ├── backtest_tasks.py    # On-demand backtesting
│   │       ├── calendar_tasks.py    # Earnings/macro event calendar seeding
│   │       ├── engagement_tasks.py  # Free-tier digest, re-engagement nudges
│   │       ├── seo_tasks.py         # SEO content generation
│   │       └── subscription_tasks.py # Subscription expiry checks
│   │
│   ├── migrations/                  # 11 Alembic migrations
│   │   └── versions/
│   │       ├── b0396d5bb542_initial_schema.py
│   │       ├── c4a8f2d1e3b5_add_watchlist_column.py
│   │       ├── d5b9e3f4a6c7_add_p3_tables.py
│   │       ├── e6c0a5d7b8f9_add_news_event_tables.py
│   │       ├── f7d1b2c3e4a5_add_missing_news_columns.py
│   │       ├── g8e2c4d5f6a7_add_users_and_refresh_tokens.py
│   │       ├── h9f3d5e6g7b8_add_user_id_to_trades_and_alerts.py
│   │       ├── i0a4b6c8d2e3_add_timeframe_to_market_data.py
│   │       ├── j1b5c7d9e3f4_add_subscriptions_table.py
│   │       ├── k2c6d8e0f4g5_add_seo_pages_table.py
│   │       └── a1b2c3d4e5f6_add_security_constraints.py
│   │
│   ├── scripts/                     # Utility scripts
│   │   ├── seed.py                  # Database seeding
│   │   ├── seed_demo_signals.py     # Demo signal data
│   │   └── backup.sh               # Database backup
│   │
│   ├── tests/                       # 65 test files, 1,117+ backend tests
│   │   ├── conftest.py              # Fixtures: test DB, test client, mocks
│   │   ├── test_indicators*.py      # Technical indicator tests
│   │   ├── test_signal_*.py         # Signal gen, scorer, resolution tests
│   │   ├── test_ai_*.py             # AI engine, budget, cost tracker tests
│   │   ├── test_api_*.py            # API endpoint tests
│   │   ├── test_auth_*.py           # JWT auth, password account tests
│   │   ├── test_security_*.py       # Security sprint regression tests
│   │   ├── test_breaker_*.py        # Adversarial/breaker tests
│   │   ├── test_v14_*.py            # v1.4 feature tests
│   │   ├── test_websocket.py        # WebSocket delivery tests
│   │   ├── test_pipeline_*.py       # Integration pipeline tests
│   │   ├── test_web_user_identity.py # Web-only user identity tests
│   │   └── test_sprint*_*.py        # Sprint regression tests
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── middleware.ts            # Next.js middleware (auth, redirects)
│   │   │
│   │   ├── app/                     # 20+ pages (Next.js App Router)
│   │   │   ├── layout.tsx           # Root layout (Outfit + JetBrains Mono fonts)
│   │   │   ├── page.tsx             # Dashboard / Landing page
│   │   │   ├── globals.css          # Tailwind + dark theme CSS vars
│   │   │   ├── signal/[id]/page.tsx # Signal detail: chart, indicators, risk calc
│   │   │   ├── history/page.tsx     # Signal history with outcome filters
│   │   │   ├── portfolio/page.tsx   # Trade log, positions, P&L
│   │   │   ├── alerts/page.tsx      # Alert config, watchlist
│   │   │   ├── backtest/page.tsx    # Historical backtesting
│   │   │   ├── how-it-works/page.tsx# Educational guide
│   │   │   ├── shared/[id]/page.tsx # Public shared signal view
│   │   │   ├── auth/signin/page.tsx # Sign-in page
│   │   │   ├── auth/signup/page.tsx # Sign-up page
│   │   │   ├── brief/page.tsx       # AI market briefs
│   │   │   ├── calendar/page.tsx    # Economic/earnings calendar
│   │   │   ├── contact/page.tsx     # Contact page
│   │   │   ├── news/page.tsx        # News intelligence dashboard
│   │   │   ├── pricing/page.tsx     # Subscription pricing
│   │   │   ├── privacy/page.tsx     # Privacy policy
│   │   │   ├── refund-policy/page.tsx # Refund policy
│   │   │   ├── settings/page.tsx    # User settings
│   │   │   ├── terms/page.tsx       # Terms of service
│   │   │   ├── track-record/page.tsx# Signal track record
│   │   │   ├── watchlist/page.tsx   # Symbol watchlist
│   │   │   └── api/                 # Next.js API proxy routes
│   │   │
│   │   ├── components/              # 55 React components
│   │   │   ├── signals/             # SignalFeed, SignalCard, SimpleSignalCard,
│   │   │   │                        # SignalBadge, ConfidenceGauge, ConfidenceBreakdown,
│   │   │   │                        # AIReasoningPanel, TargetProgressBar,
│   │   │   │                        # RiskCalculator, PipCalculator,
│   │   │   │                        # WinRateCard, AccuracyChart, ShareButton,
│   │   │   │                        # AskAI, EventTimeline, TrailingStopSuggestion
│   │   │   ├── markets/             # MarketOverview, MarketHeatmap, Sparkline
│   │   │   ├── charts/              # AllocationPieChart, BenchmarkComparison,
│   │   │   │                        # CandlestickChart, EquityCurve
│   │   │   ├── alerts/              # AlertTimeline, AlertConfig
│   │   │   ├── dashboard/           # DashboardContent
│   │   │   ├── landing/             # LandingPage
│   │   │   └── shared/              # Navbar, BottomNav, MobileMenuSheet, SiteFooter,
│   │   │                            # WelcomeModal, ChatIdPrompt, LoadingSpinner,
│   │   │                            # ErrorBoundary, KeyboardHelpModal, Toast,
│   │   │                            # IndicatorPill, IndicatorTooltip, Skeleton,
│   │   │                            # AuthProvider, SessionSync, QueryProvider,
│   │   │                            # ThemeProvider, TextSizeProvider,
│   │   │                            # CollapsibleSection, CookieConsent,
│   │   │                            # FocusTrap, GuidedTour, NotificationCenter,
│   │   │                            # OfflineBanner, SebiDisclaimer, SettingsPanel,
│   │   │                            # SymbolAutocomplete, UpgradePrompt
│   │   │
│   │   ├── hooks/                   # 5 custom hooks
│   │   │   ├── useSignals.ts        # REST signal fetching
│   │   │   ├── useMarketData.ts     # Market data fetching
│   │   │   ├── useWebSocket.ts      # WebSocket + auto-reconnect
│   │   │   ├── useKeyboardShortcuts.ts # Global keyboard shortcuts
│   │   │   └── useQueries.ts        # React Query hooks
│   │   │
│   │   ├── store/                   # 5 Zustand stores
│   │   │   ├── signalStore.ts       # Signals, filters, unseen count
│   │   │   ├── marketStore.ts       # Market snapshots, WS status
│   │   │   ├── userStore.ts         # Auth tokens, user state (sessionStorage)
│   │   │   ├── preferencesStore.ts  # User UI preferences
│   │   │   └── tierStore.ts         # Subscription tier state
│   │   │
│   │   ├── lib/                     # Shared utilities
│   │   │   ├── api.ts               # REST client for /api/v1
│   │   │   ├── auth.ts              # Auth helpers (token refresh, interceptors)
│   │   │   ├── websocket.ts         # WebSocket client class
│   │   │   ├── types.ts             # 25+ TypeScript interfaces
│   │   │   ├── constants.ts         # Colors, thresholds, badge labels, nav links
│   │   │   ├── notifications.ts     # Browser notification helpers
│   │   │   └── tiers.ts             # Tier feature gates
│   │   │
│   │   ├── utils/
│   │   │   ├── formatters.ts        # Price, %, date, time formatting
│   │   │   └── market-hours.ts      # Market open/close detection
│   │   │
│   │   └── __tests__/               # 79 frontend test files, 741 tests
│   │       ├── setup.ts             # Test setup (jsdom, mocks)
│   │       ├── helpers.ts            # Test utilities
│   │       └── *.test.{tsx,ts}      # Component, hook, store, utility tests
│   │
│   ├── package.json
│   ├── tsconfig.json                # strict: true, @/* path alias
│   ├── tailwind.config.ts           # Dark theme color tokens
│   ├── vitest.config.ts             # Vitest configuration
│   └── Dockerfile
│
└── docs/
    ├── README.md                    # Docs index
    ├── compliance/                  # Regulatory & data breach templates
    ├── decisions/                   # Architecture decision records
    ├── design/                      # Spec documents (v1–v4), nav reorganization
    ├── guides/                      # Developer guides
    ├── operations/                  # Ops runbooks
    ├── reference/                   # API & technical references
    ├── research/                    # Research notes
    ├── review/                      # Code review findings
    ├── reviews/                     # Multi-agent & expert reviews
    ├── security/                    # Security reports & hardening plans
    └── sprints/                     # Sprint plans (1-4 + v1.1, v1.2)
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
| GET | `/health` | Health check + system status | `{ status, uptime, ... }` |
| GET | `/metrics` | Prometheus metrics | text/plain |
| **Signals** | | | |
| GET | `/api/v1/signals` | List active signals | `{ data: Signal[], meta }` |
| GET | `/api/v1/signals/{id}` | Signal detail | `{ data: Signal }` |
| POST | `/api/v1/signals/{id}/feedback` | Submit signal feedback | `{ data: ... }` |
| GET | `/api/v1/signals/{id}/feedback` | Get signal feedback | `{ data: ... }` |
| POST | `/api/v1/signals/{id}/share` | Create shareable link | `{ data: { share_id } }` |
| GET | `/api/v1/signals/shared/{id}` | View shared signal | `{ data: Signal }` |
| **History & Analytics** | | | |
| GET | `/api/v1/signals/history` | Past signals with outcomes | `{ data: SignalHistory[], meta }` |
| GET | `/api/v1/signals/stats` | Aggregate signal statistics | `{ data: SignalStats }` |
| GET | `/api/v1/signals/stats/trend` | Weekly trend data | `[WeeklyTrendItem]` |
| GET | `/api/v1/signals/{symbol}/track-record` | Per-symbol track record | `SymbolTrackRecord` |
| GET | `/api/v1/signals/performance` | Performance metrics | `{ data: ... }` |
| GET | `/api/v1/signals/streak-check` | Consecutive loss check | `{ data: ... }` |
| GET | `/api/v1/signals/calibration` | Confidence calibration | `{ data: ... }` |
| **Markets** | | | |
| GET | `/api/v1/markets/overview` | Live market snapshot | `{ data: { stocks, crypto, forex } }` |
| **Alerts** | | | |
| GET | `/api/v1/alerts/config` | Get alert preferences | `{ data: AlertConfig }` |
| POST | `/api/v1/alerts/config` | Create alert config | `{ data: AlertConfig }` |
| PUT | `/api/v1/alerts/config/{id}` | Update alert config | `{ data: AlertConfig }` |
| GET | `/api/v1/alerts/watchlist` | Get watchlist | `{ data: [...] }` |
| POST | `/api/v1/alerts/watchlist` | Add to watchlist | `{ data: ... }` |
| **Price Alerts** | | | |
| GET | `/api/v1/price-alerts` | List price alerts | `{ data: [...] }` |
| POST | `/api/v1/price-alerts` | Create price alert | `{ data: ... }` |
| DELETE | `/api/v1/price-alerts/{id}` | Delete price alert | `{ data: ... }` |
| **Portfolio** | | | |
| GET | `/api/v1/portfolio/trades` | List trades | `{ data: [...] }` |
| POST | `/api/v1/portfolio/trades` | Log a trade | `{ data: ... }` |
| GET | `/api/v1/portfolio/summary` | Portfolio summary/P&L | `{ data: ... }` |
| **Auth** | | | |
| POST | `/api/v1/auth/register` | Create account | `{ data: { tokens, user } }` |
| POST | `/api/v1/auth/login` | Login | `{ data: { tokens, user } }` |
| POST | `/api/v1/auth/refresh` | Refresh JWT | `{ data: { access_token } }` |
| POST | `/api/v1/auth/logout` | Logout (revoke token) | `{ data: ... }` |
| POST | `/api/v1/auth/logout-all` | Logout all sessions | `{ data: ... }` |
| GET | `/api/v1/auth/profile` | Get user profile | `{ data: User }` |
| PUT | `/api/v1/auth/password` | Change password | `{ data: ... }` |
| DELETE | `/api/v1/auth/account` | Delete account | `{ data: ... }` |
| **AI** | | | |
| POST | `/api/v1/ai/ask` | Ask Claude about a symbol | `{ data: { answer } }` |
| **News & Events** | | | |
| GET | `/api/v1/news` | List news events | `NewsEventListResponse` |
| GET | `/api/v1/news/signal/{id}` | News linked to signal | `NewsEventListResponse` |
| GET | `/api/v1/news/events` | Entity events | `EventEntityListResponse` |
| GET | `/api/v1/news/events/{id}` | Event detail | `{ data: ... }` |
| GET | `/api/v1/news/chains/{symbol}` | Causal chains for symbol | `{ data: ... }` |
| GET | `/api/v1/news/calendar` | Event calendar | `EventCalendarListResponse` |
| POST | `/api/v1/news/calendar` | Create calendar event | `{ data: ... }` |
| **Payments** | | | |
| GET | `/api/v1/payments/subscription` | Get subscription status | `{ data: ... }` |
| GET | `/api/v1/payments/plans` | List subscription plans | `{ data: ... }` |
| POST | `/api/v1/payments/trial` | Start free trial | `{ data: ... }` |
| POST | `/api/v1/payments/subscribe` | Create subscription | `{ data: ... }` |
| POST | `/api/v1/payments/webhook` | Razorpay webhook | — |
| **Backtest** | | | |
| POST | `/api/v1/backtest/run` | Run backtest | `{ data: BacktestRun }` |
| GET | `/api/v1/backtest/{id}` | Get backtest result | `{ data: BacktestRun }` |
| **Feedback Loop** | | | |
| GET | `/api/v1/feedback/accuracy` | Accuracy metrics | `{ data: ... }` |
| GET | `/api/v1/feedback/weights` | Adaptive weights | `{ data: ... }` |
| GET | `/api/v1/feedback/indicators` | Indicator performance | `{ data: ... }` |
| **Admin** | | | |
| GET | `/api/v1/admin/revenue` | Revenue dashboard | `{ data: ... }` |
| GET | `/api/v1/admin/shadow-mode` | Shadow mode results | `{ data: ... }` |
| **SEO** | | | |
| GET | `/api/v1/seo/` | List SEO pages | `{ data: [...] }` |
| GET | `/api/v1/seo/{slug}` | Get SEO page | `{ data: ... }` |
| **WebSocket** | | | |
| POST | `/ws/ticket` | Get WS auth ticket | `{ data: { ticket } }` |
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
        "task": "app.tasks.data_tasks.fetch_indian_stocks",
        "schedule": 60.0,                               # Every 1 min (during NSE hours only)
    },
    "fetch-crypto-prices": {
        "task": "app.tasks.data_tasks.fetch_crypto",
        "schedule": 30.0,                               # Every 30 sec (24/7)
    },
    "fetch-forex-rates": {
        "task": "app.tasks.data_tasks.fetch_forex",
        "schedule": 60.0,                               # Every 1 min (24/5)
    },

    # ── Multi-Timeframe Data (for MTF confirmation) ──
    "fetch-crypto-daily": {
        "task": "app.tasks.data_tasks.fetch_crypto_daily",
        "schedule": 3600.0,                             # Every hour — daily candle
    },
    "fetch-forex-4h": {
        "task": "app.tasks.data_tasks.fetch_forex_4h",
        "schedule": 900.0,                              # Every 15 min — 4h candle
    },

    # ── Analysis ──
    "run-technical-analysis": {
        "task": "app.tasks.analysis_tasks.run_analysis",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── AI Engine ──
    "run-sentiment-analysis": {
        "task": "app.tasks.ai_tasks.run_sentiment",
        "schedule": 3600.0,                             # Every 1 hour
    },

    # ── Signal Generation ──
    "generate-signals": {
        "task": "app.tasks.signal_tasks.generate_signals",
        "schedule": 300.0,                              # Every 5 min
    },

    # ── Digests ──
    "morning-brief": {
        "task": "app.tasks.alert_tasks.morning_brief",
        "schedule": crontab(hour=8, minute=0),          # 8:00 AM IST daily
    },
    "evening-wrap": {
        "task": "app.tasks.alert_tasks.evening_wrap",
        "schedule": crontab(hour=16, minute=0),         # 4:00 PM IST daily
    },
    "weekly-digest": {
        "task": "app.tasks.alert_tasks.weekly_digest",
        "schedule": crontab(hour=18, minute=0, day_of_week=0),  # Sunday 6 PM IST
    },

    # ── Signal Resolution ──
    "resolve-signals": {
        "task": "app.tasks.signal_tasks.resolve_expired",
        "schedule": 900.0,                              # Every 15 min
    },

    # ── User Alerts ──
    "check-price-alerts": {
        "task": "app.tasks.price_alert_tasks.check_price_alerts",
        "schedule": 60.0,                               # Every 1 min
    },

    # ── Maintenance ──
    "health-check": {
        "task": "app.tasks.data_tasks.health_check",
        "schedule": 300.0,                              # Every 5 min
    },
    "pipeline-health-check": {
        "task": "app.tasks.alert_tasks.pipeline_health_check",
        "schedule": 900.0,                              # Every 15 min
    },

    # ── Event Chain Maintenance ──
    "expire-stale-events": {
        "task": "app.tasks.ai_tasks.expire_stale_events",
        "schedule": 3600.0,                             # Every hour
    },

    # ── Calendar Seeding ──
    "seed-calendar-events": {
        "task": "app.tasks.calendar_tasks.seed_calendar_events",
        "schedule": crontab(hour=6, minute=0),          # 6:00 AM IST daily
    },

    # ── Subscription Management ──
    "check-expired-subscriptions": {
        "task": "app.tasks.subscription_tasks.check_expired_subscriptions",
        "schedule": 3600.0,                             # Every hour
    },

    # ── SEO Content Generation ──
    "generate-seo-pages": {
        "task": "app.tasks.seo_tasks.generate_seo_pages",
        "schedule": crontab(hour=8, minute=30),         # 8:30 AM IST daily
    },

    # ── Engagement ──
    "free-tier-weekly-digest": {
        "task": "app.tasks.engagement_tasks.send_free_tier_digest",
        "schedule": crontab(hour=18, minute=30, day_of_week=0),  # Sunday 6:30 PM IST
    },
    "reengagement-nudge": {
        "task": "app.tasks.engagement_tasks.send_reengagement_nudge",
        "schedule": crontab(hour=10, minute=0, day_of_week=3),   # Wednesday 10 AM IST
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

# ── JWT Auth ──
JWT_SECRET_KEY=...                    # HMAC signing key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Payments (Razorpay) ──
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
RAZORPAY_MONTHLY_PLAN_ID=...          # ₹499/mo plan
RAZORPAY_ANNUAL_PLAN_ID=...           # ₹4999/yr plan

# ── App Config ──
ENVIRONMENT=development               # development | production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
API_SECRET_KEY=...                    # Shared secret between FE & BE
INTERNAL_API_KEY=...                  # Celery/bot internal calls
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
backend/tests/                       # 65 test files, flat structure
├── conftest.py                      # Shared fixtures
│   ├── test_db                      # In-memory SQLite or test PostgreSQL
│   ├── test_client                  # FastAPI TestClient (Telegram user)
│   ├── web_user_client              # FastAPI TestClient (web-only user)
│   ├── mock_claude_api              # Mocked Claude responses
│   ├── sample_market_data           # Fixture OHLCV DataFrames
│   └── sample_signals               # Pre-built signal objects
│
├── test_indicators*.py              # Technical indicator tests
├── test_signal_*.py                 # Signal gen, scorer, resolution, feedback
├── test_ai_*.py                     # AI engine, budget, cost tracker
├── test_api_*.py                    # 12 API endpoint test files
├── test_auth_*.py                   # JWT auth, password accounts
├── test_security_sprint*.py         # 5 security sprint regression tests
├── test_breaker_*.py                # 5 adversarial/breaker test files
├── test_v14_*.py                    # 6 v1.4 feature test files
├── test_sprint*_*.py                # Sprint regression tests
├── test_pipeline_*.py               # Integration pipeline tests
├── test_websocket.py                # WebSocket delivery tests
├── test_web_user_identity.py        # Web-only user identity tests
└── test_structured_logging.py       # Structured logging tests

frontend/src/__tests__/              # 79 test files
├── setup.ts                         # Test setup (jsdom, mocks)
├── helpers.ts                       # Test utilities
├── *.test.tsx                       # Component tests (55 files)
├── *.test.ts                        # Store, hook, utility tests (24 files)
└── (covers all 55 components, 5 hooks, 5 stores, utilities)
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

```toml
# railway.toml (Backend)
[build]
builder = "dockerfile"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "supervisord -c supervisord.conf"
restartPolicyType = "always"
healthcheckPath = "/health"
healthcheckTimeout = 30
```

**Process model**: `supervisord.conf` manages 4 programs in a single container:
1. `migrate` — runs `alembic upgrade head` once at startup (priority 1, no restart)
2. `web` — `uvicorn app.main:app` on `$PORT` (auto-restart)
3. `celery-worker` — 2 concurrent workers (auto-restart)
4. `celery-beat` — scheduler (auto-restart)

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
| Add a new market/symbol | `backend/app/config.py` (tracked_stocks/tracked_crypto/tracked_forex) |
| Add a new technical indicator | `backend/app/services/analysis/indicators.py` |
| Change signal scoring weights | `backend/app/services/signal_gen/scorer.py` |
| Modify a Claude AI prompt | `backend/app/services/ai_engine/prompts.py` |
| Add a new API endpoint | `backend/app/api/` + register in `router.py` |
| Change Celery task timing | `backend/app/tasks/scheduler.py` |
| Add a dashboard component | `frontend/src/components/` |
| Add a new page | `frontend/src/app/<route>/page.tsx` |
| Change WebSocket message format | `backend/app/api/websocket.py` + `frontend/src/lib/websocket.ts` |
| Add a Telegram command | `backend/app/services/alerts/telegram_bot.py` |
| Change Telegram message format | `backend/app/services/alerts/formatter.py` |
| Add a database table | `backend/app/models/` + create Alembic migration |
| Change auth/JWT logic | `backend/app/auth.py` |
| Change payment/subscription logic | `backend/app/services/payment/razorpay_service.py` |
| Change tier gating rules | `backend/app/services/tier_gating.py` + `frontend/src/lib/tiers.ts` |
| Add a Zustand store | `frontend/src/store/` |
| Update project instructions | This file (CLAUDE.md) |

---

## Project History & Current State

### Version: v1.3.0 (latest tag, 27 March 2026)

> **Note:** HEAD is ahead of v1.3.0 with unreleased changes (navigation reorganization, v1.5 audit fixes). The CHANGELOG has entries up to v1.1.1. Missing entries: v1.2.0 (docs reorganization + expert review), v1.3.0 (v1.4 implementation + settings review + breaker tests). These need to be backfilled.

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
| v1.1.0 | `e5e0c23` | v1.1 improvements — Sprints A through E |
| v1.1.1 | `27fe622` | Start.sh reliability, Redis config fix |
| v1.2.0 | `839fdfe` | Docs reorganization, 20-expert v1.2 review |
| v1.3.0 | `6151b07` | Security hardening, JWT auth, Razorpay payments, causal event chains, SEO, engagement, Prometheus metrics, structured logging, tier gating |
| Unreleased | `44f5dd7` | Navigation reorganization, v1.5 audit fixes |

### Key Metrics

| Metric | Count |
|--------|-------|
| Backend Python files | 99 (14,400+ lines) |
| Frontend TypeScript files | 98 (12,500+ lines) |
| API endpoints | 57 REST + 1 WebSocket |
| Database model files | 18 |
| Tracked symbols | 31 (15 stocks, 10 crypto, 6 forex) |
| Backend test files | 65 |
| Frontend test files | 79 |
| Backend tests collected | 1,241 (+ 16 skipped) |
| Frontend tests passing | 741 |
| React components | 55 |
| Frontend pages | 20 |
| Zustand stores | 5 |
| Custom hooks | 5 |
| Celery scheduled tasks | 20 |
| Alembic migrations | 11 |
| Git tags | v0.0.1, v0.0.2, v0.0.3, v1.0.0, v1.1.0, v1.1.1, v1.2.0, v1.3.0 |

### Known Issues

- `origin/feature/phase4-integration-deploy` remote branch still exists (was GitHub default branch; needs manual GitHub settings change to delete)
- ~~12 backend test collection errors~~ — FIXED (missing local pip packages: celery, asyncpg, structlog, slowapi)
- CHANGELOG.md is missing entries for v1.2.0 and v1.3.0
- No v1.4.0 tag exists despite previous CLAUDE.md references — version was v1.3.0

---

*Last updated: 29 March 2026 | SignalFlow AI v1.3.0 + unreleased*
