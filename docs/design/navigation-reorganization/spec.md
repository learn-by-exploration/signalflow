# Navigation Reorganization — Design Spec

> **Status**: Draft  
> **Author**: Claude (Brainstorm Agent)  
> **Date**: 27 March 2026  
> **Version**: v1  

---

## 1. Problem Statement

SignalFlow AI has 16 user-facing pages, but the current Navbar only exposes 6. Ten pages — including high-value daily-use features like Portfolio, Watchlist, Brief, News, and Calendar — are completely unreachable from navigation. A user who doesn't know the URL cannot discover them.

**Current Navbar:**
- 3 primary links: Dashboard, Track Record, Alerts
- 3 in "More" dropdown: Signal History, How It Works, Settings
- 1 gear icon: Settings (duplicated)

**Missing from navigation:** Portfolio, Watchlist, Brief, News, Calendar, Backtest, Pricing + 4 legal pages.

The navigation was over-simplified in a previous sprint. This spec designs the optimal navigation structure for all pages.

---

## 2. User Persona & Workflow

**Primary user**: Finance professional (M.Com), beginning active trading. Checks the app on her phone during market hours, reviews signals, logs trades, reads AI briefings.

### Daily Workflow (the "trading loop")

| Time | Action | Page(s) Used |
|------|--------|-------------|
| 8:00 AM | Read morning AI briefing | **Brief** |
| 9:15 AM | Check signals, review watchlist | **Dashboard**, **Watchlist** |
| During market | New signal alert → view detail | **Signal Detail** (via push/card) |
| During market | Log a trade based on signal | **Portfolio** |
| During market | Check relevant news | **News** |
| 4:00 PM | Read evening wrap | **Brief** |
| Evening | Review track record, history | **Track Record**, **Signal History** |
| Weekly | Check upcoming events, backtest | **Calendar**, **Backtest** |
| Rare | Configure alerts, settings | **Alerts**, **Settings** |
| One-time | See pricing, how it works | **Pricing**, **How It Works** |

### Key Insight

**Dashboard, Watchlist, Brief, and Portfolio are daily-use pages** — they must be reachable in 1 tap on mobile and 1 click on desktop. Track Record is checked daily-to-weekly. Everything else is secondary or tertiary.

---

## 3. Page Inventory & Classification

### Tier 1 — Primary (1-tap access, every session)

| Page | Route | Daily Use | Why Primary |
|------|-------|-----------|-------------|
| Dashboard | `/` | Every session | Signal feed, market overview — the home base |
| Watchlist | `/watchlist` | Every session | Personalized symbol tracker — "my stocks" |
| Brief | `/brief` | 2x daily | AI morning/evening briefings — unique value prop |
| Portfolio | `/portfolio` | Every session | Trade log, P&L — tracks her actual trading |
| Track Record | `/track-record` | Daily–weekly | Win rate, accuracy — builds trust in signals |

### Tier 2 — Secondary (accessible from nav, used weekly+)

| Page | Route | Usage | Access Pattern |
|------|-------|-------|----------------|
| News | `/news` | Several times/week | Market context, causal event chains |
| Calendar | `/calendar` | Weekly | Upcoming earnings, RBI decisions |
| Backtest | `/backtest` | Weekly | Test strategies against history |
| Signal History | `/history` | Weekly | Browse resolved signals, outcomes |
| Alerts | `/alerts` | Occasional | Configure notification preferences |

### Tier 3 — Tertiary (accessible from menu/footer, infrequent)

| Page | Route | Usage | Access Pattern |
|------|-------|-------|----------------|
| Settings | `/settings` | Rare | Theme, text size, currency |
| How It Works | `/how-it-works` | One-time | Educational, onboarding |
| Pricing | `/pricing` | One-time | Subscription conversion |

### Tier 4 — Legal (footer only, never in main nav)

| Page | Route |
|------|-------|
| Privacy Policy | `/privacy` |
| Terms of Service | `/terms` |
| Refund Policy | `/refund-policy` |
| Contact | `/contact` |

### Not in Navigation (accessed via context)

| Page | Route | Access Pattern |
|------|-------|----------------|
| Signal Detail | `/signal/[id]` | Click signal card from Dashboard/Watchlist/History |
| Shared Signal | `/shared/[id]` | External link (shareable URL) |
| Sign In | `/auth/signin` | Auth flow, CTA buttons |

---

## 4. Recommended Navigation Structure

### 4.1 Design Principles

1. **5 primary tabs** on mobile bottom nav (industry standard: Robinhood, Zerodha, Groww all use 5)
2. **5-7 visible links** on desktop top bar (within cognitive load research limits)
3. **Grouped "More" menu** for secondary pages (not a flat dropdown)
4. **Legal pages in footer only** — never pollute main navigation
5. **No duplication** — Settings appears once (gear icon), not in dropdown AND icon
6. **Notification badge** on Dashboard tab and bell icon — for new signals

### 4.2 Desktop Navigation (Top Bar)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [SignalFlow AI]   Dashboard  Watchlist  Portfolio  Brief  Track Record   [Research ▾]   [🔔] [⚙️] [👤]  │
└──────────────────────────────────────────────────────────────────────┘
```

**Primary links (always visible):** 5 items
1. **Dashboard** `/` — Home, signal feed
2. **Watchlist** `/watchlist` — Tracked symbols
3. **Portfolio** `/portfolio` — Trades, P&L
4. **Brief** `/brief` — AI market briefings
5. **Track Record** `/track-record` — Signal performance

**"Research" dropdown** (grouped secondary items): 5 items
```
┌─────────────────────┐
│ 📰 News             │
│ 📅 Calendar         │
│ 🔬 Backtest         │
│ 📜 Signal History   │
│ 🔔 Alerts           │
├─────────────────────┤
│ ❓ How It Works     │
│ 💎 Pricing          │
└─────────────────────┘
```

**Icon actions (right side):**
- 🔔 Notification bell — links to in-app notification center (already exists as `NotificationCenter` component)
- ⚙️ Settings gear — links to `/settings`
- 👤 User avatar — shows name, sign out option

### 4.3 Mobile Navigation (Bottom Bar + Drawer)

**Bottom navigation bar** (fixed, always visible): 5 tabs

```
┌──────────────────────────────────────────────┐
│  🏠        👁        📰        💼        ☰   │
│ Home    Watchlist   Brief   Portfolio   Menu  │
└──────────────────────────────────────────────┘
```

| Tab | Icon | Route | Badge |
|-----|------|-------|-------|
| Home | 🏠 (house) | `/` | Red dot + count for unseen signals |
| Watchlist | 👁 (eye) | `/watchlist` | — |
| Brief | 📰 (newspaper) | `/brief` | Blue dot when new brief available |
| Portfolio | 💼 (briefcase) | `/portfolio` | — |
| Menu | ☰ (hamburger) | Opens drawer | Red dot if unseen items in sub-pages |

**Mobile top bar** (simplified):
```
┌──────────────────────────────────────┐
│ [SignalFlow AI]              [🔔]    │
└──────────────────────────────────────┘
```

Only logo + notification bell on mobile top bar. No hamburger (that's in bottom nav). No settings icon (it's in the Menu drawer).

**Menu drawer** (slides up from bottom on mobile — "bottom sheet" pattern):

```
┌─────────────────────────────────────┐
│ ──── (drag handle)                  │
│                                     │
│ ── Performance ──                   │
│ 📊  Track Record                    │
│ 📜  Signal History                  │
│                                     │
│ ── Research ──                      │
│ 📰  News                           │
│ 📅  Calendar                       │
│ 🔬  Backtest                       │
│                                     │
│ ── Account ──                       │
│ 🔔  Alert Settings                 │
│ ⚙️  Settings                       │
│                                     │
│ ── About ──                         │
│ ❓  How It Works                    │
│ 💎  Pricing                        │
│                                     │
│ ─────────────────────               │
│ Privacy · Terms · Refund · Contact  │
└─────────────────────────────────────┘
```

### 4.4 Footer (All Layouts)

The footer appears on every page (via `SebiDisclaimer` component and a new site-wide footer). Legal pages live here exclusively.

```
┌─────────────────────────────────────────────────────────────┐
│ [SignalFlow AI]                                             │
│                                                             │
│ Product          Research         Legal          Support    │
│ Dashboard        News             Privacy        Contact   │
│ Watchlist        Calendar         Terms          Help      │
│ Portfolio        Backtest         Refund Policy             │
│ Brief            Signal History                             │
│ Track Record                                                │
│                                                             │
│ ⚠️ AI-generated analysis for educational purposes only.    │
│ Not financial advice. Always consult a qualified advisor.   │
│                                                             │
│ © 2026 SignalFlow AI                                        │
└─────────────────────────────────────────────────────────────┘
```

On mobile, the footer collapses to a simpler layout (single column, all links).

---

## 5. Rationale & Design Decisions

### 5.1 Why These 5 Primary Pages?

**Decision**: Dashboard, Watchlist, Portfolio, Brief, Track Record

**Alternatives considered:**

| Option | Bottom Nav Items | Rejected Because |
|--------|-----------------|-----------------|
| A: Include Alerts | Dashboard, Watchlist, Portfolio, Alerts, Menu | Alerts is a config page, not daily use. Notification bell handles alert viewing. |
| B: Include News | Dashboard, Watchlist, News, Portfolio, Menu | News is context, not action. Brief subsumes the "what happened" need. |
| C: Include Track Record | Dashboard, Watchlist, Brief, Track Record, Menu | Dropped Portfolio — but Portfolio is where she *logs trades*, which is the core action loop. |
| **D: Selected** | Dashboard, Watchlist, Brief, Portfolio, Menu | Track Record moves to Menu. It's important but checked less than Brief/Portfolio. |

**The "trading action loop" test**: Every page in the bottom nav should be part of the daily trading workflow:
1. See signals (Dashboard) → 2. Check my symbols (Watchlist) → 3. Read AI analysis (Brief) → 4. Log trade (Portfolio)

Track Record is a *review* page, not an *action* page. It belongs 1 tap into Menu, not in the primary bar.

### 5.2 Why "Research" Instead of "More" on Desktop?

"More" is vague and uninviting. "Research" communicates that these are analysis and knowledge tools — which is exactly what News, Calendar, Backtest, and History are. This also aligns with the user's M.Com background; she's comfortable with "research" as a concept.

**Alternative labels considered:** "Explore", "Tools", "Analyze", "More"  
**Chosen**: "Research" — specific, professional, matches the content

### 5.3 Why Bottom Sheet Instead of Side Drawer for Mobile Menu?

| Pattern | Pros | Cons |
|---------|------|------|
| Side drawer (hamburger from left) | Familiar, large area | Thumb reach on large phones is awkward; feels like legacy pattern |
| Bottom sheet (slides up) | Natural thumb reach, modern (used by Google Maps, Apple Maps, trading apps), progressive disclosure via partial/full height | Less horizontal space for content |
| Full-screen overlay | Maximum space | Heavy, disruptive |

**Decision**: Bottom sheet. It's the modern mobile pattern for "more options" when triggered from a bottom nav bar. The drawer slides up partially (showing ~60% of screen), and can be pulled to full height. Tapping outside or swiping down dismisses it.

### 5.4 Why Isn't Pricing in Primary Navigation?

Pricing is a **conversion page**, not a **daily-use page**. Putting it in primary nav makes the app feel like a sales tool rather than a trading tool. Pricing should be:
- Accessible from the Menu drawer
- Linked from feature-gated CTAs ("Upgrade to Pro for Backtest")
- Present in the footer
- Shown on the landing page (unauthenticated view)

### 5.5 Why Alerts Moved from Primary to Secondary?

In the current Navbar, Alerts is a primary link. But examining usage patterns:
- **Configuring alerts** is done once, then rarely changed
- **Viewing alerts** happens via the notification bell (NotificationCenter component) and push notifications
- The `/alerts` page is primarily a **settings page** for alert preferences

Moving it to the "Research" dropdown (desktop) and Menu drawer (mobile) is appropriate. The notification bell remains in the top bar for instant access to recent alerts.

### 5.6 Pages That Could Be Merged (Future Consideration)

| Candidate | Merge Into | Rationale | Recommendation |
|-----------|-----------|-----------|----------------|
| News + Calendar | "Market Intel" page with tabs | Both provide market context | **Maybe later** — they serve different time horizons (past events vs upcoming events). Keep separate for now, but group them together in nav. |
| Track Record + Signal History | Combined with tab switcher | Both show signal outcomes | **No** — Track Record is statistics/charts, History is a browsable list. Different mental models. |
| Brief + News | "Insights" page | Both are information consumption | **No** — Brief is personalized AI analysis, News is raw market events. Very different UX. |
| Alerts + Settings | Combined settings page | Both are configuration | **Maybe** — but Alerts has enough depth (watchlist, preferences, quiet hours) to justify its own page. |

**Recommendation**: No merges in this iteration. The grouping in navigation already provides logical association. Merging pages adds implementation complexity without clear UX benefit.

---

## 6. Detailed Wireframes (Text-Based)

### 6.1 Desktop Top Bar — Authenticated User

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [SignalFlow AI]                                                            │
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────┐ ┌──────────────┐        │
│  │Dashboard │ │Watchlist │ │Portfolio  │ │Brief  │ │Track Record  │        │
│  │  (active)│ │          │ │           │ │       │ │              │        │
│  └──────────┘ └──────────┘ └───────────┘ └───────┘ └──────────────┘        │
│     ▔▔▔▔▔▔                                                                  │
│  (purple underline on active)                                 [Research ▾]  │
│                                                                             │
│                                                        [🔔•] [⚙️] [S ▾]   │
│                                                         │          │        │
│                                                    notification  avatar +   │
│                                                      bell       sign out    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Active state**: Purple text + purple underline + subtle purple background tint  
**Hover state**: Text brightens from `text-secondary` to `text-primary` + faint bg  
**Badge**: Red circle with count on Dashboard tab when unseen signals > 0

### 6.2 Desktop "Research" Dropdown — Open State

```
                                              ┌─────────────────────┐
                                              │                     │
                        Research ▾  ──────►   │  📰  News           │
                                              │  📅  Calendar       │
                                              │  🔬  Backtest       │
                                              │  📜  Signal History │
                                              │  🔔  Alerts         │
                                              │─────────────────────│
                                              │  ❓  How It Works   │
                                              │  💎  Pricing        │
                                              │                     │
                                              └─────────────────────┘
```

**Divider**: A thin line separates daily-use secondary pages from informational pages (How It Works, Pricing). This prevents Pricing from feeling like a core feature.

**Hover**: Same pattern as primary links — text brightens + faint bg.  
**Active indicator**: Purple text when current page is within this dropdown. The "Research" label itself also turns purple to signal "you're in this group."

### 6.3 Mobile Bottom Navigation Bar

```
Phone screen (375px):

┌─────────────────────────────────────┐
│                                     │
│  (page content fills here)          │
│                                     │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  🏠       👁       📰      💼    ☰  │
│ Home   Watch-   Brief  Port-  Menu  │
│         list          folio         │
│                                     │
│  ▔▔▔▔                              │
│ (purple indicator under active tab) │
└─────────────────────────────────────┘
```

**Tab icons**: Simple line icons (not filled). Active tab gets filled icon + purple color.  
**Labels**: Always visible (not icon-only). 4-6 character labels to fit 5 columns on 375px.  
**Safe area**: Bottom bar respects iOS safe area inset (env(safe-area-inset-bottom)).  
**Height**: 56px content + safe area padding.  
**Badge on Home**: Red circle with number (same as desktop).

### 6.4 Mobile Top Bar

```
┌─────────────────────────────────────┐
│                                     │
│  [SignalFlow AI]          [🔔•]     │
│                                     │
└─────────────────────────────────────┘
```

**Simplified**: Logo left, notification bell right. No hamburger (bottom nav handles it). No settings icon.  
**Height**: 48px (compact, maximizes content area).  
**Sticky**: Fixed to top with backdrop blur, same as current implementation.

### 6.5 Mobile Menu — Bottom Sheet

```
(Triggered by tapping ☰ Menu in bottom nav)

┌─────────────────────────────────────┐
│                                     │  ← dimmed overlay
│                                     │
│                                     │
├─────────────────────────────────────┤
│           ── (drag handle) ──       │
│                                     │
│  ── Performance ──────────────────  │
│  📊  Track Record              →   │
│  📜  Signal History            →   │
│                                     │
│  ── Research ─────────────────────  │
│  📰  News                      →   │
│  📅  Calendar                  →   │
│  🔬  Backtest                  →   │
│                                     │
│  ── Account ──────────────────────  │
│  🔔  Alert Settings            →   │
│  ⚙️  Settings                 →   │
│                                     │
│  ── About ────────────────────────  │
│  ❓  How It Works              →   │
│  💎  Pricing                   →   │
│                                     │
│  ─────────────────────────────────  │
│  Privacy · Terms · Refund · Contact │
│                                     │
│  🏠       👁       📰      💼    ☰  │
│ Home   Watch-   Brief  Port-  Menu  │
│         list          folio         │
└─────────────────────────────────────┘
```

**Behavior**:
- Slides up from bottom, covering ~70% of screen height
- Dimmed overlay behind (tapping dismisses)
- Swipe down to dismiss
- Menu tab in bottom bar shows "X" (close) icon while sheet is open
- Navigating to a page auto-closes the sheet
- Group headers are muted, uppercase, small text (same pattern as current mobile drawer)
- Legal links at bottom in small, inline text — not prominent, just accessible

### 6.6 Desktop Navigation — Unauthenticated User

```
┌──────────────────────────────────────────────────────────────┐
│  [SignalFlow AI]     How It Works    Pricing       [Sign In] │
└──────────────────────────────────────────────────────────────┘
```

Minimal nav for logged-out users. No need to show Dashboard/Watchlist/etc since they can't use them without auth. "Sign In" is a primary CTA button (purple background).

---

## 7. Interaction Details

### 7.1 Notification Badge Logic

| Location | Triggers | Display |
|----------|----------|---------|
| Home/Dashboard tab | `unseenCount > 0` from `signalStore` | Red circle with count (max "9+") |
| 🔔 Notification bell | Any unread notification | Red dot (no count) |
| Menu tab (mobile) | Any unread item in sub-pages (e.g., new brief available) | Small red dot |
| Brief tab (mobile) | New brief generated since last visit | Blue dot |

### 7.2 Active State Indicators

| Component | Active Indicator |
|-----------|-----------------|
| Desktop primary link | Purple text + `bg-accent-purple/10` + 2px bottom border |
| Desktop "Research" dropdown | "Research" label turns purple when any child page is active |
| Mobile bottom tab | Filled icon + purple color + label turns purple |
| Mobile menu sheet item | Purple text + left accent bar |

### 7.3 Keyboard Shortcuts (Desktop)

Extend existing keyboard shortcuts to include navigation:

| Shortcut | Action |
|----------|--------|
| `G then H` | Go to Home (Dashboard) |
| `G then W` | Go to Watchlist |
| `G then P` | Go to Portfolio |
| `G then B` | Go to Brief |
| `G then T` | Go to Track Record |
| `G then N` | Go to News |
| `?` | Open keyboard shortcut help (existing) |

Two-key shortcuts (press G, then the letter) avoid conflicting with browser shortcuts.

### 7.4 Responsive Breakpoints

| Breakpoint | Layout |
|------------|--------|
| ≥ 768px (md) | Desktop top bar. No bottom nav. Full "Research" dropdown. |
| < 768px | Mobile bottom nav + simplified top bar. Menu opens bottom sheet. |

The 768px breakpoint matches the existing `md:` Tailwind breakpoint used throughout the app for `hidden md:flex` patterns.

---

## 8. Implementation Notes

### 8.1 Files to Modify

| File | Change |
|------|--------|
| `frontend/src/components/shared/Navbar.tsx` | Major rewrite: new link arrays, desktop "Research" dropdown, remove "More" dropdown, remove Settings duplication |
| **New**: `frontend/src/components/shared/BottomNav.tsx` | New component: mobile bottom navigation bar (5 tabs) |
| **New**: `frontend/src/components/shared/MobileMenuSheet.tsx` | New component: bottom sheet drawer with grouped menu items |
| **New**: `frontend/src/components/shared/SiteFooter.tsx` | New component: full site footer with column layout |
| `frontend/src/app/layout.tsx` | Add BottomNav + SiteFooter. Adjust main content padding for bottom nav on mobile. |
| `frontend/src/app/globals.css` | Add `pb-[72px] md:pb-0` to main content area for bottom nav spacing |

### 8.2 Component Architecture

```
layout.tsx
├── Navbar (top bar — responsive desktop/mobile)
├── main (page content)
│   └── (padding-bottom on mobile for bottom nav clearance)
├── BottomNav (mobile only, fixed bottom)
│   └── MobileMenuSheet (rendered inside, shown/hidden)
├── SiteFooter (full-width footer)
└── SebiDisclaimer (existing, keep as-is or merge into SiteFooter)
```

### 8.3 Data Constants

```typescript
// Navigation configuration (single source of truth)

const PRIMARY_DESKTOP_LINKS = [
  { href: '/', label: 'Dashboard', icon: 'home' },
  { href: '/watchlist', label: 'Watchlist', icon: 'eye' },
  { href: '/portfolio', label: 'Portfolio', icon: 'briefcase' },
  { href: '/brief', label: 'Brief', icon: 'newspaper' },
  { href: '/track-record', label: 'Track Record', icon: 'chart' },
];

const RESEARCH_DROPDOWN_LINKS = [
  { href: '/news', label: 'News', icon: '📰' },
  { href: '/calendar', label: 'Calendar', icon: '📅' },
  { href: '/backtest', label: 'Backtest', icon: '🔬' },
  { href: '/history', label: 'Signal History', icon: '📜' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
];

const INFO_LINKS = [
  { href: '/how-it-works', label: 'How It Works', icon: '❓' },
  { href: '/pricing', label: 'Pricing', icon: '💎' },
];

const MOBILE_BOTTOM_TABS = [
  { href: '/', label: 'Home', icon: 'home' },
  { href: '/watchlist', label: 'Watchlist', icon: 'eye' },
  { href: '/brief', label: 'Brief', icon: 'newspaper' },
  { href: '/portfolio', label: 'Portfolio', icon: 'briefcase' },
  { id: 'menu', label: 'Menu', icon: 'menu' },
];

const MOBILE_MENU_GROUPS = [
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

const LEGAL_LINKS = [
  { href: '/privacy', label: 'Privacy' },
  { href: '/terms', label: 'Terms' },
  { href: '/refund-policy', label: 'Refund Policy' },
  { href: '/contact', label: 'Contact' },
];
```

### 8.4 Accessibility Requirements

- Bottom nav must have `role="navigation"` and `aria-label="Main navigation"`
- Active tab: `aria-current="page"`
- Menu sheet: `role="dialog"` with `aria-modal="true"`, focus trap when open
- Escape key closes menu sheet and Research dropdown
- All icons must have `aria-hidden="true"` with text labels visible
- Tab order: top bar → page content → bottom bar (skip bottom bar content when sheet is closed)

### 8.5 Animation Specifications

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Bottom sheet open | Slide up from bottom | 300ms | `ease-out` |
| Bottom sheet close | Slide down | 200ms | `ease-in` |
| Overlay appear | Fade in | 200ms | `ease-out` |
| Research dropdown open | Fade in + slide down 4px | 150ms | `ease-out` |
| Tab switch (bottom nav) | No animation on icon swap; page transition handled by Next.js | — | — |

---

## 9. Migration from Current Navigation

### What Changes

| Before | After |
|--------|-------|
| 3 primary links (Dashboard, Track Record, Alerts) | 5 primary links (Dashboard, Watchlist, Portfolio, Brief, Track Record) |
| "More" dropdown (History, How It Works, Settings) | "Research" dropdown (News, Calendar, Backtest, History, Alerts + How It Works, Pricing) |
| Settings duplicated (dropdown + gear icon) | Settings in gear icon only (desktop) or Menu drawer (mobile) |
| Alerts as primary link | Alerts moves to Research dropdown / Menu drawer |
| No mobile bottom nav | New 5-tab mobile bottom nav |
| Mobile hamburger opens side dropdown | Mobile Menu tab opens bottom sheet |
| No footer links | Full site footer with columns |

### What Stays the Same

- Logo / brand in top left
- Notification bell icon (right side)
- Settings gear icon (desktop, right side)
- User avatar + sign out (desktop, right side)
- Desktop breakpoint at `md` (768px)
- Active state color (purple accent)
- Unauthenticated view shows minimal nav

---

## 10. Open Questions

1. **Should Brief show a "new brief" indicator?** The morning and evening briefs are generated on schedule. We could show a blue dot on the Brief tab when a new brief is available that the user hasn't seen. Needs a "last seen" timestamp in local storage.

2. **Should the menu sheet show user profile info?** Some apps show the user avatar/name/email at the top of the menu drawer. Could be useful for account context but adds visual weight.

3. **Should Pricing be hidden for paid users?** Once subscribed, the Pricing page is less relevant. Could replace with "Manage Subscription" or remove entirely from paid users' navigation.

4. **Should we add a search/command palette?** A `Cmd+K` / `Ctrl+K` command palette could provide instant access to any page, any symbol, any signal. This is a power-user feature that could complement the navigation restructure. Out of scope for this spec but worth considering.

---

## 11. Success Criteria

| Metric | Target |
|--------|--------|
| All 16 pages reachable from navigation or footer | 100% (currently ~37%) |
| Primary pages reachable in ≤1 tap (mobile) | 5 pages (Dashboard, Watchlist, Brief, Portfolio + Menu for rest) |
| Time to reach any secondary page from any page | ≤2 taps (1 tap Menu + 1 tap page) |
| Mobile bottom nav thumb reach | All 5 tabs within natural thumb zone |
| No navigation items removed vs current | Alerts, Track Record, History, How It Works all still accessible |
| Lighthouse accessibility score | ≥90 (proper ARIA, focus management) |

---

*Spec complete. Ready for implementation planning.*
