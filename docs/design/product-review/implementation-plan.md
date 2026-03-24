# SignalFlow AI — UI/UX Redesign Implementation Plan

> **Multi-Expert Plan** | Created: 25 March 2026
> Contributors: 2 Architects, 2 Product Managers, 2 QA Testers
> Source: [UI/UX Review v2](ui-ux-review-v2.md) (10-Agent Deep Analysis, Score 7.2/10)
> Target User: Finance professional (M.Com), beginning active trader, primarily checks signals on mobile

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Plan (Architect 1 & 2)](#2-architecture-plan)
3. [User Stories & Prioritization (PM 1)](#3-user-stories--prioritization)
4. [Feature Rollout Strategy (PM 2)](#4-feature-rollout-strategy)
5. [Sprint Plan (4 Sprints)](#5-sprint-plan)
6. [Test Strategy (Tester 1 & 2)](#6-test-strategy)
7. [Success Metrics](#7-success-metrics)
8. [Risk Assessment](#8-risk-assessment)

---

## 1. Executive Summary

### What We're Fixing

| Problem | Severity | Target Score |
|---------|----------|-------------|
| Signal detail page: 50+ data points, 3,500px scroll | CRITICAL | ≤1,200px scroll, 20 data points visible |
| Mobile: broken at 320px, unreadable text, untappable buttons | CRITICAL | All viewports 320px+ fully usable |
| Accessibility: fails WCAG AA, no focus states, color-only indicators | HIGH | WCAG 2.1 AA compliant |
| Navigation: 20 routes buried in menus, settings in 4 places | HIGH | 3-group nav, 1 settings page |
| Error recovery: no retry buttons, no offline detection | MEDIUM | Retry on all errors, offline banner |
| State management: dual WebSocket + polling coexistence | MEDIUM | Single React Query strategy |

### Plan at a Glance

```
Sprint 1 (Days 1-10):   Critical Mobile & Accessibility Fixes     — 15 stories, ~3.5 dev-days
Sprint 2 (Days 11-20):  Signal Detail Redesign & Card Clarity     — 12 stories, ~5 dev-days
Sprint 3 (Days 21-30):  Navigation & Settings Consolidation       — 7 stories, ~5 dev-days
Sprint 4 (Days 31-40):  Polish, Progressive Disclosure, Perf      — 4 stories, ~4 dev-days
                                                                     ──────────────────────
                                                    TOTAL:           38 stories, ~17.5 dev-days
```

### Dependency Chain

```
Phase A: Design System Foundation (Sprint 1)
    ↓
Phase B: Signal Detail Restructure (Sprint 2)  ←→  Phase D: Navigation (Sprint 3)
    ↓                                                    ↓
Phase C: React Query Migration (Sprint 4)        Phase E: Settings Consolidation (Sprint 3)
```

---

## 2. Architecture Plan

### Architect 1: Frontend Component Architecture

#### Phase A — Design System Foundation (Sprint 1 prerequisite)

| Task | File(s) | Change | Size |
|------|---------|--------|------|
| A1. Semantic color tokens | `tailwind.config.ts` | Add `semantic: { success, danger, warning, info }` mapping to existing signal colors | S |
| A2. Focus-visible system | `globals.css` | Add `:focus-visible` outline rule + `:focus:not(:focus-visible)` removal | S |
| A3. Touch target utility | `globals.css` | Add `.touch-target` class (min-w-[44px] min-h-[44px]) | S |
| A4. Font-size floor | `globals.css` + `tailwind.config.ts` | Enforce 12px minimum on `text-xs`, eliminate `text-[10px]`/`text-[9px]` | S |
| A5. CollapsibleSection component | NEW: `components/shared/CollapsibleSection.tsx` | Reusable collapse/expand with `aria-expanded`, chevron icon, animation | M |
| A6. StickyHeader component | NEW: `components/shared/StickyHeader.tsx` | Sticky signal header (confidence + price) that stays visible on scroll | M |

**All A-tasks are parallelizable** — no dependencies between them.

#### Phase B — Signal Detail Page Restructure (Sprint 2)

| Task | File(s) | Change | Size |
|------|---------|--------|------|
| B1. Remove ConfidenceBreakdown | DELETE import/render in `signal/[id]/page.tsx` | Move data to ConfidenceGauge tooltip. Delete ConfidenceBreakdown section from page. | S |
| B2. Reorder sections | `signal/[id]/page.tsx` | Move Price+Target+StopLoss to position 2 (below header, above chart) | S |
| B3. Wrap in CollapsibleSection | `signal/[id]/page.tsx` | Wrap News Context, Risk Calculator, Pip Calculator, Trailing Stop, Track Record in CollapsibleSection (defaultOpen=false) | M |
| B4. Section group headers | `signal/[id]/page.tsx` | Add 3 muted headers: "Signal Analysis", "Context & History", "Trading Tools" | S |
| B5. Mobile indicator collapse | `signal/[id]/page.tsx` | At <640px, show top 2 indicators + "Show all" toggle | M |
| B6. Pip Calculator forex-only | `signal/[id]/page.tsx` | Conditionally render PipCalculator only when `market_type === 'forex'` | S |

**Dependency**: B3 requires A5 (CollapsibleSection component). B1-B6 otherwise independent.

**Impact**: Page scroll reduces from ~3,500px → ~1,200px.

#### Phase C — React Query Migration (Sprint 4)

| Task | File(s) | Change | Size |
|------|---------|--------|------|
| C1. Migrate signal fetching | `hooks/useSignals.ts` → consumers use `hooks/useQueries.ts` | Replace `setInterval` polling with `useSignalsQuery` (staleTime: 30s, refetchInterval: 60s) | M |
| C2. Migrate market fetching | `hooks/useMarketData.ts` → consumers use `hooks/useQueries.ts` | Replace polling with `useMarketOverviewQuery` (staleTime: 15s, refetchInterval: 30s) | M |
| C3. WebSocket query invalidation | `hooks/useWebSocket.ts` | On WS signal message: `queryClient.invalidateQueries(['signals'])`. On WS price update: update market query cache directly. | M |
| C4. Remove legacy hooks | DELETE: `useSignals.ts`, `useMarketData.ts` (after migration verified) | Remove only after all consumers migrated | S |

**Dependency**: C3 depends on C1+C2 complete. C4 is cleanup after verification.

**Key insight from Architect 1**: `useQueries.ts` hooks already exist but have **zero production consumers**. The migration is about switching consumers, not building new infrastructure.

#### Phase D — Navigation Architecture (Sprint 3)

| Task | File(s) | Change | Size |
|------|---------|--------|------|
| D1. Group nav items | `components/shared/Navbar.tsx` | Replace flat list with 3 groups: Markets (Dashboard, News, Calendar), Analysis (Track Record, History, Backtest, Brief), Account (Portfolio, Alerts, Watchlist, Settings) | L |
| D2. Mobile drawer with sections | `components/shared/Navbar.tsx` | Add section headers with emoji icons, dividers between groups | M |
| D3. Remove "More" dropdown | `components/shared/Navbar.tsx` | All items visible in categorized groups on desktop. No hidden dropdown. | M |
| D4. Settings gear → route link | `components/shared/Navbar.tsx` | Change gear icon from opening modal to navigating to `/settings` | S |

#### Phase E — Settings Consolidation (Sprint 3)

| Task | File(s) | Change | Size |
|------|---------|--------|------|
| E1. Build unified settings page | `app/settings/page.tsx` | 5 tabs: Display, Alerts, Telegram, Watchlist, About | L |
| E2. Migrate modal content | Extract form logic from SettingsPanel, AlertConfigModal, ChatIdPrompt into settings tab sections | M |
| E3. Remove SettingsPanel modal | DELETE: `components/shared/SettingsPanel.tsx` + all references | S |
| E4. Remove ChatIdPrompt popup | DELETE: conditional render logic from layout/dashboard | S |

**Dependency**: E3-E4 require E1+E2 complete and verified.

---

### Architect 2: Mobile & Accessibility Architecture

#### WCAG 2.1 AA Color Contrast Fixes

| Element | Current | Fix | WCAG Criterion |
|---------|---------|-----|---------------|
| `text-text-muted` on `bg-secondary` | #6B7280 → 4:1 ratio | → **#9CA3AF** (5.5:1) | 1.4.3 Contrast |
| `text-text-secondary` on `bg-card` | #9CA3AF → 3.5:1 | → **#D1D5DB** (7:1) | 1.4.3 Contrast |
| Info icon (IndicatorTooltip) | `text-muted/50` (invisible) | → **`text-muted`** full opacity | 1.4.3 Contrast |
| Signal badge background | 20% opacity | → **35% opacity** | 1.4.3 Contrast |
| Inactive nav items | `text-text-secondary` | → **`text-text-primary/70`** | 1.4.3 Contrast |

**Tailwind config change**: Update `text.muted` value from `#6B7280` to `#9CA3AF` in `tailwind.config.ts`.

#### Responsive Grid Fixes

| Component | Current | Fix |
|-----------|---------|-----|
| Dashboard skeleton | `grid-cols-3` | → `grid-cols-1 sm:grid-cols-3` |
| MarketOverview | Horizontal scroll | → `grid-cols-1 sm:grid-cols-3` with vertical stack on mobile |
| History table | `hidden sm:grid` (invisible on mobile) | → Card layout fallback at <640px (already exists, needs tuning) |

#### Touch Target Audit — All Violations

| Element | Current Size | Fix | File |
|---------|-------------|-----|------|
| Navbar hamburger | `w-5 h-5 p-2` = 36px | → `p-3` = 44px | `Navbar.tsx` |
| Settings gear icon | `w-4 h-4 p-2` = 32px | → `w-5 h-5 p-2.5` = 40px + wrapper | `Navbar.tsx` |
| Notification badge | `min-w-[16px] h-4` = 16px | Enlarge to `min-w-[20px] h-5` in 44px parent | `Navbar.tsx` |
| Close buttons (modals) | `w-5 h-5` = 20px | → `p-2.5` wrapper = 40px | Multiple |
| Search icon toggle | `w-4 h-4 p-1.5` = 28px | → `p-2.5` = 36px minimum | `SignalFeed.tsx` |
| IndicatorTooltip icon | `w-3 h-3` = 12px | → `w-4 h-4 p-2` = 32px (within 44px parent) | `IndicatorTooltip.tsx` |

#### Semantic HTML Fixes

| Component | Current | Fix | File |
|-----------|---------|-----|------|
| Signal card expand | `<div role="button" tabIndex={0}>` | → `<button className="w-full text-left">` | `SignalCard.tsx` |
| IndicatorTooltip trigger | `<span>` with onClick | → `<button>` with tooltip | `IndicatorTooltip.tsx` |
| Filter buttons | Some use `<div>` | → `<button aria-pressed={active}>` | `SignalFeed.tsx` |

#### Form Label Fixes

| Input | Current | Fix | File |
|-------|---------|-----|------|
| Chat ID input | placeholder only | + `aria-label="Telegram Chat ID"` | `ChatIdPrompt.tsx` → `settings/page.tsx` |
| AskAI symbol input | placeholder only | + `aria-label="Stock symbol"` | `AskAI.tsx` |
| AskAI question input | placeholder only | + `aria-label="Your question"` | `AskAI.tsx` |
| Risk calculator custom input | placeholder only | + `aria-label="Custom investment amount"` | `RiskCalculator.tsx` |
| Alert confidence slider | no label | + `aria-label="Minimum confidence threshold"` | `AlertConfigModal.tsx` → `settings/page.tsx` |

#### Modal Focus Trap Pattern

```tsx
// Shared FocusTrap wrapper — reuse for all modals/bottom-sheets
function FocusTrap({ children, isOpen, onClose }) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!isOpen) return;
    const container = containerRef.current;
    const focusables = container?.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusables?.[0] as HTMLElement;
    const last = focusables?.[focusables.length - 1] as HTMLElement;
    
    first?.focus();
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);
  
  return <div ref={containerRef}>{children}</div>;
}
```

---

## 3. User Stories & Prioritization

### RICE-Scored User Stories (Top 20 by Priority)

| Rank | ID | Story | RICE | Sprint |
|------|-----|-------|------|--------|
| 1 | MOB-1 | Fix mobile grid to single-column at 320px | 3000 | 1 |
| 2 | MOB-2 | All touch targets ≥44px | 1500 | 1 |
| 3 | MOB-3 | All text ≥12px minimum | 1500 | 1 |
| 4 | A11Y-7 | Signal badge opacity 20% → 35% | 1000 | 1 |
| 5 | SD-2 | Remove ConfidenceBreakdown (→ tooltip on gauge) | 1000 | 1 |
| 6 | SD-3 | Collapse News/Tools/Track Record by default | 1000 | 1 |
| 7 | SD-1 | Move Price+Target to position 2 on detail page | 1000 | 2 |
| 8 | A11Y-1 | Fix color contrast to WCAG AA (5 elements) | 667 | 1 |
| 9 | ERR-1 | Add retry buttons to all error states | 667 | 1 |
| 10 | A11Y-5 | Signal type: text labels alongside color | 533 | 1 |
| 11 | MOB-5 | MarketOverview vertical stack on mobile | 533 | 1 |
| 12 | MOB-7 | Hide keyboard shortcuts modal on touch devices | 500 | 1 |
| 13 | PD-3 | `inputMode="numeric"` for Chat ID (no spinner) | 500 | 1 |
| 14 | A11Y-3 | Semantic `<button>` instead of `<div role="button">` | 500 | 1 |
| 15 | A11Y-2 | Focus-visible states system-wide | 320 | 1 |
| 16 | SC-1 | Signal card: dedicated row for Target/Stop/Timeframe | 320 | 2 |
| 17 | MOB-4 | History table → card layout on mobile | 320 | 2 |
| 18 | NAV-2 | Mobile nav with 3 grouped sections + icons | 320 | 2 |
| 19 | SD-5 | Collapse indicators on mobile (show top 2) | 320 | 2 |
| 20 | A11Y-4 | `aria-label` on all form inputs | 333 | 1 |

### User Story Epics

```
Epic 1: Signal Detail Redesign  — SD-1, SD-2, SD-3, SD-4, SD-5, SD-6     (6 stories)
Epic 2: Mobile UX Fixes         — MOB-1 to MOB-7                          (7 stories)
Epic 3: Accessibility            — A11Y-1 to A11Y-7                       (7 stories)
Epic 4: Navigation & Settings   — NAV-1 to NAV-5                          (5 stories)
Epic 5: Signal Card Clarity      — SC-1, SC-2, SC-3                       (3 stories)
Epic 6: Error Recovery           — ERR-1 to ERR-4                         (4 stories)
Epic 7: Progressive Disclosure   — PD-1 to PD-4                           (4 stories)
Epic 8: State Management         — SM-1, SM-2                             (2 stories)
                                                                    TOTAL: 38 stories
```

---

## 4. Feature Rollout Strategy

### Feature Flag Categorization (PM 2)

#### Deploy All-at-Once (Safe — no behavioral change)

| Changes | Why Safe |
|---------|----------|
| Mobile grid fix, touch targets, font floor | Pure CSS, strictly additive |
| WCAG contrast fixes, focus-visible, semantic buttons | Accessibility fixes, invisible to mouse users |
| Retry buttons, form labels, offline banner | Additive, no existing behavior removed |
| `inputMode="numeric"`, hide keyboard modal on touch | Bug fixes |

#### Feature Flags Required (Behavioral/layout change)

| Change | Flag Name | Default | Rollout |
|--------|-----------|---------|---------|
| Signal detail: collapsed sections | `sf_flag_collapsed_detail` | `false` → `true` after 3 days | Sprint 2 |
| Signal detail: section reorder | `sf_flag_detail_reorder` | `false` → `true` after 3 days | Sprint 2 |
| Navigation: 3-group categorized | `sf_flag_grouped_nav` | `false` → `true` after 5 days | Sprint 3 |
| Unified settings page | `sf_flag_unified_settings` | `false` → `true` after 5 days | Sprint 3 |
| 3 signal card view modes | `sf_flag_three_view_modes` | `false` → `true` after 3 days | Sprint 3 |
| Progressive feature disclosure | `sf_flag_progressive_disclosure` | `false` (opt-in only) | Sprint 4 |
| Market-hours-aware dashboard | `sf_flag_market_hours_ordering` | `false` → `true` after 5 days | Sprint 4 |

#### Implementation Pattern

```typescript
// preferencesStore.ts — extend with featureFlags
featureFlags: {
  sf_flag_collapsed_detail: getStored('sf_flag_collapsed_detail', false),
  sf_flag_grouped_nav: getStored('sf_flag_grouped_nav', false),
  // ...
}

// URL override for testing: ?sf_flags=all enables everything
// Settings → Display → "Try New Layout" toggle for user control
```

#### Rollout Timeline

```
Sprint 1: No flags needed (all CSS/a11y fixes deployed directly)
Sprint 2: sf_flag_collapsed_detail + sf_flag_detail_reorder → enabled after 3 days 
Sprint 3: sf_flag_grouped_nav + sf_flag_unified_settings → enabled after 5 days
Sprint 4: sf_flag_progressive_disclosure stays opt-in for 2 weeks
```

After 2-week bake with no issues: remove old code paths and feature flags.

### A/B Testing Approach

Since this is a single-user product, use **self-A/B testing** — expose variants with an explicit toggle:

| Test | Variants | Metric | Toggle Location |
|------|----------|--------|----------------|
| Signal Detail Layout | Classic / Collapsible / Tabbed | Time-to-action, scroll depth | Settings → Display |
| Signal Card Density | Minimal / Standard / Detailed | Card expand rate, click-through | Settings → Display |
| Navigation | Flat list / 3-group categorized | Pages per session | Settings → Display |

### User Communication

| Sprint | Communication | Channel |
|--------|--------------|---------|
| Sprint 1 | No announcement (invisible a11y/mobile fixes) | — |
| Sprint 2 | "Signal pages are now cleaner and faster to scan" | Toast on first visit post-deploy |
| Sprint 3 | "We reorganized navigation — find everything faster" | In-app "What's New" modal (one-time) |
| Sprint 4 | "Dashboard now shows what matters most right now" | Subtle tooltip on first market-hours ordering |

---

## 5. Sprint Plan

### Sprint 1: Critical Mobile & Accessibility (Days 1-10)

**Goal**: Make the app fully usable on mobile. Pass WCAG AA on all critical paths.
**Theme**: *"Every tap works, every word is readable, every signal is accessible"*
**Velocity**: ~3.5 dev-days

#### Stories

| ID | Story | Est. | Acceptance Criteria |
|----|-------|------|-------------------|
| **A-tasks** | Design system foundation | 0.5d | Semantic colors, focus-visible, touch-target utility, font floor in place |
| MOB-1 | Fix mobile grid | 0.1d | Dashboard single-column at 320px. No horizontal overflow |
| MOB-2 | Touch targets ≥44px | 0.2d | All interactive elements ≥44px. Verified on iPhone SE |
| MOB-3 | 12px text floor | 0.2d | `grep 'text-\[1[01]px\]\|text-\[9px\]'` returns 0 hits |
| MOB-5 | MarketOverview stack | 0.3d | Vertical cards at <640px. No horizontal scroll |
| MOB-7 | Hide keyboard modal on touch | 0.1d | Renders `null` when `navigator.maxTouchPoints > 0` |
| A11Y-1 | WCAG AA contrast | 0.3d | axe DevTools: 0 contrast violations |
| A11Y-2 | Focus-visible states | 0.5d | Every interactive element shows 2px purple outline on keyboard focus |
| A11Y-3 | Semantic buttons | 0.2d | Zero `<div role="button">` in codebase |
| A11Y-4 | Form aria-labels | 0.3d | All inputs have `aria-label` or `<label>`. axe: 0 form-label violations |
| A11Y-5 | Signal type text labels | 0.3d | Text ("STRONG BUY", etc.) alongside icon/color. Screen reader announces type |
| A11Y-7 | Badge opacity 35% | 0.1d | Signal badges readable against dark card |
| ERR-1 | Retry buttons on errors | 0.3d | All error states show "Try Again" button |
| ERR-2 | Offline detection banner | 0.3d | Banner appears when `navigator.onLine === false` |
| PD-3 | `inputMode="numeric"` | 0.1d | No number spinner on mobile |
| SD-2 | Remove ConfidenceBreakdown | 0.2d | Section gone; data shows as gauge tooltip |

#### Definition of Done — Sprint 1
- [ ] All 15+ stories implemented and code-reviewed
- [ ] `npx vitest run` — 0 failures
- [ ] `docker compose build` — passes
- [ ] Manual QA on iPhone SE (320px), iPhone 14 (390px), iPad (768px)
- [ ] axe DevTools scan: 0 critical/serious violations on Dashboard + Signal Detail
- [ ] Keyboard tab-through test: Dashboard → Signal Card → Signal Detail → Back
- [ ] No visual regressions on desktop (1440px)

**Rollback**: All CSS/component-level changes. `git revert` sprint branch. No backend/DB changes.

---

### Sprint 2: Signal Detail Redesign & Card Clarity (Days 11-20)

**Goal**: Reduce signal detail from 3,500px to ≤1,500px scroll. Signal cards scannable in <2 seconds.
**Theme**: *"Decision in 30 seconds, not 3 minutes"*
**Velocity**: ~5 dev-days

#### Stories

| ID | Story | Est. | Acceptance Criteria |
|----|-------|------|-------------------|
| SD-1 | Move Price+Target to position 2 | 0.3d | Price section renders directly below header |
| SD-3 | Collapse tool/news/track sections | 0.3d | 5 sections collapsed by default. Click to expand. State in sessionStorage |
| SD-4 | Section group headers | 0.3d | 3 headers: "Signal Analysis", "Context & History", "Trading Tools" |
| SD-5 | Collapse indicators on mobile | 0.5d | <640px: top 2 indicators + "Show all" toggle |
| SD-6 | Pip calc forex-only + collapsed | 0.3d | Only renders for forex signals. Collapsed by default |
| SC-1 | Signal card target/stop row | 0.5d | Dedicated row: 🎯 target | 🛑 stop | ⏱ timeframe |
| SC-3 | Text label on signal card border | 0.3d | "BUY"/"SELL"/"HOLD" text alongside colored border |
| MOB-4 | History table → cards on mobile | 0.5d | Card layout at <640px with symbol, signal, outcome, return, date |
| NAV-2 | Mobile nav grouped sections | 0.5d | Drawer shows 3 groups with dividers and icons |
| NAV-5 | Mobile drawer section icons | 0.3d | Emoji prefix on each item. Muted uppercase section headers |
| ERR-3 | Consistent empty states | 0.7d | All pages match SignalFeed empty state quality |
| NAV-4 | "NEW" tag on signal cards | 0.5d | Green badge on signals <5 min old. IntersectionObserver marks as seen after 3s |

#### Definition of Done — Sprint 2
- [ ] Signal detail scroll height ≤1,500px at 1440px viewport
- [ ] Signal card collapsed state communicates actionable info in ≤3 rows
- [ ] `npx vitest run` — 0 failures (update existing tests for restructured detail)
- [ ] `docker compose build` — passes
- [ ] Mobile QA: Signal detail usable on iPhone SE without horizontal scroll
- [ ] All sections still accessible via expand/collapse
- [ ] Feature flags `sf_flag_collapsed_detail` + `sf_flag_detail_reorder` active

**Rollback**: Component-level changes. Revert sprint branch + disable feature flags.

---

### Sprint 3: Navigation & Settings Consolidation (Days 21-30)

**Goal**: Unify settings. Restructure navigation for feature discovery.
**Theme**: *"One place for everything, everything in its place"*
**Velocity**: ~5 dev-days

#### Stories

| ID | Story | Est. | Acceptance Criteria |
|----|-------|------|-------------------|
| NAV-1 | Nav grouped into 3 categories | 0.7d | Desktop: 3 groups visible. "More" dropdown eliminated |
| NAV-3 | Unified /settings page | 1.0d | 5 tabs: Display, Alerts, Telegram, Watchlist, About. Old modals removable |
| MOB-6 | Bottom-sheet modals on mobile | 1.0d | <640px: modals slide up from bottom. Swipe-down to dismiss |
| A11Y-6 | Modal focus traps | 0.5d | Focus trapped in open modals. Escape closes. Focus returns on close |
| SC-2 | 3-tier signal card view modes | 1.0d | Minimal/Standard/Detailed modes. Persisted in localStorage |
| PD-4 | Confidence preset buttons | 0.3d | 4 presets (60/70/80/90%) replace 0-100 slider |
| ERR-4 | Data freshness indicator | 0.3d | "Updated Xs ago" near MarketOverview. Amber if >60s. Red if >5m |

#### Definition of Done — Sprint 3
- [ ] SettingsPanel modal, AlertConfigModal, ChatIdPrompt — removed from codebase
- [ ] `/settings` page fully functional with 5 tabs
- [ ] Desktop nav shows categories, no "More" dropdown
- [ ] `npx vitest run` — 0 failures
- [ ] `docker compose build` — passes
- [ ] Settings persist across page refreshes
- [ ] Feature flags `sf_flag_grouped_nav` + `sf_flag_unified_settings` active

**Rollback**: **Medium risk.** Keep old modal components hidden (feature flag) for 1 sprint post-launch. Navigation is CSS — safe to revert.

---

### Sprint 4: Polish, Progressive Disclosure & Performance (Days 31-40)

**Goal**: Intelligent UX that reduces noise. Clean up state management tech debt.
**Theme**: *"Smart defaults that grow with you"*
**Velocity**: ~4 dev-days

#### Stories

| ID | Story | Est. | Acceptance Criteria |
|----|-------|------|-------------------|
| PD-1 | Progressive feature disclosure | 1.3d | Visit 1-5: basic view. Visit 6-15: +indicators. Visit 16-30: +tools. Visit 31+: full. Override in Settings |
| PD-2 | Market-hours-aware dashboard | 0.7d | Active markets sorted first. Contextual message about market status |
| SM-1 | Complete React Query migration | 1.3d | All REST fetching via React Query. Zero `setInterval` patterns. WebSocket invalidates query cache |
| SM-2 | IntersectionObserver seen-tracking | 0.5d | Signals marked seen after 3s in viewport. Unseen badge accurate |

#### Definition of Done — Sprint 4
- [ ] Zero `setInterval` for REST data fetching
- [ ] Fresh localStorage → only basic features on signal detail
- [ ] Market-hours logic matches backend `market_hours.py`
- [ ] `npx vitest run` — 0 failures
- [ ] `docker compose build` — passes
- [ ] Network tab: no duplicate requests
- [ ] Lighthouse Performance ≥85

**Rollback**: Feature flags on all items. React Query: toggle between old/new via flag.

---

## 6. Test Strategy

### Current Test Infrastructure

- **Framework**: Vitest 4.1.1 + Testing Library (React 16.3, user-event 14.6, jest-dom 6.9)
- **Environment**: jsdom
- **Existing tests**: 74 test files in `frontend/src/__tests__/`
- **Missing**: No accessibility testing (axe-core), no viewport testing, no visual regression

### New Test Infrastructure (Sprint 1 setup)

| Addition | Package | Purpose |
|----------|---------|---------|
| Accessibility testing | `vitest-axe` + `axe-core` | Automated WCAG audits in every component test |
| ESLint a11y rules | `eslint-plugin-jsx-a11y` | Catch accessibility violations at lint time |
| Viewport testing helper | Custom utility | Set `window.innerWidth` for responsive assertions |

### Test Coverage Per Sprint

#### Sprint 1 Tests (Mobile & Accessibility)

| Area | New Tests | Modified Tests | Total |
|------|-----------|---------------|-------|
| Mobile grid fix | 3 | 1 | 4 |
| Touch targets audit | 6 | 1 | 7 |
| Font size floor | 1 | 3 | 4 |
| WCAG contrast | 5 | 0 | 5 |
| Focus-visible | 3 | 0 | 3 |
| Semantic buttons | 2 | 2 | 4 |
| Form labels | 3 | 0 | 3 |
| Retry buttons | 4 | 0 | 4 |
| ConfidenceBreakdown removal | 2 | 2 (delete old) | 4 |
| **Sprint 1 Total** | **~32** | **~9** | **~41** |

#### Sprint 2 Tests (Signal Detail & Card)

| Area | New Tests | Modified Tests | Total |
|------|-----------|---------------|-------|
| Section reorder | 3 | 3 | 6 |
| Collapsed sections | 6 | 3 | 9 |
| Section headers | 2 | 0 | 2 |
| Mobile indicator collapse | 3 | 1 | 4 |
| Signal card layout | 4 | 4 | 8 |
| Empty states | 5 | 0 | 5 |
| "NEW" badge | 3 | 0 | 3 |
| **Sprint 2 Total** | **~26** | **~11** | **~37** |

#### Sprint 3 Tests (Navigation & Settings)

| Area | New Tests | Modified Tests | Total |
|------|-----------|---------------|-------|
| Nav restructure | 8 | 5 | 13 |
| Settings page (5 tabs) | 15 | 0 | 15 |
| Modal removal cleanup | 0 | 3 (delete old) | 3 |
| Focus traps | 4 | 0 | 4 |
| View modes | 4 | 2 | 6 |
| **Sprint 3 Total** | **~31** | **~10** | **~41** |

#### Sprint 4 Tests (Polish & Performance)

| Area | New Tests | Modified Tests | Total |
|------|-----------|---------------|-------|
| Progressive disclosure | 6 | 0 | 6 |
| Market-hours ordering | 4 | 1 | 5 |
| React Query migration | 8 | 5 | 13 |
| IntersectionObserver | 3 | 1 | 4 |
| **Sprint 4 Total** | **~21** | **~7** | **~28** |

#### Grand Total

```
New tests:      ~110
Modified tests: ~37
Deleted tests:  ~5 (ConfidenceBreakdown, old SettingsPanel, old AlertConfig)
───────────────────
Net new:        ~105 tests added to the 74 existing = ~179 frontend tests
```

### Device Test Matrix (QA Tester 2)

**For every sprint**, test on these viewports:

| Device | Width | Critical For |
|--------|-------|-------------|
| iPhone SE | 375px | Grid collapse, touch targets, font sizes |
| Samsung Galaxy S21 | 360px | Narrowest viewport - catches edge cases |
| iPhone 14 | 390px | Standard mobile baseline |
| iPad Mini | 768px | Breakpoint boundary (md:) |
| Desktop | 1440px | Layout verification, keyboard/a11y |

### Critical Touch Interaction Test Cases

| ID | Test | Devices |
|----|------|---------|
| TC-01 | Signal card tap-to-expand (toggle, scroll within, rapid double-tap) | All mobile |
| TC-02 | Filter button tapping (toggle, rapid switches, with keyboard open) | All mobile |
| TC-03 | Navbar hamburger (open, close, nav + auto-close, outside tap) | All mobile |
| TC-04 | Collapsible section toggle (expand, collapse, all-expanded scroll) | All mobile |
| TC-05 | Risk calculator amount buttons (select, deselect, custom input) | All mobile |
| TC-06 | Search input focus + virtual keyboard (doesn't overlap content) | iPhone SE, Galaxy |
| TC-07 | Bottom-sheet modal (swipe-down dismiss, scroll within) | All mobile |

### Accessibility Audit Checklist (80+ items)

**Automated (axe-core in every test file)**:
- [ ] 0 critical violations per page
- [ ] 0 serious violations per page
- [ ] Color contrast ≥4.5:1 for all text
- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] All buttons have accessible names
- [ ] All links have descriptive text
- [ ] ARIA roles used correctly
- [ ] No duplicate IDs

**Manual (per sprint)**:
- [ ] Keyboard-only navigation through every page (Tab, Shift+Tab, Enter, Escape)
- [ ] Focus visible on every interactive element
- [ ] Focus order matches visual order
- [ ] No focus trap outside modals
- [ ] Focus trapped inside open modals
- [ ] Screen reader announces signal type, confidence, price
- [ ] Screen reader announces form field purpose
- [ ] Reduced-motion preference respected (no animations)
- [ ] 200% zoom: no content cutoff or horizontal scroll

### Performance Budget (QA Tester 1)

| Metric | Current | Target | Threshold |
|--------|---------|--------|-----------|
| Bundle size (gzip) | ~600KB | ≤650KB | Alert if >700KB |
| Lighthouse Performance | Baseline TBD | ≥85 | Block if <80 |
| LCP (Largest Contentful Paint) | Baseline TBD | <2.5s | Block if >4s |
| FID (First Input Delay) | Baseline TBD | <100ms | Block if >300ms |
| CLS (Cumulative Layout Shift) | Baseline TBD | <0.1 | Block if >0.25 |

New components (CollapsibleSection, FocusTrap, StickyHeader) estimated at <5KB total — well within budget.

---

## 7. Success Metrics

### Epic 1: Signal Detail Page

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Page scroll height | ~3,500px | ≤1,500px | DOM measurement at 1440px |
| Sections visible without scroll | 2 of 11 | 4 of 5 primary | Visual count |
| Price/Target visible | Below fold (400px scroll) | Above fold (0 scroll) | Position measurement |
| Time to decision data | 3-5 min scrolling | <30 seconds | User testing (qualitative) |

### Epic 2: Mobile UX

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Touch target violations | 8+ | 0 | Manual audit + axe WCAG 2.5.8 |
| Text below 12px | 25+ instances | 0 | `grep` codebase scan |
| Grid break at 320px | Dashboard broken | Zero overflow | Chrome DevTools responsive |
| Mobile data hidden | History table invisible | All data accessible | Manual QA on iPhone SE |

### Epic 3: Accessibility

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| axe critical+serious violations | ~15+ | 0 | axe DevTools full scan |
| WCAG contrast failures | 5+ elements | 0 | Contrast checker tool |
| Keyboard navigability | Partially broken | 100% tab-navigable | Manual keyboard test |
| Form label compliance | 5+ missing | 0 | axe automated scan |

### Epic 4: Navigation

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Hidden features ("More" dropdown) | 8 items | 0 | UI inspection |
| Settings locations | 4 scattered | 1 unified | Code audit |
| Nav items with clear grouping | 0 groups | 3 groups | UI inspection |

### Epic 6: Error Recovery

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Error states with retry | 0 of 8 | 8 of 8 | Code audit |
| Offline detection | None | Immediate | Toggle airplane mode |
| Recovery time from API error | ~90s (poll) | <5s (retry click) | Manual test |

---

## 8. Risk Assessment

### Sprint 1 Risks (Low Overall)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CSS changes break desktop layout | Medium | High | Screenshot comparison at 1440px before/after |
| Touch target increase causes layout shifts | Low | Medium | Use padding (not width) increase |
| Contrast changes break dark theme aesthetic | Medium | Low | Only increase muted text lightness |
| ConfidenceBreakdown removal breaks tests | Low | Medium | Update 1-2 tests in same PR |

### Sprint 2 Risks (Medium)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Signal detail restructure breaks test selectors | **High** | Medium | Update selectors in same PR. Run full suite before merge |
| Collapsed sections confuse users | Medium | Medium | Clear expand/collapse affordances. Persist state in sessionStorage |
| Signal card 3-row layout too tall | Medium | Medium | Verify ≤6 cards above fold. Adjust padding if needed |

### Sprint 3 Risks (Highest Risk Sprint)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Removing 3 modals breaks deep links | **High** | **High** | Search ALL references before removal. Keep old components behind feature flag for 1 sprint |
| Navigation restructure disorients returning users | Medium | Medium | Dashboard unchanged. Section headers help. "What's New" modal on first visit |
| Bottom-sheet gesture handling complex | Medium | Medium | Use proven library (`@radix-ui/react-dialog` or `vaul`). Don't build from scratch |

### Sprint 4 Risks (Medium)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| React Query + WebSocket race conditions | **High** | Medium | Feature flag. Test: WS delivers signal → RQ cache invalidated → no dupes |
| Progressive disclosure frustrates power users | Medium | Medium | "Show all features" toggle always available |
| Market-hours logic drift from backend | Medium | Low | Share constants or fetch from backend API |

### Cross-Sprint Risks

| Risk | Mitigation |
|------|------------|
| Test suite grows too large (slows CI) | Group tests by sprint. Run only affected tests in PRs |
| Feature flags pile up | Mandatory flag removal 2 weeks after stable launch |
| User preference data loss during Settings migration | Migrate localStorage keys in E1 before deleting old stores |
| Bundle size creep from new components | Performance budget alert at 650KB. Lazy-load chart components |

---

## Files Impact Summary

### New Files to Create

| File | Sprint | Purpose |
|------|--------|---------|
| `components/shared/CollapsibleSection.tsx` | 1 | Reusable expand/collapse with a11y |
| `components/shared/StickyHeader.tsx` | 2 | Sticky signal header on scroll |
| `components/shared/FocusTrap.tsx` | 3 | Modal focus management |
| `components/shared/OfflineBanner.tsx` | 1 | Network status detection |
| **~110 new test files/additions** | 1-4 | Coverage for all changes |

### Files to Heavily Modify

| File | Sprint | Changes |
|------|--------|---------|
| `tailwind.config.ts` | 1 | Semantic colors, muted text value |
| `globals.css` | 1 | Focus-visible, touch-target, font floor |
| `signal/[id]/page.tsx` | 2 | Complete section reorder + collapse |
| `components/shared/Navbar.tsx` | 2-3 | Group navigation, remove More dropdown |
| `components/signals/SignalCard.tsx` | 2 | 3-row layout, text labels, a11y |
| `components/signals/SignalFeed.tsx` | 1-2 | Touch targets, font sizes, search a11y |
| `components/signals/ConfidenceGauge.tsx` | 1-2 | Tooltip with breakdown data |
| `app/settings/page.tsx` | 3 | Build unified 5-tab settings |
| `hooks/useWebSocket.ts` | 4 | React Query cache invalidation |
| `store/preferencesStore.ts` | 2-4 | Feature flags, view modes |

### Files to Delete (After Migration)

| File | Sprint | Reason |
|------|--------|--------|
| `components/signals/ConfidenceBreakdown.tsx` | 2 | Data moved to gauge tooltip |
| `components/shared/SettingsPanel.tsx` | 3 | Merged into /settings page |
| `hooks/useSignals.ts` | 4 | Replaced by React Query |
| `hooks/useMarketData.ts` | 4 | Replaced by React Query |

---

*Plan created: 25 March 2026*
*Contributors: Architect 1 (Frontend Architecture), Architect 2 (Mobile & Accessibility), PM 1 (User Journey & RICE), PM 2 (Feature Rollout & Metrics), QA Tester 1 (Test Strategy), QA Tester 2 (Mobile & A11y Testing)*
*Source: [UI/UX Review v2](ui-ux-review-v2.md) — 10-agent analysis*
