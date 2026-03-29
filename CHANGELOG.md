# Changelog

All notable changes to SignalFlow AI are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Navigation reorganization: 5 primary links, Research dropdown, mobile bottom nav, site footer
- v1.5 audit fixes: 14 items (models, env, hardcoded URLs, event loop, SEO routes, tests)

### Planned
- Documentation reorganization (see docs/design/v1.2-review-and-docs-plan.md)
- Tier A quick wins: favicon, breadcrumbs, sparklines on cards, empty states

---

## [1.3.0] — 2026-03-27 (`v1.3.0`)

### Added
- **JWT Authentication**: Full auth system — register, login, refresh, logout, logout-all, profile, password change, account deletion
- **Razorpay Payments**: Subscription management (₹499/mo, ₹4999/yr), free trial, webhook handling, plan listing
- **Tier Gating**: Feature-based access control by subscription tier (free, pro, premium)
- **Causal Event Chains**: AI-powered causal link analysis between news events (causes, amplifies, dampens, contradicts)
- **SEO Content Generation**: Automated SEO page creation via Celery task
- **Engagement Tasks**: Free-tier weekly digest, re-engagement nudge (Wednesday 10 AM IST)
- **Prometheus Metrics**: `/metrics` endpoint for monitoring
- **Structured Logging**: Correlation IDs, JSON-format structured logs
- **Admin Endpoints**: Revenue dashboard, shadow mode results
- **Feedback Loop API**: Accuracy metrics, adaptive weights, indicator performance endpoints
- **Signal Feedback**: "Did you take this trade?" buttons (took/watching/skipped)
- **Shadow Mode**: Test new strategies without affecting live signals
- **Streak Protection**: Consecutive loss detection and alerts
- **Risk Guard**: Per-sector and per-market position limits
- **Multi-Timeframe Confirmation**: MTF signal validation across timeframes
- **Confidence Calibration**: Historical accuracy-based calibration tracking
- **News Intelligence**: Full news API — articles, entities, chains, calendar, signal-linked news
- **Settings & Breaker Tests**: Adversarial tests for scoring, pipeline, formatting, API, security
- 8 new Alembic migrations (news events, users, subscriptions, SEO, security constraints, timeframe)
- 6 new schema files (auth, news)
- 7 new API route files (auth, admin, feedback, news, payments, seo, signal_feedback)
- 7 new service files (cache, metrics, pubsub, revenue, seo, tier_gating, earnings_calendar)
- Payment service (Razorpay)
- 4 new Celery task files (calendar, engagement, seo, subscription)

### Changed
- Backend Python files grew from ~60 to 99 (14,400+ lines)
- Models refactored from 4 files (monolithic p3_models.py) to 18 individual model files
- API endpoints grew from ~25 to 57 REST + 1 WebSocket
- Test files grew from 40 to 65 (backend) + 79 (frontend) = 144 total
- Frontend components grew from 22 to 55
- Zustand stores grew from 3 to 5 (added preferencesStore, tierStore)
- Custom hooks grew from 4 to 5 (added useQueries)
- Frontend lib files grew from 4 to 7 (added auth, notifications, tiers)
- Frontend pages grew from 8 to 20+
- Celery scheduled tasks grew from 12 to 20

---

## [1.2.0] — 2026-03-26 (`v1.2.0`)

### Added
- Comprehensive documentation reorganization into 11 directories
- 20-expert multi-agent v1.2 review
- Architecture decision records, compliance templates, operation runbooks
- Security reports and hardening documentation
- Sprint plans and developer guides

### Changed
- Docs restructured from flat files to organized directories (compliance, decisions, design, guides, operations, reference, research, review, reviews, security, sprints)

---

## [1.1.1] — 2026-03-26

### Added
- **Sprint A**: POLUSDT fix (MATIC→POL migration), FocusTrap on all 6 modals, adaptive feedback loop wired into scorer
- **Sprint B**: Per-currency portfolio breakdowns (INR/USD), split equity curves, allocation pie chart with currency labels
- **Sprint C**: Position sizing calculator with "Size" mode (account equity + risk % → recommended quantity)
- **Sprint D**: "Did you take this trade?" feedback buttons (took/watching/skipped) with SignalFeedback model + API
- **Sprint E**: Central bank event suppression for forex (FOMC, RBI MPC, ECB, BOJ — 4hr suppression window), earnings calendar seeding with Celery task

### Changed
- Signal scorer now accepts optional adaptive weights from feedback loop
- AllocationPieChart shows market-level breakdown with currency warnings for multi-currency portfolios
- RiskCalculator redesigned with two modes: P&L (preset amounts) and Size (position sizing from risk %)

### Fixed
- MATICUSDT → POLUSDT in crypto fetcher CoinGecko mapping
- MATICUSDT → POLUSDT in event chain sector symbols
- Portfolio page no longer mixes INR and USD values in single summary

---

## [1.1.0] — 2026-03-21 (`v1.1.0`)

### Added
- **Sprint 1**: Mobile accessibility, design system foundation, touch targets (44px)
- **Sprint 2**: Signal detail page redesign, card clarity improvements
- **Sprint 3**: Navigation consolidation, accessibility patterns, focus management
- **Sprint 4**: React Query migration, WebSocket cache sync, data age indicators

### Changed
- Navigation restructured: 4 primary links + "More" dropdown
- Signal cards redesigned: 6 key data points with 3-section expand
- All external data fetching migrated to React Query with caching

---

## [1.0.0] — 2026-03-21 (`v1.0.0`)

### Added
- Complete trading signal platform with 3 markets (Stocks, Crypto, Forex)
- 31 tracked symbols (15 NSE stocks, 10 crypto pairs, 6 forex pairs)
- Technical analysis engine: RSI, MACD, Bollinger Bands, Volume, SMA, ATR
- AI sentiment analysis via Claude Sonnet with $30/month budget cap
- Signal generation pipeline: data → analysis → AI → scoring → signal
- AI reasoning in plain English for every signal
- ATR-based target/stop-loss with 1:2 risk-reward ratio
- WebSocket real-time signal delivery
- Telegram bot with 13 commands
- Dashboard with 20 pages and 49 React components
- Dark trading terminal aesthetic with Outfit + JetBrains Mono fonts
- Signal history with win/miss tracking
- Market heatmap and sparkline components
- Price alerts and watchlist management
- Portfolio trade logging with P&L tracking
- Backtesting engine with equity curves
- AI Q&A (ask Claude about any symbol)
- Signal sharing with public URLs (30-day expiry)
- How It Works educational page
- 480+ backend tests, Docker deployment

### Architecture
- FastAPI + SQLAlchemy async + PostgreSQL + TimescaleDB
- Celery + Redis for 12+ scheduled tasks
- Next.js 14 + TypeScript + Zustand + Recharts frontend
- Railway deployment with docker-compose

---

## [0.0.3] — 2026-03-20 (`v0.0.3`)

### Added
- News intelligence with causal event chains
- Event entity extraction from news articles
- Causal link analysis (causes, amplifies, dampens, contradicts)
- News dashboard with headlines, events, and calendar tabs
- EventTimeline visualization component

---

## [0.0.1] — 2026-03-19 (`v0.0.1`)

### Added
- Initial MVP scaffold
- Docker Compose with 5 services (db, redis, backend, celery, frontend)
- Database schema: market_data, signals, alert_configs, signal_history
- Three market data fetchers (yfinance, Binance, Alpha Vantage)
- Basic Celery Beat schedule for data ingestion
- FastAPI health endpoint

---

## Security Releases

### Security Sprint 4 — 2026-03-25 (`v1.1.1`)
- Hardening, structured logging, monitoring integration

### Security Sprint 3 — 2026-03-24
- AI security, prompt injection prevention, DoS protection

### Security Sprint 2 — 2026-03-23
- Race conditions, data integrity, financial precision fixes

### Security Sprint 1 — 2026-03-22
- JWT auth, access control, tier enforcement, WebSocket auth

### Security Sprint 0 — 2026-03-21
- Emergency fixes for CRIT-01, 09, 10, 11, 12, 13, 14, 23
