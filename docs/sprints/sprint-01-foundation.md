# SignalFlow AI — Improvement Spec

> **Date**: 21 March 2026
> **Author**: Review Agent
> **Status**: Draft — Ready for implementation prioritization

---

## Executive Summary

SignalFlow AI has a solid foundation: functional backend pipeline (data → analysis → AI → signals), a clean dark-themed dashboard, and useful features (portfolio, backtest, alerts, AI Q&A). This spec identifies **28 concrete improvements** across 5 categories, prioritized by user impact. Each recommendation names exact files to modify and what to change.

---

## 1. Dashboard UX Polish

### 1.1 Live Connection Status Indicator (Priority: HIGH)

**Problem**: The user has no way to know if the WebSocket is connected, reconnecting, or failed. The "Updated HH:MM" timestamp in `MarketOverview` only shows last REST poll time — not real-time connection health.

**Files to modify**:
- [frontend/src/lib/websocket.ts](../../../frontend/src/lib/websocket.ts) — Expose connection state (`connected | reconnecting | disconnected`) via a callback or observable
- [frontend/src/hooks/useWebSocket.ts](../../../frontend/src/hooks/useWebSocket.ts) — Track and expose `connectionStatus` state
- [frontend/src/components/markets/MarketOverview.tsx](../../../frontend/src/components/markets/MarketOverview.tsx) — Add a colored dot next to the "Updated" timestamp: 🟢 connected, 🟡 reconnecting, 🔴 disconnected

**Changes**:
1. In `SignalWebSocket`, add an `onStatusChange` callback parameter. Call it with `'connected'` on `ws.onopen`, `'reconnecting'` in `scheduleReconnect`, `'disconnected'` when max retries exceeded.
2. In `useWebSocket`, add a `connectionStatus` state to a new Zustand store (or add to `marketStore`).
3. In `MarketOverview`, render a `<span>` with `bg-signal-buy` (connected), `bg-signal-hold` (reconnecting), or `bg-signal-sell` (disconnected) as a 6px dot beside the timestamp.

---

### 1.2 Signal Sort Controls (Priority: HIGH)

**Problem**: `SignalFeed` filters by market and search, but has no sorting. Users can't sort by confidence (most actionable first), recency, or market type. The SQL query in `signals.py` only sorts by `created_at DESC`.

**Files to modify**:
- [frontend/src/components/signals/SignalFeed.tsx](../../../frontend/src/components/signals/SignalFeed.tsx) — Add a sort dropdown: "Newest", "Highest Confidence", "Biggest Reward" (target_price gap)
- [backend/app/api/signals.py](../../../backend/app/api/signals.py) — Add `sort_by` query param supporting `created_at`, `confidence`, `target_price` columns

**Changes**:
1. Add a `sortBy` state (`'newest' | 'confidence' | 'reward'`) with a `<select>` dropdown styled like the filter pills.
2. In the `filtered` useMemo, chain a `.sort()` after filtering. For `confidence`: sort descending by `signal.confidence`. For `reward`: sort by `(target - current) / current` descending.
3. Backend: Add `sort_by` and `sort_dir` query params to `list_signals`. Map to SQLAlchemy `.order_by()`.

---

### 1.3 Data Freshness / Stale Data Warning (Priority: MEDIUM)

**Problem**: `useMarketData` and `useSignals` poll every 30 seconds but fail silently. If the API is down or data is stale (>5 min old), the user sees no indication. The `lastUpdated` in `MarketOverview` shows the timestamp but doesn't warn when old.

**Files to modify**:
- [frontend/src/components/markets/MarketOverview.tsx](../../../frontend/src/components/markets/MarketOverview.tsx) — Color the "Updated" timestamp red if >5 minutes old, add tooltip "Data may be stale"
- [frontend/src/hooks/useMarketData.ts](../../../frontend/src/hooks/useMarketData.ts) — Track consecutive fetch failures; store `fetchFailures` count in `marketStore`

**Changes**:
1. In `MarketOverview`, compute `isStale = lastUpdated && (Date.now() - new Date(lastUpdated).getTime()) > 5 * 60 * 1000`. If stale, render timestamp with `text-signal-sell` and append " (stale)".
2. In `useMarketData`, increment a failure counter in the store on catch. Reset on success. If failures ≥ 3, show a subtle banner: "Having trouble reaching the server. Data shown may not be current."

---

### 1.4 Keyboard Shortcuts (Priority: LOW)

**Problem**: Power users (especially finance professionals who use Bloomberg terminals) expect keyboard navigation. There are none currently.

**Files to modify**:
- [frontend/src/app/page.tsx](../../../frontend/src/app/page.tsx) — Add a `useEffect` with `keydown` listener for global shortcuts
- New file: `frontend/src/hooks/useKeyboardShortcuts.ts`

**Changes**:
1. Create `useKeyboardShortcuts` hook with bindings:
   - `1/2/3/4` — Switch filter to All/Stocks/Crypto/Forex
   - `/` — Focus search input
   - `?` — Show shortcuts help modal
   - `Escape` — Close any expanded card or modal
2. Use `document.addEventListener('keydown', ...)` with proper cleanup. Only activate when no input is focused (check `document.activeElement?.tagName`).

---

### 1.5 Auto-Refresh Countdown (Priority: LOW)

**Problem**: The 30-second polling in `useSignals` and `useMarketData` is invisible. The user doesn't know when the next refresh will happen.

**Files to modify**:
- [frontend/src/components/markets/MarketOverview.tsx](../../../frontend/src/components/markets/MarketOverview.tsx) — Add a subtle countdown or circular progress near the "Updated" stamp

**Changes**:
1. Store `lastFetchTime` in `marketStore`. In `MarketOverview`, compute seconds since last fetch. Render a small text like "refreshing in 12s" or a thin animated progress bar (30s cycle) using CSS `@keyframes`.

---

## 2. Signal Card Enhancements

### 2.1 Price Change Since Signal (Priority: HIGH)

**Problem**: Signal cards show `current_price` from when the signal was created, but the user doesn't know how the price has moved SINCE then. This is critical — she needs to know if a BUY signal's price has already run up 5% or if she still has a good entry.

**Files to modify**:
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Show live price and % change from signal price
- [frontend/src/store/marketStore.ts](../../../frontend/src/store/marketStore.ts) — Add a `getPrice(symbol)` selector

**Changes**:
1. In `SignalCard`, look up the current market price from `marketStore` using the signal's symbol. Compute `changePct = ((livePrice - signalPrice) / signalPrice) * 100`.
2. Display next to the signal price: `₹1,678.90 → ₹1,695.40 (+0.98%)` with green/red coloring.
3. This makes it immediately clear whether the entry is still favorable. For a BUY signal that's already up 8% from signal price, she might skip it.

---

### 2.2 Signal Age / Expiry Countdown (Priority: HIGH)

**Problem**: Signals have `expires_at` but this isn't shown on the card. The `timeframe` field shows "2-4 weeks" generically, but not how much time is LEFT.

**Files to modify**:
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Add time remaining display

**Changes**:
1. Compute `timeRemaining = signal.expires_at ? new Date(signal.expires_at).getTime() - Date.now() : null`.
2. Display as "Expires in 5d 14h" below the timeframe. Color it `text-signal-hold` when <24 hours remaining, `text-signal-sell` when <6 hours.
3. Add a utility function `formatTimeRemaining(ms: number): string` in `formatters.ts`.

---

### 2.3 Target Progress Bar (Priority: HIGH)

**Problem**: Users see target and stop-loss prices but can't instantly visualize how close the current price is to either. This is THE most important at-a-glance metric for an active signal.

**Files to modify**:
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Add a horizontal progress bar between stop-loss and target

**Changes**:
1. For BUY signals: bar goes from `stop_loss` (left/red) to `target_price` (right/green), with current price as a marker dot on the bar.
2. Compute `progress = (livePrice - stopLoss) / (target - stopLoss) * 100`, clamped 0-100.
3. Render as a `<div>` with a green left portion and red right portion, with a white dot at the current position. Width: full card width. Height: 4px. Include labels at each end.

---

### 2.4 Sentiment Badge on Card (Priority: MEDIUM)

**Problem**: `sentiment_data` is stored on each signal but only visible in the expanded AI reasoning text. A quick glance should show bullish/bearish/neutral sentiment.

**Files to modify**:
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Add a sentiment pill next to indicator pills

**Changes**:
1. Extract `signal.sentiment_data?.market_impact` (positive/negative/neutral) and `signal.sentiment_data?.sentiment_score`.
2. Add a new `IndicatorPill` with label "Sentiment" and value like "Bullish (78)". Color: green for positive, red for negative, yellow for neutral.
3. Only show if `sentiment_data` is not null and not a fallback.

---

### 2.5 Previous Signals Comparison (Priority: MEDIUM)

**Problem**: Signal cards exist in isolation. The user can't see if the same symbol had a signal recently and what happened to it. Pattern: "HDFCBANK got 3 BUY signals this month, 2 hit target."

**Files to modify**:
- [backend/app/api/signals.py](../../../backend/app/api/signals.py) — Add optional `include_history=true` param that embeds recent history for the same symbol
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Show "Previous: 2 of 3 signals hit target" when expanded

**Changes**:
1. Backend: When `include_history=true`, for each signal, query `signal_history` for same symbol, last 30 days. Attach as `recent_history: { total, hit_target, hit_stop, expired }` to response.
2. Frontend: In expanded section, show a one-liner like "📊 Recent track record: 2/3 hit target for this symbol" with green/red coloring based on success rate.

---

## 3. Data Visualization

### 3.1 Signal Accuracy Over Time Chart (Priority: HIGH)

**Problem**: `WinRateCard` shows aggregate stats but no trend. The user can't see if signal quality is improving or declining over time.

**Files to modify**:
- New component: `frontend/src/components/signals/AccuracyChart.tsx`
- [frontend/src/app/page.tsx](../../../frontend/src/app/page.tsx) — Add to sidebar below WinRateCard
- [backend/app/api/history.py](../../../backend/app/api/history.py) — Add `/signals/stats/trend` endpoint

**Changes**:
1. Backend: New endpoint `GET /api/v1/signals/stats/trend` returning weekly buckets: `[{ week: "2026-W12", total: 8, hit_target: 5, win_rate: 62.5 }, ...]` for last 12 weeks.
2. Frontend: Use Recharts `<AreaChart>` showing win rate over time with a green-to-red gradient. Simple, 200px tall. Tooltip shows exact numbers on hover.
3. This builds trust — the user can see tracking effectiveness over time.

---

### 3.2 Mini Price Chart on Signal Card (Priority: MEDIUM)

**Problem**: `Sparkline` currently shows the last few `recent_closes` from `technical_data`, but it's tiny (50×18px) and unlabeled. It doesn't show where target/stop-loss fall on the chart.

**Files to modify**:
- [frontend/src/components/markets/Sparkline.tsx](../../../frontend/src/components/markets/Sparkline.tsx) — Enhance with target/stop-loss reference lines
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Show larger chart (full width) when expanded

**Changes**:
1. Add optional `target` and `stopLoss` props to `Sparkline`. When provided, draw horizontal dashed lines at those price levels using `<line>` SVG elements.
2. In expanded card view, render sparkline at full card width (100% × 60px) with target/stop-loss lines. This gives visual context for where the price is heading relative to the signal levels.

---

### 3.3 Portfolio P&L Chart (Priority: MEDIUM)

**Problem**: Portfolio page shows positions as a list but has no visual P&L breakdown. A simple pie or bar chart showing allocation and performance per position would be very valuable.

**Files to modify**:
- [frontend/src/app/portfolio/page.tsx](../../../frontend/src/app/portfolio/page.tsx) — Add a positions breakdown visualization

**Changes**:
1. Add a horizontal stacked bar chart showing portfolio allocation by position (% of total value). Color each bar by P&L (green if positive, red if negative).
2. Use Recharts `<BarChart>` or simple CSS `<div>` bars — no heavy library needed for this.
3. Show aggregate P&L prominently: "+₹12,450 (+4.2%)" in large green text at the top.

---

### 3.4 Market Heatmap (Priority: LOW)

**Problem**: `MarketOverview` shows only top 3 symbols per market. A heatmap of all tracked symbols (15 stocks, 10 crypto, 6 forex) would give a quick market pulse.

**Files to modify**:
- New component: `frontend/src/components/markets/MarketHeatmap.tsx`
- [frontend/src/app/page.tsx](../../../frontend/src/app/page.tsx) — Add as an expandable section

**Changes**:
1. Grid of small rectangles, one per tracked symbol. Size: proportional to absolute change. Color: green for positive, red for negative. Intensity proportional to magnitude.
2. Clicking a cell could filter the signal feed to that symbol.
3. Data source: existing `marketStore` data, no new API needed.

---

## 4. Backend Robustness

### 4.1 Missing Total Count for Pagination (Priority: HIGH)

**Problem**: `list_signals` in `signals.py` returns `count: len(signals)` which is the count of items IN THIS PAGE, not the total. The frontend can't build proper pagination without knowing the total.

**Files to modify**:
- [backend/app/api/signals.py](../../../backend/app/api/signals.py) — Add a `SELECT COUNT(*)` before the paginated query
- [backend/app/schemas/signal.py](../../../backend/app/schemas/signal.py) — Add `total` field to `MetaResponse`

**Changes**:
1. Before the paginated query, run the same base query with `select(func.count(Signal.id))` to get `total_count`.
2. Return `meta: { timestamp, count: len(signals), total: total_count }`.
3. Frontend can then show "Showing 1-20 of 47 signals" and build page controls.

---

### 4.2 API Rate Limiting (Priority: HIGH)

**Problem**: No rate limiting on any endpoint. The AI Q&A endpoint (`POST /api/v1/ai/ask`) calls Claude API per request — a user or bot could spam it and exhaust the $30/month budget in minutes.

**Files to modify**:
- [backend/app/main.py](../../../backend/app/main.py) — Add rate limiting middleware
- [backend/app/api/ai_qa.py](../../../backend/app/api/ai_qa.py) — Add per-endpoint rate limit

**Changes**:
1. Install `slowapi` or implement a simple Redis-based rate limiter.
2. Global limit: 60 requests/minute per IP.
3. AI endpoints (`/ai/ask`): 5 requests/minute per IP. This protects the Claude budget.
4. Add `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers to responses.

---

### 4.3 Health Endpoint Missing Key Metrics (Priority: MEDIUM)

**Problem**: `/health` returns uptime and environment but nothing actionable. It doesn't report database connectivity, Redis status, last data fetch time, or active signal count — all things mentioned in the CLAUDE.md spec.

**Files to modify**:
- [backend/app/main.py](../../../backend/app/main.py) — Enhance `health_check` endpoint

**Changes**:
1. Add a quick `SELECT 1` to verify database connectivity. Wrap in try/except, return `db_status: "ok" | "error"`.
2. Add Redis ping check: `redis_status: "ok" | "error"`.
3. Query `SELECT COUNT(*) FROM signals WHERE is_active = true` → `active_signals_count`.
4. Query `SELECT MAX(timestamp) FROM market_data` → `last_data_fetch`.
5. Read AI cost tracker → `ai_budget_remaining_pct`.

---

### 4.4 Indian Stock Fetcher Stores Symbol Without .NS Suffix (Priority: MEDIUM)

**Problem**: In `indian_stocks.py`, `symbol=symbol.replace(".NS", "")` strips the suffix before storing. But `SignalGenerator` queries with the full `.NS` suffix from `tracked_stocks`. The `_fetch_market_data` method in `generator.py` uses `MarketData.symbol == symbol` where symbol is `"RELIANCE.NS"` but the stored value is `"RELIANCE"`. This means **stock signals can never be generated** because the data join fails.

**Files to modify**:
- [backend/app/services/data_ingestion/indian_stocks.py](../../../backend/app/services/data_ingestion/indian_stocks.py) — Either keep the `.NS` suffix or strip it AND also strip in the generator query

**Changes**:
1. **Option A (recommended)**: Store the full symbol including `.NS` suffix. Remove the `.replace(".NS", "")` call. Update `shortSymbol()` frontend formatter to handle display.
2. **Option B**: In `SignalGenerator._fetch_market_data`, strip `.NS` before querying: `symbol_clean = symbol.replace('.NS', '')`.
3. Verify by checking if `market_data` table actually has rows with `RELIANCE` or `RELIANCE.NS`.

---

### 4.5 Missing Request Validation on AI Q&A (Priority: MEDIUM)

**Problem**: The `ask_about_symbol` endpoint in `ai_qa.py` uses raw SQL via `text()` with parameter binding (safe from injection), but doesn't validate question length beyond the schema's maxLength. The Claude API call has a 30s timeout but no retry logic, and errors return a raw exception to the client.

**Files to modify**:
- [backend/app/api/ai_qa.py](../../../backend/app/api/ai_qa.py) — Add proper error response handling

**Changes**:
1. Wrap the Claude API call in a structured try/except that returns `{"data": {"answer": "...", "source": "error"}}` instead of letting the 500 propagate.
2. Add a `question` length check at the endpoint level: reject if >500 chars with 422.
3. The raw SQL `text()` usage should be migrated to ORM queries for consistency (use `select(MarketData).where(...)` instead of `text("SELECT close, high...")`).

---

### 4.6 WebSocket Missing Heartbeat From Server (Priority: MEDIUM)

**Problem**: The CLAUDE.md spec says the server should send `{"type": "ping"}` every 30 seconds. The `ConnectionManager` in `websocket.py` has no ping/heartbeat mechanism. The client's `startPingHandler` is a no-op. Long-idle connections will silently die without the client knowing.

**Files to modify**:
- [backend/app/api/websocket.py](../../../backend/app/api/websocket.py) — Add periodic server-side pings

**Changes**:
1. In the `websocket_signals` handler, spawn an `asyncio.create_task` that sends `{"type": "ping"}` every 30 seconds.
2. Track last pong time. If no pong received within 90 seconds, disconnect the client.
3. This keeps connections alive across proxies/load balancers and detects zombie connections.

---

### 4.7 Signal History Endpoint Missing Symbol/Signal Data (Priority: MEDIUM)

**Problem**: `GET /signals/history` returns `SignalHistoryItem` which has `signal_id` but doesn't JOIN to get the actual signal's symbol, signal_type, or prices. The frontend history page tries to access `item.signal?.symbol` but this is always undefined because the API doesn't return it.

**Files to modify**:
- [backend/app/api/history.py](../../../backend/app/api/history.py) — JOIN with `signals` table
- [backend/app/schemas/signal.py](../../../backend/app/schemas/signal.py) — Embed signal summary in `SignalHistoryItem`

**Changes**:
1. Change the query to `select(SignalHistory).join(Signal, SignalHistory.signal_id == Signal.id)`.
2. Add `signal: SignalSummary | None` to `SignalHistoryItem` schema where `SignalSummary` has `symbol, market_type, signal_type, current_price, target_price, stop_loss`.
3. Populate from the JOIN result.

---

## 5. Frontend Code Quality

### 5.1 Hardcoded CHAT_ID = 1 (Priority: CRITICAL)

**Problem**: Both `alerts/page.tsx` and `portfolio/page.tsx` use `const CHAT_ID = 1` as a placeholder. This means ALL users share the same portfolio and alert config. This is a fundamental multi-user bug.

**Files to modify**:
- [frontend/src/app/alerts/page.tsx](../../../frontend/src/app/alerts/page.tsx) — Replace hardcoded CHAT_ID
- [frontend/src/app/portfolio/page.tsx](../../../frontend/src/app/portfolio/page.tsx) — Replace hardcoded CHAT_ID
- New: `frontend/src/store/userStore.ts` — Simple store to hold user identity

**Changes**:
1. For MVP without auth: Use `localStorage` to generate and persist a unique user identifier. Create a `userStore` with `chatId: number` initialized from localStorage.
2. On first visit, prompt the user to enter their Telegram chat ID (they get this from the Telegram bot). Store it in localStorage.
3. Replace all `CHAT_ID = 1` references with `userStore.getState().chatId`.

---

### 5.2 Missing Error States in AskAI Component (Priority: HIGH)

**Problem**: The `AskAI` component catches errors silently and just shows "Failed to get a response." It doesn't distinguish between network errors, rate limiting, budget exhaustion, or malformed input.

**Files to modify**:
- [frontend/src/components/signals/AskAI.tsx](../../../frontend/src/components/signals/AskAI.tsx) — Add differentiated error messages

**Changes**:
1. Check error response status: 429 → "Slow down — too many questions. Try again in a minute."
2. Check if answer contains "budget exhausted" → "AI budget used up this month. Try again next month."
3. Add a character count display under the question input showing `${question.length}/500`.

---

### 5.3 Missing aria-labels and Focus Management (Priority: HIGH)

**Problem**: Multiple interactive elements lack accessible labels:
- Filter buttons in `SignalFeed` have no `aria-label`
- The expand/collapse chevron `▼` on `SignalCard` has no accessible name
- The mobile hamburger in `Navbar` has `aria-label` (good) but the nav links don't have `aria-current="page"` for active state
- `ConfidenceGauge` SVG has `role="img"` and `aria-label` (good)
- Toast notifications aren't announced to screen readers

**Files to modify**:
- [frontend/src/components/signals/SignalFeed.tsx](../../../frontend/src/components/signals/SignalFeed.tsx) — Add `aria-label` to filter buttons, `aria-pressed` for active state
- [frontend/src/components/signals/SignalCard.tsx](../../../frontend/src/components/signals/SignalCard.tsx) — Add `role="button"`, `aria-expanded`, proper heading hierarchy
- [frontend/src/components/shared/Navbar.tsx](../../../frontend/src/components/shared/Navbar.tsx) — Add `aria-current="page"` to active link
- [frontend/src/components/shared/Toast.tsx](../../../frontend/src/components/shared/Toast.tsx) — Add `role="alert"` and `aria-live="polite"` to toast container

**Changes**:
1. SignalCard: Add `role="button"` and `aria-expanded={isExpanded}` to the outer `div`. Add `tabIndex={0}` and `onKeyDown` handler for Enter/Space.
2. SignalFeed filters: Add `aria-label={`Filter by ${opt.label}`}` and `aria-pressed={filter === opt.value}`.
3. Navbar: Add `aria-current={isActive ? 'page' : undefined}` to nav links.
4. Toast: Add `role="alert"` to each toast div. Add `aria-live="polite"` to the toast container.

---

### 5.4 ErrorBoundary Missing Error Reporting (Priority: MEDIUM)

**Problem**: `ErrorBoundary` catches render errors and shows "Something went wrong" + a "Try again" button, but: (a) it doesn't log the error anywhere, (b) it doesn't show the component name that failed, (c) the "Try again" resets state but the same error will likely recur.

**Files to modify**:
- [frontend/src/components/shared/ErrorBoundary.tsx](../../../frontend/src/components/shared/ErrorBoundary.tsx)

**Changes**:
1. Add `componentDidCatch(error: Error, errorInfo: React.ErrorInfo)` to log to console and optionally to Sentry: `console.error('ErrorBoundary caught:', error, errorInfo.componentStack)`.
2. Show a more descriptive message: "This section had a problem loading. Click to retry or refresh the page."
3. Add a `name` prop so the error message can say "Market Overview had a problem loading."

---

### 5.5 useMarketData Silently Swallows Errors (Priority: MEDIUM)

**Problem**: In `useMarketData`, the catch block does `setLoading(false)` but doesn't report the error. Over 3+ consecutive failures, the user sees data getting progressively staler with no feedback.

**Files to modify**:
- [frontend/src/hooks/useMarketData.ts](../../../frontend/src/hooks/useMarketData.ts)
- [frontend/src/store/marketStore.ts](../../../frontend/src/store/marketStore.ts) — Add `error: string | null` and `setError` action

**Changes**:
1. Add `error` and `setError` to `marketStore`.
2. In the catch block: `setError('Failed to load market data')`.
3. In `MarketOverview`, show a subtle inline error when `error` is set: "⚠️ Market data temporarily unavailable" instead of showing stale data without warning.

---

### 5.6 Missing `<head>` Font Loading (Priority: LOW)

**Problem**: Fonts are loaded via `@import url(...)` in `globals.css`. This is a render-blocking CSS import. Next.js provides `next/font` for optimized font loading.

**Files to modify**:
- [frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx) — Use `next/font/google`
- [frontend/src/app/globals.css](../../../frontend/src/app/globals.css) — Remove the `@import url(...)` line

**Changes**:
1. In `layout.tsx`:
   ```tsx
   import { Outfit, JetBrains_Mono } from 'next/font/google';
   const outfit = Outfit({ subsets: ['latin'], variable: '--font-display' });
   const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });
   ```
2. Apply to `<body className={`${outfit.variable} ${jetbrains.variable} ...`}>`.
3. Remove the `@import url(...)` from `globals.css`.
4. This eliminates the FOUT (flash of unstyled text) and improves Lighthouse performance.

---

### 5.7 No Loading State for WinRateCard Fetch Failure (Priority: LOW)

**Problem**: If `api.getSignalStats()` fails, `WinRateCard` falls through to the "No resolved signals yet" state, which is misleading — it's not that there are no signals, it's that the fetch failed.

**Files to modify**:
- [frontend/src/components/signals/WinRateCard.tsx](../../../frontend/src/components/signals/WinRateCard.tsx)

**Changes**:
1. Track `error: string | null` alongside `stats` and `isLoading`.
2. When fetch fails, show: "⚠️ Couldn't load stats" with a "Retry" button instead of the misleading "No resolved signals" text.

---

## Priority Matrix

| # | Item | Priority | Effort | User Impact |
|---|------|----------|--------|-------------|
| 5.1 | Hardcoded CHAT_ID | CRITICAL | S | Blocks multi-user usage |
| 2.1 | Price change since signal | HIGH | S | Core trading decision data |
| 2.3 | Target progress bar | HIGH | S | At-a-glance signal health |
| 2.2 | Signal age / expiry countdown | HIGH | S | Time-sensitive decision |
| 4.1 | Pagination total count | HIGH | S | Frontend can't paginate |
| 4.2 | API rate limiting | HIGH | M | Protects AI budget |
| 4.4 | Stock symbol suffix mismatch | HIGH | S | Stock signals may never generate |
| 4.7 | History endpoint missing JOIN | HIGH | S | History page is broken-looking |
| 1.1 | Connection status indicator | HIGH | S | Real-time trust feedback |
| 1.2 | Sort controls | HIGH | S | Signal discoverability |
| 5.3 | Accessibility (aria labels) | HIGH | M | Inclusive design |
| 5.2 | AskAI error differentiation | HIGH | S | User understanding |
| 3.1 | Accuracy trend chart | HIGH | M | Trust through transparency |
| 4.6 | WebSocket server-side ping | MEDIUM | S | Connection reliability |
| 4.3 | Health endpoint metrics | MEDIUM | S | Monitoring capability |
| 4.5 | AI Q&A error handling | MEDIUM | S | API robustness |
| 2.4 | Sentiment badge | MEDIUM | S | Quick info glance |
| 2.5 | Previous signals comparison | MEDIUM | M | Pattern learning |
| 1.3 | Stale data warning | MEDIUM | S | Data trust |
| 3.2 | Enhanced sparkline with targets | MEDIUM | S | Visual context |
| 3.3 | Portfolio P&L chart | MEDIUM | M | Portfolio visualization |
| 5.4 | ErrorBoundary reporting | MEDIUM | S | Debuggability |
| 5.5 | Market data error tracking | MEDIUM | S | Transparency |
| 5.6 | Next.js font loading | LOW | S | Performance |
| 5.7 | WinRateCard error state | LOW | S | UX accuracy |
| 1.4 | Keyboard shortcuts | LOW | M | Power user feature |
| 1.5 | Auto-refresh countdown | LOW | S | Polish |
| 3.4 | Market heatmap | LOW | L | Visual appeal |

**Effort**: S = <2 hours, M = 2-6 hours, L = >6 hours

---

## Implementation Order (Recommended)

**Sprint 1 — Critical fixes + High-impact quick wins** (Items: 5.1, 4.4, 4.7, 4.1, 2.1, 2.2, 2.3, 1.1)
Fix the CHAT_ID bug, symbol mismatch, broken history join, and missing pagination. Then add the three signal card enhancements that give the user the most trading confidence.

**Sprint 2 — Backend hardening + UX** (Items: 4.2, 4.6, 4.3, 1.2, 5.3, 5.2, 1.3)
Add rate limiting to protect the AI budget, fix WebSocket pings, enhance health checks. Add sort controls and accessibility improvements.

**Sprint 3 — Visualization + Polish** (Items: 3.1, 3.2, 3.3, 2.4, 2.5, 4.5, 5.4, 5.5, 5.6, 5.7)
Build the accuracy trend chart, enhance sparklines, add portfolio visualization. Clean up remaining error handling and font loading.

**Sprint 4 — Nice-to-haves** (Items: 1.4, 1.5, 3.4)
Keyboard shortcuts, refresh countdown, market heatmap.

---

## Review Checkpoint

Before implementation begins:
- [ ] Confirm the stock symbol suffix issue (4.4) by checking actual `market_data` table rows
- [ ] Decide on user identity approach (5.1) — localStorage vs. URL param vs. simple auth
- [ ] Verify history JOIN (4.7) — check if `SignalHistory` model has a relationship to `Signal`
- [ ] Choose charting approach for 3.1 — Recharts (already in package.json?) or lightweight custom SVG
