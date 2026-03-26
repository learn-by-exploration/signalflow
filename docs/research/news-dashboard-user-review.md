# SignalFlow AI — News Dashboard & Event Chain: Target User Review

> **Reviewer**: Priya (persona) — 28, M.Com Finance, Financial Services analyst, Zerodha account, ₹2L capital  
> **Date**: 24 March 2026  
> **Feature under review**: News Dashboard + Event Chain Visualization  
> **Status**: User feedback — input for spec.md  

---

## 1. Current Pain Points

### Signals feel like magic — and magic doesn't build confidence

When I open SignalFlow and see "STRONG_BUY — HDFCBANK, 92% confidence," my first reaction isn't excitement. It's suspicion. *Kyun?* The card shows me RSI: 62.7, MACD: Bullish, Volume: High — okay, but I learned these in my M.Com. I know what RSI means. What I don't know is **what happened today** that made all these indicators line up *right now*.

The AI reasoning says things like "Credit growth accelerating. NIM expansion confirmed." — confirmed by whom? Which quarterly result? Which analyst report? Which RBI circular? I have no way to verify this. I can't click through to the source. It reads like a confident friend giving me a tip at a chai stall — persuasive, but unverifiable.

### Specific frustrations:

- **No "why now" context.** A BUY signal on SBIN could mean anything. Did SBI just announce results? Did the government announce a PSU bank recapitalization? Or is it just a technical bounce? The signal doesn't tell me.

- **Sentiment score is a black box.** The card shows "sentiment_data" but it's just a number. Score: 72. Based on what? 3 articles? 30 articles? Articles from Economic Times or some random blog? I literally cannot tell.

- **The AI reasoning is a paragraph, not evidence.** It reads like a conclusion, not an argument. I want to see the premises: "RBI held rates steady (source: RBI MPC minutes, 22 Mar) → Banks' NIM protected → HDFC Bank Q3 NIM was 4.1% vs 3.8% last year (source: BSE filing) → Technical breakout above ₹1,660 resistance." That's a chain I can verify. What I get instead is a smooth paragraph I can't disaggregate.

- **I can't distinguish between technical-only and news-backed signals.** The system falls back to technical-only when the AI budget runs out or when there's no news. But I have no way to know that. A 58% confidence signal with strong news backing is very different from a 58% confidence signal with zero news analysis — but they look identical on my screen.

- **Old signals sit there like stale bread.** I see "Signal is 3d old — check conditions" but the world moved in 3 days. What happened since the signal was generated? Did any news invalidate it? I have to go check Moneycontrol myself. That defeats the purpose.

---

## 2. What Would Actually Help

### The questions I ask myself before acting on a signal:

1. **"What just happened?"** — Is there a specific trigger event? Earnings, policy change, global news?
2. **"Is this news already priced in?"** — NIFTY jumped 200 points yesterday on budget expectations. If the signal fires today, am I too late?
3. **"What could go wrong?"** — What's the bear case? What downside risks exist that this signal doesn't mention?
4. **"What are others saying?"** — Is this consensus or contrarian? If every analyst on CNBC-TV18 is already saying BUY HDFCBANK, the upside might be limited.
5. **"How much of this is news vs. just chart patterns?"** — I want to know the split. If a signal is 100% technical, fine, but tell me explicitly.
6. **"Is this relevant to my position size?"** — ₹20,000 on HDFCBANK is meaningful for me. I need to be very sure.

### What I'd want alongside every signal:

- **The 2-3 specific news events** that contributed to the sentiment score, with dates, sources, and one-line summaries. Not a paragraph — a bullet list.
- **A "freshness" indicator** for the news. "Based on 4 articles from the last 6 hours" vs. "Based on 2 articles from 3 days ago" — these are very different levels of timeliness.
- **Explicit acknowledgment when there's no news.** "No significant news found for RELIANCE in the last 24 hours — this signal is based on technical analysis only." Honesty builds trust.
- **The bear case.** Even for a STRONG_BUY, tell me the risk: "Risk: Global sell-off in financials if US Fed raises rates. FII outflow risk." One sentence is enough.

---

## 3. News Consumption Habits

### My current routine:

| Time | What I do | Source | Duration |
|------|-----------|--------|----------|
| 7:30 AM (getting ready) | Scroll headlines | Moneycontrol app push notifications | 5 min |
| 8:00 AM (commute) | Read 2-3 articles | Economic Times app / Mint app | 10-15 min |
| 9:15 AM (market open) | Glance at NIFTY | Zerodha Kite + SignalFlow Telegram | 2 min |
| 1:00 PM (lunch) | Check portfolio, scan news | Moneycontrol + Twitter (FinTwit India) | 15 min |
| 3:30 PM (market close) | Check day's performance | Zerodha Kite P&L | 5 min |
| 6:00 PM (after work) | Detailed review | SignalFlow dashboard + ET Markets | 20-30 min |
| Weekend | Weekly review | YouTube (CA Rachana Ranade, Akshat Shrivastava) | 1-2 hours |

### What I follow on Twitter/X:

- @ABORTIONFUNDS — no wait, wrong list. Market-related: @doloswala, @nitaborwankar, @OptionsTrading_ — mostly for sentiment, not for DD.

### What would make me switch to SignalFlow for news:

1. **Curation, not aggregation.** I don't want 50 headlines. I want the 3-5 that actually move prices. Moneycontrol gives me 50, and I have to figure out which ones matter.
2. **Stock-specific filtering.** I track 5-6 stocks actively. Show me news ONLY for those, not general market noise.
3. **The "so what?" factor.** Every news headline should have a one-line implication. "RBI holds rates → Bank NIMs protected → Positive for HDFCBANK, KOTAKBANK." That connection is what I currently have to make in my head.
4. **Speed.** If something breaks at 11 AM and your signal fires at 2 PM incorporating that news, I'll notice. I want near-real-time relevance, not a 3-hour delay.
5. **Credibility signals.** If a news item comes from Reuters or RBI's official website vs. "cryptonewsflash.xyz" — I need to know the source quality.

### What would NOT make me switch:

- A plain RSS feed. I have Google News for that.
- AI-rewritten summaries that lose the original phrasing. I want to see the actual headline + source, with your AI adding the "so what."
- Paywalled content. If I click through and hit a Mint paywall, that's a bad experience.

---

## 4. Event Chain Visualization — My Ideal Experience

### Morning (7:30 AM) — Phone, Telegram

I wake up. Telegram notification from SignalFlow:

```
☀️ Morning Brief — 24 Mar

📰 Overnight Events:
• US Fed holds rates, dovish tone (3:30 AM IST)
  → Positive for emerging markets, FII inflows likely
• Brent crude drops 3% to $78
  → Positive for ONGC margins, negative for oil marketing co costs

📊 What this means for your watchlist:
• HDFCBANK: Bank sector positive (rate hold + FII flow)
• RELIANCE: Mixed (crude drop helps petchem, hurts O2C margins)
• BTC: Risk-on mood globally, crypto likely to benefit

🔔 1 new signal generated overnight — check dashboard for details.
```

This is SHORT. This is actionable. I read it in 90 seconds while brushing my teeth. I now have a mental framework for the day ahead.

### Mid-morning (10:30 AM) — Signal fires on Telegram

```
🟢 STRONGLY BULLISH — HDFCBANK

💰 Price: ₹1,678.90
📊 Confidence: ████████░░ 88%

🎯 Target: ₹1,780 | 🛑 Stop: ₹1,630
⏱ Timeframe: 2-4 weeks

📰 News driving this signal:
1. US Fed dovish (3:30 AM) → FII buying expected
2. HDFC Bank Q3 NIM at 4.1% (BSE filing, 18 Mar)
3. RBI rate hold (22 Mar) → Bank margins protected

🤖 AI: Strong bullish convergence. Technical breakout 
above ₹1,660 resistance confirmed by above-average volume.
Three positive catalysts within 6 days — institutional 
buying likely to accelerate.

RSI: 62.7 | MACD: Bullish | Vol: 1.8x avg

📊 View event chain → [link to dashboard]
```

**This is dramatically better.** I can see the 3 news items, I can see the chain of logic, and I can verify each one if I want to. The "View event chain" link takes me to the dashboard for the deep dive.

### Deep dive (6:00 PM) — Dashboard on laptop

I click "View event chain" and see something like:

```
HDFCBANK — Event Timeline

22 Mar ─── RBI MPC holds repo at 6.5%
  │         Source: RBI press release
  │         Impact: Bank NIMs protected for Q4
  │
  ├── 22 Mar ─── HDFC Bank +1.2% on RBI news
  │              (Technical: Broke ₹1,650 resistance)
  │
  │
23 Mar ─── US Fed holds rates, signals 2 cuts in 2026
  │         Source: Reuters, Fed statement
  │         Impact: Emerging market inflows expected
  │
  ├── 24 Mar ─── FII net buyers ₹2,100 Cr (provisional)
  │              Source: NSE bulk deal data
  │
  │
18 Mar ─── HDFC Bank Q3 results: NIM 4.1% (vs 3.8% YoY)
             Source: BSE filing
             Impact: Earnings upgrade cycle likely
             
─── SIGNAL GENERATED ──────────────────────────────
     STRONGLY BULLISH | 88% confidence
     Technical (60%): RSI 62.7, MACD bullish cross, 
                      volume 1.8x above 20-day avg
     Sentiment (40%): Score 81/100 based on 7 articles
                      from 4 sources over 6 days
```

**THIS is what I want.** Not a mind map with bubbles and arrows — I'm not a visual designer. I want a **timeline** that reads top-to-bottom, with clear cause-and-effect annotations. I can trace exactly why this signal exists. I can also see what's missing — "Hmm, no negative news factored in? Let me check if there are any HDFC Bank concerns I should know about."

### What I DON'T want:

- A complicated graph with nodes and edges that looks like a computer science diagram. I studied Finance, not Network Theory.
- "Interactive" visualizations where I have to click 10 things to understand one signal. I have 15 minutes, not 15 hours.
- Category tags like "Macroeconomic → Monetary Policy → India → Banking Sector" — this taxonomy is for machines, not for me.

---

## 5. Information Overload Concerns

### My hard limits:

- **Telegram**: Maximum 5-6 messages per day. Morning brief, 2-3 signal alerts, evening wrap. If I get 15 messages, I'll mute the bot within a week.
- **Dashboard notifications**: A badge showing "3 new signals" is fine. A notification for every market data update is not.
- **News per signal**: 3-5 bullet points. Not 10. If there are 20 relevant articles, the AI should pick the 3 most price-relevant ones. That's the whole point of AI curation.
- **Event chain depth**: Maximum 2 levels deep. "RBI holds rates → Bank NIMs protected → HDFCBANK BUY" is two levels. Don't go deeper. I don't need "US inflation data → Fed policy expectation → Fed holds → Emerging market flows → FII buying → Bank sector positive → HDFC Bank technical breakout." That's a doctoral thesis, not a trading signal.

### When "helpful" becomes "overwhelming":

- When I have to scroll more than 2 screen-lengths on my phone to understand one signal.
- When the news dashboard shows me articles about markets I don't care about. I'm not trading Japanese stocks. Don't show me Nikkei news unless it directly affects NIFTY.
- When every signal has the same boilerplate AI text that I stop reading. Variation matters. If 5 signals in a row say "Technical breakout confirmed by volume" I'll start ignoring all reasoning.
- When the system sends me a signal for a stock I've explicitly said I'm not interested in. Watchlist filtering is essential.

### The golden ratio:

- **Morning**: 1 brief (90 seconds to read)
- **During market hours**: 0-2 signal alerts (only ≥70% confidence for my watchlist)
- **Evening**: 1 wrap (2 minutes to read)
- **Dashboard deep dive**: 15-20 minutes of content max, not a bottomless scroll

---

## 6. Learning Expectations

### What would teach me the most:

1. **Pattern recognition over time.** "This is the 3rd time RBI has held rates and banking stocks rallied within 48 hours. Historical pattern: 70% of the time, the move sustains for 2+ weeks." THIS teaches me a market pattern I can internalize and eventually recognize on my own.

2. **Showing me when the system was wrong and WHY.** "Last month, a BUY signal on TATASTEEL at 89% confidence hit stop-loss. What happened: China dumped steel inventory, global prices crashed 8% in 3 days — an event our model couldn't predict from Indian news sources." This is more valuable than 10 winning signals. It teaches me about Black Swan risks and model limitations.

3. **Connecting news to price action with a delay.** "SEBI announced new F&O margin rules on 15 Mar. The market didn't react for 2 days. On 17 Mar, Nifty options premiums spiked 30%." Showing me that news and price reaction aren't always instant — sometimes there's a digestion period — is a crucial lesson for a new trader.

4. **Sector rotation visibility.** "Money is flowing out of IT stocks and into banks this week. 4 of 5 signals this week are banking stocks." If the system can spot this and tell me, I'm learning how institutional money moves.

5. **"What I should have noticed" retrospectives.** A weekly section that says: "This week, the best signal was INFY at 91% (hit target in 4 days). The key news event was their $2B deal announcement. If you'd seen that news at 9:20 AM and noticed the volume spike by 9:45 AM, you'd have caught the move early." This teaches me to connect news → volume → price, which is the exact skill I'm building.

### How I DON'T want to learn:

- Patronizing tooltips that explain what RSI is every single time. I know what RSI is. Let me toggle off beginner explanations.
- Pop-up tutorials that block my view. I'm here to trade, not to take a course.
- Gamification (badges, streaks, leaderboards). This isn't Duolingo. I'm risking real money.

---

## 7. Trust & Confidence

### What would make me risk ₹20,000 on a signal:

1. **Track record visibility.** "HDFCBANK signals in the last 3 months: 7 generated, 5 hit target, 1 hit stop, 1 expired. Win rate: 71.4%." I need this BEFORE I act, not buried in a history page.

2. **Traceable news sources.** If the signal says "positive earnings" I want to be able to click and see the actual BSE filing or Moneycontrol article. If I can verify even one of the three news items independently, my trust increases dramatically.

3. **Honest uncertainty.** "Confidence is 72%, which means there's a meaningful 28% chance this doesn't work out. The main risk is Q4 guidance — if management commentary is cautious, expect a 3-5% pullback." I'd rather have honest doubt than false confidence.

4. **Recency of data.** "Signal generated 14 minutes ago using data up to 10:15 AM IST. News analysis covers articles published in the last 12 hours." Knowing the signal is FRESH matters enormously. A stale signal is a dangerous signal.

5. **What other signals are saying.** "HDFCBANK: BUY (88%). Other banking signals today: KOTAKBANK: BUY (74%), SBIN: HOLD (52%), ICICICBANK: BUY (69%). Sector consensus: Bullish." If the whole sector is getting buy signals, that's corroborating evidence.

6. **The explicit risk-reward math.** "If target is hit: +₹2,020 (6.0%). If stop-loss is hit: −₹980 (2.9%). Risk-reward: 1:2.06." Show me the rupee amounts for MY position size (or let me input my intended amount). ₹2,020 potential gain vs ₹980 potential loss — that's a bet I can evaluate.

### What destroys trust:

- A signal that fires and immediately moves against me by 2%. The AI said bullish, but the stock dropped. This happens once, I get nervous. Twice, I stop trusting. The cure: show me the invalidation conditions upfront. "If HDFCBANK drops below ₹1,645 intraday, this thesis is weakened. Consider exiting."
- Signals that contradict each other. "BUY HDFCBANK" on Monday, "SELL HDFCBANK" on Wednesday. If this happens, explain what changed. "Monday's signal was based on rate hold tailwinds. Wednesday's reversal triggered by unexpected RBI liquidity tightening announcement." Without that explanation, it looks like the system is confused.
- AI reasoning that's generic. If I read the same reasoning template with different stock names plugged in, I will notice. I have an M.Com. I can tell when text is formulaic.

---

## 8. Telegram vs. Dashboard

### Telegram (phone — quick glances throughout the day):

**What I want:**
- Morning brief with overnight events + watchlist implications (as described above)
- Signal alerts with 3 bullet-point news backing (not full event chain)
- Evening wrap with: what happened today, which signals were affected, any signals invalidated
- Price alerts (₹ triggers I've set)

**What I DON'T want:**
- Full event chain in Telegram. My screen is 6.1 inches. I'll read timelines on my laptop.
- Links that take me to a login page. Deep links should work without extra friction.
- Images or charts in Telegram. They load slowly on 4G and eat my data.

### Dashboard (laptop — evening deep dives):

**What I want:**
- News dashboard as a dedicated page (like /news or /events)
- Event chain timeline for each signal (as described in section 4)
- Full article links that open in new tabs
- Filtering by market, sector, and date range
- "Related signals" — if I'm reading about RBI policy, show me all banking sector signals affected
- Signal detail page should integrate the event chain seamlessly — don't make me go to a separate page

**What I DON'T want:**
- A separate app or service I have to sign up for
- News that autoplays videos. NO.
- Infinite scroll with no categorization. Give me tabs: "My Watchlist News" | "Market Moving" | "All"

### Priority:

**Telegram first, dashboard second.** I'm on my phone 70% of the time I interact with SignalFlow. If the Telegram experience is amazing, I'll open the dashboard maybe 3-4 times a week for deep dives. If Telegram is mediocre and you tell me "go to the dashboard for the full experience," I'll just... not.

---

## 9. Feature Wishlist (Ranked)

### Must-have (I would be disappointed without these):

1. **News-backed signals** — Every signal shows 2-3 specific news items that influenced it, with source, date, and one-line market implication. This is the single highest-value addition. It transforms the signal from "trust me" to "here's why, verify yourself."

2. **"Why now?" trigger explanation** — A single sentence per signal explaining the proximate cause: "Signal triggered because HDFCBANK broke above 20-day SMA with volume 1.8x average, coinciding with FII net buying after Fed dovish stance." Not the full chain — just the trigger.

3. **Watchlist-filtered news feed** — A page/section showing only news relevant to MY tracked stocks. Not a generic market news feed. I have Moneycontrol for that. Show me only what affects my 5-6 actively watched symbols.

### Nice-to-have (would make me love the product):

4. **"What changed since this signal" updates** — If a signal is 2 days old and I haven't acted on it, show me what happened since. "Since this BUY signal on RELIANCE (22 Mar): crude oil rose 2%, Reliance retail Q4 preview positive, signal thesis still intact." Or: "Warning: ITC announced demerger delay — signal may be impacted."

5. **Weekly learning retrospective** — A Sunday evening digest that says: "This week, 3 of 4 signals worked. The one that didn't: TATAMOTORS SELL hit stop because of unexpected EV subsidy announcement. Lesson: government policy announcements can override technical signals." This teaches me to factor in policy risk.

### Future (would be amazing but I can wait):

6. **Event chain timeline** (the full visualization on dashboard) — Useful for deep dives, but honestly, if the Telegram integration and signal-level news bullets are excellent, I might only use this occasionally. Don't over-invest in fancy visualization before nailing the basics.

7. **Sector heatmap with news overlay** — "Banking sector: 3 bullish signals, key driver: RBI rate hold. IT sector: 2 negative signals, driver: US tech layoffs." A bird's-eye view of sector rotation with reasons.

8. **"Similar past events" matching** — "Last time oil dropped 3% and RBI held rates, NIFTY rallied 2.4% over the following week (3 instances in 2024-25)." Historical pattern matching is enormously instructive.

---

## 10. Dealbreakers

### I will stop using SignalFlow if:

1. **Notification spam.** More than 6-8 Telegram messages per day and I'm muting the bot. The bar for sending me a message should be HIGH. Not every HOLD signal needs my attention.

2. **Stale or wrong information presented as fresh.** If the news backing a signal is 5 days old but presented without a date, I'll make a bad trade and blame the system. Always show dates. Always show freshness.

3. **Buzzword salad.** "AI-powered multi-factor sentiment-adjusted neural prediction" — if the reasoning devolves into jargon designed to sound impressive rather than be useful, I'll know. I read research papers in my M.Com. I can smell intellectual hand-waving.

4. **No way to give feedback.** If I act on a signal, I want to log whether it worked. If 5 of my last 6 signals failed and the system doesn't acknowledge this or adjust, I'll feel like I'm talking to a wall.

5. **Feature bloat without reliability.** If the news dashboard launches but the basic signal generation is still showing 3-day-old data, or the sentiment score is still a black box with a fallback value of 50, you've built a porch on a house with no foundation. Fix the core first.

6. **Patronizing tone.** I have a Master's degree in Finance. I don't need explanations of what P/E ratio means. But I also don't need PhD-level quant language. The sweet spot is "bright colleague explaining their analysis over coffee." Not textbook, not dumbed-down.

7. **The system contradicts itself without explanation.** BUY Monday, SELL Wednesday, BUY Friday on the same stock with no acknowledgment that conditions changed. Either explain the flip or don't flip so fast. Signal stability matters for user confidence.

8. **Slow dashboard.** If the news page takes more than 3 seconds to load, I'll close the tab and open Moneycontrol. Especially on my office WiFi which isn't great. Performance is a feature.

---

## Summary: What I Actually Need vs. What Sounds Cool

| What sounds cool | What I actually need |
|---|---|
| Interactive event chain mind map | A clean timeline with 5-8 events, top to bottom |
| Real-time streaming news feed | 3-5 curated headlines per signal, with "so what" |
| AI-generated market commentary | The specific news items that drove THIS signal |
| Full-page news dashboard | Watchlist-filtered news tab that loads in 2 seconds |
| Sentiment analysis visualization | "Positive sentiment from 7 articles (4 sources, last 12 hours)" — one line |
| Complex event taxonomy | "RBI holds rates → Banks benefit → HDFCBANK BUY" — three bullet points |

**The gap in SignalFlow isn't "not enough features." It's "not enough transparency."** I don't need more data. I need the data you already have — the news articles, the sentiment sources, the trigger events — surfaced clearly alongside each signal.

Build the news bullets into signals first. Make Telegram amazing. Then add the dashboard timeline. That's the order that matches how I actually use this product.

---

*— Priya (SignalFlow target user persona)*
