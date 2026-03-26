# Event-Chain Reasoning for SignalFlow AI

## Senior Investment Banking Review & Feature Specification

**Author**: IB Research Desk Review (Goldman Sachs / Morgan Stanley perspective)  
**Date**: 24 March 2026  
**Status**: Draft — Brainstorm Phase  
**Reviewer Context**: 15+ years equity research, derivatives, algorithmic trading systems

---

## Executive Summary

SignalFlow's current architecture treats sentiment as a **scalar** — a single 0-100 score derived from headline text. This is the equivalent of reading a thermometer without understanding weather systems. Institutional desks don't trade on "sentiment is 73"; they trade on "the Fed held rates, which means USD stays strong, which pressures EM currencies, which means Indian IT exporters' INR-denominated revenues face headwinds, which means INFY's forward P/E multiple compresses." That's a **causal chain**, not a number.

The proposed event-chain enhancement would move SignalFlow from consumer-grade signal generation to something resembling a junior research analyst's thought process. This review assesses the idea critically, identifies what's actually worth building within the project's constraints ($30/month AI budget, personal use, 31 symbols), and flags the traps that look brilliant in design docs but fail in production.

**Bottom line**: The concept is sound. The execution must be ruthlessly scoped. Build the event store and causal links first, defer the graph visualization, and absolutely do not try to auto-discover chains — let Claude identify them within structured prompts.

---

## 1. Signal Quality Assessment

### Current System Gaps

The current pipeline has a fundamental information-destruction problem:

```
10 news headlines → Claude → single score (0-100) → blended with technicals → signal
```

Everything Claude "knew" about WHY the score was 73 gets collapsed into one integer. The `key_factors` array preserves some nuance (3 strings), but:

- **No temporal ordering** — "RBI policy announced" and "Q3 results beat estimates" are treated as equally recent events, even if one is 3 days old
- **No cross-symbol awareness** — HDFC Bank news and NIFTY sensitivity to banking sector news are analyzed independently
- **No magnitude differentiation** — "CEO resigned" and "minor management reshuffle" both show up as headlines
- **No event persistence** — once the 15-minute cache expires, the system re-fetches and re-analyzes from scratch. It has no memory of what it analyzed 2 hours ago
- **No chain reasoning** — the system can't express "USD strengthened → INR weakened → IT export revenues look better" because each symbol is analyzed in isolation

### How Event Chains Improve Signal Reliability

Institutional research desks maintain what's effectively a **running narrative** of market structure. Every morning, the desk pieces together overnight events into causal chains. When a new signal is generated, it's placed in the context of these chains. This provides three specific reliability improvements:

**1. Corroboration filtering** — A BUY signal on INFY means nothing if the system also shows a strengthening USD (bad for IT exporters). Currently, SignalFlow generates signals per-symbol with zero cross-reference. Event chains would surface contradictions: "BUY INFY based on strong technicals, BUT active chain shows USD/INR moving against export thesis."

**2. Catalyst identification** — The difference between a high-probability signal and noise is often whether there's a specific catalyst. "RSI is oversold" is a setup, not a trade. "RSI is oversold AND Q3 results release in 48 hours with whisper numbers above consensus" is a catalyst-driven trade with a specific timeframe. Event chains provide the catalyst layer.

**3. Risk event awareness** — The current system has no concept of "the Fed meets on Wednesday." It could generate a BUY on USD/INR on Tuesday evening with no awareness that a binary event is 12 hours away. Institutional desks *always* factor in the event calendar.

### Institutional Practices to Borrow

| Practice | What It Is | How to Adapt |
|----------|-----------|-------------|
| **Morning call narrative** | Desk head weaves overnight events into a thesis | Claude morning brief should reference active event chains, not just raw signals |
| **Sector rotation tracking** | When money flows from growth to value, all growth stocks are affected | Tag events by sector. If 3+ events point same direction for a sector, flag sector-level signal |
| **Event risk calendar** | Never open new positions before known binary events (FOMC, RBI, earnings) | Maintain a simple event calendar. Suppress signal generation 24h before major events unless specifically factoring them in |
| **Thesis tracking** | Each position has a written thesis. When the thesis breaks, you exit | Each signal should reference the chain that supports it. When chain events are contradicted, auto-flag the signal |
| **Correlation monitoring** | In a crisis, "everything correlates to 1" | When multiple chains converge on the same macro event, raise systemic risk flag |

### Quantifying the Improvement

Realistically, event-chain reasoning should improve signal quality in two measurable ways:

- **Reduced false signals**: I'd estimate 15-25% of current signals are generated against the macro grain (e.g., BUY signals during broad risk-off events). Chains should catch most of these.
- **Better timing**: Catalyst-aware signals should have tighter timeframes and higher hit rates on the signals that do fire.

**Caveat**: Don't expect event chains to turn a 55% hit rate into 80%. Markets are efficient. The realistic target is getting from ~55% to ~62-65%, while dramatically reducing the worst signals (the ones that would have been obviously wrong to a human reading the news).

---

## 2. Event Chain Model

### Recommended Data Model

An event chain is a **directed graph** of `MarketEvent` nodes connected by `CausalLink` edges. Keep it simple — don't over-engineer the graph structure.

```
MarketEvent
├── id: UUID
├── title: str (≤200 chars)        -- "RBI holds repo rate at 6.5%"
├── description: str (≤500 chars)  -- longer context
├── event_type: enum               -- see below
├── source_category: enum          -- central_bank | earnings | regulatory | geopolitical | macro_data | market_action | sector
├── affected_symbols: str[]        -- ["HDFCBANK.NS", "SBIN.NS", "NIFTY"]
├── affected_sectors: str[]        -- ["banking", "financials"]
├── affected_markets: str[]        -- ["stock", "forex"]
├── geographic_scope: enum         -- india | us | global | emerging_markets
├── impact_magnitude: int (1-5)    -- 1=noise, 3=notable, 5=market-moving
├── sentiment_direction: enum      -- bullish | bearish | neutral | mixed
├── confidence: int (0-100)        -- how sure are we this event is real/correctly parsed
├── source_url: str                -- original news link
├── occurred_at: timestamptz       -- when the event actually happened
├── detected_at: timestamptz       -- when SignalFlow found it
├── expires_at: timestamptz        -- when this event stops being relevant
├── is_active: bool
├── raw_headlines: str[]           -- original headlines that triggered this event
├── created_at: timestamptz
```

```
CausalLink
├── id: UUID
├── source_event_id: UUID → MarketEvent
├── target_event_id: UUID → MarketEvent
├── relationship_type: enum  -- causes | amplifies | dampens | contradicts | precedes
├── propagation_delay: str   -- "minutes" | "hours" | "days" | "weeks"
├── impact_decay: float      -- 0.0-1.0, how much the effect diminishes
├── confidence: int (0-100)  -- how certain is this causal link
├── reasoning: str (≤200)    -- "USD strength pressures INR, benefiting export revenues"
├── created_at: timestamptz
```

```
EventChain (materialized/cached view)
├── id: UUID
├── title: str               -- "Fed Hold → USD Strength → INR Pressure → IT Exporters"
├── root_event_id: UUID
├── event_ids: UUID[]        -- ordered list of events in the chain
├── total_events: int
├── net_impact: dict         -- { "INFY.NS": +15, "TCS.NS": +12, "USD/INR": -8 }
├── active_until: timestamptz
├── created_at: timestamptz
```

### Event Type Taxonomy

Keep this tight. Don't create 50 event types — you'll never populate them consistently:

```
central_bank_decision     -- rate decisions, QE announcements, forward guidance
earnings_report           -- quarterly results, revenue surprises, guidance changes
regulatory_action         -- new regulations, sanctions, approvals (including ETF approvals)
geopolitical_event        -- conflicts, elections, trade policies, sanctions
macro_data_release        -- GDP, CPI, PMI, employment data
supply_chain_disruption   -- logistics, commodity shortages, natural disasters
sector_rotation           -- observable flow from one sector to another
technical_breakout        -- significant level breach (support/resistance on major index)
corporate_action          -- M&A, buybacks, splits, CEO changes
market_structure          -- exchange halts, circuit breakers, liquidity events
```

### How Investment Banks Model Cascading Effects

The key insight: **effects propagate at different speeds and decay at different rates**.

```
First Order (minutes-hours):
  Fed raises rates → Treasury yields jump → USD strengthens
  This is FAST and MECHANICAL. Almost 1:1.

Second Order (hours-days):
  USD strengthens → USD/INR moves → IT stocks re-price
  This takes time because it requires MARKET PARTICIPANTS to act.

Third Order (days-weeks):
  IT stock repricing → Sector weight in NIFTY shifts → Index rebalancing flows
  → Downstream effects on mutual fund NAVs → Retail sentiment shifts
  This is SLOW and UNCERTAIN.
```

**Critical metadata for each link in the chain:**

| Field | Why It Matters | Example |
|-------|---------------|---------|
| `impact_magnitude` (1-5) | Not all events are equal. Fed rate hike = 5. Minor official speech = 1 | Fed rate decision = 5, FOMC minutes (as expected) = 2 |
| `confidence` (0-100) | First-order links are ~90% confident. Third-order links are ~30-50% | "Fed hikes → USD up" = 95%. "USD up → INFY earnings beat" = 40% |
| `propagation_delay` | Determines when the effect reaches each symbol | "minutes" for FX, "days" for stock repricing |
| `impact_decay` (0-1) | How much signal is left after propagation | First-order: 0.9. Third-order: 0.3 |
| `geographic_scope` | Indian market events don't move BTC (usually) | Scope limits which chains cross asset classes |

### Chain Construction Process

**Do NOT attempt automatic chain construction with pattern matching or rule engines.** This inevitably produces garbage chains that look plausible but are causally wrong.

Instead:

1. **Claude identifies events** — When processing news for a symbol, Claude extracts discrete events (not just sentiment)
2. **Claude links events** — Given a new event + the last N active events, Claude identifies causal relationships
3. **Deterministic propagation** — Predefined sector/symbol mappings determine which symbols are affected (e.g., "banking sector" → HDFCBANK.NS, ICICIBANK.NS, SBIN.NS)
4. **Human-validated templates** — Common chains are pre-templated: "RBI rate decision" → known downstream effects. Claude fills in the specifics.

---

## 3. Risk Management Integration

### How Event Chains Should Inform Risk Parameters

Currently, targets are `price ± (ATR × multiplier)`. This is purely volatility-based and completely event-unaware. That's fine for normal markets. It's dangerous around events.

**Specific recommendations:**

**3.1 ATR Multiplier Adjustment Based on Active Events**

```
If symbol has active event chain with impact_magnitude ≥ 4:
  - Widen stop-loss by 1.5x (ATR × 1.5 instead of ATR × 1.0)
  - Widen target by 1.5x (ATR × 3.0 instead of ATR × 2.0)
  - Rationale: high-impact events cause outsized moves in both directions.
    Tight stops get hit on whipsaws.

If symbol has contradicting event chains:
  - Suppress signal generation entirely
  - Or if generated, cap confidence at 50 (force HOLD)
  - Rationale: conflicting macro narratives = uncertain directionality
```

**3.2 Correlated Event Risk (Systemic Risk Flag)**

When multiple event chains converge on the same root cause (e.g., "global risk-off"), the portfolio-level risk is much higher than individual signal risk suggests.

```
Example: March 2020
  - Chain A: "COVID cases spike → lockdowns → supply chain disruption → NIFTY drops"
  - Chain B: "COVID cases spike → travel ban → crude drops → OMCs drop"
  - Chain C: "COVID cases spike → risk-off → FIIs sell → INR weakens → all stocks drop"

  Three "independent" SELL signals on three stocks.
  But they're ALL driven by one root event.
  If you entered all three, your actual risk is 3x what each signal suggests.
```

**Implementation**: When the same `root_event_id` appears in chains affecting 3+ active signals, add a **"systemic risk" warning** to each signal and to the morning brief. Don't auto-adjust positions (that's auto-trading territory), but flag it prominently.

**3.3 Event Calendar Risk Suppression**

Before known binary events (FOMC, RBI meetings, major earnings), signal generation should either:
- **Option A**: Suppress new signals 24h before (conservative)  
- **Option B**: Generate signals with an explicit "event risk" flag and reduced confidence cap (balanced)

I recommend Option B — it's more informative. But the confidence cap is critical. No signal should be >60% confidence if a known binary event could invalidate it within 24h.

**3.4 Chain Invalidation → Signal Review**

When an event chain that supported an active signal is **contradicted** by a new event:
- Auto-resolve the signal as "thesis broken"
- Send Telegram alert: "⚠️ Signal thesis changed: [original chain summary] ← NEW: [contradicting event]"
- This is the closest thing to institutional "stop reviewing" — when the reason you entered a trade no longer holds, you re-evaluate.

---

## 4. Data Quality Assessment

### Current Sources: Honest Assessment

| Source | Current Use | Quality Rating | Verdict |
|--------|-----------|---------------|---------|
| Google News RSS | Primary headlines | **D+** — Heavily gamed by SEO, includes blog spam, clickbait, duplicates | Necessary but noisy |
| Bing News RSS | Fallback | **D** — Similar quality to Google, less coverage of Indian markets | Drop or keep as fallback only |
| Economic Times RSS | Indian stocks | **B** — Reliable for Indian market news, but headlines-only | Keep, decent for NSE signals |
| MoneyControl RSS | Indian stocks | **B** — Good coverage, but late compared to wires | Keep |
| CoinTelegraph RSS | Crypto | **C+** — Crypto-native but often hype-driven | Keep but weight lower |
| ForexLive RSS | Forex | **B+** — Actually decent for FX | Keep |

### What Institutional Desks Actually Use (and Realistic Alternatives)

**Tier 1 — Wire Services (Bloomberg, Reuters)**  
Institutional desks get events within seconds via Bloomberg Terminal ($24K/year) or Refinitiv Eikon ($22K/year). Obviously not viable for a personal project.

**Realistic alternative**: Use the free RSS/API tiers from Reuters and AP News. Not real-time, but 15-30 minute delay is acceptable for SignalFlow's 5-minute signal cycle.

**Tier 2 — Central Bank Direct Feeds**  
This is actually FREE and critically underused:
- **RBI**: https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx — RSS available
- **US Fed**: https://www.federalreserve.gov/feeds/ — official RSS feeds
- **ECB**: https://www.ecb.europa.eu/rss/press.html

These are THE most important event sources for forex and rate-sensitive stocks. The current system doesn't use them at all. This is the single biggest data quality win available.

**Tier 3 — Earnings Data**  
Currently missing entirely. For NSE stocks, earnings dates and actual results are available from:
- **BSE/NSE filings**: Corporate announcements are public and scrapeable
- **MoneyControl earnings calendar**: Structured data available

Knowing "RELIANCE reports Q4 results on April 15" is table-stakes information for any signal system.

**Tier 4 — Economic Calendar**  
Free economic calendars (Investing.com, ForexFactory) provide:
- GDP, CPI, PMI release dates
- FOMC meeting dates
- RBI monetary policy schedule
- Employment data releases

This data should be **ingested separately from news** — it's structured, predictable, and forms the backbone of the event calendar.

### What NOT to Add

- **Social media (Twitter/X, Reddit)**: Noise-to-signal ratio is abysmal. WallStreetBets-driven moves are real but unpredictable and not suitable for the user persona (learning trader, not meme trader).
- **Paid data vendors (Quandl, Bloomberg API)**: Overkill for 31 symbols. The marginal improvement doesn't justify the cost.
- **Earnings call transcripts**: Interesting in theory, but Claude API costs for processing full transcripts would blow through the $30/month budget in days. Stick to headlines + structured data (revenue beat/miss, guidance up/down).
- **Alternative data (satellite imagery, credit card data)**: This is institutional-level quant analysis. Completely out of scope.

### Recommended News Source Priority Stack

```
P0 (Must have for event chains):
  1. Central bank RSS feeds (RBI, Fed, ECB) — new addition
  2. Economic calendar structured data — new addition
  3. Existing financial RSS (ET, MC, ForexLive) — retain

P1 (Should have):
  4. Earnings calendar + results headlines — new addition
  5. Reuters/AP free RSS — new addition
  6. NSE/BSE corporate announcements — new addition

P2 (Nice to have):
  7. Google News RSS — retain, weight lower
  8. CoinTelegraph RSS — retain, weight lower
  9. Bing News RSS — deprioritize
```

---

## 5. Temporal Dynamics

### Propagation Speed Model

This is where most amateur systems get it spectacularly wrong. They treat all news as having instant, equal impact. Reality:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT PROPAGATION TIMELINE                    │
│                                                                  │
│  T+0        T+5min      T+1hr       T+1day      T+1week        │
│  │          │           │           │           │               │
│  ▼ TRIGGER  ▼ 1ST ORDER ▼ 2ND ORDER ▼ 3RD ORDER ▼ PRICED IN   │
│                                                                  │
│  Fed hikes  FX desks    EM equities Sector      Fully           │
│  25bp       reprice     reprice     rotation    reflected       │
│             USD/INR     IT stocks   Fund flows  in valuations   │
│             immediately adjust      rebalance                    │
│                                                                  │
│  Confidence: 95%       70%          45%          20%            │
│  Decay:      1.0       0.7          0.4          0.15           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Specific Time Horizons by Market Type

| Effect Order | Forex | Crypto | Indian Stocks |
|-------------|-------|--------|---------------|
| 1st (mechanical) | Seconds-minutes | Minutes | Minutes (during market hours) / next open (after hours) |
| 2nd (participant-driven) | Hours | Hours | Hours to 1 day |
| 3rd (structural) | Days | Days-weeks | Days to weeks |
| Fully priced in | 1-3 days | 1-7 days | 3-14 days (Indian markets are slower to price in global events) |

### How This Maps to SignalFlow's Architecture

**Current signal cycle: 5 minutes**. This means:

- **1st-order effects**: The system is too slow to trade these. By the time data is fetched → analyzed → signal generated, forex has already moved. **Don't try to chase first-order effects.** Accept this limitation.
- **2nd-order effects**: This is SignalFlow's sweet spot. "USD strengthened this morning → INR will be under pressure → IT stocks may benefit" is a 2nd-order thesis that plays out over hours. The 5-minute cycle can catch this.
- **3rd-order effects**: Well within the system's timeframe. "Sector rotation from banks to IT" plays out over weeks. Signals with "2-4 weeks" timeframe should primarily reference 3rd-order chains.

**Recommendation**: Tag each signal with which **order of effect** it's primarily based on, and match to appropriate timeframes:

```python
CHAIN_ORDER_TIMEFRAMES = {
    "second_order": {"stock": "1-3 days", "crypto": "12-48 hours", "forex": "4-24 hours"},
    "third_order": {"stock": "1-4 weeks", "crypto": "3-7 days", "forex": "1-5 days"},
}
```

### Event Expiration Rules

Events must expire. Old news is not news. But the decay rate differs:

| Event Type | Active Duration | Rationale |
|-----------|----------------|-----------|
| Central bank decision | 6 weeks (until next meeting) | Rate decisions are the regime until changed |
| Earnings report | 2 weeks (until priced in) | Market takes ~5 trading days to fully adjust |
| Geopolitical event | Varies, default 1 week | Unless ongoing (war, trade dispute) |
| Macro data release | 1 month (until next release) | GDP, CPI are quarterly/monthly anchors |
| Regulatory action | 4 weeks (until implementation clarity) | Market reprices as details emerge |
| Supply chain disruption | 2 weeks to 3 months | Depends on resolution timeline |

**Implementation**: Each `MarketEvent` gets `expires_at` set based on `event_type`. A nightly task garbage-collects expired events and their chains.

---

## 6. Specific Feature Recommendations

### P0 — Must Build (Core Event Infrastructure)

**P0.1: MarketEvent Storage**
- New `market_events` table (schema above)
- Event deduplication (same event from multiple RSS sources should merge, not duplicate)
- Simple admin view or CLI to inspect stored events
- Events extracted by Claude during sentiment analysis (modify the prompt to return structured events, not just a score)

**P0.2: Event-Aware Sentiment Prompt**
- Replace the current single-score prompt with an event-extracting prompt
- New prompt returns: `{ events: [{title, type, magnitude, direction, affected_symbols}], overall_sentiment: 0-100 }`
- This is the highest-ROI change: same API call, vastly more structured output
- Minimal cost increase (maybe +50 tokens per response)

**P0.3: CausalLink Storage**
- New `causal_links` table
- Claude identifies links when processing events (add to the prompt: "given these events, identify any causal relationships")
- Store chain relationships

**P0.4: Cross-Symbol Event Propagation**
- When an event affects sector X, propagate awareness to all symbols in that sector
- Predefined sector-to-symbol mapping (already have symbol lists in config.py, just need sector tags)
- Modify `generate_for_symbol()` to check active events for the symbol AND its sector before scoring

**P0.5: Event Calendar (Scheduled Events)**
- Simple table of known upcoming events: FOMC dates, RBI dates, earnings dates
- Populated manually or via calendar API
- Signal generator checks calendar before generating — adds "event risk" flag if binary event within 24h

### P1 — Should Build (Signal Enhancement)

**P1.1: Chain-Backed Signal Reasoning**
- Modify AI reasoning to reference specific event chains
- Instead of "Technical indicators and positive sentiment suggest bullish momentum"
- Show: "RBI's rate hold (Mar 20) → banking sector stability → HDFC's NIM protected. Combined with RSI oversold at 28, this creates a high-probability mean reversion setup."
- Front-end: display event chain as a visual trail below the AI reasoning

**P1.2: Contradicting Chain Detection**
- When a new event contradicts an active chain, flag it
- Telegram alert for affected active signals
- Dashboard shows "⚠️ 1 contradicting event" badge on affected signals
- This is the single most valuable risk feature

**P1.3: Event-Adjusted Risk Parameters**
- Modify `calculate_targets()` to accept active event chains
- Widen stops before high-impact events
- Cap confidence when contradicting chains exist
- Add `event_risk_adjustment` field to Signal model

**P1.4: Correlation/Systemic Risk Detection**
- When 3+ active signals share a root event, flag as correlated group
- Show correlation indicator on dashboard
- Include in morning brief: "Note: 4 of your 7 active signals are driven by the same USD strength theme. Effective exposure is concentrated."

### P2 — Nice to Have (Enhanced Data & UI)

**P2.1: Central Bank Feed Integration**
- Add RBI, Fed, ECB RSS parsers to `news_fetcher.py`
- These get `impact_magnitude: 5` automatically
- Priority processing: central bank events skip the regular queue

**P2.2: Earnings Calendar Integration**
- Scrape or API-fetch upcoming earnings dates for tracked NSE stocks
- Auto-create "scheduled event" in event calendar
- Post-earnings: auto-create event with beat/miss classification

**P2.3: Event Chain Visualization (Frontend)**
- Visual node-graph or timeline showing event relationships
- Click on a signal → see the chain that supports it
- This is impressive but complex. Defer until events/chains are proven useful in practice.

**P2.4: Chain Performance Tracking**
- Track which event chains led to accurate signals
- Over time, weight chains by historical accuracy
- "Chains starting with RBI decisions have led to signals with 72% hit rate"

**P2.5: Economic Calendar Widget**
- Dashboard component showing upcoming events
- Countdown to next major event
- "RBI meets in 3 days" → visual awareness for the user

---

## 7. Anti-Patterns to Avoid

### 7.1 "More Data = Better Signals" Fallacy

**The trap**: "Let's add Twitter, Reddit, Telegram groups, YouTube transcripts, podcast mentions..."

**Reality**: More noise doesn't produce more signal. The current RSS feeds already generate more headlines than Claude can meaningfully analyze within the $30/month budget. Adding more sources will either:
- Blow the budget (more Claude calls)
- Require aggressive deduplication/filtering (engineering complexity)
- Introduce sentiment manipulation vectors (social media is trivially gamed)

**Rule**: Add data sources only when they provide categorically different information (e.g., central bank feeds provide policy decisions, which RSS headlines cannot reliably parse). Don't add more sources of the same type.

### 7.2 Overfitting Event Chains to Historical Data

**The trap**: "In backtesting, our event chain model correctly predicted the March 2020 crash!"

**Reality**: Of course it did — you built it knowing the chain existed. This is extreme survivorship bias. In real-time, 30 potential chains form every day. 29 of them dissipate without effect. 1 of them leads to a real move. Your backtesting only tests the 1.

**Rule**: Never evaluate chain quality by backtesting alone. The only valid metric is **forward-looking hit rate** on live signals. Track this from day one.

### 7.3 Chain Hallucination

**The trap**: Claude generates plausible-sounding causal chains that have no real-world basis.

**Reality**: LLMs are extremely good at constructing narratives. "Panama Canal blockage → shipping delays → Maersk rises → supply chain costs → inflation → RBI tightens → banking stocks fall" sounds great. But the actual causal links may be tenuous (Maersk's impact on Indian inflation is negligible).

**Rule**: Every chain link must have a confidence score. Third-order links should ALWAYS have <50% confidence. The system should visually distinguish high-confidence links (solid lines) from speculative ones (dashed lines). Never present speculative chains as factual.

### 7.4 Latency Arbitrage Delusion

**The trap**: "Let's detect events faster and trade before the market prices them in!"

**Reality**: With RSS feeds (15-30 min delay), a 5-min signal cycle, and a retail execution context, SignalFlow will NEVER beat the market on first-order effects. HFT firms process events in microseconds. Even Bloomberg Terminal users process in seconds. Don't even try.

**Rule**: SignalFlow's edge is NOT speed. It's **synthesis** — connecting events across three different markets in a way that a single human monitoring 31 symbols cannot. Optimize for breadth and depth of reasoning, not latency.

### 7.5 Confidence Score Inflation

**The trap**: Event chains make signals look more "reasoned" and thus more confident. The system starts generating 85%+ confidence signals regularly.

**Reality**: If >20% of your signals are STRONG_BUY/STRONG_SELL, your scoring is broken. Markets are uncertain. Most of the time, the right answer is "maybe slight lean bullish." A system that's always highly confident is a system that's always wrong in hindsight.

**Rule**: After adding event chains, re-calibrate. The distribution should still be: ~10% STRONG signals, ~30% BUY/SELL, ~60% HOLD (which get filtered out). If the distribution shifts toward extremes, the chain impact weighting is too high.

### 7.6 Ignoring the "Priced In" Problem

**The trap**: "There's a positive event chain for INFY! Generate BUY signal!"

**Reality**: If the event happened 3 days ago and the stock already rallied 8%, the chain's effect is already priced in. Generating a BUY signal based on information the market has already acted on is the #1 mistake retail traders make.

**Rule**: Every event chain must include a "priced-in" check. Compare the chain's expected impact against the actual price move since the chain started. If actual move >= expected impact, the chain is exhausted. No new signals from exhausted chains.

### 7.7 The "God Prompt" Anti-Pattern

**The trap**: Cramming event extraction, chain linking, sentiment scoring, cross-symbol propagation, and risk assessment into a single Claude API call.

**Reality**: Prompt complexity degrades output quality non-linearly. A 2000-token prompt with 5 tasks produces worse results on each task than 5 separate 500-token prompts.

**Rule**: Keep Claude calls focused. One call to extract events. One call to identify chain links. One call for reasoning. This costs more tokens but produces dramatically better results.

---

## 8. Missing Pieces — What an IB Desk Would Never Ship Without

### 8.1 Position Sizing Guidance (CRITICAL)

The current system says "BUY HDFCBANK, target ₹1780, stop ₹1630." It never addresses **how much** to buy. Even basic guidance matters:

- "Risk 2% of capital per signal" is the universal rule
- Position size = (2% × capital) / (entry - stop_loss)
- The system already has all the data to compute this. Just needs portfolio capital input.

**Without position sizing, event chain improvements don't matter** — a user could put 50% of capital into one signal and get wiped on a stop hit.

### 8.2 Sector Exposure Tracking

If the system generates BUY signals on HDFC Bank, ICICI Bank, and SBI simultaneously, the user has 100% allocation to banking. One adverse banking event wipes all three positions.

**Required**: Track sector allocation across active signals. Warn when >40% of active signals are in one sector.

### 8.3 Drawdown Monitoring

No concept of "I've hit 3 stop-losses in a row, maybe I should reduce size." Institutional desks have mandatory drawdown limits:
- 5% drawdown → reduce position sizes by 50%
- 10% drawdown → halt new positions, review

This is simple to implement using the existing portfolio tracking.

### 8.4 Signal Expiry + Auto-Resolution (Partially Exists)

The resolution system exists but is simplistic. Missing:
- **Partial target hits** — Price reached 80% of target. Is that a win or not?
- **Time-based decay** — A 4-week signal that's flat after 2 weeks should lose confidence
- **Thesis invalidation** — The event chain that justified the signal is now dead

### 8.5 Market Regime Detection

The biggest missing piece after event chains. The system treats all market conditions identically:
- In a **trending market**, momentum signals (MACD, SMA cross) work great
- In a **ranging market**, mean-reversion signals (RSI, Bollinger) work great
- In a **volatile/crisis market**, almost nothing works — stay flat

**A single flag** — `current_regime: trending | ranging | volatile` — would let the system weight indicators differently. This doesn't require event chains; it can be computed from NIFTY/BTC price action directly (ADX indicator, realized volatility vs. VIX).

### 8.6 Slippage Awareness

Targets are calculated to 8 decimal places (`Decimal("0.00000001")`). But in reality:
- NSE stocks: execution at exact price is rare; expect 0.05-0.1% slippage
- Crypto: spread + slippage = 0.1-0.5% depending on exchange and volume
- Forex: tightest, but still 1-3 pips on majors

The target and stop-loss displayed to the user should factor in realistic execution costs. A 2% target with 0.5% slippage is really a 1.5% target.

### 8.7 Disclaimer System (Legal)

The CLAUDE.md mentions disclaimers but the current implementation is thin. With event chains providing specific causal narratives, the legal risk increases — the system could be perceived as providing specific investment advice.

**Every event chain display should include**: "This event analysis represents one possible interpretation. Markets may react differently than the causal chain suggests. This is not investment advice."

---

## 9. Budget Impact Analysis

All of this must work within the $30/month Claude API budget. Current usage breakdown (estimated):

```
Current budget allocation:
  Sentiment analysis: ~2000 calls/day × $0.004 ≈ $8/day → ❌ This seems too high
  Actually: 31 symbols × 1 call/hour × 24h ≈ 744 calls/day × ~500 tokens avg
  Monthly: ~22,000 calls × 800 tokens avg = 17.6M tokens
  At Sonnet pricing ($3/1M input, $15/1M output):
    Input: ~14M × $3/1M = $42 ← ALREADY OVER BUDGET if running full tilt
```

**This is a real problem.** The current system's hourly sentiment task across 31 symbols is already budget-constrained. Adding event extraction and chain linking will make it worse.

### Budget-Friendly Event Chain Strategy

1. **Don't add new Claude calls for event extraction** — restructure the existing sentiment prompt to return events AND sentiment in one call (P0.2). Net: zero new calls.

2. **Chain linking via prompt, not separate call** — Include "active events" context in the sentiment prompt. Claude links them in the same response. Net: +200 tokens per call (~10% increase).

3. **Reduce call frequency for stable symbols** — If a symbol has no new news, don't re-analyze every hour. Cache for 4 hours. This could cut calls by 40-60%. Net: significant savings.

4. **Priority-based analysis** — Analyze symbols with new events first. If budget is tight, skip symbols with no recent news. Net: smarter spending.

**Estimated budget after optimization:**
```
31 symbols × smarter frequency (avg 4 calls/day) × 30 days = ~3,700 calls/month
~1,200 tokens avg per call (expanded for events) = 4.4M tokens total
Input cost: ~3.5M × $3/1M = $10.50
Output cost: ~0.9M × $15/1M = $13.50
Total: ~$24/month ← within budget with room for chain reasoning calls
```

---

## 10. Implementation Sequencing

```
Phase 1: Event Foundation (P0.1, P0.2)
├── Add market_events + causal_links tables
├── Modify sentiment prompt to extract structured events
├── Store events alongside existing sentiment flow
├── No frontend changes
├── Tests: event extraction accuracy, deduplication
└── Duration estimate: significant backend work

Phase 2: Cross-Symbol Awareness (P0.4, P0.5)
├── Add sector-to-symbol mapping
├── Add event calendar table + seed with FOMC/RBI dates
├── Modify signal generator to check active events
├── Add "event risk" flag to signals
└── Tests: cross-symbol propagation, calendar suppression

Phase 3: Signal Enhancement (P1.1, P1.2, P1.3)
├── Chain-backed reasoning in AI output
├── Contradicting chain detection
├── Event-adjusted risk parameters
├── Frontend: event trail below AI reasoning
└── Tests: chain display, contradiction alerts

Phase 4: Data Quality (P2.1, P2.2)
├── Central bank RSS integration
├── Earnings calendar integration
├── Priority processing for high-impact sources
└── Tests: source ingestion, priority ordering

Phase 5: Advanced Features (P1.4, P2.3, P2.4)
├── Systemic risk detection
├── Chain visualization
├── Chain performance tracking
└── Tests: correlation detection, historical tracking
```

---

## Final Verdict

This enhancement is the right strategic direction. SignalFlow currently operates as a "sentiment thermometer" — it takes the market's temperature but doesn't understand the disease. Event chains add diagnostic capability.

**What to build**: P0 and P1 features. These are structurally sound and achievable within budget.

**What to defer**: Graph visualization (P2.3), alternative data sources, and anything that requires additional Claude API calls beyond the restructured prompt.

**What to never build**: Real-time event detection (wrong architecture for this), social media integration (noise), automatic chain discovery without Claude (will produce garbage).

**The highest-ROI single change**: Modify the sentiment prompt (P0.2) to return structured events instead of just a score. This costs nearly nothing extra and immediately unlocks event storage, chain building, and better reasoning. Start there.

**Risk**: The main risk is complexity creep. Event chains are conceptually elegant but operationally complex. Every chain needs storage, display, expiry, contradiction checking, and performance tracking. Scope aggressively. Ship Phase 1, measure impact on signal quality over 2-4 weeks, then decide on Phase 2.

---

*This review represents an institutional perspective applied to a personal project. The recommendations are calibrated for SignalFlow's constraints (31 symbols, $30/month AI budget, single user). Institutional implementations of similar systems cost $500K-$2M annually and employ dedicated teams. The goal here is to capture 60% of the value at 1% of the cost.*
