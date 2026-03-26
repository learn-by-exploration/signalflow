# Settings & User Configuration — Multi-Expert Review

> **Date**: 26 March 2026  
> **Scope**: All settings, preferences, alert config, and user configuration surfaces  
> **Reviewers**: UX Expert, Security Expert, Finance/PM Expert  
> **Version**: v1.0.0 (post-auth system)

---

## Executive Summary

The settings system is **functional but skeletal**. It covers basics (market filter, confidence slider, signal types) but misses the depth expected by even a beginner Indian retail trader. The backend has strong bones (market hours, quiet hours schema, watchlist validation) but the frontend settings surface barely scratches what's available.

| Expert | Overall Score | Grade |
|--------|--------------|-------|
| UX Expert | 4.8/10 | D+ |
| Security Expert | 6.0/10 | C |
| Finance/PM Expert | 3.3/10 | F |
| **Combined** | **4.7/10** | **D+** |

---

## Part 1: UX Expert Review (4.8/10)

### 1.1 Information Architecture — 4/10

**Findings:**
- Settings fragmented across **4 separate surfaces**: `/settings` page, `/alerts` page, `SettingsPanel` modal (dead code), and `AlertConfigModal`
- `SettingsPanel` component is exported and tested but **never imported or rendered anywhere** — dead code
- No single entry point for "all my preferences"
- Settings page has 6 sections (Account, Display, Signals, Notifications, Telegram, Reset) but alert preferences live on a completely different page

**Recommendations:**
- Consolidate into a single settings hub with tabbed navigation
- Remove or integrate `SettingsPanel` dead code
- Add cross-links between settings and alerts pages

### 1.2 Discoverability — 5/10

**Findings:**
- Settings is buried in the "More" dropdown in the navbar — not a top-level nav item
- No breadcrumb or back-navigation from settings sub-sections
- Watchlist is hidden in a secondary column on the alerts page
- Price alerts section has no link from signal cards

**Recommendations:**
- Promote settings to top-level navigation (gear icon)
- Add contextual links: signal card → price alert, signal card → watchlist add

### 1.3 Progressive Disclosure — 6/10

**Findings:**
- Confidence presets (60/70/80/90) are a good progressive disclosure pattern
- But no "recommended" badge on any preset — beginner doesn't know which to pick
- Symbol input on watchlist/price alerts is free-text — needs autocomplete from tracked symbols
- View mode options (Simple/Standard) have cryptic descriptions

**Recommendations:**
- Add "Recommended" badge on 70% confidence preset
- Symbol autocomplete dropdown for all symbol inputs
- Clearer view mode descriptions with visual previews

### 1.4 Feedback & Confirmation — 4/10

**Findings:**
- **No confirmation dialog on "Reset to Defaults"** — destructive action with no guard
- Settings page auto-saves on every interaction — no dirty-state indicator
- Alerts page has explicit "Save Preferences" button — inconsistent with settings page pattern
- `animate-pulse` used for "saved" feedback — wrong semantic (pulse implies ongoing activity, not completion)

**Recommendations:**
- Add confirmation modal before reset: "This will clear all your preferences. Continue?"
- Unified save pattern: either auto-save everywhere or explicit save everywhere
- Use `animate-bounce` or a checkmark toast for save confirmation

### 1.5 Mobile Usability — 5/10

**Findings:**
- Watchlist remove buttons use `opacity-0 group-hover:opacity-100` — **invisible on touch devices** (no hover state on mobile)
- Toggle switches are appropriately sized for touch
- Signal type toggles in alerts page have adequate spacing
- Price alert cards stack correctly on mobile

**Recommendations:**
- Replace hover-reveal delete buttons with always-visible icon buttons or swipe-to-delete
- Ensure all touch targets are ≥44px (WCAG 2.5.5)

### 1.6 Consistency — 5/10

**Findings:**
- **Mixed save patterns**: Settings auto-saves per interaction; Alerts requires explicit "Save Preferences" click
- **Mixed storage**: `preferencesStore` uses `localStorage` (persists); `userStore` uses `sessionStorage` (lost on tab close)
- `chatId` stored in `sessionStorage` — **bug**: user loses Telegram connection on tab close and must re-enter
- Color tokens are consistent (signal-buy green, signal-sell red)

**Recommendations:**
- Standardize on one save pattern across all settings surfaces
- Move `chatId` from `sessionStorage` to `localStorage`
- Document the storage strategy (what goes where and why)

### 1.7 Onboarding Flow — 4/10

**Findings:**
- `WelcomeModal` appears on first visit but doesn't guide user to configure settings
- No setup checklist ("Set your markets → Set confidence → Connect Telegram")
- No "getting started" wizard or first-run experience for settings
- User must discover settings organically — no prompts or nudges

**Recommendations:**
- Add post-welcome guided tour to key settings
- Setup checklist component with progress indicator
- "Configure your alerts" CTA on the dashboard for new users

### 1.8 Accessibility — 5/10

**Findings:**
- Toggle buttons missing `aria-pressed` attribute
- No `role="group"` on toggle button groups (market toggles, signal type toggles)
- Confidence slider missing `aria-valuetext` (screen reader would read raw number without context)
- Color-only state indicators (red/green toggles) — no icon or text differentiation
- Tab navigation works but focus ring styling is inconsistent

**Recommendations:**
- Add `aria-pressed` to all toggle buttons
- Add `role="group"` with `aria-label` to toggle groups
- Add `aria-valuetext` to slider: "Minimum confidence: 70 percent"
- Add icon indicators alongside color changes (checkmark for on, X for off)

---

## Part 2: Security Expert Review (6.0/10)

### 2.1 Authentication Security — 6/10

**Findings:**
- **[MEDIUM] NextAuth session embeds raw backend JWTs with no refresh mechanism.** Backend access token expires in 30 minutes (`jwt_access_token_expire_minutes: int = 30`), but NextAuth session `maxAge` is 7 days. After 30 minutes, every API call silently fails with 401.
- **[MEDIUM] No token refresh logic on the frontend.** `apiFetch` in `api.ts` clears tokens on 401 but never attempts to use the refresh token. The refresh token is stored in `sessionStorage` but never consumed.
- **[LOW] API key exposed to browser via `NEXT_PUBLIC_API_KEY`.** The fallback sends the shared `api_secret_key` to the browser — the same key used for Celery/bot internal calls. Leaking this key gives full API-key-level access.

**Fix (API key removal):**
```typescript
// frontend/src/lib/api.ts — REMOVE this block:
} else if (process.env.NEXT_PUBLIC_API_KEY) {
    headers['X-API-Key'] = process.env.NEXT_PUBLIC_API_KEY;
}
```

**Recommendations:**
1. Implement a client-side token refresh interceptor in `apiFetch` that calls `/api/v1/auth/refresh` when a 401 is received
2. Remove `NEXT_PUBLIC_API_KEY` from all client environment configs
3. Add `aud` (audience) claim to JWT tokens to prevent cross-service token reuse

### 2.2 Password Policy — 3/10

**Findings:**
- **[CRITICAL] No password complexity requirements.** `RegisterRequest` only enforces `min_length=8`. An 8-character all-lowercase password like `aaaaaaaa` is accepted.
- **[HIGH] No brute-force protection beyond rate limiting.** Login is rate-limited to `10/minute`, but there is no account lockout, no failed-attempt counter, and no exponential backoff. An attacker can try 14,400 passwords per day per IP.
- **[LOW] No password breach checking** (HaveIBeenPwned integration).

**Fix (password validator):**
```python
# backend/app/schemas/auth.py
from pydantic import field_validator
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Must contain at least one special character")
        return v
```

**Recommendations:**
1. Enforce password complexity at schema level
2. Implement account lockout after 5 failed attempts (15-minute lockout via Redis)
3. Log every failed login with IP, email, and timestamp

### 2.3 Input Validation — 7/10

**Findings:**
- **[MEDIUM] `AlertConfigCreate.markets` and `signal_types` accept arbitrary strings.** `markets` is `list[str]` with no validation that values are in `{"stock", "crypto", "forex"}`. Arbitrary data gets stored in JSONB.
- **[MEDIUM] `quiet_hours` accepts any dict** — `dict | None = None` allows any arbitrary JSON payload.
- **[GOOD] Symbol inputs are regex-validated** with `pattern=r"^[A-Za-z0-9/.]+$"` and length limits.
- **[GOOD] Pydantic v2 provides automatic type coercion and validation for most fields.

**Fix (schema validators):**
```python
# backend/app/schemas/alert.py
@field_validator("markets")
@classmethod
def validate_markets(cls, v: list[str]) -> list[str]:
    valid = {"stock", "crypto", "forex"}
    for m in v:
        if m not in valid:
            raise ValueError(f"Invalid market: {m}. Must be one of {valid}")
    return v

@field_validator("signal_types")
@classmethod
def validate_signal_types(cls, v: list[str]) -> list[str]:
    valid = {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}
    for st in v:
        if st not in valid:
            raise ValueError(f"Invalid signal type: {st}")
    return v
```

**Recommendations:**
1. Add enum/Literal validation for `markets` and `signal_types`
2. Define `QuietHours` Pydantic model with `start: str` and `end: str` with time format validation
3. Add max length constraints on lists to prevent payload abuse

### 2.4 Authorization — 7/10

**Findings:**
- **[GOOD] Ownership checks exist** on update/delete — both `update_alert_config` and `delete_price_alert` verify ownership via dual `user_id`/`telegram_chat_id` checks.
- **[MEDIUM] `update_alert_config` uses `setattr` with unfiltered fields.** While constrained by the Pydantic schema, if the schema ever gains a field mapping to `user_id` or `telegram_chat_id`, it becomes a privilege escalation vector.
- **[LOW] Tier-based limits rely solely on JWT `tier` claim.** If a user is downgraded, their JWT still carries the old tier for up to 30 minutes.

**Recommendations:**
1. Use an explicit allowlist in `update_alert_config` instead of iterating all schema fields
2. Add `user_id` and `telegram_chat_id` to `AlertConfigUpdate`'s `model_config` with `exclude`

### 2.5 Data Exposure — 7/10

**Findings:**
- **[GOOD] Global exception handler sanitizes errors** — returns `"Internal server error"` instead of stack traces.
- **[GOOD] `UserProfile` response excludes `password_hash`.**
- **[MEDIUM] Telegram Chat ID exposed in JWT payload and API responses.** Could be used for targeted Telegram messages if leaked.
- **[LOW] Settings page displays Telegram Chat ID in plain text.**

**Recommendations:**
1. Omit `telegram_chat_id` from JWT claims — resolve server-side from `user_id`
2. Mask chat ID in frontend display (e.g., `****1234`)

### 2.6 Session Management — 5/10

**Findings:**
- **[HIGH] No "revoke all sessions" / "logout everywhere" capability.** No endpoint to revoke all refresh tokens. If credentials are compromised, no way to invalidate all sessions except waiting for token expiry.
- **[HIGH] Access tokens cannot be revoked.** Stateless JWTs valid for 30 minutes with no blacklist/denylist.
- **[MEDIUM] Refresh token rotation implemented but lacks replay detection.** If an attacker replays a revoked refresh token, the endpoint returns generic 401 instead of revoking ALL tokens (OWASP recommendation).
- **[GOOD] Tokens stored in `sessionStorage`** — cleared on tab close, not accessible to other tabs.

**Fix (logout-all endpoint):**
```python
@router.post("/logout-all", response_model=dict)
async def logout_all(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke ALL refresh tokens for the current user."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True
    return {"data": "all_sessions_revoked"}
```

**Recommendations:**
1. Add `/auth/logout-all` endpoint
2. Implement refresh token replay detection — revoke ALL tokens on replay
3. Consider Redis-based JWT denylist for emergency token revocation

### 2.7 Rate Limiting — 6/10

**Findings:**
- **[GOOD] Auth endpoints are rate-limited** — Registration: `5/minute`, Login: `10/minute`, Refresh: `20/minute`.
- **[MEDIUM] Alert config update, watchlist, and price alert endpoints have NO rate limits.** An attacker could spam these endpoints.
- **[LOW] Rate limiting is IP-based only.** Behind a proxy/CDN, all users could share the same IP.

**Recommendations:**
1. Add rate limits to update/watchlist/price-alert endpoints
2. Consider user-scoped rate limiting (by `user_id`) for authenticated endpoints
3. Configure `X-Forwarded-For` trusted proxy list

### 2.8 CSRF/CORS — 7/10

**Findings:**
- **[GOOD] CORS is restrictive** — only allows configured `frontend_url`, not `*`.
- **[GOOD] Security headers are comprehensive** — `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, CSP, HSTS.
- **[MEDIUM] No explicit CSRF protection** — Bearer token auth is inherently CSRF-resistant, but `X-API-Key` fallback + `allow_credentials=True` is a theoretical vector.
- **[LOW] CSP allows `'unsafe-inline'` and `'unsafe-eval'`** — common for Next.js but weakens XSS protection.

**Recommendations:**
1. Transition to nonce-based CSP if feasible
2. Remove `allow_credentials=True` from CORS if cookies aren't used for auth

### 2.9 Compliance Gaps

| Gap | Regulation | Status |
|-----|-----------|--------|
| No password change endpoint | GDPR Art. 5 (data integrity) | Missing |
| No account deletion endpoint | GDPR Art. 17 (right to erasure) | Missing |
| No data export endpoint | GDPR Art. 20 (data portability) | Missing |
| Telegram Chat ID in JWT | PII minimization | Needs fix |
| No audit trail for settings changes | SOC2 CC6.1 | Missing |

---

## Part 3: Finance/PM Expert Review (3.3/10)

### 3.1 Signal Customization Power — 3/10

**What exists:**
- Market filter (stock/crypto/forex) on alerts page
- Minimum confidence slider (0–100) with 60/70/80/90 presets
- Signal type toggles (STRONG_BUY, BUY, SELL, STRONG_SELL)

**What's missing:**
- **No timeframe preference** — can't filter by "intraday" vs. "swing (1–4 weeks)"
- **No per-market confidence thresholds** — might trust stocks more than crypto
- **No sector/industry filter** — can't focus on NIFTY Bank stocks only
- **No signal frequency cap** — "max 5 signals per day" to prevent information overload
- **HOLD signals can't be independently toggled** — excluded from UI despite existing in schema

**Recommendations:**
- Add timeframe filter: Intraday / Swing / Positional
- Per-market confidence thresholds
- Signal frequency cap (max N signals/day)
- Sector filter for Indian stocks

### 3.2 Alert Intelligence — 3/10

**What exists:**
- Push notification toggle, Telegram integration, price alerts
- `quiet_hours` field in DB schema and backend API

**What's critically missing:**
- **Quiet hours UI completely absent** — backend supports it, zero frontend UI exists
- **No market-hour awareness in alerts** — stock signals fire after 3:30 PM IST
- **No batching vs. real-time preference** — can't choose "digest every 2 hours"
- **No alert urgency levels** — STRONG_BUY at 95% should feel different than BUY at 65%
- **Push notification `minConfidence` hardcoded to 70** — not linked to user preferences

**Recommendations:**
- Ship quiet hours UI (time picker, IST-aware)
- Digest mode toggle: Real-time vs. Batched
- Link push threshold to user's `min_confidence` setting
- Auto-suppress stock alerts when NSE is closed

### 3.3 Portfolio-Signal Alignment — 4/10

**What exists:**
- Watchlist with add/remove, validates against tracked symbols
- Separate portfolio page with trade logging

**What's missing:**
- **No visible link between watchlist and signal feed** — promise of "priority signals" not delivered
- **No "only show signals for my watchlist" toggle**
- **Portfolio positions don't inform signal relevance** — SELL signal for a held stock should be flagged as critical
- **Watchlist buried in alerts page** — should be dashboard-level (like Zerodha's Marketwatch)

**Recommendations:**
- "Watchlist only" filter toggle on signal feed
- Visual badge on signals matching watchlist symbols
- Position-aware alerts: "You hold this stock" callout on SELL signals
- Promote watchlist to more prominent location

### 3.4 Learning Support — 2/10

**What exists:**
- Terse description text on setting rows
- `/how-it-works` page (separate from settings)

**What's critically missing:**
- **No tooltips/info icons** explaining what settings do — "60% confidence" means nothing to a beginner
- **No setting impact previews** — "With these settings, you'd receive ~12 signals/week"
- **No recommended presets** — Beginner/Moderate/Aggressive to reduce analysis paralysis
- **No signal type explanations** — BUY vs. STRONG_BUY difference not explained
- **View Mode descriptions are cryptic**

**Recommendations:**
- Info (ℹ) tooltips on every setting with beginner-friendly explanation
- "Recommended for beginners" badge on 70% confidence + BUY/STRONG_BUY only
- Preset profiles: Conservative / Balanced / Aggressive
- Impact preview: "With these settings, you'd see ~X signals/day"

### 3.5 Indian Market Awareness — 5/10

**What exists:**
- INR formatting with `₹` and Indian number system (`en-IN` locale)
- NSE market hours detection (9:15 AM – 3:30 PM IST)
- NSE symbols tracked (RELIANCE, HDFCBANK, TCS, etc.)

**What's missing:**
- **No IST timestamp display preference** — timestamps come as UTC
- **No NSE holiday calendar** — `isNSEOpen()` only checks weekends, misses Diwali, Republic Day, etc.
- **No pre-market/post-market signal context** — "Execute tomorrow at 9:15 AM"
- **No currency indicator on price alert input** — Is it ₹, $, or pips?
- **No INR-denomination in risk calculations**

**Recommendations:**
- Force IST display or add timezone setting
- Integrate NSE holiday calendar (SEBI publishes annually)
- Show "Market opens in X hours" on after-hours stock signals
- Currency indicator on price alert input based on market type

### 3.6 Notification Control — 3/10

**What exists:**
- Browser push (on/off), Telegram (chat ID), min confidence, market/type filters
- Morning brief + evening wrap (Celery tasks, not user-configurable)

**What's missing:**
- **No channel preference** — can't route STRONG_BUY to push and everything else to Telegram
- **No frequency control** — no "max N alerts per hour/day"
- **No snooze** — "Mute all alerts for 2 hours"
- **Morning brief / evening wrap timing not configurable** — hardcoded 8:00 AM / 4:00 PM
- **Web push and Telegram are two disconnected systems** with separate configs

**Recommendations:**
- Unified notification preference: per-channel × per-type × per-market matrix
- Digest timing config (morning brief time, evening wrap time)
- Snooze button with duration options
- Max alerts per day cap

### 3.7 Risk Management Settings — 1/10

**What exists:**
- Nothing in settings/alerts related to risk management
- `RiskCalculator` component exists on signal detail page (per-signal, not a preference)

**What's completely absent:**
- No default position size setting ("₹10,000 per trade")
- No max exposure setting ("don't show signals if I have 5 open positions")
- No risk tolerance profile (Conservative/Moderate/Aggressive)
- No capital amount input
- No stop-loss preference (tighter/wider than default 1:2 R:R)
- No per-trade max loss setting
- No portfolio-level risk metrics

**Recommendations:**
- Capital input (₹ amount) with position size calculator
- Risk profile selector: Conservative (80%+ only, tight stops) / Balanced / Aggressive
- Default position sizing rule: Fixed amount or % of portfolio
- Max concurrent open signals preference
- Flow into signal card display (show ₹ profit/loss, not just %)

### 3.8 Multi-Market Workflow — 5/10

**What exists:**
- Market toggle buttons, default market filter, per-market formatting, market hours awareness
- Price alerts auto-detect market from symbol pattern

**What's missing:**
- **No per-market alert profiles** — different confidence/type settings per market
- **No system-wide market context switching** — "I'm only looking at stocks right now"
- **Market detection is fragile** — `symbol.includes('USDT')` is naive
- **No per-market digest preferences**
- **No symbol autocomplete** — free-text input, must know exact format

**Recommendations:**
- Per-market alert configuration tabs
- Global market context switch
- Symbol autocomplete/search
- Market-specific signal card layouts

---

## Part 4: Cross-Expert Comparison — Indian Broker Benchmarks

| Feature | Zerodha/Groww | SignalFlow | Gap |
|---------|--------------|------------|-----|
| Watchlist as primary view | First thing you see, 5 custom lists | Buried in alerts page | Critical |
| Smart alerts / Nudgekit | "52-week high", "unusual volume" | Binary price above/below only | Major |
| Position size calculator | "₹10K = ~6 shares. P&L: +₹840 / -₹420" | Raw target/stop-loss prices | Major |
| Risk profile presets | Aggressive / Moderate / Conservative | None | Critical |
| IST-first + holidays | IST everywhere, greyed-out holidays | IST in code, no holiday calendar | Moderate |
| Symbol search autocomplete | Universal search with sector tags | Raw text input | Major |
| Notification center | In-app bell with unread count, filtering | `unseenCount` badge, no history | Moderate |

---

## Part 5: Prioritized Implementation Roadmap

### Tier 1 — Critical Security Fixes (must-fix before any release)

| # | Item | Expert | Severity | Effort | Files |
|---|------|--------|----------|--------|-------|
| 1 | Password complexity requirements | Security | CRITICAL | Small | `backend/app/schemas/auth.py` |
| 2 | Brute-force protection (account lockout) | Security | HIGH | Medium | `backend/app/api/auth_routes.py`, Redis |
| 3 | Token refresh interceptor | Security | HIGH | Medium | `frontend/src/lib/api.ts` |
| 4 | Remove `NEXT_PUBLIC_API_KEY` from client | Security | HIGH | Small | `frontend/src/lib/api.ts` |
| 5 | Validate markets/signal_types/quiet_hours | Security | MEDIUM | Small | `backend/app/schemas/alert.py` |

### Tier 2 — High-Value UX + Domain Features

| # | Item | Expert | Severity | Effort | Files |
|---|------|--------|----------|--------|-------|
| 6 | Quiet hours UI | Finance | HIGH | Medium | `frontend/src/app/alerts/page.tsx` |
| 7 | Beginner preset profiles | Finance+UX | HIGH | Medium | `frontend/src/app/settings/page.tsx`, `preferencesStore.ts` |
| 8 | Fix destructive action confirmations | UX | MEDIUM | Small | `frontend/src/app/settings/page.tsx` |
| 9 | Fix mobile watchlist buttons | UX | MEDIUM | Small | `frontend/src/app/alerts/page.tsx` |
| 10 | Fix chatId storage (sessionStorage → localStorage) | UX | MEDIUM | Small | `frontend/src/store/userStore.ts` |

### Tier 3 — Enhanced User Experience

| # | Item | Expert | Severity | Effort | Files |
|---|------|--------|----------|--------|-------|
| 11 | Setting tooltips/explanations | Finance | MEDIUM | Medium | Settings + alerts pages |
| 12 | Logout-all / revoke sessions endpoint | Security | HIGH | Medium | `backend/app/api/auth_routes.py` |
| 13 | Watchlist-first signal filtering | Finance | MEDIUM | Medium | Dashboard + signal feed |
| 14 | Consolidate settings surfaces | UX | MEDIUM | Large | Multiple frontend files |
| 15 | Remove dead SettingsPanel code | UX | LOW | Small | `frontend/src/components/shared/SettingsPanel.tsx` |

### Tier 4 — Future Enhancements

| # | Item | Expert | Severity | Effort | Files |
|---|------|--------|----------|--------|-------|
| 16 | Capital input + position sizing | Finance | MEDIUM | Large | New component + store |
| 17 | Per-market alert profiles | Finance | LOW | Large | Schema + UI changes |
| 18 | Symbol autocomplete | Finance+UX | LOW | Medium | Watchlist + price alert inputs |
| 19 | NSE holiday calendar | Finance | LOW | Medium | Backend + frontend |
| 20 | Notification center (in-app) | Finance | LOW | Large | New component |
| 21 | Password change endpoint | Security/GDPR | MEDIUM | Medium | Backend auth routes |
| 22 | Account deletion endpoint | Security/GDPR | MEDIUM | Medium | Backend + cascade deletes |

---

## Appendix A: Files Reviewed

### Frontend
- `frontend/src/app/settings/page.tsx` — Main settings page (6 sections)
- `frontend/src/app/alerts/page.tsx` — Alert config + watchlist + price alerts
- `frontend/src/components/shared/SettingsPanel.tsx` — Dead code modal
- `frontend/src/components/alerts/AlertConfig.tsx` — Alert preferences modal
- `frontend/src/store/preferencesStore.ts` — localStorage preferences (theme, textSize, viewMode)
- `frontend/src/store/userStore.ts` — sessionStorage tokens (JWT, chatId, tier)
- `frontend/src/lib/api.ts` — REST client with auth headers
- `frontend/src/lib/auth.ts` — NextAuth configuration
- `frontend/src/lib/notifications.ts` — Browser push notifications
- `frontend/src/utils/formatters.ts` — Price/date formatting
- `frontend/src/utils/market-hours.ts` — Market open/close detection

### Backend
- `backend/app/api/auth_routes.py` — Auth endpoints (register, login, refresh, logout, profile)
- `backend/app/api/alerts.py` — Alert config CRUD + watchlist
- `backend/app/api/price_alerts.py` — Price alert CRUD
- `backend/app/auth.py` — JWT creation/validation, API key auth
- `backend/app/schemas/auth.py` — RegisterRequest, LoginRequest, UserProfile
- `backend/app/schemas/alert.py` — AlertConfigCreate/Update, WatchlistUpdate
- `backend/app/models/alert_config.py` — AlertConfig ORM model
- `backend/app/rate_limit.py` — SlowAPI rate limiter config
- `backend/app/main.py` — CORS, security headers, exception handlers

---

## Appendix B: Current Settings Architecture

```
┌─────────────────────────────────────────────────┐
│                  Settings Surfaces               │
│                                                  │
│  /settings page                                  │
│  ├─ Account (email display, tier badge)          │
│  ├─ Display (theme, text size)                   │
│  ├─ Signals (view mode, default market)          │
│  ├─ Notifications (browser push toggle)          │
│  ├─ Telegram (chat ID input)                     │
│  └─ Reset to Defaults                            │
│                                                  │
│  /alerts page                                    │
│  ├─ Alert Preferences                            │
│  │   ├─ Markets (stock/crypto/forex toggles)     │
│  │   ├─ Min Confidence (slider + presets)        │
│  │   └─ Signal Types (BUY/SELL toggles)          │
│  ├─ Watchlist (add/remove symbols)               │
│  └─ Price Alerts (above/below threshold)         │
│                                                  │
│  SettingsPanel modal (DEAD CODE — never rendered)│
│  AlertConfigModal (invoked from AlertConfig)     │
│                                                  │
├─────────────────────────────────────────────────┤
│                 Storage Layer                    │
│                                                  │
│  preferencesStore (localStorage)                 │
│  ├─ theme: 'dark' | 'light'                     │
│  ├─ textSize: 'sm' | 'base' | 'lg'              │
│  ├─ viewMode: 'simple' | 'standard'             │
│  └─ marketFilter: 'all' | 'stock' | ...         │
│                                                  │
│  userStore (sessionStorage) ⚠️ lost on tab close │
│  ├─ accessToken: string                          │
│  ├─ refreshToken: string                         │
│  ├─ chatId: string        ← BUG                 │
│  └─ tier: string                                 │
│                                                  │
│  Backend PostgreSQL                              │
│  ├─ alert_configs (markets, min_confidence,      │
│  │   signal_types, quiet_hours, watchlist)        │
│  ├─ price_alerts (symbol, condition, threshold)  │
│  └─ users (email, password_hash, tier)           │
└─────────────────────────────────────────────────┘
```

---

*Generated by Multi-Expert Review Panel — 26 March 2026*
