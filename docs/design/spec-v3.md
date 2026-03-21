# SignalFlow AI — Sprint 7+ Improvement Spec (v3)

> **Date**: 21 March 2026  
> **Author**: Brainstorm Agent  
> **Status**: Draft — Ready for review  
> **Previous**: [spec-v2.md](spec-v2.md) (10 items, sprints 5-6 completed)

---

## Context

Six sprints of improvements have been completed:

| Sprint | Items Shipped |
|--------|---------------|
| 1 | User store (chatId), WebSocket status dot, sort controls, target progress bar, expiry countdown, accessibility |
| 2 | Rate limiting (slowapi), WebSocket server pings, enhanced health endpoint, AskAI error handling, font optimization |
| 3 | Sentiment badge on card, ErrorBoundary improvements, WinRateCard error/retry state, market data error tracking |
| 4 | Keyboard shortcuts (1/2/3/4, /, ?, Esc), auto-refresh countdown, enhanced sparkline with target/stop-loss lines |
| 5 | History JOIN with signals table, .NS symbol fix in generator, pagination total count, live price change on cards |
| 6 | History page filters, market heatmap, Load More pagination |

**Remaining from spec-v2** (not yet done):
- #5: Symbol track record per symbol (backend endpoint + frontend in expanded card)
- #6: Accuracy trend chart (backend weekly stats endpoint + Recharts AreaChart)
- #8: Portfolio P&L chart (visual breakdown)
- #10: Signal detail page (dedicated route /signal/[id])

**Newly discovered issues** during codebase exploration:
- Signal resolution broken for Indian stocks (`.NS` suffix mismatch in `signal_tasks.py`)
- `TargetProgressBar` never receives `livePrice` despite `SignalCard` computing it
- Portfolio summary uses last trade price instead of live market price
- History page lacks market type filter (only outcome filter implemented)
- No signal/[id] route exists despite backend `GET /signals/{signal_id}` being ready

---

## 12 Improvements — Ranked by User Impact

### 1. Signal Resolution .NS Suffix Bug (Priority: CRITICAL)

**Problem**: Signal resolution in `signal_tasks.py` queries `MarketData.symbol == signal.symbol` where `signal.symbol` is `"RELIANCE.NS"` but `market_data` stores `"RELIANCE"` (the Indian stock fetcher strips `.NS` before storing). This means **stock signals can never resolve** — they'll never hit target or stop-loss, all will expire after 7 days.

Sprint 5 fixed the `.NS` issue in the signal *generator* (stripping `.NS` when querying market data), but the same pattern was not applied to the signal *resolution* task.

**Files to modify**:
- `backend/app/tasks/signal_tasks.py` — Normalize symbol in `_resolve_signals_async`

**Changes**:
1. In `_resolve_signals_async`, when querying for the latest price, normalize the symbol:
   ```python
   query_symbol = signal.symbol.replace(".NS", "")
   price_stmt = (
       select(MarketData.close)
       .where(MarketData.symbol == query_symbol)
       .order_by(MarketData.timestamp.desc())
       .limit(1)
   )
   ```

**User impact**: Without this fix, the entire signal history for Indian stocks is fiction — everything expires, nothing hits target or stop. This pollutes win rate stats and destroys the user's trust in the system. **This is a data integrity bug.**

---

### 2. Pass Live Price to TargetProgressBar (Priority: HIGH)

**Problem**: `SignalCard` computes `livePrice` from the market store and displays it as a price arrow (`₹1,678.90 → ₹1,695.40`), but never passes it to `TargetProgressBar`. The progress bar dot still shows the *signal creation* price, not the current live price. The user sees two conflicting stories: the text says "→ ₹1,695.40" but the dot hasn't moved.

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx` — Pass `livePrice` prop

**Changes**:
1. Change line 125:
   ```tsx
   // Before
   <TargetProgressBar signal={signal} />
   // After
   <TargetProgressBar signal={signal} livePrice={livePrice ?? undefined} />
   ```

**User impact**: The progress bar becomes a live indicator. The user watches the dot move toward target or stop-loss in real-time — this is the most intuitive "how is my signal doing?" visualization.

---

### 3. Symbol Track Record (Priority: HIGH) — *Spec-v2 #5 carryover*

**Problem**: Signal cards exist in isolation. When the user sees a BUY signal for HDFCBANK, she has no context: "How did previous HDFCBANK signals perform?" This is vital for building trust and pattern recognition.

**Files to modify**:
- `backend/app/api/history.py` — New endpoint `GET /api/v1/signals/{symbol}/track-record`
- `backend/app/schemas/signal.py` — New `SymbolTrackRecord` schema
- `frontend/src/lib/api.ts` — New API method
- `frontend/src/lib/types.ts` — New type
- `frontend/src/components/signals/SignalCard.tsx` — Display track record in expanded section

**Changes**:
1. **Backend**: New endpoint returning per-symbol stats:
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
   Query: JOIN `signal_history` with `signals` table, filter by symbol and last 30 days, GROUP BY outcome.

2. **Frontend**: Fetch track record lazily when card is expanded. Display as one-liner:
   ```
   📊 HDFCBANK track record (30d): 2/3 hit target (66.7%)
   ```
   Green if win_rate >= 60%, yellow if 40-60%, red if <40%.

**User impact**: "This symbol's signals are usually reliable" vs "mixed results — I'll be cautious." Builds pattern recognition and trust.

---

### 4. Accuracy Trend Chart (Priority: HIGH) — *Spec-v2 #6 carryover*

**Problem**: `WinRateCard` shows aggregate stats but no trend. The user can't see if signal quality is improving or declining. For a finance professional, trend is everything.

**Files to modify**:
- `backend/app/api/history.py` — New endpoint `GET /api/v1/signals/stats/trend`
- `frontend/src/components/signals/AccuracyChart.tsx` — New component
- `frontend/src/app/page.tsx` — Add to sidebar
- `frontend/src/lib/api.ts` — New API method
- `frontend/src/lib/types.ts` — New type

**Changes**:
1. **Backend**: Weekly win rate buckets:
   ```json
   {
     "data": [
       { "week": "2026-W10", "start_date": "2026-03-02", "total": 8, "hit_target": 5, "win_rate": 62.5 },
       { "week": "2026-W11", "start_date": "2026-03-09", "total": 12, "hit_target": 9, "win_rate": 75.0 }
     ]
   }
   ```
   Query: `GROUP BY date_trunc('week', resolved_at)`, filter last N weeks.

2. **Frontend**: Recharts `<AreaChart>` with:
   - X-axis: weeks, Y-axis: win rate (0-100%)
   - Area fill: green gradient
   - Reference line at 50% (break-even)
   - Tooltip showing exact numbers
   - Placed below `WinRateCard` in sidebar

**User impact**: The #1 trust builder. An upward trend = "signals are getting better." A decline = "be more cautious." Either way, it's transparency.

---

### 5. Signal Detail Page (Priority: HIGH) — *Spec-v2 #10 carryover*

**Problem**: There's no dedicated page for a single signal. Signals expand inline with limited space. The backend `GET /api/v1/signals/{signal_id}` endpoint exists (and works), and the API client has `getSignal(id)`, but there's no frontend route.

The `/shared/[id]` page exists but is designed for external sharing (minimal info, no interactivity). There is no `/signal/[id]` route.

**Files to modify**:
- `frontend/src/app/signal/[id]/page.tsx` — New signal detail page
- `frontend/src/components/signals/SignalCard.tsx` — Add "View Details →" link
- `frontend/src/lib/types.ts` — Existing types are sufficient

**Changes**:
1. **New route** `/signal/[id]` with full-page signal view:
   - Large confidence gauge + signal badge at top
   - Full-width sparkline or Recharts line chart with target/stop-loss lines
   - All technical indicators in a detailed grid (not compressed pills)
   - Full AI reasoning text (no truncation)
   - Full-width target progress bar
   - Risk calculator
   - Symbol track record (item #3)
   - Share button
   - Back link to dashboard

2. **SignalCard**: Add subtle "View details →" link in expanded section, navigating to `/signal/{id}`.

3. **Metadata**: Dynamic `<title>` and OpenGraph tags:
   ```
   STRONG BUY — HDFCBANK (92% confidence) | SignalFlow AI
   ```

**User impact**: Bookmarkable, shareable URL per signal. Full-screen view on mobile instead of cramped inline expansion. The signal becomes a "page" she can reference later.

---

### 6. Portfolio P&L Chart (Priority: HIGH) — *Spec-v2 #8 carryover*

**Problem**: The portfolio page shows summary cards and a position table, but no visual breakdown. A stacked bar or pie chart showing allocation and P&L per position would give instant insight.

Additionally, the portfolio summary endpoint uses `func.max(Trade.price).label("last_price")` instead of actual live market prices. This means P&L is calculated against the last *trade* price, not the current market price — which can be very stale.

**Files to modify**:
- `frontend/src/app/portfolio/page.tsx` — Add chart section
- `backend/app/api/portfolio.py` — Use live market price in summary (optional enhancement)

**Changes**:
1. **Position allocation bar**: Horizontal Recharts `<BarChart>` or pure-CSS stacked bar.
   - Each segment = one position, width proportional to allocation
   - Green for profitable, red for losing
   - Hover shows: symbol, quantity, current value, P&L, % return

2. **P&L waterfall** (alternative / additional): Vertical bars per position showing absolute P&L.
   - Sorted by P&L descending — winners on left, losers on right
   - Immediate visual of "which positions are driving my returns?"

3. **Backend enhancement** (optional): Look up live prices from `market_data` table for each position symbol, instead of using last trade price. This makes P&L accurate between trades.

**User impact**: "I'm overweight in crypto and it's dragging my returns" is visible in one glance.

---

### 7. History Page Market Type Filter (Priority: MEDIUM)

**Problem**: Sprint 6 added outcome filter pills to the history page, but there's no market type filter (Stocks/Crypto/Forex). The backend already JOINs signals (sprint 5), so `item.signal.market_type` is available. The frontend just doesn't expose a filter for it.

**Files to modify**:
- `frontend/src/app/history/page.tsx` — Add market type filter pills

**Changes**:
1. Add market filter pills identical to the SignalFeed pattern (All / Stocks / Crypto / Forex).
2. Client-side filtering using `item.signal?.market_type` — no backend change needed.
3. Display below the outcome filter pills.
4. Update the summary stats bar to reflect the active market filter.

**User impact**: "My crypto signals keep hitting stops, but stock signals are solid" — this kind of market-specific analysis is essential for refining strategy.

---

### 8. Dashboard Quick Jump to Signal Detail (Priority: MEDIUM)

**Problem**: This is a UX convenience feature that complements item #5. Currently clicking a signal card toggles expansion. There's no way to get to the full detail view except by constructing the URL manually.

Every expanded signal card should have a "View full details →" text link that goes to `/signal/{id}`. Additionally, on the history page, clicking a resolved signal row could link to its original signal detail page.

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx` — Add link in expanded area
- `frontend/src/app/history/page.tsx` — Make signal rows linkable

**Changes**:
1. In `SignalCard` expanded section, between Share button and expand indicator:
   ```tsx
   <Link href={`/signal/${signal.id}`} className="text-xs text-accent-purple hover:underline">
     View full details →
   </Link>
   ```
   With `onClick={(e) => e.stopPropagation()}` to prevent card collapse.

2. In history page, wrap the symbol name in a `<Link>` to `/signal/{item.signal_id}` so the user can trace back to the original signal.

**User impact**: Smooth navigation. Every signal is one click away from its full detail page.

---

### 9. Signal Age Warning on Stale Cards (Priority: MEDIUM)

**Problem**: Active signals can be up to 7 days old before they expire. A 5-day-old signal with no live price movement shows the same confidence and entry price as when it was created. The user might act on a stale signal thinking it's fresh.

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx` — Add age badge

**Changes**:
1. Calculate signal age: `const ageHours = (Date.now() - new Date(signal.created_at).getTime()) / 3600000;`
2. If `ageHours > 48` (2 days), show a subtle warning badge:
   ```
   ⚠️ Signal is 3 days old — check if conditions still apply
   ```
   Amber text, displayed below the target/stop row. Disappearing when `ageHours < 48`.
3. If `ageHours > 120` (5 days) and no live price change, flag as "Expiring soon — verify before acting."

**User impact**: Prevents the most common beginner mistake: acting on outdated information. This is a trust-building safeguard.

---

### 10. History Sortable Columns (Priority: MEDIUM)

**Problem**: The history page displays data in a grid with columns (Symbol, Signal, Outcome, Return, Exit Price, Resolved), but columns aren't sortable. A finance professional expects to sort by return % to see best/worst performers, or by resolved date.

**Files to modify**:
- `frontend/src/app/history/page.tsx` — Add click-to-sort on column headers

**Changes**:
1. Add state: `const [sortCol, setSortCol] = useState<'return' | 'resolved' | null>(null);`
2. Add `const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');`
3. Make column headers clickable with sort indicators (▲/▼).
4. Apply client-side sorting to the filtered list.
5. Default sort: resolved date descending (newest first, current behavior).

**User impact**: "Show me my best performers" or "Show me my worst losses" — this is standard analytical behavior for someone reviewing their trading journal.

---

### 11. Notification Badge for New Signals (Priority: LOW)

**Problem**: When new signals arrive via WebSocket while the user is on the History or Portfolio page, there's no visual indication. The navbar link to "Dashboard" looks the same whether there are 0 or 5 new signals.

**Files to modify**:
- `frontend/src/store/signalStore.ts` — Track unseen signal count
- `frontend/src/components/shared/Navbar.tsx` — Show badge
- `frontend/src/hooks/useWebSocket.ts` — Increment unseen count on new signal

**Changes**:
1. Add `unseenCount: number` to `signalStore`, incremented when WebSocket delivers a new signal and the user isn't on the dashboard.
2. Reset to 0 when Dashboard page mounts (in `useSignals` or `page.tsx`).
3. In Navbar, show a small red dot or count next to "Dashboard" when `unseenCount > 0`:
   ```
   📊 Dashboard (3)
   ```

**User impact**: The user knows there are new signals without constantly checking the dashboard. Reduces anxiety about missing signals.

---

### 12. Market Hours Indicator (Priority: LOW)

**Problem**: The user may not know whether NSE or forex markets are currently open or closed. Signals for closed markets are less actionable (she can't act until the market opens). The backend has market hour awareness in data tasks, but this information isn't surfaced to the user.

**Files to modify**:
- `frontend/src/utils/market-hours.ts` — Already exists but may need updates
- `frontend/src/components/markets/MarketOverview.tsx` — Show open/closed badge per market

**Changes**:
1. Import or create market hours logic:
   - NSE: Mon-Fri 9:15 AM – 3:30 PM IST
   - Forex: Sun 5:30 PM IST – Sat 3:30 AM IST
   - Crypto: 24/7
2. Display a small `🟢 Open` or `🔴 Closed` badge next to each market section in MarketOverview.
3. When a market is closed, show the next opening time: "Opens Mon 9:15 AM IST".

**User impact**: Prevents the confusion of "why aren't stock prices updating?" at 8 PM. Also helps her plan: "Forex opens Sunday evening — I'll check then."

---

## Priority Matrix

| # | Item | Priority | Effort | Files Changed | User Impact |
|---|------|----------|--------|---------------|-------------|
| 1 | Signal resolution .NS bug | CRITICAL | XS (30min) | 1 backend | Stock signals never resolve → broken history stats |
| 2 | Pass livePrice to TargetProgressBar | HIGH | XS (10min) | 1 frontend | Progress bar becomes live, not frozen |
| 3 | Symbol track record | HIGH | M (3-4hr) | 3 backend, 2 frontend | "How did this symbol's signals perform?" |
| 4 | Accuracy trend chart | HIGH | M (4-5hr) | 1 backend, 3 frontend | Weekly win rate trend visualization |
| 5 | Signal detail page | HIGH | M (4-5hr) | 2 frontend | Bookmarkable, full-screen signal view |
| 6 | Portfolio P&L chart | HIGH | M (3-4hr) | 1 frontend (+ opt. backend) | Visual portfolio breakdown |
| 7 | History market type filter | MEDIUM | S (1hr) | 1 frontend | Filter history by Stocks/Crypto/Forex |
| 8 | Dashboard ↔ Detail links | MEDIUM | S (1hr) | 2 frontend | Smooth navigation to signal detail pages |
| 9 | Signal age warning | MEDIUM | S (1hr) | 1 frontend | Prevents acting on stale signals |
| 10 | History sortable columns | MEDIUM | S (1-2hr) | 1 frontend | Sort by return %, date in history table |
| 11 | Notification badge | LOW | S (1-2hr) | 3 frontend | "3 new signals" badge on Dashboard nav link |
| 12 | Market hours indicator | LOW | S (1-2hr) | 2 frontend | Show open/closed status per market |

**Effort**: XS = <30 min, S = <2 hours, M = 3-5 hours

---

## Recommended Implementation Order

### Sprint 7 — Bug Fixes + Signal Intelligence (Items 1, 2, 3, 7, 9)

**Theme**: Fix data integrity issues and make signal cards smarter.

| Item | What | Effort |
|------|------|--------|
| #1 | Signal resolution .NS suffix | XS |
| #2 | Pass livePrice to TargetProgressBar | XS |
| #3 | Symbol track record endpoint + expanded card display | M |
| #7 | History page market type filter (client-side) | S |
| #9 | Signal age warning badge on stale cards | S |

**Why this order**: Items 1-2 are bug fixes that take minutes but have outsized impact on data correctness and visual accuracy. Item 3 is the highest-impact new feature remaining — it gives every signal context. Items 7 and 9 are quick wins that deepen the analytical experience.

**Estimated total**: 6-8 hours

---

### Sprint 8 — Signal Detail Page + Visualization (Items 4, 5, 6, 8)

**Theme**: Full signal detail view and data visualization.

| Item | What | Effort |
|------|------|--------|
| #5 | Signal detail page `/signal/[id]` | M |
| #8 | Dashboard ↔ Detail navigation links | S |
| #4 | Accuracy trend chart (backend endpoint + Recharts) | M |
| #6 | Portfolio P&L chart | M |

**Why this order**: The signal detail page (#5) is the foundation — #8 links to it, and #3's track record will appear inside it. The accuracy trend chart (#4) complements WinRateCard and completes the "trust dashboard." Portfolio P&L chart (#6) is the visual upgrade the portfolio page needs.

**Estimated total**: 12-15 hours

---

### Sprint 9 — Polish & Engagement (Items 10, 11, 12)

**Theme**: Analytical tools and engagement polish.

| Item | What | Effort |
|------|------|--------|
| #10 | History sortable columns | S |
| #11 | Notification badge for new signals | S |
| #12 | Market hours open/closed indicator | S |

**Why this order**: These are polish items that make the app feel complete. Sortable columns make the history page a real analysis tool. Notification badges drive engagement. Market hours prevent confusion.

**Estimated total**: 4-6 hours

---

## Dependencies

```
Item 1 (resolution fix) ──→ Item 3 (track record) needs accurate history data
Item 1 (resolution fix) ──→ Item 4 (accuracy chart) needs correct resolution outcomes
Item 5 (detail page) ──→ Item 8 (navigation links) needs the route to exist
Item 3 (track record) ──→ Item 5 (detail page) will embed track record
```

---

## Out of Scope for v3

These are valuable but deferred beyond these 3 sprints:
- **Live portfolio pricing**: Using real-time market data in portfolio summary instead of last trade price. Would require a backend service to look up market_data for each position symbol.
- **Authentication**: Still a personal tool — auth adds complexity without immediate value.
- **Push notifications (browser)**: Telegram covers alert delivery; browser push is additive.
- **Multi-user support**: Single-user design is correct for MVP.
- **Custom indicator weights**: Over-engineering — the fixed 60/40 technical/sentiment split works.
- **Dark/light theme toggle**: Dark terminal theme is the right choice.
- **Export to CSV**: Nice-to-have for history/portfolio, but not critical.

---

## Review Checkpoint

Before implementation begins, the following should be confirmed:

1. **Item #1 verification**: Run `SELECT symbol FROM signals WHERE market_type = 'stock' LIMIT 5` — if symbols have `.NS` suffix, the resolution fix is needed. If they don't, the generator has been updated and this item is moot.
2. **Recharts availability**: Already in `package.json` (`^2.13.0`) — confirmed available.
3. **Backend route ordering**: The `router.py` already places history routes before signal routes (to avoid `/signals/history` being caught by `/signals/{signal_id}`). The new `/signals/{symbol}/track-record` and `/signals/stats/trend` endpoints need the same treatment — register before the catch-all `/{signal_id}` route.
4. **No breaking changes**: All 12 items are additive. No existing API contracts change. No database migrations required (the new track-record and trend endpoints query existing tables).

---

*Last updated: 21 March 2026 | SignalFlow AI v3 Sprint Plan*
