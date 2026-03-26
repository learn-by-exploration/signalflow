# News Intelligence Enhancement — Expert Review

> **Date**: 24 March 2026  
> **Author**: Brainstorm Agent (Senior Financial Journalist Persona)  
> **Status**: Draft — Awaiting architect review  
> **Scope**: Review of proposed news event tracking, causal chain mapping, and news dashboard  
> **Perspective**: 12+ years in Indian/global financial journalism (ET, CNBC TV18, Bloomberg)

---

## Executive Summary

SignalFlow's current news system is **headline-only, source-blind, and temporarily amnesiac**. It fetches RSS titles, throws them at Claude, gets a sentiment number, and forgets everything in 60 minutes. This is a perfectly fine MVP—but calling it "news intelligence" would be generous.

The proposed enhancement—event tracking, causal chains, news dashboard—is ambitious and *directionally correct*. But it has serious risks of over-engineering if the team isn't brutally realistic about how financial news actually works. This review provides that reality check.

**Bottom line**: Build the event layer. Be very cautious with causal chains. Skip auto-generated chain depths beyond 1 hop. Let Claude suggest connections, but never present them as facts.

---

## 1. News Taxonomy for Market-Moving Events

### Proposed Category System

A good taxonomy for a retail-oriented Indian trading platform needs **two dimensions**: event type and impact scope.

#### Dimension 1: Event Type (Primary Classification)

| Category | Sub-Categories | Examples | Typical Symbol Impact |
|----------|---------------|----------|----------------------|
| **Macro-Economic** | GDP, CPI/WPI, IIP, PMI, trade balance, employment data | India CPI at 5.1%, US Non-Farm Payrolls | Broad market (NIFTY), forex pairs |
| **Monetary Policy** | Rate decisions, liquidity operations, policy statements | RBI MPC holds repo at 6.5%, Fed dot plot | Banks, NBFCs, rate-sensitive sectors, forex |
| **Corporate Earnings** | Quarterly results, guidance updates, management commentary | TCS Q3 PAT up 12%, HDFC Bank NIM guidance | Direct stock, sector peers |
| **Corporate Actions** | Dividends, buybacks, splits, bonus, M&A, demergers | Reliance demerger, ITC hotel spin-off | Direct stock |
| **Regulatory** | SEBI orders, RBI circulars, govt policy changes, tax | SEBI tightens F&O rules, GST rate changes | Sector-wide or market-wide |
| **Geopolitical** | Wars, sanctions, trade wars, elections, diplomacy | India-China border, US-China tariffs, Middle East | Broad market, crude, defence stocks |
| **Sector-Specific** | Industry data, commodity prices, supply disruptions | Auto sales numbers, crude oil price spike, IT deal wins | Sector basket |
| **Institutional Flows** | FII/DII data, block deals, bulk deals, mutual fund flows | FIIs sell ₹5,000cr in cash market | Broad market direction |
| **Sentiment/Technical** | Index milestones, record highs/lows, VIX spikes | NIFTY crosses 25,000, India VIX above 20 | Market-wide sentiment |
| **Crypto-Native** | Protocol updates, hacks, regulatory, whale moves, ETF flows | BTC ETF inflows, Ethereum Dencun upgrade, exchange hack | Direct crypto pairs |

#### Dimension 2: Impact Scope

| Scope | Description | Example |
|-------|-------------|---------|
| **Single Symbol** | Affects one stock/token directly | Infosys buyback announcement |
| **Sector** | Affects a group of related stocks | RBI rate cut → all bank stocks |
| **Market-Wide** | Affects NIFTY/Sensex broadly | Union Budget, global risk-off |
| **Cross-Market** | Ripples across stocks + forex + possibly crypto | US CPI → USD → INR → IT stocks |
| **Global** | Affects all markets simultaneously | Fed emergency rate decision, pandemic |

#### Dimension 3: Urgency/Time Sensitivity

| Level | Window | Example |
|-------|--------|---------|
| **Flash** | Minutes | Earnings surprise, RBI surprise cut, exchange hack |
| **Session** | Hours | FII data released, PMI data, block deal |
| **Day** | Full day | Budget speech, policy document released |
| **Thematic** | Days-Weeks | Earnings season, monsoon progress, election campaign |
| **Structural** | Weeks-Months | Rate cycle shift, regulatory regime change |

### Recommendation for SignalFlow

Implement categories as **tags, not a rigid hierarchy**. An event like "RBI cuts repo rate by 25bps" would be tagged:

```
type: monetary_policy
scope: cross_market  
urgency: flash
affected_sectors: [banks, nbfc, real_estate, auto]
affected_symbols: [HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, KOTAKBANK.NS, ...]
affected_forex: [USD/INR]
```

Don't force every event into exactly one box. Financial events are inherently multi-dimensional.

---

## 2. Event vs. Article — The Deduplication Problem

### The Core Challenge

This is the hardest problem in the proposed system, and the one most likely to be underestimated.

**What an event is**: A discrete thing that happened in the real world at a specific time.  
**What an article is**: One journalist's framing of an event (or multiple events), published at a specific time.

### The Messy Reality

Consider "RBI keeps repo rate unchanged at 6.5%":

| Source | Headline | Angle |
|--------|----------|-------|
| Reuters | "RBI holds repo rate at 6.5% as expected" | Neutral, factual |
| ET | "RBI Governor Das flags inflation risks, holds rates" | Inflation hawk angle |
| Moneycontrol | "NIFTY Bank rallies as RBI signals rate cut in next meeting" | Bullish spin |
| LiveMint | "RBI MPC minutes reveal 4-2 split — dovish shift?" | Policy nuance |
| CNBCTV18 | "Markets cheer RBI status quo, HDFC Bank up 3%" | Market reaction |
| Random blog | "RBI confirms economy in trouble by not cutting" | Bearish clickbait |

These are **6 articles** about arguably **2-3 events**:
1. The rate decision itself  
2. The forward guidance / commentary  
3. The market reaction  

### How to Deduplicate: A Practical Approach

**Don't try to be perfect. Try to be useful.**

#### Event Metadata Schema

```
Event:
  id: uuid
  canonical_title: str          # e.g., "RBI MPC holds repo rate at 6.5%"
  event_type: str               # from taxonomy above
  occurred_at: datetime          # when the event actually happened (not article publish time)
  first_reported_at: datetime    # earliest article timestamp
  symbols_affected: list[str]
  sectors_affected: list[str]
  magnitude: enum[low, medium, high, extreme]
  is_scheduled: bool            # was this a calendar event?
  
  articles: list[Article]       # all articles covering this event
  article_count: int
  source_consensus: str         # do sources agree on the direction?
```

#### Deduplication Strategy (for Claude)

The most practical approach for SignalFlow's scale (31 symbols, ~300 articles/day max):

1. **Time-window clustering**: Articles about the same symbol within a 2-hour window are candidates for the same event
2. **Claude-assisted grouping**: Send Claude a batch of 10-15 headlines for a symbol and ask: "Which of these headlines refer to the same underlying event? Group them."
3. **Canonical title extraction**: For each group, Claude generates a single factual event title
4. **Don't over-cluster**: If in doubt, keep events separate. Two events wrongly merged is worse than one event represented twice.

#### What NOT To Do

- **Don't use TF-IDF or cosine similarity on headlines alone.** "HDFC Bank Q3 results beat estimates" and "HDFC Bank delivers strong Q3" are the same event, but "HDFC Bank Q3 provisions worry analysts" is a *different angle on the same event* — cosine similarity will fail here.
- **Don't build a separate NLP deduplication pipeline.** Claude is already in the loop. Use it.
- **Don't try real-time deduplication.** Batch it. Run dedup every 30-60 minutes. Real-time dedup across sources is a research problem, not a startup feature.

---

## 3. Causal Chain Reality Check

### The Hard Truth About Causal Chains

I've spent 12 years watching reporters (myself included) construct neat causal chains that are **post-hoc narratives, not predictive models**.

#### How Often Are Chains Clean?

**Almost never.** Here's why:

| Your Example Chain | What Actually Happens |
|---|---|
| "Panama Canal blockage → shipping costs surge → Indian pharma imports impacted → SUNPHARMA signal" | Real chain: Panama Canal issue → 47 other supply chain factors → shipping costs move (maybe) → pharma companies hedge or use alternative routes → impact shows up in Q2 earnings 3 months later → stock moves on earnings day. By the time RSS feeds report the canal blockage, pharma stocks have already moved (or not at all). |
| "US CPI data hot → Fed rate cut expectations shift → USD strengthens → USD/INR moves → IT stocks impacted" | This chain is almost instant. CPI data drops → all 4 subsequent effects happen within 15-45 minutes through algo trading. By the time your RSS feed picks up the CPI article, IT stocks have already repriced. |

#### Reliable Chain Depth

| Depth | Reliability | Example |
|-------|------------|---------|
| **0 hops** (direct) | High (70-90%) | "TCS Q3 profit up 15%" → TCS stock moves |
| **1 hop** (immediate sector) | Moderate (40-60%) | "TCS Q3 strong" → INFY/WIPRO/HCLTECH catch bid |
| **2 hops** (cross-market) | Low (20-35%) | "US CPI hot → USD strengthens → INR weakens" |
| **3+ hops** | Noise (<15%) | Anything with 3+ steps is a narrative, not a chain |

#### When "Chains" Are Really Just Narratives

> **Journalist confession**: We write "X happened BECAUSE of Y" dozens of times a week. At least half the time, we're pattern-matching, not demonstrating causation. The honest version of most market stories is "X happened, and also Y happened around the same time, and traders we spoke to said Y was the reason, but honestly the market goes up because there were more buyers than sellers today."

Financial journalists create causal narratives because:
1. Readers demand explanations ("why did the market fall?")
2. Random noise doesn't make a good story
3. The simplest narrative that fits today's price action wins
4. Tomorrow, if the market reverses, we'll construct a different narrative

### Recommendation for SignalFlow

1. **Build 1-hop connections ONLY.** Event → directly affected symbols. That's it.
2. **Let Claude SUGGEST multi-hop chains as "narrative context"** but label them explicitly: *"Possible connection (AI-suggested, not confirmed)"*
3. **Never present auto-generated causal chains as fact.** This will destroy trust.
4. **Track chain accuracy.** When you suggest "Event A impacts Symbol X," track whether X actually moved. Over time, you'll learn which chain types are predictive vs. noise.
5. **The most valuable "chain" for your user is the simplest one**: "This stock is moving. Here's why." Not a 4-hop supply chain diagram.

---

## 4. News Timeliness — The Latency Tax

### Current State: RSS Feeds Are Slow

Your current pipeline:

```
Real-world event → Reporter writes → Editor approves → Published → RSS feed updates → 
Your scraper fetches → Claude analyzes → Signal generated → User sees it

Total latency: 15 minutes (best case) to 90+ minutes (typical)
```

For comparison:

| Channel | Typical Latency from Event |
|---------|--------------------------|
| Bloomberg Terminal | 5-30 seconds |
| Reuters Eikon | 10-60 seconds |
| Twitter/X financial accounts | 30-120 seconds |
| CNBCTV18/ETNow live feed | 1-5 minutes |
| News agency wire (PTI, ANI) | 2-10 minutes |
| Google News RSS | 10-30 minutes |
| Moneycontrol article | 15-45 minutes |
| Economic Times article | 20-60 minutes |

### The "News Edge" Window

| Market | Edge Window | After This, Priced In |
|--------|-----------|----------------------|
| **Large-cap Indian stocks** | 1-5 minutes for earnings, macro data | Priced in within 10-15 minutes |
| **Mid/small-cap stocks** | 5-30 minutes (less algo coverage) | Can take 1-2 hours |
| **Crypto (BTC/ETH)** | 30 seconds to 2 minutes | Highly efficient, priced in fast |
| **Altcoins** | 5-15 minutes | Less efficient, more edge |
| **Forex majors (EUR/USD)** | Nearly instant for macro data | 1-5 minutes |
| **USD/INR** | 2-10 minutes for RBI actions | 15-30 minutes for full adjustment |

### What This Means for SignalFlow

**Your user will NEVER get a news edge from RSS feeds for intraday trading.** Full stop.

But that's okay, because your user is:
- A beginner-to-intermediate trader with an M.Com
- Making swing trades (2-4 week timeframe per CLAUDE.md)
- Not competing with HFT firms

For a swing trader, being 30-60 minutes late on news is **completely acceptable** as long as:
1. The signal captures the *direction* correctly
2. The entry point accounts for the initial price reaction
3. The system is honest about timing: "This event occurred 45 minutes ago; initial market reaction was +1.2%"

### How to Handle Timeliness

| Scenario | Recommended Handling |
|----------|---------------------|
| **News < 15 min old** | Flag as "Breaking" — signal is timely |
| **News 15-60 min old** | Flag as "Recent" — price may have partially adjusted |
| **News 1-4 hours old** | Flag as "Developing" — initial reaction complete, watch for follow-through |
| **News > 4 hours old** | Normal analysis — focus on trend/thesis, not reaction trade |
| **Rumor / unconfirmed** | Flag explicitly. Never generate a high-confidence signal on rumors |
| **Pre-market news** | Higher value — Indian stocks haven't reacted yet (if news breaks overnight) |
| **During-market news** | Alert quickly, but note the initial price reaction has happened |

### Key Insight: Pre-Market Is Your Best Use Case

The biggest value your user gets from news is **overnight/pre-market analysis**:
- US markets closed, India reacting to global cues at 9:15 AM
- Your morning brief at 8:00 AM IST is the ideal moment
- Crypto news that broke at 2:00 AM IST affecting morning crypto positions

Focus your best news intelligence on the morning brief window (7:00-9:15 AM IST).

---

## 5. Source Quality & Bias

### Indian Financial News Source Ratings

#### Tier 1 — Reliable, First-to-Report, Low Bias

| Source | Strengths | Weaknesses | Speed | Trading Relevance |
|--------|-----------|------------|-------|-------------------|
| **Reuters India** | Wire service accuracy, global context, regulatory coverage | Less India-specific color, paywalled | ★★★★★ | ★★★★☆ |
| **Bloomberg Quint (NDTV Profit)** | Deep analysis, institutional sources, M&A scoops | Some stories arrive late, ad-heavy website | ★★★★☆ | ★★★★★ |
| **BSE/NSE Official** | Primary source for corporate filings, board outcomes | Not "news" per se—raw data | ★★★★★ | ★★★★★ |
| **PTI (economic wires)** | Fast, factual, no editorial spin | Terse, lacks analysis | ★★★★★ | ★★★☆☆ |

#### Tier 2 — Good Coverage, Some Bias

| Source | Strengths | Weaknesses | Speed | Trading Relevance |
|--------|-----------|------------|-------|-------------------|
| **Economic Times** | Broadest India market coverage, decent RSS feeds | Clickbait headlines on web, morning paper bias | ★★★☆☆ | ★★★★☆ |
| **Moneycontrol** | Real-time quotes, good earnings coverage | Significant clickbait, "exclusive" stories often thin, SEO-driven headlines | ★★★★☆ | ★★★☆☆ |
| **LiveMint** | Quality analysis, good on policy/macro | Slower to break news, fewer daily articles | ★★★☆☆ | ★★★★☆ |
| **CNBCTV18** | Market hours live coverage, trader sentiment | TV-first means web articles are transcripts, repetitive | ★★★★☆ | ★★★☆☆ |
| **Business Standard** | Policy depth, regulatory scoops | Conservative bias, slower publication | ★★☆☆☆ | ★★★☆☆ |

#### Tier 3 — Use With Caution

| Source | Why Caution | Specific Issues |
|--------|-------------|-----------------|
| **Moneycontrol "exclusive" reports** | Often planted, promotional content | Hype cycles around IPOs, SME stocks |
| **Zee Business / Anil Singhvi segments** | Retail-targeted, hype-heavy | Specific stock "tips" that create pump dynamics |
| **Pulse by Zerodha (Tickertape)** | Aggregator, no original reporting | Deduplication noise—same story from 5 sources |
| **IndiaBulls/Angel One research** | Broker research disguised as news | Conflict of interest—they profit from trading volume |
| **Any "WhatsApp forward" type source** | Manipulation, pump-and-dump | Common in Indian markets, especially small-caps |

### Crypto Sources

#### Tier 1

| Source | Notes |
|--------|-------|
| **CoinDesk** | Industry standard, breaks major stories, recently acquired by Bullish (bias risk) |
| **The Block** | Institutional-grade reporting, paywalled for best content |
| **Glassnode/CoinMetrics (on-chain)** | Data, not news — but more reliable than any article |

#### Tier 2

| Source | Notes |
|--------|-------|
| **Cointelegraph** | Good coverage, but sensationalist headlines. Your current RSS source — acceptable but weight lower |
| **Decrypt** | Decent, but smaller team, sometimes slow |
| **CryptoSlate** | Aggregator-heavy |

#### Tier 3 — Dangerous for Trading

| Source | Why |
|--------|-----|
| **99% of Crypto Twitter/X** | Paid shilling, coordinated pumps, "alpha" accounts that front-run followers |
| **YouTube crypto channels** | Entertainment, not intelligence |
| **Telegram channels** | Pump-and-dump central |

**Crypto exception**: For BTC/ETH specifically, Twitter/X is actually faster than any news site for breaking events (exchange hacks, protocol issues, whale movements). But it's a minefield. Using it requires sophisticated bot detection that's outside SignalFlow's scope.

### Forex Sources

| Tier | Sources |
|------|---------|
| Tier 1 | **ForexLive** (your current source — good choice), **Reuters FX**, **Bloomberg FX** |
| Tier 2 | **FXStreet**, **DailyFX**, **Investing.com** |
| Tier 3 | **BabyPips** (educational, not news), **FX Empire** (SEO spam) |

### Source Weighting Recommendation

```python
SOURCE_WEIGHTS = {
    # Tier 1: High reliability, primary sources
    "reuters": 1.0,
    "bloomberg": 1.0,
    "bse_nse_filings": 1.0,     # treat exchange filings as gospel
    "pti_wire": 0.95,
    
    # Tier 2: Good but needs cross-reference  
    "economic_times": 0.80,
    "livemint": 0.80,
    "cnbctv18": 0.75,
    "moneycontrol": 0.65,       # lower due to clickbait
    "business_standard": 0.75,
    
    # Crypto sources
    "coindesk": 0.85,
    "the_block": 0.85,
    "cointelegraph": 0.65,      # sensationalist headlines
    
    # Forex sources
    "forexlive": 0.80,
    "fxstreet": 0.70,
    
    # Default for unknown sources
    "unknown": 0.40,
    
    # Social / blogs
    "twitter": 0.30,            # except for crypto breaking news
    "blog": 0.20,
    "youtube_transcript": 0.15,
}
```

### Critical Issue With Current Implementation

Your current `news_fetcher.py` fetches from Google News RSS and Bing News RSS. These are **aggregators** — you get the headline but lose source identity. When Claude sees 10 headlines, it doesn't know if they're from Reuters (trustworthy) or a random blog (noise).

**You MUST pass source attribution to Claude.** Change from:

```
Articles:
- RBI holds repo rate at 6.5%
- Markets rally on RBI hold
- Inflation fears ease after RBI decision
```

To:

```
Articles:
- [Reuters] RBI holds repo rate at 6.5% — 10 min ago
- [Moneycontrol] Markets rally on RBI hold — 25 min ago  
- [Unknown Blog] Inflation fears ease after RBI decision — 45 min ago
```

This alone will dramatically improve sentiment analysis quality.

---

## 6. Indian Market News Calendar

### Key Scheduled Events That Move Indian Markets

#### HIGH Impact (Market-Wide)

| Event | Frequency | Typical Date/Time | Impact Duration | Advance Notice |
|-------|-----------|-------------------|-----------------|----------------|
| **RBI MPC Decision** | 6x/year (bimonthly) | 10:00 AM IST, Friday of MPC week | 1-3 days | Schedule published yearly |
| **Union Budget** | Annual (1 Feb) | 11:00 AM IST | 1-2 weeks | Date fixed by convention |
| **US Federal Reserve Decision** | 8x/year | 11:30 PM IST (next day impact on India) | 2-5 days | FOMC calendar published yearly |
| **India CPI Data** | Monthly (12th-14th) | 5:30 PM IST | 1 day | ~2 weeks advance |
| **India GDP Data** | Quarterly | 5:30 PM IST | 2-3 days | ~2 weeks advance |
| **FII/DII Data (daily)** | Daily after market close | 6:30 PM IST onwards | Next day open | Daily |
| **US Non-Farm Payrolls** | Monthly (1st Friday) | 6:00 PM IST (next day impact) | 1-2 days | Known schedule |
| **India PMI (Mfg + Services)** | Monthly (1st-5th) | 10:30 AM IST | 1 day | ~1 week advance |
| **India IIP Data** | Monthly | 5:30 PM IST | 1 day | ~2 weeks advance |

#### MEDIUM Impact (Sector-Specific)

| Event | Frequency | Typical Timing | Key Sectors |
|-------|-----------|----------------|-------------|
| **Quarterly Earnings Season** | 4x/year (Jan, Apr, Jul, Oct) | After market hours, staggered over 3-4 weeks | ALL sectors |
| **Auto Sales Data** | Monthly (1st of month) | Throughout the day | Auto stocks |
| **GST Collection Data** | Monthly (1st of month) | Morning | Broad market sentiment |
| **Crude Oil Inventory (EIA)** | Weekly (Thursday) | 8:00 PM IST | Oil stocks, ONGC, IOC, aviation |
| **India Trade Balance** | Monthly | Post-market | INR, IT stocks |
| **RBI Forex Reserves** | Weekly (Friday) | Evening | USD/INR |
| **SEBI Board Meetings** | As scheduled | Varies | Broker stocks, market structure |

#### LOW Impact But Worth Tracking

| Event | Impact On |
|-------|-----------|
| Monsoon progress reports (IMD) | Agri, FMCG, rural economy plays |
| OPEC meetings | Crude-linked stocks |
| China PMI/data | Metals, commodities |
| ECB decisions | EUR/USD, global sentiment |
| Japanese macro data | GBP/JPY (your tracked pair) |

### Scheduled vs. Unscheduled Events

This distinction is **critical** for signal generation:

| Aspect | Scheduled Events | Unscheduled Events |
|--------|-----------------|-------------------|
| **Timing** | Known in advance (calendar) | Surprise |
| **Market pricing** | Market prices in expectations BEFORE the event | No pre-pricing |
| **Signal timing** | Signal value is in the DEVIATION from expectations | Signal value is in the event itself |
| **Volatility** | Often spike in VIX before event, mean-revert after | Unpredictable volatility |
| **News coverage** | Pre-event speculation articles → post-event reaction | Breaking news only |
| **Trading approach** | "Better/worse than expected" is what matters | Magnitude + implications matter |

**For SignalFlow, this means:**

1. **Maintain an economic calendar** (even a simple JSON file of known event dates)
2. **For scheduled events**: Track *consensus expectations* vs *actual outcomes* — the deviation is the signal, not the event itself
3. **For unscheduled events**: Speed matters more. Flag them as "Unscheduled" and prioritize in alerts
4. **Pre-event signals**: Lower confidence. "RBI MPC tomorrow, expect volatility" is useful but shouldn't be a high-confidence BUY/SELL
5. **Post-event signals**: Higher confidence. "RBI cut 25bps vs expected hold" — this is actionable

### The Indian Market News Cycle (A Typical Day)

```
05:30-07:00  Global cues trickle in
             - US market close results (~05:30 IST)
             - Asian markets open (Japan 05:30, China 07:00)
             - SGX Nifty futures indicate opening direction

07:00-09:15  Pre-market prep (YOUR MORNING BRIEF WINDOW)
             - Newspaper headlines (ET, BS, Mint)
             - Broker pre-market notes
             - F&O data analysis (OI changes)
             - ADR prices for Indian stocks listed abroad

09:15-10:00  Opening hour — most volatile
             - Gap-up or gap-down based on global cues
             - Initial price discovery, high volumes
             - Avoid generating signals in first 15 min (noise)

10:00-11:30  News-driven morning
             - Corporate announcements
             - Broker upgrades/downgrades
             - Government/regulatory announcements
             - RBI data releases at 10:00 AM

11:30-13:00  Pre-lunch lull
             - Volumes thin
             - European markets open (~13:30 IST impact)

13:00-14:00  Post-lunch recovery
             - Fresh institutional activity
             - European market influence begins

14:00-15:00  Closing hour preparation
             - Institutional squaring-off
             - F&O expiry effects (Thursday)
             - Final hour momentum trades

15:30-16:00  Post-market
             - Closing prices finalized
             - After-hours corporate announcements begin
             - FII/DII data processing

16:00-18:00  Evening analysis (YOUR EVENING WRAP WINDOW)
             - FII/DII data released
             - Corporate results (after board meetings)
             - Post-market analysis articles flood in

18:00-23:30  US pre-market → US Market Hours
             - US data releases (CPI, payrolls, etc.)
             - Fed decisions (~11:30 PM IST)
             - Will affect next day's India open
```

### Recommendation

Build a lightweight `EventCalendar` service:
- Preload known event dates from a JSON/YAML file (updated monthly)
- Tag incoming news events as "scheduled" or "unscheduled"
- For scheduled events: capture the *surprise factor* (actual vs consensus)
- Adjust signal timing: pre-event signals get lower confidence; post-event, higher

---

## 7. Narrative Formation — How Market Stories Work

### How Narratives Form

A financial narrative is a collective story that market participants tell themselves to explain price action and project the future.

**Formation pattern**:

```
Phase 1: SEED EVENT
    A single data point or event creates the initial narrative
    Example: "RBI signals dovish tilt in February MPC" (Feb 2026)

Phase 2: CONFIRMATION BIAS
    Media & analysts cherry-pick data that supports the narrative
    Example: "CPI falls to 4.8% — rate cut imminent"
    Example: "Credit growth slowing, supports rate cut thesis"
    (Disconfirming data gets buried: "Core inflation sticky? Minor detail.")

Phase 3: CONSENSUS HARDENS
    The narrative becomes "what everyone knows"
    Example: "Rate cut cycle has begun" — consensus, priced into bonds and rate-sensitives

Phase 4: CROWDED TRADE
    Everyone is positioned for the narrative
    Example: Bank stocks at all-time highs on rate-cut expectations

Phase 5: NARRATIVE BREAK
    Something challenges the story
    Example: "Vegetable prices spike, CPI back to 5.5% — RBI pauses"

Phase 6: NEW NARRATIVE
    The old story dies, new one emerges
    Example: "Inflation concerns return" or "Growth slowdown fears"
```

### Narrative Persistence

| Narrative Type | Typical Duration | Examples |
|---------------|-----------------|---------|
| **Flash narrative** | Hours to 1-2 days | "Panic selling on FII outflows" |
| **Event narrative** | 1-2 weeks | "Budget rally" / "Budget selloff" |
| **Thematic narrative** | 1-3 months | "Rate cut cycle", "Earnings recovery", "China+1 beneficiary" |
| **Structural narrative** | 6-18 months | "India growth story", "Digital India transformation" |
| **Secular narrative** | Years | "India's demographic dividend", "India as $5T economy" |

**For SignalFlow's timeframe (2-4 week swing trades)**: Thematic narratives are the sweet spot. Your signals should aim to ride 1-3 month narratives, not flash reactions.

### How to Detect Narrative Shifts (Practical Approach)

1. **Keyword frequency tracking**: Count how often specific phrases appear across sources over time
   - "Rate cut" mentions per week → declining = narrative fading
   - "Inflation" mentions per week → rising = new narrative forming
   
2. **Sentiment trend vs. spot**: Don't just look at today's sentiment score. Track the 7-day and 30-day moving average.
   - Sentiment trending from 70→50 over 2 weeks = narrative shift in progress
   - Single-day drop from 70→45 = event reaction, not narrative shift
   
3. **Cross-source divergence**: When Reuters says bullish and Moneycontrol says bearish for the same symbol, a narrative battle is underway. That's a signal of high uncertainty — lower confidence, not higher.

4. **What doesn't move the market**: If bearish news drops and the stock doesn't fall, the bullish narrative is strong. Track "non-reactions" — they're more informative than reactions.

### Recommendation for SignalFlow

Don't try to build a "narrative detection engine." That's PhD-level NLP research.

Instead:
1. **Track rolling sentiment** over 7/14/30 day windows per symbol
2. **Detect sentiment trend breaks**: When 7-day average crosses 14-day average, flag as "Sentiment reversal detected"
3. **Surface narrative keywords**: Have Claude extract 3-5 key themes per week ("rate cut hopes, FII outflows, earnings season, monsoon fears"). Show these as tags on the dashboard.
4. **Weekly narrative summary**: Your existing weekly digest is the perfect place. Have Claude write 2-3 sentences about "narrative shifts this week."

---

## 8. Red Flags — How Retail Traders Get Burned by News

### The Top 7 News Traps

#### 1. "Buy the Rumor, Sell the News" (Most Common)

**What happens**: Stock rallies into an expected positive event. On the event day (good results, approval, etc.), it falls.

**Why**: Institutional investors bought before the news (on the "rumor"). They sell INTO the positive news because retail is now buying.

**How SignalFlow should handle this**: 
- If a stock has rallied >5% in the 5 days before a scheduled event, reduce confidence on BUY signals
- After positive scheduled events (earnings, policy), wait 1 session before generating BUY
- Label signals as "Event may be priced in" when pre-event rally is detected

#### 2. Headline ≠ Reality

**What happens**: "TCS delivers RECORD revenue!" — stock falls 4%. Why? Revenue was up 3%, but margins contracted, and management guided lower for next quarter.

**The problem**: RSS headlines can only capture one dimension. Claude sees "RECORD revenue" and scores bullish. But the actual story is bearish.

**How to mitigate**:
- Never generate signals on headlines alone for earnings events
- If possible, wait for analyst reaction articles (30-60 min post-event)
- For earnings: the DETAIL matters more than the headline. Consider adding a specific earnings data source that provides actual numbers (not headlines)

#### 3. Contradictory News for Same Symbol

**What happens**: "HDFC Bank strong loan growth!" and "HDFC Bank faces RBI scrutiny on tech outages" on the same day.

**Current system problem**: Your system fetches both, Claude averages them, and you get a wishy-washy "neutral" score. The reality is one is bullish and one is bearish FOR DIFFERENT REASONS.

**Solution**: Have Claude explicitly identify contradictory signals and surface them. A signal with "conflicting news detected" and a lower confidence is more honest than a false-precision "52% neutral."

#### 4. Old News Recycled

**What happens**: RSS feeds serve the same story from 3 days ago because it's still "trending." Your system treats it as fresh news.

**Your current dedup**: Exact headline match only. Easy to miss: "RBI holds rates" (Day 1) vs "Impact of RBI rate hold on banks" (Day 3 analysis of same event).

**Solution**: Timestamp-aware analysis. Pass article dates to Claude. Ask Claude to distinguish "new development" from "analysis of old event."

#### 5. Regional/Language Bias

**What happens**: English language financial media in India has an urban, IT-sector, large-cap bias. Coverage of pharma, commodities, and regional companies is thinner.

**Impact on SignalFlow**: Your sentiment analysis will be systematically better for TCS/INFY (heavy coverage) than for BHARTIARTL or MARUTI (less financial coverage).

**Mitigation**: Track article count per symbol. If a symbol consistently gets <3 articles, reduce the sentiment weight in scoring. Your existing fallback (cap at 60% confidence if no AI) already handles this — good.

#### 6. Paid/Planted News

**What happens**: In Indian markets, promotional articles disguised as news are common, especially for mid-caps and SMEs. These appear on Moneycontrol, ET, and even BSE press releases.

**Red flags**: 
- "Hidden gem stock" / "multibagger" language
- Tiny companies with suspiciously bullish coverage
- Multiple "different" articles appearing within hours with same bullish talking points

**For SignalFlow**: Less of an issue since you track large-cap NIFTY 50 names. But if you ever expand to mid/small-caps, this becomes critical. For now, note in your source weighting.

#### 7. After-Hours/Pre-Market Panic

**What happens**: Negative news drops at 7 PM IST, retail traders panic on social media, morning gap-down is severe...then the stock recovers to green by 11 AM because the news wasn't as bad as feared.

**Recommendation**: For after-hours breaking news, include a disclaimer: "After-hours news — wait for market open to assess full impact before acting."

---

## 9. Specific Source Recommendations by Market

### Indian Stocks — Top 10 Sources

| Rank | Source | Access Method | Speed | Reliability | Trading Relevance | Notes |
|------|--------|-------------|-------|-------------|-------------------|-------|
| 1 | **BSE/NSE Corporate Filings** | BSE API / NSE API (scraping) | ★★★★★ | ★★★★★ | ★★★★★ | Primary source for all corporate data. Board outcomes, insider trades, shareholding. |
| 2 | **Reuters India** | Google News RSS (filtered) | ★★★★★ | ★★★★★ | ★★★★☆ | Best wire service for India markets. |
| 3 | **Economic Times Markets** | RSS: `economictimes.com/markets/rssfeeds/1977021501.cms` | ★★★☆☆ | ★★★★☆ | ★★★★☆ | You already have this. Good breadth. |
| 4 | **Moneycontrol** | RSS: `moneycontrol.com/rss/marketreports.xml` | ★★★★☆ | ★★★☆☆ | ★★★★☆ | You already have this. Fast but noisy. |
| 5 | **LiveMint** | RSS: `livemint.com/rss/markets` | ★★★☆☆ | ★★★★☆ | ★★★★☆ | Better signal-to-noise than MC. Add this. |
| 6 | **NDTV Profit (Bloomberg Quint)** | RSS / scraping | ★★★★☆ | ★★★★☆ | ★★★★☆ | Strong on M&A, institutional stories. |
| 7 | **Business Standard** | RSS: `business-standard.com/rss/markets-106.rss` | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | Slower, but quality analysis. |
| 8 | **CNBCTV18** | RSS / scraping | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | Good for intraday sentiment. |
| 9 | **Trendlyne** | API (freemium) | ★★★☆☆ | ★★★★☆ | ★★★★★ | Aggregated fundamental data + news. |
| 10 | **Screener.in** | Scraping (no API) | ★★☆☆☆ | ★★★★★ | ★★★★☆ | Best for quarterly results data. |

### Crypto — Top 10 Sources

| Rank | Source | Access Method | Speed | Reliability | Trading Relevance |
|------|--------|-------------|-------|-------------|-------------------|
| 1 | **On-chain data (Glassnode)** | API (paid) | ★★★★★ | ★★★★★ | ★★★★★ |
| 2 | **CoinDesk** | RSS: `coindesk.com/arc/outboundfeeds/rss/` | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| 3 | **The Block** | RSS (partial) | ★★★★☆ | ★★★★★ | ★★★★☆ |
| 4 | **Cointelegraph** | RSS: `cointelegraph.com/rss` (you have this) | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| 5 | **CoinGecko Blog/News** | API + RSS | ★★★☆☆ | ★★★★☆ | ★★★☆☆ |
| 6 | **Messari** | API (freemium) | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| 7 | **DeFi Llama** | API (free) | ★★★★☆ | ★★★★★ | ★★★★☆ |
| 8 | **Whale Alert (on-chain)** | API / Twitter | ★★★★★ | ★★★★★ | ★★★☆☆ |
| 9 | **Decrypt** | RSS | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| 10 | **Twitter/X (select accounts)** | API (expensive) | ★★★★★ | ★★☆☆☆ | ★★★★★ |

### Forex — Top 10 Sources

| Rank | Source | Access Method | Speed | Reliability | Trading Relevance |
|------|--------|-------------|-------|-------------|-------------------|
| 1 | **Reuters FX** | Google News RSS | ★★★★★ | ★★★★★ | ★★★★★ |
| 2 | **ForexLive** | RSS: `forexlive.com/feed` (you have this) | ★★★★☆ | ★★★★☆ | ★★★★★ |
| 3 | **FXStreet** | RSS | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| 4 | **DailyFX** | RSS | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| 5 | **Investing.com** | RSS / scraping | ★★★★☆ | ★★★☆☆ | ★★★★☆ |
| 6 | **Central Bank Official Feeds** | Websites (RBI, Fed, ECB, BOJ) | ★★★★★ | ★★★★★ | ★★★★★ |
| 7 | **Bloomberg FX** | Google News RSS | ★★★★★ | ★★★★★ | ★★★★★ |
| 8 | **TradingEconomics** | API (freemium) | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| 9 | **ActionForex** | RSS | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ |
| 10 | **FX Empire** | RSS | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ |

---

## 10. Content Design — How to Display News to a Retail Trader

### The Core Principle

**Your user doesn't want to read news. She wants to know what the news MEANS for her positions.**

She has an M.Com. She's smart enough to understand "repo rate unchanged" but she needs help connecting to "what does this mean for my HDFC Bank position?"

### Ideal Signal-Linked News Card

```
┌─────────────────────────────────────────────────────┐
│ 🔴 HIGH IMPACT EVENT                    45 min ago  │
│                                                      │
│ RBI MPC Holds Repo Rate at 6.5%                     │
│                                                      │
│ Monetary Policy · Scheduled Event · 5 sources        │
│                                                      │
│ "RBI held as expected but Governor's commentary      │
│  was hawkish, surprising markets. Highlighted        │
│  food inflation risks and global uncertainty."       │
│  — AI Summary (3 sentences max)                      │
│                                                      │
│ ┌──────────────────────────────────────┐             │
│ │ 📊 Market Reaction (within 30 min): │             │
│ │  NIFTY Bank: -0.8%  │  USD/INR: +0.2%│            │
│ │  HDFCBANK: -1.1%    │  SBIN: -0.6%   │            │
│ └──────────────────────────────────────┘             │
│                                                      │
│ 🔗 Related Signal: HDFCBANK — HOLD (dropped         │
│    from BUY after hawkish commentary)                │
│                                                      │
│ Sources: Reuters, ET, Moneycontrol, LiveMint, BS     │
│ [Expand for full article links]                      │
└─────────────────────────────────────────────────────┘
```

### Metadata That Matters

| Field | Why It Matters | Display Priority |
|-------|---------------|------------------|
| **Event title** | What happened | Always show |
| **Time since event** | Is this stale? | Always show ("45 min ago") |
| **Impact magnitude** | Should I care? | Always show (color-coded) |
| **Event type tag** | Quick categorization | Always show |
| **Scheduled/Unscheduled** | Sets expectations | Show as badge |
| **AI summary** | What it means | Always show (3 sentences MAX) |
| **Affected symbols** | What to watch | Always show |
| **Market reaction** | How big was the move? | Show if data available |
| **Source count** | Credibility signal | Always show |
| **Related signals** | Connect to action | Show if signal exists |
| **Consensus direction** | Do sources agree? | Show if divergent |
| **Contradictory signals** | Risk warning | Show prominently if present |
| **Full source list** | For the curious | Collapsed/expandable |

### Summary Length Guidelines

| Context | Ideal Length | Format |
|---------|-------------|--------|
| **Signal card snippet** | 1 sentence (15-20 words) | "RBI hawkish hold may pressure bank stocks short-term." |
| **Event card summary** | 2-3 sentences (40-80 words) | What happened + why it matters + what to watch |
| **Signal detail page** | 3-5 sentences (80-150 words) | Full AI reasoning with specific indicators |
| **Morning/evening brief** | 150-200 words total | Already implemented well in your prompts |
| **Full event timeline** | No limit (scrollable) | Chronological articles with timestamps |

### What NOT to Show

1. **Full article text.** You're not a news reader. Link out.
2. **Raw sentiment scores.** "Sentiment: 67" means nothing to a human. Translate: "Mildly Bullish" with a color bar.
3. **Multiple articles about the same thing without grouping.** This is the #1 UX anti-pattern in news dashboards.
4. **Causal chains unless high confidence.** One wrong chain will undermine trust in all chains.

---

## Summary of Prioritized Recommendations

### Must Have (for the news intelligence enhancement)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| 1 | **Pass source identity to Claude** — Stop losing source info from RSS aggregators | Low | High |
| 2 | **Add article timestamps to sentiment prompt** — Let Claude weigh fresh vs stale | Low | High |
| 3 | **Build Event entity** — Cluster articles into events with canonical titles | Medium | High |
| 4 | **Add 3-4 RSS sources** — LiveMint, Business Standard, CoinDesk, FXStreet | Low | Medium |
| 5 | **Source weighting** — Weight sentiment by source credibility tier | Medium | High |
| 6 | **Scheduled event calendar** — JSON file of known RBI/macro/earnings dates | Low | Medium |

### Should Have

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| 7 | **Event-to-signal traceability** — Every signal links back to news events that influenced it | Medium | High |
| 8 | **News staleness flags** — Label events by age and adjust trader expectations | Low | Medium |
| 9 | **Rolling sentiment trend** — 7/14/30 day moving average per symbol | Medium | Medium |
| 10 | **Contradictory news detection** — Flag when sources disagree on direction | Medium | Medium |

### Nice to Have (but be careful)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| 11 | **1-hop causal connections** — Event → directly affected symbols | Medium | Medium |
| 12 | **News dashboard page** — Timeline of events with filters by type/market | High | Medium |
| 13 | **Narrative keyword tracking** — Weekly theme extraction | Medium | Low |

### Do NOT Build (yet)

| # | Why Not |
|---|---------|
| Multi-hop causal chains | Unreliable, will erode trust. Let Claude suggest in text, don't visualize as graphs |
| Real-time news ingestion | RSS is fine for swing trading. Real-time needs paid APIs and 10x infrastructure |
| Social media integration | Minefield of noise, manipulation, and bots. Not worth it at current scale |
| Automated narrative detection | Research-grade NLP problem. Use Claude's weekly summary instead |

---

## Current System Gaps (Specific to Codebase)

Based on reviewing the code:

1. **`news_fetcher.py` discards everything except headline text.** No source, no URL, no timestamp, no article body. This is the single biggest improvement opportunity.

2. **No news persistence.** Articles are fetched, sent to Claude, and forgotten. You can't build event tracking without storing articles in the database.

3. **Deduplication is headline-exact-match only** (lowercase `seen` set in `fetch_news_for_symbol`). Two slightly different headlines about the same event pass through as separate articles.

4. **Google News RSS strips source attribution.** When you fetch from `news.google.com/rss/search`, the `<title>` tag contains the headline but the source is buried in `<source>` tag which you don't parse.

5. **No article date parsing.** RSS feeds include `<pubDate>` which you ignore. Claude has no idea if an article is 10 minutes old or 10 hours old.

6. **Sentiment cache is per-symbol, not per-event.** If two big events hit the same stock in one day, the second event gets the cached result from the first.

7. **No feedback loop from signal accuracy → news source quality.** You don't know which sources led to accurate signals vs. which led to wrong calls.

---

*This review reflects the perspective of someone who has written 10,000+ market stories and watched every kind of news-driven trade blow up. The goal is not to be pessimistic — it's to save you from building a beautiful causal chain visualization that shows "A caused B caused C" when the honest answer is "nobody really knows why the market did what it did today."*

*Build the foundations (event tracking, source quality, timeliness). The fancy visualizations can come later, once you have data to prove they add value.*
