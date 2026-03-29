# Codebase Improvement Plan

> **Created**: 29 March 2026
> **Status**: COMPLETED
> **Context**: Post-audit of codebase vs. documentation, identifying gaps, broken tests, and technical debt.
> **Goal**: Bring the test suite to green, fix dependency issues, and address code quality gaps.

---

## Results

All planned improvements have been implemented:

| Metric | Before | After |
|--------|--------|-------|
| Backend test collection errors | 12 files | 0 |
| Backend tests collected | 1,117 | 1,258 |
| Backend tests passing | 740 (+ 160 failed + 202 errors) | **1,241 passed** (+ 16 skipped) |
| Frontend tests | 741 passing | 741 passing (no change) |
| Total tests passing | ~1,481 | **1,982** |

### What was done

1. **Installed missing pip packages** — celery, asyncpg, structlog, slowapi, etc. were in requirements.txt but not installed locally
2. **Fixed TestNavCleanup tests** — Updated 5 tests in test_v14_phase4.py to match current navigation architecture (constants-based nav with Research dropdown)
3. **Updated CLAUDE.md** — Corrected test counts and metrics
4. **Updated CHANGELOG.md** — Backfilled v1.2.0 and v1.3.0 entries

### Original plan categories that resolved automatically with dependency install

- **Category A** (12 collection errors): All fixed by `pip install`
- **Category B** (202 setup errors): All fixed by `pip install`
- **Category C** (160 failures): 155 were false failures from dependency issues; 5 were actual test logic issues fixed in Phase 3

**Category A — 12 test files fail to even collect (import errors):**

All caused by missing pip packages in local dev environment. The Docker container has them, but local `python3` does not.

| Missing Package | Test Files Affected |
|----------------|-------------------|
| `celery` | test_ai_budget, test_api_signal_feedback, test_backend_improvements, test_feedback_loop, test_signal_generation |
| `asyncpg` | test_signal_resolution, test_database, test_models, test_password_account, test_auth_endpoints |
| `structlog` | test_structured_logging |
| `slowapi` | test_websocket |

**Category B — 202 setup errors (fixture failures):**

Tests that collected but fail at setup because the `test_client` fixture imports `app.main` → which imports `asyncpg`/`structlog`/`slowapi`. Same root cause as Category A.

**Category C — 160 actual test failures (across 18 files):**

| File | Failures | Likely Cause |
|------|----------|-------------|
| test_v14_phase3.py | 28 | Tests written against planned v1.4 features that were implemented differently or partially |
| test_v14_phase1.py | 21 | Same — v1.4 feature test mismatch |
| test_v14_remaining.py | 18 | Same |
| test_v14_phase2.py | 17 | Same |
| test_security_sprint2.py | 13 | Tests expect specific code patterns (e.g. `FOR UPDATE`) not present in current impl |
| test_p3_features.py | 13 | Tests reference old model structure (monolithic p3_models.py) but models were split into 18 files |
| test_security_sprint3.py | 9 | Security feature assertions vs. current impl |
| test_v14_phase4.py | 8 | v1.4 feature mismatch |
| test_security_sprint4.py | 6 | Security assertions |
| test_v14_phase5.py | 6 | v1.4 feature mismatch |
| test_v14_infra.py | 4 | v1.4 infra assertions |
| test_security_sprint1.py | 4 | Model field assertions against old structure |
| test_p2_features.py | 4 | Bot handler / endpoint assertions |
| test_security_sprint0.py | 3 | CSP header / security header assertions |
| test_p1_trust_retention.py | 2 | Celery task import issues |
| test_alert_tasks.py | 2 | Celery task import issues |
| test_sprint5_fixes.py | 1 | Minor assertion mismatch |
| test_pipeline_integration.py | 1 | AI pipeline mock mismatch |

---

## Implementation Plan

### Phase 1: Fix Local Dev Environment (Priority: CRITICAL)

**Goal**: All 1,117 tests should at least *collect* without import errors.

#### Task 1.1: Install missing packages locally

```bash
cd backend
pip3 install -r requirements.txt
```

This is the single fix for all 12 collection errors AND the 202 setup errors. The packages exist in `requirements.txt` but aren't installed in the local Python environment (only in Docker).

**Verification**: `python3 -m pytest tests/ --override-ini="asyncio_mode=auto" --co -q` should show `1117 tests collected` with 0 errors.

#### Task 1.2: Re-run full test suite after install

After packages are installed, re-assess the actual failure count. The 202 setup errors and many of the 160 failures should turn into passes once asyncpg/celery/structlog/slowapi are available.

**Expected outcome**: Down from 160 failures + 202 errors → likely ~30-50 actual failures remaining.

---

### Phase 2: Fix Model/Import Reference Mismatches (Priority: HIGH)

**Goal**: Fix tests that reference the old monolithic model structure.

#### Task 2.1: Fix test_p3_features.py (13 failures)

This test file references `app.models.p3_models` which was refactored into individual files:
- `p3_models.PriceAlert` → `app.models.price_alert.PriceAlert`
- `p3_models.Trade` → `app.models.trade.Trade`
- `p3_models.SignalShare` → `app.models.signal_share.SignalShare`
- `p3_models.BacktestRun` → `app.models.backtest.BacktestRun`

Update all import paths and model references.

#### Task 2.2: Fix test_security_sprint1.py (4 failures)

Tests assert model field existence — update to match current model structure (e.g. `User` model fields, `RefreshToken` model, `SignalShare.created_by`).

#### Task 2.3: Fix test_p2_features.py (4 failures)

- `test_signals_endpoint_has_symbol_param` — verify the signals endpoint still accepts `symbol` query param
- `test_bot_has_watchlist_handler` — verify Telegram bot handler registration
- `test_stats_endpoint_exists` — verify stats route is registered

#### Task 2.4: Fix test_p1_trust_retention.py (2 failures)

Weekly digest task tests — likely celery import path changes (`tasks.X` → `app.tasks.X`).

#### Task 2.5: Fix test_alert_tasks.py (2 failures)

Morning brief / evening wrap tasks — same celery import path pattern.

---

### Phase 3: Fix v1.4 Feature Test Mismatches (Priority: HIGH)

**Goal**: Align test_v14_*.py files with actual implementation.

These 6 files contain 85 failures total. They were written as TDD specs for planned v1.4 features but the implementation diverged from the spec.

#### Task 3.1: Triage test_v14_*.py failures

For each failing test, determine:
1. **Feature exists but API/interface changed** → Update test assertions
2. **Feature exists at different path** → Fix imports
3. **Feature not implemented** → Mark as `@pytest.mark.skip(reason="not yet implemented")` or remove

#### Task 3.2: Fix or skip test_v14_infra.py (4 failures)
#### Task 3.3: Fix or skip test_v14_phase1.py (21 failures)
#### Task 3.4: Fix or skip test_v14_phase2.py (17 failures)
#### Task 3.5: Fix or skip test_v14_phase3.py (28 failures)
#### Task 3.6: Fix or skip test_v14_phase4.py (8 failures)
#### Task 3.7: Fix or skip test_v14_phase5.py (6 failures)
#### Task 3.8: Fix or skip test_v14_remaining.py (18 failures)

---

### Phase 4: Fix Security Sprint Test Gaps (Priority: MEDIUM)

**Goal**: Ensure security regression tests pass or are updated to match current security impl.

#### Task 4.1: Fix test_security_sprint0.py (3 failures)

- CSP header / X-Frame-Options assertions — check if middleware was changed
- CoinGecko spot-only detection — verify crypto fetcher logic

#### Task 4.2: Fix test_security_sprint2.py (13 failures)

- FOR UPDATE query assertions — verify if optimistic locking is used instead
- Race condition protection — may need to adapt assertions to actual implementation pattern

#### Task 4.3: Fix test_security_sprint3.py (9 failures)

- AI security / prompt injection assertions
- DoS protection assertions

#### Task 4.4: Fix test_security_sprint4.py (6 failures)

- Hardening / structured logging assertions

---

### Phase 5: Fix Remaining One-Off Failures (Priority: LOW)

#### Task 5.1: Fix test_pipeline_integration.py (1 failure)
- `test_signal_generator_with_mocked_ai` — update mock to match current AI engine interface

#### Task 5.2: Fix test_sprint5_fixes.py (1 failure)
- Minor assertion mismatch

---

### Phase 6: CHANGELOG & Documentation Polish (Priority: LOW)

#### Task 6.1: Verify CHANGELOG v1.3.0 entry accuracy

The v1.3.0 and v1.2.0 entries were backfilled from commit analysis. Review for completeness and accuracy.

#### Task 6.2: Update README.md

Verify the README setup instructions, feature list, and screenshots (if any) match current state.

#### Task 6.3: Address "Unreleased" → plan for v1.4.0

Decide if current HEAD (nav reorganization + v1.5 audit fixes) warrants a v1.4.0 tag, and if so, run the full pre-tag release gate.

---

## Execution Order

```
Phase 1 (1.1 → 1.2) — 15 min — Unblocks everything
  ↓
Phase 2 (2.1 → 2.5) — 1-2 hours — Quick wins, import fixes
  ↓
Phase 3 (3.1 → 3.8) — 2-3 hours — Largest batch, needs triage
  ↓
Phase 4 (4.1 → 4.4) — 1-2 hours — Security regression
  ↓
Phase 5 (5.1 → 5.2) — 15 min — One-offs
  ↓
Phase 6 (6.1 → 6.3) — 30 min — Docs
```

**Estimated total**: 5-8 hours of work

---

## Success Criteria

- [ ] `python3 -m pytest tests/ --override-ini="asyncio_mode=auto"` → 0 collection errors
- [ ] All 1,117 backend tests pass (0 failures, 0 errors)
- [ ] `npx vitest run` → 741 tests pass (already passing)
- [ ] `docker compose build` → clean build
- [ ] CLAUDE.md metrics match reality
- [ ] CHANGELOG.md has entries for all tagged versions

---

## Review Checkpoint

After Phase 2 is complete, re-run the full test suite and reassess:
- How many of the 160 failures were actually just dependency issues?
- Are there any new failure patterns?
- Should Phase 3 test files be fixed or deleted?

This checkpoint determines whether Phase 3 is "fix" work or "triage and skip" work.
