# Navigation Reorganization — Implementation Plan

> **Spec**: [spec.md](spec.md)  
> **Date**: 27 March 2026  
> **Status**: Ready for implementation  

---

## Scope Summary

Restructure navigation so all 16+ pages are reachable. Currently 6 pages are in nav; 10+ are undiscoverable. Changes:

1. **Desktop top bar**: 5 primary links + "Research" dropdown (replaces 3 links + "More")
2. **Mobile bottom nav**: New 5-tab fixed bar (Home, Watchlist, Brief, Portfolio, Menu)
3. **Mobile menu sheet**: Bottom sheet drawer (replaces hamburger dropdown)
4. **Site footer**: New full-width footer with column layout (supplements SebiDisclaimer)
5. **Navbar.tsx rewrite**: New link arrays, Research dropdown, remove duplication
6. **Layout changes**: Bottom nav spacing, footer placement

No backend changes. No new pages. No route changes.

---

## Current State Assessment

### Files to modify
| File | Current State | Change Scope |
|------|--------------|--------------|
| [Navbar.tsx](../../../frontend/src/components/shared/Navbar.tsx) | 230 lines. 3 primary links, "More" dropdown, hamburger mobile menu, Settings gear + Settings in dropdown (duplicated) | Major rewrite — new link arrays, Research dropdown, simplified mobile top bar |
| [layout.tsx](../../../frontend/src/app/layout.tsx) | Renders Navbar → OfflineBanner → main → SebiDisclaimer → CookieConsent | Add BottomNav, SiteFooter; adjust main padding |
| [globals.css](../../../frontend/src/app/globals.css) | ~140 lines. CSS vars, animations, theme overrides | Add bottom sheet animations, safe-area padding |
| [Navbar.test.tsx](../../../frontend/src/__tests__/Navbar.test.tsx) | 115 lines. Tests 3 primary links, "More" dropdown, badge, auth states | Rewrite to match new 5-link structure, Research dropdown |
| [useKeyboardShortcuts.ts](../../../frontend/src/hooks/useKeyboardShortcuts.ts) | Single-key shortcuts (1-4, /, ?, Esc) for dashboard filters | Add G-then-letter navigation shortcuts |
| [constants.ts](../../../frontend/src/lib/constants.ts) | Colors, thresholds, labels | Add navigation link constants |

### Files to create
| File | Purpose |
|------|---------|
| `frontend/src/components/shared/BottomNav.tsx` | Mobile bottom navigation bar (5 tabs) |
| `frontend/src/components/shared/MobileMenuSheet.tsx` | Bottom sheet drawer with grouped menu items |
| `frontend/src/components/shared/SiteFooter.tsx` | Full site footer with 4-column layout |
| `frontend/src/__tests__/BottomNav.test.tsx` | Tests for bottom nav component |
| `frontend/src/__tests__/MobileMenuSheet.test.tsx` | Tests for mobile menu sheet |
| `frontend/src/__tests__/SiteFooter.test.tsx` | Tests for site footer |

### Existing infrastructure to reuse
- `FocusTrap` component — for menu sheet focus management
- `NotificationCenter` component — bell icon, stays in top bar
- `useSignalStore.unseenCount` — for badge on Dashboard/Home tab
- `usePathname()` — for active state detection
- `useSession()` / `signOut()` — for auth-gated rendering
- Tailwind `md:` breakpoint at 768px — consistent with all existing responsive patterns
- CSS custom properties in globals.css — all color tokens already defined

---

## Task Breakdown

### Task 1: Add navigation constants to constants.ts

**File**: `frontend/src/lib/constants.ts`  
**Depends on**: Nothing  
**Effort**: Small  

Add all navigation link arrays as a single source of truth. These will be imported by Navbar, BottomNav, MobileMenuSheet, and SiteFooter.

```typescript
// Add to constants.ts:

export const NAV_PRIMARY_LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/watchlist', label: 'Watchlist' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/brief', label: 'Brief' },
  { href: '/track-record', label: 'Track Record' },
];

export const NAV_RESEARCH_LINKS = [
  { href: '/news', label: 'News', icon: '📰' },
  { href: '/calendar', label: 'Calendar', icon: '📅' },
  { href: '/backtest', label: 'Backtest', icon: '🔬' },
  { href: '/history', label: 'Signal History', icon: '📜' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
];

export const NAV_INFO_LINKS = [
  { href: '/how-it-works', label: 'How It Works', icon: '❓' },
  { href: '/pricing', label: 'Pricing', icon: '💎' },
];

export const NAV_MOBILE_TABS = [
  { href: '/', label: 'Home', id: 'home' },
  { href: '/watchlist', label: 'Watchlist', id: 'watchlist' },
  { href: '/brief', label: 'Brief', id: 'brief' },
  { href: '/portfolio', label: 'Portfolio', id: 'portfolio' },
  { id: 'menu', label: 'Menu' },
] as const;

export const NAV_MOBILE_MENU_GROUPS = [
  {
    title: 'Performance',
    links: [
      { href: '/track-record', label: 'Track Record', icon: '📊' },
      { href: '/history', label: 'Signal History', icon: '📜' },
    ],
  },
  {
    title: 'Research',
    links: [
      { href: '/news', label: 'News', icon: '📰' },
      { href: '/calendar', label: 'Calendar', icon: '📅' },
      { href: '/backtest', label: 'Backtest', icon: '🔬' },
    ],
  },
  {
    title: 'Account',
    links: [
      { href: '/alerts', label: 'Alert Settings', icon: '🔔' },
      { href: '/settings', label: 'Settings', icon: '⚙️' },
    ],
  },
  {
    title: 'About',
    links: [
      { href: '/how-it-works', label: 'How It Works', icon: '❓' },
      { href: '/pricing', label: 'Pricing', icon: '💎' },
    ],
  },
];

export const NAV_LEGAL_LINKS = [
  { href: '/privacy', label: 'Privacy' },
  { href: '/terms', label: 'Terms' },
  { href: '/refund-policy', label: 'Refund Policy' },
  { href: '/contact', label: 'Contact' },
];

export const NAV_PUBLIC_LINKS = [
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/pricing', label: 'Pricing' },
];
```

**Verification**: Existing tests still pass (`npx vitest run`). No functional change yet.

---

### Task 2: Add bottom sheet CSS animations to globals.css

**File**: `frontend/src/app/globals.css`  
**Depends on**: Nothing  
**Effort**: Small  

Add keyframe animations for the bottom sheet and overlay. Also add a utility for bottom-nav safe-area padding.

```css
/* Bottom sheet animations */
@keyframes sheet-slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes sheet-slide-down {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}

@keyframes overlay-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-sheet-up {
  animation: sheet-slide-up 300ms ease-out forwards;
}

.animate-sheet-down {
  animation: sheet-slide-down 200ms ease-in forwards;
}

.animate-overlay-in {
  animation: overlay-fade-in 200ms ease-out forwards;
}

/* Safe area for bottom nav on iOS */
.pb-safe-bottom {
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}
```

Add `prefers-reduced-motion` entries for the new animations in the existing `@media` block.

**Verification**: No visual change yet. Existing tests pass.

---

### Task 3: Create SiteFooter component

**File**: `frontend/src/components/shared/SiteFooter.tsx` (new)  
**Depends on**: Task 1 (constants)  
**Effort**: Medium  

Four-column footer layout: Product, Research, Legal, Support. Includes SEBI disclaimer text (matching current `SebiDisclaimer` content). On mobile, collapses to 2-column or single-column grid.

Key implementation details:
- Import `NAV_PRIMARY_LINKS`, `NAV_RESEARCH_LINKS`, `NAV_LEGAL_LINKS` from constants
- Use `Link` from `next/link`
- Include the SEBI disclaimer text and copyright
- `role="contentinfo"` with `aria-label="Site footer"`
- On mobile (`< md`), add extra bottom padding to clear the bottom nav bar: `pb-20 md:pb-0`
- Render for both authenticated and unauthenticated users

Column structure:
```
Product:       Research:         Legal:           Support:
Dashboard      News              Privacy          Contact
Watchlist      Calendar          Terms
Portfolio      Backtest          Refund Policy
Brief          Signal History
Track Record
```

**Verification**: Renders standalone. Write test (Task 8).

---

### Task 4: Create MobileMenuSheet component

**File**: `frontend/src/components/shared/MobileMenuSheet.tsx` (new)  
**Depends on**: Task 1 (constants), Task 2 (animations)  
**Effort**: Medium-Large  

Bottom sheet that slides up when the Menu tab is tapped in the bottom nav. Contains grouped navigation links.

Key implementation details:
- Props: `isOpen: boolean`, `onClose: () => void`
- Import `NAV_MOBILE_MENU_GROUPS`, `NAV_LEGAL_LINKS` from constants
- Use the existing `FocusTrap` component for accessibility
- Render dimmed overlay behind sheet (click to dismiss)
- Sheet covers ~70% of viewport height, with rounded top corners
- Drag handle at top (decorative `div`)
- Group headers: uppercase, small, muted text
- Each link: icon + label, full-width tap target, navigates and auto-closes
- Legal links at bottom: inline, small text, separated by `·`
- `role="dialog"`, `aria-modal="true"`, `aria-label="Navigation menu"`
- Escape key closes (handled by FocusTrap)
- Animate in with `animate-sheet-up`, overlay with `animate-overlay-in`
- Use `usePathname()` for active state (purple text + left border)
- Use `useSession()` to conditionally show auth-gated items
- Prevent body scroll when open (`overflow: hidden` on body)

**Verification**: Renders standalone. Write test (Task 9).

---

### Task 5: Create BottomNav component

**File**: `frontend/src/components/shared/BottomNav.tsx` (new)  
**Depends on**: Task 1 (constants), Task 4 (MobileMenuSheet)  
**Effort**: Medium  

Fixed bottom navigation bar for mobile. 5 tabs with icons and labels.

Key implementation details:
- Import `NAV_MOBILE_TABS` from constants
- Only renders on mobile: entire component wrapped in a `div` with `md:hidden`
- Fixed to bottom: `fixed bottom-0 left-0 right-0 z-50`
- Height: 56px content + `env(safe-area-inset-bottom)` padding
- Background: `bg-bg-secondary/95 backdrop-blur-md border-t border-border-default`
- 5 equal-width columns: grid or flex
- Each tab: SVG icon (line-style) + text label
- Icons to use (inline SVG, not icon library):
  - Home: house icon
  - Watchlist: eye icon
  - Brief: newspaper icon
  - Portfolio: briefcase icon
  - Menu: hamburger (3 lines) / X (when sheet open)
- Active state: icon fills + purple color + label turns purple
- Home tab: red badge circle with `unseenCount` from `useSignalStore`
- Menu tab: toggles `MobileMenuSheet` open/closed
- `role="navigation"`, `aria-label="Main navigation"`
- `aria-current="page"` on active tab
- Use `usePathname()` for active detection
- Use `useSession()` — only render when authenticated
- For unauthenticated: don't render bottom nav at all (spec shows minimal top bar only)

Icon SVG paths (simple 24x24 viewBox):
- Home: `M3 12l9-8 9 8M5 10v10h4v-6h6v6h4V10`
- Eye: `M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8z` + circle r=3 at center
- Newspaper: `M4 4h16v16H4z` with internal lines
- Briefcase: standard briefcase path
- Menu: three horizontal lines

**Verification**: Write test (Task 8). Check with MobileMenuSheet integration.

---

### Task 6: Rewrite Navbar.tsx

**File**: `frontend/src/components/shared/Navbar.tsx`  
**Depends on**: Task 1 (constants)  
**Effort**: Large  

Major rewrite. The component structure changes significantly.

#### What to remove:
- `PRIMARY_LINKS` array (moved to constants)
- `MORE_LINKS` array (replaced by Research dropdown)
- `MOBILE_NAV_GROUPS` array (moved to constants, used by MobileMenuSheet)
- `PUBLIC_LINKS` array (moved to constants)
- `mobileOpen` state + hamburger button + mobile dropdown panel (replaced by BottomNav)
- Settings gear icon link (keep on desktop only, remove duplication)
- "More ▾" dropdown

#### What to add:
- Import `NAV_PRIMARY_LINKS`, `NAV_RESEARCH_LINKS`, `NAV_INFO_LINKS`, `NAV_PUBLIC_LINKS` from constants
- **5 primary desktop links** (Dashboard, Watchlist, Portfolio, Brief, Track Record) with active + badge states
- **"Research" dropdown**: click to toggle. Contains `NAV_RESEARCH_LINKS` above a divider, then `NAV_INFO_LINKS` below. Closes on outside click (reuse existing `moreRef` pattern). "Research" label turns purple when any child route is active.
- **Desktop right side**: NotificationCenter + Settings gear + User avatar/sign-out (unchanged pattern)
- **Mobile top bar simplification**: On `< md`, show only logo + NotificationCenter. No hamburger. No Settings gear (those are in bottom nav / menu sheet).
- **Unauthenticated desktop**: Show `NAV_PUBLIC_LINKS` (How It Works, Pricing) + Sign In button
- **Unauthenticated mobile**: Show only logo + Sign In link in top bar. No bottom nav rendered.

#### Active state logic for Research dropdown:
```typescript
const RESEARCH_ROUTES = ['/news', '/calendar', '/backtest', '/history', '/alerts', '/how-it-works', '/pricing'];
const isResearchActive = RESEARCH_ROUTES.includes(pathname);
```

When `isResearchActive`, the "Research" label gets `text-accent-purple`.

#### Desktop link active state:
- Active: `text-accent-purple bg-accent-purple/10 border-b-2 border-accent-purple`  
- Non-active: `text-text-secondary hover:text-text-primary hover:bg-white/[0.03]`

#### Badge logic (unchanged from current):
- Show red badge on Dashboard link when `unseenCount > 0` and Dashboard is not active page
- Cap at "9+"

**Verification**: Rewrite tests (Task 7). Visual check on desktop.

---

### Task 7: Update Navbar.test.tsx

**File**: `frontend/src/__tests__/Navbar.test.tsx`  
**Depends on**: Task 6 (Navbar rewrite)  
**Effort**: Medium  

Rewrite tests to match the new navigation structure.

#### Tests to update:
- "renders primary navigation links" → check for 5 links: Dashboard, Watchlist, Portfolio, Brief, Track Record
- "renders 'More' dropdown" → replace with "renders 'Research' dropdown" testing Research click → shows News, Calendar, Backtest, Signal History, Alerts + divider + How It Works, Pricing
- Remove test for Settings link via `getByLabelText('Settings')` in primary links area (settings is still a gear icon on desktop but no longer in dropdown)

#### Tests to add:
- "Research dropdown highlights when child route is active" — set `pathname = '/news'`, verify Research label has purple styling
- "mobile top bar shows only logo and notification bell" — verify no hamburger button, no Settings gear on mobile
- "does not render hamburger toggle on mobile" — the mobile menu is now handled by BottomNav, not Navbar

#### Tests to keep (with adjustments):
- Logo rendering — unchanged
- `aria-current` on active page — same logic, new link set
- Unseen badge on Dashboard — same logic
- Badge caps at 9+ — same logic
- Unauthenticated view — update to check for "How It Works" + "Pricing" (not just How It Works)
- Sign In button for visitors — unchanged

---

### Task 8: Write tests for new components

**Files**: `frontend/src/__tests__/BottomNav.test.tsx`, `frontend/src/__tests__/SiteFooter.test.tsx` (new)  
**Depends on**: Task 3 (SiteFooter), Task 5 (BottomNav)  
**Effort**: Medium  

#### BottomNav.test.tsx:
- Renders 5 tabs: Home, Watchlist, Brief, Portfolio, Menu
- Highlights active tab with `aria-current="page"`
- Shows unseen badge on Home tab when `unseenCount > 0` and not on Dashboard
- Badge caps at 9+
- Does not render when unauthenticated
- Has `role="navigation"` and `aria-label`
- Menu tab toggles MobileMenuSheet open state

#### SiteFooter.test.tsx:
- Renders Product column links (Dashboard, Watchlist, Portfolio, Brief, Track Record)
- Renders Research column links (News, Calendar, Backtest, Signal History)
- Renders Legal column links (Privacy, Terms, Refund Policy)
- Renders Contact link
- Renders SEBI disclaimer text
- Renders copyright
- Has `role="contentinfo"`

---

### Task 9: Write MobileMenuSheet tests

**File**: `frontend/src/__tests__/MobileMenuSheet.test.tsx` (new)  
**Depends on**: Task 4 (MobileMenuSheet)  
**Effort**: Medium  

Tests:
- Does not render when `isOpen=false`
- Renders grouped links when `isOpen=true` (Performance, Research, Account, About groups)
- Renders legal links at bottom
- Has `role="dialog"` and `aria-modal="true"`
- Calls `onClose` when overlay is clicked
- Active page shows purple text
- Does not render when unauthenticated

---

### Task 10: Update layout.tsx

**File**: `frontend/src/app/layout.tsx`  
**Depends on**: Task 3 (SiteFooter), Task 5 (BottomNav)  
**Effort**: Small  

Changes:
1. Import `BottomNav` and `SiteFooter`
2. Add `BottomNav` after `<main>` (before SiteFooter)
3. Add `SiteFooter` after BottomNav (before or replacing SebiDisclaimer)
4. Add bottom padding to `<main>` for mobile bottom nav clearance: `pb-[72px] md:pb-0`
5. **Decision on SebiDisclaimer**: The SiteFooter will include the SEBI disclaimer text. Remove the standalone `<SebiDisclaimer />` component render from layout to avoid duplication. Keep the component file in case it's used elsewhere.

New layout structure:
```tsx
<Navbar />
<OfflineBanner />
<main className="flex-1 pb-[72px] md:pb-0">{children}</main>
<BottomNav />
<SiteFooter />
<CookieConsent />
```

**Verification**: Full test suite passes. Visual check: desktop shows no bottom padding, mobile shows clearance for bottom nav.

---

### Task 11: Add navigation keyboard shortcuts

**File**: `frontend/src/hooks/useKeyboardShortcuts.ts`  
**Depends on**: Task 6 (Navbar has new routes to navigate to)  
**Effort**: Small  

Add two-key "G then letter" navigation shortcuts using `useRouter()`.

Implementation approach:
- Track a `pendingNavKey` state. When `g` is pressed, set `pendingNavKey = true` with a 1-second timeout.
- On the next keypress within that window, check for navigation letters:
  - `h` → `/` (Home)
  - `w` → `/watchlist`
  - `p` → `/portfolio`
  - `b` → `/brief`
  - `t` → `/track-record`
  - `n` → `/news`
- If no match within 1 second, reset.
- Only fire when not in INPUT/TEXTAREA/SELECT.

Add to `KEYBOARD_SHORTCUTS` array:
```typescript
{ key: 'G H', description: 'Go to Home' },
{ key: 'G W', description: 'Go to Watchlist' },
{ key: 'G P', description: 'Go to Portfolio' },
{ key: 'G B', description: 'Go to Brief' },
{ key: 'G T', description: 'Go to Track Record' },
{ key: 'G N', description: 'Go to News' },
```

The hook needs to accept a `router` (from `useRouter()`) or the caller passes navigation callbacks. Since the hook is used in the dashboard page component, the cleanest approach is to add an `onNavigate?: (path: string) => void` callback to `ShortcutCallbacks` and let the consuming component pass `router.push`.

**Verification**: Manual test of G-then-H navigating to dashboard. Existing shortcut tests still pass.

---

## Task Dependency Graph

```
Task 1 (constants) ─────┬──────────────────────────────────┐
                         │                                  │
Task 2 (CSS animations) ─┤                                  │
                         │                                  │
                         ├── Task 3 (SiteFooter) ──┐        │
                         │                         │        │
                         ├── Task 4 (MenuSheet) ───┤        │
                         │         │               │        │
                         │         ▼               │        │
                         ├── Task 5 (BottomNav) ───┤        │
                         │                         │        │
                         └── Task 6 (Navbar) ──────┤        │
                                    │              │        │
                                    ▼              │        │
                              Task 7 (Navbar       │        │
                               tests)             │        │
                                                   │        │
                              Task 8 (BottomNav +  │        │
                               SiteFooter tests) ──┤        │
                                                   │        │
                              Task 9 (MenuSheet    │        │
                               tests) ────────────┤        │
                                                   │        │
                                                   ▼        │
                                            Task 10 (layout)│
                                                            │
                                            Task 11 (kbd    │
                                             shortcuts) ────┘
```

**Parallelizable**: Tasks 1 + 2 can be done simultaneously. Tasks 3, 4, 6 can be done in parallel after 1+2. Task 5 depends on Task 4. Tasks 7, 8, 9 can be done in parallel after their respective components. Task 10 waits for 3 + 5. Task 11 is independent of layout changes.

---

## Recommended Execution Order

| Step | Tasks | Rationale |
|------|-------|-----------|
| 1 | Task 1 + Task 2 | Foundation: constants + CSS. No functional change. Tests pass. |
| 2 | Task 3 (SiteFooter) | Standalone component, no dependencies on other new components. |
| 3 | Task 4 (MobileMenuSheet) | Standalone component, uses FocusTrap and constants. |
| 4 | Task 5 (BottomNav) | Imports MobileMenuSheet, renders it internally. |
| 5 | Task 6 (Navbar rewrite) | The big change. Desktop nav restructured. Mobile simplified. |
| 6 | Task 7 + Task 8 + Task 9 | All tests for all changed/new components. |
| 7 | Task 10 (layout.tsx) | Wire everything together. Remove SebiDisclaimer duplication. |
| 8 | Task 11 (keyboard shortcuts) | Polish: navigation shortcuts. |

After each step, run `npx vitest run` to ensure no regressions.

---

## Risk & Edge Cases

| Risk | Mitigation |
|------|-----------|
| Bottom nav overlaps page content on mobile | `pb-[72px] md:pb-0` on `<main>`. Verify on pages with sticky footers or FABs. |
| Bottom sheet body scroll bleed | Set `document.body.style.overflow = 'hidden'` when sheet is open, restore on close. Use cleanup in `useEffect`. |
| z-index conflicts (bottom nav vs modals/toasts) | Bottom nav: `z-50`. Menu sheet overlay: `z-50`. Toasts already use `z-50`+. Verify no overlap. If conflict, menu sheet overlay should be `z-[60]`. |
| SebiDisclaimer removal breaks existing tests | Search for `SebiDisclaimer` in tests. If tested directly, update. The text content moves to SiteFooter. |
| iOS safe area on bottom nav | Use `env(safe-area-inset-bottom)` in padding. Test on iPhone Safari viewport. |
| Research dropdown active detection | `pathname.startsWith` won't work for `/` (would match everything). Use exact `RESEARCH_ROUTES.includes(pathname)` array check. |
| Keyboard shortcut "G" conflicts | Only activate when not in input fields. The 1-second timeout prevents accidental triggers. Cancel pending if Escape is pressed. |
| Unauthenticated users see bottom nav briefly during SSR | BottomNav checks `useSession()` status. Use `status === 'authenticated'` guard. During `loading`, don't render. |

---

## Files Changed Summary

| Action | File |
|--------|------|
| **Modify** | `frontend/src/lib/constants.ts` |
| **Modify** | `frontend/src/app/globals.css` |
| **Create** | `frontend/src/components/shared/SiteFooter.tsx` |
| **Create** | `frontend/src/components/shared/MobileMenuSheet.tsx` |
| **Create** | `frontend/src/components/shared/BottomNav.tsx` |
| **Modify** | `frontend/src/components/shared/Navbar.tsx` |
| **Modify** | `frontend/src/__tests__/Navbar.test.tsx` |
| **Create** | `frontend/src/__tests__/BottomNav.test.tsx` |
| **Create** | `frontend/src/__tests__/MobileMenuSheet.test.tsx` |
| **Create** | `frontend/src/__tests__/SiteFooter.test.tsx` |
| **Modify** | `frontend/src/app/layout.tsx` |
| **Modify** | `frontend/src/hooks/useKeyboardShortcuts.ts` |

Total: 5 new files, 7 modified files. Backend untouched. No database changes.

---

## Verification Checklist

After all tasks complete:

- [ ] `npx vitest run` — all frontend tests pass (existing + new)
- [ ] `docker compose build` — frontend Docker build succeeds (no TS errors)
- [ ] Desktop: 5 primary links visible, Research dropdown works, active states correct
- [ ] Desktop: Settings gear + NotificationCenter + avatar all functional
- [ ] Desktop: Unauthenticated view shows How It Works + Pricing + Sign In
- [ ] Mobile: Bottom nav shows 5 tabs, active state highlights correctly
- [ ] Mobile: Menu tab opens bottom sheet with grouped links
- [ ] Mobile: Navigating from menu sheet closes it and routes correctly
- [ ] Mobile: Top bar shows only logo + notification bell
- [ ] Mobile: Bottom nav not visible when logged out
- [ ] Footer: All 4 columns render, SEBI disclaimer present, legal links work
- [ ] Footer: No duplicate SEBI disclaimer (SebiDisclaimer removed from layout)
- [ ] Keyboard: G+H navigates to dashboard, G+W to watchlist, etc.
- [ ] Accessibility: `role`, `aria-label`, `aria-current`, `aria-modal` all present
- [ ] No z-index conflicts between bottom nav, menu sheet, toasts, and modals

---

*Plan complete. Ready for implementation.*
