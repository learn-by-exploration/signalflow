# Neural Trader — News-Driven Signal Intelligence

> **Product Review Spec**  
> **Date**: 24 March 2026  
> **Author**: PM Review Agent (Senior PM perspective — retail trading tools, Indian market)  
> **Status**: Draft — Awaiting decision  
> **Scope**: News Dashboard, Event Chains, News-to-Signal Traceability

---

## Executive Summary

The proposal is to transform SignalFlow from a *signal-with-explanation* platform into a *news-first signal platform* where:
- News is a first-class entity (not hidden behind sentiment scores)
- Causal event chains are mapped and visualized
- Every signal traces back to specific news events
- The user learns *how* events drive markets

**My overall take**: The vision is compelling but dangerously large for a single-user personal tool. The gap between "show news that fed into signals" (achievable) and "Bloomberg Terminal + Kensho event analytics" (multi-year, multi-team) is enormous. This review argues for a **ruthlessly scoped V1** that delivers 80% of the value at 20% of the effort — and defers the causal graph / mind-map visualization to V2+.

### The Core Insight Worth Building

The user doesn't need a Bloomberg Terminal. She needs to answer one question every time she sees a signal:

> **"What happened in the world that made the AI think this?"**

That's it. If we answer that question well — with links to actual headlines, timestamps, and a 2-sentence "connect the dots" explanation — we've delivered the feature. Everything else (causal graphs, event chains, mind maps) is frosting.

---

## 1. User Stories

### Primary Stories (V1 — Must Ship)

**US-1: See why a signal was generated, grounded in specific news**
> As Priya (the user), when I see a STRONG_BUY signal for HDFCBANK on my phone (Telegram), I want to see the 2-3 specific news headlines that contributed to this signal, so I can judge whether the AI's reasoning makes sense before I act.

**Acceptance**: Every signal (Telegram + Dashboard) shows the headlines that fed into its sentiment score. Not just "credit growth accelerating" — but "Economic Times: HDFC Bank Q3 net profit rises 33% — 6 hours ago."

**US-2: Browse recent market news on the dashboard**
> As Priya, when I open the dashboard on my laptop in the morning, I want to see a feed of recent market news categorized by my tracked markets (stocks, crypto, forex), so I can quickly understand what happened overnight.

**Acceptance**: A "News" section on the dashboard or a dedicated `/news` page showing the last 24 hours of headlines, grouped by market, with sentiment tags (bullish/bearish/neutral) and timestamps.

**US-3: Tap a headline to see which signals it influenced**
> As Priya, when I see a headline like "RBI holds repo rate at 6.5%," I want to tap it and see which of my tracked symbols were affected and what signals were generated, so I can connect macro events to specific trading opportunities.

**Acceptance**: Each news headline links to a list of signals it influenced (could be zero). Each signal card in the dashboard shows a "News" section with the relevant headlines.

**US-4: Filter news by market and impact level**
> As Priya, on the news page on my laptop, I want to filter by market (stocks/crypto/forex) and by impact (high/medium/low), so I don't drown in irrelevant crypto news when I'm focused on NSE.

**Acceptance**: Filters at the top of the news page. Pre-filtered views: "Stock News," "Crypto News," "Forex News." Impact badges on each headline.

**US-5: See news context in the signal detail page**
> As Priya, when I drill into a signal on `/signal/[id]`, I want a "News Context" section showing the specific articles that were part of the AI's sentiment analysis, with timestamps and source names, so I can trace the reasoning.

**Acceptance**: Signal detail page has a new expandable section "📰 News that influenced this signal" showing 3-5 headlines with source, time, and sentiment contribution.

### Secondary Stories (V1 — Should Have)

**US-6: Understand how a macro event ripples across markets**
> As Priya, when a major event happens (e.g., US Fed rate hold), I want to see a simple timeline showing which of my tracked symbols were affected and in what order, so I learn how one event cascades.

**Acceptance**: On the signal detail page or a dedicated event page, show a simple vertical timeline: "Event → Symbol A affected (signal generated) → Symbol B affected (signal generated)." Not a complex graph — just a time-ordered list.

**US-7: Get notified only about signal-generating events**
> As Priya, I don't want to be notified about every news headline. I only want Telegram alerts for news events that actually generated or significantly changed a signal.

**Acceptance**: Telegram signal alerts include a "Triggered by:" line with the key headline. No standalone news notifications in V1. News-only digest is optional in V2.

**US-8: See today's key events in my morning brief**
> As Priya, my morning Telegram brief should include 3-5 key news events from the last 12 hours that are likely to affect my tracked symbols today.

**Acceptance**: Morning brief adds a "📰 Key overnight headlines" section with 3-5 entries.

### V2+ Stories (Deferred)

**US-9: Visualize causal chains between events**
> As Priya, I want to see a visual map showing how Event A (RBI policy) led to Event B (banking stock rally) which influenced Event C (NIFTY50 movement), so I build mental models of market causality.

**Rationale for deferral**: Causal chain extraction from news is an AI research problem. Getting it wrong (showing false causal links) is worse than not showing it. Defer until we have enough signal history to validate causal models.

**US-10: Search historical news and their market impact**
> As Priya, I want to search past news events and see what signals they generated and whether those signals were accurate, so I can study patterns.

**Rationale for deferral**: Requires a news archive database (not just 24-hour cache). Build this after V1 proves the news-to-signal link is valuable.

---

## 2. MVP Definition

### The Ruthless Scoping Rule

**V1 ships only what can be built on top of existing infrastructure** — the news fetcher, the sentiment engine, and the signal pipeline. No new databases, no graph algorithms, no complex visualizations.

### V1: "News-Backed Signals" (4-6 weeks)

| Feature | Description | Effort |
|---------|-------------|--------|
| **Store fetched headlines** | Currently, news_fetcher.py fetches headlines but they're consumed and discarded by the sentiment engine. Store them in a new `news_articles` table with symbol, source, headline, fetched_at, sentiment_contribution. | Backend: 3 days |
| **News section on signal detail** | Add a "📰 News Context" expandable section to `/signal/[id]` showing the 3-5 headlines that fed into this signal's sentiment analysis. | Frontend: 2 days |
| **News feed page** | `/news` page showing last 24h of fetched headlines, grouped by market, with sentiment chips (bullish/bearish/neutral), source, and timestamp. Filterable by market. | Frontend: 3 days |
| **Signal → News backlinks** | Each signal stores IDs of the news articles used in its sentiment analysis. Signal API response includes `news_context: [{headline, source, time, sentiment}]`. | Backend: 2 days |
| **Telegram signal enhancement** | Signal alerts include "📰 Key news:" with 1-2 top headlines. | Backend: 1 day |
| **Morning brief enhancement** | Morning brief includes "Key overnight headlines" section. | Backend: 1 day |
| **News nav item** | Add "News" to the navbar between Dashboard and History. | Frontend: 0.5 day |

**Total V1 estimate: ~2-3 sprints (12-18 dev days)**

### V2: "Event Timelines" (defer to 2+ months post-V1)

| Feature | Description |
|---------|-------------|
| Event entity extraction | AI extracts named events from clusters of headlines ("RBI Q1 Policy Review") |
| Event → Signal timeline | Vertical timeline showing event → affected symbols → generated signals |
| Event impact scoring | Rate events by how many signals they influenced and what outcomes resulted |
| Event-based filtering | "Show me all signals driven by RBI events" |
| Daily news digest (Telegram) | Evening Telegram message: "Today's 5 biggest market-moving headlines" |

### V3: "Causal Intelligence" (defer to 6+ months post-V1)

| Feature | Description |
|---------|-------------|
| Causal chain extraction | AI identifies chains: "US CPI → Fed hawkish tone → USD/INR strengthens → IT stocks sell off" |
| Visual event graph | Interactive node-link diagram showing event cascades |
| Historical pattern matching | "Last time RBI raised rates, here's what happened to banking stocks" |
| Predictive event impact | "An FOMC meeting is scheduled tomorrow — historically, here's how your portfolio is affected" |

### What I'm Explicitly Killing from V1

| Cut Feature | Why |
|-------------|-----|
| Mind-map / flow-chart visualization | Too complex for V1. A simple list of headlines is more useful on mobile. |
| Causal chain extraction | AI hallucination risk is too high. False causal links erode trust. |
| Event entity (as a first-class object) | Premature abstraction. Headlines linked to signals is enough for V1. |
| News search / archive | Requires new infra, retention policy, storage. Not needed for personal use. |
| Real-time news streaming | RSS is polled hourly already. That's sufficient. |
| Event impact predictions | Needs 6+ months of signal outcome data to be credible. |

---

## 3. UX/UI Design

### 3.1 News Feed Page (`/news`)

**Desktop Layout (≥1024px)**:

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: [Dashboard] [News ●] [History] [Portfolio] ...     │
├───────────────┬─────────────────────────────────────────────┤
│               │                                             │
│  FILTERS      │  NEWS FEED                                  │
│  ──────────   │  ──────────                                 │
│               │                                             │
│  Market:      │  ┌─── TODAY ────────────────────────────┐   │
│  [All]        │  │                                      │   │
│  ○ Stocks     │  │  🟢 HDFC Bank Q3 profit surges 33%  │   │
│  ○ Crypto     │  │  Economic Times • 2h ago • Bullish   │   │
│  ○ Forex      │  │  → Influenced: HDFCBANK STRONG_BUY   │   │
│               │  │                                      │   │
│  Impact:      │  │  🔴 US CPI comes in hot at 3.5%     │   │
│  [All]        │  │  Reuters • 6h ago • Bearish           │   │
│  ○ High       │  │  → Influenced: EUR/USD SELL          │   │
│  ○ Medium     │  │                                      │   │
│  ○ Low        │  │  🟡 Bitcoin ETF sees $200M outflow   │   │
│               │  │  CoinTelegraph • 8h ago • Neutral     │   │
│  Source:      │  │  → No signals generated              │   │
│  [All sources]│  │                                      │   │
│               │  ├─── YESTERDAY ────────────────────────┤   │
│               │  │  ...                                 │   │
│               │  └──────────────────────────────────────┘   │
│               │                                             │
└───────────────┴─────────────────────────────────────────────┘
```

**Mobile Layout (<768px)**:

```
┌──────────────────────────────┐
│  ☰  News            🔔 (3)  │
├──────────────────────────────┤
│  [All] [Stocks] [Crypto] [Fx]│  ← Horizontal pill filters
├──────────────────────────────┤
│                              │
│  🟢 HDFC Bank Q3 profit     │
│  surges 33%                  │
│  Economic Times • 2h ago     │
│  [Bullish]  → 1 signal       │  ← Tappable → goes to signal
│  ────────────────────────    │
│  🔴 US CPI comes in hot     │
│  at 3.5%                     │
│  Reuters • 6h ago            │
│  [Bearish]  → 1 signal       │
│  ────────────────────────    │
│  🟡 Bitcoin ETF sees         │
│  $200M outflow               │
│  CoinTelegraph • 8h ago      │
│  [Neutral]  No signals       │
│                              │
└──────────────────────────────┘
```

**Design Decisions**:
- **No infinite scroll**. Show last 24h by default, "Load more" button for yesterday. News is ephemeral; old headlines lose value fast.
- **Sentiment chip** on each headline: green "Bullish," red "Bearish," amber "Neutral" — using existing signal color tokens (`--signal-buy`, `--signal-sell`, `--signal-hold`).
- **"→ Influenced: SYMBOL SIGNAL_TYPE"** link under headlines that triggered signals. Tapping goes to signal detail. If no signal was generated, show "No signals generated" in muted text.
- **Group by time** (Today / Yesterday), not by market. Market filtering via pills or sidebar.

### 3.2 Signal Detail Page — News Context Section

Add a new section between the existing "AI Reasoning" panel and the "Technical Indicators" section:

```
┌─────────────────────────────────────────────────┐
│  📰 News Context                         [▼]    │
│  ─────────────────────────────────────────────   │
│                                                  │
│  These headlines were analyzed when generating   │
│  this signal's sentiment score (62/100 Bullish): │
│                                                  │
│  • "HDFC Bank Q3 net profit rises 33%, beats    │
│    estimates" — Economic Times, 2h ago           │
│  • "Banking sector rally continues as NIM       │
│    expansion confirmed" — MoneyControl, 5h ago   │
│  • "RBI holds rates steady, positive for        │
│    credit growth" — LiveMint, 1d ago             │
│                                                  │
│  💡 Learning note: This signal's confidence was  │
│  boosted from 72% (technical only) to 85%       │
│  (with sentiment) because news was strongly      │
│  positive. Technical analysis alone would have   │
│  generated a BUY, not STRONG_BUY.               │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Design Decisions**:
- **Collapsed by default** on mobile, expanded on desktop. The AI reasoning already handles the "why" — news context is for users who want to dig deeper.
- **Learning note** at the bottom explains how sentiment boosted or reduced the signal confidence. This is the teaching moment.
- **Max 5 headlines** shown. Don't overwhelm.

### 3.3 Telegram Signal Card Enhancement

Current format already includes AI reasoning. Add a news line:

```
🟢 STRONG BUY — HDFCBANK

💰 Price: ₹1,678.90 (+1.42%)
📊 Confidence: ████████░░ 92%

🎯 Target: ₹1,780  |  🛑 Stop: ₹1,630
⏱ Timeframe: 2-4 weeks

📰 Key news:
• HDFC Bank Q3 profit surges 33% (ET, 2h ago)
• RBI holds rates, positive for credit growth

🤖 AI: Credit growth accelerating. NIM expansion
confirmed. Bank posted strongest Q3 in 5 years.
Strong technical momentum with RSI at 62.

RSI: 62.7 | MACD: Strong Bullish | Vol: High
```

**Rules**:
- Show max 2 headlines in Telegram (space is premium on mobile).
- Headlines are truncated to 50 characters + source abbreviation.
- Only show the "📰 Key news:" section if articles actually exist. Don't show an empty section.

### 3.4 Navigation Flow

```
Dashboard ─────→ Signal Card ──→ Signal Detail ──→ News Context (expandable)
    │                                                     │
    │                                                     ↓
    └──→ News Page ──→ Headline ──→ Linked Signal ──→ Signal Detail
```

The user should be able to go **both ways**: from signal → news, and from news → signal. This bidirectional link is the core UX.

### 3.5 Event Timeline (V2 only — wireframe for discussion)

In V2, if we build event entity extraction, a simple vertical timeline inside the signal detail page:

```
  ● RBI Policy: Rates held at 6.5%        ← macro event
  │  1 day ago
  │
  ├── HDFCBANK sentiment: Bullish (+15)    ← sentiment impact
  │   STRONG_BUY signal generated (85%)
  │
  ├── ICICIBANK sentiment: Bullish (+12)
  │   BUY signal generated (71%)
  │
  └── NIFTY50 overall: Bullish
      3 banking signals fired
```

**Not a mind map. Not a flow chart. A simple vertical timeline.** Mind maps look impressive in decks but are terrible on mobile screens. A timeline is readable at any width.

---

## 4. Information Architecture

### Where Does "News" Live?

**Recommendation: New top-level nav item, positioned second.**

```
[Dashboard]  [News]  [History]  [Portfolio]  [Alerts]  [Calendar]
```

**Why top-level**:
- News is a *primary input* to the system, not a sub-feature. Users who understand what news drives signals will trust those signals more.
- The user checks news proactively ("what happened?") — it's not just reactive context.
- It replaces/complements the existing morning brief page, which is currently a dead-end.

**Why second (after Dashboard)**:
- The workflow is: Open dashboard → check signals → want context → go to news. Placing News next to Dashboard supports this flow.
- On mobile, it should be in the bottom nav if you add one.

### Hierarchy

```
News (page)
  └── Headline (list item)
        ├── Sentiment: Bullish/Bearish/Neutral
        ├── Source + Timestamp
        ├── Market: Stock/Crypto/Forex
        └── Linked Signals (0-N)
              └── → Signal Detail Page (existing)
                    └── News Context (new section)
                          └── Back-link to News Page headlines
```

This is a **flat hierarchy**, not a deep one. There's no "Event" entity in V1, no "Chain" entity, no nesting beyond headline → signal.

### Integration with Existing Pages

| Existing Page | News Integration |
|---------------|-----------------|
| **Dashboard** | Add a "📰 Latest" compact card showing 3 most impactful headlines. Clicking → `/news`. |
| **Signal Detail** | Add "News Context" expandable section (see 3.2 above). |
| **History** | V2: Show which news events drove historical signals. For now, no change. |
| **Morning Brief** | Enhance with "Key overnight headlines" section (already planned). |
| **Calendar** | V2: Link economic events to news outcomes ("RBI decision was: rates held"). |

---

## 5. User Education

This is the most important section. The user is learning to trade. Every piece of news context should teach her something.

### 5.1 The "Learning Note" Pattern

Every signal's News Context section ends with a **💡 Learning note** that explains the relationship between news and the signal:

| Scenario | Learning Note |
|----------|---------------|
| News strongly boosted a technical signal | "💡 This signal's confidence was boosted from 65% (technical only) to 88% (with sentiment) because recent earnings news was strongly positive. Technical analysis alone would have generated a BUY, but the news upgrade pushed it to STRONG_BUY." |
| News contradicted technicals | "💡 Technical indicators show oversold conditions (RSI: 28), but negative news about regulatory action kept sentiment bearish. The signal remained HOLD despite technical BUY conditions because news sentiment pulled confidence down." |
| No significant news found | "💡 This signal was generated purely from technical analysis. No significant news was found for this symbol in the last 24 hours. When news is absent, the maximum confidence is capped at 60%." |
| News from a related sector | "💡 While no direct news about INFY was found, broader IT sector news (Accenture earnings beat) contributed to bullish sentiment for Indian IT stocks." |

### 5.2 Sentiment Score Breakdown

On the signal detail page, show how the 60/40 score was computed:

```
  Signal Confidence: 85%
  ├── Technical Score: 78% (weight: 60%) → contributes 46.8
  └── Sentiment Score: 95% (weight: 40%) → contributes 38.0
                                            ─────────
                                Total:      84.8 → 85%
```

This makes the "black box" transparent. She sees exactly how much news matters vs. chart patterns. Over time, she learns which is more reliable for which market.

### 5.3 "What Does This Mean?" Tooltips (V2)

In V2, headlines on the news page can have optional "What does this mean?" expandable tooltips:

- "RBI holds repo rate at 6.5%" → "The repo rate is the interest rate at which RBI lends to banks. Holding it steady means borrowing costs stay the same, which is generally positive for banking stocks and equities."
- "US CPI at 3.5%" → "CPI (Consumer Price Index) measures inflation. 3.5% is above the Fed's 2% target, which increases the chance of continued high interest rates — generally negative for risk assets (crypto, equities) and strengthens the dollar."

For V1, the AI reasoning on the signal already provides this educational context. V2 adds it to standalone headlines.

### 5.4 Weekly "Market Lesson"

Enhance the existing weekly digest (Sunday 6 PM IST) to include:

> "📚 This week's biggest lesson: The US jobs report on Friday caused a chain reaction — strong employment data → higher rate expectations → USD strengthened → INR weakened → IT stocks rallied on rupee depreciation. This is a classic 'bad news is good news for exporters' pattern."

This is where event chains come alive — not through a visual graph, but through narrative. The AI is good at writing these narratives; complex visualizations add less value than a well-crafted paragraph.

---

## 6. Notification Strategy

### V1: Conservative — Only Signal-Linked News

| Event | Notification | Channel |
|-------|--------------|---------|
| New signal generated | Include "📰 Key news:" in existing signal alert | Telegram |
| Morning brief | Add "📰 Key overnight headlines" section (3-5 items) | Telegram |
| Evening wrap | Add "📰 Today's market-moving headlines" section | Telegram |
| New headline fetched but no signal | **No notification** | — |
| High-impact headline fetched | **No notification** (V1) | — |

**Rationale**: The user is a beginner. Every additional notification is cognitive load. Her phone already buzzes for signal alerts. Adding standalone news notifications turns SignalFlow into a news ticker — which she can get from any app. Our value is *curated, signal-linked* news, not a firehose.

### V2: Optional News Digest

Add an opt-in "📰 Daily News Digest" Telegram command:
- `/newsdigest on` — Receive a 6 PM IST daily summary of the 5 most impactful headlines
- `/newsdigest off` — Turn off

This is opt-in only. Never default to more notifications.

### V3: Smart Alerts

Alert only for "threshold-crossing" events:
- RBI rate change (not "rates held")
- Major earnings surprises (beat/miss by >10%)
- Crash/rally (>5% intraday move in tracked symbol)

These require event classification infrastructure from V3.

---

## 7. Indian Market Specifics

### News Categories that Matter for NSE/BSE

| Category | Why It Matters | Frequency | Impact Level |
|----------|---------------|-----------|-------------|
| **RBI Monetary Policy** | Repo rate, CRR, SLR decisions directly affect banking stocks (largest NIFTY weight) | ~6x/year | Extreme |
| **Quarterly Earnings** | India has 4 earnings seasons. Each of the 15 tracked NSE stocks reports. Result day ±2 days see highest volatility. | ~60 events/year across tracked stocks | High |
| **FII/DII Flows** | Foreign Institutional Investor flows are the single biggest driver of NIFTY direction. Net FII selling = market down. | Daily data | High |
| **Government Policy** | Budget, PLI schemes, sector regulations (SEBI, TRAI) | Irregular | High |
| **Global Cues** | US Fed, US CPI, China PMI — Indian markets react to these the next morning | Monthly | Medium-High |
| **Crude Oil Prices** | India imports 85% of crude. Spike in oil = inflation fear = negative for markets | Real-time | Medium |
| **INR/USD Movement** | Affects IT stocks (positive when INR weakens) and oil companies (negative when INR weakens) | Real-time | Medium |
| **Sector-Specific** | Auto sales (monthly), pharma approvals, IT deal wins | Irregular | Medium |
| **Geopolitical** | India-Pakistan, India-China, Middle East events | Event-driven | Variable |

### India-Specific UI Elements

1. **Earnings Calendar Integration**: The existing `/calendar` page has static economic events. V2 should add actual earnings dates for the 15 tracked NSE stocks. In V1, mention "Earnings season" in morning briefs when relevant.

2. **FII/DII Ticker**: Add a small "FII: ₹-2,340 Cr | DII: ₹+1,800 Cr" ticker to the dashboard (data available from NSE daily). This is the single most-watched number by Indian traders.

3. **Market Hours Context**: News fetched during NSE closed hours (3:30 PM to 9:15 AM) should be tagged "Pre-market" or "After-hours" so the user knows these will affect the *next* session.

4. **Hindi Source Support (V3)**: Some important Indian market news breaks first in Hindi (LiveHindustan Business, Dainik Jagran Business). V3 could add Hindi headline translation.

### Indian Market News Source Priority

| Source | Reliability | Latency | Free RSS? |
|--------|------------|---------|-----------|
| **Economic Times** | High | Fast | ✅ Already integrated |
| **MoneyControl** | High | Fast | ✅ Already integrated |
| **LiveMint** | High | Medium | ✅ (need to add) |
| **NDTV Profit** | Medium | Medium | ✅ (need to add) |
| **NSE Announcements** | Highest (official) | Slow | API available |
| **BSE Announcements** | Highest (official) | Slow | API available |
| **Reuters India** | Highest | Fast | Paid |

**V1 recommendation**: Keep existing sources (ET, MC, Google News RSS). Add LiveMint RSS. That gives sufficient Indian stock coverage without new API integrations.

---

## 8. Metrics & Success

### Primary Metrics (Track from Day 1)

| Metric | What It Measures | Target (3 months) |
|--------|-----------------|-------------------|
| **News Context click-through** | % of signal detail page views where the user expands "📰 News Context" | >40% |
| **News page visits/day** | Does the user actually use the news page? | >1 visit/day on active trading days |
| **Time on signal detail** | Does news context increase engagement with signals? | +30% increase vs. baseline |
| **Signal action rate** | Does the user act on signals more often when news context is shown? | Track via portfolio trades linked to signals |
| **Morning brief open rate** | Does the enhanced morning brief get read? | Track Telegram message delivery + link clicks |

### Secondary Metrics (Track after 1 month)

| Metric | What It Measures |
|--------|-----------------|
| **News → Signal navigation** | How often users go from News page to a linked signal |
| **Signal → News navigation** | How often users expand News Context on signal detail |
| **Filter usage on News page** | Which market filters are used most often |
| **Learning note engagement** | Do users scroll to / read the learning notes? |

### North Star Metric

**Signal Trust Index**: After seeing news context, does the user trust signals more? Measured by:
1. Higher % of signals that lead to portfolio trades
2. User feedback (Telegram: `/feedback` command after signals)
3. Reduced "Ask AI" questions about signal reasoning (they already got the answer from news context)

### How We Know It's Failing

| Signal | Meaning | Action |
|--------|---------|--------|
| <10% click-through on News Context | User doesn't care about the headlines | Simplify: show only top 1 headline inline, ditch the expandable section |
| 0 visits to /news page after 2 weeks | News-as-a-page doesn't work for this user | Kill the page. Embed news inline in signal cards only. |
| "Information overload" feedback | Too much news | Reduce to 1 headline per signal, remove news page, keep only morning brief |

---

## 9. Risks & Mitigation

### Risk 1: Information Overload (Severity: HIGH)

**The problem**: Adding a whole news dimension to a platform designed for one beginner trader. She's already processing: signal type + confidence + target + stop-loss + AI reasoning + technical indicators. Now we're adding news headlines?

**Mitigation**:
- V1 news context is **collapsed by default** on signal detail.
- Telegram shows **max 2 headlines**, not 5.
- News page exists but is not the default landing page (Dashboard remains home).
- Learning notes are brief (1-2 sentences).
- If the user never opens the news page, it doesn't affect her core experience.

**Escape hatch**: If metrics show <10% engagement, fold the entire feature into just enhancing the existing AI reasoning text with 1 specific headline reference. No new pages, no new sections.

### Risk 2: Stale or Irrelevant Headlines (Severity: HIGH)

**The problem**: RSS fetching gets garbage headlines. "HDFC Bank Recruitment 2026: Apply for 10,000 posts" is not relevant to trading. Showing irrelevant headlines next to signals destroys trust.

**Mitigation**:
- The Claude sentiment analysis already filters for relevance (it ignores non-market headlines when scoring).
- Only show headlines that were actually used by the sentiment engine (not all fetched headlines).
- Add a relevance score from Claude's analysis (already returns `confidence_in_analysis`). Only show headlines from analyses where Claude's own confidence was >60%.
- Add a "relevance" field to the sentiment prompt asking Claude to rate each headline's market relevance.

### Risk 3: False Causal Narratives (Severity: CRITICAL — V2/V3 concern)

**The problem**: Showing "Event A caused B" when the causation is correlation. Markets are complex; most retail traders already suffer from narrative bias ("the market fell because of X" when X is a post-hoc rationalization).

**Mitigation**:
- **V1 deliberately avoids causal claims.** We say "These headlines were analyzed when generating this signal" — not "This headline caused this signal."
- Language is "influenced" and "contributed to," never "caused" or "triggered."
- The learning note explains the score weighting transparently, so the user sees that technical analysis (60% weight) is always the primary driver.
- V2+ causal chains should include confidence levels and the caveat "This connection is AI-interpreted, not guaranteed."

### Risk 4: Claude API Budget Pressure (Severity: MEDIUM)

**The problem**: The existing $30/month budget barely covers 31 symbols × hourly sentiment. Adding news-to-signal attribution, learning notes, and event extraction requires more Claude calls.

**Mitigation for V1**:
- No additional Claude calls needed. V1 just stores and displays the headlines that the sentiment engine *already fetches and analyzes*. The news data is already flowing through the system — we're just making it visible.
- Learning notes can be template-based (no Claude call), with variable fill from existing score data.

**Mitigation for V2/V3**:
- Event extraction and causal chain analysis will need additional Claude calls. Budget needs to increase to $50-75/month.
- Batch event extraction: run once daily for all events (not per-symbol).
- Cache aggressively: event descriptions don't change.

### Risk 5: Regulatory Risk (Severity: LOW for V1, MEDIUM for V2+)

**The problem**: Showing news alongside specific buy/sell signals could be perceived as giving investment advice (SEBI RA registration concern from repo memory findings).

**Mitigation**:
- V1 shows news as *context*, not as *advice*. "These headlines were part of the analysis" is factual, not advisory.
- Maintain existing disclaimers on every signal.
- Frame news as educational: "Understanding what news drove this analysis" — not "This news means you should buy."
- The learning notes use educational language ("indicators suggest," "sentiment contributed to").

### Risk 6: RSS Source Reliability (Severity: MEDIUM)

**The problem**: Free RSS feeds can go down, change format, or get rate-limited. Google News RSS is particularly unreliable.

**Mitigation**:
- Existing `news_fetcher.py` already has fallback sources (Google → Bing → Financial RSS).
- Add LiveMint RSS as an additional source.
- Store fetched headlines with a `source` field, so if one source fails, we still have others.
- Track source availability metrics (how often each source returns 0 results).

---

## 10. Competitive Analysis

### The Landscape

| Tool | News Integration | Event Analysis | Signal-News Link | Indian Market | Price | Target User |
|------|-----------------|----------------|-------------------|---------------|-------|-------------|
| **Bloomberg Terminal** | Real-time, comprehensive | Kensho event analytics | Manual | Limited India | $24,000/yr | Institutional |
| **Refinitiv Eikon** | Real-time, Refinitiv News | Event-driven analytics | Semi-auto | Good India (IIFL integration) | $22,000/yr | Institutional |
| **Kensho (S&P)** | Event-focused | Causal chain analysis | Core feature | US-focused | Enterprise | Quants |
| **StockEdge** | Basic news feed | None | None | **Excellent** India | ₹999/yr | Indian retail |
| **MarketSmith India** | IBD-style news | None | None | Good India | ₹8,833/yr | Indian retail |
| **TradingView** | News sidebar (Pine) | None | None | Global | Free-$60/mo | Global retail |
| **Tickertape** | Basic news + screener | None | None | **Excellent** India | Free-₹249/mo | Indian retail |
| **Zerodha Pulse** | Curated news feed | None | None | Excellent India | Free (with Zerodha) | Indian retail |
| **SignalFlow V1 (proposed)** | Headlines linked to signals | None (V1) | **Core feature** | 15 NSE stocks | Free | 1 user |

### Where We Win

1. **Signal-to-news traceability**: No free retail tool links specific news headlines to specific trading signals with transparent sentiment scoring. StockEdge, Tickertape, and Zerodha Pulse show news feeds and stock screeners, but they don't say "these 3 headlines are why this stock is showing bullish signals."

2. **Educational framing**: Bloomberg and Kensho assume expert users. We explain *why* the news matters to this specific signal. The learning note is unique.

3. **Integrated signal + news in Telegram**: No Indian trading bot combines actionable signals with their news sources in a single message.

### Where We Lose (and that's OK)

1. **Breadth**: Bloomberg covers every asset class, every country. We cover 31 symbols. That's fine — depth > breadth for a personal tool.

2. **Real-time**: We poll RSS hourly. Bloomberg/Refinitiv have sub-second news. That's fine — she's not executing HFT strategies on 2-4 week timeframe signals.

3. **Event analytics sophistication**: Kensho's causal models are built by PhD teams. Our V2 event timeline is a manual approximation. That's fine — it's a personal learning tool, not a hedge fund.

4. **Source quality**: Our RSS sources are free and sometimes noisy. Paid tools have curated, verified news desks. Mitigation: Claude filters irrelevant headlines during sentiment analysis.

### The Real Competitor

The actual competitor isn't Bloomberg. It's **"checking MoneyControl, ET, and Twitter/X manually before acting on a signal."** That's what she does today without this feature. If V1 saves her that manual step by showing the relevant headlines *inside the signal itself*, we've won.

---

## Appendix A: Data Model Changes (V1)

### New Table: `news_articles`

```sql
CREATE TABLE news_articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(20) NOT NULL,
    market_type     VARCHAR(10) NOT NULL,
    headline        TEXT NOT NULL,
    source          VARCHAR(100),       -- "Economic Times", "Google News", etc.
    url             TEXT,               -- Original article URL (if available from RSS)
    sentiment_label VARCHAR(10),        -- "bullish", "bearish", "neutral"
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_symbol_time ON news_articles (symbol, fetched_at DESC);
CREATE INDEX idx_news_market_time ON news_articles (market_type, fetched_at DESC);
```

### New Join Table: `signal_news`

```sql
CREATE TABLE signal_news (
    signal_id       UUID REFERENCES signals(id) ON DELETE CASCADE,
    news_id         UUID REFERENCES news_articles(id) ON DELETE CASCADE,
    PRIMARY KEY (signal_id, news_id)
);
```

### Signal API Response Change

```json
{
  "data": {
    "id": "uuid",
    "symbol": "HDFCBANK",
    "signal_type": "STRONG_BUY",
    "confidence": 92,
    "ai_reasoning": "...",
    "news_context": [
      {
        "headline": "HDFC Bank Q3 net profit rises 33%, beats estimates",
        "source": "Economic Times",
        "fetched_at": "2026-03-24T08:30:00Z",
        "sentiment_label": "bullish"
      },
      {
        "headline": "RBI holds rates steady, positive for credit growth",
        "source": "LiveMint",
        "fetched_at": "2026-03-23T14:00:00Z",
        "sentiment_label": "bullish"
      }
    ],
    "sentiment_breakdown": {
      "technical_score": 78,
      "technical_weight": 0.6,
      "sentiment_score": 95,
      "sentiment_weight": 0.4,
      "final_confidence": 85
    }
  }
}
```

---

## Appendix B: Budget Impact Analysis

| Item | Current Cost | V1 Additional Cost |
|------|-------------|-------------------|
| Claude API (sentiment analysis) | ~$15-20/month | $0 (reuse existing calls) |
| News fetching (RSS) | $0 (free RSS) | $0 (same RSS feeds) |
| Database storage (news_articles) | Minimal | ~5,000 rows/month × 0.5KB = 2.5MB/month |
| Claude API (learning notes) | N/A | $0 (template-based in V1) |
| Additional RSS source (LiveMint) | $0 | $0 (free RSS) |
| **V1 Total Additional Cost** | — | **$0/month** |

V1 is budget-neutral. We're surfacing data the system already collects and discards.

V2 event extraction will add ~$10-15/month in Claude calls (daily batch of ~50 headlines → event classification).

---

## Appendix C: Implementation Dependencies

### Prerequisites (Must Be True Before V1 Starts)

1. ✅ `news_fetcher.py` exists and fetches headlines from Google News RSS, Bing News RSS, and financial RSS feeds.
2. ✅ `sentiment.py` sends headlines to Claude and receives sentiment scores.
3. ⚠️ **Headlines are currently discarded after sentiment analysis** — they are not stored. This is the core change V1 makes: store them.
4. ✅ Signal detail page exists at `/signal/[id]`.
5. ✅ Telegram formatter exists and can be extended.
6. ⚠️ **Sentiment engine often returns neutral (50/100)** due to no news found — this limits the value of "show the news that drove this signal" when there was no news. This is an existing limitation, not introduced by V1.

### Technical Risk: The "No News" Problem

From the repo memory: "Sentiment engine non-functional: No news data source → fallback sentiment 50/100."

If the news fetcher frequently returns zero headlines, V1 will show empty "📰 News Context" sections. This makes the feature look broken.

**Recommendation**: Before building V1, verify that the news fetcher reliably returns ≥3 headlines for the 15 NSE tracked symbols. If it doesn't, fix the news fetcher first. This is a precondition, not a V1 feature.

---

## Decision Required

| Question | Options |
|----------|---------|
| **Proceed with V1?** | Yes (news-backed signals) / No / Defer |
| **Build news page or inline only?** | Dedicated `/news` page / Inline in signal detail only / Both |
| **Include learning notes in V1?** | Yes (template-based) / Defer to V2 |
| **Fix news fetcher first?** | Yes (precondition) / No (build V1 and hope) |
| **Target timeline** | 2 sprints (~2 weeks) / 3 sprints (~3 weeks) |

**My recommendation**: Yes, proceed with V1. Build both the `/news` page and inline signal context. Include template-based learning notes. Fix the news fetcher reliability as Sprint 0 before V1 starts. Budget: 3 sprints (Sprint 0 = news fetcher fix, Sprint 1-2 = V1 features).

---

*Review complete. Ready for architect/implementer handoff.*
