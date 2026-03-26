# Regulatory Compliance — Implementation Plan

> **Source spec**: `docs/design/regulatory-compliance/spec.md`  
> **Created**: 24 March 2026  
> **Status**: READY FOR IMPLEMENTATION  
> **Sprints**: 4 (Sprint 1–2 fully actionable in code; Sprint 3–4 partially require legal counsel)

---

## Plan Overview

This plan implements the regulatory compliance findings from the spec across 4 independently committable sprints. Each sprint has a clear goal, ordered tasks with dependencies, exact file paths, code-level detail, and acceptance criteria.

**Key constraint**: The underlying database `signal_type` values (`STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL`) remain unchanged in the DB and backend logic. The language reframing (Sprint 2) is a **display-layer transformation** — mapping internal values to user-facing labels at the presentation boundary (frontend constants, Telegram formatter, API response serialization). This keeps the scoring algorithm, signal generation pipeline, targets calculator, and 480+ existing tests untouched.

### Sprint Dependency Graph

```
Sprint 1 (Legal Foundation) ← no dependencies
Sprint 2 (Data Rights & Language) ← depends on Sprint 1 consent model
Sprint 3 (Geographic & Access Controls) ← depends on Sprint 1, Sprint 2
Sprint 4 (Payment Compliance & Hardening) ← depends on Sprint 1, Sprint 2, Sprint 3
```

---

## Sprint 1: Legal Foundation

**Goal**: Privacy Policy, Terms of Service, consent infrastructure, disclaimer overhaul, per-signal disclaimers.

**Commit message**: `feat: legal foundation — privacy policy, ToS, consent flow, disclaimer overhaul`

### Task 1.1 — Create Privacy Policy page

**Spec refs**: LB-1, DPDPA-1, IT-1, Finding TRUST-4

**Files to create**:
- `frontend/src/app/privacy/page.tsx`

**What to build**:
- Server component (static content, no client interactivity needed).
- Structured sections covering DPDPA requirements:
  1. Data We Collect (email, Telegram chat ID, trade logs, watchlist, alert prefs, IP addresses in logs)
  2. How We Use Your Data (authentication, alert delivery, portfolio tracking, service improvement)
  3. Data Storage & Security (PostgreSQL on Railway, encrypted in transit via TLS, no data sold to third parties)
  4. Your Rights (access, correction, erasure, portability — per DPDPA §11-12)
  5. Data Retention (market data: indefinite; user data: until account deletion; logs: 90 days)
  6. Third-Party Services (Anthropic Claude API for AI analysis, Google OAuth, Telegram Bot API)
  7. Cookies & Local Storage (NextAuth session cookie, localStorage for tier/preferences)
  8. Grievance Officer (name placeholder + email: `privacy@signalflow.ai`)
  9. Changes to This Policy (notification via email/Telegram)
  10. Contact (email address)
- Use Tailwind prose classes (`prose prose-invert`) for readable long-form text.
- Page metadata: `title: 'Privacy Policy — SignalFlow AI'`.
- Include `Last updated: [date]` at the top.
- **Legal counsel note**: Content is a developer draft. Must be reviewed by a qualified Indian law firm before commercial launch.

**Tests**:
- `frontend/src/__tests__/privacy-page.test.tsx`: Renders without error, contains key sections ("Data We Collect", "Your Rights", "Grievance Officer"), contains contact email.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Page renders at `/privacy`
- [ ] All 10 sections present with meaningful content
- [ ] Grievance officer contact info displayed
- [ ] DPDPA rights (access, erasure, portability) mentioned explicitly

---

### Task 1.2 — Create Terms of Service page

**Spec refs**: LB-2, Finding TRUST-4

**Files to create**:
- `frontend/src/app/terms/page.tsx`

**What to build**:
- Server component, same styling approach as privacy page (Tailwind prose).
- Structured sections:
  1. Acceptance of Terms
  2. Service Description ("AI-powered market analysis tool for educational and informational purposes")
  3. Not Investment Advice (prominent, bolded — "SignalFlow AI does not provide investment advice, is not registered with SEBI as a Research Analyst, and does not recommend buying or selling any security")
  4. User Responsibilities (own research, own risk, 18+ age requirement)
  5. Account & Data (what we store, user's right to delete)
  6. Intellectual Property
  7. Limitation of Liability ("Under no circumstances shall SignalFlow AI be liable for trading losses")
  8. Disclaimer of Warranties ("provided 'as is'")
  9. Governing Law (Indian law, jurisdiction: [city])
  10. Changes to Terms
  11. Contact
- Page metadata: `title: 'Terms of Service — SignalFlow AI'`.
- **Legal counsel note**: Must be reviewed by a lawyer for enforceability under Indian Contract Act before commercial use.

**Tests**:
- `frontend/src/__tests__/terms-page.test.tsx`: Renders without error, contains "Not Investment Advice" section, contains "Limitation of Liability", contains "SEBI".

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Page renders at `/terms`
- [ ] "Not Investment Advice" section is prominent and includes SEBI non-registration disclosure
- [ ] Limitation of liability clause present
- [ ] 18+ age requirement stated

---

### Task 1.3 — Enhance SebiDisclaimer component

**Spec refs**: LB-4, Finding TRUST-1, Finding ADV-1

**Files to modify**:
- `frontend/src/components/shared/SebiDisclaimer.tsx`

**Current state**: 10px font, `text-text-muted` (low contrast), single `<p>` tag.

**What to change**:
- Increase font size from `text-[10px]` to `text-xs` (12px) — spec says 14px+ but 12px is a pragmatic minimum for a footer that doesn't dominate the UI.
- Change color from `text-text-muted` to `text-text-secondary` for higher contrast.
- Add structured disclaimer per SEBI advertising guidelines format:
  ```
  ⚠ Important Disclaimer:
  SignalFlow AI is NOT registered with SEBI or any financial regulatory authority.
  All analysis is AI-generated and for educational/informational purposes only — it does not constitute investment advice
  or a recommendation to buy or sell any security. Past performance does not guarantee future results. 
  Trading involves substantial risk of loss. Always consult a SEBI-registered investment advisor before making investment decisions.
  ```
- Add links to `/privacy` and `/terms` at the bottom of the disclaimer.
- Add `role="contentinfo"` and `aria-label="Legal disclaimer"` for accessibility.

**Tests**:
- `frontend/src/__tests__/sebi-disclaimer.test.tsx`: Renders disclaimer text, contains "NOT registered with SEBI", contains links to `/privacy` and `/terms`, font class is `text-xs` not `text-[10px]`.

**Dependencies**: Tasks 1.1, 1.2 (links to privacy/terms pages).

**Acceptance criteria**:
- [ ] Disclaimer text is at least 12px
- [ ] Text color is `text-text-secondary` (higher contrast than before)
- [ ] Contains explicit "NOT registered with SEBI" statement
- [ ] Contains "not investment advice" statement
- [ ] Links to Privacy Policy and Terms of Service
- [ ] Readable on mobile without squinting

---

### Task 1.4 — Add per-signal disclaimer to SignalCard

**Spec refs**: LB-4, Finding TRUST-2

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx`

**What to change**:
- In the expanded section (after the AI reasoning panel and before the "View full analysis" link), add a compact disclaimer line:
  ```tsx
  <p className="text-[10px] text-text-muted mt-2">
    AI-generated analysis for informational purposes only — not investment advice. 
    <Link href="/terms" className="underline hover:text-text-secondary">Terms</Link>
  </p>
  ```
- This goes inside the `{isExpanded && (` block, after the `AIReasoningPanel` and before the action link `<div>`.

**Tests**:
- Extend existing SignalCard tests (or create `frontend/src/__tests__/signal-card-disclaimer.test.tsx`): When expanded, disclaimer text "not investment advice" is visible. Link to `/terms` is present.

**Dependencies**: Task 1.2 (terms page exists).

**Acceptance criteria**:
- [ ] Per-signal disclaimer visible when card is expanded
- [ ] Links to Terms page
- [ ] Does not appear in collapsed state (avoid clutter)

---

### Task 1.5 — Add disclaimer to Telegram signal alerts

**Spec refs**: LB-4, Finding TRUST-2, Sprint 2.8 in spec

**Files to modify**:
- `backend/app/services/alerts/formatter.py`

**What to change**:
- In `format_signal_alert()`, append a brief disclaimer line at the end of the `lines` list:
  ```python
  lines.append("")
  lines.append("⚠️ AI analysis only — not investment advice. DYOR.")
  ```
- In `format_morning_brief()`, append:
  ```python
  return f"☀️ Morning Brief\n\n{brief_text}\n\n⚠️ For informational purposes only."
  ```
- In `format_evening_wrap()`, append:
  ```python
  return f"🌙 Evening Wrap\n\n{wrap_text}\n\n⚠️ For informational purposes only."
  ```
- In `format_weekly_digest()`, append disclaimer line before the final `\n`.
- In `format_welcome()`, enhance the existing disclaimer from one line to a more prominent section:
  ```python
  "⚠️ IMPORTANT: SignalFlow AI is an AI-powered analysis tool. "
  "It is NOT registered with SEBI and does NOT provide investment advice. "
  "All analysis is for educational and informational purposes only. "
  "Always do your own research and consult a qualified financial advisor."
  ```

**Tests**:
- Update `backend/tests/test_formatter.py`: Assert `format_signal_alert()` output contains "not investment advice". Assert `format_welcome()` contains "NOT registered with SEBI". Assert `format_morning_brief()` contains "informational purposes".
- Run via `make test` (Docker).

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Every Telegram signal alert includes disclaimer footer
- [ ] Welcome message includes expanded SEBI non-registration statement
- [ ] Morning brief and evening wrap include disclaimer
- [ ] Weekly digest includes disclaimer
- [ ] All existing formatter tests still pass

---

### Task 1.6 — Consent flow on sign-in page

**Spec refs**: LB-3, Finding TRUST-4, DPDPA §6

**Files to modify**:
- `frontend/src/app/auth/signin/page.tsx`

**Files to create**:
- `frontend/src/components/shared/ConsentCheckbox.tsx`

**What to change in `signin/page.tsx`**:
- Add state: `const [consented, setConsented] = useState(false);`
- Before the "Sign In" button and the Google button, add the `ConsentCheckbox` component.
- Disable both sign-in buttons until `consented === true`.
- Replace the existing one-liner at the bottom (`By signing in, you agree...`) with the checkbox.

**What to build in `ConsentCheckbox.tsx`**:
```tsx
interface ConsentCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function ConsentCheckbox({ checked, onChange }: ConsentCheckboxProps) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 rounded border-border-default bg-bg-card text-accent-purple focus:ring-accent-purple"
        required
      />
      <span className="text-xs text-text-secondary leading-relaxed">
        I am 18 years or older. I have read and agree to the{' '}
        <a href="/terms" target="_blank" className="text-accent-purple underline">Terms of Service</a>
        {' '}and{' '}
        <a href="/privacy" target="_blank" className="text-accent-purple underline">Privacy Policy</a>.
        I understand that SignalFlow AI provides AI-generated analysis for educational purposes only
        and does not constitute investment advice.
      </span>
    </label>
  );
}
```

**What to change in sign-in flow**:
- The `handleCredentials` function and Google `signIn` call should check `consented` before proceeding.
- Google button gets `disabled={!consented}` with reduced opacity styling.
- Credential submit button gets `disabled={loading || !consented}`.

**Tests**:
- `frontend/src/__tests__/signin-consent.test.tsx`: Sign-in buttons disabled when checkbox unchecked. Buttons enabled after checking. Checkbox contains links to `/terms` and `/privacy`. Contains "18 years or older" text.

**Dependencies**: Tasks 1.1, 1.2 (privacy and terms pages exist for links).

**Acceptance criteria**:
- [ ] Cannot sign in without checking consent checkbox
- [ ] Checkbox includes 18+ age declaration
- [ ] Checkbox includes links to ToS and Privacy Policy
- [ ] Checkbox includes "not investment advice" acknowledgment
- [ ] Both Google and credentials sign-in paths require consent

---

### Task 1.7 — Consent tracking model + migration

**Spec refs**: LB-3, Sprint 1.7 in spec

**Files to create**:
- `backend/app/models/consent.py`
- `backend/migrations/versions/e7a1b2c3d4f5_add_consent_log.py` (generated via alembic)

**Files to modify**:
- `backend/app/models/__init__.py` (if it imports models — check; currently empty `__init__.py`)

**What to build in `consent.py`**:
```python
"""Consent log model — tracks user acceptance of ToS, Privacy Policy, and risk acknowledgment."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConsentLog(Base):
    """Immutable log of user consent events."""

    __tablename__ = "consent_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_identifier: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # email or telegram chat_id
    consent_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "tos_v1", "privacy_v1", "risk_ack_v1", "age_18_plus"
    consent_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "1.0"
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

**Migration**: Generate via `alembic revision --autogenerate -m "add_consent_log"` from within the backend container.

**API endpoint** (create in Task 1.8 below is for Telegram; this is for web):

**Files to create**:
- `backend/app/api/consent.py`

**What to build**:
```python
"""Consent recording API."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.consent import ConsentLog

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentRequest(BaseModel):
    user_identifier: str  # email
    consent_type: str  # "tos_v1", "privacy_v1", "risk_ack_v1"
    consent_version: str  # "1.0"


@router.post("")
async def record_consent(
    payload: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record a user's consent acceptance."""
    log = ConsentLog(
        user_identifier=payload.user_identifier,
        consent_type=payload.consent_type,
        consent_version=payload.consent_version,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)
    await db.commit()
    return {"data": {"recorded": True}}
```

**Files to modify**:
- `backend/app/api/router.py` — add `from app.api.consent import router as consent_router` and `api_router.include_router(consent_router)`.

**Frontend integration**: After successful sign-in, the sign-in page should POST to `/api/v1/consent` to record the acceptance. This can be done in the `handleCredentials` callback and after Google OAuth redirect. Alternatively, call it from a `useEffect` on the dashboard page if the consent hasn't been recorded yet (tracked via a `consentRecorded` flag in localStorage).

**Tests**:
- `backend/tests/test_api_consent.py`: POST `/api/v1/consent` creates a record. Verify `consent_type` and `user_identifier` stored correctly. GET should not exist (write-only log).
- Run via `make test`.

**Dependencies**: None (model is standalone).

**Acceptance criteria**:
- [ ] `consent_logs` table created via migration
- [ ] POST `/api/v1/consent` records consent with user identifier, type, version, IP, user-agent, timestamp
- [ ] Consent log is append-only (no UPDATE/DELETE endpoints)
- [ ] Frontend calls consent API after successful sign-in

---

### Task 1.8 — Telegram /start consent step

**Spec refs**: LB-3, Finding TRUST-4

**Files to modify**:
- `backend/app/services/alerts/telegram_bot.py`

**What to change in `_cmd_start()`**:
- Instead of immediately registering the user and sending the welcome message, the flow becomes:
  1. Send a consent message explaining what data is collected and that this is not investment advice.
  2. Ask user to confirm with an inline keyboard button: "I Accept" / "Cancel".
  3. Only on acceptance: call `_get_or_create_config()` and send `format_welcome()`.
- Use `telegram.InlineKeyboardMarkup` with a callback:
  ```python
  keyboard = InlineKeyboardMarkup([
      [InlineKeyboardButton("✅ I Accept — Start", callback_data="consent_accept")],
      [InlineKeyboardButton("❌ Cancel", callback_data="consent_reject")],
  ])
  ```
- Add a `CallbackQueryHandler` for `consent_accept`/`consent_reject` in the bot builder (`_build_app()`).
- On accept: persist AlertConfig + log consent to `ConsentLog` table.
- On reject: send a polite message and do not register.

**Consent message text**:
```
📋 Before we begin:

SignalFlow AI is an AI-powered market analysis tool. 
It is NOT registered with SEBI and does NOT provide investment advice.

By continuing, you confirm:
• You are 18 years or older
• You understand this is AI-generated analysis, not financial advice
• You accept our Terms of Service and Privacy Policy

Tap "I Accept" to proceed.
```

**Tests**:
- Update `backend/tests/test_formatter.py` or create `backend/tests/test_telegram_consent.py`: Verify that `_cmd_start` sends consent message (mock update/context). Verify callback handler creates config on accept. Verify callback handler does NOT create config on reject.
- Run via `make test`.

**Dependencies**: Task 1.7 (ConsentLog model).

**Acceptance criteria**:
- [ ] /start no longer auto-registers; shows consent prompt first
- [ ] Inline keyboard with Accept/Cancel buttons
- [ ] Only "I Accept" creates the AlertConfig record
- [ ] Consent acceptance logged to `consent_logs` table
- [ ] "Cancel" sends polite decline message, no data stored

---

### Task 1.9 — Add Privacy Policy + ToS links to footer and Navbar

**Spec refs**: LB-10

**Files to modify**:
- `frontend/src/components/shared/SebiDisclaimer.tsx` (already done partially in Task 1.3 — add links there)
- `frontend/src/components/shared/Navbar.tsx`

**What to change in Navbar.tsx**:
- Add Privacy and Terms links to the `MORE_LINKS` array:
  ```typescript
  { href: '/privacy', label: 'Privacy Policy', icon: '🔒' },
  { href: '/terms', label: 'Terms of Service', icon: '📄' },
  ```
- These appear in the "More" dropdown and mobile menu alongside existing links.

**Tests**:
- `frontend/src/__tests__/navbar-legal-links.test.tsx`: Navbar renders links to `/privacy` and `/terms` in the dropdown.

**Dependencies**: Tasks 1.1, 1.2.

**Acceptance criteria**:
- [ ] Privacy Policy link accessible from Navbar "More" dropdown
- [ ] Terms of Service link accessible from Navbar "More" dropdown
- [ ] Both links appear in mobile menu
- [ ] Footer disclaimer also links to both pages (via Task 1.3)

---

### Sprint 1 Summary

| Task | Files Created | Files Modified | Effort |
|------|-------------|----------------|--------|
| 1.1 Privacy Policy | `frontend/src/app/privacy/page.tsx` | — | M |
| 1.2 Terms of Service | `frontend/src/app/terms/page.tsx` | — | M |
| 1.3 SebiDisclaimer overhaul | — | `SebiDisclaimer.tsx` | S |
| 1.4 Per-signal disclaimer | — | `SignalCard.tsx` | S |
| 1.5 Telegram disclaimers | — | `formatter.py` | S |
| 1.6 Consent flow (sign-in) | `ConsentCheckbox.tsx` | `signin/page.tsx` | M |
| 1.7 Consent model + API | `consent.py` (model), `consent.py` (API), migration | `router.py` | M |
| 1.8 Telegram consent | — | `telegram_bot.py` | M |
| 1.9 Navbar legal links | — | `Navbar.tsx`, `SebiDisclaimer.tsx` | S |

**New frontend test files**: `privacy-page.test.tsx`, `terms-page.test.tsx`, `sebi-disclaimer.test.tsx`, `signal-card-disclaimer.test.tsx`, `signin-consent.test.tsx`, `navbar-legal-links.test.tsx`

**New backend test files**: `test_api_consent.py`, `test_telegram_consent.py`

**New migration**: `add_consent_log`

---

## Sprint 2: Data Rights & Language Reframing

**Goal**: DPDPA data rights (deletion/export), display-layer language reframing (BUY → Bullish), AI Q&A guardrails, grievance contact page.

**Commit message**: `feat: data rights + language reframing — account deletion/export, bullish/bearish labels, AI guardrails`

### Task 2.1 — Account deletion endpoint

**Spec refs**: LB-7, DPDPA-2, DPDPA §12

**Files to create**:
- `backend/app/api/account.py`
- `backend/app/schemas/account.py`

**Files to modify**:
- `backend/app/api/router.py`

**What to build in `account.py` (API)**:
```python
@router.delete("")
async def delete_account(
    payload: AccountDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete all user data. DPDPA §12 right to erasure."""
```
- `AccountDeleteRequest` schema requires `user_identifier: str` (email or telegram_chat_id as string) and `confirmation: str` (must be `"DELETE"` to prevent accidental calls).
- The endpoint deletes, in order:
  1. `consent_logs` where `user_identifier` matches
  2. `trades` where `telegram_chat_id` matches (lookup from alert_configs)
  3. `price_alerts` where `telegram_chat_id` matches
  4. `alert_configs` where `telegram_chat_id` matches OR email matches
- Returns `{ "data": { "deleted": true, "records_removed": <count> } }`.
- **Important**: Does NOT delete signals, signal_history, or market_data — those are aggregate/anonymous platform data, not personal data.

**What to build in `schemas/account.py`**:
```python
class AccountDeleteRequest(BaseModel):
    user_identifier: str
    confirmation: str = Field(pattern="^DELETE$")

class AccountExportResponse(BaseModel):
    email: str | None
    telegram_chat_id: int | None
    alert_config: dict | None
    trades: list[dict]
    price_alerts: list[dict]
    consent_logs: list[dict]
```

**Register in `router.py`**:
```python
from app.api.account import router as account_router
api_router.include_router(account_router)
```

**Tests**:
- `backend/tests/test_api_account.py`:
  - POST seed data (alert config, trades, price alerts, consent logs).
  - DELETE `/api/v1/account` with correct confirmation.
  - Verify all personal records removed.
  - Verify DELETE with wrong confirmation returns 422.
  - Verify signals/market_data NOT deleted.
- Run via `make test`.

**Dependencies**: Task 1.7 (consent model exists).

**Acceptance criteria**:
- [ ] DELETE `/api/v1/account` removes all personal data
- [ ] Requires explicit `"DELETE"` confirmation string
- [ ] Returns count of records removed
- [ ] Does not delete anonymous/aggregate data (signals, market_data)
- [ ] All related tables cleaned (alert_configs, trades, price_alerts, consent_logs)

---

### Task 2.2 — Data export endpoint

**Spec refs**: LB-8, DPDPA §11

**Files to modify**:
- `backend/app/api/account.py` (add GET endpoint to same router)

**What to build**:
```python
@router.get("/export")
async def export_account_data(
    user_identifier: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export all user data. DPDPA §11 right to access / Art. 20 portability."""
```
- Query all personal data for the given identifier across all tables.
- Return structured JSON with: alert_config, trades (list), price_alerts (list), consent_logs (list).
- Timestamps formatted as ISO 8601.
- Decimal values serialized as strings (financial precision).

**Tests**:
- `backend/tests/test_api_account.py` (extend): Seed data → GET export → verify all seeded records appear in response. Verify empty response for unknown user.
- Run via `make test`.

**Dependencies**: Task 2.1 (same router file).

**Acceptance criteria**:
- [ ] GET `/api/v1/account/export?user_identifier=...` returns all personal data
- [ ] Response includes alert config, trades, price alerts, consent logs
- [ ] Timestamps are ISO 8601
- [ ] Empty but valid response for non-existent user

---

### Task 2.3 — Account settings page (frontend)

**Spec refs**: LB-7, LB-8

**Files to create**:
- `frontend/src/app/account/page.tsx`

**Files to modify**:
- `frontend/src/components/shared/Navbar.tsx` (add Account link to `MORE_LINKS`)
- `frontend/src/middleware.ts` (add `/account/:path*` to protected routes matcher)

**What to build**:
- Client component (uses session for user email).
- Two sections:
  1. **Export My Data** — button that calls GET `/api/v1/account/export?user_identifier={email}`, downloads result as JSON file.
  2. **Delete My Account** — red danger zone section. Requires typing "DELETE" into a confirmation input. Calls DELETE `/api/v1/account`. On success, signs out and redirects to `/`.
- Use `useSession()` to get current user's email as the `user_identifier`.
- Standard dark theme styling consistent with other pages.

**Tests**:
- `frontend/src/__tests__/account-page.test.tsx`: Renders export and delete sections. Delete button disabled until "DELETE" typed. Export button triggers API call (mock fetch).

**Dependencies**: Tasks 2.1, 2.2 (API endpoints exist).

**Acceptance criteria**:
- [ ] Page renders at `/account` (protected route)
- [ ] Export button downloads JSON file with user data
- [ ] Delete requires typing "DELETE" confirmation
- [ ] Successful deletion signs out and redirects
- [ ] Page accessible from Navbar "More" dropdown

---

### Task 2.4 — Language reframing: display-layer label mapping

**Spec refs**: LB-6, Finding GROWTH-2, recommended positioning Option C+

**CRITICAL DESIGN DECISION**: The database column `signal_type` and all backend logic (`scorer.py`, `targets.py`, `generator.py`, `feedback.py`) continue to use `STRONG_BUY`/`BUY`/`HOLD`/`SELL`/`STRONG_SELL` internally. The reframing is purely at the **display boundary**:
- Frontend constants/labels
- Telegram formatter output
- AI reasoning prompts (how Claude describes the signal)
- API response schemas can optionally include a `display_label` field

This approach ensures zero breakage to the 480+ existing tests and all backend scoring/generation logic.

**Mapping**:
| Internal (`signal_type`) | Display Label | Badge Icon |
|-------------------------|---------------|------------|
| `STRONG_BUY` | `Strongly Bullish` | `▲▲` |
| `BUY` | `Bullish` | `▲` |
| `HOLD` | `Neutral` | `◆` |
| `SELL` | `Bearish` | `▼` |
| `STRONG_SELL` | `Strongly Bearish` | `▼▼` |

**Additional terminology mapping**:
| Current Term | New Term |
|-------------|----------|
| Signal | Analysis / Insight |
| Target Price | Resistance Level (for bullish) / Support Level (for bearish) |
| Stop-Loss | Risk Level |
| Confidence | Analysis Strength |
| Win Rate | Analysis Accuracy |
| Signal History | Analysis History |
| Trading Signals | Market Analysis |

#### 2.4a — Frontend constants

**Files to modify**:
- `frontend/src/lib/constants.ts`

**What to change**:
```typescript
// Add display label mapping (keep SIGNAL_COLORS keys unchanged)
export const DISPLAY_LABELS: Record<string, string> = {
  STRONG_BUY: 'Strongly Bullish',
  BUY: 'Bullish',
  HOLD: 'Neutral',
  SELL: 'Bearish',
  STRONG_SELL: 'Strongly Bearish',
} as const;

// Replace BADGE_LABELS values
export const BADGE_LABELS = {
  STRONG_BUY: 'STRONGLY BULLISH',
  BUY: 'BULLISH',
  HOLD: 'NEUTRAL',
  SELL: 'BEARISH',
  STRONG_SELL: 'STRONGLY BEARISH',
} as const;
```

#### 2.4b — SignalBadge component

**Files to modify**:
- `frontend/src/components/signals/SignalBadge.tsx`

**What to change**:
- Remove local `BADGE_LABELS` definition — import from `@/lib/constants` instead (it already has it but the component defines its own copy).
- Update the local `BADGE_LABELS` Record to use new display values (Bullish/Bearish).
- Update `aria-label` from `Signal: ${label}` to `Analysis: ${label}`.

#### 2.4c — SignalCard component

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx`

**What to change**:
- Update local `BADGE_ICONS` comment — the icons stay the same, only semantics change.
- The card already uses `BADGE_LABELS[signal.signal_type]` from constants — will automatically pick up new values.
- Change "View full analysis →" link text (already says "analysis" — keep).
- Change the target/stop-loss labels in expanded section: instead of displaying raw "Target:" / "Stop:", show:
  - For bullish signals: green price = "Resistance" / red price = "Risk Level"
  - For bearish signals: green price = "Support" / red price = "Risk Level"
- This requires checking if `signal.signal_type` contains `BUY` or `SELL` to determine label direction.

#### 2.4d — SimpleSignalCard component

**Files to modify**:
- `frontend/src/components/signals/SimpleSignalCard.tsx`

**What to change**:
- Same updates as SignalCard: uses imported `BADGE_LABELS` (will auto-update), update local `BADGE_ICONS` if duplicated.

#### 2.4e — Telegram formatter

**Files to modify**:
- `backend/app/services/alerts/formatter.py`

**What to change**:
- Add a display mapping dict at module level:
  ```python
  DISPLAY_LABELS = {
      "STRONG_BUY": "STRONGLY BULLISH",
      "BUY": "BULLISH",
      "HOLD": "NEUTRAL",
      "SELL": "BEARISH",
      "STRONG_SELL": "STRONGLY BEARISH",
  }
  ```
- In `format_signal_alert()`:
  - Change the header line from `f"{emoji} {signal_type.replace('_', ' ')}"` to `f"{emoji} {DISPLAY_LABELS.get(signal_type, signal_type)}"`.
  - Change "Confidence" label to "Strength".
  - Change "Target" / "Stop" to "Resistance" / "Risk Level" (for bullish) or "Support" / "Risk Level" (for bearish).
  - Change "Timeframe" to "Analysis Horizon" (or remove entirely per spec recommendation — but keeping with safer label is better for UX).
- In `format_signals_list()`:
  - Replace signal_type display with `DISPLAY_LABELS`.
  - Replace "Top Active Signals" with "Top Active Analyses".
- In `format_welcome()`:
  - Replace "trading signals" with "market analysis".
  - Replace "/signals — Current active signals" with "/signals — Current active analyses".
- In `format_tutorial()`:
  - Replace all "signal" references with "analysis".
  - Replace "BUY/SELL" labels with "Bullish/Bearish".
  - Replace "Confidence Score" with "Analysis Strength".

#### 2.4f — Page titles and metadata

**Files to modify** (content only — page titles/headings):
- `frontend/src/app/page.tsx` — if title mentions "signals", change to "analyses"
- `frontend/src/app/history/page.tsx` — "Signal History" → "Analysis History"
- `frontend/src/app/track-record/page.tsx` — if mentions "signals" or "win rate", use "analyses" and "accuracy"
- `frontend/src/app/layout.tsx` — Change metadata: `title: 'SignalFlow AI — Market Analysis'` and `description: 'AI-powered market analysis platform...'`

**Tests**:
- `frontend/src/__tests__/display-labels.test.tsx`: Import `BADGE_LABELS` and `DISPLAY_LABELS`, verify `STRONG_BUY` maps to "STRONGLY BULLISH" / "Strongly Bullish".
- Update `backend/tests/test_formatter.py`: Assert `format_signal_alert()` output contains "BULLISH" or "BEARISH" (not "BUY"/"SELL"). Assert `format_welcome()` contains "market analysis". Assert `format_tutorial()` contains "Analysis Strength".
- Run `make test` for backend.

**Dependencies**: None (pure display change).

**Acceptance criteria**:
- [ ] No user-facing surface displays "BUY", "SELL", "STRONG_BUY", "STRONG_SELL" as labels
- [ ] All frontend badges show "Bullish"/"Bearish" variants
- [ ] Telegram messages use "Bullish"/"Bearish" labels
- [ ] "Target"/"Stop-Loss" replaced with "Resistance"/"Support"/"Risk Level"
- [ ] "Confidence" replaced with "Analysis Strength" on user-facing surfaces
- [ ] Database `signal_type` column unchanged (still stores STRONG_BUY etc.)
- [ ] All 480+ existing backend tests pass without modification
- [ ] Signal generation pipeline completely unchanged

---

### Task 2.5 — Claude AI prompt guardrails

**Spec refs**: HP-4, Finding IA-1

**Files to modify**:
- `backend/app/services/ai_engine/prompts.py`

**What to change**:

1. **Update `SYMBOL_QA_PROMPT`** — add strict guardrails:
   ```python
   SYMBOL_QA_PROMPT = """You are an expert financial analyst assistant helping an intelligent \
   finance professional (M.Com in Finance) who is learning active trading.

   She is asking about: {symbol} ({market_type})

   Current Market Data:
   {market_data}

   Active Analyses (if any):
   {signals_info}

   Her question: {question}

   STRICT GUIDELINES:
   - NEVER give personalized buy/sell/hold recommendations
   - NEVER say "you should buy/sell" or "I recommend buying/selling"
   - You may discuss technical levels, market conditions, and what indicators show
   - If asked "should I buy X?", respond with educational analysis of the current market 
     conditions, not a direct recommendation
   - Always end with "This is educational analysis, not investment advice"
   - Answer specifically about this symbol using available data
   - Use financial terminology she'd know from her M.Com
   - Keep the answer concise (2-4 sentences)
   - If you don't have enough data, say so honestly

   Respond with the answer text only."""
   ```

2. **Update `REASONING_PROMPT`** — reframe from "signal" to "analysis":
   ```python
   REASONING_PROMPT = """You are explaining a market analysis finding to an intelligent finance \
   professional who is learning active trading. She has an M.Com in Finance.

   Symbol: {symbol}
   Analysis: {signal_type} (Analysis Strength: {confidence}%)
   Technical Data: {technical_summary}
   Sentiment: {sentiment_summary}

   Write a 2-3 sentence explanation of WHY this analysis conclusion was reached.
   - Be specific about which indicators and news drove the analysis
   - Use financial terminology she would know from her M.Com
   - Include ONE key risk or scenario where this analysis could be wrong
   - Be direct and educational — no filler
   - Do NOT use the words "buy", "sell", or "trade" as recommendations

   Respond with the explanation text only, no JSON."""
   ```
   Note: Adding the "one key risk" requirement addresses Finding TRUST-3.

3. **Update `SENTIMENT_PROMPT`** — no changes needed (internal-facing, not user-visible).

4. **Update `MORNING_BRIEF_PROMPT`** and `EVENING_WRAP_PROMPT`** — replace "signal" language:
   - "Active Signals" → "Active Analyses"
   - "Top signal highlights with entry levels" → "Top analysis highlights with key price levels"
   - "How the day's signals performed" → "How the day's analyses performed"
   - Add to both: "Do not recommend specific trades. Present factual analysis only."

**Tests**:
- `backend/tests/test_prompts.py` (update existing): Verify `SYMBOL_QA_PROMPT` contains "NEVER give personalized buy/sell". Verify `REASONING_PROMPT` contains "risk or scenario". Verify neither prompt contains "entry price" or "buy signal".
- Run via `make test`.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] `SYMBOL_QA_PROMPT` contains explicit guardrails against personalized recommendations
- [ ] `REASONING_PROMPT` asks Claude to include one risk scenario
- [ ] `REASONING_PROMPT` avoids "buy"/"sell" recommendation language
- [ ] Morning/evening brief prompts use "analysis" not "signal" terminology
- [ ] All existing prompt tests pass (may need updating)

---

### Task 2.6 — Grievance officer / Contact page

**Spec refs**: LB-10, DPDPA-3, DPDPA §8(10)

**Files to create**:
- `frontend/src/app/contact/page.tsx`

**What to build**:
- Server component with:
  1. **Grievance Officer** section: Name placeholder (e.g., "[To be appointed]"), email: `grievance@signalflow.ai`, response timeline: "within 15 days per DPDPA §8(10)"
  2. **General Contact**: `support@signalflow.ai`
  3. **Data Requests**: How to request data export or deletion (link to `/account` page)
  4. **Regulatory Concerns**: Separate email for compliance-related matters
- **Legal counsel note**: Actual grievance officer must be a named individual. Placeholder used until appointment.

**Files to modify**:
- `frontend/src/components/shared/Navbar.tsx` — add Contact link to `MORE_LINKS`

**Tests**:
- `frontend/src/__tests__/contact-page.test.tsx`: Page renders. Contains "Grievance Officer". Contains email address. Contains "15 days" response timeline.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Page renders at `/contact`
- [ ] Grievance officer section with contact info and response timeline
- [ ] Data requests section linking to account page
- [ ] Accessible from Navbar

---

### Task 2.7 — Update /how-it-works page with methodology disclosure

**Spec refs**: Finding PFUTP-1 (analysis accuracy methodology must be verifiable), Finding ADV-1

**Files to modify**:
- `frontend/src/app/how-it-works/page.tsx`

**What to change**:
- Add a new section: **"How Analysis Accuracy Is Calculated"**
  - Explain the signal resolution logic: signal expires → check if price hit resistance level or risk level → resolution recorded in `signal_history`
  - Explain that "accuracy rate" = (hit resistance / total resolved) × 100
  - Explain that pending/unresolved analyses are excluded from accuracy calculations
  - State: "Past analysis accuracy does not predict future accuracy"
- Update existing signal explanation section to use "analysis"/"bullish"/"bearish" terminology.
- Add a **"Data Sources"** section listing: Yahoo Finance (stocks), Binance (crypto), Alpha Vantage (forex), with a note that data may be delayed.
- Add a **"Limitations"** section: AI can be wrong, markets are unpredictable, analysis strength is a model score not a probability of profit.

**Tests**:
- `frontend/src/__tests__/how-it-works.test.tsx` (create or extend): Page renders. Contains "How Analysis Accuracy Is Calculated". Contains "past analysis accuracy does not predict". Contains "Limitations".

**Dependencies**: None (but should use reframed terminology from Task 2.4).

**Acceptance criteria**:
- [ ] Methodology disclosure section present
- [ ] Data sources listed
- [ ] Limitations section present
- [ ] Past performance disclaimer present next to accuracy info
- [ ] Uses reframed terminology

---

### Sprint 2 Summary

| Task | Files Created | Files Modified | Effort |
|------|-------------|----------------|--------|
| 2.1 Account deletion | `account.py` (API), `account.py` (schema) | `router.py` | M |
| 2.2 Data export | — | `account.py` (API) | M |
| 2.3 Account settings page | `account/page.tsx` | `Navbar.tsx`, `middleware.ts` | M |
| 2.4 Language reframing | — | `constants.ts`, `SignalBadge.tsx`, `SignalCard.tsx`, `SimpleSignalCard.tsx`, `formatter.py`, `layout.tsx`, history/track-record page titles | L |
| 2.5 AI prompt guardrails | — | `prompts.py` | S |
| 2.6 Grievance / Contact page | `contact/page.tsx` | `Navbar.tsx` | S |
| 2.7 How-it-works updates | — | `how-it-works/page.tsx` | M |

**New frontend test files**: `account-page.test.tsx`, `display-labels.test.tsx`, `contact-page.test.tsx`, `how-it-works.test.tsx`

**New backend test files**: `test_api_account.py` (with deletion + export tests)

**Updated backend test files**: `test_formatter.py`, `test_prompts.py`

---

## Sprint 3: Geographic & Access Controls

**Goal**: Jurisdiction selection, forex FEMA warnings, cookie consent, signal retraction, educational tooltips.

**Commit message**: `feat: geographic controls + forex warnings + cookie consent + signal retraction`

> **Legal counsel note**: Geo-blocking decisions (which countries to block) should be validated with legal counsel. The implementation below provides the **infrastructure**; the country list is configurable.

### Task 3.1 — Jurisdiction selection on sign-up

**Spec refs**: HP-1, Finding SEC-1, Finding GDPR-1, Finding FCA-1

**Files to modify**:
- `frontend/src/app/auth/signin/page.tsx`
- `frontend/src/components/shared/ConsentCheckbox.tsx` (from Sprint 1)

**Files to create**:
- `frontend/src/lib/jurisdictions.ts`

**What to build in `jurisdictions.ts`**:
```typescript
export const BLOCKED_COUNTRIES = ['US', 'GB'] as const;
// EU countries — block until GDPR compliance
export const EU_COUNTRIES = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'] as const;

export const COUNTRY_LIST = [
  { code: 'IN', name: 'India' },
  // ... full list
  { code: 'OTHER', name: 'Other' },
] as const;

export function isBlockedCountry(code: string): boolean {
  return BLOCKED_COUNTRIES.includes(code as any) || EU_COUNTRIES.includes(code as any);
}
```

**What to change in sign-in page**:
- Add country selector dropdown before the consent checkbox.
- If blocked country selected, show message: "SignalFlow AI is not yet available in your jurisdiction. We are working on regulatory compliance for your region."
- Disable sign-in buttons.
- Store selected country in the consent log (add `jurisdiction` field to ConsentLog model or pass as metadata).

**What to store**:
- Add `jurisdiction: str | None` column to `ConsentLog` model (or alternatively store in `alert_configs` as a new column — simpler to use in future for per-user content filtering).

**⚠️ Legal counsel needed**: Final list of blocked countries should be confirmed by legal counsel. Default: US, UK, all EU member states.

**Tests**:
- `frontend/src/__tests__/jurisdiction.test.tsx`: Blocked countries disable sign-in. India allows sign-in. Country stored in consent.

**Dependencies**: Sprint 1 (consent flow).

**Acceptance criteria**:
- [ ] Country selector on sign-up
- [ ] US/UK/EU countries show blocking message
- [ ] India and other non-blocked countries proceed normally
- [ ] Selected jurisdiction recorded in consent/profile

---

### Task 3.2 — Forex FEMA disclaimer

**Spec refs**: HP-2, Finding FOREX-1

**Files to modify**:
- `frontend/src/components/signals/SignalCard.tsx`
- `backend/app/services/alerts/formatter.py`

**What to change**:
- **Frontend**: When `signal.market_type === 'forex'` and the symbol is a cross-currency pair (not containing "INR"), show an additional warning in the expanded card:
  ```tsx
  {signal.market_type === 'forex' && !signal.symbol.includes('INR') && (
    <p className="text-[10px] text-signal-hold mt-1">
      ⚠️ Cross-currency forex trading is restricted for Indian residents under FEMA. 
      This analysis is for informational purposes only.
    </p>
  )}
  ```
- **Telegram**: In `format_signal_alert()`, if `market_type == "forex"` and symbol doesn't contain "INR", append FEMA warning.

**Tests**:
- Frontend: SignalCard renders FEMA warning for EUR/USD but not for USD/INR.
- Backend: `format_signal_alert()` for forex cross-pair contains "FEMA".

**Dependencies**: Task 2.4 (language reframing done first).

**Acceptance criteria**:
- [ ] FEMA warning shown on cross-currency forex analyses (EUR/USD, GBP/JPY, etc.)
- [ ] No FEMA warning on INR pairs (USD/INR)
- [ ] Warning appears in both web and Telegram

---

### Task 3.3 — Cookie consent banner

**Spec refs**: HP-3

**Files to create**:
- `frontend/src/components/shared/CookieConsent.tsx`

**Files to modify**:
- `frontend/src/app/layout.tsx`

**What to build**:
- A bottom-fixed banner that appears on first visit (check `localStorage.getItem('cookieConsent')`).
- Text: "We use cookies for authentication and local preferences. See our [Privacy Policy](/privacy)."
- Two buttons: "Accept" (stores `cookieConsent: 'accepted'` in localStorage) and "Learn More" (links to `/privacy`).
- Banner disappears after acceptance.
- Add `<CookieConsent />` to `layout.tsx` inside the `<ThemeProvider>` wrapper, after `<SebiDisclaimer />`.

**Tests**:
- `frontend/src/__tests__/cookie-consent.test.tsx`: Banner renders on first visit. Clicking "Accept" hides it. On subsequent render, banner does not appear.

**Dependencies**: Task 1.1 (privacy page for link).

**Acceptance criteria**:
- [ ] Cookie banner shown to new visitors
- [ ] Disappears after acceptance
- [ ] Links to privacy policy
- [ ] Does not reappear after acceptance (localStorage)

---

### Task 3.4 — Signal retraction mechanism

**Spec refs**: HP-5, Finding TRUST-5

**Files to modify**:
- `backend/app/models/signal.py`
- `backend/app/api/signals.py`
- `frontend/src/components/signals/SignalCard.tsx`

**What to add to Signal model**:
```python
is_retracted: Mapped[bool] = mapped_column(Boolean, default=False)
retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
retracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Migration**: New Alembic migration `add_signal_retraction_fields`.

**API endpoint** (add to `signals.py`):
```python
@router.patch("/signals/{signal_id}/retract")
async def retract_signal(signal_id: UUID, reason: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Mark an analysis as retracted/superseded."""
```
- Sets `is_retracted = True`, `retraction_reason = reason`, `retracted_at = now()`, `is_active = False`.

**Frontend**: In `SignalCard.tsx`, if `signal.is_retracted`, show a prominent red banner at the top of the card:
```tsx
{signal.is_retracted && (
  <div className="bg-signal-sell/10 border border-signal-sell/30 rounded px-3 py-2 mb-2">
    <p className="text-xs text-signal-sell font-semibold">⚠️ This analysis has been retracted</p>
    {signal.retraction_reason && (
      <p className="text-[10px] text-text-muted mt-0.5">{signal.retraction_reason}</p>
    )}
  </div>
)}
```

**Types update** (`frontend/src/lib/types.ts`): Add `is_retracted?: boolean`, `retraction_reason?: string | null` to `Signal` interface.

**Tests**:
- Backend: `test_api_signals.py` (extend): PATCH retract → signal becomes inactive + retracted. GET returns retraction info.
- Frontend: SignalCard renders retraction banner when `is_retracted` is true.

**⚠️ Note**: This is an internal/admin action. No public-facing retraction UI in this sprint — the endpoint can be called via API or a future admin panel.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Signal model has retraction fields
- [ ] PATCH endpoint marks analysis as retracted
- [ ] Retracted analyses show visual banner in UI
- [ ] Retracted analyses marked as inactive
- [ ] Migration created

---

### Task 3.5 — Risk counter-scenario in AI reasoning

**Spec refs**: Finding TRUST-3 (already partially addressed in Task 2.5)

**Files to modify**:
- `backend/app/services/ai_engine/prompts.py` (verify Task 2.5 included this)

**What to verify/change**:
- The `REASONING_PROMPT` (updated in Task 2.5) should already include: "Include ONE key risk or scenario where this analysis could be wrong".
- If Task 2.5 is already done, this task is just **verification**: read a few generated analyses and confirm the risk sentence appears.
- No additional code changes expected if Task 2.5 was executed properly.

**Tests**:
- Existing prompt tests validate the prompt content.

**Dependencies**: Task 2.5.

**Acceptance criteria**:
- [ ] REASONING_PROMPT includes risk scenario instruction
- [ ] Sample generated analyses include a risk/downside mention

---

### Task 3.6 — Educational tooltips on indicator pills

**Spec refs**: Sprint 3.9 in spec

**Files to modify**:
- `frontend/src/components/shared/IndicatorPill.tsx` (if exists, or add to SignalCard expanded section)

**What to build**:
- When technical indicators are displayed (RSI, MACD, Volume in expanded card), add a small `?` icon that shows a tooltip on hover/tap explaining what the indicator means:
  - RSI: "Relative Strength Index — measures momentum. Above 70 = overbought, below 30 = oversold."
  - MACD: "Moving Average Convergence Divergence — shows trend direction and momentum changes."
  - Volume: "Trading volume relative to average. High volume confirms price moves."
  - Bollinger: "Bollinger Bands — price trading near upper band may indicate overbought conditions."
- Use a simple CSS tooltip (no external library needed) or the existing `title` attribute on the indicator display in SignalCard's expanded section.

**Tests**:
- `frontend/src/__tests__/indicator-tooltips.test.tsx`: RSI indicator has explanatory tooltip/title attribute. MACD indicator has tooltip.

**Dependencies**: Task 2.4 (terminology reframing done).

**Acceptance criteria**:
- [ ] Each technical indicator displayed has an educational explanation accessible via hover/tap
- [ ] Explanations are accurate and beginner-friendly
- [ ] Does not clutter the compact card view

---

### Sprint 3 Summary

| Task | Files Created | Files Modified | Effort |
|------|-------------|----------------|--------|
| 3.1 Jurisdiction selection | `jurisdictions.ts` | `signin/page.tsx`, `ConsentCheckbox.tsx`, consent model | M |
| 3.2 Forex FEMA disclaimer | — | `SignalCard.tsx`, `formatter.py` | S |
| 3.3 Cookie consent banner | `CookieConsent.tsx` | `layout.tsx` | S |
| 3.4 Signal retraction | — + migration | `signal.py`, `signals.py` (API), `SignalCard.tsx`, `types.ts` | M |
| 3.5 Risk counter-scenario | — | Verification only (done in 2.5) | S |
| 3.6 Educational tooltips | — | `SignalCard.tsx` or `IndicatorPill.tsx` | S |

**⚠️ Legal counsel needed for Sprint 3**:
- Task 3.1: Confirm blocked country list
- Task 3.2: Confirm FEMA disclaimer wording
- Task 3.4: Confirm retraction process is legally adequate for regulatory requirements

---

## Sprint 4: Payment Compliance & Hardening

**Goal**: Payment infrastructure with GST compliance, refund policy, audit trail, compliance test suite.

**Commit message**: `feat: payment compliance + audit trail + compliance test suite`

> **⚠️ This sprint requires external actions**: GST registration must be completed outside of code. Razorpay merchant account requires approval. Legal counsel should review refund policy and invoice format.

### Task 4.1 — Refund & cancellation policy page

**Spec refs**: HP-9, Finding PAY-1

**Files to create**:
- `frontend/src/app/refund-policy/page.tsx`

**What to build**:
- Server component with clear refund/cancellation policy:
  1. Free tier: no charges, cancel anytime
  2. Pro tier: monthly subscription, cancel anytime (no refund for current billing period)
  3. Pro annual (if offered): prorated refund for unused months
  4. How to cancel: account settings page → cancel subscription
  5. Refund processing timeline: 5-7 business days
  6. Contact for billing: `billing@signalflow.ai`
- Link from pricing page and footer.
- **Legal counsel note**: Refund policy must comply with Consumer Protection Act 2019 for digital services.

**Files to modify**:
- `frontend/src/components/shared/Navbar.tsx` — add to MORE_LINKS
- `frontend/src/app/pricing/page.tsx` — add link to refund policy + add risk warning + "not SEBI registered" note

**Tests**:
- `frontend/src/__tests__/refund-policy.test.tsx`: Renders. Contains "cancel". Contains refund timeline.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Refund policy page renders at `/refund-policy`
- [ ] Clear cancellation process described
- [ ] Refund timeline stated
- [ ] Linked from pricing page

---

### Task 4.2 — Pricing page compliance disclaimers

**Spec refs**: Finding ADV-1, Finding GROWTH-1

**Files to modify**:
- `frontend/src/app/pricing/page.tsx`

**What to add**:
- Below the pricing cards, add a prominent disclaimer section:
  ```
  ⚠️ Important:
  • SignalFlow AI is NOT registered with SEBI as a Research Analyst or Investment Adviser
  • Analysis provided is AI-generated and for educational/informational purposes only
  • Past analysis accuracy does not guarantee future results
  • Trading and investing involve substantial risk of loss
  • Prices are inclusive of applicable taxes
  ```
- Add link to refund policy.
- Add "View Terms of Service" link.

**Tests**:
- `frontend/src/__tests__/pricing-compliance.test.tsx`: Pricing page contains SEBI disclaimer. Contains risk warning. Contains link to terms.

**Dependencies**: Tasks 1.2, 4.1.

**Acceptance criteria**:
- [ ] SEBI non-registration stated on pricing page
- [ ] Risk warnings present
- [ ] Tax inclusion noted
- [ ] Links to ToS and refund policy

---

### Task 4.3 — Immutable audit log for analyses

**Spec refs**: HP-10, Finding RA-4 (5-year record keeping)

**Files to create**:
- `backend/app/models/audit_log.py`
- Migration for `audit_logs` table

**Files to modify**:
- `backend/app/services/signal_gen/generator.py`

**What to build**:
- `AuditLog` model:
  ```python
  class AuditLog(Base):
      __tablename__ = "audit_logs"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "signal_generated", "signal_retracted", "signal_resolved"
      signal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
      payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # full snapshot of signal data at time of event
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  ```
- In `generator.py`'s `generate_signal()` method (or wherever the Signal is created and committed), after commit, create an `AuditLog` entry with `event_type="signal_generated"` and `payload` containing the full signal data snapshot.
- This provides the SEBI RA Regulation 24-25 requirement for 5-year record keeping of all research reports and rationale.

**Tests**:
- `backend/tests/test_audit_log.py`: Generate a signal (mock pipeline) → AuditLog record created with correct event_type and payload.

**Dependencies**: None (model is standalone).

**Acceptance criteria**:
- [ ] `audit_logs` table created via migration
- [ ] Every generated analysis creates an audit log entry
- [ ] Audit log contains full signal data snapshot
- [ ] Audit log is append-only (no update/delete endpoints)

---

### Task 4.4 — Data breach notification template

**Spec refs**: DPDPA §8(6), 72-hour requirement

**Files to create**:
- `docs/compliance/data-breach-template.md`

**What to build**:
- Pre-drafted notification template for the Data Protection Board of India.
- Sections: What happened, What data was affected, When it happened, What we're doing about it, Contact information.
- Include the 72-hour timeline requirement.
- **This is a documentation-only task** — no code changes.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Template document exists
- [ ] Contains all required sections per DPDPA §8(6)
- [ ] 72-hour timeline noted

---

### Task 4.5 — Record retention policy implementation

**Spec refs**: HP-7, Finding RA-4

**Files to create**:
- `backend/app/tasks/retention_tasks.py`

**Files to modify**:
- `backend/app/tasks/scheduler.py`
- `backend/app/tasks/celery_app.py` (register new task module)

**What to build**:
- A weekly Celery task that:
  1. Deletes `market_data` rows older than 2 years (raw OHLCV data is high-volume; keep aggregate data longer via audit log)
  2. Anonymizes server log IP addresses older than 90 days (if log rotation is in place)
  3. Does NOT delete signals, signal_history, or audit_logs (5-year retention for SEBI compliance)
- Schedule: Run once per week (Sunday 3 AM IST).

**Tests**:
- `backend/tests/test_retention_tasks.py`: Seed old market_data rows → run task → old rows deleted, recent rows kept.

**Dependencies**: None.

**Acceptance criteria**:
- [ ] Weekly retention task created
- [ ] Deletes market_data older than 2 years
- [ ] Does not delete signals or audit logs (5-year retention)
- [ ] Scheduled in Celery Beat

---

### Task 4.6 — Comprehensive compliance test suite

**Spec refs**: Sprint 4.10 in spec

**Files to create**:
- `backend/tests/test_compliance.py`
- `frontend/src/__tests__/compliance.test.tsx`

**Backend compliance tests** (`test_compliance.py`):
1. Health endpoint contains "disclaimer" field
2. Every signal response includes `signal_type` field (for audit)
3. Consent endpoint accepts and stores correctly
4. Account deletion actually removes data
5. Formatter output contains disclaimer text for all message types
6. AI prompts contain guardrail keywords ("NEVER give personalized", "not investment advice")

**Frontend compliance tests** (`compliance.test.tsx`):
1. `SebiDisclaimer` component renders with adequate font size
2. `SebiDisclaimer` contains links to `/privacy` and `/terms`
3. Sign-in page has consent checkbox
4. Consent checkbox contains 18+ verification text
5. `BADGE_LABELS` does not contain "BUY" or "SELL" as standalone words (only "BULLISH"/"BEARISH")
6. `layout.tsx` metadata does not say "trading signals"

**Dependencies**: All previous sprints.

**Acceptance criteria**:
- [ ] Backend compliance tests pass via `make test`
- [ ] Frontend compliance tests pass via `npx vitest`
- [ ] Tests serve as regression guard against compliance backsliding

---

### Task 4.7 — Update CLAUDE.md with compliance architecture

**Spec refs**: Sprint 4.9 in spec

**Files to modify**:
- `CLAUDE.md`

**What to add**:
- New section: "## Regulatory Compliance" after the "Important Constraints & Rules" section.
- Content:
  - Summary of legal positioning ("AI Market Analysis & Education Platform")
  - List of compliance features implemented (consent, disclaimers, language reframing, data rights, geo-blocking)
  - Reference to `docs/design/regulatory-compliance/spec.md` for full analysis
  - Quick reference for terminology mapping (BUY→Bullish etc.)
  - Note: "Backend `signal_type` column stores internal values (STRONG_BUY etc.); display layer maps to user-facing labels."

**Dependencies**: All previous sprints.

**Acceptance criteria**:
- [ ] CLAUDE.md contains regulatory compliance section
- [ ] Terminology mapping documented
- [ ] Clear separation between internal and display values documented

---

### Sprint 4 Summary

| Task | Files Created | Files Modified | Effort |
|------|-------------|----------------|--------|
| 4.1 Refund policy | `refund-policy/page.tsx` | `Navbar.tsx`, `pricing/page.tsx` | S |
| 4.2 Pricing disclaimers | — | `pricing/page.tsx` | S |
| 4.3 Audit log | `audit_log.py`, migration | `generator.py` | M |
| 4.4 Breach template | `docs/compliance/data-breach-template.md` | — | S |
| 4.5 Retention tasks | `retention_tasks.py` | `scheduler.py`, `celery_app.py` | M |
| 4.6 Compliance test suite | `test_compliance.py`, `compliance.test.tsx` | — | M |
| 4.7 Update CLAUDE.md | — | `CLAUDE.md` | S |

**⚠️ External actions required for Sprint 4** (not code):
- GST registration (government portal)
- Razorpay merchant account setup (deferred to separate sprint when payment integration is needed)
- Legal counsel review of refund policy
- Legal counsel review of audit log adequacy for SEBI RA Regulation 24-25
- Professional indemnity insurance (deferred to post-launch)

---

## Appendix A: Full File Inventory

### Files Created (Total: ~18)

| Sprint | File | Type |
|--------|------|------|
| 1 | `frontend/src/app/privacy/page.tsx` | Page |
| 1 | `frontend/src/app/terms/page.tsx` | Page |
| 1 | `frontend/src/components/shared/ConsentCheckbox.tsx` | Component |
| 1 | `backend/app/models/consent.py` | Model |
| 1 | `backend/app/api/consent.py` | API |
| 1 | `backend/migrations/versions/*_add_consent_log.py` | Migration |
| 2 | `backend/app/api/account.py` | API |
| 2 | `backend/app/schemas/account.py` | Schema |
| 2 | `frontend/src/app/account/page.tsx` | Page |
| 2 | `frontend/src/app/contact/page.tsx` | Page |
| 3 | `frontend/src/lib/jurisdictions.ts` | Utility |
| 3 | `frontend/src/components/shared/CookieConsent.tsx` | Component |
| 3 | `backend/migrations/versions/*_add_signal_retraction.py` | Migration |
| 4 | `frontend/src/app/refund-policy/page.tsx` | Page |
| 4 | `backend/app/models/audit_log.py` | Model |
| 4 | `backend/app/tasks/retention_tasks.py` | Task |
| 4 | `docs/compliance/data-breach-template.md` | Doc |
| 4 | `backend/migrations/versions/*_add_audit_log.py` | Migration |

### Files Modified (Total: ~20)

| File | Sprints |
|------|---------|
| `frontend/src/components/shared/SebiDisclaimer.tsx` | 1 |
| `frontend/src/components/signals/SignalCard.tsx` | 1, 2, 3 |
| `frontend/src/components/signals/SimpleSignalCard.tsx` | 2 |
| `frontend/src/components/signals/SignalBadge.tsx` | 2 |
| `frontend/src/components/shared/Navbar.tsx` | 1, 2, 4 |
| `frontend/src/app/auth/signin/page.tsx` | 1, 3 |
| `frontend/src/app/layout.tsx` | 2, 3 |
| `frontend/src/app/pricing/page.tsx` | 4 |
| `frontend/src/app/how-it-works/page.tsx` | 2 |
| `frontend/src/app/history/page.tsx` | 2 (title only) |
| `frontend/src/app/track-record/page.tsx` | 2 (title only) |
| `frontend/src/lib/constants.ts` | 2 |
| `frontend/src/lib/types.ts` | 3 |
| `frontend/src/middleware.ts` | 2 |
| `backend/app/services/alerts/formatter.py` | 1, 2, 3 |
| `backend/app/services/ai_engine/prompts.py` | 2 |
| `backend/app/api/router.py` | 1, 2 |
| `backend/app/api/signals.py` | 3 |
| `backend/app/models/signal.py` | 3 |
| `backend/app/services/signal_gen/generator.py` | 4 |
| `backend/app/tasks/scheduler.py` | 4 |
| `CLAUDE.md` | 4 |

### Test Files Created (Total: ~14)

| File | Sprint |
|------|--------|
| `frontend/src/__tests__/privacy-page.test.tsx` | 1 |
| `frontend/src/__tests__/terms-page.test.tsx` | 1 |
| `frontend/src/__tests__/sebi-disclaimer.test.tsx` | 1 |
| `frontend/src/__tests__/signal-card-disclaimer.test.tsx` | 1 |
| `frontend/src/__tests__/signin-consent.test.tsx` | 1 |
| `frontend/src/__tests__/navbar-legal-links.test.tsx` | 1 |
| `backend/tests/test_api_consent.py` | 1 |
| `backend/tests/test_telegram_consent.py` | 1 |
| `frontend/src/__tests__/account-page.test.tsx` | 2 |
| `frontend/src/__tests__/display-labels.test.tsx` | 2 |
| `frontend/src/__tests__/contact-page.test.tsx` | 2 |
| `frontend/src/__tests__/how-it-works.test.tsx` | 2 |
| `backend/tests/test_api_account.py` | 2 |
| `frontend/src/__tests__/jurisdiction.test.tsx` | 3 |
| `frontend/src/__tests__/cookie-consent.test.tsx` | 3 |
| `backend/tests/test_audit_log.py` | 4 |
| `backend/tests/test_retention_tasks.py` | 4 |
| `backend/tests/test_compliance.py` | 4 |
| `frontend/src/__tests__/compliance.test.tsx` | 4 |
| `frontend/src/__tests__/refund-policy.test.tsx` | 4 |
| `frontend/src/__tests__/pricing-compliance.test.tsx` | 4 |

---

## Appendix B: Items Requiring Legal Counsel

| Item | Sprint | Why Legal Counsel |
|------|--------|------------------|
| Privacy Policy content | 1 | Must be enforceable under DPDPA 2023 |
| Terms of Service content | 1 | Must be enforceable under Indian Contract Act |
| Blocked country list | 3 | Regulatory analysis per jurisdiction |
| FEMA disclaimer wording | 3 | Must be legally accurate |
| Refund policy wording | 4 | Consumer Protection Act 2019 compliance |
| SEBI RA registration decision | Post-Sprint 2 | Strategic decision: register, reframe, or remove stock signals |
| GST registration | Before Sprint 4 payment integration | Tax compliance |
| Audit log adequacy | 4 | SEBI RA Regulation 24-25 record-keeping |

---

## Appendix C: Risk Mitigation Summary

| Risk (from spec) | Mitigation (this plan) | Sprint |
|-------------------|----------------------|--------|
| No Privacy Policy | Created at `/privacy` | 1 |
| No Terms of Service | Created at `/terms` | 1 |
| No consent mechanism | Consent checkbox + consent log | 1 |
| Disclaimers too small/hidden | Font increase, higher contrast, per-signal disclaimers | 1 |
| No Telegram consent | /start consent flow with inline keyboard | 1 |
| "BUY"/"SELL" language = RA activity | Display-layer reframing to "Bullish"/"Bearish" | 2 |
| No data deletion (DPDPA §12) | DELETE `/api/v1/account` endpoint | 2 |
| No data export (DPDPA §11) | GET `/api/v1/account/export` endpoint | 2 |
| No grievance officer (DPDPA §8(10)) | Contact page with officer info | 2 |
| AI Q&A = personalized advice risk | Prompt guardrails preventing recommendations | 2 |
| No geographic restrictions | Jurisdiction selector + geo-blocking | 3 |
| Forex FEMA exposure | Cross-currency disclaimers | 3 |
| No cookie consent | Cookie consent banner | 3 |
| No signal retraction mechanism | Retraction model + endpoint | 3 |
| No audit trail | Immutable audit_log table | 4 |
| No record retention policy | Weekly retention task | 4 |
| No compliance regression tests | Dedicated compliance test suite | 4 |

---

*Plan created: 24 March 2026 | Based on regulatory compliance spec v1.0.0*
