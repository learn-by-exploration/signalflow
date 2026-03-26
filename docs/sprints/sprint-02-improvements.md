# SignalFlow AI — Sprint 5 Improvement Spec

> **Date**: 21 March 2026
> **Author**: Brainstorm Agent
> **Status**: Draft — Ready for implementation
> **Previous**: [spec.md](spec.md) (28 items, 4 sprints completed)

---

## Context

Four sprints of improvements have been completed:

| Sprint | Items Shipped |
|--------|---------------|
| 1 | User store (chatId from localStorage), WebSocket status dot, sort controls, target progress bar, expiry countdown, accessibility (aria-labels) |
| 2 | Rate limiting (slowapi), WebSocket server pings, enhanced health endpoint, AskAI error handling, font optimization (next/font) |
| 3 | Sentiment badge on card, ErrorBoundary with component name, WinRateCard error/retry state, market data error tracking |
| 4 | Keyboard shortcuts (1/2/3/4, /, ?, Esc), auto-refresh countdown, enhanced sparkline with target/stop-loss lines |

**What remains from spec v1** (not yet done):
- 2.1 Price change since signal (live price vs signal price)
- 2.5 Previous signals comparison (track record per symbol)
- 3.1 Signal accuracy trend chart (win rate over time)
- 3.3 Portfolio P&L chart
- 3.4 Market heatmap
- 4.1 Pagination total count
- 4.4 Indian stock symbol suffix mismatch
- 4.7 Signal history JOIN missing

This spec identifies the **10 highest-impact improvements** for Sprint 5, combining critical carryovers from spec v1 with newly-identified issues.

---

## TOP 10 Improvements — Ranked by User Impact

### 1. Signal History JOIN — Show Symbol and Signal Details on History Page (Priority: CRITICAL)

**Problem**: The history page is essentially broken for the user. `GET /api/v1/signals/history` returns `SignalHistoryItem` with only `signal_id` — it does NOT JOIN with the `signals` table. The frontend tries to render `item.signal?.symbol` and `item.signal?.signal_type`, which are always undefined. Every row displays "—" for symbol and signal type. The user sees a table of outcomes with no way to tell *which* signal each outcome belongs to.

This is the single most user-visible data issue in the app.

**Files to modify**:
- [backend/app/api/history.py](../../backend/app/api/history.py) — JOIN with `signals` table
- [backend/app/schemas/signal.py](../../backend/app/schemas/signal.py) — Add embedded `SignalSummary` to `SignalHistoryItem`
- [backend/app/models/signal_history.py](../../backend/app/models/signal_history.py) — Add relationship to Signal model

**Changes**:
1. Add a `SignalSummary` schema with fields: `symbol`, `market_type`, `signal_type`, `current_price`, `target_price`, `stop_loss`.
2. Add `signal: SignalSummary | None = None` to `SignalHistoryItem`.
3. In `list_signal_history`, change query to:
   ```python
   query = (
       select(SignalHistory)
       .options(joinedload(SignalHistory.signal_rel))
   )
   ```
   Or use an explicit JOIN:
   ```python
   query = select(SignalHistory, Signal).join(Signal, SignalHistory.signal_id == Signal.id)
   ```
4. Populate the `signal` field in the response from the joined data.
5. Add relationship on `SignalHistory` model: `signal_rel = relationship("Signal", lazy="joined")`.

**User impact**: Transforms the history page from unusable to fully functional. The user can finally see which symbols hit targets vs stops.

---

### 2. Live Price Change Since Signal (Priority: HIGH)

**Problem**: Signal cards show `current_price` — but this is the price **at signal creation time**, not the live price. The user has no way to tell if a BUY signal from 3 hours ago has already moved +5% (bad entry) or is still at the signal price (good entry). This is the #1 missing piece for trade decisions.

The `TargetProgressBar` component already accepts a `livePrice` prop but it's never passed — it always falls back to `signal.current_price`.

**Files to modify**:
- [frontend/src/components/signals/SignalCard.tsx](../../frontend/src/components/signals/SignalCard.tsx) — Look up live price, display change
- [frontend/src/store/marketStore.ts](../../frontend/src/store/marketStore.ts) — Add a `getPrice(symbol)` selector

**Changes**:
1. Add a selector to `marketStore`:
   ```typescript
   getPrice: (symbol: string) => {
     const state = get();
     const all = [...state.stocks, ...state.crypto, ...state.forex];
     return all.find((s) => s.symbol === symbol || shortSymbol(s.symbol) === shortSymbol(symbol));
   }
   ```
2. In `SignalCard`, look up the live market price:
   ```typescript
   const liveSnapshot = useMarketStore((s) => s.getPrice(signal.symbol));
   const livePrice = liveSnapshot ? parseFloat(liveSnapshot.price) : null;
   const signalPrice = parseFloat(signal.current_price);
   const priceChange = livePrice ? ((livePrice - signalPrice) / signalPrice) * 100 : null;
   ```
3. Display next to the signal price:
   ```
   ₹1,678.90 → ₹1,695.40 (+0.98%)
   ```
   Green if favorable (BUY signal + price still near/below entry), red if unfavorable.
4. Pass `livePrice` to `TargetProgressBar` so the progress dot reflects current position.
5. Handle symbol normalization (stock symbols stored without `.NS` in market data, but signals may have it — see item #3).

**User impact**: Enables the most critical trading decision: "Is this entry price still available?"

---

### 3. Indian Stock Symbol Suffix Mismatch (Priority: HIGH)

**Problem**: `IndianStockFetcher` strips the `.NS` suffix before storing to `market_data` (`symbol=symbol.replace(".NS", "")`). But `SignalGenerator` queries with the full `.NS` suffix from `tracked_stocks` config (`RELIANCE.NS`). The `_fetch_market_data` method uses `MarketData.symbol == symbol` where `symbol` = `"RELIANCE.NS"` but stored value = `"RELIANCE"`. **This means stock signals can never be generated** because the data query returns empty.

Additionally, on the frontend, `shortSymbol()` in formatters strips `.NS` for display, and the `getPrice()` lookup in item #2 will also fail if symbols don't match between signals and market data.

**Files to modify**:
- [backend/app/services/data_ingestion/indian_stocks.py](../../backend/app/services/data_ingestion/indian_stocks.py) — Stop stripping suffix
- [backend/app/services/signal_gen/generator.py](../../backend/app/services/signal_gen/generator.py) — Normalize symbol when querying
- [frontend/src/utils/formatters.ts](../../frontend/src/utils/formatters.ts) — Ensure `shortSymbol` handles both formats

**Changes** (Option A — store full suffix, recommended for consistency):
1. In `indian_stocks.py`, remove `.replace(".NS", "")` — store as `RELIANCE.NS`.
2. In `fetch_symbol`, also keep the `.NS` suffix.
3. Frontend `shortSymbol()` already strips `.NS` for display — no change needed.
4. Verify the WebSocket `market_update` messages also use the `.NS` form so live price lookup works.
5. Write a one-time data migration to update existing `market_data` rows: `UPDATE market_data SET symbol = symbol || '.NS' WHERE market_type = 'stock' AND symbol NOT LIKE '%.NS'`.

**Changes** (Option B — strip everywhere):
1. In `generator.py`'s `_fetch_market_data`, strip `.NS` before querying: `query_symbol = symbol.replace('.NS', '')`.
2. When creating the `Signal` object, also strip `.NS` from the stored symbol.
3. Less clean — requires stripping in every component that touches stock symbols.

**User impact**: Unblocks the entire Indian stock signal pipeline. Without this fix, 15 of 31 tracked symbols (almost half) never generate signals.

---

### 4. Pagination Total Count (Priority: HIGH)

**Problem**: Both `GET /api/v1/signals` and `GET /api/v1/signals/history` return `meta.count` as `len(results)` — the number of items in the current page, not the total. The frontend can't build pagination controls ("Page 1 of 5") or show "Showing 1-20 of 87 signals" because it doesn't know the total.

Currently the signal feed loads up to 20 signals and stops — the user has no idea more exist and no way to navigate to them.

**Files to modify**:
- [backend/app/schemas/signal.py](../../backend/app/schemas/signal.py) — Add `total` to `MetaResponse`
- [backend/app/api/signals.py](../../backend/app/api/signals.py) — Add COUNT query
- [backend/app/api/history.py](../../backend/app/api/history.py) — Add COUNT query
- [frontend/src/components/signals/SignalFeed.tsx](../../frontend/src/components/signals/SignalFeed.tsx) — Add pagination controls
- [frontend/src/app/history/page.tsx](../../frontend/src/app/history/page.tsx) — Add pagination controls

**Changes**:
1. Add `total: int | None = None` to `MetaResponse`.
2. In both `list_signals` and `list_signal_history`, before the paginated query, run:
   ```python
   count_query = select(func.count()).select_from(base_query.subquery())
   total = (await db.execute(count_query)).scalar()
   ```
3. Return `meta: { timestamp, count: len(results), total: total }`.
4. Frontend: Add a simple "Load More" button or page number controls. Show "Showing 1-20 of {total}".
5. Pass `offset` and `limit` query params from frontend when user navigates pages.

**User impact**: Users can see and access all their signals, not just the latest 20.

---

### 5. Previous Signals Track Record Per Symbol (Priority: HIGH)

**Problem**: Signal cards exist in isolation. When the user sees a BUY signal for HDFCBANK, she has no idea how previous HDFCBANK signals performed. "This symbol had 3 signals this month — 2 hit target." This context is vital for trust and decision-making.

**Files to modify**:
- [backend/app/api/signals.py](../../backend/app/api/signals.py) — Add `include_history` query param OR create a new endpoint
- [backend/app/schemas/signal.py](../../backend/app/schemas/signal.py) — Add `SymbolTrackRecord` schema
- [frontend/src/components/signals/SignalCard.tsx](../../frontend/src/components/signals/SignalCard.tsx) — Display track record in expanded section

**Changes**:
1. **Backend approach A** (separate endpoint — preferred for caching):
   New endpoint `GET /api/v1/signals/{symbol}/track-record` that returns:
   ```json
   {
     "data": {
       "symbol": "HDFCBANK.NS",
       "total_signals_30d": 3,
       "hit_target": 2,
       "hit_stop": 1,
       "expired": 0,
       "win_rate": 66.7,
       "avg_return_pct": 2.3
     }
   }
   ```
   Query: `SELECT outcome, COUNT(*), AVG(return_pct) FROM signal_history sh JOIN signals s ON sh.signal_id = s.id WHERE s.symbol = :sym AND sh.created_at > NOW() - INTERVAL '30 days' GROUP BY outcome`.

2. **Backend approach B** (embed in signals list):
   Add `include_history=true` param to `list_signals`. For each signal, include `recent_track_record` subobject. Downside: N+1 queries unless batched.

3. **Frontend**: In the expanded `SignalCard` section, show a one-liner:
   ```
   📊 HDFCBANK track record (30d): 2/3 hit target (66.7%)
   ```
   Green if win_rate >= 60%, yellow if 40-60%, red if <40%.
4. Fetch lazily — only when the card is expanded, via a `useEffect` triggered by `isExpanded`.

**User impact**: Builds pattern recognition and trust. "This symbol's signals are usually reliable" vs "mixed results — I'll be cautious."

---

### 6. Signal Accuracy Trend Chart (Priority: HIGH)

**Problem**: `WinRateCard` shows aggregate stats (win rate, avg return, total signals) but no trend. The user can't see if signal quality is improving, stable, or declining. For a finance professional, trend is everything — a 65% win rate means nothing without knowing if it was 80% last month and falling.

**Files to modify**:
- [backend/app/api/history.py](../../backend/app/api/history.py) — New `/signals/stats/trend` endpoint
- New file: `frontend/src/components/signals/AccuracyChart.tsx`
- [frontend/src/app/page.tsx](../../frontend/src/app/page.tsx) — Add below WinRateCard
- [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts) — Add API method
- [frontend/src/lib/types.ts](../../frontend/src/lib/types.ts) — Add type

**Changes**:
1. **Backend**: New endpoint `GET /api/v1/signals/stats/trend`:
   ```python
   @router.get("/stats/trend")
   async def get_signal_stats_trend(weeks: int = Query(default=12, ge=4, le=52), db=Depends(get_db)):
       """Weekly win rate buckets for the last N weeks."""
       # GROUP BY date_trunc('week', resolved_at), compute hit_target/total per week
   ```
   Response:
   ```json
   {
     "data": [
       { "week": "2026-W10", "total": 8, "hit_target": 5, "win_rate": 62.5 },
       { "week": "2026-W11", "total": 12, "hit_target": 9, "win_rate": 75.0 },
       ...
     ]
   }
   ```

2. **Frontend**: New `AccuracyChart` component using Recharts `<AreaChart>`:
   - X-axis: weeks
   - Y-axis: win rate (0-100%)
   - Area fill: gradient green-to-transparent
   - Reference line at 50% (break-even)
   - Tooltip showing exact numbers on hover
   - Height: ~180px, placed in the sidebar below `WinRateCard`

3. Add to dashboard page inside the sidebar section, wrapped in `ErrorBoundary`.

**User impact**: The #1 trust builder. Seeing an upward trend in accuracy gives the user confidence to act on signals. Seeing a decline tells her to be more cautious. Either way, it's transparency.

---

### 7. Market Heatmap — All Tracked Symbols at a Glance (Priority: MEDIUM)

**Problem**: `MarketOverview` shows only top 3 symbols per market (9 out of 31 tracked). The user has no quick way to see the overall market sentiment across all tracked assets. A finance professional expects a heatmap view — it's one of the most intuitive market visualization tools.

**Files to modify**:
- New file: `frontend/src/components/markets/MarketHeatmap.tsx`
- [frontend/src/app/page.tsx](../../frontend/src/app/page.tsx) — Add as collapsible section between MarketOverview and main content
- [frontend/src/store/marketStore.ts](../../frontend/src/store/marketStore.ts) — Ensure all symbols are available (not just top 3)

**Changes**:
1. **Component**: Grid of colored rectangles, one per tracked symbol.
   - Color: green (positive change) → red (negative change), intensity proportional to absolute % change.
   - Each cell shows: symbol name + change %.
   - Layout: 3 rows (stocks / crypto / forex), responsive wrapping.
   - Size: uniform cells, ~60×40px each.
   - Click a cell to filter the signal feed to that symbol.

2. **Data**: Uses existing `marketStore` data — no new API needed. Currently `MarketOverview` slices to top 3 per market, but the store already holds all of them.

3. **Collapsible**: Default collapsed on mobile, expanded on desktop. Toggle via a "Show all markets" / "Hide" link.

4. **No library needed**: Pure CSS grid with inline background-color. No heavyweight heatmap library.

**User impact**: "At a glance, I can see the market is mostly green today, except for 2 crypto pairs that are red." This is the kind of overview that makes a finance professional feel at home.

---

### 8. Portfolio P&L Visualization (Priority: MEDIUM)

**Problem**: The portfolio page shows trades as a flat list and a summary card with total P&L, but no visual breakdown. A user with 10 positions can't quickly see which ones are winning vs losing, or how her capital is allocated.

**Files to modify**:
- [frontend/src/app/portfolio/page.tsx](../../frontend/src/app/portfolio/page.tsx) — Add chart section
- [frontend/src/lib/types.ts](../../frontend/src/lib/types.ts) — Verify `PortfolioSummary` has position-level data

**Changes**:
1. **Position breakdown bar**: Horizontal stacked bar chart showing each position as a segment.
   - Width proportional to allocation (% of total portfolio value).
   - Color: green gradient for profitable positions, red gradient for losing ones.
   - Hover shows: symbol, quantity, current value, P&L, % return.

2. **Implementation**: Use Recharts `<BarChart>` (already in package.json as a dependency) or simple CSS `<div>` bars if positions are few (<15).

3. **Aggregate P&L header**: Already exists as summary but should be more prominent:
   ```
   +₹12,450 (+4.2%)
   ```
   Large text, green/red, at the top of the portfolio page.

4. **Backend check**: Verify the `/api/v1/portfolio/summary` endpoint returns per-position data (symbol, quantity, avg_price, current_value, pnl). If it only returns totals, extend it.

**User impact**: Turns the portfolio from a data dump into actionable insight. "I'm overweight in crypto and it's dragging my returns" is visible in one glance.

---

### 9. History Page Filtering and Outcome Breakdown (Priority: MEDIUM)

**Problem**: The history page is a simple chronological list with no filtering capability. The user can't filter by market, outcome type, or date range. She also can't see a breakdown like "25 signals: 15 hit target, 6 hit stop, 4 expired." The `outcome` query param exists on the backend but the frontend doesn't expose it.

**Files to modify**:
- [frontend/src/app/history/page.tsx](../../frontend/src/app/history/page.tsx) — Add filters and summary stats
- [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts) — Pass filter params to history API

**Changes**:
1. **Outcome filter pills**: Row of buttons at the top — "All", "🎯 Target Hit", "🛑 Stop Hit", "⏰ Expired", "⏳ Pending". Each filters the list via the existing `outcome` query param.

2. **Market filter**: Same filter pill pattern as SignalFeed — "All", "Stocks", "Crypto", "Forex". Requires either:
   - (a) Adding `market_type` filter to the history backend (via the JOIN from item #1), or
   - (b) Client-side filtering (acceptable for <100 items).

3. **Summary bar at the top**: Show outcome counts as colored chips:
   ```
   🎯 15  🛑 6  ⏰ 4  ⏳ 3  |  Win Rate: 71.4%
   ```
   This reuses logic from WinRateCard but specific to the filtered data set.

4. **Empty state per filter**: If filtering to "Target Hit" shows 0 results, display "No signals have hit their target yet" instead of the generic "No signal history."

**User impact**: Converts the history page from a passive log into an analytical tool. The user can study patterns: "Most of my crypto signals hit stop-loss, but stock signals are 80% accurate."

---

### 10. Signal Detail Page — Dedicated View Per Signal (Priority: MEDIUM)

**Problem**: There is no dedicated page for a single signal. The signal card expands inline, but:
- The URL doesn't change (no bookmarking / sharing a deep link to a specific signal).
- The expanded view has limited space — especially on mobile.
- The backend `GET /api/v1/signals/{signal_id}` endpoint exists but there's no frontend route that uses it.
- The shared signal page (`/shared/[id]`) exists for external sharing but doesn't work for an internal signal detail view.

**Files to modify**:
- New file: `frontend/src/app/signal/[id]/page.tsx` — Signal detail page
- [frontend/src/components/signals/SignalCard.tsx](../../frontend/src/components/signals/SignalCard.tsx) — Add "View Details →" link
- [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts) — Already has `getSignal(id)`

**Changes**:
1. **New route** `/signal/[id]` — Full-page signal view with:
   - Large confidence gauge and signal badge
   - Full price chart (wider sparkline or Recharts line chart)
   - All technical indicators in a detailed grid (not just pills)
   - Full AI reasoning text (not truncated)
   - Target progress bar at full width
   - Risk calculator
   - Share button
   - Previous signals for this symbol (item #5)
   - Link back to dashboard

2. **SignalCard link**: Add a small "View details →" link in the expanded section that navigates to `/signal/{id}`.

3. **Data fetching**: Use the existing `getSignal(id)` API call. Optionally fetch the symbol track record for the sidebar.

4. **SEO / Sharing**: Add proper `<title>` and OG meta tags so when the URL is shared, it shows: "STRONG BUY — HDFCBANK (92% confidence) | SignalFlow AI".

**User impact**: Gives signals a permanent, shareable URL. The user can bookmark key signals, share them with confidence, and revisit them later to see how they performed.

---

## Priority Matrix

| # | Item | Priority | Effort | Files Changed | User Impact |
|---|------|----------|--------|---------------|-------------|
| 1 | History page JOIN | CRITICAL | S (2-3hr) | 3 backend | History page goes from broken to functional |
| 2 | Live price since signal | HIGH | S (2-3hr) | 2 frontend | Core trading decision — "is entry still good?" |
| 3 | Stock symbol mismatch | HIGH | S (1-2hr) | 2 backend + migration | Unblocks 15 of 31 symbols from generating signals |
| 4 | Pagination total count | HIGH | M (3-4hr) | 2 backend, 2 frontend | Users can access all signals, not just top 20 |
| 5 | Symbol track record | HIGH | M (3-4hr) | 2 backend, 1 frontend | Trust — "this symbol's signals are usually right" |
| 6 | Accuracy trend chart | HIGH | M (4-5hr) | 1 backend, 2 frontend | #1 trust builder — performance trend over time |
| 7 | Market heatmap | MEDIUM | M (3-4hr) | 2 frontend | At-a-glance market overview, professional feel |
| 8 | Portfolio P&L chart | MEDIUM | M (3-4hr) | 1-2 frontend | Visual portfolio insight |
| 9 | History page filters | MEDIUM | S (2-3hr) | 1 frontend, 1 api | Analytical tool for studying signal patterns |
| 10 | Signal detail page | MEDIUM | M (4-5hr) | 2 frontend | Bookmarkable, shareable, full signal context |

**Effort**: S = <3 hours, M = 3-5 hours

---

## Recommended Implementation Order

**Batch A — Critical fixes + data integrity** (Items 1, 3, 4)
Fix the broken history JOIN, unblock stock signals, and add pagination total. These are bugs/gaps that prevent core functionality from working. Do these first because items 2, 5, 6 depend on having correct data.

**Batch B — Signal card intelligence** (Items 2, 5)
Add live price comparison and symbol track records. These transform signal cards from "static snapshots" into "live decision tools." Both rely on the data integrity fixes from Batch A.

**Batch C — Visualization** (Items 6, 7, 8)
Build the accuracy trend chart, market heatmap, and portfolio P&L chart. These are the visual features that make the app feel like a professional trading tool.

**Batch D — Navigation & analysis** (Items 9, 10)
Add history page filtering and the signal detail page. These deepen the analytical capability and make the app more navigable.

---

## Dependencies

```
Item 3 (symbol fix) ──→ Item 2 (live price) depends on consistent symbols
Item 1 (history JOIN) ──→ Item 5 (track record) needs history data with symbols
Item 1 (history JOIN) ──→ Item 6 (accuracy chart) needs history data
Item 1 (history JOIN) ──→ Item 9 (history filters) needs symbol/market on history items
Item 5 (track record) ──→ Item 10 (detail page) shows track record in sidebar
```

---

## Out of Scope for Sprint 5

These are valuable but lower priority than the 10 items above:
- **Authentication/authorization** — The app is a personal tool; auth adds complexity without immediate value
- **Auto-refresh push signals** — WebSocket already delivers new signals; REST polling covers the rest
- **Custom indicator creation** — Over-engineering for MVP; users should use the 6 built-in indicators
- **Notification preferences granularity** — Current config (markets, min_confidence, signal_types) is sufficient
- **Dark/light theme toggle** — Dark theme is the right choice for a trading terminal; adding light mode is pure polish
