# SignalFlow AI — Regulatory & Product Compliance Review

> **Date**: 24 March 2026  
> **Version**: v1.0.0 (post-Sprint 10)  
> **Methodology**: 6-perspective regulatory audit  
> **Status**: DRAFT — Requires legal counsel review before implementation  
> **Classification**: CONFIDENTIAL

---

## Executive Summary

SignalFlow AI faces **significant regulatory exposure** across multiple jurisdictions. The platform generates specific buy/sell signals with entry, target, and stop-loss prices on SEBI-regulated Indian securities, unregulated crypto assets, and RBI-regulated forex pairs — all without any regulatory registration, proper legal documentation, or backend authentication.

### Top 5 Regulatory Risks (by severity)

| # | Risk | Severity | Regulatory Body | Potential Penalty |
|---|------|----------|----------------|-------------------|
| 1 | **Operating as unregistered Research Analyst** — Generating specific buy/sell/hold recommendations with price targets on NSE securities | CRITICAL | SEBI | Up to ₹25 crore fine or 10 years imprisonment (SEBI Act §24) |
| 2 | **No Privacy Policy or Terms of Service** — Collecting personal data (Telegram chat IDs, email, trade logs) without legal basis or user consent | CRITICAL | MeitY (DPDPA 2023) / GDPR | ₹250 crore fine under DPDPA §33; €20M or 4% global revenue under GDPR Art. 83 |
| 3 | **No backend API authentication** — All 25+ REST endpoints publicly accessible; user data exposed without access controls | CRITICAL | DPDPA / GDPR / SEBI | Regulatory action for inadequate data security (DPDPA §8(4)) |
| 4 | **Forex signal delivery without authorization** — Providing forex trading recommendations may violate FEMA and RBI guidelines | HIGH | RBI / FEMA | Penalties under FEMA §13 (up to three times the sum involved) |
| 5 | **Monetization without GST/payment compliance** — Charging ₹749/mo without GST registration, payment gateway compliance, or refund policy | HIGH | GST Council / RBI | GST evasion penalties + payment aggregator violations |

### Overall Assessment

**Commercial launch is NOT legally safe in the current state.** The platform requires a minimum of 2-3 weeks of compliance work before accepting any paying users. Personal use is lower risk but still carries exposure for Indian stock signals.

---

## Part 1: SEBI Compliance Analysis

### 1.1 Research Analyst (RA) Regulations (SEBI RA Regulations 2014, amended 2020)

**Regulation**: SEBI (Research Analysts) Regulations, 2014 (Last amended 2020)  
**Relevant sections**: Regulation 2(1)(u), 2(1)(v), 2(1)(w), 3(1), 12, 16, 17, 18, 24, 25

#### What constitutes a "Research Report"?

Per Regulation 2(1)(w):
> "research report" means any written or electronic communication that includes research analysis, research recommendation or an opinion concerning securities or public offer, providing a basis for investment decisions

#### Does SignalFlow qualify?

| Element | SignalFlow's Output | RA Requirement Met? |
|---------|-------------------|---------------------|
| Written/electronic communication | Yes — dashboard + Telegram signals | ✅ Yes |
| Includes research analysis | Yes — technical indicators (RSI, MACD, Bollinger, SMA, ATR) | ✅ Yes |
| Research recommendation | Yes — explicit BUY/SELL/STRONG_BUY/STRONG_SELL | ✅ Yes |
| Opinion concerning securities | Yes — on NSE-listed NIFTY 50 constituents | ✅ Yes |
| Provides basis for investment decisions | Yes — entry price, target price, stop-loss, timeframe, AI reasoning | ✅ Yes |

**Finding RA-1 [CRITICAL]**: SignalFlow's Indian stock signals constitute "research reports" under SEBI RA Regulations. Operating without registration is a violation of Regulation 3(1).

#### Registration Requirements (Regulation 3-8)

| Requirement | Status | Gap |
|-------------|--------|-----|
| Registration with SEBI as Research Analyst | ❌ Not registered | Must register or remove stock signals |
| Qualification: NISM Series XV certification | ❌ Not held | Requires passing NISM Research Analyst exam |
| Qualification: Graduate + 2 years experience OR Postgraduate + relevant knowledge | ⚠️ Partial — primary user has M.Com | M.Com qualifies as postgrad in commerce |
| Net worth: ₹5 lakhs (individual) / ₹50 lakhs (body corporate) | Unknown | Must verify |
| Compliance officer appointment (for body corporate) | ❌ N/A | Required if registering as company |
| Registration fee: ₹1 lakh (individual), ₹5 lakhs (body corporate), valid 3 years | ❌ Not paid | Required for registration |

**Finding RA-2 [CRITICAL]**: Without SEBI RA registration, commercially distributing Indian stock signals (even free) violates Regulation 3(1). Penalties under SEBI Act §24: imprisonment up to 10 years, or fine up to ₹25 crore, or both.

#### Disclosure Requirements (Regulation 16-20)

If registered, the following disclosures are mandatory on every signal/report:

| Disclosure | Required By | Current State |
|------------|-------------|---------------|
| SEBI registration number | Reg. 16(1) | ❌ Missing (not registered) |
| Analyst's holdings in recommended security | Reg. 16(2)(a) | ❌ Missing |
| Conflict of interest statement | Reg. 16(2)(b) | ❌ Missing |
| Compensation disclosure | Reg. 16(2)(c) | ❌ Missing |
| Track record of past recommendations (12 months) | Reg. 17 | ⚠️ Partial — track record page exists but unverified |
| Disclaimer text (prescribed wording) | Reg. 18 | ⚠️ Exists but doesn't meet prescribed format |
| Risk factors specific to recommendation | Reg. 18(2) | ❌ Missing per-signal risk factors |
| Reasonable basis for recommendation | Reg. 20 | ✅ AI reasoning provides this |

**Finding RA-3 [HIGH]**: Even if registered, current disclaimers do not meet SEBI's prescribed format. Regulation 18 requires specific language including SEBI registration number and explicit risk warnings.

#### Record-Keeping (Regulation 24-25)

| Requirement | Period | Current State |
|-------------|--------|---------------|
| All research reports | 5 years | ⚠️ Signals stored in DB but no archival policy |
| Rationale for recommendations | 5 years | ✅ AI reasoning and technical_data stored |
| Client communication records | 5 years | ❌ Telegram messages not archived server-side |
| Conflict of interest records | 5 years | ❌ Not tracked |

**Finding RA-4 [MEDIUM]**: Record-keeping is partially met through database storage, but lacks formal archival policy and Telegram message logging.

### 1.2 Investment Adviser (IA) Regulations (SEBI IA Regulations 2013, amended 2020)

**Regulation**: SEBI (Investment Advisers) Regulations, 2013

#### RA vs IA Classification

| Factor | Research Analyst | Investment Adviser |
|--------|-----------------|-------------------|
| Service type | General research/recommendations to public | Personalized advice to specific clients |
| Client relationship | Broadcast (one-to-many) | One-to-one advisory |
| Fee structure | Subscription-based is common | Fee-based or AUM-based |
| Fiduciary duty | Standard duty of care | Enhanced fiduciary duty |

**Finding IA-1 [MEDIUM]**: SignalFlow currently operates as a broadcast service (RA territory). However, the "Ask AI" feature (POST /ai/ask) where users ask personalized questions about their portfolio/positions could be interpreted as personalized investment advice, pushing into IA territory.

**Recommendation**: Either remove the AI Q&A feature entirely, or strictly limit it to educational/informational queries and never provide personalized buy/sell recommendations in responses. Add explicit guardrails in the Claude prompt.

### 1.3 SEBI (PFUTP) Regulations 2003

**Regulation**: SEBI (Prohibition of Fraudulent and Unfair Trade Practices) Regulations, 2003

| Risk | Regulation | Applicability |
|------|-----------|---------------|
| Misleading statements about signal accuracy | Reg. 4(1) | ⚠️ If win rate is advertised without verification methodology |
| Market manipulation through coordinated signals | Reg. 4(2)(e) | LOW — signals are algorithmic, not targeted manipulation |
| Publishing misleading research | Reg. 4(2)(k) | ⚠️ If AI-generated reasoning is presented as human analysis |

**Finding PFUTP-1 [MEDIUM]**: Win rate statistics must be independently verifiable. Signal resolution logic (checking if target/stop was hit) must be audit-proof and not cherry-pick favorable outcomes.

**Finding PFUTP-2 [MEDIUM]**: AI-generated signals must clearly state they are AI-generated, not human-analyst outputs. Current disclaimer says "AI-generated analysis" which is good, but it must be more prominent — not in 10px font in the footer.

### 1.4 SEBI Advertising Guidelines

**Circular**: SEBI/HO/MIRSD/DOP/CIR/P/2020/137

| Requirement | Current State |
|-------------|---------------|
| No guaranteed returns language | ✅ No guarantees found |
| Past performance disclaimer | ⚠️ Generic — needs "Past performance does not guarantee future results" on every performance metric |
| Risk-return trade-off disclosure | ❌ Missing |
| Equal prominence of risk warnings vs performance claims | ❌ Win rate chart has no equal-prominence risk warning |
| SEBI registration number in all advertising | ❌ Not registered |

**Finding ADV-1 [HIGH]**: If the pricing page (₹749/mo Pro tier) is live, it constitutes advertising of financial services. Without SEBI registration, advertising investment advisory services is a separate violation under SEBI Intermediaries Regulations.

---

## Part 2: RBI + Indian IT Law Compliance

### 2.1 Digital Personal Data Protection Act 2023 (DPDPA)

**Status**: Enacted August 2023. Rules expected 2025-2026. Even without final rules, the Act's principles apply.

#### Data Fiduciary Obligations (DPDPA §4-11)

| Obligation | Section | Current State | Gap |
|-----------|---------|---------------|-----|
| Lawful purpose for data processing | §4 | ❌ No stated purpose | Need privacy policy with explicit purpose |
| Consent before processing personal data | §6 | ❌ No consent mechanism | Need consent flow before data collection |
| Notice to data principal before collection | §5 | ❌ No notice given | Need privacy notice at registration |
| Purpose limitation | §5(1)(a) | ❌ No stated purposes | Must limit to stated purposes only |
| Data minimization | §4(2) | ⚠️ Collecting Telegram chat IDs + email + trade logs — reasonable for service delivery | Acceptable if stated in privacy policy |
| Storage limitation | §8(7) | ❌ No data retention policy | Must define retention periods |
| Data accuracy | §8(3) | ⚠️ Market data may have delays/errors | Disclose data source limitations |
| Right to erasure | §12(1) | ❌ No data deletion endpoint | Must implement account deletion |
| Right to access | §11 | ❌ No data export feature | Must implement data portability |
| Grievance officer appointment | §8(10) | ❌ Not appointed | Required for data fiduciaries |
| Data breach notification (72 hours to DPB) | §8(6) | ❌ No incident response plan | Must implement |
| Children's data (under 18) | §9 | ❌ No age verification | Need age gate if platform accessible to minors |

**Finding DPDPA-1 [CRITICAL]**: Platform collects personal data (Telegram chat ID, email via NextAuth, trade logs, watchlist, alert preferences) without any legal basis, consent mechanism, or privacy notice. This violates DPDPA §4-6.

**Finding DPDPA-2 [CRITICAL]**: No data deletion capability exists. DPDPA §12 grants every data principal the right to erasure. The only "delete" endpoint is for price alerts — no account deletion, no data export.

**Finding DPDPA-3 [HIGH]**: No grievance redressal mechanism. DPDPA §8(10) requires appointment of a grievance officer and a clear complaints process.

#### Data Collected by SignalFlow

| Data Point | Where Stored | Purpose | Minimization OK? |
|-----------|-------------|---------|------------------|
| Email address | NextAuth session (JWT) | Authentication | ✅ Necessary |
| Telegram chat ID | `alert_configs.telegram_chat_id` (PostgreSQL) | Alert delivery | ✅ Necessary |
| Username | `alert_configs.username` | Display | ⚠️ Optional — could be removed |
| Trade logs | `trades` table | Portfolio tracking | ✅ Necessary for feature |
| Watchlist | `alert_configs.watchlist` | Custom alerts | ✅ Necessary for feature |
| Alert preferences | `alert_configs.*` | Alert filtering | ✅ Necessary |
| Signal viewing history | Tier store (localStorage) | Feature gating | ✅ Client-side only |
| IP addresses | Server logs | Security | ✅ Standard practice |

### 2.2 Information Technology Act 2000

#### IT Act Compliance

| Requirement | Section | Current State |
|-------------|---------|---------------|
| Reasonable security practices | §43A | ❌ No backend auth, no encryption at rest |
| Privacy policy publication | §43A + IT Rules 2011, Rule 4 | ❌ No privacy policy anywhere |
| Sensitive personal data handling | IT Rules 2011, Rule 3 | ⚠️ Financial data (trade logs) may qualify as SPDI |
| Intermediary guidelines (IT Intermediary Rules 2021) | §79 | May apply if user-generated content exists (AI Q&A responses cached) |

**Finding IT-1 [HIGH]**: IT Rules 2011, Rule 4 requires any entity collecting personal information to publish a privacy policy on its website. SignalFlow has no privacy policy. This is a straightforward compliance failure.

### 2.3 RBI + FEMA — Forex Regulations

**Key Regulations**:
- Foreign Exchange Management Act 1999 (FEMA)
- RBI Master Direction on forex trading
- RBI circular on Electronic Trading Platforms (ETPs)

| Issue | Regulation | Analysis |
|-------|-----------|----------|
| Forex signal delivery to Indian residents | FEMA §3-4 | ⚠️ Forex trading in India is restricted to authorized dealers (banks) and recognized exchanges. Retail forex (off-exchange, leveraged) is **illegal for Indian residents**. |
| Forex pairs in signals | RBI | Only INR-paired forex (USD/INR, etc.) on recognized exchanges (NSE, BSE, MSEI) is legal. Cross-currency pairs (EUR/USD, GBP/JPY) operate in a gray area. |
| Recommending forex trades | FEMA §13 | Recommending illegal activity could expose the platform to liability regardless of its position as "information service" |

**Finding FOREX-1 [HIGH]**: Delivering forex signals on EUR/USD, GBP/JPY, and other cross-currency pairs to Indian users is legally risky. While providing *information* is generally legal, providing specific trade recommendations (with entry, target, stop-loss) on instruments that Indian residents cannot legally trade retail could be viewed as facilitating FEMA violations.

**Recommendation**: 
1. Remove cross-currency pairs (EUR/USD, GBP/JPY) for Indian users, OR
2. Add prominent warning: "Forex signals on cross-currency pairs are for informational purposes only. Retail forex trading on non-exchange platforms is not permitted for Indian residents under FEMA."
3. Keep USD/INR signals (legal on NSE/BSE)

### 2.4 Payment Compliance

| Requirement | Status |
|-------------|--------|
| GST registration (if revenue > ₹20 lakhs) | ❌ Not registered (not needed at current scale, but needed before meaningful revenue) |
| GST on digital services (18%) | ❌ Not accounted for in ₹749 pricing |
| Payment gateway compliance (RBI PA/PG Guidelines 2020) | ❌ "Razorpay/Stripe coming soon" — not implemented |
| Refund/cancellation policy | ❌ Missing |
| Invoice generation | ❌ No billing system |

**Finding PAY-1 [MEDIUM]**: Payment processing is not yet implemented (pricing page switches tiers in localStorage only). This becomes CRITICAL before accepting real money. Razorpay/Stripe integration must comply with RBI's PA/PG (Payment Aggregator/Payment Gateway) guidelines.

---

## Part 3: Global Regulatory Exposure

### 3.1 United States — SEC/FINRA

**Question**: Does serving crypto/forex signals to US users require registration?

| Scenario | Regulation | Risk |
|----------|-----------|------|
| Crypto signals accessible to US users | Securities Act 1933 §5, Howey Test | MEDIUM — If crypto tokens are classified as securities (ongoing SEC litigation), providing buy/sell recommendations may require SEC Investment Adviser registration |
| Forex signals to US users | Commodity Exchange Act, NFA membership | HIGH — Forex advisory services in the US require NFA registration and CFTC compliance |
| Indian stock signals to US users | SEC Reg S | LOW — Foreign securities generally not covered unless specifically marketed to US persons |

**Finding SEC-1 [MEDIUM]**: The platform is globally accessible with no geographic restrictions. If US users access crypto or forex signals, SignalFlow could face SEC/CFTC/NFA jurisdiction claims. The simplest mitigation is a geo-block on US IPs or a jurisdiction acknowledgment during sign-up.

### 3.2 European Union — GDPR + MiCA

#### GDPR (if EU users access the platform)

| Right | GDPR Article | Current State |
|-------|-------------|---------------|
| Right to be informed (privacy notice) | Art. 13-14 | ❌ No privacy notice |
| Right of access | Art. 15 | ❌ No data export |
| Right to rectification | Art. 16 | ❌ Not implemented |
| Right to erasure ("right to be forgotten") | Art. 17 | ❌ Not implemented |
| Right to data portability | Art. 20 | ❌ Not implemented |
| Lawful basis for processing | Art. 6 | ❌ No stated legal basis |
| Data Protection Officer requirement | Art. 37 | ❌ May not be required (small scale) |
| Cross-border data transfer safeguards | Art. 44-49 | ❌ Data stored presumably in India/US (Railway hosting) |
| Cookie consent | ePrivacy Directive | ❌ No cookie banner (localStorage is used, but session cookies from NextAuth need consent) |
| Data processing agreements with processors | Art. 28 | ❌ No DPA with Anthropic, Railway, etc. |

**Finding GDPR-1 [HIGH]**: If EU users can access the platform (which they currently can — no geo-restriction), GDPR applies extraterritorially per Art. 3(2). The lack of privacy notice, consent mechanism, data subject rights endpoints, and cross-border transfer safeguards is a comprehensive GDPR failure.

#### MiCA (Markets in Crypto-Assets Regulation)

**Status**: Fully applicable from 30 December 2024.

| Question | Analysis |
|----------|---------|
| Does MiCA apply to crypto advisory? | MiCA primarily regulates issuers and service providers. Crypto *advisory* services fall under MiFID II if personalized, or may be unregulated if general information |
| Buy/sell signals with price targets | Could be classified as "investment recommendation" under MAR (Market Abuse Regulation) if related to instruments admitted to EU trading venues |

**Finding MiCA-1 [LOW]**: MiCA risk is LOW at current scale but becomes relevant if actively marketing to EU users or if any tracked crypto tokens are classified as MiCA-regulated instruments.

### 3.3 United Kingdom — FCA

| Regulation | Risk |
|-----------|------|
| Financial Promotions Regime (FSMA §21) | MEDIUM — Any communication that invites/induces investment activity to UK persons must be issued or approved by FCA-authorized firm |
| Consumer Duty 2023 | If platform has UK users, FCA expects duty of care including clear risk warnings |

**Finding FCA-1 [MEDIUM]**: UK's financial promotions regime is one of the strictest globally. SignalFlow's buy/sell signals with specific price targets clearly constitute "financial promotions" if communicated to UK persons. Without FCA authorization, this is a criminal offense under FSMA §25 (up to 2 years imprisonment).

### 3.4 Geographic Strategy Summary

| Jurisdiction | Risk Level | Recommendation |
|-------------|-----------|----------------|
| **India** | CRITICAL | Must resolve SEBI RA registration or legal positioning before commercial launch |
| **United States** | HIGH | Block US IPs or implement jurisdiction acknowledgment |
| **European Union** | HIGH | Block or implement GDPR compliance suite |
| **United Kingdom** | MEDIUM-HIGH | Block or obtain FCA permissions |
| **Singapore** | MEDIUM | MAS advisory license may be needed |
| **Rest of World** | VARIES | Default geo-block with opt-in for low-risk jurisdictions |

---

## Part 4: Product Manager — Trust & Safety

### 4.1 Disclaimer Audit

| Location | Current State | Issue |
|----------|---------------|-------|
| Website footer (SebiDisclaimer.tsx) | 10px font, low contrast (text-text-muted) | **Inadequate** — Too small/low-contrast to constitute meaningful disclosure. SEBI and consumer protection frameworks require prominent, readable disclaimers. |
| Dashboard inline disclaimer | 12px, muted color | **Inadequate** — same issue |
| Signal detail page | 10px, muted | **Inadequate** |
| Telegram welcome message | One-line disclaimer at end | **Inadequate** — should be a separate, prominent message |
| Health endpoint | JSON field "disclaimer" | ✅ OK for API consumers |
| How It Works page | Larger section with explanation | ⚠️ Better, but still not prominent enough |
| Pricing page | No disclaimer at all | **Missing** — pricing page must have risk warnings |
| Signal cards (on dashboard) | No per-signal disclaimer | **Missing** |
| Telegram signal alerts | No disclaimer per alert | **Missing** |

**Finding TRUST-1 [HIGH]**: Disclaimers exist but are systematically insufficient. The 10px font in `SebiDisclaimer.tsx` and muted colors make the disclaimer practically invisible. A reasonable user test: "Can my mother read this disclaimer on her phone without squinting?" Current answer: No.

**Finding TRUST-2 [HIGH]**: Signal-level disclaimers are missing. Each signal card and each Telegram alert should carry a brief risk reminder, not just the global footer.

### 4.2 Risk Communication

| Best Practice | Current State |
|--------------|---------------|
| Every signal shows maximum possible loss | ✅ Stop-loss is provided |
| Risk calculator available | ✅ RiskCalculator component exists on signal detail |
| Risk relative to portfolio size | ❌ Not implemented |
| Risk aggregation (if following multiple signals) | ❌ Not implemented |
| "What could go wrong" section per signal | ❌ AI reasoning is only bullish/bearish, no counter-scenario |
| Beginner risk education | ⚠️ How It Works page exists but no interactive tutorials |

**Finding TRUST-3 [MEDIUM]**: AI reasoning text only presents the *case for* the signal, never the *case against*. The Claude prompt should include: "Also briefly mention one key risk or scenario where this signal could fail."

### 4.3 Consent & Onboarding

| Required Consent | Current Implementation |
|-----------------|----------------------|
| Terms of Service acceptance | ❌ No ToS exists |
| Privacy Policy acknowledgment | ❌ No PP exists |
| Risk acknowledgment ("I understand these are not investment advice") | ❌ No explicit consent |
| Marketing communications opt-in | ❌ No marketing consent |
| Cookie/storage consent | ❌ No consent banner |
| Age verification (18+) | ❌ No age check |
| Telegram bot consent | ❌ /start just registers — no consent step |

**Finding TRUST-4 [CRITICAL]**: Zero consent mechanisms exist. Before any data collection or signal delivery, users must explicitly accept ToS, acknowledge risks, and consent to data processing. The Telegram /start command must include a consent step.

### 4.4 Incident Response

**Scenario**: A STRONG_BUY signal on HDFCBANK with 92% confidence is generated. 50 users follow it. The stock drops 15% on unexpected news. Users lose money.

| Question | Current Answer |
|----------|---------------|
| Is there a process for signal review/retraction? | ❌ No |
| Can the platform send a retraction/update alert? | ❌ No mechanism |
| Is there a complaints process? | ❌ No |
| Is there liability protection in ToS? | ❌ No ToS |
| Does the platform track if users followed a signal? | ⚠️ Portfolio page exists but voluntary |
| Is there insurance against liability? | ❌ No |

**Finding TRUST-5 [HIGH]**: No incident response process exists for adverse signal outcomes. At minimum, need: (1) ability to send signal updates/retractions, (2) complaints email/form, (3) ToS liability limitation clause.

### 4.5 Data Minimization Audit

| Data Point | Necessary? | Recommendation |
|-----------|-----------|----------------|
| Telegram chat_id | Yes — required for alert delivery | Keep |
| Username (Telegram) | No — display only | Make optional, don't store by default |
| Email (NextAuth) | Yes — authentication | Keep |
| Password hash | Yes — for credentials auth | Keep (but prefer OAuth-only) |
| Trade logs (symbol, entry, exit, P&L) | Yes — for portfolio feature | Keep, but add retention limit (2 years) |
| Watchlist symbols | Yes — for custom alerts | Keep |
| Alert preferences (markets, min_confidence, quiet_hours) | Yes — for alert filtering | Keep |
| IP addresses in logs | Yes — security | Anonymize after 90 days |
| AI Q&A conversation history | ⚠️ Currently not stored server-side | Don't store unless needed; if stored, add retention limit |

**Finding TRUST-6 [LOW]**: Data collection is relatively minimal and purpose-aligned. The main issue is not *what* is collected but that there's no documentation of what's collected and no mechanism for users to see or delete it.

---

## Part 5: Product Manager — Growth & Compliance Balance

### 5.1 Legal Positioning Options

| Positioning | Legal Burden | Revenue Impact | Feasibility |
|------------|-------------|---------------|-------------|
| **Option A: SEBI-Registered Research Analyst** | Heavy — registration, NISM cert, compliance officer, record-keeping, annual audit | Maximum — can charge for stock signals legally | Medium — 3-6 month registration process, ₹1L fee |
| **Option B: Educational/Informational Platform** | Light — no registration needed if genuinely educational | Moderate — can charge for educational content, tools, analytics | High — requires significant reframing of signals |
| **Option C: Technology Platform / Tool** | Minimal — providing tools, not advice | Moderate — charge for platform access, not signal content | High — position as "AI analysis tool" not "signal provider" |
| **Option D: Hybrid — RA for stocks + Educational for crypto/forex** | Medium | High — covers all markets | Medium — complex |

### 5.2 Recommended Positioning: Option C (Technology Platform) — Short Term

**Reframe the entire product** from "signal provider" to "AI-powered market analysis tool":

| Current Language (Risky) | Recommended Language (Safer) |
|-------------------------|------------------------------|
| "BUY HDFCBANK" | "Analysis suggests bullish momentum for HDFCBANK" |
| "STRONG_BUY" / "STRONG_SELL" | "Strongly Bullish" / "Strongly Bearish" |
| "Target Price: ₹1,780" | "Projected resistance level: ₹1,780 based on ATR analysis" |
| "Stop-loss: ₹1,630" | "Key support level: ₹1,630" |
| "Signal" (throughout) | "Analysis" or "Insight" |
| "confidence: 92%" | "Analysis strength: 92%" |
| "entry price" | "Current price" (already exists, just remove "entry" framing) |
| "Signals are not investment advice" (disclaimer) | "This is a technical analysis tool for educational and informational purposes. It does not constitute a recommendation to buy or sell any security." |
| "Buy Signal" (Telegram) | "Bullish Analysis Alert" |

**Critical caveat**: Cosmetic rebranding alone is NOT legally sufficient. SEBI looks at substance, not labels. If the platform walks like a research analyst and quacks like a research analyst, it IS one. True repositioning requires:

1. Removing explicit "BUY"/"SELL" action labels
2. Framing targets/stops as "technical levels" not "trade levels"
3. Never stating "you should buy/sell X"
4. Adding genuine educational content around each analysis
5. Removing timeframes like "2-4 weeks" (implies expected holding period)
6. Removing "entry price" terminology entirely

### 5.3 Impact of Charging Money

| Scenario | Regulatory Burden |
|----------|------------------|
| **100% Free, no revenue** | Lower risk — harder for regulators to argue commercial advisory activity. Still not zero risk for stock signals. |
| **Free tier + Paid Pro (₹749/mo)** | **Significantly increases regulatory burden** — commercial provision of financial analysis. Triggers RA/IA registration requirements more clearly. Also triggers GST, payment compliance, consumer protection. |
| **Free with voluntary donations** | Similar to 100% free but cleaner. Still carries stock signal risk. |
| **Free platform, charge only for tools (backtesting, portfolio)** | Lower risk — charging for tools, not advice. Signals are free "educational content." |

**Finding GROWTH-1 [HIGH]**: The ₹749/mo Pro tier, as currently structured, increases regulatory exposure substantially. Charging money for buy/sell signal access makes the "educational information" defense much weaker. Consider: charge for *tools* (backtesting, portfolio, AI Q&A, export) but keep signal *access* free.

### 5.4 Free Tier Compliance

**Question**: Does the free tier still need full compliance?

**Answer**: Yes. SEBI RA regulations apply regardless of whether a fee is charged. Even free stock research reports trigger registration requirements. DPDPA applies to all personal data processing regardless of payment. The free tier is NOT a compliance loophole.

### 5.5 Marketing Guardrails

| Claim | Legal Status |
|-------|-------------|
| "92% confidence signal" | ⚠️ Must be clearly explained — "confidence" is a model score, not a probability of profit |
| "72% win rate this month" | ⚠️ Must include: past performance disclaimer, methodology disclosure, sample size |
| "AI-powered trading signals" | ❌ "Trading signals" implies actionable trade advice — use "AI-powered market analysis" |
| "Make smarter trading decisions" | ✅ Acceptable — doesn't promise outcomes |
| "Never miss a trading opportunity" | ❌ Implies guaranteed returns/opportunities |
| "Backed by technical analysis and AI" | ✅ Acceptable — factual description |
| "Trusted by X users" | ⚠️ Only if X is verifiable and "trusted" doesn't imply financial trust/fiduciary |

**Finding GROWTH-2 [MEDIUM]**: Marketing copy throughout must be audited. Replace "trading signals" with "market analysis" everywhere. Replace "buy/sell" with "bullish/bearish analysis." Replace "signal confidence" with "analysis strength."

---

## Part 6: Technical Implementation Plan

### 6.1 What Can Be Done in Code vs. Needs Legal Counsel

| Item | Code? | Legal? | Notes |
|------|-------|--------|-------|
| Privacy Policy page | Code (static page) | **Legal review needed** for content | Draft in code, lawyer reviews |
| Terms of Service page | Code (static page) | **Legal review required** | Must be enforceable under Indian Contract Act |
| SEBI registration | ❌ Code cannot solve | **Pure legal action** | 3-6 month process |
| Disclaimer enhancement | ✅ Pure code | Minor legal review | Can implement immediately |
| Consent flows (onboarding) | ✅ Pure code | Legal wording review | Implement checkbox + acceptance tracking |
| Data deletion endpoint | ✅ Pure code | — | Backend DELETE endpoint + frontend UI |
| Data export endpoint | ✅ Pure code | — | GET endpoint returning user data as JSON/CSV |
| Backend API authentication | ✅ Pure code | — | JWT token validation on backend |
| Geographic blocking | ✅ Pure code | — | IP-based or jurisdiction acknowledgment |
| Language reframing (BUY→Bullish) | ✅ Pure code | — | Search-and-replace across codebase |
| Age verification | ✅ Pure code | — | Date of birth or checkbox |
| Cookie consent banner | ✅ Pure code | Legal wording review | Standard cookie consent library |
| Grievance officer details | Code (static page) | Needs appointed person | Display contact details |
| GST registration | ❌ Not code | **Pure legal/tax action** | Required before accepting money |
| Payment integration | ✅ Code + config | Razorpay/Stripe compliance review | Razorpay handles most RBI compliance |
| Incident response plan | Documentation | — | Draft as internal document |
| Record retention policy | Code + documentation | Legal review | Implement auto-archival |

### 6.2 Priority Classification

#### LAUNCH BLOCKERS (Must have before any commercial activity)

| ID | Item | Effort | Sprint |
|----|------|--------|--------|
| LB-1 | Privacy Policy page + content | M | Sprint 1 |
| LB-2 | Terms of Service page + content | M | Sprint 1 |
| LB-3 | Consent flow at registration (ToS + PP acceptance, risk acknowledgment) | M | Sprint 1 |
| LB-4 | Disclaimer overhaul (prominent, readable, per-signal) | S | Sprint 1 |
| LB-5 | Backend API authentication (JWT validation) | L | Sprint 1 |
| LB-6 | Language reframing ("signals" → "analysis", "BUY" → "Bullish", etc.) | M | Sprint 2 |
| LB-7 | Data deletion endpoint + UI | M | Sprint 2 |
| LB-8 | Data export endpoint + UI | S | Sprint 2 |
| LB-9 | Age verification (18+ checkbox) | S | Sprint 2 |
| LB-10 | Grievance officer / contact details page | S | Sprint 2 |
| LB-11 | Indian stock signal legal decision (register as RA, or remove, or reframe) | — | External legal |

#### HIGH PRIORITY (Should have before Pro tier goes live)

| ID | Item | Effort | Sprint |
|----|------|--------|--------|
| HP-1 | Geographic access controls (jurisdiction acknowledgment on sign-up) | M | Sprint 3 |
| HP-2 | Forex signal warning for Indian users (FEMA) | S | Sprint 3 |
| HP-3 | Cookie/storage consent banner | S | Sprint 3 |
| HP-4 | AI Q&A guardrails (prevent personalized advice in responses) | M | Sprint 3 |
| HP-5 | Signal retraction/update mechanism | M | Sprint 3 |
| HP-6 | Complaints/feedback mechanism | S | Sprint 3 |
| HP-7 | Record retention policy + auto-archival | M | Sprint 4 |
| HP-8 | GST registration (external action) | — | Sprint 3 |
| HP-9 | Payment integration with compliance (Razorpay) | L | Sprint 4 |
| HP-10 | Audit trail for all signals (immutable log) | M | Sprint 4 |

#### MEDIUM PRIORITY (v1.2 — 1-2 months post-launch)

| ID | Item | Effort | Sprint |
|----|------|--------|--------|
| MP-1 | GDPR compliance suite (for EU users, or geo-block EU) | L | v1.2 |
| MP-2 | US geo-block or jurisdiction acknowledgment | M | v1.2 |
| MP-3 | Conflict of interest disclosure framework | M | v1.2 |
| MP-4 | Automated compliance monitoring (disclaimer presence checks) | M | v1.2 |
| MP-5 | SEBI RA registration (if proceeding) | XL | External |

#### LOW PRIORITY (v1.3+)

| ID | Item | Effort |
|----|------|--------|
| LP-1 | Data localization compliance (India data storage) | L |
| LP-2 | FCA/MiCA compliance (if expanding to UK/EU) | XL |
| LP-3 | Professional indemnity insurance | External |
| LP-4 | Independent audit of signal accuracy methodology | External |

---

## Part 7: Legal Classification Analysis

### Is SignalFlow a Research Analyst, Investment Adviser, Educational Tool, or Information Service?

#### Substance-Over-Form Test

SEBI applies a "substance over form" approach. Labels don't matter; actual activity does.

| Factor | SignalFlow's Activity | Classification Implication |
|--------|---------------------|---------------------------|
| Provides specific buy/sell recommendations | Yes — STRONG_BUY, BUY, SELL, STRONG_SELL | **Research Analyst** |
| Includes price targets | Yes — target_price, stop_loss | **Research Analyst** |
| Uses technical analysis | Yes — RSI, MACD, Bollinger, SMA, ATR | **Research Analyst** |
| Covers specific SEBI-regulated securities | Yes — NIFTY 50 constituents on NSE | **Research Analyst** |
| Personalized to individual client situation | No — broadcast to all users | Not Investment Adviser |
| Charges a fee | Yes — ₹749/mo Pro tier | Makes RA registration more urgent |
| Uses AI, not human analyst | Yes — but doesn't change classification | Doesn't exempt from RA requirements |
| Platform claims "not investment advice" | Yes — but disclaimer doesn't override substance | Disclaimer is not a legal shield |

#### Classification Verdict

| Market | Current Classification | Risk |
|--------|----------------------|------|
| **Indian Stocks** | **Research Analyst** activity — specific buy/sell on SEBI securities with targets/stops | CRITICAL — needs registration or structural change |
| **Cryptocurrency** | **Unregulated** in India — no specific crypto advisory license exists (crypto is neither "security" nor "commodity" under Indian law currently) | LOW in India; MEDIUM in US/EU |
| **Forex** | **Gray area** — informational analysis is likely OK, but specific trade recommendations on cross-currency pairs raise FEMA concerns | HIGH for cross-pairs, LOW for USD/INR |

#### Key Legal Precedent

SEBI has taken action against unregistered entities providing stock tips/recommendations:
- **SEBI vs. Investment Guru** (2019): Unregistered entity providing stock tips via WhatsApp — ₹52 lakh penalty
- **SEBI vs. Sure Shot Returns** (2020): Social media stock tips without registration — ₹25 lakh penalty + disgorgement
- **SEBI Circular SEBI/HO/MIRSD/MIRSD-PoD-1/P/CIR/2023/58**: Clarified that even informal/free stock recommendations on digital platforms require RA registration

These precedents establish that: (1) medium of delivery (app/Telegram) doesn't matter, (2) "free" doesn't exempt you, (3) "AI-generated" doesn't exempt you, (4) disclaimers don't override substance.

---

## Part 8: Recommended Legal Positioning

### Recommended Strategy: "AI Market Analysis & Education Platform" (Option C+)

#### Core Positioning

**What to tell regulators/in legal documents:**
> "SignalFlow AI is an AI-powered technical analysis and market education platform. It processes publicly available market data using standard technical indicators (RSI, MACD, SMA, Bollinger Bands, ATR) and displays the results as educational market analysis. It does not provide personalized investment recommendations or act as an investment intermediary. Users are responsible for their own investment decisions."

#### Structural Changes Required to Support This Positioning

| Change | Effort | Impact on UX |
|--------|--------|-------------|
| Replace "BUY"/"SELL" with "Bullish"/"Bearish" | S | Minimal — users adapt quickly |
| Replace "STRONG_BUY"/"STRONG_SELL" with "Strongly Bullish"/"Strongly Bearish" | S | Minimal |
| Replace "Signal" with "Analysis" or "Insight" throughout | M | Moderate — 100+ references |
| Replace "Target Price" with "Projected Resistance/Support Level" | S | Low |
| Replace "Stop-Loss" with "Key Support/Resistance Level" | S | Low |
| Remove explicit "Entry" price framing | S | None — "Current Price" already exists |
| Replace "Confidence: 92%" with "Analysis Strength: 92%" | S | Minimal |
| Remove "Timeframe: 2-4 weeks" (implies holding period) | S | Moderate — useful info lost |
| Add educational context to every analysis | M | Positive — adds value |
| Replace "Signal History" with "Analysis History" | S | None |
| Replace "Win Rate" with "Analysis Accuracy" | S | None |
| Add "How to Read This" expandable section per analysis | M | Positive |

#### What This Positioning Does NOT Protect Against

- If SEBI determines that "Bullish Analysis Strength 92% with Projected Resistance ₹1,780 and Key Support ₹1,630 within 2-4 weeks" is substantively the same as a buy recommendation (which it arguably is), registration is still required
- This positioning buys time and reduces risk but is NOT a guarantee of regulatory safety
- For long-term commercial operation on Indian stocks, SEBI RA registration is the only truly safe path

### Recommended Parallel Track

| Timeline | Action |
|----------|--------|
| **Now (Sprint 1-2)** | Implement all code-level compliance (privacy policy, ToS, consent, disclaimers, language reframing) |
| **Month 1-2** | Consult SEBI-registered compliance firm about RA registration viability |
| **Month 2-3** | If pursuing RA: begin registration. If not: remove Indian stock signals entirely and focus on crypto/forex |
| **Month 3+** | If RA approved: restore full stock signals with proper disclosures. If not: operate as crypto/forex analysis platform |

---

## Part 9: Geographic Strategy

### Recommended Phase 1 (Launch)

| Market | Serve? | Rationale |
|--------|--------|-----------|
| **India (stocks)** | ⚠️ With reframed language + legal disclaimer | Core market but highest risk. Reframe as educational analysis. Pursue RA registration in parallel |
| **India (crypto)** | ✅ Yes | No specific crypto RA regulation in India yet |
| **India (forex — USD/INR)** | ✅ Yes with disclaimer | INR pairs tradeable on NSE |
| **India (forex — cross-pairs)** | ⚠️ With FEMA warning | Add prominent FEMA disclaimer |
| **United States** | ❌ Block or restrict | SEC/NFA compliance is expensive; not worth the risk at current scale |
| **European Union** | ❌ Block unless GDPR-compliant | GDPR fines are severe; implement geo-block until compliance work is done |
| **United Kingdom** | ❌ Block | FCA financial promotions regime — criminal penalties |
| **Rest of World** | ⚠️ Default allow with jurisdiction acknowledgment | Require users to acknowledge their local jurisdiction during sign-up |

### Implementation

```
1. Sign-up flow: "Select your country of residence"
2. If US/UK/EU → "Sorry, SignalFlow is not yet available in your jurisdiction"
3. If India → proceed with Indian-specific disclaimers
4. If Other → proceed with general disclaimers + jurisdiction acknowledgment
```

---

## Part 10: Implementation Sprint Plan

### Sprint 1: Legal Foundation (Week 1-2) — LAUNCH BLOCKER

**Goal**: Basic legal documentation and consent infrastructure

| # | Task | Files to Create/Modify | Effort |
|---|------|----------------------|--------|
| 1.1 | **Create Privacy Policy page** | `frontend/src/app/privacy/page.tsx` (new) | M |
| 1.2 | **Create Terms of Service page** | `frontend/src/app/terms/page.tsx` (new) | M |
| 1.3 | **Enhance SebiDisclaimer component** — larger font (14px+), higher contrast, per SEBI-like format | `frontend/src/components/shared/SebiDisclaimer.tsx` | S |
| 1.4 | **Add per-signal disclaimer** to SignalCard component | `frontend/src/components/signals/SignalCard.tsx` | S |
| 1.5 | **Add disclaimer to every Telegram signal alert** | `backend/app/services/alerts/formatter.py` | S |
| 1.6 | **Consent flow at registration** — ToS + PP checkbox, risk acknowledgment, age verification (18+) | `frontend/src/app/auth/signin/page.tsx`, `frontend/src/components/shared/ConsentDialog.tsx` (new) | M |
| 1.7 | **Store consent acceptance** — timestamp + version of ToS/PP accepted | `backend/app/models/` (new model), migration | M |
| 1.8 | **Telegram /start consent step** — require explicit acknowledgment before registering | `backend/app/services/alerts/telegram_bot.py` | S |
| 1.9 | **Backend API auth enforcement** — validate JWT from NextAuth on backend endpoints | `backend/app/api/` (middleware), all route files | L |
| 1.10 | **Add Privacy Policy + ToS links to footer/navbar** | `frontend/src/components/shared/SebiDisclaimer.tsx`, `Navbar.tsx` | S |

### Sprint 2: Data Rights & Language (Week 3-4)

**Goal**: DPDPA/GDPR data rights + product language reframing

| # | Task | Files to Create/Modify | Effort |
|---|------|----------------------|--------|
| 2.1 | **Account deletion endpoint** — DELETE /api/v1/account — removes all user data (alert configs, trades, watchlist) | `backend/app/api/account.py` (new), `backend/app/api/router.py` | M |
| 2.2 | **Data export endpoint** — GET /api/v1/account/export — returns all user data as JSON | `backend/app/api/account.py` | M |
| 2.3 | **Account settings page** with delete/export options | `frontend/src/app/account/page.tsx` (new) | M |
| 2.4 | **Language reframing — signal types** — BUY→Bullish, SELL→Bearish, STRONG_BUY→Strongly Bullish, STRONG_SELL→Strongly Bearish | `backend/app/models/signal.py`, `backend/app/services/signal_gen/`, `backend/app/services/alerts/formatter.py`, `frontend/src/lib/types.ts`, `frontend/src/lib/constants.ts`, all component files referencing signal types | L |
| 2.5 | **Language reframing — terminology** — "target"→"resistance level", "stop-loss"→"support level", "signal"→"analysis", "confidence"→"analysis strength" | All frontend components, all backend formatters | L |
| 2.6 | **Age verification** — add date of birth or 18+ checkbox to registration | `frontend/src/app/auth/signin/page.tsx`, consent model | S |
| 2.7 | **Grievance officer / Contact page** | `frontend/src/app/contact/page.tsx` (new) | S |
| 2.8 | **Telegram disclaimer per signal message** | `backend/app/services/alerts/formatter.py` — add to `format_signal_alert`, `format_morning_brief`, etc. | S |
| 2.9 | **Claude prompt guardrails** — prevent AI Q&A from giving personalized buy/sell advice | `backend/app/services/ai_engine/prompts.py` | S |
| 2.10 | **Update /how-it-works page** with methodology disclosure and analysis accuracy methodology | `frontend/src/app/how-it-works/page.tsx` | M |

### Sprint 3: Geographic & Access Controls (Week 5-6)

**Goal**: Geographic restrictions + forex compliance + advanced consent

| # | Task | Files to Create/Modify | Effort |
|---|------|----------------------|--------|
| 3.1 | **Jurisdiction selection on sign-up** — country selector with US/UK/EU blocking | `frontend/src/app/auth/signin/page.tsx`, `frontend/src/components/shared/ConsentDialog.tsx` | M |
| 3.2 | **Geo-restriction middleware** — backend check on user's declared jurisdiction | `backend/app/api/` (middleware) | M |
| 3.3 | **Forex FEMA disclaimer** — prominent warning on cross-currency pair analyses for Indian users | `frontend/src/components/signals/SignalCard.tsx`, `backend/app/services/alerts/formatter.py` | S |
| 3.4 | **Cookie consent banner** | `frontend/src/components/shared/CookieConsent.tsx` (new), `frontend/src/app/layout.tsx` | S |
| 3.5 | **Signal retraction mechanism** — ability to mark an analysis as "superseded" or "retracted" | `backend/app/models/signal.py` (add retraction fields), `backend/app/api/signals.py`, `frontend/src/components/signals/SignalCard.tsx` | M |
| 3.6 | **Complaints/feedback form** | `frontend/src/app/contact/page.tsx` (enhance), `backend/app/api/feedback.py` (check existing) | S |
| 3.7 | **AI Q&A rate limiting** — prevent abuse of Claude API through AI Q&A | `backend/app/api/ai_qa.py` | S |
| 3.8 | **Remove "entry price" terminology** from all user-facing surfaces | Frontend components, backend formatters | S |
| 3.9 | **Add educational tooltip/expandable per analysis** — "Why is RSI at 62.7 important?" | `frontend/src/components/signals/` (enhance IndicatorPill/tooltip) | M |
| 3.10 | **Risk counter-scenario in AI reasoning** — update Claude prompt to include one risk factor | `backend/app/services/ai_engine/prompts.py` | S |

### Sprint 4: Payment Compliance & Hardening (Week 7-8)

**Goal**: Safe monetization + long-term compliance infrastructure

| # | Task | Files to Create/Modify | Effort |
|---|------|----------------------|--------|
| 4.1 | **Razorpay integration** with proper compliance (refund policy, GST) | `backend/app/api/payments.py` (new), `frontend/src/app/pricing/page.tsx` | L |
| 4.2 | **Refund/cancellation policy page** | `frontend/src/app/refund-policy/page.tsx` (new) | S |
| 4.3 | **Invoice generation** on payment | `backend/app/services/payments/` (new) | M |
| 4.4 | **Record retention policy implementation** — auto-archive signals older than 5 years, log retention | `backend/app/tasks/` (archival task) | M |
| 4.5 | **Immutable audit log** for all analyses generated | `backend/app/models/` (audit_log table), `backend/app/services/signal_gen/generator.py` | M |
| 4.6 | **Compliance dashboard** — internal page showing disclaimer presence, consent rates, data deletion requests | `frontend/src/app/admin/compliance/page.tsx` (new) | L |
| 4.7 | **Pricing page compliance** — add risk warnings, past performance disclaimer, "not SEBI registered" to pricing page | `frontend/src/app/pricing/page.tsx` | S |
| 4.8 | **Data breach notification template** — pre-drafted notification for DPDPA §8(6) 72-hour requirement | `docs/compliance/data-breach-template.md` (new) | S |
| 4.9 | **Update README and CLAUDE.md** with compliance architecture | `README.md`, `CLAUDE.md` | S |
| 4.10 | **Comprehensive compliance test suite** — test that disclaimers are present, consent enforced, auth required | `backend/tests/test_compliance.py` (new), `frontend/src/__tests__/compliance.test.tsx` (new) | M |

---

## Appendix A: Current State — What's Already Compliant

| Item | Status | Notes |
|------|--------|-------|
| "Not investment advice" disclaimer exists | ⚠️ Partial | Exists but too small/hidden |
| SEBI non-registration disclosed | ⚠️ Partial | In footer only, 10px font |
| No guaranteed returns language | ✅ Compliant | No guarantees found anywhere |
| AI-generated disclosure | ✅ Compliant | Clearly states AI-generated |
| Stop-loss on every signal | ✅ Compliant | Both target and stop-loss generated |
| Signal reasoning provided | ✅ Compliant | AI reasoning for every signal |
| Technical data transparency | ✅ Compliant | RSI, MACD, Bollinger, SMA values shown |
| Frontend authentication | ✅ Partial | NextAuth.js with Google + credentials |
| Decimal for all prices | ✅ Compliant | Never using float for financial data |
| "Past performance" disclaimer | ⚠️ Partial | On How It Works page, not on track record/history pages |

---

## Appendix B: Regulation Quick Reference

| Regulation | Full Name | Key Sections | Relevance |
|-----------|-----------|-------------|-----------|
| SEBI RA 2014 | SEBI (Research Analysts) Regulations, 2014 | Reg 2, 3, 12, 16-18, 24-25 | Stock signal compliance |
| SEBI IA 2013 | SEBI (Investment Advisers) Regulations, 2013 | Reg 2, 3, 15 | AI Q&A feature |
| SEBI PFUTP 2003 | SEBI (Prohibition of Fraudulent and Unfair Trade Practices) Regulations, 2003 | Reg 4 | Signal accuracy claims |
| DPDPA 2023 | Digital Personal Data Protection Act, 2023 | §4-12, §33 | All personal data processing |
| IT Act 2000 | Information Technology Act, 2000 | §43A, §79 | Data security, intermediary liability |
| IT Rules 2011 | IT (Reasonable Security Practices) Rules, 2011 | Rule 3-4 | Privacy policy, SPDI |
| FEMA 1999 | Foreign Exchange Management Act, 1999 | §3-4, §13 | Forex signal delivery |
| SEBI Act 1992 | Securities and Exchange Board of India Act, 1992 | §12, §24 | Penalties for non-registration |
| GDPR | General Data Protection Regulation (EU) | Art. 3, 6, 13-17, 44-49 | EU user data processing |
| MiCA | Markets in Crypto-Assets Regulation (EU) | Title V | Crypto advisory (future) |
| FSMA 2000 | Financial Services and Markets Act, 2000 (UK) | §21, §25 | UK financial promotions |

---

## Appendix C: Estimated Legal Costs

| Item | Estimated Cost | Priority |
|------|---------------|----------|
| Privacy Policy drafting (Indian law firm) | ₹15,000 – ₹50,000 | Sprint 1 |
| Terms of Service drafting | ₹15,000 – ₹50,000 | Sprint 1 |
| SEBI RA registration consultation | ₹25,000 – ₹75,000 | Month 2 |
| SEBI RA registration fee | ₹1,00,000 (individual) | If proceeding |
| NISM Series XV exam fee | ₹1,500 | If proceeding |
| GST registration | Free (government portal) | Before payments |
| GDPR compliance consultation | ₹50,000 – ₹2,00,000 | If serving EU |
| Annual compliance audit | ₹50,000 – ₹1,50,000/year | If RA registered |

**Total estimated compliance budget**: ₹1,00,000 – ₹3,00,000 for initial setup (excluding RA registration).

---

## Appendix D: Decision Log

| Decision Needed | Options | Recommended | Deadline |
|----------------|---------|-------------|----------|
| SEBI RA registration | Register / Remove stock signals / Reframe language | Reframe NOW + pursue registration in parallel | Before commercial launch |
| Forex cross-pairs | Keep with disclaimer / Remove for Indian users | Keep with prominent FEMA disclaimer | Sprint 3 |
| US access | Allow / Block | Block (geo-restriction) | Sprint 3 |
| EU access | Allow with GDPR / Block | Block until GDPR-compliant | Sprint 3 |
| UK access | Allow / Block | Block | Sprint 3 |
| Pro tier pricing | ₹749 with GST / ₹749 inclusive / Revise | ₹749 inclusive of 18% GST (actual: ₹635 + ₹114 GST) | Sprint 4 |
| AI Q&A scope | Allow personalized advice / Restrict to educational | Restrict to educational, add prompt guardrails | Sprint 2 |
| Signal terminology | Keep BUY/SELL / Reframe to Bullish/Bearish | Reframe | Sprint 2 |

---

*This document is for internal planning purposes and does not constitute legal advice. All findings should be reviewed by a qualified legal professional before implementation. Regulatory requirements may change; verify current regulations before acting.*

*Generated: 24 March 2026 | SignalFlow AI v1.0.0*
