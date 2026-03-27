# v1.5 Audit Fixes — Implementation Plan

> **Source**: Full-stack audit of SignalFlow v1.4.0 (commit `6151b07`) + prior code review findings.
> **Scope**: 2 critical, 4 high, 6 medium fixes + 3 code review items.
> **Rule**: READ-ONLY plan. No code changes here.

---

## Context

After completing v1.4.0 (1939 tests, 88 files committed), a comprehensive full-stack audit identified gaps in infrastructure, documentation, testing, and code quality. This plan addresses every finding, ordered by severity and dependency.

---

## Task Breakdown

### Phase 1: Critical Fixes (Data Integrity + Production Bug)

#### Task 1 — Fix Alembic env.py model imports (C1)

**Severity**: 🔴 Critical — silent schema drift; `alembic revision --autogenerate` sees incomplete metadata.

**Problem**: `backend/migrations/env.py` imports only 4 of 19 models:
```python
from app.models import MarketData, Signal, AlertConfig, SignalHistory  # noqa: F401
```

**Missing models** (15): `PriceAlert`, `User`, `RefreshToken`, `Trade`, `SignalShare`, `BacktestRun`, `NewsEvent`, `EventEntity`, `CausalLink`, `SignalNewsLink`, `EventCalendar`, `SignalFeedback`, `SeoPage`, `Subscription`, `ConfidenceCalibration`.

**Fix**: Replace the single import line with:
```python
from app.models import (  # noqa: F401
    MarketData, Signal, AlertConfig, SignalHistory,
    PriceAlert, User, RefreshToken, Trade, SignalShare,
    BacktestRun, NewsEvent, EventEntity, CausalLink,
    SignalNewsLink, EventCalendar, SignalFeedback,
)
from app.models.seo_page import SeoPage  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.confidence_calibration import ConfidenceCalibration  # noqa: F401
```

**Note**: `SeoPage`, `Subscription`, and `ConfidenceCalibration` are NOT in `app/models/__init__.py` `__all__`. Either add them to `__init__.py` or import directly from their modules.

**Verification**: Run `cd backend && alembic check` — should show "No new upgrade operations detected" (or show the drift if any tables were missed).

**Files to edit**:
- `backend/migrations/env.py` — update import block
- `backend/app/models/__init__.py` — add `SeoPage`, `Subscription`, `ConfidenceCalibration` to exports

---

#### Task 2 — Fix hardcoded localhost in telegram_bot.py (C2)

**Severity**: 🔴 Critical — Telegram `/ask` command broken in production.

**Problem**: `backend/app/services/alerts/telegram_bot.py` line 288:
```python
f"http://localhost:{settings.api_port}/api/v1/ai/ask"
```

In production (Railway), the backend is not reachable at `localhost`. This should use the configured API host.

**Fix**: Replace with:
```python
backend_host = settings.api_host if settings.environment == "production" else "localhost"
backend_port = settings.api_port
f"http://{backend_host}:{backend_port}/api/v1/ai/ask"
```

Or better — since in production the API is behind a reverse proxy with no port suffix, match the pattern already used in `main.py` line 142:
```python
if settings.environment == "production":
    api_base = f"http://0.0.0.0:{settings.api_port}"
else:
    api_base = f"http://localhost:{settings.api_port}"
```

**Note**: In Railway's containerized environment, using `0.0.0.0` or `127.0.0.1` for self-referencing within the same container works. Since telegram_bot.py runs inside the same container (via supervisord), `0.0.0.0:{PORT}` is correct for production. Alternatively, since both backend and bot are in the same process, calling the service function directly (bypassing HTTP) would be more robust.

**Files to edit**:
- `backend/app/services/alerts/telegram_bot.py` — fix the URL construction

---

### Phase 2: High-Priority Fixes (Config, CI, Docs)

#### Task 3 — Update .env.example with all missing variables (H1)

**Severity**: 🟠 High — new developers won't know about required vars.

**Problem**: `.env.example` is missing environment variables that exist in `config.py`:

| Variable | In config.py | In .env.example |
|----------|-------------|----------------|
| `INTERNAL_API_KEY` | ✅ | ❌ |
| `ALLOWED_HOSTS` | ✅ | ❌ |
| `MAX_REQUEST_BODY_BYTES` | ✅ | ❌ |
| `RAZORPAY_KEY_ID` | ✅ | ❌ |
| `RAZORPAY_KEY_SECRET` | ✅ | ❌ |
| `RAZORPAY_WEBHOOK_SECRET` | ✅ | ❌ |
| `RAZORPAY_MONTHLY_PLAN_ID` | ✅ | ❌ |
| `RAZORPAY_ANNUAL_PLAN_ID` | ✅ | ❌ |
| `PRO_TRIAL_DAYS` | ✅ | ❌ |
| `PAYMENT_GRACE_DAYS` | ✅ | ❌ |
| `FLOWER_USER` | docker-compose | ❌ |
| `FLOWER_PASSWORD` | docker-compose | ❌ |
| `REDIS_PASSWORD` | docker-compose | ❌ (only as comment) |
| `CLAUDE_MODEL` | ✅ | ❌ |

**Fix**: Add all missing variables to `.env.example` with section headers and comments explaining each. Group under:
```
# ── Payments (Razorpay) ──
# ── Security ──
# ── Monitoring (Flower) ──
```

**Files to edit**:
- `.env.example`

---

#### Task 4 — Verify CI typecheck step (H2)

**Severity**: 🟠 High — TypeScript errors could slip through if `tsc --noEmit` silently fails.

**Current state**: CI already has `npx tsc --noEmit` step. ✅ Verified in `.github/workflows/ci.yml`. This item from the audit is already resolved.

**Action**: No change needed — mark as verified/closed.

---

#### Task 5 — Update CLAUDE.md version and history (H3)

**Severity**: 🟠 High — stale documentation causes confusion for AI agents and contributors.

**Problem**: CLAUDE.md says `### Version: v1.0.0 (Released 21 March 2026)` but the actual version is v1.4.0.

**Fix**: Update the version section to reflect v1.4.0 and add the v1.1–v1.4 development phases to the history table. Update key metrics (test count: 1939, file counts, etc.).

**Files to edit**:
- `CLAUDE.md` — version header, development phases table, key metrics

---

#### Task 6 — Document supervisord deployment model (H4)

**Severity**: 🟠 High — railway.toml references supervisord, but it's undocumented.

**Problem**: `railway.toml` calls `supervisord -c supervisord.conf` but:
1. CLAUDE.md still shows the old `bash -c 'alembic upgrade head && uvicorn ... & celery ...'` in the Railway Configuration section
2. `supervisord.conf` exists at project root but is not mentioned in CLAUDE.md project structure
3. The file manages 4 programs (migrate, web, celery-worker, celery-beat) but this is invisible to developers

**Fix**:
1. Update CLAUDE.md Railway Configuration section to show `supervisord -c supervisord.conf`
2. Add `supervisord.conf` to the project structure tree in CLAUDE.md
3. Add a brief note explaining the 4-program process model

**Files to edit**:
- `CLAUDE.md` — Railway Configuration section, project structure

---

### Phase 3: Medium-Priority Fixes (Code Quality + Testing)

#### Task 7 — Add startup validation for required secrets (M4)

**Severity**: 🟡 Medium — empty-string defaults for security-critical secrets allow silent startup with no auth.

**Problem**: In `config.py`, these have empty defaults:
```python
api_secret_key: str = ""
internal_api_key: str = ""
jwt_secret_key: str = ""
```
If unset, the app starts but auth is broken or bypassed.

**Fix**: Add a validation check in the `lifespan` startup (in `main.py`) that warns or raises when critical secrets are empty in production:
```python
if settings.environment == "production":
    missing = []
    if not settings.jwt_secret_key:
        missing.append("JWT_SECRET_KEY")
    if not settings.api_secret_key:
        missing.append("API_SECRET_KEY")
    if missing:
        raise RuntimeError(f"Required secrets not set: {', '.join(missing)}")
```

The existing check for `DATABASE_URL` at line 140 of `main.py` is the pattern to follow.

**Files to edit**:
- `backend/app/main.py` — add secret validation in lifespan startup

---

#### Task 8 — Fix TODO: parse published_at in sentiment.py (M5)

**Severity**: 🟡 Medium — news events stored with `published_at=None`, losing temporal metadata.

**Problem**: `backend/app/services/ai_engine/sentiment.py` line 241:
```python
published_at=None,  # TODO: parse published_at string
```

The `structured_articles` already have `published_at` strings from the news fetcher.

**Fix**: Parse the `published_at` string using `dateutil.parser.parse()` or a try-except with `datetime.fromisoformat()`:
```python
from dateutil.parser import parse as parse_dt

pub_str = article.get("published_at")
published_at = None
if pub_str:
    try:
        published_at = parse_dt(pub_str)
    except (ValueError, TypeError):
        pass
```

**Verify**: `python-dateutil` is already in requirements.txt (it's a pandas dependency).

**Files to edit**:
- `backend/app/services/ai_engine/sentiment.py` — replace `published_at=None` with parsed datetime

---

#### Task 9 — Make forex rate-limit sleep configurable (M6)

**Severity**: 🟡 Medium — hardcoded `time.sleep(8)` is untestable and non-obvious.

**Problem**: `backend/app/services/data_ingestion/forex.py` line 86:
```python
time.sleep(8)
```

This is a blocking sleep in a sync context (OK since forex fetcher runs in Celery worker), but the 8-second magic number should be a named constant.

**Fix**: Add a class-level constant or config setting:
```python
# At class level or module level:
RATE_LIMIT_DELAY_SECONDS = 8  # Twelve Data free tier: ~8 sec between calls
```

**Files to edit**:
- `backend/app/services/data_ingestion/forex.py` — extract constant

---

#### Task 10 — Fix deprecated asyncio.get_event_loop() calls (M-review)

**Severity**: 🟡 Medium — deprecated in Python 3.10+, will emit DeprecationWarning and may break in Python 3.14.

**Problem**: 3 files use `asyncio.get_event_loop().run_until_complete()`:
- `backend/app/tasks/_engine.py` line 62
- `backend/app/tasks/seo_tasks.py` line 70
- `backend/app/tasks/engagement_tasks.py` lines 81, 153

**Fix**: Replace with `asyncio.run()` (Python 3.7+) which creates a new event loop cleanly:
```python
# Before:
result = asyncio.get_event_loop().run_until_complete(coro())
# After:
result = asyncio.run(coro())
```

**Note**: If these are called from within Celery tasks (which already have an event loop), use a helper pattern:
```python
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = None

if loop and loop.is_running():
    # We're in an async context, use nest_asyncio or thread
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = pool.submit(asyncio.run, coro()).result()
else:
    result = asyncio.run(coro())
```

Check if `_engine.py` already handles this pattern — if so, make `seo_tasks.py` and `engagement_tasks.py` use the same shared helper.

**Files to edit**:
- `backend/app/tasks/seo_tasks.py`
- `backend/app/tasks/engagement_tasks.py`
- Possibly `backend/app/tasks/_engine.py` (verify if its pattern is already correct)

---

#### Task 11 — Fix SEO route ordering (M-review)

**Severity**: 🟡 Medium — `GET /analysis/{slug}` defined before `GET /analysis/` means a request to `/analysis/?market=stock` would match `/{slug}` with slug="".

**Problem**: In `backend/app/api/seo.py`, the `/{slug}` route is defined before `/`. FastAPI evaluates routes in definition order, so `/` won't match if `/{slug}` catches it first.

**Current order**:
```python
@router.get("/{slug}", ...)   # Line 16 — catches everything
@router.get("/", ...)          # Line 32 — unreachable?
```

**Fix**: Swap the route order — define `/` before `/{slug}`:
```python
@router.get("/", ...)          # List pages — must be first
@router.get("/{slug}", ...)   # Get specific page — must be after /
```

**Note**: FastAPI uses Starlette's route matching which gives priority to literal paths over parameterized paths, so this may not be a real bug. Verify by testing both endpoints. Swapping order is the safest fix regardless.

**Files to edit**:
- `backend/app/api/seo.py` — swap route definition order

---

#### Task 12 — Add tests for signal_feedback API (M1)

**Severity**: 🟡 Medium — API endpoint in production with zero test coverage.

**Problem**: `backend/app/api/signal_feedback.py` is registered in the router and serves live traffic but has no tests.

**Fix**: Create test file or add tests to existing test file covering:
- `POST /api/v1/signals/{signal_id}/feedback` — submit feedback (took/skipped/watching)
- `GET /api/v1/signals/{signal_id}/feedback` — retrieve feedback
- Auth required (both JWT and API key)
- Invalid signal_id handling
- Duplicate feedback handling

**Files to create/edit**:
- `backend/tests/test_api_signal_feedback.py` (new test file)

---

#### Task 13 — Add tests for earnings_calendar service (M2)

**Severity**: 🟡 Medium — service module with zero test coverage.

**Problem**: `backend/app/services/earnings_calendar.py` has no tests. It's a data seeder with static earnings dates.

**Fix**: Add basic tests covering:
- `UPCOMING_EARNINGS` list has expected format (symbol, title, datetime string, magnitude)
- `CENTRAL_BANK_EVENTS` list has expected format
- Date strings are parseable
- The `seed_earnings_dates()` function (if it exists) inserts correctly

**Files to create/edit**:
- `backend/tests/test_earnings_calendar.py` (new test file)

---

#### Task 14 — Update models/__init__.py exports (M-housekeeping)

**Severity**: 🟡 Medium — `SeoPage`, `Subscription`, `ConfidenceCalibration` exist as model files but aren't exported from `__init__.py`, making imports inconsistent.

**Fix**: Add the 3 missing models to `backend/app/models/__init__.py`:
```python
from app.models.seo_page import SeoPage
from app.models.subscription import Subscription
from app.models.confidence_calibration import ConfidenceCalibration
```
And add to `__all__`.

**Dependencies**: Must be done before or alongside Task 1 (env.py fix).

**Files to edit**:
- `backend/app/models/__init__.py`

---

### Phase 4: Documentation Sync

#### Task 15 — Full CLAUDE.md refresh

**Severity**: 🟡 Medium — CLAUDE.md is the "single source of truth" but is stale.

**Items to update** (beyond what Tasks 5 and 6 cover):
1. Project structure tree — add all new files from v1.1–v1.4 (19 new model files, 18 API files, 15+ service files, 15+ task files, auth.py, new test files)
2. Database schema section — add tables: `users`, `refresh_tokens`, `subscriptions`, `seo_pages`, `news_events`, `event_entities`, `causal_links`, `signal_news_links`, `event_calendar`, `signal_feedback`, `confidence_calibration`
3. Key metrics — update counts (tests: 1939, models: 19, endpoints: 30+, etc.)
4. Quick Reference table — add new file mappings (auth, payments, SEO, etc.)
5. Tech stack table — add supervisord, structlog, Razorpay
6. Known issues — remove resolved items, add current known issues

**Files to edit**:
- `CLAUDE.md`

---

## Execution Order & Dependencies

```
Phase 1 (Critical):
  Task 14 (model exports) → Task 1 (alembic env.py) [dependency]
  Task 2 (hardcoded localhost)                       [independent]

Phase 2 (High):
  Task 3 (.env.example)  [independent]
  Task 4 (CI typecheck)  [verified — no action]
  Task 5 (CLAUDE.md version) [independent]
  Task 6 (supervisord docs)  [independent]

Phase 3 (Medium):
  Task 7 (startup validation) [independent]
  Task 8 (published_at TODO)  [independent]
  Task 9 (forex sleep const)  [independent]
  Task 10 (asyncio deprecation) [independent]
  Task 11 (SEO route order)   [independent]
  Task 12 (signal_feedback tests) [independent]
  Task 13 (earnings_calendar tests) [independent]

Phase 4 (Documentation):
  Task 15 (CLAUDE.md refresh) [depends on Tasks 5, 6 being done first, or do all at once]
```

## Summary

| # | Task | Severity | Files | Est. Complexity |
|---|------|----------|-------|----------------|
| 1 | Fix Alembic model imports | 🔴 Critical | env.py, __init__.py | Simple |
| 2 | Fix hardcoded localhost | 🔴 Critical | telegram_bot.py | Simple |
| 3 | Update .env.example | 🟠 High | .env.example | Simple |
| 4 | Verify CI typecheck | 🟠 High | — | ✅ Already done |
| 5 | Update CLAUDE.md version | 🟠 High | CLAUDE.md | Simple |
| 6 | Document supervisord | 🟠 High | CLAUDE.md | Simple |
| 7 | Startup secret validation | 🟡 Medium | main.py | Simple |
| 8 | Parse published_at | 🟡 Medium | sentiment.py | Simple |
| 9 | Forex sleep constant | 🟡 Medium | forex.py | Trivial |
| 10 | Fix asyncio deprecation | 🟡 Medium | 3 task files | Moderate |
| 11 | Fix SEO route order | 🟡 Medium | seo.py | Trivial |
| 12 | signal_feedback tests | 🟡 Medium | new test file | Moderate |
| 13 | earnings_calendar tests | 🟡 Medium | new test file | Simple |
| 14 | Model __init__ exports | 🟡 Medium | __init__.py | Trivial |
| 15 | CLAUDE.md full refresh | 🟡 Medium | CLAUDE.md | Large |

**Total**: 15 tasks (1 already done = 14 actionable). Phases 1-3 are code changes. Phase 4 is documentation only.

---

## Review Checkpoint

Before implementation begins, review this plan for:
1. Are all audit findings accounted for?
2. Is the dependency order correct (Task 14 before Task 1)?
3. Any findings that should be reclassified in severity?
4. Should Task 15 (CLAUDE.md refresh) be split into smaller tasks?

---

## Handoff

Once approved, execute phases in order. All code changes (Phases 1-3) must pass the full test suite before committing. Phase 4 (documentation) can be a separate commit.

**Test commands**:
```bash
cd backend && python -m pytest tests/ -v --override-ini="asyncio_mode=auto"
cd frontend && npx vitest run
```
