# MKG Expert Panel Review — Iterations 1 & 2

> **Review Date:** 31 March 2026  
> **Document Under Review:** `core/MKG_REQUIREMENTS.md`  
> **Review Scope:** Full requirements document (Sections 1–15)  
> **Review Type:** Expert Panel — 2 of 10 iterations

---

## Panel Members — This Iteration

| # | Expert | Role | Perspective |
|---|--------|------|-------------|
| 1 | **Marcus Chen** | Senior Hedge Fund PM, 20 years, multi-strategy ($5B AUM) | Buy-side financial user |
| 2 | **Dr. Priya Sharma** | VP Supply Chain Risk, Top-5 Automotive OEM | Enterprise supply chain buyer |

---

# EXPERT 1: Marcus Chen — Senior Hedge Fund Portfolio Manager

*Background: Ran event-driven and relative-value strategies at Citadel, Point72. Deep experience with supply chain analysis for semiconductor positions. Currently PM at a $5B multi-strategy fund.*

---

## A. Concept-Requirement Alignment — Score: 7/10

**What aligns well:**
- The Speed 3 framework (Section 2.1) is the single most compelling insight in this document. He's lived this exact pain — spending 3–7 days with analysts manually tracing semiconductor supply chain disruptions while alpha decays. The gap is real.
- The TSMC case study resonates. He actually traded this in February 2024 and remembers the frustrating lag.
- The propagation engine concept (R-PE1 through R-PE10) maps directly to how a PM thinks: "Who gets hit, how hard, which direction."
- Causal chain explainability (R-EXP1) is non-negotiable. PMs need to defend positions to risk committees. "The model said so" doesn't cut it.

**Where concept diverges from requirements:**

1. **The confidence calibration promise is underspecified.** Section 10, capability #19 claims "confidence calibration." But R-EXP5 only says "historical accuracy tracking." A real hedge fund PM needs to know: *What is the out-of-sample hit rate broken down by market regime, sector, event type, and hop depth?* The requirements don't specify this granularity.

2. **"Before anyone else connects the dots" is a testable claim that has no acceptance criteria.** The document promises speed advantage but only specifies <60s propagation latency. Speed advantage isn't just about computation — it's about *information coverage*. If Bloomberg has a headline and 500 analysts read it simultaneously, MKG's 60-second propagation window starts *after* the same news event. The requirements don't address the information sourcing latency or exclusivity.

3. **Cross-domain intelligence (capability #6) is a vision statement, not a requirement.** The document says "financial + supply chain in one graph" but doesn't specify the actual cross-domain queries a financial user would run, the schema for cross-domain edges, or how supply chain disruption events map to tradeable positions.

4. **Backtesting (capability #18) is listed as P2 but is essential for buy-side adoption.** No PM will trust a tool without historical validation. This should be P0.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Portfolio Integration — SHOW-STOPPER GAP

**There is no requirement for portfolio overlay.** The entire document describes MKG as a standalone intelligence tool, but a PM doesn't care about "entity X is impacted." A PM cares about "entity X is impacted, *and I have a $50M position in it, and my risk limit for semiconductor exposure is $200M, and this takes me to $247M.*"

Missing requirements:
- Portfolio position import (via API, file upload, or OMS integration)
- Propagation results overlaid on portfolio positions
- PnL impact estimation ("this event will move my portfolio by approximately $X")
- Real-time portfolio monitoring against graph events
- Risk limit breach alerts tied to propagation events

Without portfolio overlay, this is an interesting academic tool, not a trading tool. This is the #1 gap.

### B2. Historical Backtesting — CRITICAL GAP

R-PE9 ("historical propagation replay") is P2. This is a fundamental misjudgment. No quantitative PM will adopt a tool without backtesting. The specific gaps:

- No requirement for ingesting historical news/event data for backtesting
- No requirement for comparing propagation predictions against actual stock price movements
- No requirement for signal decay analysis (how quickly does the alpha decay after a propagation event?)
- No requirement for strategy-level backtesting (if I traded every STRONG propagation signal, what's the Sharpe?)
- No requirement for regime-conditional accuracy (does it work better in high-vol or low-vol?)

### B3. Signal Latency — UNDERSTATED PROBLEM

The requirements spec says "article to graph update: <5 minutes" (R-NF1) and "trigger to propagation: <60 seconds" (R-NF3). But:

- There's no requirement for how quickly MKG detects the *existence* of news. If Reuters publishes at T+0 and MKG's RSS crawler checks every 60 seconds, MKG doesn't even start processing until T+60s. Bloomberg terminal users had it at T+0s.
- For Speed 3 alpha, 5 minutes might be acceptable. But the document doesn't differentiate between "first-order detection" (where Bloomberg wins) and "second/third-order propagation" (where MKG claims to win).
- No requirement for a low-latency event ingestion mode (direct API feeds from news wire services like Dow Jones Newswires, Thomson Reuters TASS).

### B4. Coverage & Data Quality — INSUFFICIENT SPECIFICATION

- R-DS1 to R-DS8 list data sources but don't specify *completeness requirements*. For semiconductor supply chain, the document needs to define: "What percentage of actual TSMC→Customer relationships must be captured for the graph to be useful?" If MKG captures 60% of edges, the 40% it misses could be exactly where the opportunity is.
- No requirement for data freshness metrics. How stale can an edge weight be before it becomes dangerous? A weight from a 6-month-old signal is worse than no weight at all.
- No quality scoring for edge weights. A SUPPLIES_TO weight of 0.8 from a single blog post vs. 0.8 from SEC filings + earnings transcript + trade data should be treated very differently.

### B5. False Positive / False Negative Analysis

No requirements exist for:
- False positive rate targets (how many propagation alerts turn out to be noise?)
- False negative rate targets (what percentage of real cascading events does MKG miss?)
- Cost of false positives (in a trading context, a false positive means bad trades, not just annoyance)
- Cost of false negatives (missed opportunities have quantifiable dollar impact)

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **R-IA1**: 50+ sources, 13 languages (P0) | Building robust multilingual NER/RE across 13 languages in a 24-week timeline is a multi-year NLP effort. Japanese and Chinese NER for financial entities is a research-grade problem. This should be: English P0, Chinese/Japanese P1, everything else P2. |
| **R-IA10**: 10,000 articles/day | At what cost? If using Claude API for NER/RE at $3/million tokens, 10K articles × ~2K tokens each = 20M tokens/day = ~$60/day = ~$1,800/month just for NER. The document doesn't have a cost model for the ingestion pipeline. |
| **SOM Year 1: $50M–$100M** | This is fantasy. For a B2B data product with no established brand, $50M ARR in Year 1 would require ~100 enterprise contracts averaging $500K/yr, in a space where sales cycles are 6–12 months. A realistic Year 1 target is $1M–$5M ARR from 10–20 early design partners. The document's TAM/SAM analysis is reasonable, but the SOM is off by 10–50x. |
| **R-KG2**: 5,000 entities at launch | This is aggressive but achievable for semiconductor vertical. However, quality matters more than quantity. 500 deeply-connected entities with accurate weights beats 5,000 shallow nodes. |
| **R-NF7**: 99.5% uptime | Standard for paid SaaS, but the document doesn't discuss failover architecture, disaster recovery, or what happens to in-flight propagation calculations during downtime. |

### C2. Underspecified

| Requirement | What's Missing |
|-------------|---------------|
| **R-PE3**: Impact attenuation "default 0.7 per hop" | Why 0.7? This single parameter fundamentally changes output quality. No requirement for how to calibrate it. No requirement for sector-specific or edge-type-specific attenuation. A SUPPLIES_TO edge should attenuate differently than COMPETES_WITH. |
| **R-WAN2**: "Rule-based weight adjustment" | Which rules? What's the rule format? Who writes them? How are they versioned? This is the core intelligence of the product and it's described in one sentence. |
| **R-KG4**: Edge weight 0.0–1.0 | What does 0.3 vs 0.7 mean semantically? Is it revenue dependency percentage? Market share overlap? There's no semantic definition of what the weight *represents*, which means different edges will use weight inconsistently. |
| **R-OUT7**: Alert system with configurable triggers | No requirement for alert fatigue management, alert prioritization, alert grouping, or alert delivery SLA. A PM getting 50 alerts/day will turn them off. |
| **R-SC4**: Multi-tenant isolated graph views | No specification of what "isolated" means. Can Tenant A's tribal knowledge leak to Tenant B? What about shared graph structure vs. private weights? This is a critical data isolation question for hedge fund clients. |

### C3. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| R-IA3 (NER) | No precision/recall targets. "Named Entity Recognition for Company" — at what accuracy? 90%? 95%? 99%? These have very different engineering costs. |
| R-IA4 (RE) | No accuracy target for relation extraction. RE is significantly harder than NER. State-of-the-art financial RE is maybe 75-85% F1. What's the minimum viable accuracy? |
| R-PE6 (<60s latency) | At what graph size? <60s with 5K nodes is easy. <60s with 50K nodes and 500K edges is a different engineering problem. |
| Section 15 (Prediction accuracy >65%) | 65% accuracy *at what confidence threshold*? A system that says "I'm 90% confident" but is right only 65% of the time is worse than one that says "I'm 65% confident" and is right 65%. The calibration curve matters. |

### C4. Missing Edge Cases

- **Market hours**: What happens to propagation during market close? Does the system account for the fact that many affected stocks can't be traded for 16 hours after a weekend event?
- **Liquidity**: Propagation to a micro-cap with $50K daily volume is useless — you can't trade it. No requirement for liquidity filtering.
- **Short-selling constraints**: "SELL propagation" for entities in markets with short-selling bans (China A-shares, certain India stocks) — is this flagged?
- **Currency**: Multi-currency impact estimation. A TSMC disruption affects USD, TWD, JPY, KRW positions simultaneously.
- **Earnings**: What happens when propagation conflicts with an upcoming earnings event? Does the system dampen or amplify?

---

## D. New Requirements to Add

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| R-PORT1 | System must support portfolio position import via API (quantity, entry price, current exposure) | P0 | PM needs to see impact on *their* positions, not abstract entities |
| R-PORT2 | Propagation results must overlay portfolio positions showing estimated PnL impact per position | P0 | The core value proposition requires this |
| R-PORT3 | System must alert when propagation event causes estimated portfolio risk limit breach | P0 | Risk management integration |
| R-BT1 | System must support historical backtesting of propagation signals against actual price movements | P0 (upgrade from P2) | No PM adopts without this |
| R-BT2 | Backtest results must include: hit rate, average return, Sharpe ratio, max drawdown, average decay in alpha | P0 | Standard quantitative evaluation metrics |
| R-BT3 | Historical news/event data must be ingested for backtesting (minimum 2 years for semiconductor vertical) | P0 | Backtesting requires historical data |
| R-DQ1 | Every edge weight must have a data quality score based on source count, source diversity, and recency | P0 | PM needs to distinguish reliable vs. speculative edges |
| R-DQ2 | System must define minimum acceptable edge coverage for each sector before declaring sector "ready" | P1 | Prevents garbage-in-garbage-out |
| R-DQ3 | Edge weights must have a staleness indicator showing time since last confirming signal | P0 | Stale weights are dangerous |
| R-LIQ1 | Propagation results must include liquidity scoring for each affected entity (average daily volume, market cap) | P1 | Untradable entities are noise |
| R-LAT1 | System must support direct news wire API integration (DJNS, Reuters) for <10s event detection | P1 | RSS polling is too slow for serious users |
| R-FP1 | System must track and report false positive rate per event type, sector, and hop depth | P0 | Quality control |
| R-FP2 | System must target false positive rate <30% for high-confidence (>80%) propagation alerts | P0 | Usability threshold |
| R-ATT1 | Impact attenuation factor must be configurable per edge type, not globally | P0 | SUPPLIES_TO attenuates differently than COMPETES_WITH |
| R-ATT2 | System must provide empirical calibration of optimal attenuation factors from backtesting data | P1 | Data-driven, not guesswork |

---

## E. Pricing Validation

**Stated pricing: $50K–$200K/yr per seat for Multi-Strategy Hedge Fund PM**

### Assessment: Conditionally Realistic

The pricing *range* is realistic for the buy-side if — and only if — the product delivers demonstrable alpha. Context:

- Bloomberg Terminal: $24K/yr/seat. MKG needs to be *additive* to Bloomberg, not replace it. So MKG is an incremental $50K–$200K on top of existing $24K Bloomberg spend.
- Alternative data budgets at top-20 hedge funds: $5M–$50M/year. MKG at $200K/seat × 5 seats = $1M/year is within budget.
- **BUT**: The document assumes 50K–$200K/yr pricing without specifying the *unit of value*. Per seat? Per portfolio? Per entity coverage? Per propagation query? This matters enormously for fund adoption.
- **Realistic Year 1 pricing**: $30K–$50K/yr for research analyst seat, $100K–$150K/yr for PM seat with portfolio integration. Discounted "design partner" pricing at 50% off for first 10 clients.

### What actually drives purchasing:

1. **Alpha attribution**: Can the fund attributably show that MKG-sourced signals generated alpha? If yes, $200K/yr is cheap. If no, $30K/yr is expensive.
2. **Integration with existing stack**: Does it pipe into their OMS/PMS? If it requires manual copy-paste into Bloomberg, adoption dies.
3. **Exclusivity window**: How many funds have access? If 200 funds all get the same propagation alert, there's no alpha. The document doesn't address client concentration / exclusivity tiers.
4. **Risk team buy-in**: The PM might want it, but the CRO needs to approve the data vendor. Compliance reviews take 3–6 months at established funds.

### SOM Reality Check:

$50M–$100M Year 1 is unsupportable. More realistic:
- Year 1: 5–10 design partners at $50K avg = $250K–$500K ARR
- Year 2: 20–40 customers at $80K avg = $1.6M–$3.2M ARR
- Year 3: 80–150 customers at $100K avg = $8M–$15M ARR

---

## F. Critical Questions — Make or Break

1. **"Show me a backtest."** What would my PnL have looked like if I'd traded MKG's top-10 propagation signals over the past 24 months? If MKG can't answer this at the first sales meeting, the conversation is over.

2. **"How do I know the graph is complete enough?"** If MKG says "TSMC disruption impacts 47 entities" but I know from my 20 years of experience that it's actually 63 entities — what does that incompleteness mean for the entities MKG *does* flag? How do I calibrate my trust?

3. **"What's the exclusivity model?"** If Point72, Citadel, and Millennium all subscribe, we're all getting the same propagation alerts and there's zero alpha. Is there a limited-seat model? Do I get a different view than competitors?

4. **"How does this integrate with my existing risk system?"** I use Axioma/Barra for factor risk, Bloomberg PORT for portfolio analytics, and an internal OMS. MKG needs to feed into these, not be yet another browser tab.

5. **"What happens when MKG is wrong and I lose money on its signal?"** What's the liability model? How does MKG handle and communicate failed predictions? Is there a kill-switch where I can flag a bad signal and get root-cause analysis within 24 hours?

---
---

# EXPERT 2: Dr. Priya Sharma — VP of Supply Chain Risk, Top-5 Automotive OEM

*Background: Led supply chain resilience programs at Bosch and Toyota. Expert on Tier 2/3 dependency mapping. PhD in Operations Research from IIT Bombay. 15 years experience in automotive supply chain.*

---

## A. Concept-Requirement Alignment — Score: 6/10

**What aligns well:**
- The Tier 2/3 hidden dependency problem (Section 2.2, Problem #1) is *exactly* the problem that keeps her up at night. After the 2021 semiconductor shortage, Toyota's entire resilience program was built around mapping Tier 2/3+ dependencies — and they spent $10M+ on consultants to do what MKG proposes to automate.
- Tribal knowledge encoding (Section 4) is genuinely novel. She has 200+ supplier relationship managers who carry critical intelligence in their heads. When someone retires, that knowledge vanishes.
- Chokepoint detection (capability #16) is directly actionable. She can point to 3 factory shutdowns in the past 2 years caused by chokepoints they didn't know about.
- Substitution difficulty scoring (capability #9) could shave months off supplier qualification decisions.

**Where concept diverges from requirements:**

1. **The entire architecture is optimized for financial markets, not supply chain operations.** The propagation engine assumes "impact scores" as output, but supply chain operators need: estimated disruption duration, alternative sourcing options, recommended mitigation actions, and cost-of-disruption estimates. A number from 0-100 means nothing to a procurement team.

2. **"60-second propagation" is the wrong success metric for supply chain.** For supply chain risk, you don't need 60-second answers — you need *accurate* answers. A supply chain team takes 2–4 weeks to make a sourcing decision. The constraint is accuracy and completeness, not speed. Speed matters for financial markets; depth matters for supply chain.

3. **The data model is entity-centric, not product-flow-centric.** Supply chain analysis follows *products* through transformation stages, not *companies* through business relationships. "TSMC supplies Apple" is less useful than "TSMC N3 process → A17 wafer → OSAT packaging at ASE → shipped to Foxconn Zhengzhou → iPhone 15 assembly." The requirements don't model product flow at this granularity.

4. **No BOM (Bill of Materials) integration.** The requirements have Company→Company SUPPLIES_TO edges, but manufacturing supply chains operate on BOMs. Without BOM mapping, MKG can say "TSMC is disrupted" but can't say "your Q4 production of Model X is at risk because 3 of the 47 components in the ECU come from TSMC's Fab 18."

5. **The "financial + supply chain in one graph" cross-domain claim is premature.** The edge types (Section 5.3.2) are financial-centric. There are no edge types for: SHIPS_VIA, ASSEMBLES_AT, QUALIFIES_AS_ALTERNATIVE, TRANSFORMS_INTO, SUBCOMPONENT_OF. These are the verbs of supply chain intelligence.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Product-Level Granularity — SHOW-STOPPER GAP

The graph models companies, but supply chains operate at the product/component level. Critical missing model elements:

- **Component/Part nodes**: Not just "Product" generically, but specific part numbers (e.g., "TSMC N3 wafer, 300mm, CoWoS package")
- **BOM (Bill of Materials) structure**: Which components go into which finished products, in what quantities?
- **Product-to-facility mapping**: Which specific products are made at which specific facilities?
- **Qualification status**: Which suppliers are qualified for which components? (Automotive qualification takes 12–24 months — you can't just "switch")
- **Inventory buffer levels**: How many weeks of safety stock exist for each component? (This determines how long you have before a disruption hits production)

Without product-level granularity, MKG's supply chain vertical is a marketing story, not a usable tool.

### B2. Disruption Impact Quantification — CRITICAL GAP

The propagation engine produces abstract "impact scores" (0-100). Supply chain operators need:

- **Estimated disruption duration** (days/weeks/months): "Based on historical data and current signals, this disruption is likely to last 6–10 weeks"
- **Revenue-at-risk**: "This disruption puts $47M of Q4 revenue at risk across these 3 product lines"
- **Production line impact**: "Lines 2, 5, and 7 at Plant Nagoya will be affected starting Week 38"
- **Lead time impact**: "Your lead time for Component X increases from 12 weeks to 22 weeks"
- **Cost impact**: "Emergency air freight to bypass this chokepoint will cost approximately $2.3M"

### B3. Alternative Sourcing & Mitigation — CRITICAL GAP

When a disruption is detected, the *immediately next question* is "What do we do about it?" The requirements don't address:

- Alternative supplier recommendations ranked by: qualification status, available capacity, geographic diversification benefit, lead time, cost premium
- Recommended mitigation actions: build buffer stock, qualify alternative, dual-source, redesign component
- Action tracking: has the recommended mitigation been started? By whom? Timeline?
- Historical mitigation effectiveness: "Last time we had a similar disruption, switching to Supplier Y took 14 weeks and cost $3M"

### B4. Industry-Specific Compliance & Standards — MISSING

Automotive supply chain intelligence has regulatory requirements:

- **IATF 16949**: Quality management system compliance tracking for suppliers
- **IMDS (International Material Data System)**: Material composition tracking
- **REACH/RoHS compliance**: Chemical substance restrictions
- **Conflict mineral reporting (SEC Rule 13p-15)**: Tin, tantalum, tungsten, gold sourcing transparency
- **CSRD/ESG**: EU Corporate Sustainability Reporting Directive

None of these are in the requirements. For an automotive VP of Supply Chain, supplier risk = quality risk + disruption risk + compliance risk. MKG only addresses disruption risk.

### B5. Integration with Supply Chain Systems — MISSING

Enterprise supply chain teams use:
- **ERP systems** (SAP S/4HANA, Oracle): Master supplier data, PO history, lead times
- **SRM (Supplier Relationship Management)**: Supplier scorecards, performance history
- **PLM (Product Lifecycle Management)**: BOM structure, component specifications, qualification status
- **Risk platforms**: Resilinc, Everstream, Coupa Risk Aware — MKG needs to show value *beyond* these

The requirements have REST API (R-OUT1) but no specification for any enterprise system integration. Without ERP/SRM/PLM integration, MKG is a standalone tool that requires manual data re-entry — a dealbreaker for enterprise adoption.

### B6. Geographical Risk Modeling — INSUFFICIENT

R-KG, Section 5.3.1 has a "Country/Region" node with "geopolitical_risk_score." This is far too simple for supply chain risk:

- Need sub-national granularity (province/state level — a disruption in Guangdong vs. Xinjiang has very different implications)
- Need natural disaster risk layering (earthquake, flood, typhoon zones mapped to facility locations)
- Need logistics route modeling (shipping lanes, port congestion, border crossing delays)
- Need labor market risk (strikes, wage inflation, skill availability)
- Need energy infrastructure risk (grid reliability, energy cost volatility)

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **SOM Year 1: $50M–$100M** | In enterprise supply chain software, $50M Year 1 is impossible without an established sales force. Resilinc took 10 years to reach ~$50M ARR. Interos took 7 years to reach ~$50M. A realistic Year 1 for supply chain vertical: $500K–$2M from 3–5 design partners. |
| **24-week build plan** | This plan produces a *demo*, not an enterprise-grade product. Enterprise supply chain buyers require: SOC 2 Type II certification (6 months), ISO 27001 (12 months), penetration testing, data residency compliance (GDPR for EU subsidiaries), and SLA guarantees. These alone add 6–12 months. |
| **R-IA1: 50+ sources, 13 languages** | For automotive supply chain, the languages that matter are: English, German, Japanese, Chinese, Korean. Five, not thirteen. And automotive-specific sources (Automotive News, just-auto, WardsAuto, OICA) are more important than generic news sources. |
| **R-KG2: 5,000 entities at launch** | For automotive supply chain, it's not about entity count — it's about *depth* within specific supply chains. 200 entities with complete BOM-level mapping for one vehicle platform beats 5,000 shallow entities across all of semiconductors. |
| **Cross-domain claim** | Combining financial and supply chain intelligence in one product means serving two extremely different user personas with different UX needs, different data requirements, different sales cycles, and different compliance requirements. This is 2 products pretending to be 1. |

### C2. Underspecified

| Requirement | What's Missing |
|-------------|---------------|
| **R-PE3**: Attenuation factor 0.7 per hop | In supply chain, attenuation depends on: inventory buffer (if 12 weeks of stock, first 12 weeks of disruption have zero impact), substitution availability, and production flexibility. A flat 0.7 is meaningless. |
| **Section 8.2**: Semiconductor seed data | Automotive supply chains share semiconductor dependencies but also have: mechanical, chemical, electrical, glass, rubber, polymer, and textile supply chains. The semiconductor focus is a reasonable start but the requirements don't specify how/when to expand to other verticals. |
| **R-TK1**: Expert input with confidence scores | Who enters this? How is entry time compensated? In her experience, getting supply chain managers to enter data into *yet another system* requires management mandate, workflow integration, and clear value-back. No requirement addresses the expert input UX/workflow. |
| **R-OUT3**: Graph visualization | Supply chain users need geographic map overlays showing facility locations, shipping routes, and risk zones — not abstract force-directed graphs. Force-directed layouts are useful for analysts; supply chain managers need maps. |
| **R-SEC7**: "No PII, people tracked as public figures only" | In supply chain, key contacts at Tier 2/3 suppliers are NOT public figures. Factory managers, quality engineers, logistics coordinators — these are private individuals whose contact info and role data may be subject to GDPR. This requirement contradicts supply chain use cases. |

### C3. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| Hidden Dependency Discovery (capability #10) | What's the recall rate target? "Detected 40 of 200 actual Tier 2 dependencies" is 20% recall — is that useful? What minimum recall makes the product valuable? |
| Chokepoint Detection (capability #16) | How is a chokepoint defined? Single-source? <3 qualified alternatives? <6 months of buffer? The definition determines the output list. |
| Substitution Difficulty Scoring (capability #9) | What inputs produce the score? How is it validated? A score without methodology is just a guess. |
| R-NF3: <60s propagation | Supply chain users would prefer 10-minute propagation that models inventory buffers, qualified alternatives, and production schedules over 60s propagation that ignores all of these. |

### C4. Missing Edge Cases

- **Cascade across industries**: Automotive and consumer electronics share semiconductor supply chains. A TSMC disruption affects both. Does MKG model the *competition for limited supply* between industries?
- **Force majeure**: Some supply contracts have force majeure clauses that change the financial impact of disruptions. Not modeled.
- **Supplier financial health**: A Tier 2 supplier going bankrupt is different from a Tier 2 supplier having a temporary capacity issue. Financial health as a leading indicator of supply risk is not in the requirements.
- **Seasonal demand**: Disruption impact varies by season. A fab outage in Q3 (holiday build season) is catastrophically worse than the same outage in Q1.
- **Multi-source components**: If a component is dual-sourced 60/40, a disruption to the 60% supplier is partially mitigated by the 40% supplier's available capacity. Current requirements don't model this.

---

## D. New Requirements to Add

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| R-PROD1 | Graph must support Component/Part nodes with attributes: part_number, specification, category, lifecycle_stage, qualification_status | P0 | Supply chains operate at component level, not company level |
| R-PROD2 | Graph must support BOM (Bill of Materials) edges: SUBCOMPONENT_OF with quantity, criticality, and qualified_supplier_count | P0 | BOM is the foundational structure of manufacturing supply chains |
| R-PROD3 | Graph must support SHIPS_VIA edges with logistics route, transit time, and chokepoint flags | P1 | Logistics modeling is essential for disruption duration estimation |
| R-PROD4 | Graph must support QUALIFIES_AS_ALTERNATIVE edges with qualification_status, time_to_qualify, cost_premium, and capacity_available | P0 | Alternative sourcing is the #1 action taken after disruption detection |
| R-DUR1 | Propagation results must include estimated disruption duration (P10/P50/P90 range) based on historical data and disruption type | P0 | "Impact score 0.8" is meaningless; "6-10 week disruption" is actionable |
| R-DUR2 | Propagation results must include inventory buffer runway per affected component (weeks of supply remaining) | P0 | Determines urgency: 12 weeks of buffer means you have time; 2 weeks means emergency |
| R-MIT1 | System must recommend ranked mitigation actions for each detected disruption (dual-source, buffer, qualify alternative, redesign) | P1 | Detection without recommendation is only half the value |
| R-MIT2 | System must track mitigation action status (recommended → in progress → completed) | P1 | Enterprise workflow integration |
| R-INT1 | System must support SAP S/4HANA integration for master supplier data and purchase order history import | P1 | Enterprise adoption requires ERP integration |
| R-INT2 | System must support BOM import from PLM systems (Teamcenter, Windchill) via standard formats (STEP AP242, JSON) | P1 | Manual BOM entry is impractical for automotive (10,000+ components per vehicle) |
| R-GEO1 | Facility nodes must include sub-national location with natural disaster risk zone classification | P0 | "Taiwan" is insufficient; "Tainan Science Park, Seismic Zone 4, Typhoon Path A" is actionable |
| R-GEO2 | System must support geographic map visualization with facility locations, shipping routes, and risk zone overlays | P1 | Supply chain users think geographically, not abstractly |
| R-COMP1 | Graph must support regulatory compliance edges: REQUIRES_CERTIFICATION with type (IATF, REACH, RoHS), status, and expiry | P1 | Compliance risk is inseparable from supply risk in regulated industries |
| R-FIN1 | System must track and display supplier financial health indicators (credit rating, Z-score proxy, payment behavior) as leading risk indicators | P1 | Supplier bankruptcy is a supply chain risk |
| R-INV1 | Propagation attenuation must account for inventory buffer levels (disruption impact is zero until buffer is exhausted) | P0 | Flat attenuation ignores the most important physical constraint in supply chains |

---

## E. Pricing Validation

**Stated pricing: $100K–$500K/yr for VP Supply Chain**

### Assessment: Range is Realistic, but Adoption Barriers are High

Context from enterprise supply chain procurement:

- **Resilinc**: $150K–$400K/yr depending on supplier count and module. Established market leader for supply chain risk.
- **Interos**: $100K–$300K/yr for multi-tier mapping. Growing competitor.
- **Everstream Analytics**: $200K–$500K/yr for comprehensive supply chain risk + ESG. Acquired by Coupa.
- **Coupa Risk Aware**: $100K–$250K/yr bundled with procurement platform.

MKG's pricing at $100K–$500K/yr is within market range, BUT:

1. **Incumbent displacement is very hard.** She already pays Resilinc $300K/yr. MKG would need to either replace Resilinc (unlikely as a v1.0 product) or be additive to it (which means MKG's value proposition must be clearly differentiated from Resilinc's Tier 2/3 mapping — and Resilinc has 10 years of supplier data she doesn't want to lose).

2. **Enterprise procurement cycles are 9–18 months.** The company would need: RFI → Shortlist → RFP → POC (3-month pilot) → Security review → Legal review → Budget approval → Contract. Year 1 revenue from enterprise supply chain is optimistically 2–3 signed contracts.

3. **Value quantification is required.** She needs to present an ROI case to the CFO. MKG must quantify: "Since deployment, MKG detected disruptions X days earlier on average, enabling mitigation actions that saved an estimated $Y in expediting costs and $Z in lost production."

4. **Data rights and IP are critical.** If MKG's graph learns from her supply chain data and then shares those patterns (even anonymized) with competitors or financial market subscribers, that's a dealbreaker. The cross-domain financial/supply chain claim is a *liability* from the supply chain buyer's perspective — her proprietary supplier data enriching a hedge fund's trading signals.

### What actually drives purchasing:

1. **Pilot success with measurable outcome**: "MKG detected the XYZ disruption 2 weeks before Resilinc, enabling us to secure alternative supply and avoid $5M in line-down costs."
2. **BOM/ERP integration**: If it plugs into SAP and uses her existing data, adoption cost drops dramatically.
3. **Executive mandate**: Post-crisis (like the 2021 chip shortage), the CEO demands "never again." Budget opens. MKG's sales strategy should target post-crisis buying windows.
4. **Consortium model**: If 5 OEMs share the cost of MKG's infrastructure and each gets a private view of their own supply chain, the per-OEM cost drops and the data network effects increase.

---

## F. Critical Questions — Make or Break

1. **"How do you handle my proprietary supply chain data?"** If I feed MKG my BOM, supplier list, and inventory levels — can you guarantee that this data is never used to inform financial market subscribers? Is there a contractual, architectural, and technical isolation guarantee? If not, my legal team kills this on Day 1.

2. **"How does MKG compare to what I already get from Resilinc?"** I pay Resilinc $300K/yr for Tier 2/3 mapping and disruption alerts. They have 10 years of supplier survey data. Specifically, what does MKG do that Resilinc cannot? Show me a side-by-side on a real disruption.

3. **"Can you integrate with SAP S/4HANA?"** Half my procurement team's day is in SAP. Any tool that requires them to log into a separate dashboard and manually cross-reference is dead on arrival. We need push-to-SAP alerts and pull-from-SAP supplier master data at minimum.

4. **"What's the accuracy of your hidden dependency discovery?"** You claim to find Tier 3+ dependencies from news and filings. I know my actual Tier 3 suppliers. If I give you a blind test — here are 100 of my known Tier 3 suppliers, how many can you find? — what percentage do you detect? If it's below 60%, it's a curiosity, not a tool.

5. **"How do I justify the cost to my CFO?"** Give me the ROI framework. Specifically, how much does earlier disruption detection save in terms of: expediting costs, line-down costs, customer penalties, and market share erosion? I need a dollar figure, not a capability list.

---
---

# CROSS-EXPERT SYNTHESIS

## Areas of Agreement

| Finding | Marcus (Finance) | Priya (Supply Chain) | Implication |
|---------|-------------------|----------------------|-------------|
| **SOM Year 1 is fantasy** | $50M–$100M → should be $250K–$500K | $50M–$100M → should be $500K–$2M | Restate Year 1 target to $1M–$3M combined |
| **Backtesting is essential** | P0, not P2 | Less urgent but still needed for validation | Upgrade R-PE9 to P0 |
| **Attenuation factor is underspecified** | Needs to be per-edge-type | Needs to account for inventory buffers | R-PE3 needs major rework |
| **Integration is make-or-break** | OMS/PMS/Risk system integration | ERP/SRM/PLM integration | Must define integration APIs as P0 |
| **Expert input workflow is missing** | Who contributes tribal knowledge? | How to get procurement managers to input data? | Need UX/workflow requirements for R-TK1 |
| **24-week plan produces a demo, not a product** | Add 6+ months for backtest data + calibration | Add 6–12 months for enterprise compliance (SOC 2, ISO 27001) | Realistic MVP is 12–18 months |

## Areas of Divergence

| Topic | Marcus (Finance) | Priya (Supply Chain) | Resolution Needed |
|-------|-------------------|----------------------|-------------------|
| **Speed vs. Accuracy** | 60-second propagation is the value proposition | Accuracy trumps speed; 10 minutes is fine | Build different latency tiers per vertical |
| **Output format** | Impact score + direction + confidence = sufficient | Disruption duration + inventory runway + mitigation actions = required | Two output schemas for two verticals |
| **Graph granularity** | Company-level is acceptable for financial analysis | Component/BOM-level is required for supply chain | Graph must support both abstraction levels |
| **Visualization** | Force-directed graph is useful | Geographic map overlay is essential | Need both visualization modes |
| **Cross-domain value** | Positive — supply chain data enriches financial signals | Negative — proprietary data leaking to finance is a liability | Critical architecture decision: data isolation model |
| **Data sensitivity** | Happy to share graph if it means better predictions | Data is proprietary competitive advantage — no sharing | Tiered isolation is required |

## Top 5 Risks Identified

1. **Cross-domain data isolation**: The financial and supply chain verticals have fundamentally opposing data-sharing incentives. Supply chain buyers want maximum privacy; financial buyers want maximum coverage. This architectural tension must be resolved before building.

2. **Product-market fit fragmentation**: Serving both verticals with one product risks serving neither well. The requirements read like a financial product with supply chain examples bolted on. The supply chain vertical may need its own specification.

3. **Year 1 revenue expectations**: 10–50x overestimation creates unrealistic pressure on the engineering timeline and may drive premature scaling over depth.

4. **Attenuation model naivety**: A flat 0.7 attenuation factor ignores the physical and business constraints that determine actual impact (inventory buffers, substitution availability, contractual terms). This parameter singularly determines output quality.

5. **Missing backtesting foundation**: Without historical validation, neither persona will adopt. This is a data acquisition problem as much as a technical one — MKG needs 2+ years of historical news/events mapped to outcomes.

---

## Recommended Priority Actions

1. **Split the spec**: Create separate requirement addenda for Financial and Supply Chain verticals. Shared graph infrastructure, differentiated output layers.
2. **Define data isolation architecture**: Before building, resolve the cross-domain data sharing model. This is an architectural decision that's nearly impossible to retrofit.
3. **Upgrade backtesting to P0**: Move R-PE9 and add R-BT1–R-BT3. Begin historical data acquisition immediately.
4. **Restate SOM**: Year 1 target $1M–$3M from 10–15 design partners across both verticals.
5. **Add product-level graph schema**: R-PROD1–R-PROD4 for supply chain viability.
6. **Rework attenuation model**: R-ATT1–R-ATT2 + R-INV1 for physically meaningful impact propagation.
7. **Define integration requirements**: Both verticals need system integration specs (R-PORT1–R-PORT3 for finance, R-INT1–R-INT2 for supply chain) at P0/P1.

---

*Next iteration: Experts 3 & 4 — Quantitative Research Lead (systematic strategy firm) + Chief Data Officer (financial data vendor)*
