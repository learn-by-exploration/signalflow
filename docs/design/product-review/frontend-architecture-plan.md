# Frontend Architecture Implementation Plan

> **Author**: Architect 1 — Frontend Architecture Specialist
> **Date**: 25 March 2026
> **Input**: `docs/design/product-review/ui-ux-review-v2.md` + full codebase analysis
> **Status**: Ready for implementation

---

## Plan Overview

This plan addresses 5 architectural areas identified in the UI/UX review. Each area is broken into discrete tasks with dependency ordering, file-level specifics, and risk assessment.

**Execution order**: The 5 areas have inter-dependencies. The recommended sequence is:

```
Phase A: Design System Gaps (foundation — everything depends on this)
    ↓
Phase B: Component Restructuring (signal detail page)
    ↓
Phase C: State Management Migration (React Query)
    ↓
Phase D: Navigation Architecture (nav restructuring)
    ↓
Phase E: Settings Consolidation (merge scattered settings)
```

Phases B and C can be parallelized. Phase D and E can be parallelized after B completes.

---

## Phase A: Design System Gaps

**Goal**: Establish the missing CSS tokens, utility classes, and shared primitives that all subsequent phases depend on.

**Complexity**: M (Medium)

### Current State

- **Tailwind config** (`frontend/tailwind.config.ts`): 6 color groups (bg, text, accent, signal, border) but no semantic aliases (e.g., `success`, `danger`, `warning`)
- **globals.css** (`frontend/src/app/globals.css`): 8 CSS variables, light theme overrides, 5 animations. No focus-visible system, no touch-target utility, no font-size floor enforcement
- **No shared component primitives**: No `CollapsibleSection`, no standard `Button` component, no `TouchTarget` wrapper

### Tasks

#### A1. Add semantic color tokens to Tailwind config
**File**: `frontend/tailwind.config.ts`
**Change**: Add aliases under `colors.semantic`:
```
semantic: {
  success: 'var(--signal-buy)',     // maps to signal-buy
  danger: 'var(--signal-sell)',     // maps to signal-sell
  warning: 'var(--signal-hold)',   // maps to signal-hold
  info: 'var(--accent-purple)',    // maps to accent-purple
}
```
**Why**: Color-only indicators fail for colorblind users. Semantic names also improve code readability — `text-semantic-danger` is clearer than `text-signal-sell` in non-signal contexts (error states, destructive buttons).

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### A2. Add focus-visible system
**Files**:
- `frontend/src/app/globals.css` — Add base focus-visible styles
- `frontend/tailwind.config.ts` — Add `focusRing` utility plugin (optional)

**Change**: Add to globals.css:
```css
/* Focus-visible system — replaces all focus:outline-none */
:focus-visible {
  outline: 2px solid var(--accent-purple);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove default focus for mouse users, keep for keyboard */
:focus:not(:focus-visible) {
  outline: none;
}
```

**Follow-up**: Grep all `focus:outline-none` occurrences across components and remove them. Components that currently use `focus:outline-none focus:ring-*` should keep only the ring portion.

**Files to grep-and-fix** (estimated 15+ occurrences):
- `frontend/src/components/shared/ChatIdPrompt.tsx`
- `frontend/src/components/shared/SettingsPanel.tsx`
- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/alerts/page.tsx`
- `frontend/src/components/alerts/AlertConfig.tsx`
- `frontend/src/components/signals/RiskCalculator.tsx`
- `frontend/src/components/signals/AskAI.tsx`
- All `<input>` and `<button>` elements across the app

**Complexity**: S | **Risk**: Low (visual-only) | **Breaking**: No

---

#### A3. Add 44px touch-target utility
**File**: `frontend/src/app/globals.css`

**Change**: Add utility class:
```css
/* Minimum 44x44px touch target (WCAG 2.1 AAA) */
.touch-target {
  position: relative;
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* For small icons that need larger clickable area */
.touch-target-expand::after {
  content: '';
  position: absolute;
  inset: -8px;
}
```

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### A4. Enforce 12px font-size floor
**Files to modify**:
- `frontend/src/app/globals.css` — Add floor rule
- All files using `text-[10px]`, `text-[9px]` — Replace with `text-xs` (12px)

**Change in globals.css**:
```css
/* Font size floor — override Tailwind's smallest sizes */
.text-floor { font-size: max(0.75rem, 12px); }
```

**Files requiring `text-[10px]` → `text-xs` replacement** (25+ occurrences found in audit):
- `frontend/src/components/shared/SettingsPanel.tsx` (2 instances)
- `frontend/src/components/shared/ChatIdPrompt.tsx` (1 instance)
- `frontend/src/components/signals/ConfidenceBreakdown.tsx` (2 instances)
- `frontend/src/components/signals/ConfidenceGauge.tsx` (center text)
- `frontend/src/app/signal/[id]/page.tsx` (8+ instances: chart labels, metadata, sources, disclaimer)
- `frontend/src/components/signals/SignalCard.tsx` (close prices, metadata)
- `frontend/src/components/signals/EventTimeline.tsx`
- `frontend/src/components/markets/MarketOverview.tsx` (market labels)
- `frontend/src/app/settings/page.tsx` (disclaimer)
- `frontend/src/components/shared/Navbar.tsx` (badge `text-[9px]`)

**Complexity**: M (many files, mechanical change) | **Risk**: Low | **Breaking**: No (visual-only)

---

#### A5. Create shared `CollapsibleSection` component
**File to create**: `frontend/src/components/shared/CollapsibleSection.tsx`

**Interface**:
```typescript
interface CollapsibleSectionProps {
  title: string;
  icon?: string;           // emoji or ReactNode
  defaultOpen?: boolean;
  badge?: string;          // e.g., "3 articles"
  children: React.ReactNode;
}
```

**Behavior**:
- Animated expand/collapse (CSS transition on max-height or grid-rows trick)
- Chevron rotation indicator
- Stores open/closed state per section key in localStorage (optional)
- ARIA: `aria-expanded`, proper button semantics

**Why**: Needed by Phase B (signal detail restructuring) — multiple sections need collapse behavior. Currently no reusable pattern exists.

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### A6. Create shared `StickyHeader` component
**File to create**: `frontend/src/components/shared/StickyHeader.tsx`

**Interface**:
```typescript
interface StickyHeaderProps {
  children: React.ReactNode;
  offset?: number;   // top offset in px (default: 48 for navbar height)
  className?: string;
}
```

**Why**: Signal detail page and settings page both benefit from sticky section headers, especially on mobile where scroll distance is long.

**Complexity**: S | **Risk**: Low (z-index conflicts possible with Navbar z-50) | **Breaking**: No

---

### Phase A Dependency Graph

```
A1 (colors) ──┐
A2 (focus)  ──┤── All independent, can be done in parallel
A3 (touch)  ──┤
A4 (fonts)  ──┘
A5 (CollapsibleSection) ─── depends on nothing, but Phase B depends on this
A6 (StickyHeader)       ─── depends on nothing, but Phase B depends on this
```

---

## Phase B: Component Restructuring (Signal Detail Page)

**Goal**: Reduce signal detail page from 11-14 sections / ~3,500px scroll to 5 visible sections + 3 collapsed / ~1,200px scroll.

**Complexity**: L (Large)

### Current State (`frontend/src/app/signal/[id]/page.tsx`)

The page is a **single 500-line monolithic component** that renders 11 sections in this order:
1. Back link
2. Header (ConfidenceGauge + symbol + SignalBadge)
3. Earnings proximity warning (conditional)
4. **ConfidenceBreakdown** ← REDUNDANT (data shown in header gauge)
5. Price + Target + Stop-Loss + TargetProgressBar
6. Price chart (CandlestickChart or Sparkline)
7. Technical Indicators (5-card grid)
8. AI Reasoning + Sentiment details + News sources
9. News Context (conditional, up to 10 items)
10. **RiskCalculator** ← Always expanded
11. **PipCalculator** ← Always expanded (forex only)
12. **TrailingStopSuggestion** ← Always expanded
13. Track Record
14. Actions (back link + ShareButton)
15. Disclaimer

**Problems**: 
- ConfidenceBreakdown (section 4) is redundant with header gauge
- Price/Target (section 5) is the actual decision point but buried below redundancy
- Trading tools (10-12) always expanded but mostly unused on first visit
- Data fetching uses raw `useEffect` + `useState`, not React Query

### Tasks

#### B1. Delete `ConfidenceBreakdown` component (or repurpose as tooltip)
**Files**:
- `frontend/src/components/signals/ConfidenceBreakdown.tsx` — Keep file, but make it a tooltip/popover variant
- `frontend/src/app/signal/[id]/page.tsx` — Remove the ConfidenceBreakdown section (lines ~157-170)

**Change**: Remove the standalone section. Add a click/hover handler on the ConfidenceGauge that shows the breakdown data in a popover or tooltip.

**Alternative (simpler)**: Just delete the section. The gauge already shows the composite score. The breakdown formula (`Technical × 60% + Sentiment × 40%`) can be added as a subtitle under the gauge.

**Complexity**: S | **Risk**: Low | **Breaking**: No (information is presented differently, not removed)

---

#### B2. Reorder sections — Price+Targets to position 2
**File**: `frontend/src/app/signal/[id]/page.tsx`

**New section order**:
```
1. Header (gauge + symbol + badge)           ← KEEP
2. Price + Target + Stop-Loss + Progress     ← MOVE UP from position 5
3. Price Chart                               ← KEEP
4. AI Reasoning + Sentiment                  ← KEEP
5. Technical Indicators                      ← KEEP
6. [Collapsed] News Context                  ← WRAP in CollapsibleSection
7. [Collapsed] Trading Tools                 ← WRAP in CollapsibleSection
   └── RiskCalculator
   └── PipCalculator (forex only)
   └── TrailingStopSuggestion
8. [Collapsed] Track Record                  ← WRAP in CollapsibleSection
9. Actions + Disclaimer                      ← KEEP
```

**Change**: This is a reordering of JSX blocks within the same file. The ConfidenceBreakdown section (current position 4) is removed per B1. The Price+Target section moves from ~line 170 to immediately after the header (~line 140).

**Complexity**: M | **Risk**: Low (JSX reorder, no logic changes) | **Breaking**: No

---

#### B3. Wrap sections 6-8 in `CollapsibleSection`
**File**: `frontend/src/app/signal/[id]/page.tsx`
**Depends on**: A5 (CollapsibleSection component)

**Change**: Import `CollapsibleSection` and wrap:
- News Context → `<CollapsibleSection title="News Context" icon="📰" badge={`${newsContext.length} articles`} defaultOpen={false}>`
- Trading Tools → `<CollapsibleSection title="Trading Tools" icon="🧮" defaultOpen={false}>` containing RiskCalculator, PipCalculator, TrailingStopSuggestion
- Track Record → `<CollapsibleSection title="Track Record" icon="📊" defaultOpen={false}>`

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### B4. Add section group headers
**File**: `frontend/src/app/signal/[id]/page.tsx`

**Change**: Add semantic dividers:
- After chart: `<SectionDivider label="Context & History" />` before News + Trading Tools
- The divider is a simple `<div>` with muted text and a horizontal rule. No new component needed — can be inline JSX or a tiny helper.

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### B5. Mobile: collapse Technical Indicators, show only top 2
**File**: `frontend/src/app/signal/[id]/page.tsx`

**Change**: On screens < 640px, show only the 2 most relevant indicators (determined by signal strength or pre-ranked: RSI + MACD), with a "Show all indicators" toggle.

**Implementation**: Use a state variable `showAllIndicators` defaulting to `false` on mobile (detect via `window.innerWidth` or a Tailwind `sm:` media query approach). Show full grid on desktop always.

**Complexity**: S | **Risk**: Low | **Breaking**: No

---

#### B6. Migrate signal detail page to React Query
**File**: `frontend/src/app/signal/[id]/page.tsx`
**Depends on**: Phase C progress (but can be done independently since `useSignalQuery` already exists in `useQueries.ts`)

**Current**: Raw `useEffect` + `useState` + `api.getSignal()` + `api.getSymbolTrackRecord()`
**Target**: Use `useSignalQuery(id)` from `frontend/src/hooks/useQueries.ts`

**Change**:
1. Replace the manual `useEffect`/`useState` pattern (lines 35-60) with `useSignalQuery(signalId)`
2. Add a new `useTrackRecordQuery(symbol)` hook in `useQueries.ts` for the track record fetch
3. Remove local `loading`/`error`/`signal` state — use React Query's `isLoading`/`error`/`data`
4. Add retry button using React Query's `refetch()`

**Complexity**: M | **Risk**: Medium (behavioral change: React Query's caching + retry vs manual fetch) | **Breaking**: No

---

### Phase B Summary

| Task | Depends On | Complexity | Files Modified | Files Created |
|------|-----------|------------|----------------|---------------|
| B1 | None | S | signal/[id]/page.tsx, ConfidenceBreakdown.tsx | — |
| B2 | B1 | M | signal/[id]/page.tsx | — |
| B3 | A5, B2 | S | signal/[id]/page.tsx | — |
| B4 | B2 | S | signal/[id]/page.tsx | — |
| B5 | B2 | S | signal/[id]/page.tsx | — |
| B6 | None (uses existing useSignalQuery) | M | signal/[id]/page.tsx, useQueries.ts | — |

**Execution order**: B1 → B2 → (B3, B4, B5 in parallel) → B6

---

## Phase C: State Management Migration (React Query)

**Goal**: Complete the migration from legacy polling hooks (`useSignals`, `useMarketData`) + Zustand stores (`signalStore`, `marketStore`) to React Query, eliminating dual data fetching.

**Complexity**: XL (Extra Large — touches every data-consuming component)

### Current State

**Two parallel data-fetching systems coexist:**

| System | Files | Used By |
|--------|-------|---------|
| Legacy polling | `useSignals.ts` (30s interval), `useMarketData.ts` (30s interval) | `DashboardContent.tsx` (production) |
| React Query | `useQueries.ts` (60s refetchInterval) | **No production consumers** — only tests |

**State flow (legacy)**:
```
useSignals() → api.getSignals() → signalStore.setSignals()
useMarketData() → api.getMarketOverview() → marketStore.setMarkets()
useWebSocket() → signalStore.addSignal() / marketStore.updatePrice()
```

**Problem**: WebSocket and REST polling can both update the same store, causing potential duplicate signals and unnecessary API calls.

### Migration Strategy

The migration must be done **consumer-by-consumer** to avoid a big-bang rewrite. Each step replaces one legacy consumer with its React Query equivalent.

### Tasks

#### C1. Add missing React Query hooks
**File**: `frontend/src/hooks/useQueries.ts`

**Add**:
```typescript
// Track record for a symbol
export function useTrackRecordQuery(symbol: string) {
  return useQuery({
    queryKey: ['track-record', symbol],
    queryFn: () => api.getSymbolTrackRecord(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  });
}

// Alert config
export function useAlertConfigQuery(chatId: number) {
  return useQuery({
    queryKey: ['alert-config', chatId],
    queryFn: () => api.getAlertConfig(chatId),
    enabled: !!chatId,
  });
}

// Portfolio
export function usePortfolioQuery(chatId: number) {
  return useQuery({
    queryKey: ['portfolio', chatId],
    queryFn: () => api.getPortfolioSummary(chatId),
    enabled: !!chatId,
    staleTime: 60_000,
  });
}
```

**Complexity**: S | **Risk**: None | **Breaking**: No

---

#### C2. Migrate DashboardContent to React Query
**File**: `frontend/src/components/dashboard/DashboardContent.tsx`
**Depends on**: C1

**Current** (lines 9-23):
```typescript
import { useSignals } from '@/hooks/useSignals';
import { useMarketData } from '@/hooks/useMarketData';
// ...
const { signals, isLoading, error } = useSignalStore();
useSignals();
useMarketData();
```

**Target**:
```typescript
import { useSignalsQuery, useMarketOverviewQuery } from '@/hooks/useQueries';
// ...
const { data: signalsData, isLoading, error, refetch } = useSignalsQuery();
const { data: marketData } = useMarketOverviewQuery();
```

**Key decisions**:
1. **signalStore still needed** for WebSocket-pushed signals and `unseenCount`. React Query handles REST fetching; the store handles WS-pushed additions.
2. **marketStore still needed** for WS price updates. React Query handles initial market load; WS updates flow through the store.
3. **Remove the 30s polling intervals** from legacy hooks. React Query's `refetchInterval: 60_000` replaces them.

**Migration path**:
- Replace `useSignals()` call with `useSignalsQuery()`
- Replace `useMarketData()` call with `useMarketOverviewQuery()`
- Read `signals` from React Query `data` instead of Zustand `signalStore`
- Keep `signalStore` only for `addSignal()` (WebSocket) and `unseenCount`
- Keep `marketStore` for `updatePrice()` (WebSocket) and `wsStatus`

**Complexity**: L | **Risk**: High (this is the central data flow; bugs here affect the entire dashboard) | **Breaking**: Behavioral (polling interval changes from 30s to 60s)

---

#### C3. Reconcile WebSocket + React Query
**File**: `frontend/src/hooks/useWebSocket.ts`
**Depends on**: C2

**Problem**: WebSocket pushes signals via `signalStore.addSignal()`, but if the dashboard reads from React Query's cache, WS-pushed signals won't appear until the next refetchInterval.

**Solution**: When WebSocket receives a new signal, also invalidate the React Query cache:
```typescript
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './useQueries';

// Inside handleMessage:
if (msg.type === 'signal') {
  queryClient.invalidateQueries({ queryKey: queryKeys.signals });
}
if (msg.type === 'market_update') {
  queryClient.invalidateQueries({ queryKey: queryKeys.marketOverview });
}
```

**Alternative (lower risk)**: Keep `signalStore` as the single source of truth for the signal list. React Query fetches and writes into signalStore via `onSuccess`. WebSocket also writes into signalStore. Components read from signalStore only. This avoids the reconciliation problem entirely but keeps Zustand as the state layer.

**Recommended approach**: The alternative (Zustand as source of truth, React Query as fetcher) is lower risk for MVP. Full React Query-only migration can happen later.

**Complexity**: M | **Risk**: High | **Breaking**: Potential (duplicate/missing signals if reconciliation fails)

---

#### C4. Migrate Signal History page
**File**: `frontend/src/app/history/page.tsx`
**Depends on**: C1

**Current**: Likely uses raw `useEffect` + `api.getSignalHistory()`
**Target**: Use `useSignalHistoryQuery(params)` from `useQueries.ts`

**Complexity**: S | **Risk**: Low | **Breaking**: No

---

#### C5. Migrate Track Record page
**File**: `frontend/src/app/track-record/page.tsx`
**Depends on**: C1

**Current**: Likely uses raw `useEffect` + `api.getSignalStats()` + `api.getAccuracyTrend()`
**Target**: Use `useSignalStatsQuery()` and `useAccuracyTrendQuery()` from `useQueries.ts`

**Complexity**: S | **Risk**: Low | **Breaking**: No

---

#### C6. Migrate Watchlist page
**File**: `frontend/src/app/watchlist/page.tsx`
**Depends on**: C1

**Target**: Use `useWatchlistQuery(chatId)` and `useWatchlistMutation(chatId)` from `useQueries.ts`

**Complexity**: S | **Risk**: Low | **Breaking**: No

---

#### C7. Deprecate legacy hooks
**Files**:
- `frontend/src/hooks/useSignals.ts` — Mark deprecated, then delete after all consumers migrated
- `frontend/src/hooks/useMarketData.ts` — Mark deprecated, then delete after all consumers migrated

**When**: Only after C2-C6 are complete and all consumers are verified.

**Complexity**: S | **Risk**: Medium (must verify zero remaining imports) | **Breaking**: Yes (deletes files)

---

#### C8. Slim down Zustand stores
**Files**:
- `frontend/src/store/signalStore.ts` — Remove `setSignals`, `setLoading`, `setError`, `appendSignals` (these become React Query's job). Keep `addSignal`, `unseenCount`, `resetUnseen`.
- `frontend/src/store/marketStore.ts` — Remove `setMarkets`, `setLoading`, `setFetchError`. Keep `updatePrice`, `wsStatus`.

**When**: Only after C7 (legacy hooks deleted).

**Complexity**: M | **Risk**: Medium (must update all store consumers) | **Breaking**: Yes (API surface changes)

---

### Phase C Dependency Graph

```
C1 (add hooks) ──┬── C4 (history page)
                  ├── C5 (track record page)
                  ├── C6 (watchlist page)
                  └── C2 (dashboard) ── C3 (WS reconciliation)
                                              │
                                              ▼
                                    C7 (deprecate legacy hooks)
                                              │
                                              ▼
                                    C8 (slim stores)
```

### Phase C Risk Mitigation

1. **Feature flag**: Add `NEXT_PUBLIC_USE_REACT_QUERY=true` env var. Wrap new hooks in a feature check so legacy can be re-enabled instantly.
2. **Test each page independently**: After migrating each page, verify data loads correctly, pagination works, and WebSocket updates still appear.
3. **Keep signalStore as source of truth** (recommended approach from C3) until full migration is proven stable.

---

## Phase D: Navigation Architecture

**Goal**: Restructure navigation from flat 12-item list (4 primary + 8 in "More" dropdown) to 3 semantic groups. Fix mobile drawer. Reduce 7 competing modals.

**Complexity**: L (Large)

### Current State (`frontend/src/components/shared/Navbar.tsx`)

- **Desktop**: 4 `PRIMARY_LINKS` + "More" dropdown with 8 `MORE_LINKS` + settings icon + user avatar
- **Mobile**: Hamburger opens flat list of all 12 links (no grouping, no icons, no section headers)
- **7 modals/overlays** compete for attention: WelcomeModal, ChatIdPrompt, GuidedTour, KeyboardHelpModal, SettingsPanel, AlertConfigModal, UpgradePrompt

### Tasks

#### D1. Define navigation groups data structure
**File**: `frontend/src/components/shared/Navbar.tsx`

**Change**: Replace `PRIMARY_LINKS` / `MORE_LINKS` with grouped structure:
```typescript
const NAV_GROUPS = [
  {
    label: 'Markets',
    icon: '📊',
    links: [
      { href: '/', label: 'Dashboard', icon: '📈' },
      { href: '/news', label: 'News', icon: '📰' },
      { href: '/calendar', label: 'Calendar', icon: '📅' },
    ],
  },
  {
    label: 'Analysis',
    icon: '🔍',
    links: [
      { href: '/track-record', label: 'Track Record', icon: '🏆' },
      { href: '/history', label: 'Signal History', icon: '📜' },
      { href: '/backtest', label: 'Backtest', icon: '⚡' },
      { href: '/brief', label: 'Daily Brief', icon: '☀️' },
    ],
  },
  {
    label: 'My Account',
    icon: '👤',
    links: [
      { href: '/portfolio', label: 'Portfolio', icon: '💼' },
      { href: '/alerts', label: 'Alerts', icon: '🔔' },
      { href: '/watchlist', label: 'Watchlist', icon: '👁' },
      { href: '/settings', label: 'Settings', icon: '⚙️' },
    ],
  },
];
```

**Desktop rendering**: Show top-level items from each group as flat links. Use a mega-menu or grouped dropdown instead of "More".

**Complexity**: M | **Risk**: Medium (navigation change affects all user flows) | **Breaking**: Visual change, not functional

---

#### D2. Redesign desktop navigation
**File**: `frontend/src/components/shared/Navbar.tsx`

**Design**: 
- Show 3 group labels as nav items: `Markets | Analysis | Portfolio`
- Each group label opens a dropdown with its child links (icon + label)
- Keep Dashboard as a direct link (always visible, no dropdown needed)
- Settings icon remains in the right corner

**Alternative (simpler)**: Keep 5-6 top-level links visible (Dashboard, News, Track Record, Portfolio, Alerts) and put the rest in a single "More" dropdown grouped with section headers.

**Recommended**: The simpler alternative — fewer behavioral changes, lower risk.

**Complexity**: M | **Risk**: Medium | **Breaking**: Visual

---

#### D3. Redesign mobile drawer with groups
**File**: `frontend/src/components/shared/Navbar.tsx`

**Current** (lines 198-221): Flat list with `.map()` over all links.

**Change**: Replace with grouped rendering:
```tsx
{NAV_GROUPS.map((group) => (
  <div key={group.label}>
    <p className="px-4 py-2 text-xs text-text-muted uppercase tracking-wider font-display">
      {group.icon} {group.label}
    </p>
    {group.links.map((link) => (
      <Link key={link.href} href={link.href} className="block px-4 py-3 ...">
        {link.icon} {link.label}
      </Link>
    ))}
  </div>
))}
```

**Touch targets**: Each link must be `py-3` minimum (≥48px height), satisfying the 44px requirement from A3.

**Complexity**: S | **Risk**: Low | **Breaking**: Visual only

---

#### D4. Consolidate modals — Remove redundant ones
**Files to modify**:
- `frontend/src/components/shared/SettingsPanel.tsx` — **DELETE** (replaced by /settings page)
- `frontend/src/components/shared/ChatIdPrompt.tsx` — **DELETE** (moved to /settings/telegram or inline on /settings)
- `frontend/src/components/shared/KeyboardHelpModal.tsx` — **KEEP** but hide on touch devices
- `frontend/src/components/shared/WelcomeModal.tsx` — **KEEP** (onboarding, good UX)
- `frontend/src/components/shared/GuidedTour.tsx` — **KEEP** (onboarding)
- `frontend/src/components/shared/UpgradePrompt.tsx` — **KEEP** (tier gating)
- `frontend/src/components/alerts/AlertConfig.tsx` — **KEEP** as a component but embed in /settings page instead of as a modal

**Impact**: Settings icon in Navbar should link to `/settings` page directly instead of opening `SettingsPanel` modal.

**Dependencies**: Phase E (Settings Consolidation) must be complete before SettingsPanel and ChatIdPrompt can be deleted.

**Complexity**: M | **Risk**: Medium (removing modals changes user flows; must ensure /settings page has all the same functionality) | **Breaking**: Yes (modal entry points disappear)

---

#### D5. Hide keyboard shortcuts on touch devices
**File**: `frontend/src/components/shared/KeyboardHelpModal.tsx`

**Change**: Detect touch device and suppress:
```typescript
const isTouchDevice = typeof window !== 'undefined' && 
  ('ontouchstart' in window || navigator.maxTouchPoints > 0);
if (isTouchDevice) return null;
```

Also suppress the keyboard shortcut trigger (`?` key) registration on touch devices in `frontend/src/hooks/useKeyboardShortcuts.ts`.

**Complexity**: S | **Risk**: None | **Breaking**: No

---

### Phase D Dependency Graph

```
D1 (data structure) ── D2 (desktop nav) ── parallel with ── D3 (mobile drawer)
                                                              │
D4 (consolidate modals) ── depends on Phase E completion
D5 (keyboard modal) ── independent
```

---

## Phase E: Settings Consolidation

**Goal**: Merge 4 scattered settings surfaces into one unified `/settings` page with sections.

**Complexity**: M (Medium)

### Current State — 4 Settings Surfaces

| Surface | Location | What It Controls |
|---------|----------|-----------------|
| **SettingsPanel** (modal) | `components/shared/SettingsPanel.tsx` | View mode, text size, theme, notifications |
| **AlertConfigModal** (modal) | `components/alerts/AlertConfig.tsx` | Markets, min confidence, signal types |
| **/settings page** | `app/settings/page.tsx` | Account, display, signals (market filter), notifications, Telegram, reset |
| **ChatIdPrompt** (popup) | `components/shared/ChatIdPrompt.tsx` | Telegram Chat ID |

**Overlap**:
- Theme/View Mode/Text Size: in SettingsPanel AND /settings page (duplicated code)
- Telegram Chat ID: in ChatIdPrompt popup AND /settings page (duplicated code)
- Notification permission: in SettingsPanel AND /settings page (duplicated code)

### Tasks

#### E1. Audit /settings page — identify missing features
**File**: `frontend/src/app/settings/page.tsx` (already read, ~280 lines)

**Current sections on /settings page**:
1. Account (sign in/out)
2. Display (theme, view mode, text size)
3. Signals (default market filter)
4. Notifications (push permission)
5. Telegram (Chat ID)
6. Reset
7. App info

**Missing from /settings page** (present in AlertConfigModal):
- Markets filter (which markets to receive alerts for)
- Minimum confidence threshold
- Signal type selection (Strong Buy, Buy, Sell, Strong Sell)
- Quiet hours configuration

**Action**: These must be added to /settings page before AlertConfigModal can be removed.

**Complexity**: S (audit only) | **Risk**: None

---

#### E2. Add Alert Preferences section to /settings page
**File**: `frontend/src/app/settings/page.tsx`

**Change**: Add a new `<section>` between "Signals" and "Notifications" that embeds the AlertConfig form fields (markets toggle, confidence slider, signal type toggle). Reuse the toggle button UI pattern already in the page.

**Data source**: The AlertConfig currently gets its data via props (`config`, `onSave`, `onClose`). The /settings page will need to fetch alert config from the API (via React Query `useAlertConfigQuery` from C1) and save changes via a mutation.

**Depends on**: C1 (useAlertConfigQuery)

**Complexity**: M | **Risk**: Low | **Breaking**: No

---

#### E3. Remove SettingsPanel modal
**Files**:
- `frontend/src/components/shared/SettingsPanel.tsx` — **DELETE**
- `frontend/src/app/layout.tsx` or wherever SettingsPanel is rendered — Remove import and usage
- `frontend/src/components/shared/Navbar.tsx` — Change settings icon to link to `/settings` instead of toggling a modal

**Depends on**: E2 (all SettingsPanel functionality must exist on /settings page first)

**Grep for imports**: Search all files for `SettingsPanel` to find every usage.

**Complexity**: S | **Risk**: Low | **Breaking**: Yes (modal ceases to exist; gear icon behavior changes)

---

#### E4. Remove ChatIdPrompt popup
**Files**:
- `frontend/src/components/shared/ChatIdPrompt.tsx` — **DELETE**
- `frontend/src/app/layout.tsx` or parent that renders ChatIdPrompt — Remove import

**Replacement**: The Telegram section on /settings page already handles Chat ID entry. For the "progressive nudge" behavior (showing on 3rd visit), add a subtle banner on the dashboard: "Connect Telegram for alerts → Settings" instead of a blocking modal.

**Depends on**: E2 (Telegram section verified on /settings page)

**Complexity**: S | **Risk**: Low (removal of a nudge modal — slight reduction in Telegram onboarding conversion, mitigated by dashboard banner) | **Breaking**: Yes

---

#### E5. Refactor AlertConfig as embeddable component (not modal)
**File**: `frontend/src/components/alerts/AlertConfig.tsx`

**Current**: `AlertConfigModal` is a full-screen modal component that takes `onClose` prop.
**Target**: Extract the form content into a standalone `AlertPreferencesForm` component that can be embedded on the /settings page OR the /alerts page. Remove the modal wrapper.

**Change**:
```typescript
// NEW: Embeddable form (no modal wrapper)
interface AlertPreferencesFormProps {
  config: AlertConfig | null;
  onSave: (data: Partial<AlertConfig>) => void;
}

export function AlertPreferencesForm({ config, onSave }: AlertPreferencesFormProps) {
  // ... same form internals, no <div className="fixed inset-0 ..."> wrapper
}

// KEEP: Modal variant for backward compat during transition
export function AlertConfigModal({ config, onSave, onClose }: AlertConfigProps) {
  return (
    <ModalWrapper onClose={onClose}>
      <AlertPreferencesForm config={config} onSave={onSave} />
    </ModalWrapper>
  );
}
```

**Complexity**: S | **Risk**: None | **Breaking**: No (additive)

---

### Phase E Dependency Graph

```
E1 (audit) → E2 (add alert prefs to settings page) → E3 (remove SettingsPanel)
                                                     → E4 (remove ChatIdPrompt)
E5 (refactor AlertConfig) → feeds into E2
```

**Full order**: E1 → E5 → E2 → (E3, E4 in parallel)

---

## Cross-Cutting Concerns

### Test Impact

| Phase | Tests Affected | Action |
|-------|---------------|--------|
| A | None (CSS/utility changes) | Add tests for CollapsibleSection |
| B | `__tests__/SignalDetailPage.test.tsx` | Update to match new section order, collapsed defaults |
| C | `__tests__/useQueries.test.ts`, `__tests__/signalStore.test.ts`, `__tests__/SignalFeed.test.tsx` | Major updates — mock React Query instead of manual fetch |
| D | `__tests__/Navbar.test.tsx` | Update for grouped nav structure, removed "More" dropdown |
| E | None found for SettingsPanel or ChatIdPrompt | Write new tests for /settings page with embedded alert prefs |

### Files to Create (New)

| File | Phase | Purpose |
|------|-------|---------|
| `frontend/src/components/shared/CollapsibleSection.tsx` | A5 | Reusable expand/collapse wrapper |
| `frontend/src/components/shared/StickyHeader.tsx` | A6 | Sticky section header |
| `frontend/src/components/alerts/AlertPreferencesForm.tsx` | E5 | Embeddable alert config form |

### Files to Delete (After Migration Complete)

| File | Phase | Condition |
|------|-------|-----------|
| `frontend/src/hooks/useSignals.ts` | C7 | All consumers migrated to React Query |
| `frontend/src/hooks/useMarketData.ts` | C7 | All consumers migrated to React Query |
| `frontend/src/components/shared/SettingsPanel.tsx` | E3 | /settings page has all features |
| `frontend/src/components/shared/ChatIdPrompt.tsx` | E4 | Telegram section in /settings works |

### Files with Heaviest Modifications

| File | Phases | Change Scope |
|------|--------|-------------|
| `frontend/src/app/signal/[id]/page.tsx` | B1-B6 | Section reorder, collapse wrappers, React Query migration |
| `frontend/src/components/shared/Navbar.tsx` | D1-D3 | Full nav restructure |
| `frontend/src/app/settings/page.tsx` | E2 | Add alert preferences section |
| `frontend/src/hooks/useQueries.ts` | C1 | Add ~5 new hooks |
| `frontend/src/components/dashboard/DashboardContent.tsx` | C2 | Replace useSignals+useMarketData with React Query |
| `frontend/src/hooks/useWebSocket.ts` | C3 | Add React Query cache invalidation |
| `frontend/src/app/globals.css` | A2-A4 | Focus system, touch targets, font floor |
| `frontend/tailwind.config.ts` | A1 | Semantic colors |

---

## Implementation Schedule

### Recommended Execution Waves

**Wave 1 — Foundation (Phase A)**: All 6 tasks in parallel. No dependencies.
- A1: Semantic colors
- A2: Focus-visible system
- A3: Touch-target utility
- A4: 12px font floor (mechanical grep-and-replace)
- A5: CollapsibleSection component
- A6: StickyHeader component

**Wave 2 — Signal Detail Restructure (Phase B)**: Sequential within phase.
- B1 → B2 → (B3 + B4 + B5 parallel) → B6

**Wave 3 — React Query + Navigation (Phases C + D in parallel)**:
- C branch: C1 → (C4 + C5 + C6 parallel) → C2 → C3 → C7 → C8
- D branch: D1 → (D2 + D3 parallel) → D5

**Wave 4 — Settings Consolidation (Phase E)**:
- E1 → E5 → E2 → (E3 + E4 parallel)
- D4 (modal consolidation) — executes after E3/E4

---

## Review Checkpoint

Before implementation begins, the following must be verified:

1. **React Query is installed and configured**: Confirm `@tanstack/react-query` is in `package.json` and `QueryProvider` wraps the app in `layout.tsx` → verified: `frontend/src/components/shared/QueryProvider.tsx` exists.

2. **No consumers of `useSignalsQuery`/`useMarketOverviewQuery` in production**: Confirmed — only test files import from `useQueries.ts`. Safe to migrate without breaking existing behavior.

3. **signalStore.unseenCount** must survive the migration: It's used by Navbar badge and DashboardContent. WebSocket updates it. This must remain in Zustand regardless of React Query migration.

4. **alertConfig API exists**: Verify `api.getAlertConfig()` and `api.updateAlertConfig()` exist in `frontend/src/lib/api.ts` before starting E2.

5. **Test suite passes**: Run `npx vitest run` before starting any changes.

---

*Plan created: 25 March 2026*
*Ready for implementation handoff*
