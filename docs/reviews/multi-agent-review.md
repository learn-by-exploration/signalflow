# SignalFlow AI — Multi-Agent Strategic Review

> **Date**: 20 March 2026 | **Version**: Post-Phase 4 (116 tests passing, 4 phases committed)
> **Methodology**: Ruflo-style multi-agent review — 4 perspective agents + 1 architect synthesis
> **Agents**: Sales, Product Manager, Senior Architect, Investment Banker

---

## EXECUTIVE SUMMARY

| Agent | Verdict | Key Finding |
|-------|---------|-------------|
| **Sales** | Promising but unshippable | The AI reasoning moat is real, but the product can't demo its core value (sentiment is non-functional) |
| **Product Manager** | 85% MVP complete | P0 blockers: news fetcher, signal dedup, Telegram persistence, signal resolution |
| **Senior Architect** | Solid foundation, critical security gaps | No auth, no rate limiting, SQL injection in alert_tasks, async event loop issues in Celery |
| **Investment Banker** | Conditional NO-GO | $30/month AI budget sustains only ~4 days. SEBI RA registration required. Unit economics excellent at scale. |

**One-line synthesis**: *The architecture is production-grade, the UX is polished, and the business model is viable — but the AI engine (the core moat) is non-functional for 85% of each month, and regulatory/security gaps block any commercial launch.*

---

## 1. SALES PERSPECTIVE

### Value Proposition
**Current**: "AI-powered trading signals for Indian Stocks, Crypto, and Forex"
**Recommended**: "Your AI trading analyst — explains every signal in plain English, with exact entry, target, and stop-loss"

The explanation is the moat. No free competitor (TradingView, Zerodha Streak, CoinMarketCap) explains *why* a signal was generated.

### Competitive Positioning

| Feature | SignalFlow | TradingView | Zerodha Streak | CoinMarketCap |
|---------|-----------|-------------|----------------|---------------|
| AI reasoning per signal | **YES** (unique) | No | No | No |
| Multi-market | **YES** | Yes (view only) | Stocks only | Crypto only |
| Stop-loss enforced | **YES** | Manual | Yes | No |
| Backtesting | **NO** | Yes | Yes | No |
| Auto-trading | **NO** | Via broker | Yes | No |

### Revenue Path
- **Free tier**: 5 signals/day, stocks only, morning brief
- **Pro (₹499/month)**: Unlimited signals, all markets, morning + evening wraps
- **Premium (₹1,499/month)**: Custom watchlist, personal AI Q&A, API access
- **Break-even**: ~67 paying users at ₹299/month

### Missing Selling Points
1. **Learn While You Trade** — educational tips in AI reasoning
2. **Risk Calculator** — "₹10K invested → max loss ₹500, max gain ₹1,200"
3. **"Why Not" signals** — explain why a followed symbol has no signal
4. **Weekly win-rate badge** — "72% accurate this month"

---

## 2. PRODUCT MANAGER PERSPECTIVE

### Feature Completeness

| Feature | Status | MVP-Critical? |
|---------|--------|---------------|
| Signal generation (technical + AI) | ✓ Complete | YES |
| Telegram bot + alerts | ✓ Complete | YES |
| Web dashboard (dark theme) | ✓ Complete | YES |
| Signal history tracking | ⚠ Partial | YES |
| Morning/evening briefs | ✓ Complete | No |
| WebSocket real-time | ✓ Complete | No |
| Alert config persistence | ⚠ Not persisted | No |

### Critical Finding: Sentiment Engine is Dead Weight

The `AISentimentEngine` calls Claude to analyze "news articles" — but **there is no news data source**. Without news:
- Sentiment score defaults to 50 (neutral fallback)
- Signal confidence is capped at 60% (no-AI cap in scorer.py)
- **STRONG_BUY (requires 80+) is impossible to generate**
- The 40% AI sentiment weight in the scoring formula is dead weight

### User Stories Gap Analysis (Top 5)

| User Story | Status |
|-----------|--------|
| "I want to see if past signals were correct" | ⚠ signal_history exists but resolution logic doesn't run |
| "I want my Telegram prefs to survive bot restarts" | ✗ In-memory only |
| "I want to know the product's win rate" | ✗ Not built |
| "I want to search signals by symbol" | ✗ Only market-type filter |
| "I want to see charts with signal overlays" | ✗ Sparkline built but unused |

### Notification Strategy Issues
- **No signal deduplication** — same symbol can spam 24 identical alerts in 2 hours
- **No daily alert budget** — no cap on alerts/day
- **No cooldown period** — 5-min signal interval means constant noise

---

## 3. SENIOR ARCHITECT PERSPECTIVE

### Architecture Strengths
- Clean service layer separation (data → analysis → AI → signal → alerts)
- Async throughout (FastAPI + SQLAlchemy async + asyncpg)
- Pydantic v2 schemas with proper validation
- Decimal for ALL financial data (never float)
- TimescaleDB for time-series optimization
- 116 tests passing across 8 test files

### CRITICAL Security Issues

| Issue | Severity | Location |
|-------|----------|----------|
| **No authentication** on any endpoint | CRITICAL | All `/api/v1/*` routes |
| **No rate limiting** | CRITICAL | HTTP + WebSocket |
| **SQL injection** in raw queries | HIGH | `alert_tasks.py` lines 48-50 |
| **WebSocket unauthenticated** | HIGH | `/ws/signals` |
| **No HTTPS enforcement** | HIGH | Production config |

### Performance Concerns

| Issue | Fix |
|-------|-----|
| N+1 query in market overview | Window function `ROW_NUMBER()` |
| `asyncio.run()` in sync Celery tasks | Blocks worker threads |
| Sequential Claude API calls per symbol | Batch or parallelize |
| No Redis TTL on some cache entries | Memory bloat |

### Missing Infrastructure
- No pre-commit hooks enforcing test pass
- No CI/CD pipeline
- Cost tracker uses JSON file (not atomic, not production-grade)
- No database backup strategy
- No log aggregation beyond Sentry

---

## 4. INVESTMENT BANKER PERSPECTIVE

### Cost Structure Reality

| Component | Stated Budget | Actual Requirement |
|-----------|--------------|-------------------|
| Claude API | $30/month | **$135–235/month** |
| Railway (5 services) | Not budgeted | ~$45/month |
| Alpha Vantage Premium | Not budgeted | ~$50/month |
| **Total** | ~$30/month | **$232–332/month** |

**The $30/month AI budget sustains only ~4 days of operation.** For the remaining ~26 days, the AI engine returns fallback values, confidence is capped at 60%, and no STRONG_BUY signals can fire.

### Unit Economics (Favorable at Scale)

| Users | Monthly Cost | Cost/User | Revenue at ₹299/mo |
|-------|-------------|-----------|-------------------|
| 1 | $232 | $232.00 | N/A (personal) |
| 100 | $240 | $2.40 | $357 → **profitable** |
| 1,000 | $280 | $0.28 | $3,570 → **highly profitable** |

**Key insight**: This is a broadcast system. AI costs are per-symbol (fixed), not per-user. Adding users is nearly free.

### Regulatory Risk — CRITICAL

**SEBI Research Analyst Regulations**: Any entity providing specific buy/sell recommendations with entry/target/stop-loss on Indian securities must be registered as a Research Analyst. Penalty: up to ₹25 crore fine or 10 years imprisonment.

**Options**: Register as SEBI RA / Remove Indian stock signals / Rebrand as "educational analysis"

### 3-Year Revenue Projection

| Year | Paying Users | Annual Revenue | Annual Cost | Net |
|------|-------------|---------------|------------|-----|
| Y1 | 0→200 | $4,300 | $3,600 | +$700 |
| Y2 | 200→2,000 | $47,000 | $8,000 | +$39,000 |
| Y3 | 2,000→8,000 | $214,000 | $25,000 | +$189,000 |

### Investment Verdict: **CONDITIONAL NO-GO**

Score: 3.0/5.0. Investable with these conditions met:
1. Fix AI budget to $135+/month (or restructure sentiment frequency)
2. 3 months backtested signal accuracy (>55% win rate)
3. SEBI RA registration for commercial launch
4. Replace yfinance + Google News RSS with licensed data feeds
5. 100+ free beta users with retention data

---

## 5. SYNTHESIZED PHASE 5 ROADMAP

### P0 — LAUNCH BLOCKERS (Estimated: 5-7 days)

| # | Task | Owner (Ruflo Agent) | Effort | Why |
|---|------|-------------------|--------|-----|
| 1 | **Implement news fetcher** (NewsAPI/RSS) to feed sentiment engine | `sf-ai-engineer` | 2-3 days | Without this, AI moat is non-functional. Max confidence stuck at 60%. |
| 2 | **Signal deduplication/cooldown** — 1-hour cooldown per symbol | `sf-backend` | 0.5 day | Prevents Telegram alert spam |
| 3 | **Persist Telegram registrations** to `alert_configs` DB table | `sf-backend` | 0.5 day | Bot restart = all users lost |
| 4 | **Persist `/config` preferences** to database | `sf-backend` | 1 day | User preferences are currently theater |
| 5 | **Signal resolution task** — check prices vs targets/stops, update `signal_history` | `sf-backend` | 1-2 days | Cannot measure accuracy without this |
| 6 | **Restructure AI budget** — reduce sentiment frequency to sustainable level | `sf-architect` | 0.5 day | $30/month → 4 days. Need $30 → 30 days. |

### P1 — TRUST & RETENTION (Estimated: 5-7 days)

| # | Task | Owner | Effort | Why |
|---|------|-------|--------|-----|
| 7 | **Win rate dashboard** — aggregate signal performance stats | `sf-frontend` | 1-2 days | Trust signal #1 |
| 8 | **Weekly Telegram digest** — automated performance summary | `sf-backend` | 1 day | Retention driver |
| 9 | **Daily alert budget** — max 10 push alerts/day, ranked by confidence | `sf-backend` | 0.5 day | Notification fatigue prevention |
| 10 | **Guided onboarding** — `/tutorial` command + sample signal on `/start` | `sf-backend` | 1-2 days | Reduces drop-off |
| 11 | **"Last updated" indicator** on dashboard | `sf-frontend` | 0.5 day | Users need to know if data is live |

### P2 — SECURITY & HARDENING (Estimated: 3-5 days)

| # | Task | Owner | Effort | Why |
|---|------|-------|--------|-----|
| 12 | **API authentication** — JWT or API key on all endpoints | `sf-backend` | 2 days | Currently public access to everything |
| 13 | **Rate limiting** — per-IP and per-key limits | `sf-backend` | 1 day | DDoS/cost protection |
| 14 | **Fix SQL injection** in `alert_tasks.py` — parameterized queries | `sf-backend` | 0.5 day | Security vulnerability |
| 15 | **Global error handlers** — structured HTTP error responses | `sf-backend` | 0.5 day | No stack traces in production |
| 16 | **Input validation enums** — validate market_type, signal_type params | `sf-backend` | 0.5 day | Currently accepts any string |

### P3 — SCALE & GROWTH (Month 2+)

| # | Task | Effort |
|---|------|--------|
| 17 | Backtesting framework | 1-2 weeks |
| 18 | Replace yfinance with licensed NSE data feed | 1 week |
| 19 | Custom watchlist per user | 2-3 days |
| 20 | "Ask about a symbol" AI Q&A | 2-3 days |
| 21 | SEBI RA registration research | External |

---

## APPENDIX: Ruflo Swarm Commands for Phase 5

```bash
# P0 — Launch Blockers
npx ruflo hive-mind spawn \
  "Phase 5 P0 - Launch Blockers: (1) Build a news fetcher service using NewsAPI or RSS feeds to feed the sentiment engine — currently non-functional. (2) Add 1-hour signal cooldown per symbol to prevent duplicate alerts. (3) Persist Telegram /start registrations to alert_configs DB instead of in-memory bot_data. (4) Wire /config inline keyboard toggles to update alert_configs. (5) Build signal resolution Celery task that checks current prices vs active signal targets/stops and updates signal_history. (6) Restructure AI budget: reduce sentiment frequency to 1hr for stocks (market hours only), 30min crypto, skip forex sentiment." \
  --queen-type strategic

# P1 — Trust & Retention
npx ruflo hive-mind spawn \
  "Phase 5 P1 - Trust & Retention: (7) Add win-rate dashboard component showing aggregate signal performance. (8) Weekly performance Telegram digest. (9) Daily alert budget (max 10). (10) /tutorial command + sample signal on /start. (11) Last-updated indicator on dashboard." \
  --queen-type strategic

# P2 — Security
npx ruflo hive-mind spawn \
  "Phase 5 P2 - Security Hardening: (12) JWT authentication on all /api/v1 endpoints. (13) Rate limiting middleware. (14) Fix SQL injection in alert_tasks.py. (15) Global exception handlers. (16) Enum validation on query params." \
  --queen-type strategic
```

---

*Generated by multi-agent review: sf-architect (synthesis), sales-agent, pm-agent, architect-agent, banker-agent*
*All findings verified against actual source code, not just CLAUDE.md spec*
