# SignalFlow AI — Improvement Spec v4

> **Date**: 21 March 2026  
> **Author**: Brainstorm Agent  
> **Status**: Draft — Ready for review  
> **Previous**: [spec-v3.md](spec-v3.md) (12 items, sprints 7-9 completed)

---

## Context

Nine sprints of improvements have been completed across three specs:

| Sprint | Spec | Items Shipped |
|--------|------|---------------|
| 1 | v1 | User store (chatId), WebSocket status dot, sort controls, target progress bar, expiry countdown, accessibility |
| 2 | v1 | Rate limiting (slowapi), WebSocket server pings, health endpoint, AskAI error handling, font optimization |
| 3 | v1 | Sentiment badge, ErrorBoundary improvements, WinRateCard error/retry, market data error tracking |
| 4 | v1 | Keyboard shortcuts, auto-refresh countdown, enhanced sparkline with target/stop-loss lines |
| 5 | v2 | History JOIN with signals table, .NS symbol fix in generator, pagination total count, live price change on cards |
| 6 | v2 | History page filters, market heatmap, Load More pagination |
| 7 | v3 | Signal resolution .NS bug, livePrice to TargetProgressBar, symbol track record, history market filter, signal age warning |
| 8 | v3 | Signal detail page `/signal/[id]`, dashboard ↔ detail links, accuracy trend chart, portfolio P&L chart |
| 9 | v3 | Sortable history columns, notification badge for new signals, market hours indicator |

**Tests**: 243 passing, 14 skipped.

**This spec** focuses on: performance, polish, robustness, mobile UX, accessibility, testing gaps, and feature refinements identified through deep codebase exploration.

---

## Issues Found During Exploration

### Category Breakdown

| Category | Issues | Priority Distribution |
|----------|--------|-----------------------|
| Performance & Bundle | 3 | 1 HIGH, 2 MEDIUM |
| Backend Robustness | 4 | 2 HIGH, 2 MEDIUM |
| Frontend UX & Polish | 5 | 1 HIGH, 3 MEDIUM, 1 LOW |
| Mobile UX | 3 | 1 HIGH, 2 MEDIUM |
| Accessibility | 2 | 1 HIGH, 1 MEDIUM |
| Testing Gaps | 3 | 1 HIGH, 2 MEDIUM |
| Dead Code & Cleanup | 2 | 2 LOW |

**Total: 22 improvements across 2 sprints.**

---

## Sprint 10 — Performance, Backend Robustness, Mobile (13 items)

### 1. Portfolio Summary Uses Last Trade Price Instead of Live Market Price (Priority: HIGH)

**Problem**: `GET /api/v1/portfolio/summary` calculates current position value using `func.max(Trade.price).label("last_price")` — the highest trade price for a symbol, not the current market price. If the user bought HDFCBANK at ₹1,600 three weeks ago and the price is now ₹1,750, the portfolio still shows ₹1,600 as the "current value." This makes P&L calculations wrong, sometimes significantly.

The comment in the code acknowledges this: `"Current value uses the last trade price as proxy (real-time pricing would require a market data lookup)."`

**Files to modify**:
- `backend/app/api/portfolio.py` — Query `market_data` for live prices per symbol

**Changes**:
1. After calculating `net_qty` and `net_cost` per symbol, perform a subquery against `market_data` to get the latest close price for each position symbol:
   ```python
   # For each position symbol, get the latest market price
   latest_price_subq = (
       select(MarketData.symbol, MarketData.close)
       .distinct(MarketData.symbol)
       .order_by(MarketData.symbol, MarketData.timestamp.desc())
   )
   ```
2. Normalize symbols when matching (strip `.NS` for stocks stored without suffix).
3. Fall back to `last_price` (from trades) only if no market data exists for that symbol.
4. Update the `PortfolioSummary` response to include a `price_source` field: `"live"` or `"last_trade"`.

**User impact**: P&L becomes accurate and real-time. A user with 5 positions sees her actual portfolio value, not a stale estimate. This is foundational for a trading platform.

---

### 2. AI Q&A Endpoint Uses Raw SQL `text()` (Priority: HIGH)

**Problem**: The `ask_about_symbol` endpoint in `ai_qa.py` uses raw `text()` SQL queries:
```python
market_row = await db.execute(
    text("SELECT close, high, low, volume, timestamp FROM market_data WHERE symbol = :sym ORDER BY timestamp DESC LIMIT 1"),
    {"sym": symbol},
)
```
While parameterized (safe from injection), this bypasses SQLAlchemy's model system, meaning:
- No type checking or column validation at import time
- Column renames or model changes won't be caught
- Inconsistent with every other endpoint that uses ORM queries

Additionally, the symbol lookup doesn't handle the `.NS` normalization, so asking about "HDFCBANK.NS" will find no market data (stored as "HDFCBANK").

**Files to modify**:
- `backend/app/api/ai_qa.py` — Replace `text()` with ORM `select()` queries

**Changes**:
1. Replace the market data query:
   ```python
   query_symbol = symbol.replace(".NS", "")
   stmt = (
       select(MarketData.close, MarketData.high, MarketData.low, MarketData.volume, MarketData.timestamp)
       .where(MarketData.symbol == query_symbol)
       .order_by(MarketData.timestamp.desc())
       .limit(1)
   )
   md = (await db.execute(stmt)).first()
   ```
2. Replace the signals query similarly with ORM `select(Signal)`.
3. Add `.NS` normalization to the symbol before querying.

**User impact**: Fixes silent 429-like failures when users ask about Indian stocks with `.NS` suffix. Also improves code consistency and maintainability.

---

### 3. History Page Does Not Load All Results (Priority: HIGH)

**Problem**: The history page calls `api.getSignalHistory()` once on mount with no pagination parameters — it gets the first 20 items and stops. Unlike the signal feed which has "Load More" functionality, the history page has no way to load older entries. If the user has 50+ resolved signals, she can only see the latest 20.

The backend supports `limit` and `offset` params, and returns `meta.total`, but the frontend doesn't use them.

**Files to modify**:
- `frontend/src/app/history/page.tsx` — Add Load More or pagination

**Changes**:
1. Track `offset` state and `total` from the API response.
2. Add a "Load More" button at the bottom (matching the pattern in `SignalFeed.tsx`):
   ```tsx
   const hasMore = total != null && history.length < total;
   // ...
   {hasMore && (
     <button onClick={loadMore} className="...">
       Load More ({history.length} of {total})
     </button>
   )}
   ```
3. `loadMore` calls `api.getSignalHistory(new URLSearchParams({ offset: String(history.length), limit: '20' }))` and appends results.
4. Show "Showing X of Y signals" in the summary bar.

**User impact**: Users with extensive history can actually browse all their resolved signals, not just the latest 20.

---

### 4. Market Overview Horizontal Scroll Cuts Off on Mobile (Priority: HIGH)

**Problem**: `MarketOverview` renders market tickers in a `flex` row with `overflow-x-auto`. On mobile screens (<640px), the three market sections (Stocks, Crypto, Forex) with 3 symbols each overflow horizontally. The `scrollbar-none` class hides the scrollbar, so there's no visual cue that content is scrollable. Users on phones may never realize there are more tickers to the right.

**Files to modify**:
- `frontend/src/components/markets/MarketOverview.tsx` — Improve mobile layout

**Changes**:
1. On mobile, stack market sections vertically instead of horizontally:
   ```tsx
   <div className="flex items-center gap-6 overflow-x-auto scrollbar-none md:flex-row flex-col md:items-center items-start gap-y-1.5">
   ```
2. Alternatively, show only 1 symbol per market on mobile (the most changed), with a "See all" that expands to the heatmap.
3. Add a subtle fade gradient on the right edge to hint at scrollable content:
   ```css
   .market-ticker-container::after {
     content: '';
     position: absolute;
     right: 0;
     width: 24px;
     background: linear-gradient(to right, transparent, var(--bg-secondary));
   }
   ```
4. Add `snap-x snap-mandatory` to the scroll container and `snap-start` to each section for momentum scrolling on touch devices.

**User impact**: Mobile users (the primary use case — checking signals on phone) can see all market data without mystery scrolling.

---

### 5. useSignals Creates New `params` Object Every Render (Priority: HIGH)

**Problem**: In `useSignals.ts`, the `fetchSignals` callback depends on `[params, setSignals, setLoading, setError]`. The `params` parameter comes from the component. If the calling component doesn't memoize `params`, a new `URLSearchParams` object is created every render, causing `fetchSignals` to be recreated, which triggers the `useEffect` to re-run, creating an infinite loop of API calls.

In `page.tsx`, `useSignals()` is called without params (so `params` is `undefined` — stable). But this is a latent bug: any future caller that passes `new URLSearchParams(...)` inline will trigger infinite re-fetching.

**Files to modify**:
- `frontend/src/hooks/useSignals.ts` — Stabilize params dependency

**Changes**:
1. Serialize params to string for the dependency array:
   ```typescript
   const paramsString = params?.toString() ?? '';
   
   const fetchSignals = useCallback(async () => {
     // ... use params from closure
   }, [paramsString, setSignals, setLoading, setError]);
   ```
2. This ensures the callback is only recreated when params actually change, not on every render.

**User impact**: Prevents potential infinite API call loops when params are passed to `useSignals`. Improves reliability.

---

### 6. CostTracker Uses Filesystem JSON — Race Conditions in Production (Priority: MEDIUM)

**Problem**: `CostTracker` stores API cost data in `ai_cost_log.json` using `_load_data()` / `_save_data()` with no locking. In production with multiple Celery workers, two concurrent sentiment analysis tasks can:
1. Both read the file (e.g., total = $5.00)
2. Both add their cost (e.g., $0.05 each)
3. Both write back $5.05 — losing one $0.05 entry.
4. Eventually the budget tracking drifts and the $30/month limit becomes unreliable.

**Files to modify**:
- `backend/app/services/ai_engine/cost_tracker.py` — Use database or Redis for storage

**Changes**:
1. **Option A (Redis — recommended)**: Use Redis `INCRBYFLOAT` for atomic cost tracking:
   ```python
   async def record_usage_async(self, redis_client, input_tokens, output_tokens, task_type, symbol):
       cost = self.calculate_cost(input_tokens, output_tokens)
       month_key = f"ai_cost:{self._get_month_key()}"
       await redis_client.incrbyfloat(month_key, cost)
       await redis_client.expire(month_key, 40 * 86400)  # 40 days TTL
       return cost
   ```
2. **Option B (file locking)**: Use `fcntl.flock()` around reads/writes. Less robust than Redis but simpler.
3. Keep the JSON file as a backup/audit log, but use Redis as the source of truth for budget checking.
4. Update `is_budget_available()` to check Redis.

**User impact**: Prevents cost tracking drift that could either block AI features prematurely or allow budget overruns. More reliable in multi-worker production.

---

### 7. Health Endpoint Missing Active Signal Count and Last Data Fetch (Priority: MEDIUM)

**Problem**: The `/health` endpoint checks database and Redis connectivity (good), but per CLAUDE.md it should also report `active_signals_count` and `last_data_fetch`. These are critical for monitoring:
- If `active_signals_count` drops to 0, signal generation may be broken.
- If `last_data_fetch` is >10 minutes old, data ingestion may be stalled.

The health endpoint currently returns:
```json
{ "status": "healthy", "uptime": "...", "environment": "...", "db_status": "ok", "redis_status": "ok" }
```

**Files to modify**:
- `backend/app/main.py` — Add signal count and data freshness queries

**Changes**:
1. Add to the health check:
   ```python
   # Active signal count
   from app.models.signal import Signal
   sig_count = await db.execute(select(func.count()).where(Signal.is_active.is_(True)))
   status["active_signals_count"] = sig_count.scalar() or 0
   
   # Last data fetch timestamp
   from app.models.market_data import MarketData
   last_fetch = await db.execute(select(func.max(MarketData.timestamp)))
   status["last_data_fetch"] = last_fetch.scalar()
   ```
2. Set `status = "degraded"` if active signals = 0 or last data fetch > 10 minutes old.
3. Add `ai_budget_remaining_pct` from cost tracker.

**User impact**: Enables UptimeRobot to detect signal generation failures and data pipeline stalls, not just server up/down.

---

### 8. Shared Signal Page Missing SEO Metadata (Priority: MEDIUM)

**Problem**: The `/shared/[id]` page renders a signal card for external viewers (shared via URL), but has no dynamic `<title>` or OpenGraph tags. When shared via WhatsApp or Telegram, the link preview shows the generic "SignalFlow AI — Trading Signals" instead of something like "STRONG BUY — HDFCBANK (92% confidence)".

The `/signal/[id]` detail page has the same issue — no dynamic metadata.

**Files to modify**:
- `frontend/src/app/shared/[id]/page.tsx` — Add dynamic metadata
- `frontend/src/app/signal/[id]/page.tsx` — Add dynamic metadata

**Changes**:
1. Since these are client components (`'use client'`), use `useEffect` to set `document.title`:
   ```tsx
   useEffect(() => {
     if (signal) {
       document.title = `${signal.signal_type.replace('_', ' ')} — ${shortSymbol(signal.symbol)} (${signal.confidence}%) | SignalFlow AI`;
     }
   }, [signal]);
   ```
2. For proper OG tags, consider converting these to server components using `generateMetadata()`:
   ```tsx
   export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
     const res = await fetch(`${API_URL}/api/v1/signals/shared/${params.id}`);
     const data = await res.json();
     return {
       title: `${data.data.signal_type} — ${data.data.symbol} | SignalFlow AI`,
       description: `${data.data.confidence}% confidence. Target: ${data.data.target_price}, Stop: ${data.data.stop_loss}`,
     };
   }
   ```
3. If keeping as client component, at minimum set `document.title` dynamically.

**User impact**: Shared signal links show meaningful previews in social/messaging apps, increasing engagement and professionalism.

---

### 9. Signal Detail Page Chart Uses Fixed Width (Priority: MEDIUM)

**Problem**: In `/signal/[id]/page.tsx`, the Sparkline component is rendered with `width={600}`:
```tsx
<Sparkline data={recentCloses} positive={isBuyish} width={600} height={100} ... />
```
On mobile screens (320-414px wide), this SVG overflows its container. The chart extends beyond the card boundary and either clips or causes horizontal scroll.

**Files to modify**:
- `frontend/src/app/signal/[id]/page.tsx` — Use responsive width
- `frontend/src/components/markets/Sparkline.tsx` — Support `100%` width or container-aware sizing

**Changes**:
1. **Quick fix**: Use a container ref to measure width:
   ```tsx
   const chartRef = useRef<HTMLDivElement>(null);
   const [chartWidth, setChartWidth] = useState(600);
   useEffect(() => {
     if (chartRef.current) setChartWidth(chartRef.current.offsetWidth);
     const observer = new ResizeObserver(([entry]) => setChartWidth(entry.contentRect.width));
     if (chartRef.current) observer.observe(chartRef.current);
     return () => observer.disconnect();
   }, []);
   // Then: <div ref={chartRef}><Sparkline width={chartWidth} ... /></div>
   ```
2. **Better fix**: Update `Sparkline` to accept `width="100%"` by using `viewBox` and `preserveAspectRatio` on the SVG:
   ```tsx
   <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto" preserveAspectRatio="none">
   ```

**User impact**: Price charts display properly on all screen sizes. Currently broken on mobile.

---

### 10. SignalCard Expanded Section Has Duplicate Indicator Rows on Detail Page (Priority: MEDIUM)

**Problem**: On the `/signal/[id]` detail page, technical indicators are displayed twice:
1. A detailed `IndicatorDetail` grid (RSI, MACD, Volume, Bollinger, SMA)
2. A compact `IndicatorPill` row immediately below it with the same RSI, MACD, Vol data

This is redundant — the detail page has enough space for the full grid; the pills are just noise.

**Files to modify**:
- `frontend/src/app/signal/[id]/page.tsx` — Remove the duplicate pill row

**Changes**:
1. Remove the `<div className="flex flex-wrap gap-1.5 mt-3">` block containing the redundant `IndicatorPill` components (lines that follow the `IndicatorDetail` grid).

**User impact**: Cleaner detail page without confusing duplicate data.

---

### 11. Backtest Page Has No Input Validation Feedback (Priority: MEDIUM)

**Problem**: The backtest page lets users type any string as a symbol. If they enter "ASDF", the backtest starts, runs for up to 120 seconds polling, and eventually returns `status: "failed"`. There's no upfront validation that the symbol exists in tracked symbols or market data.

Also, the polling `setInterval` in `startBacktest()` is never cleaned up if the component unmounts during polling. This is a memory leak.

**Files to modify**:
- `frontend/src/app/backtest/page.tsx` — Add symbol validation and cleanup

**Changes**:
1. Add a symbol validation check before starting the backtest:
   ```tsx
   const VALID_SYMBOLS = [
     'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', // ...tracked_stocks
     'BTCUSDT', 'ETHUSDT', // ...tracked_crypto
     'EUR/USD', 'GBP/JPY', // ...tracked_forex
   ];
   ```
   Or better: fetch tracked symbols from the backend config and show a dropdown/autocomplete.
2. Show a warning if the entered symbol doesn't match: "This symbol may not have enough data. Try one of: HDFCBANK.NS, BTCUSDT, EUR/USD"
3. Clean up the polling interval on unmount:
   ```tsx
   useEffect(() => {
     return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
   }, []);
   ```

**User impact**: Prevents wasted time on invalid backtests and eliminates a memory leak.

---

### 12. Alert Config `useEffect` Missing `chatId` Dependency (Priority: MEDIUM)

**Problem**: In `frontend/src/app/alerts/page.tsx`, the `useEffect` that loads alert config, price alerts, and watchlist uses `chatId` from the store but doesn't include it in the dependency array:
```tsx
useEffect(() => {
    async function loadAll() { /* uses chatId */ }
    loadAll();
}, []); // <-- chatId not in deps
```
If the user changes their chat ID (via ChatIdPrompt), the alerts page won't reload with the correct data until they navigate away and back.

The same pattern exists in `portfolio/page.tsx`.

**Files to modify**:
- `frontend/src/app/alerts/page.tsx` — Add `chatId` to dependency array
- `frontend/src/app/portfolio/page.tsx` — Add `chatId` to dependency array

**Changes**:
1. Add `chatId` to both useEffect hooks:
   ```tsx
   useEffect(() => {
     loadAll();
   }, [chatId]);
   ```
2. Reset state when chatId changes to show loading state:
   ```tsx
   useEffect(() => {
     setLoading(true);
     loadAll();
   }, [chatId]);
   ```

**User impact**: Prevents stale data display when user switches chat ID. Currently shows the wrong user's data.

---

### 13. No Frontend Error Tracking / Reporting (Priority: MEDIUM)

**Problem**: The backend has Sentry integration configured via `sentry_dsn`. The frontend has no error reporting — `ErrorBoundary` catches errors and shows a UI fallback, but doesn't send them anywhere. Console errors on user devices are invisible to the developer.

**Files to modify**:
- `frontend/src/app/layout.tsx` — Initialize Sentry
- `frontend/src/components/shared/ErrorBoundary.tsx` — Report to Sentry

**Changes**:
1. Install `@sentry/nextjs` (peer dependency):
   ```json
   "@sentry/nextjs": "^8.0.0"
   ```
2. Add Sentry init in layout or `instrumentation.ts`:
   ```tsx
   if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
     Sentry.init({ dsn: process.env.NEXT_PUBLIC_SENTRY_DSN, tracesSampleRate: 0.1 });
   }
   ```
3. In `ErrorBoundary.componentDidCatch`, report:
   ```tsx
   Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } });
   ```
4. Add `NEXT_PUBLIC_SENTRY_DSN` to `.env.example`.

**User impact**: Developer gets visibility into production frontend errors, enabling faster diagnosis and fix of user-facing issues.

---

## Sprint 11 — Accessibility, Testing, Polish (9 items)

### 14. Signal Detail Page Not Accessible via Keyboard (Priority: HIGH)

**Problem**: The signal detail page (`/signal/[id]`) has several interactive elements that aren't keyboard accessible:
- The "Back to Dashboard" link works (it's an `<a>`)
- But the `RiskCalculator` preset amount buttons don't have keyboard focus indicators
- The `ShareButton` opens a share dialog but doesn't trap focus
- There's no skip-to-content link
- The expandable sections have no heading hierarchy — it's all `<h2>` at the same level

More broadly across the app:
- The `MarketHeatmap` cells are `<div>` with hover tooltips but no keyboard interaction — they should be focusable if they're informational
- The portfolio trade form inputs lack `id` attributes matching their `<label>` elements (accessibility violation)

**Files to modify**:
- `frontend/src/app/signal/[id]/page.tsx` — Add heading hierarchy, skip link
- `frontend/src/components/signals/RiskCalculator.tsx` — Add focus rings
- `frontend/src/app/portfolio/page.tsx` — Add `id`/`htmlFor` to form inputs
- `frontend/src/components/markets/MarketHeatmap.tsx` — Add keyboard access

**Changes**:
1. **Heading hierarchy**: Use `<h1>` for signal symbol/badge at top, `<h2>` for sections (Price, Technical Indicators, AI Reasoning, Risk Calculator, Track Record), `<h3>` for subsections.
2. **Focus rings**: Add `focus-visible:ring-2 focus-visible:ring-accent-purple focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary` to all interactive buttons that lack them (RiskCalculator presets, MarketHeatmap cells).
3. **Portfolio form labels**: Add `htmlFor` and matching `id` attributes:
   ```tsx
   <label htmlFor="trade-symbol" ...>Symbol</label>
   <input id="trade-symbol" ... />
   ```
4. **HeatmapCells**: Add `tabIndex={0}` and `role="gridcell"` with `aria-label`:
   ```tsx
   <div tabIndex={0} role="gridcell" aria-label={`${symbol}: ${pct}% change`} ...>
   ```

**User impact**: Screen reader users and keyboard-only users can navigate the full app. Required for basic WCAG 2.1 AA compliance.

---

### 15. No Tests for API Endpoints (Signals, History, Markets, Portfolio) (Priority: HIGH)

**Problem**: The test suite has 243 passing tests covering indicators, signal scoring, targets, signal resolution, formatters, alert tasks, and frontend utilities. However, there are **no integration tests for the actual API endpoints**:
- `GET /api/v1/signals` — no test
- `GET /api/v1/signals/{id}` — no test
- `GET /api/v1/signals/history` — no test
- `GET /api/v1/signals/stats` — no test
- `GET /api/v1/markets/overview` — no test
- `POST /api/v1/portfolio/trades` — no test
- `GET /api/v1/portfolio/summary` — no test
- `POST /api/v1/ai/ask` — no test

The `test_api_integration.py` file exists but likely has limited endpoint coverage. The test files `test_backend_improvements.py` test the health endpoint and WebSocket but not the core data endpoints.

**Files to modify**:
- `backend/tests/test_api_endpoints.py` — New comprehensive test file

**Changes**:
1. Create a new test file with endpoint coverage:
   ```python
   class TestSignalEndpoints:
       async def test_list_signals_returns_200(self, client, db)
       async def test_list_signals_with_market_filter(self, client, db)
       async def test_list_signals_pagination(self, client, db)
       async def test_get_signal_by_id(self, client, db)
       async def test_get_signal_not_found(self, client)
   
   class TestHistoryEndpoints:
       async def test_list_history_with_join(self, client, db)
       async def test_history_outcome_filter(self, client, db)
       async def test_signal_stats(self, client, db)
       async def test_accuracy_trend(self, client, db)
       async def test_symbol_track_record(self, client, db)
   
   class TestMarketEndpoints:
       async def test_market_overview(self, client, db)
   
   class TestPortfolioEndpoints:
       async def test_log_trade(self, client, db)
       async def test_portfolio_summary(self, client, db)
       async def test_portfolio_summary_empty(self, client)
   ```
2. Use `pytest-asyncio` with test database fixtures from `conftest.py`.
3. Seed test data (signals, market data, history entries) in fixtures.

**User impact**: Catches regressions before they reach production. Currently, endpoint-breaking changes would only be caught by manual testing.

---

### 16. FormatPrice Doesn't Handle Forex Currency Symbols (Priority: MEDIUM)

**Problem**: `formatPrice()` in `formatters.ts` adds `₹` for stocks, no symbol for crypto/forex. Forex prices should show their pair context — displaying `1.0854` is ambiguous without knowing it's EUR/USD. Meanwhile, crypto prices above 1000 use `en-IN` locale formatting (Indian commas: 1,00,000) which is wrong for USD-denominated crypto.

**Files to modify**:
- `frontend/src/utils/formatters.ts` — Fix forex and crypto formatting

**Changes**:
1. Update `formatPrice` for forex:
   ```typescript
   if (marketType === 'forex') {
     return num.toFixed(4); // Forex is already rate-based, no currency symbol needed
   }
   ```
   This is acceptable as-is, but add a context-aware option:
   ```typescript
   if (marketType === 'crypto') {
     if (num >= 1000) return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
     return '$' + num.toFixed(4);
   }
   ```
2. Change crypto formatting to use `en-US` locale (USD convention: `$97,842.00` not `$97,842.00` with Indian commas).
3. Keep `en-IN` locale only for `marketType === 'stock'`.

**User impact**: Prices display with correct cultural formatting. Crypto prices show `$97,842.00` not `97,842.00`. Indian stock prices show `₹1,67,890.00` correctly.

---

### 17. WinRateCard Stats Response Has Wrong Type Casting (Priority: MEDIUM)

**Problem**: `WinRateCard` fetches stats via `api.getSignalStats()` and casts the result as `SignalStats`:
```tsx
const res = await api.getSignalStats() as SignalStats;
setStats(res);
```
But the API returns `{ data: {...} }` wrapped in an envelope per the API contract — not the stats object directly. The `SignalStatsResponse` schema wraps the fields at the top level (not in a `data` key), but this is inconsistent with every other endpoint that uses `{ data: ... }`.

Looking at the backend: `get_signal_stats()` returns a `SignalStatsResponse` directly (not wrapped in `{ data: ... }`), unlike the other endpoints. This inconsistency means:
- The frontend code works (by accident) because the response IS the stats object
- But it's inconsistent with the API envelope pattern used everywhere else

**Files to modify**:
- `backend/app/api/history.py` — Wrap stats response in `{ data: ... }` envelope
- `frontend/src/components/signals/WinRateCard.tsx` — Access via `.data`

**Changes**:
1. Backend: Change `get_signal_stats` to return `{"data": SignalStatsResponse(...)}` for consistency.
2. Frontend: Update to `const res = await api.getSignalStats() as { data: SignalStats }; setStats(res.data);`
3. Update test expectations if stats endpoint is tested.

**User impact**: No visible change, but fixes API inconsistency that would confuse future development. Prevents bugs when adding caching or middleware that expects the envelope pattern.

---

### 18. No Loading State Transitions for Filter Changes (Priority: MEDIUM)

**Problem**: On the history page and signal feed, when the user clicks an outcome filter pill or market filter, the data is filtered client-side instantly. This is fine for small datasets. But there's no visual feedback — the list just jumps. On slow devices or with 100+ items, there's a perceptible freeze during the `useMemo` re-filter.

More critically, the signal feed filters are client-side but operate on only the loaded data (up to `limit`). If the user filters to "Crypto" but all crypto signals are beyond the first 20 loaded, the filter shows "No signals" even though crypto signals exist.

**Files to modify**:
- `frontend/src/components/signals/SignalFeed.tsx` — Add server-side filtering
- `frontend/src/hooks/useSignals.ts` — Accept filter params

**Changes**:
1. When a filter changes, pass it as a query param to the API:
   ```tsx
   const params = new URLSearchParams();
   if (filter !== 'all') params.set('market', filter);
   if (search) params.set('symbol', search);
   ```
2. Re-fetch signals with the filter params instead of client-side filtering.
3. Show a brief transition animation (fade) when filters change.
4. Keep client-side sorting (this is instant and correct for loaded data).
5. Reset offset to 0 when filter changes.

**User impact**: Filter results are always complete (not limited to loaded data). "Show me only crypto signals" works even if crypto signals aren't in the first 20.

---

### 19. Portfolio Trade Form Accepts Negative Quantities and Prices (Priority: MEDIUM)

**Problem**: The portfolio trade form in `portfolio/page.tsx` uses `<input type="number">` for quantity and price but sets no `min` attribute. Users can enter negative values:
- Negative quantity: Logs a buy of `-10` shares, which corrupts the position calculation
- Negative price: `price * quantity` becomes negative, breaking P&L

The backend `TradeCreate` schema also doesn't validate these fields as positive.

**Files to modify**:
- `frontend/src/app/portfolio/page.tsx` — Add `min="0.01"` to inputs
- `backend/app/schemas/p3.py` — Add `gt=0` validation to quantity and price fields

**Changes**:
1. Frontend inputs:
   ```tsx
   <input type="number" min="0.01" step="any" ... />
   ```
2. Backend schema:
   ```python
   class TradeCreate(BaseModel):
       quantity: Decimal = Field(gt=0)
       price: Decimal = Field(gt=0)
   ```
3. Optionally validate `quantity * price` < some reasonable maximum to prevent accidental huge entries.

**User impact**: Prevents data corruption from invalid inputs. Basic input validation that should have been there from the start.

---

### 20. No Test Coverage for Signal Generator Cooldown Logic (Priority: MEDIUM)

**Problem**: The `SignalGenerator._has_recent_signal()` cooldown check (1-hour window) prevents duplicate signals for the same symbol. This is tested in `test_signal_resolution.py` for basic cases, but edge cases are missing:
- What happens at exactly the cooldown boundary (1 hour)?
- What if signals exist for a different symbol vs same symbol?
- What if the existing signal is inactive (resolved)?
- What about timezone handling in the cooldown check?

**Files to modify**:
- `backend/tests/test_signal_gen.py` or existing `test_signal_resolution.py` — Add cooldown edge case tests

**Changes**:
1. Test: Signal at exactly 59 minutes ago — should block.
2. Test: Signal at exactly 61 minutes ago — should allow.
3. Test: Inactive (resolved) signal within cooldown — should still block? or allow? (clarify business rule).
4. Test: Different symbol within cooldown — should allow.
5. Test: Same symbol, different market type — should allow? (e.g., BTCUSDT as both crypto entry and if somehow tracked elsewhere).

**User impact**: Ensures the cooldown logic works correctly at boundaries, preventing duplicate signal spam or missed signals.

---

### 21. `lightweight-charts` Package Is Unused (Priority: LOW)

**Problem**: `package.json` lists `"lightweight-charts": "^4.2.0"` as a dependency, but no file in the frontend codebase imports or uses it. All charts use either:
- Custom SVG `Sparkline` component
- Recharts (`AreaChart` in AccuracyChart, `BarChart` planned for portfolio)

This adds ~150KB to the bundle for zero benefit.

**Files to modify**:
- `frontend/package.json` — Remove `lightweight-charts`

**Changes**:
1. Remove from `dependencies`:
   ```diff
   - "lightweight-charts": "^4.2.0"
   ```
2. Run `npm install` to update lockfile.
3. Verify no import references exist (confirm with `grep -r "lightweight-charts" frontend/src/`).

**User impact**: Reduces bundle size by ~150KB. Faster page loads, especially on mobile.

---

### 22. alertStore Is Defined But Never Used (Priority: LOW)

**Problem**: `frontend/src/store/alertStore.ts` defines an `AlertState` Zustand store with `config`, `isLoading`, `setConfig`, and `setLoading`. But the alerts page (`alerts/page.tsx`) manages all state locally with `useState` — it never imports or uses `alertStore`.

**Files to modify**:
- `frontend/src/store/alertStore.ts` — Delete the file

**Changes**:
1. Delete `frontend/src/store/alertStore.ts`.
2. Verify no imports reference it:
   ```bash
   grep -r "alertStore" frontend/src/
   ```
3. If nothing references it, safe to delete.

**User impact**: None visible. Reduces code clutter and eliminates a confusing dead-code artifact.

---

## Priority Matrix

| # | Item | Priority | Effort | Category | User Impact |
|---|------|----------|--------|----------|-------------|
| 1 | Portfolio uses last trade price | HIGH | M (2-3hr) | Backend bug | P&L calculations wrong |
| 2 | AI Q&A uses raw SQL + .NS bug | HIGH | S (1hr) | Backend quality | AI Q&A fails for Indian stocks |
| 3 | History page no Load More | HIGH | S (1-2hr) | Frontend gap | Can't see >20 history items |
| 4 | MarketOverview mobile overflow | HIGH | S (1-2hr) | Mobile UX | Market data cut off on phones |
| 5 | useSignals infinite re-fetch risk | HIGH | XS (30min) | Frontend bug | Latent infinite loop |
| 6 | CostTracker filesystem race | MEDIUM | M (2-3hr) | Backend robustness | Budget tracking drift |
| 7 | Health endpoint missing metrics | MEDIUM | S (1hr) | Backend monitoring | Can't detect pipeline stalls |
| 8 | Shared/detail page no SEO | MEDIUM | S (1-2hr) | SEO | Poor link previews |
| 9 | Signal detail chart fixed width | MEDIUM | S (1hr) | Mobile UX | Chart overflows on mobile |
| 10 | Detail page duplicate indicators | MEDIUM | XS (15min) | UI cleanup | Confusing duplicated data |
| 11 | Backtest no validation + leak | MEDIUM | S (1hr) | Frontend quality | Wasted time, memory leak |
| 12 | Alert/Portfolio missing deps | MEDIUM | XS (15min) | Frontend bug | Stale data after chatId change |
| 13 | No frontend error tracking | MEDIUM | M (2-3hr) | Monitoring | Invisible production errors |
| 14 | Signal detail a11y gaps | HIGH | M (2-3hr) | Accessibility | Keyboard/screen reader blocked |
| 15 | No API endpoint tests | HIGH | L (4-6hr) | Testing | No regression safety net |
| 16 | formatPrice locale mismatch | MEDIUM | S (30min) | UI polish | Crypto prices wrong locale |
| 17 | WinRateCard API inconsistency | MEDIUM | S (30min) | API consistency | Inconsistent envelope pattern |
| 18 | Filters need server-side | MEDIUM | M (2-3hr) | Frontend quality | Missing results from filters |
| 19 | Portfolio accepts negative vals | MEDIUM | S (30min) | Validation | Data corruption risk |
| 20 | Cooldown edge case tests | MEDIUM | S (1-2hr) | Testing | Boundary bugs in signal gen |
| 21 | Unused lightweight-charts | LOW | XS (5min) | Bundle size | +150KB wasted |
| 22 | Unused alertStore | LOW | XS (5min) | Dead code | Code clutter |

**Effort**: XS = <30 min, S = 1-2 hours, M = 2-4 hours, L = 4+ hours

---

## Recommended Implementation Order

### Sprint 10 — Performance, Robustness, Mobile (Items 1-13)

**Theme**: Fix data accuracy, backend holes, and mobile experience.

| # | Item | Effort |
|---|------|--------|
| 1 | Portfolio live price lookup | M |
| 2 | AI Q&A ORM migration + .NS fix | S |
| 3 | History page Load More | S |
| 4 | MarketOverview mobile layout | S |
| 5 | useSignals params stabilization | XS |
| 10 | Remove duplicate indicator pills | XS |
| 12 | Fix missing useEffect deps | XS |
| 21 | Remove unused lightweight-charts | XS |
| 22 | Remove unused alertStore | XS |
| 7 | Health endpoint metrics | S |
| 9 | Signal detail responsive chart | S |
| 11 | Backtest validation + cleanup | S |
| 6 | CostTracker Redis migration | M |

**Rationale**: Start with quick wins (items 5, 10, 12, 21, 22 — under 30 min each), then fix the HIGH priority items (1, 2, 3, 4), then MEDIUM items.

**Estimated effort**: 14-18 hours

---

### Sprint 11 — Accessibility, Testing, Polish (Items 14-20)

**Theme**: Harden test coverage, fix accessibility, and polish UX details.

| # | Item | Effort |
|---|------|--------|
| 15 | API endpoint test suite | L |
| 14 | Signal detail a11y fixes | M |
| 18 | Server-side signal filtering | M |
| 13 | Frontend Sentry integration | M |
| 8 | Dynamic SEO metadata | S |
| 19 | Portfolio input validation | S |
| 16 | formatPrice locale fix | S |
| 17 | WinRateCard API envelope | S |
| 20 | Cooldown edge case tests | S |

**Rationale**: API tests (item 15) first — they establish a safety net for all subsequent changes. Then accessibility (item 14) and server-side filtering (item 18). Polish items last.

**Estimated effort**: 15-20 hours

---

## Dependencies

```
Item 1 (portfolio live price) depends on market_data having data for position symbols
Item 2 (AI Q&A ORM) is standalone
Item 3 (history Load More) is standalone
Item 5 (useSignals fix) should be done before Item 18 (server-side filtering)
Item 15 (API tests) should be done before Items 17, 18 (they change API behavior)
Item 17 (stats envelope) should coordinate frontend + backend in same PR
```

---

## Out of Scope for v4

These are valuable but deferred:
- **Authentication / multi-user**: Still a personal tool — full auth adds significant complexity.
- **PWA support**: Service worker for offline access — not critical for MVP.
- **Export to CSV**: History/portfolio export — nice-to-have for analysis.
- **Custom indicator weights**: Over-engineering for MVP.
- **WebSocket reconnection backoff**: Current fixed 3s interval with 10 max retries is adequate.
- **Database indexing optimization**: Current indexes are sufficient for single-user scale.
- **Internationalization (i18n)**: English-only is correct for current user.
- **Dark/light theme toggle**: Dark terminal theme is the permanent choice.

---

## Review Checkpoint

Before implementation begins, confirm:

1. **Item 1**: Check current portfolio summary response — does it include per-position data with `last_price`? Verify by calling `GET /api/v1/portfolio/summary?telegram_chat_id=1`.
2. **Item 5**: Verify `useSignals()` is only called without params currently. If params are always undefined, the fix is precautionary but still important.
3. **Item 15**: Verify `conftest.py` has fixtures for test database, test client, and sample data seeding.
4. **Item 21**: Run `grep -r "lightweight-charts" frontend/src/` to confirm zero usage before removing.
5. **Item 22**: Run `grep -r "alertStore" frontend/src/` to confirm zero imports before removing.

---

*Last updated: 21 March 2026 | SignalFlow AI v4 Sprint Plan*
