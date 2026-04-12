---
name: signalflow-architecture
description: >
  SignalFlow project architecture rules, conventions, and quick-reference patterns.
  Invoke when working on any part of the SignalFlow codebase to stay aligned with
  non-negotiables, file locations, and the tech stack.
version: 1.0.0
---

# SignalFlow Architecture Skill

## Repo Structure
```
signalflow/
  CLAUDE.md                 Master spec (source of truth)
  backend/
    app/
      api/                  57 REST endpoints + 1 WebSocket
      models/               18 SQLAlchemy ORM models
      schemas/              Pydantic v2 request/response schemas
      services/
        data_ingestion/     yfinance · Binance WS · Alpha Vantage
        analysis/           TechnicalAnalyzer (RSI/MACD/BB/Vol/SMA/ATR)
        ai_engine/          Claude API · sentiment · cost tracker · prompts
        signal_gen/         generator · scorer · targets · calibration
        alerts/             Telegram bot · formatter · dispatcher
        payment/            Razorpay
      tasks/                20 Celery scheduled tasks
    tests/                  65 test files · 1,241 backend tests
    migrations/             11 Alembic migrations
  frontend/
    src/
      app/                  20 pages (Next.js App Router)
      components/           55 React components
      store/                5 Zustand stores
      hooks/                5 custom hooks
      lib/                  api.ts · types.ts · websocket.ts · constants.ts
    __tests__/              79 test files · 741 frontend tests
  external/
    ai-powerhouse/          Claude Code agents, skills & hooks (submodule)
  .claude/
    agents/signalflow/      6 domain-specialist agents
    skills/                 this skill
    helpers/                hook-handler · router · session · intelligence
```

## Tech Stack
- **Backend:** Python 3.11 · FastAPI 0.115+ · SQLAlchemy 2.0 async · Pydantic v2
- **Queue:** Celery 5.x · Redis 7.x
- **Database:** PostgreSQL 16 · TimescaleDB 2.x (hypertable on market_data)
- **AI:** Claude `claude-sonnet-4-20250514` · $30/month budget
- **Frontend:** Next.js 14 App Router · TypeScript 5 strict · Tailwind 3 · Zustand 4
- **Alerts:** python-telegram-bot 20.x
- **Deploy:** Railway · supervisord (web + celery-worker + celery-beat + migrate)

## Non-Negotiables (Always Enforce)
1. **Decimal prices** — `decimal.Decimal` everywhere, never `float`
2. **TIMESTAMPTZ** — all timestamps timezone-aware
3. **Async everywhere** — all FastAPI endpoints + DB ops are `async def`
4. **Every signal has a stop-loss** — R:R ≥ 1:2 always
5. **$30/month Claude budget** — cost_tracker.py wraps every API call
6. **All prompts in prompts.py** — never inline
7. **Service independence** — data_ingestion ↔ ai_engine ↔ signal_gen never cross-import
8. **Identity dual test** — every user-scoped endpoint tested with Telegram user AND web-only user
9. **Pre-commit gate** — pytest + vitest + docker build all green before commit
10. **No financial advice** — every signal includes disclaimer

## Signal Pipeline
```
market_data → TechnicalAnalyzer → technical_score (×0.60)
news → Claude sentiment → ai_score (×0.40)
→ final_confidence → signal_type → target/stop (ATR×2 / ATR×1)
```

## Scoring Weights
RSI 20% · MACD 25% · Bollinger 15% · Volume 15% · SMA crossover 25%

## Signal Thresholds
80–100: STRONG_BUY · 65–79: BUY · 36–64: HOLD · 21–35: SELL · 0–20: STRONG_SELL

## Market Hours (IST)
NSE/BSE: 9:15 AM–3:30 PM Mon–Fri · Crypto: 24/7 · Forex: 24/5

## Tracked Symbols (31)
Stocks (15): HDFCBANK RELIANCE TCS INFY ICICIBANK KOTAKBANK AXISBANK SBIN WIPRO BAJFINANCE HINDUNILVR ITC BHARTIARTL MARUTI LT
Crypto (10): BTC ETH SOL BNB XRP ADA DOGE AVAX MATIC DOT
Forex (6): USD/INR EUR/USD GBP/JPY EUR/INR GBP/USD USD/JPY

## Quick File Reference
| I need to... | Edit this file |
|---|---|
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

## Commands
```bash
make init          # First-time: build + start + migrate
make up            # Start all services
make test          # Backend pytest
make frontend-dev  # Next.js dev server
make migrate       # Apply Alembic migrations
make logs          # Follow all logs
docker compose build  # Pre-commit build verification
```

## AI Powerhouse Agents for This Project
```
signalflow-backend    → FastAPI · Celery · PostgreSQL · Redis · Telegram
signalflow-ai-engine  → Claude API · prompts · cost tracker · LLM security
signalflow-signal     → scoring · targets · calibration · resolution
signalflow-data       → market fetchers · TechnicalAnalyzer · market hours
signalflow-frontend   → Next.js · React · Zustand · TypeScript · Tailwind
signalflow-security   → JWT · Razorpay · OWASP · rate limiting
signalflow-reviewer   → pre-commit gate · architecture compliance
```
