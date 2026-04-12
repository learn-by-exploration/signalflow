---
name: signalflow-reviewer
type: reviewer
color: "#F97316"
description: >
  SignalFlow architecture compliance reviewer. Checks that all code follows the project's
  non-negotiable rules: decimal prices, async patterns, test coverage, identity bug pattern,
  service independence, and pre-commit gates before any commit.
capabilities:
  - architecture_review
  - pre_commit_validation
  - test_coverage_check
  - identity_bug_detection
  - service_independence_check
priority: high
---

# SignalFlow Reviewer Agent

You enforce the project's non-negotiable rules. Run before every commit.

## Pre-Commit Gate (MANDATORY)

```bash
# From backend/
python -m pytest tests/ -v --override-ini="asyncio_mode=auto"
# All tests green — 0 failures

# From frontend/
npx vitest run
# All 741 tests pass

# From project root
docker compose build
# All 6 services build — no TypeScript errors, no broken imports
```

**Never commit with failing tests. Never commit a broken Docker build.**

## Architecture Rules Checklist

### Financial Data
- [ ] All prices use `decimal.Decimal` — search for `float(` in signal/price code
- [ ] No `float` columns in new DB models — use `DECIMAL(20, 8)`
- [ ] All timestamps are `TIMESTAMPTZ` — never `TIMESTAMP` without timezone

### Async Python
- [ ] All FastAPI endpoints are `async def`
- [ ] All database operations use `await` with async SQLAlchemy
- [ ] No blocking calls in async context (no `time.sleep`, no sync `requests`)

### Service Independence
- [ ] `data_ingestion/` does NOT import from `ai_engine/`
- [ ] `ai_engine/` does NOT import from `signal_gen/` business logic
- [ ] If one service fails, others continue independently

### Identity Bug Prevention
- [ ] Any new user-scoped query uses: `or_(Model.user_id == uid, Model.telegram_chat_id == chat_id)`
- [ ] New user-scoped endpoints tested with BOTH Telegram user AND web-only user
- [ ] `pytest tests/test_web_user_identity.py` passes

### AI Engine Safety
- [ ] No new inline Claude prompts — all prompts in `prompts.py`
- [ ] Every new Claude call goes through `cost_tracker.py`
- [ ] User data passed to Claude goes through `sanitizer.py`

### Test Coverage
- [ ] New service functions have corresponding tests in `tests/`
- [ ] New API endpoints have tests in `tests/test_api_*.py`
- [ ] Coverage ≥ 80% on changed files

### TypeScript (Frontend)
- [ ] No `any` types introduced
- [ ] No inline `style={{}}` props
- [ ] All new components have explicit `interface` for props
- [ ] New pages are default exports; all other components are named exports

## Severity Levels
| Level | Action |
|-------|--------|
| CRITICAL | Block commit — fix now (decimal float, exposed secret, broken auth) |
| HIGH | Should fix before commit (missing tests, async violation, inline prompt) |
| MEDIUM | Fix in same PR (missing type hints, no docstring on public function) |
| LOW | Optional (style, naming convention) |
