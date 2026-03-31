# MKG Expert Panel Review — Iterations 9 & 10 + FINAL CONSENSUS

> **Review Date:** 31 March 2026  
> **Document Under Review:** `core/MKG_REQUIREMENTS.md`  
> **Review Scope:** Full requirements document (Sections 1–15)  
> **Review Type:** Expert Panel — Final Iterations (9 & 10 of 10)  
> **Previous Iterations:** [Iteration 1-2](iteration-1-2.md) (Hedge Fund PM + Supply Chain VP), [Iteration 3-4](iteration-3-4.md) (Graph DB Architect + NLP Scientist), [Iteration 5-6](iteration-5-6.md) (Enterprise PM/GTM + CISO/Compliance), [Iteration 7-8](iteration-7-8.md) (Pipeline Architect + Financial UX Designer)

---

## Cumulative Findings Entering This Iteration

| Expert | Score | Critical Gaps |
|--------|-------|---------------|
| Marcus Chen (Hedge Fund PM) | 7/10 | No portfolio overlay, backtesting must be P0, SOM 10–50x overstated |
| Dr. Priya Sharma (Supply Chain VP) | 6/10 | No BOM-level granularity, no disruption duration, cross-domain data isolation |
| Dr. Kai Müller (Graph DB Architect) | 5/10 | Neo4j CE can't deliver 5+ requirements, temporal versioning unspecified, Decimal impossible, edge embeddings unsupported, no consistency model |
| Dr. Aisha Ibrahim (NLP Scientist) | 4/10 | Tail entity NER at 60–75% F1, RE at 65–75% F1, 4-hop ~24% all-correct, LLM hallucination 8–15%, 13-language NER multi-year, NLP costs ~$10K/month unbudgeted, no evaluation loop |
| Megan Torres (Enterprise PM / GTM) | 3/10 | No beachhead vertical, no GTM strategy, no MVP defined, no pricing validation, dual-vertical kills focus |
| James Wright (CISO / Compliance) | 4/10 | SOC 2 missing, SSO/SAML missing, investment adviser classification unresolved, LLM data leakage, GDPR non-compliance, no IR/DR plan |
| Ethan Kowalski (Pipeline Architect) | 4/10 | No pipeline topology, at-most-once delivery, no DLQ, no observability, Claude API bottleneck unaddressed, no backpressure, no article storage |
| Yuki Tanaka (Financial UX Designer) | 4/10 | No information hierarchy, D3/vis.js can't handle 5K nodes, no user workflows, real-time graph updates cause visual vertigo, no keyboard nav |
| **Cumulative** | **Avg: 4.6/10** | **145 new requirements identified, 80 at P0** |

---

## Panel Members — This Iteration

| # | Expert | Role | Perspective |
|---|--------|------|-------------|
| 9 | **Sophia Nakamura** | Competitive Intelligence & Product Strategy, 16 years (Bloomberg product lead → AlphaSense VP Product → independent strategy advisor to 12 fintech startups) | Competitive moats, data defensibility, pricing strategy, distribution, replication risk |
| 10 | **Rajesh Krishnamurthy** | Platform Engineer, 18 years (AWS principal engineer → Stripe infrastructure architect → CTO of a B2B SaaS platform serving 200+ enterprise clients) | Multi-tenancy, infrastructure costs, SaaS vs on-prem, API design, disaster recovery, CI/CD, client integration |

---
---

# EXPERT 9: Sophia Nakamura — Competitive Intelligence & Product Strategy

*Background: 7 years at Bloomberg (2012–2019), starting as a product analyst and rising to Product Lead for Bloomberg's Supply Chain Intelligence initiative — the internal R&D effort that evaluated whether Bloomberg should build exactly what MKG describes. She knows, from the inside, why Bloomberg chose not to build it (and under what conditions they would). 3 years as VP Product at AlphaSense ($500M ARR), where she led the competitive intelligence product line and observed firsthand how enterprises evaluate, purchase, and churn from financial data products. Last 4 years as an independent strategy advisor to 12 fintech startups — 4 of which achieved product-market fit, 3 acqui-hired, 5 failed. She has seen the exact failure mode MKG is approaching from the inside of both incumbents and startups.*

---

## A. Concept-Requirement Alignment — Score: 3/10

**What aligns well:**

- The Speed 3 framework is genuinely novel positioning. At Bloomberg, we evaluated the same market gap in 2017 under the internal project name "Cascade." The conclusion was that the gap existed but was too small for Bloomberg to pursue because: (a) the addressable market was niche, (b) the data acquisition cost was high, and (c) the margin structure didn't fit Bloomberg's $24K/seat model. MKG's positioning into this abandoned quadrant is strategically sound *if the market is large enough to sustain an independent company.*

- The 20 "zero commercial competitor" capabilities (Section 10) are mostly accurate as of early 2026. Nr. 1 (dynamic relationship weights), Nr. 2 (multi-hop propagation), and Nr. 3 (causal chain explainability) combined form a genuinely differentiated capability bundle. I evaluated all 9 competitors listed in Section 3.2 during my AlphaSense tenure, and none of them do these three things together.

- The semiconductor beachhead is correct. At Bloomberg, "Cascade" also started with semiconductors because the supply chain is: (a) well-documented in public filings, (b) concentrated enough to be tractable (100 critical companies), (c) subject to frequent disruptions that create urgency, and (d) connected to some of the world's largest companies by market cap (Apple, NVIDIA, TSMC). Every advisory client I've worked with in this space also picked semiconductors first.

**Why this is 3/10 — the document fundamentally misunderstands competitive dynamics:**

1. **Bloomberg didn't build "Cascade" — but they haven't decided never to build it.** The internal project was shelved, not killed. The data science team is still prototyping a supply chain graph on top of Bloomberg's existing entity universe (300,000+ companies already mapped). If MKG gains traction and validates the market at even $5M ARR, Bloomberg can build a competing product in 6–12 months using their existing data infrastructure, distribution (325,000 terminal subscribers), and brand trust. The document's competitive analysis treats Bloomberg as if it's frozen. It is not.

2. **AlphaSense's "AI Search" is one product pivot away from graph intelligence.** AlphaSense already ingests the exact same sources MKG plans to use (SEC filings, earnings transcripts, news, broker reports — 200M+ documents). They already run NER for company detection. They already have 4,000+ enterprise clients and embedded procurement relationships. If AlphaSense decides to add relationship extraction and graph traversal — which their product roadmap discussed in Q3 2025 — they ship a competing feature to their existing user base within one product cycle. They don't need to acquire customers; they already have them.

3. **The document has no concept of a competitive moat.** It describes what MKG does (capabilities) but not what prevents competitors from doing the same thing (defensibility). In my framework, there are only 5 real moats for data products:

| Moat Type | Description | MKG Status |
|-----------|-------------|------------|
| **Proprietary data** | Data that nobody else has | ❌ All data sources are public (SEC, news, transcripts) — any competitor can ingest the same articles |
| **Network effects** | Product gets better as more users use it | ❌ No social features, no user-contributed data, no marketplace — each client installation is independent |
| **Switching costs** | Painful to leave once adopted | ⚠️ Marginally — tribal knowledge entries create lock-in, but a client can export and re-import |
| **Scale economies** | Marginal cost drops with more clients | ⚠️ NLP pipeline cost is per-article regardless of client count. Graph is shared (marginal cost per new client ≈ $0 for read access) |
| **Brand / trust** | Reputation that takes years to build | ❌ New entrant, zero brand recognition, financial clients are risk-averse |

**MKG currently has no durable moat.** The technology is replicable (Claude API + Neo4j is available to everyone), the data is public, and the user base starts at zero. The only potential moats are: (a) tribal knowledge data contributed by paying clients (if structured as a network), and (b) historical accuracy track record built over 12+ months of operation. Neither exists at launch.

4. **The pricing strategy is untested and potentially suicidal.** Section 7 lists willingness-to-pay ranges ($20K–$300K/yr) but these are aspirational, not validated. At AlphaSense, initial pricing was set at $15K/seat, then revised to $30K after discovery calls revealed that below $20K, institutional buyers don't take you seriously (an enterprise software purchase under $20K often goes through a different, slower procurement channel — ironically, cheap software is harder to sell in finance). At Bloomberg, $24K/year is an anchor price that every financial buyer carries in their head. MKG's pricing must be positioned relative to Bloomberg, not in a vacuum.

5. **The distribution strategy is nonexistent.** The document describes the product in 15 sections and 600+ lines but never answers: How does the first customer learn that MKG exists? How do they evaluate it? How long does the trial period last? Who deploys it? Who renews? At AlphaSense, customer acquisition cost (CAC) for enterprise financial clients averaged $45K–$60K. At Bloomberg, it's lower because of brand, but Bloomberg spends $200M+/year on sales and marketing. MKG's budget doesn't appear to include any go-to-market spending.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Competitive Moat — EXISTENTIAL GAP

The document doesn't address defensibility at all. Every capability described (dynamic weights, propagation, causal chains) is a software feature, not a moat. Any well-funded team (or any incumbent) can build the same features.

**The only paths to a moat for MKG:**

**Path A — Proprietary Data Moat (Tribal Knowledge Network)**

If every client who uses MKG contributes tribal knowledge back to a shared layer (anonymized, aggregated), the graph becomes more valuable with each new client. This creates a network effect: the 100th client gets a graph that's 100x richer than what a new competitor can offer. This is how LinkedIn's Economic Graph works — every user who updates their profile makes the data more valuable for all users.

But R-SC4 says "isolated graph views per subscription tier" and R-TK1–R-TK6 describe tribal knowledge as client-specific. If tribal knowledge is client-private, there is no network effect. The document must decide: is tribal knowledge shared (creating a moat) or isolated (protecting client secrets but preventing a moat)?

**Path B — Accuracy Track Record Moat**

After 12 months of operation, MKG will have a calibration record: "For events with confidence >80%, our propagation predictions matched actual market movements 73% of the time." This track record is valuable and unreplicable by a new entrant — they'd need 12 months of their own to build it. At Bloomberg, historical back-tested accuracy is the #1 factor in client retention for analytics products.

But R-EXP5 lists this as P1, and there's no specification for how accuracy is measured, reported, or marketed. The track record needs to be a *product feature* (visible in the dashboard, in the sales deck, in every alert) — not a back-office metric.

**Path C — Integration Moat (Client Workflow Embedding)**

If MKG integrates deeply into client workflows (Excel/Google Sheets plugins, Bloomberg Terminal add-on, Slack/Teams bot, portfolio management system connectors), switching becomes painful. The product becomes the "plumbing" rather than an optional dashboard. At AlphaSense, our highest-retention clients (98%+) were those who had AlphaSense integrated into their CRM or research management system — not the ones using the web dashboard.

The document mentions REST API (R-OUT1) and WebSocket (R-OUT2) but has no requirements for integration connectors.

> **R-COMP-1** (P0): System must document its competitive moat strategy. Choose at least one from: (a) shared tribal knowledge network (requires redesigning R-SC4 isolation model), (b) accuracy track record (requires promoting R-EXP5 to P0 with specific measurement methodology), (c) workflow integration (requires integration connector requirements). The chosen moat strategy must be reflected in the product roadmap, pricing model, and sales narrative.

> **R-COMP-2** (P1): System must implement a "community knowledge layer" — aggregated, anonymized relationship data that is shared across all clients. Individual client tribal knowledge remains private, but the community layer (derived from public signals) creates a network effect. New clients get instant value from the accumulated community graph. Contributing clients get better coverage. This is the data moat that prevents incumbents from replicating the product by building their own.

> **R-COMP-3** (P1): System must build accuracy track record as a first-class product feature, not a back-office metric. Every propagation event must be tracked to outcome (did the predicted market impact actually occur within the predicted timeframe?). Accuracy must be displayed: (a) in the dashboard (rolling 90-day hit rate), (b) in every alert ("historically, signals like this have been accurate 74% of the time"), (c) in a public-facing "track record page" for sales and marketing. Promote R-EXP5 to P0.

### B2. Data Defensibility — ALL DATA SOURCES ARE PUBLIC

Every data source in R-DS1 through R-DS8 is publicly available. SEC EDGAR is free. Earnings transcripts are available from multiple vendors. News APIs are commodity. This means the raw data input to MKG is available to every competitor at the same cost.

**What creates data defensibility is not the data itself, but:**

1. **Coverage completeness** — having extracted entities from 100% of relevant articles vs a competitor's 80% means you see supply chain relationships they miss. The first mover who builds 2+ years of historical extraction has a structural advantage.

2. **Extraction quality** — consistently correct NER/RE on financial entities (especially tail entities — obscure Tier 3 suppliers) creates a graph that's measurably better than a competitor's. But this requires the evaluation infrastructure that Dr. Ibrahim found missing (Iteration 4).

3. **Temporal depth** — historical graph state (R-KG5) becomes valuable only after years of accumulation. A competitor who starts in 2028 can never reconstruct "what did the TSMC supply chain look like in February 2024" unless they back-process 4 years of articles — which is expensive and produces lower-quality extraction than real-time processing.

> **R-COMP-4** (P0): System must begin accumulating historical extraction data from day 1 of operation, even during alpha/beta. Every article processed, every entity extracted, every edge created must be permanently stored with timestamps. This historical corpus is a depreciating competitive advantage — every day of delay in starting is a day of data that can never be recovered at the same quality.

> **R-COMP-5** (P1): System must implement "historical backfill" capability — the ability to process archived articles (e.g., SEC EDGAR filings from 2020–2025) through the extraction pipeline to bootstrap the temporal graph. The backfilled data should be marked with lower confidence than real-time extraction (backfill without contemporaneous context tends to miss contextual nuances).

### B3. Pricing Strategy — UNTESTED AND MISALIGNED

The pricing ranges in Section 7 ($20K–$300K/yr) span 15x. This range is so wide that it's not a pricing strategy — it's a guess. At AlphaSense, we spent 4 months validating pricing through 60 structured discovery calls before setting our launch price (and still got it wrong on the first try — dropped from $30K to $22K within 6 months).

**Enterprise financial product pricing principles:**

| Principle | Implication for MKG |
|-----------|-------------------|
| **Price anchoring** | Buyers will compare to Bloomberg ($24K/seat) and AlphaSense ($30K–$100K). MKG must position explicitly: "We're $X because we do Y that Bloomberg doesn't." |
| **Value metric** | What unit does the client pay for? Per seat? Per entity monitored? Per propagation alert? Per API call? The document doesn't specify. The value metric determines whether MKG scales as a $50K product or a $500K product. |
| **Land-and-expand** | Starting price must be low enough to get in the door (typically <$50K for first-year contracts with hedge funds), with clear expansion triggers (more seats, more entities, more features). |
| **Pilot pricing** | The first 5 clients should pay 50–70% of list price in exchange for feedback and case study rights. This is standard enterprise SaaS. |
| **Annual commitment** | Monthly pricing is a mistake for enterprise financial products. Annual contracts with quarterly reviews is the norm. Monthly suggests instability. |
| **Tier structure** | Free tier is standard for developer adoption but wrong for enterprise financial products. No hedge fund PM uses a free-tier tool for trading decisions. The tiers should be: Starter ($30K–$50K/yr, 1 vertical, 500 entities), Professional ($80K–$150K/yr, full graph, what-if, API), Enterprise ($200K+/yr, dedicated instance, SLA, SSO, custom integrations). |

> **R-COMP-6** (P0): System must define a pricing model with: (a) value metric (per-seat vs per-entity vs hybrid), (b) tier structure (minimum 3 tiers with explicit feature gates), (c) pilot pricing for first 5 clients (50–70% of list), (d) annual commitment as default (no monthly), (e) expansion triggers per tier. Pricing must be validated through 20+ discovery interviews before launch.

> **R-COMP-7** (P1): System must implement usage metering that supports future pricing changes. Track per-client: API calls/day, entities monitored, propagation events triggered, what-if scenarios run, users logged in, data export volume. Even if v1 charges flat per-seat, usage data enables future value-based pricing.

### B4. Distribution & Go-To-Market — ZERO STRATEGY

The document is 100% product specification and 0% distribution strategy. For enterprise B2B, distribution is harder than product. 

**The MKG go-to-market reality:**

| Phase | Duration | Activity | Cost |
|-------|----------|----------|------|
| Discovery | Months 1–3 | 50 outreach calls, 20 discovery conversations, identify 5 design partners | $0 (founder-led) |
| Design Partnership | Months 3–6 | 5 clients using free beta, providing feedback, validating use cases | $0 revenue, $50K engineering cost |
| First Revenue | Months 6–9 | 2–3 design partners convert to annual contracts at pilot pricing | $60K–$150K ARR |
| Proof Point | Months 9–15 | Client case study, accuracy track record, conference presentation | +$100K–$200K ARR |
| Hiring Sales | Months 12–18 | First AE hired ($120K base + commission), outbound + inbound established | +$200K–$400K ARR |
| Scale | Months 18–24 | 2–3 AEs, marketing budget, analyst briefings (Gartner, Celent) | $500K–$1M ARR |

**The total cost to reach $500K ARR (from Section 15's target): 18–24 months and $400K–$700K in sales + marketing spend, on top of engineering costs.**

The document's Year 1 revenue target of $500K ARR (Section 15) is achievable *only if* the product is in market by Month 6 and sales starts by Month 9. Given the 24-week (6-month) build timeline produces only a demo (per Megan Torres, Iteration 5), the revenue timeline is: start building Month 0, demo at Month 6, sellable product at Month 12, first revenue at Month 15, $500K ARR at Month 24–30.

> **R-COMP-8** (P0): System must include a distribution plan with: (a) target account list (20 specific firms with named contacts if possible), (b) outreach strategy (conference circuit: SALT, Milken Institute, Alpha Conference — event-driven funds concentrate there), (c) design partner criteria (not just "willing to use it" but "has the exact Speed 3 pain, will provide structured feedback, would pay $30K+ for a solution"), (d) first-year revenue forecast by quarter (not by year), (e) sales tool requirements (demo environment, trial provisioning, ROI calculator).

> **R-COMP-9** (P1): System must implement a self-serve demo environment — a pre-loaded graph with the semiconductor beachhead (500 entities), a curated set of historical events (TSMC February 2024 earthquake, NVIDIA export controls, ASML restrictions), and a "replay" mode that shows how MKG would have detected and propagated those events. This is the sales tool. Every client conversation must begin with this demo, not a slide deck.

### B5. Replication Risk by Incumbents — THE BLOOMBERG/ALPHASENSE THREAT

**Bloomberg scenario (60% likelihood within 3 years if MKG validates market):**

Bloomberg's advantages: 300K+ entities already in their BPIPE data universe. 325,000 terminal subscribers (built-in distribution). $12B/yr revenue to fund R&D. NLP team of 40+ (Bloomberg's DeepSearch product already does entity extraction on financial documents). Internal "Cascade" prototype already built for semiconductor supply chain.

Bloomberg's disadvantages: Channel conflict (graph intelligence might cannibalize terminal revenue if clients realize they can get supply chain insight without $24K/seat Bloomberg access). Organizational inertia (Bloomberg ships slowly — 18–24 months for new features). Not graph-native (Bloomberg's data model is entity-centric, not graph-centric — building a propagation engine would require new architecture).

**AlphaSense scenario (40% likelihood within 2 years):**

AlphaSense's advantages: Already processes the same documents. Already has NER for company names. 4,000+ enterprise clients. Raised $900M+ at $4B valuation — has capital. Strong engineering team.

AlphaSense's disadvantages: Search-centric product DNA — "graph" is architecturally foreign. Would need to build or acquire graph capability. Cultural preference for AI search, not structured data products.

**Defense strategies:**

| Strategy | Effectiveness | MKG Feasibility |
|----------|--------------|-----------------|
| Move faster (ship first, iterate fast) | MEDIUM — speed advantage lasts 12–18 months | ✅ Possible as a startup |
| Go deeper on semiconductor vertical (1,000+ Tier 3/4 entities that Bloomberg doesn't track) | HIGH — tail entity coverage is expensive for incumbents to replicate | ✅ Possible with focused NER effort |
| Build tribal knowledge network (client-contributed data) | VERY HIGH — network effects are the only durable moat | ⚠️ Requires solving the data isolation vs sharing tension |
| Patent the propagation algorithm | LOW — financial algorithms are hard to patent, software patents are increasingly invalidated | ❌ Not recommended |
| Secure exclusive data partnerships (e.g., trade data providers, satellite imagery) | HIGH — exclusive access creates proprietary input | ⚠️ Expensive and hard to negotiate as a startup |

> **R-COMP-10** (P0): System must assume incumbent replication within 24–36 months and plan accordingly. The product strategy must answer: "When Bloomberg/AlphaSense ships a competing feature, what do MKG's clients have that makes them stay?" The answer must be one or more of: (a) 2+ years of accumulated data and accuracy track record, (b) tribal knowledge network effects, (c) integration embedding that makes switching painful, (d) deeper vertical coverage than incumbents will invest in.

> **R-COMP-11** (P1): System must target "tail entity coverage" as a differentiation axis — the 500+ Tier 3/4 semiconductor companies (specialty chemical suppliers, packaging substrate manufacturers, photomask shops, wafer handling equipment makers) that Bloomberg, AlphaSense, and FactSet don't track. These entities are where MKG's graph provides insight that no other product can. Maintain a "coverage depth" metric: percentage of real-world semiconductor supply chain entities present in MKG's graph.

### B6. Switching Cost Architecture — CLIENTS MUST NOT BE ABLE TO LEAVE EASILY

This sounds aggressive, but it's standard enterprise SaaS architecture. Every successful B2B product makes itself indispensable through workflow integration, not contract terms.

**Current MKG switching costs: near zero.** A client using MKG's dashboard and API can stop paying and lose access. Their tribal knowledge entries are trapped, but the core graph intelligence is available from alternative sources (or Bloomberg builds it).

**Target switching costs:**

1. **Tribal knowledge library** — after 6 months of a client's analysts adding tribal knowledge entries (executive relationships, unofficial alliances, cultural risk factors), that knowledge base represents 100+ hours of expert time. Leaving MKG means losing (or manually re-creating) this library.

2. **Custom alert rules** — analysts who've configured 50+ alert rules (entity X changes by >5%, sector Y has new entrant, etc.) won't rebuild these on a competitor.

3. **Historical accuracy context** — "MKG has 14 months of accuracy data for my portfolio concentration risk scores. A new product starts at zero."

4. **API integration** — if the client's internal systems (portfolio management, risk reporting, compliance logging) call MKG's API, switching requires engineering work.

> **R-COMP-12** (P1): System must implement tribal knowledge export in a non-standard format (proprietary JSON schema, not CSV). While data export must be available (R-KG13), the export format should require non-trivial transformation to import into a competing product. This is standard practice — Bloomberg, AlphaSense, and FactSet all make data portable in principle but friction-laden in practice.

> **R-COMP-13** (P1): System must implement at least 3 integration connectors by Month 12: (a) Excel/Google Sheets plugin (impact table data in a spreadsheet — where analysts actually work), (b) Slack/Teams bot (propagation alerts in the collaboration tool), (c) REST API with client libraries in Python and JavaScript (for programmatic integration into quant workflows). Each integration creates switching cost.

---

## C. Requirement Challenges

### C1. The "Feature-Complete vs Moat-First" Tension

The document lists 150+ requirements across 15 sections. The expert panel has added 145 more. The resulting requirement set (~300 requirements) is architecturally comprehensive but strategically unfocused. Building features doesn't create a business; building moats does.

**The counterintuitive truth:** MKG should ship v1 with *fewer* features but *more* defensibility infrastructure. A product with 20 features and no moat loses to a competitor with 10 features and a data network effect.

| Feature-First Approach (Current) | Moat-First Approach (Recommended) |
|----------------------------------|-----------------------------------|
| Build propagation engine, graph viz, what-if, temporal versioning, 13 languages, WebSocket, alerts | Build propagation engine, tribal knowledge input, accuracy tracking, 3 integrations, alert API |
| Year 1: impressive demo, 0 defensibility | Year 1: narrower product, data accumulation started, 3 integrations creating switching cost |
| Year 2: clients notice Bloomberg building similar features | Year 2: clients have 12 months of tribal knowledge + accuracy track record + integrated workflows |
| Year 3: Bloomberg ships, MKG has no moat, clients consider switching | Year 3: Bloomberg ships, MKG clients stay because switching costs are high and data is unique |

> **R-COMP-14** (P0): Product roadmap must be restructured to prioritize moat-building features over capability features. Specifically: (a) tribal knowledge input and community knowledge layer in v1, not v2, (b) accuracy tracking from day 1 of production, (c) at least 1 integration connector in v1. Graph visualization, what-if simulation, and multilingual NER are P2 until a moat is established.

### C2. Bloomberg's Internal "Cascade" Project — Intelligence from the Inside

I have direct knowledge of Bloomberg's internal evaluation. Key factors that made Bloomberg *not* build this (as of 2019):

1. **Market size concern**: Bloomberg estimated the Speed 3 intelligence market at $200M–$400M TAM — too small for a company with $12B revenue to pursue as a product line.
2. **Data acquisition cost**: Building and maintaining 50,000+ entity relationships requires ongoing NLP infrastructure that Bloomberg estimated at $5M–$10M/year for a team of 15–20 engineers + data analysts. The ROI didn't pencil out.
3. **Channel risk**: Offering supply chain graph intelligence as a standalone product could attract clients who then realize they don't need the full Bloomberg Terminal — cannibalizing the $24K/seat cash cow.
4. **Quality assurance**: Bloomberg's brand depends on accuracy. A propagation engine that is 70% accurate (which is optimistic, per Dr. Ibrahim's analysis) would damage Bloomberg's reputation. They won't ship below 90% accuracy.

**What would make Bloomberg reconsider:**

- If MKG (or any competitor) reaches $10M+ ARR — validates the market is real
- If client demand for supply chain intelligence during a major geopolitical event (Taiwan crisis, real TSMC disruption) causes visible demand that Bloomberg's sales team can't fulfill with existing products
- If AlphaSense adds graph features first — Bloomberg would respond competitively

> **R-COMP-15** (P1): MKG must stay below Bloomberg's radar during the first 18 months (below $5M ARR). The go-to-market strategy should avoid: (a) public PR that names Bloomberg as a competitor, (b) direct comparison marketing, (c) selling to Bloomberg's top 50 accounts before MKG's accuracy track record is established. Instead, target mid-tier event-driven funds ($500M–$5B AUM) that are Bloomberg-dependent but underserved by Bloomberg's analytics.

---

## D. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Bloomberg builds a competing feature ("Cascade" revival) within 24–36 months of MKG market validation | HIGH (60%) | FATAL — Bloomberg has distribution, brand, data | R-COMP-10: build moat (accuracy track record + tribal knowledge network + integrations) before Bloomberg notices |
| 2 | AlphaSense adds graph intelligence to existing product within 18 months | MEDIUM (40%) | HIGH — AlphaSense has the clients already | R-COMP-11: go deeper on tail entities that AlphaSense doesn't track |
| 3 | MKG has no moat: any funded startup can replicate capabilities in 12 months | HIGH | HIGH — race to zero | R-COMP-1: choose and implement moat strategy before launch |
| 4 | Pricing set wrong — too low to signal quality, too high for unproven product | HIGH | MEDIUM — revenue stunted | R-COMP-6: validate through 20+ discovery calls before launch |
| 5 | No distribution strategy — product built but nobody knows it exists | HIGH | FATAL | R-COMP-8: distribution plan with named accounts and conference strategy |
| 6 | First-mover advantage decays faster than moat builds — competitors ship before MKG has switching costs | MEDIUM | HIGH | R-COMP-14: moat-first roadmap, not feature-first |
| 7 | Tribal knowledge data remains client-private (per R-SC4), preventing network effects, leaving MKG with zero data moat | HIGH | HIGH — no defensibility | R-COMP-2: community knowledge layer (aggregated, anonymized) |

---

## E. Five Critical Questions

1. **If Bloomberg announced tomorrow that they're building supply chain graph intelligence as a Terminal feature, would MKG still have a viable business?** If the answer is "no," then MKG's strategy depends on Bloomberg choosing not to compete — which is a hope, not a plan. The answer needs to be "yes, because…" followed by a specific defensibility claim.

2. **What is MKG's value metric?** "We charge per seat" means you cap revenue at (seats × price). "We charge per entity monitored" means you grow with the client's universe. "We charge per propagation alert" means you grow with market volatility (which is when you're most valuable). The value metric determines whether this is a $50K product or a $500K product per client. This must be decided before the first sales conversation.

3. **Is tribal knowledge shared or private?** This is the single most important strategic decision for MKG's long-term viability. Shared creates a network effect moat. Private protects client trust. You cannot have both. The resolution might be: raw tribal knowledge entries are private; aggregated statistical patterns derived from tribal knowledge are shared (e.g., "87% of experts in our network rate the TSMC→Apple dependency as critical" without revealing which specific expert said what).

4. **What is the MKG sales cycle end-to-end?** From "PM hears about MKG" to "signed annual contract." Hedge fund procurement is faster than corporate but still requires: (a) discovery demo, (b) trial period (30–60 days), (c) compliance/security review, (d) legal contract negotiation. Total: 3–6 months. Does MKG's runway accommodate 3–6 months of zero revenue after the product ships?

5. **If MKG's propagation accuracy is 65% (Section 15 target), is that sufficient to charge $30K–$50K/year?** At Bloomberg, analytics products with <80% accuracy get terminated. At AlphaSense, search relevance below 85% triggers escalation. A 65% hit rate means 1 in 3 propagation predictions is wrong. Is this a "valuable signal with known limitations" or a "product that's wrong too often to trust"? The answer depends entirely on how confidence is communicated and whether false positives are more costly than false negatives for the target buyer.

---
---

# EXPERT 10: Rajesh Krishnamurthy — Platform Engineer

*Background: 7 years at AWS (2010–2017) as a Principal Engineer on the DynamoDB team, where he designed the multi-tenant partition management system that serves 100,000+ tables across AWS accounts with strict isolation guarantees. 5 years at Stripe (2017–2022) as infrastructure architect for the payments platform — designed the disaster recovery system, the multi-region failover architecture, and the API versioning strategy that supports 10,000+ API integrations without breaking changes. Last 4 years as CTO of a B2B SaaS platform serving 200+ enterprise clients across financial services and healthcare — built the entire platform from zero to SOC 2 Type II certified, handling $2B+ in annual transaction volume. He knows exactly what it takes to build a production SaaS platform that enterprise clients trust with their data.*

---

## A. Concept-Requirement Alignment — Score: 3/10

**What aligns well:**

- The dual-database architecture (Neo4j for graph + PostgreSQL for relational, Section 12.2) is architecturally sound. At Stripe, we ran a similar pattern — DynamoDB for payments data + PostgreSQL for account metadata. Having the right database for the right workload avoids the "one database to rule them all" anti-pattern that I've seen kill 3 startups' performance. The key is getting the boundary right: Neo4j owns entities, edges, and graph queries. PostgreSQL owns users, audit logs, subscriptions, and time-series metrics. The document draws this boundary correctly.

- Using FastAPI (Section 12.1) is a defensible choice for the API layer. At my current company, we started with Flask and migrated to FastAPI at client #50 because async support and automatic OpenAPI documentation became non-negotiable for enterprise integrations. Starting with FastAPI avoids that migration.

- The Celery + Redis choice is appropriate for the prototype phase (per Ethan Kowalski's agreement in Iteration 7). My additional perspective: at AWS, we built queue-based processing systems that started simple and scaled to planetary scale. The key was *abstraction* — the processing stages didn't know or care about the queue technology underneath. If MKG follows R-PIPE-19's recommendation (PipelineStage interface), the Celery→Kafka migration path is viable.

**Why this is 3/10 — the platform is not enterprise-ready:**

1. **There is no multi-tenancy architecture.** R-SC4 says "multi-tenant: isolated graph views per subscription tier" in one line. At AWS, multi-tenancy was the single hardest engineering challenge in DynamoDB — harder than consistency, harder than scaling, harder than operations. It took 40 engineers 2 years to get right. A single line in a requirements document does not constitute a multi-tenancy design.

   Multi-tenancy for MKG means answering: Does each client get their own Neo4j instance? Their own database within a shared instance? A shared graph with filtered views? Each answer has dramatically different cost, security, and operational implications.

2. **The infrastructure cost model is absent.** The document describes what to build but never models what it costs to run. At Stripe, every architecture decision included a "cost per transaction" analysis. At AWS, "blast radius" (cost impact of a single tenant's usage spike) is evaluated for every feature. MKG's document has no cost model for:
   - Neo4j hosting (RAM-intensive — 50K nodes + 500K edges with vector indexes requires 16GB+ RAM minimum)
   - Claude API (estimated at $9K–$10K/month by Iteration 7)
   - PostgreSQL with TimescaleDB
   - Redis
   - Celery workers
   - Frontend (Next.js) hosting
   - Monitoring (Sentry, Prometheus, Grafana)
   - Total monthly infrastructure run rate

3. **The API design is underspecified for enterprise integration.** R-OUT1 says "REST API returning ranked impact lists in standard JSON format." But enterprise API design requires: versioning strategy, pagination, rate limiting per client, webhook delivery, idempotency keys, error response format, deprecation policy, SDK generation, and API documentation. At Stripe, our API design guidelines document is 47 pages. MKG's is one line.

4. **There is no disaster recovery or business continuity plan.** James Wright (Iteration 6) flagged this (R-SEC-35, R-SEC-36), but the gap is deeper than he described. For a system that claims to deliver intelligence "before anyone else connects the dots," what happens when:
   - The Neo4j instance crashes and the last backup was 6 hours ago?
   - The Claude API has a 4-hour outage during a major geopolitical event?
   - A database migration corrupts 10% of edge weights?
   - A deployment introduces a bug that causes incorrect propagation results for 2 hours before detection?
   
   Each scenario requires a documented recovery procedure, an RTO (recovery time objective), and an RPO (recovery point objective). None exist.

5. **CI/CD is not specified.** For a platform that processes financial intelligence 24/7, deployment must be zero-downtime, automated, tested, and auditable. The document's deployment section (Section 12.1) mentions "Docker Compose (dev), Railway (prod)" — but doesn't specify: How are deployments triggered? What tests must pass before deployment? How do you roll back a bad deployment? How do you deploy to production without interrupting in-flight propagation calculations? At Stripe, we had a 23-step deployment pipeline with automated canary analysis. MKG has zero.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Multi-Tenancy Architecture — THE HARDEST ENGINEERING PROBLEM

The document mentions "multi-tenant" once (R-SC4) and "isolated graph views" once. This is the platform decision that determines MKG's entire cost structure, security model, and scaling trajectory.

**Four multi-tenancy models, ranked by isolation:**

| Model | Isolation Level | Cost per Client | Complexity | Data Leak Risk |
|-------|----------------|----------------|------------|----------------|
| **A. Dedicated instance** | Complete (separate Neo4j, PG, Redis per client) | HIGH ($500–$2K/month per client) | LOW | ZERO |
| **B. Shared instance, separate databases** | Strong (separate Neo4j databases, shared PG with row-level security) | MEDIUM ($100–$300/month per client) | MEDIUM | LOW |
| **C. Shared database, logical isolation** | Application-level (shared tables with `tenant_id` column, every query includes `WHERE tenant_id = X`) | LOW ($20–$50/month per client) | HIGH (one missing WHERE = data leak) | MEDIUM |
| **D. Shared graph, filtered views** | Minimal (shared graph, clients see different subsets based on role) | VERY LOW ($5–$20/month per client) | HIGHEST | HIGH |

At AWS, DynamoDB uses Model C at planetary scale — but with 40 engineers maintaining the isolation layer and automated testing that catches missing tenant filters. At Stripe, payments are Model A for PCI compliance reasons (dedicated infrastructure per jurisdiction).

For MKG:
- **Financial clients will require Model A or B.** Hedge fund compliance teams will not accept shared-database isolation. The risk of one fund's tribal knowledge leaking to a competitor is career-ending for the compliance officer. James Wright (Iteration 6) confirmed this.
- **Model C is acceptable for the shared knowledge graph** (public company data is not tenant-specific). Only tribal knowledge and client-specific alert configurations need tenant isolation.
- **The hybrid answer is:** Shared Neo4j graph (Model D) for public entity/relationship data + dedicated tenant storage (Model A or B) for tribal knowledge, portfolio data, alerts, and usage data.

> **R-PLAT-1** (P0): System must implement a hybrid multi-tenancy model: (a) shared read-only graph for public entity data (companies, products, facilities, regulations, and publicly-derived relationships), (b) tenant-isolated storage for: tribal knowledge entries, alert configurations, portfolio positions, usage logs, and API keys. Tenant isolation must be provable — an automated test suite must verify that no API endpoint can return data from tenant A when authenticated as tenant B. At minimum, 100 isolation boundary tests.

> **R-PLAT-2** (P0): System must define cost-per-tenant for each multi-tenancy tier. At current infrastructure prices (March 2026): dedicated Neo4j instance (16GB RAM, 4 vCPU) ≈ $300–$500/month. Shared PostgreSQL row-level security ≈ $20–$50/month incremental. Dedicated Redis namespace ≈ $10–$30/month. Total infrastructure cost per client must be documented and compared against expected contract value. If cost-per-client exceeds 30% of contract value, the pricing model is unsustainable.

### B2. Infrastructure Cost Model — CRITICAL FOR BUSINESS VIABILITY

The document has no cost model. Here is my estimate based on the stated architecture:

**Minimum production infrastructure (10 clients, 10K articles/day):**

| Service | Specification | Monthly Cost |
|---------|--------------|--------------|
| Neo4j (shared graph) | 32GB RAM, 8 vCPU, 500GB SSD | $400–$800 (Railway/AWS) |
| PostgreSQL + TimescaleDB | 16GB RAM, 4 vCPU, 200GB SSD | $200–$400 |
| Redis | 4GB RAM, 2 vCPU | $50–$100 |
| FastAPI backend (2 replicas) | 4GB RAM each, 2 vCPU each | $100–$200 |
| Celery workers (3 workers) | 4GB RAM each, 2 vCPU each | $150–$300 |
| Next.js frontend | 2GB RAM, 1 vCPU | $30–$50 |
| Claude API | 10K articles/day, batched | $9,000–$10,000 |
| Monitoring (Sentry, Prometheus, Grafana) | Basic tiers | $100–$200 |
| Object storage (article archive) | 50GB/month growth | $10–$20 |
| **Subtotal (infrastructure)** | | **$10,040–$12,070/month** |
| **Subtotal (annualized)** | | **$120K–$145K/year** |

**Add operational costs:**

| Category | Monthly Cost |
|----------|-------------|
| SSL certificates / DNS | $10–$20 |
| Backup storage | $20–$50 |
| CI/CD (GitHub Actions / Railway) | $50–$100 |
| Error tracking (Sentry pro) | $26–$80 |
| Log aggregation | $50–$100 |
| **Subtotal (ops)** | **$156–$350/month** |
| **Subtotal (annualized)** | **$1.9K–$4.2K/year** |

**Total infrastructure + ops: $122K–$149K/year**

**The dominant cost is Claude API at $108K–$120K/year.** This single line item is 75–80% of total infrastructure cost. Dr. Ibrahim (Iteration 4) and Ethan Kowalski (Iteration 7) both flagged this. The cost optimization strategy for Claude API is not optional — it's the most important infrastructure decision in the entire platform.

> **R-PLAT-3** (P0): System must include a complete infrastructure cost model with: (a) per-service monthly cost at current scale (10K articles/day, 10 clients), (b) per-service cost at target scale (100K articles/day, 100 clients), (c) cost-per-client metric (infrastructure cost ÷ number of clients), (d) Claude API cost as percentage of total — with target to reduce below 50% via tiered extraction (R-PIPE-20). The cost model must be reviewed monthly and updated when pricing or scaling changes.

> **R-PLAT-4** (P1): System must implement Claude API cost optimization: (a) response caching — identical or near-identical articles (>90% cosine similarity of embeddings) should return cached extraction results, not re-invoke Claude, (b) model cascading — use a cheaper/faster model (Claude Haiku or local Mistral) for initial entity detection, then Claude Sonnet only for relationship extraction on articles where entities are detected, (c) batch scheduling — process non-urgent articles in off-peak batches (overnight) to smooth API load.

### B3. API Design for Enterprise Integration — VASTLY UNDERSPECIFIED

R-OUT1 says "REST API." At Stripe, our API was the product — more clients interacted via API than via dashboard. For MKG targeting hedge funds with quantitative teams, the API must be designed as a first-class product surface.

**Missing API design requirements:**

| Aspect | Current Spec | Enterprise Requirement |
|--------|-------------|----------------------|
| **Versioning** | Not mentioned | Must support multiple live API versions. Breaking changes must never break existing integrations. Strategy: URL-based versioning (`/v1/`, `/v2/`) with 12-month deprecation windows. |
| **Pagination** | Not mentioned | All list endpoints must support cursor-based pagination (`next_cursor`, `limit`). Offset-based pagination is unacceptable at scale (O(n) page skipping). |
| **Rate limiting** | R-SEC6 ("per user/tier") | Per-client rate limits with clear headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`). Burst allowance (150% of sustained limit for 30 seconds). Different limits per tier and per endpoint. |
| **Webhooks** | Not mentioned | Clients must be able to register webhook URLs for propagation events, weight changes, and alert triggers. Webhook delivery must include: HMAC signature verification, retry with exponential backoff (5 retries over 24 hours), delivery logs, and manual re-delivery via API. |
| **Idempotency** | Not mentioned | All POST/PUT endpoints must accept an `Idempotency-Key` header. Re-submitting the same request with the same key returns the original response without re-processing. Essential for reliability in distributed systems. |
| **Error format** | Not mentioned | Standard error response: `{ "error": { "type": "invalid_request", "code": "entity_not_found", "message": "...", "param": "entity_id", "doc_url": "https://docs.mkg.ai/errors/entity_not_found" } }`. Machine-parseable error codes, not just HTTP status codes. |
| **SDK generation** | Not mentioned | Auto-generated SDKs in Python and JavaScript from OpenAPI spec (FastAPI generates this automatically). Published to PyPI and npm. |
| **API documentation** | Not mentioned | Interactive API documentation (Swagger/Redoc + custom docs site). Every endpoint with examples, error cases, and rate limit information. |
| **Expansion** | Not mentioned | Support `?expand=causal_chain,evidence` parameter to include related objects in a single request, reducing round-trips. At Stripe, expansion reduced API call volume by 40%. |

> **R-PLAT-5** (P0): API must implement versioning (URL-based, e.g., `/v1/propagation`), cursor-based pagination on all list endpoints, standardized error response format with machine-parseable error codes, and `Idempotency-Key` support on all mutation endpoints. API versioning policy: new versions every 6–12 months, old versions supported for 12 months after deprecation announcement, never break existing integrations.

> **R-PLAT-6** (P0): API must implement webhook delivery for propagation events. Clients register webhook URLs via API. Webhooks include: HMAC-SHA256 signature in header (for verification), event payload, event type, event timestamp, and idempotency key. Retry policy: 5 attempts with exponential backoff (1s, 10s, 60s, 300s, 3600s). Failed deliveries after 5 retries must be queryable via API and manually re-deliverable.

> **R-PLAT-7** (P1): System must auto-generate and publish client SDKs in Python and JavaScript from the OpenAPI specification. SDKs must include: typed models for all request/response objects, automatic retry with exponential backoff, rate limit handling (wait and retry on 429), and API key management. Publish to PyPI and npm. SDKs reduce integration effort from days to hours.

### B4. Disaster Recovery — NOT SPECIFIED, CRITICALLY NEEDED

For a 24/7 financial intelligence system, the question is not if disaster strikes, but when. At Stripe, we had 3 major incidents per year despite having a 15-person SRE team. MKG with a 1–2 person team will have *more* incidents with *less* capacity to respond.

**Recovery scenarios that must be planned:**

| Scenario | RTO Target | RPO Target | Recovery Procedure |
|----------|-----------|-----------|-------------------|
| Neo4j instance crashes (hardware failure) | <1 hour | <6 hours (last backup) | Restore from last backup + replay pipeline events from article store |
| PostgreSQL corruption | <30 min | <1 hour (WAL replay) | Point-in-time recovery from WAL archive |
| Claude API outage (1–4 hours) | N/A (graceful degradation) | N/A | Switch to fallback extraction (R-PIPE-7), queue articles for re-processing when API returns |
| Bad deployment corrupts edge weights | <2 hours | <1 hour (identify + revert) | Blue-green deployment with instant rollback; weight audit trail enables edge-level correction |
| Redis failure (cache + queue loss) | <15 min | <5 min (rebuild from persistent store) | Redis Sentinel for HA; queue messages durable in PostgreSQL if Redis fails |
| Data breach / unauthorized access | N/A | N/A | Incident response plan per R-SEC-35; client notification within 72 hours (GDPR requirement) |
| Railway platform outage | <4 hours | <1 hour | Multi-cloud readiness: Docker containers deployable on any cloud with environment variable configuration |

> **R-PLAT-8** (P0): System must define Recovery Time Objective (RTO) and Recovery Point Objective (RPO) for every persistent data store (Neo4j, PostgreSQL, Redis). Minimum: Neo4j RTO <4 hours, RPO <6 hours. PostgreSQL RTO <1 hour, RPO <1 hour. Redis RTO <15 minutes, RPO acceptable loss (cache only). Backup verification must run weekly (restore backup to test environment and validate data integrity).

> **R-PLAT-9** (P0): System must implement automated backup for all persistent data stores. Neo4j: daily full backup + hourly incremental (CE supports offline backup only — schedule during lowest-traffic window, or migrate to Enterprise/Aura for online backup). PostgreSQL: continuous WAL archiving with point-in-time recovery. Backups must be stored in a separate cloud region/account from production.

> **R-PLAT-10** (P1): System must implement "graceful degradation" for every external dependency failure. When Claude API is down: fallback extraction continues with reduced accuracy. When Neo4j is down: cached results served from Redis/PostgreSQL (read-only mode). When Redis is down: PostgreSQL-backed queue takes over (higher latency, no cache). The dashboard must show a "degradation status" indicator so users know which capabilities are operating at reduced quality.

### B5. CI/CD Pipeline — ZERO-DOWNTIME DEPLOYMENT FOR 24/7 SYSTEM

The document mentions Docker Compose for dev and Railway for prod. There is no CI/CD specification. For a financial intelligence system that operates 24/7, deployment without CI/CD is like surgery without sterilization — technically possible but professionally unacceptable.

**Minimum CI/CD pipeline:**

```
┌────────────┐   ┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌────────────┐
│ Git Push   │──►│ Lint + Type  │──►│ Unit Tests     │──►│ Integration  │──►│ Security   │
│ (PR)       │   │ Check        │   │ (backend +     │   │ Tests        │   │ Scan       │
│            │   │              │   │ frontend)      │   │ (pipeline,   │   │ (Snyk,     │
│            │   │              │   │                │   │ API)         │   │ Trivy)     │
└────────────┘   └──────────────┘   └────────────────┘   └──────────────┘   └────────────┘
                                                                                  │
                                     ┌──────────────┐   ┌────────────────┐        │
                                     │ Canary       │◄──│ Build + Push   │◄───────┘
                                     │ Deployment   │   │ Docker Images  │
                                     │ (5% traffic) │   │                │
                                     └──────┬───────┘   └────────────────┘
                                            │
                                     ┌──────▼───────┐   ┌────────────────┐
                                     │ Health Check │──►│ Full Rollout   │
                                     │ (5 min)      │   │ (100% traffic) │
                                     └──────────────┘   └────────────────┘
```

> **R-PLAT-11** (P0): System must implement a CI/CD pipeline with minimum stages: (a) lint + type check (Ruff/Black for Python, TypeScript strict for frontend), (b) unit tests (all backend + frontend tests must pass — existing gate from SignalFlow), (c) integration tests (pipeline end-to-end, API contract tests), (d) security scan (dependency vulnerability check + container image scan), (e) Docker image build + push. Pipeline must block deployment on any failure. Average pipeline duration target: <10 minutes.

> **R-PLAT-12** (P0): Deployments must be zero-downtime. Implementation: blue-green deployment with health check gate — new version is deployed alongside old version, traffic switches after new version passes health checks (HTTP 200 on `/health` + Neo4j connection test + Redis connection test). Rollback must be instant (switch traffic back to old version). In-flight Celery tasks must not be interrupted — worker draining must complete before old workers are terminated.

> **R-PLAT-13** (P1): System must maintain deployment audit log: who deployed, when, what commit, what tests passed, deployment duration, rollback events. Accessible via admin API. Required for SOC 2 compliance (R-SEC-8).

### B6. Client Integration Patterns — HOW DO CLIENTS ACTUALLY USE THIS?

The document assumes clients interact via dashboard (R-OUT3) and API (R-OUT1). In practice, enterprise financial clients integrate in 4 patterns, and MKG must support at least the first two from day 1:

**Pattern 1 — Dashboard Only (Analyst Persona)**
PM opens MKG dashboard, views propagation events, clicks through causal chains, sets alerts. This is the most visible but least sticky integration — if the dashboard is closed, MKG has zero presence in the workflow.

**Pattern 2 — API Integration (Quant Persona)**
Quant team pulls propagation data into their internal systems via REST API. They build custom screens, feed impact scores into risk models, trigger automated hedging. This is the stickiest integration — once API calls are embedded in production code, switching cost is high.

**Pattern 3 — Alert-Driven (Mobile PM Persona)**
PM receives Telegram/Slack/email alerts when propagation events match their watchlist. They may never open the dashboard — the value is delivered entirely through push notifications. This requires excellent alert relevance (no false positives or the PM turns off alerts within a week).

**Pattern 4 — Data Feed (Enterprise Persona)**
Large client wants MKG's propagation data as a raw feed into their data lake / Snowflake / Databricks environment. They don't use MKG's dashboard or API — they ingest the data and build their own analytics. This requires: a streaming data feed (Kafka topic or webhook stream), a schema contract (published Avro/Protobuf schema), and a data SLA (delivery latency, completeness, freshness).

> **R-PLAT-14** (P0): System must support at minimum 2 integration patterns at launch: (a) Dashboard (web-based, real-time via WebSocket), (b) REST API (cursor-based pagination, webhook delivery, SDK). Each pattern must have dedicated documentation, quick-start guide, and example code. Pattern 3 (alert-driven) should ship in v1 via Telegram and Slack. Pattern 4 (data feed) is P2.

> **R-PLAT-15** (P1): System must implement an "API-first" development methodology: every feature must be available via API before (or simultaneously with) dashboard implementation. The dashboard is a reference client of the API, not a separate application. This ensures quant clients are never second-class and that the API surface is complete.

### B7. SaaS vs On-Prem — THE INEVITABLE ENTERPRISE QUESTION

Within the first 5 sales conversations, a hedge fund client will ask: "Can we run this on our infrastructure?" For financial firms with $1B+ AUM, data leaving their network boundary is often a compliance blocker. Bloomberg Terminal works precisely because data flows from Bloomberg to the terminal — client data (portfolio positions, trading ideas) never leaves the client's network.

MKG's architecture assumes SaaS (Section 12.1: "Railway" for production). But the API-based telemetry (tribal knowledge input, alert configuration, portfolio overlay) means client data flows to MKG's servers.

**Three deployment models to support:**

| Model | Where It Runs | Client Data Exposure | MKG Revenue Model | Engineering Complexity |
|-------|--------------|---------------------|-------------------|----------------------|
| **SaaS (multi-tenant)** | MKG's infrastructure | Client data on MKG's servers | Subscription ($30K–$150K/yr) | Standard |
| **Dedicated SaaS** | Separate infra managed by MKG | Client data on dedicated, MKG-managed servers | Premium subscription ($100K–$300K/yr) | +50% ops overhead |
| **On-prem / VPC** | Client's infrastructure | Client data never leaves their network | License + support ($200K–$500K/yr + $50K/yr support) | +200% — must package for deployment on arbitrary infrastructure |

Don't build on-prem support for v1 — it's a 6+ month project. But the architecture must not *preclude* on-prem. This means:

- All configuration via environment variables (already in SignalFlow pattern — good)
- No hard dependencies on Railway-specific features
- Docker Compose must work as a self-contained deployment (already exists for dev — extend for production-grade on-prem)
- No phone-home telemetry that won't work in air-gapped environments

> **R-PLAT-16** (P1): System architecture must not preclude future on-premises deployment. Specifically: (a) no Railway-specific dependencies in application code, (b) all configuration via environment variables + config files, (c) Docker Compose as a complete deployment unit, (d) no internet-required features for core functionality (graph queries, propagation, alerts must work offline — only news ingestion requires internet). This does not mean building on-prem support now — it means not painting yourself into a SaaS-only corner.

> **R-PLAT-17** (P2): System must define a "Dedicated SaaS" tier for clients requiring infrastructure isolation. In this tier: separate Neo4j instance, separate PostgreSQL database, separate Redis namespace, dedicated Celery workers. Data is physically isolated, not logically isolated. This tier targets hedge funds with $5B+ AUM where compliance requires dedicated infrastructure.

### B8. Observability and Operability — RUNNING A 24/7 SERVICE WITH 1–2 ENGINEERS

At AWS, DynamoDB has 200+ engineers, 50+ on-call SREs. At Stripe, payments infrastructure has 30+ engineers on rotation. MKG will have 1–2 engineers running a 24/7 financial intelligence system. This demands *extreme automation* — no manual intervention for routine operations.

**What must be automated:**

| Operation | Current Status | Required Automation |
|-----------|---------------|-------------------|
| Deployment | Manual Docker push | Automated CI/CD (R-PLAT-11) |
| Scaling | Manual | Auto-scale Celery workers by queue depth |
| Backup | Not mentioned | Automated daily + hourly (R-PLAT-9) |
| Backup verification | Not mentioned | Automated weekly restore-and-verify |
| Certificate renewal | Not mentioned | Automated via Let's Encrypt / Certbot |
| Log rotation | Not mentioned | Automated with retention policy |
| Dead-letter reprocessing | Not mentioned | Automated retry with configurable delay |
| Source health monitoring | Not mentioned | Automated Source Registry (R-PIPE-16) |
| Claude API budget alerting | Not mentioned | Automated at 80%, 90%, 100% of budget |
| Database connection pool monitoring | Not mentioned | Alert on pool exhaustion (>80% utilization) |
| Disk space monitoring | Not mentioned | Alert at 80% capacity, auto-archive at 90% |

> **R-PLAT-18** (P0): System must implement comprehensive operational automation for a 1–2 person engineering team. Minimum: (a) automated backup + weekly restore verification, (b) automated certificate renewal, (c) automated disk space monitoring with alerts, (d) automated Celery worker health check with restart, (e) automated Claude API budget alerts at configurable thresholds, (f) single-command deployment with automatic rollback on failure. Every manual operational procedure must be documented as a runbook.

> **R-PLAT-19** (P1): System must implement structured operational dashboards: (a) Infrastructure health: CPU, memory, disk, network per service, (b) Pipeline health: Ethan Kowalski's 15+ metrics (R-PIPE-10), (c) Business health: articles processed, entities created, propagation events, active users, API calls, (d) Cost health: Claude API spend, infrastructure spend, cost-per-client. Dashboards must be accessible via a single URL and require no manual setup after deployment.

### B9. Database Migration Strategy — THE NEO4J RISK

Neo4j CE is the stated graph database (Section 12.1). But multiple experts have identified CE limitations (Iteration 3: RBAC, clustering, multi-database; Iteration 6: compliance requirements; this iteration: multi-tenancy).

**The migration risk matrix:**

| Scenario | Probability | Trigger | Cost to Migrate |
|----------|------------|---------|----------------|
| CE → Neo4j Enterprise | HIGH (70%) | First enterprise client requires RBAC or HA | $36K–$100K/yr license + 2–4 weeks migration |
| CE → Neo4j Aura (managed) | MEDIUM (50%) | Operational burden exceeds team capacity | $500–$2K/month + 1 week migration |
| Neo4j → Amazon Neptune | LOW (15%) | Neo4j pricing unacceptable, need AWS-native | 3–6 months (different query language: Gremlin/SPARQL, different data model) |
| Neo4j → TigerGraph | LOW (10%) | Performance requirements exceed Neo4j capability at 50K+ nodes | 4–8 months (different everything) |

**The safe path:** Start with Neo4j CE. Implement a `GraphStorage` interface (as MiroFish already does). Test all graph operations against the interface, not against Neo4j directly. When migration is required, implement a new adapter behind the same interface.

> **R-PLAT-20** (P0): All graph operations must be abstracted behind a `GraphStorage` interface (already specified by R-MF6 from MiroFish). No Cypher queries in application code outside the Neo4j adapter. This enables migration from CE to Enterprise, Aura, or an alternative graph database without rewriting business logic. The interface must cover: entity CRUD, edge CRUD, subgraph traversal, propagation traversal, vector search, and backup/restore.

> **R-PLAT-21** (P1): System must maintain a "database migration readiness" checklist: (a) all graph operations behind interface = ✅/❌, (b) no Neo4j-specific code in business logic = ✅/❌, (c) integration tests runnable against mock graph store = ✅/❌, (d) migration script templates prepared for CE→Enterprise and CE→Aura paths. Review quarterly.

---

## C. Requirement Challenges

### C1. The "1–2 Engineer" Reality — Operations Will Dominate Engineering

The document assumes a small team building features. In reality, for a 24/7 SaaS platform:

| Activity | % of Engineering Time (Year 1) |
|----------|-------------------------------|
| New feature development | 25–30% |
| Bug fixes and maintenance | 15–20% |
| Operations and incident response | 20–25% |
| Customer support and integration help | 10–15% |
| Security and compliance | 10–15% |
| Infrastructure and scaling | 5–10% |

**Only 25–30% of engineering time goes to features.** The rest goes to keeping the lights on. At Stripe, we called this the "operational tax" — and it only increases as the client base grows. With 1–2 engineers, ~1 engineer is effectively full-time on operations by Month 12.

This means the feature velocity the document implies (6 phases in 24 weeks = one phase every 4 weeks) is unrealistic once the system is live. Post-launch feature velocity will drop by 50–70%.

> **R-PLAT-22** (P0): Project timeline must account for operational overhead. After initial deployment, engineering capacity for new features is reduced by 50–70%. Post-launch feature sprints should be planned at 2x the pre-launch duration. A single engineer maintaining a 24/7 SaaS platform with 10+ clients has approximately 15–20 hours/week available for new features.

### C2. The Cost-Revenue Equation — DOES THIS BUSINESS WORK?

Using the cost model from B2 and Megan Torres's revenue estimates (Iteration 5):

**Year 1 costs:**

| Category | Annual Cost |
|----------|------------|
| Infrastructure (10 clients, 10K articles/day) | $122K–$149K |
| Claude API | $108K–$120K |
| Compliance: SOC 2 prep + pentest + legal | $95K–$220K (Iteration 6) |
| Sales & marketing (1 AE + conference circuit) | $150K–$250K |
| Engineering (2 engineers, assuming founders) | $0 (founder cost) or $250K–$400K (if hired) |
| Legal (investment adviser opinion, contracts, privacy) | $50K–$100K |
| **Total (founders as engineers)** | **$525K–$839K** |
| **Total (hired engineers)** | **$775K–$1.24M** |

**Year 1 revenue (optimistic, per Megan Torres adjusted estimates):**

| Quarter | Clients | Revenue |
|---------|---------|---------|
| Q1 | 0 (building) | $0 |
| Q2 | 0 (beta with design partners) | $0 |
| Q3 | 2–3 (first paid) | $15K–$38K |
| Q4 | 5–8 (growing) | $38K–$100K |
| **Year 1 Total** | | **$53K–$138K** |

**Gap: $400K–$700K minimum.** This is a venture-backable gap (raise $1M–$1.5M seed round) but it means MKG is a VC-funded startup, not a bootstrappable side project. The document doesn't acknowledge this financial reality.

> **R-PLAT-23** (P0): Business plan must include a financial model showing: (a) monthly burn rate by category, (b) revenue forecast by quarter for 24 months, (c) funding requirement (gap between costs and revenue), (d) break-even target (month when revenue covers costs — likely Month 24–30), (e) sensitivity analysis (what if Claude API costs double? what if sales cycle is 9 months instead of 6?).

---

## D. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Infrastructure costs (especially Claude API) exceed revenue for 18+ months — requires VC funding | HIGH | HIGH — cash runs out | R-PLAT-3: cost model; R-PLAT-4: cost optimization; R-PLAT-23: financial plan |
| 2 | Multi-tenancy not properly isolated — tribal knowledge leaks between clients | MEDIUM | FATAL — trust destroyed, legal liability | R-PLAT-1: hybrid isolation with 100+ boundary tests |
| 3 | No disaster recovery — data loss during incident destroys accuracy track record and client trust | HIGH | HIGH | R-PLAT-8, R-PLAT-9: RTO/RPO targets + automated backups |
| 4 | API breaks client integrations during update — quant team's production code stops working | MEDIUM | HIGH — client churn, reputation damage | R-PLAT-5: versioning + deprecation policy |
| 5 | Operational overhead consumes engineering capacity — no features shipped for months | HIGH | MEDIUM — competitive risk | R-PLAT-18: automation; R-PLAT-22: realistic timeline |
| 6 | Railway (single cloud) outage takes MKG offline during market event | MEDIUM | HIGH — clients lose trust in 24/7 availability | R-PLAT-16: architecture portability; R-PLAT-10: graceful degradation |
| 7 | Neo4j CE limitations force unplanned migration under pressure | HIGH (70%) | MEDIUM — 2–4 weeks lost + license cost | R-PLAT-20: GraphStorage interface; R-PLAT-21: migration readiness |
| 8 | No CI/CD: manual deployment introduces bugs into production | HIGH | HIGH — financial intelligence with incorrect data | R-PLAT-11, R-PLAT-12: automated pipeline with zero-downtime deployment |

---

## E. Five Critical Questions

1. **What is the monthly infrastructure cost at 1, 10, 50, and 100 clients?** If cost-per-client doesn't decrease significantly with scale (because Claude API cost is per-article, not per-client), then the margin structure may not work. A $50K/yr contract with $15K/yr infrastructure cost per client is a 70% gross margin (healthy). A $50K/yr contract with $40K/yr cost per client is a 20% margin (unsustainable for SaaS). Model this before building.

2. **Can MKG survive a 4-hour Claude API outage during a major market event?** This is the worst-case scenario: the system is needed most when the API is most likely to be strained (all Anthropic customers processing the same event). The fallback extraction mode (R-PIPE-7) must be tested under realistic conditions — not just "it exists" but "it produces useful output that clients won't complain about."

3. **How do you prevent tenant data leakage with a 1–2 person team?** At AWS, DynamoDB's multi-tenancy isolation was tested by a 10-person security team running continuous penetration tests. At Stripe, isolation was verified by automated contract testing on every deployment. With 1–2 engineers, the isolation test suite must be fully automated, run on every CI/CD pipeline, and cover every API endpoint × every tenant boundary.

4. **Is Railway the right production platform for a 24/7 financial intelligence system?** Railway is excellent for prototypes and small-scale deployment. But it's a managed PaaS with limited control over instance placement, networking, and disaster recovery. For SOC 2 compliance (R-SEC-8), MKG needs to demonstrate control over its infrastructure. At what client count does MKG migrate from Railway to AWS/GCP with Kubernetes? (My estimate: client 15–20, or first enterprise client with compliance requirements, whichever comes first.)

5. **What happens when the second engineer goes on vacation?** A 24/7 system with a single point of human failure (one engineer on-call) is a burnout machine. The first $100K of revenue should fund a part-time DevOps/SRE contractor or managed service. This is not a feature decision — it's a sustainability decision. The founding engineer cannot maintain a pager for 365 days without relief.

---
---

# Cross-Expert Synthesis — Iterations 9 & 10

## Areas of Agreement

| Finding | Sophia Nakamura (Competitive Intel) | Rajesh Krishnamurthy (Platform) | Implication |
|---------|--------------------------------------|----------------------------------|-------------|
| **MKG has no durable competitive moat** | No proprietary data, no network effects, no switching costs — any funded team or incumbent replicates in 12–18 months | No technical barriers to entry — Neo4j + Claude API available to anyone, architecture is standard microservices | Moat must be built deliberately (data accumulation, accuracy track record, integration depth) — not assumed from technology |
| **The business model is unvalidated** | Pricing ranges span 15x ($20K–$300K), no discovery calls, no sales motion defined | Cost model shows $122K–$149K/yr infrastructure at 10 clients; break-even requires ~15 clients at $50K each | Revenue assumptions are aspirational, costs are concrete — gap requires funding |
| **Operational reality will crush feature velocity** | Go-to-market requires sales infrastructure that the document doesn't budget for | Engineering time for features drops to 25–30% post-launch; operational overhead dominates | Timeline and scope must account for GTM cost and operational tax |
| **Claude API is the strategic chokepoint** | Dependency on a single vendor's API for core intelligence creates vendor risk and cost exposure | Claude API is 75–80% of infrastructure cost; any pricing change by Anthropic changes MKG's economics | Cost optimization + fallback extraction = survival requirements, not nice-to-haves |

## Areas of Divergence

| Topic | Sophia Nakamura | Rajesh Krishnamurthy | Resolution |
|-------|-----------------|----------------------|------------|
| **Tribal knowledge: shared vs private?** | Must be shared (aggregated, anonymized) to create network effects moat | Must be isolated per tenant for enterprise security compliance | Both are right — implement tiered model: raw entries private, aggregated statistics shared |
| **On-premises support** | Not needed for beachhead (event-driven funds are cloud-comfortable) | Must be architecturally possible even if not built yet | Agree on architecture portability without building on-prem support in v1 |
| **Biggest risk** | Bloomberg replication kills the business within 36 months | Infrastructure costs exceed revenue for 18+ months, requiring VC funding | Both existential — one is competitive, the other is financial |
| **Neo4j Enterprise decision** | Don't spend $36K/yr on database before revenue exists | Need RBAC and HA before first enterprise client; CE limitations hit at client #3 | Start CE, budget for Enterprise at client #5 or first $200K ARR, whichever comes first |

---

## New Requirements Count

| Iteration | Expert | New Requirements | Critical (P0) |
|-----------|--------|-----------------|---------------|
| 1 | Marcus Chen (Hedge Fund PM) | 15 | 9 |
| 2 | Dr. Priya Sharma (Supply Chain VP) | 15 | 6 |
| 3 | Dr. Kai Müller (Graph DB Architect) | 12 | 7 |
| 4 | Dr. Aisha Ibrahim (NLP/NER Scientist) | 20 | 12 |
| 5 | Megan Torres (Enterprise PM / GTM) | 15 | 7 |
| 6 | James Wright (CISO / Compliance) | 32 | 21 |
| 7 | Ethan Kowalski (Pipeline Architect) | 21 | 11 |
| 8 | Yuki Tanaka (Financial UX Designer) | 15 | 7 |
| 9 | Sophia Nakamura (Competitive Intel) | 15 | 7 |
| 10 | Rajesh Krishnamurthy (Platform Engineer) | 23 | 12 |
| **Total** | | **183** | **99** |

---
---

# FINAL CONSENSUS — All 10 Experts

## Overall Viability Score

| Expert | Domain | Score |
|--------|--------|-------|
| 1. Marcus Chen | Hedge Fund PM (buy-side user) | 7/10 |
| 2. Dr. Priya Sharma | Supply Chain VP (enterprise buyer) | 6/10 |
| 3. Dr. Kai Müller | Graph DB Architecture | 5/10 |
| 4. Dr. Aisha Ibrahim | NLP/NER Science | 4/10 |
| 5. Megan Torres | Enterprise PM / GTM | 3/10 |
| 6. James Wright | CISO / Compliance | 4/10 |
| 7. Ethan Kowalski | Pipeline Architecture | 4/10 |
| 8. Yuki Tanaka | Financial UX Design | 4/10 |
| 9. Sophia Nakamura | Competitive Intelligence | 3/10 |
| 10. Rajesh Krishnamurthy | Platform Engineering | 3/10 |
| **AVERAGE** | | **4.3/10** |

**Interpretation:** The concept is strong (users who feel the Speed 3 pain validated it immediately — Marcus gave 7/10). The execution specification is deeply inadequate. Scores decline monotonically from the user perspective (7) to the builder perspective (3) — the closer an expert is to implementation reality, the more gaps they find.

**This is not a failing grade for the vision — it's a failing grade for the specification.** The Speed 3 market gap is real. The propagation engine concept is sound. The semiconductor beachhead is correct. But the document describes a 24-week build plan for a product that requires 18–24 months, $600K–$1.2M in capital, and approximately 300 requirements (183 newly identified + existing ~120) — of which only ~20 should be in a beachhead MVP.

---

## Top 10 Showstoppers (Ranked by Severity × Likelihood)

| Rank | Showstopper | Expert(s) | Impact If Unresolved |
|------|-------------|-----------|---------------------|
| **1** | **No competitive moat — technology is replicable, data is public, zero network effects** | Sophia (9) | Bloomberg or AlphaSense replicates within 24–36 months; MKG loses all clients |
| **2** | **No go-to-market strategy — product exists but nobody knows, sales cycle unplanned, zero distribution** | Megan (5), Sophia (9) | Product built, nobody buys it, runway exhausted |
| **3** | **Investment adviser classification unresolved — portfolio overlay + personalized alerts may require registration** | James (6) | Federal crime if unregistered; product scope must change if registration required |
| **4** | **NLP accuracy fundamentally insufficient — 4-hop all-correct ~24%, RE at 65–75% F1, hallucination 8–15%** | Aisha (4) | Graph filled with incorrect relationships; propagation results are wrong; clients lose trust |
| **5** | **Claude API: single vendor dependency at $108K–$120K/yr, no fallback, 75–80% of infrastructure cost** | Ethan (7), Rajesh (10) | Anthropic price increase, API outage, or policy change threatens entire business |
| **6** | **Institutional procurement gates missing — no SOC 2, no SSO, no pentest** | James (6), Rajesh (10) | Every enterprise sales process terminates at security questionnaire |
| **7** | **Year 1 financial gap: $525K–$839K costs vs $53K–$138K revenue** | Megan (5), Rajesh (10) | Business runs out of money before reaching product-market fit |
| **8** | **Pipeline has no reliability guarantees — at-most-once delivery, no DLQ, no observability, no backpressure** | Ethan (7) | Articles silently lost; graph has invisible holes; impossible to detect or repair |
| **9** | **Multi-tenancy undesigned — one missing WHERE clause = tribal knowledge leak between competing hedge funds** | Kai (3), James (6), Rajesh (10) | Client trust destroyed; legal liability; career-ending for client compliance officers |
| **10** | **24-week plan produces a demo, not a product — first revenue at Month 15–18, not Month 6** | Megan (5), Sophia (9), Rajesh (10) | Expectations misaligned; investor/stakeholder disappointment; premature launch of unready product |

---

## Beachhead MVP — Maximum 20 Requirements

If MKG is to ship a viable, revenue-generating product, it must ruthlessly cut scope. The following 20 requirements define the **minimum product that a single event-driven hedge fund PM would pay $30K–$50K/yr to use:**

### What's IN (20 requirements):

| # | Requirement | Source | Rationale |
|---|-------------|--------|-----------|
| 1 | **Semiconductor entity graph: 500 companies, 5,000 edges** | R-KG1, R-KG2, R-KG3 | Minimum graph for useful propagation in semiconductor vertical |
| 2 | **English-only NER/RE from SEC filings + earnings transcripts + 5 news sources** | R-IA1 (scoped), R-IA3, R-IA4 | English only. 5 sources, not 50. Filings + transcripts = highest signal-to-noise |
| 3 | **Entity deduplication (canonical name resolution)** | R-IA5, R-KG7 | Graph integrity depends on entity resolution |
| 4 | **Edge weight 0.0–1.0 with confidence and source tracking** | R-KG4 | Core data model for propagation quality |
| 5 | **Rule-based weight adjustment (no GAT)** | R-WAN1, R-WAN2 | Interpretable, debuggable, shippable in weeks not months |
| 6 | **Propagation engine: trigger → ranked impact list, 4 hops, <60 seconds** | R-PE1, R-PE2, R-PE3, R-PE6 | Core product value — this is the sale |
| 7 | **Causal chain explainability per impacted entity** | R-PE5, R-EXP1 | Non-negotiable for PM trust and compliance |
| 8 | **At-least-once pipeline delivery with DLQ** | R-PIPE-3, R-PIPE-9 | Data integrity minimum — no silent article loss |
| 9 | **Claude API cost governance + fallback extraction** | R-PIPE-14, R-PIPE-7 | Business survival — cannot allow unbounded API spend |
| 10 | **Durable article storage (2-year retention)** | R-PIPE-18 | Data moat starts accumulating from day 1 |
| 11 | **REST API with versioning, pagination, error format** | R-OUT1, R-PLAT-5 | Quant integration: the stickiest deployment pattern |
| 12 | **Webhook delivery for propagation events** | R-PLAT-6 | Core alert mechanism for API-integrated clients |
| 13 | **Ranked impact table (not graph viz) as primary view** | R-VIZ-1, R-VIZ-2 | Table-first per Yuki Tanaka: 80% of usage is Levels 1–3 |
| 14 | **Accuracy tracking from day 1** | R-COMP-3, R-EXP5 | Moat building — after 12 months, this is unreplicable |
| 15 | **Tribal knowledge input (manual expert assertions)** | R-TK1, R-TK2, R-TK5 | Switching cost + data moat — only private, no sharing in v1 |
| 16 | **JWT authentication + tenant isolation (hybrid model)** | R-SEC1, R-PLAT-1 | Enterprise security minimum |
| 17 | **Automated backup + disaster recovery** | R-PLAT-8, R-PLAT-9 | Operational survival |
| 18 | **CI/CD pipeline with zero-downtime deployment** | R-PLAT-11, R-PLAT-12 | 24/7 reliability without manual deployment risk |
| 19 | **Pipeline observability (15+ metrics + health dashboard)** | R-PIPE-10 | Operational awareness — detect failures before clients do |
| 20 | **Alert system: configurable propagation event triggers** | R-OUT7 | Core user-facing feature — PM sets watchlist, gets notified |

### What's OUT (defer to v2+):

| Feature | Original Priority | Why It's Cut |
|---------|-------------------|-------------|
| Graph visualization (force-directed / WebGL) | P1 (R-OUT3) | 80% of usage is tables; graph is 3–4 months of engineering; defer to v2 |
| What-if scenario simulation | P1 (R-OUT5) | Complex UX + unreliable results without calibration data; defer to v2 |
| Temporal versioning (query graph at time T) | P0 (R-KG5) | 3–6 month engineering project (per Kai Müller); defer to v2 |
| Multilingual NER (13 languages) | P0/P1 (R-IA1, R-IA9) | Multi-year NLP effort; English-only for beachhead |
| GAT-based weight adjustment (Layer 3 ML) | P2 (R-WAN3) | Rule-based is sufficient and interpretable for v1 |
| 10,000 articles/day ingestion | P1 (R-IA10) | Start with 1,000/day; scale when pipeline is proven |
| MiroFish simulation layer | P0–P2 (R-MF1–R-MF8) | Separate product; adds complexity without validating core MKG value |
| Supply chain vertical features | Various | Financial markets is the beachhead; supply chain is v2 |
| SSO/SAML | P0 (R-SEC-29) | Required for enterprise — but first 5 clients can use JWT; add at client #6 |
| SOC 2 certification | P0 (R-SEC-8) | Start the process during MVP build; submit during v2 |
| Excel/Sheets/Slack integrations | P1 (R-COMP-13) | Valuable but not launch-blocking; add by Month 9 |
| On-prem deployment support | P2 (R-PLAT-16) | Architecture allows it; don't build it until enterprise client demands it |
| Community knowledge layer | P1 (R-COMP-2) | Moat feature — but requires 10+ clients contributing first; add when client base supports it |
| Portfolio overlay | SHOW-STOPPER (Marcus) | Cut for legal clarity — defer until investment adviser status resolved |

---

## Realistic Timeline

| Phase | Duration | Deliverable | Exit Criteria |
|-------|----------|-------------|---------------|
| **Phase 0: Validation** | Weeks 1–4 | 20 discovery calls; investment adviser legal opinion; pricing validation | 5 design partner commitments; legal green light; price point validated at $30K–$50K |
| **Phase 1: Graph Foundation** | Weeks 5–12 | 500-entity semiconductor graph; entity CRUD API; seed data from SEC filings | Query "show me all TSMC suppliers" returns correct, sourced results |
| **Phase 2: Extraction Pipeline** | Weeks 13–20 | English NER/RE from 5 sources; at-least-once delivery; DLQ; cost governance | 500 articles/day auto-updating graph; <5% extraction error rate; Claude API spend <$3K/month |
| **Phase 3: Propagation + Alerts** | Weeks 21–28 | Propagation engine; causal chains; ranked impact table; alert system; webhook API | "TSMC fab fire" → ranked impact list in <60 seconds; design partners receiving alerts |
| **Phase 4: Productization** | Weeks 29–36 | Auth; tenant isolation; accuracy tracking; CI/CD; automated backups; tribal knowledge input | Design partners using daily; 100+ isolation boundary tests pass; CI/CD pipeline green |
| **Phase 5: Launch** | Weeks 37–42 | First paid clients; client onboarding; SOC 2 process started; Excel integration | 2–3 paying clients at $30K–$50K/yr; accuracy track record building |
| **Phase 6: Moat Building** | Weeks 43–52 | SSO/SAML; graph visualization (v1); more integrations; community knowledge layer prep | 5–8 paying clients; accuracy track record ≥6 months; SOC 2 Type I submitted |

**Total: 52 weeks (12 months) to first revenue. 18–24 months to $500K ARR.**

---

## Realistic Cost Estimate

| Category | Year 1 (Months 1–12) | Year 2 (Months 13–24) |
|----------|----------------------|----------------------|
| **Engineering (2 founders, no salary)** | $0 (sweat equity) | $0 (or $100K–$200K if paying selves) |
| **Infrastructure (cloud, database, monitoring)** | $18K–$36K (scaling over year) | $60K–$120K (10+ clients) |
| **Claude API** | $36K–$72K (500→2K articles/day ramp) | $108K–$120K (10K articles/day) |
| **Compliance (SOC 2, pentest, legal)** | $50K–$100K | $30K–$50K (annual renewal + maintenance) |
| **Sales & Marketing (conferences, tooling)** | $30K–$60K (founder-led sales, 2 conferences) | $150K–$250K (first AE hired) |
| **Legal (investment adviser, contracts, IP)** | $30K–$50K | $15K–$25K |
| **Miscellaneous (SaaS tools, professional services)** | $10K–$20K | $15K–$25K |
| **Total** | **$174K–$338K** | **$378K–$790K** |

**Cumulative 24-month cost: $552K–$1.13M**

**Funding requirement:** $500K–$1M seed round (pre-product or at Phase 1 completion). Alternatively, bootstrap through Phase 4 (~$174K–$338K), then raise $500K at first client milestone.

---

## Key Success Factor

**The single factor that determines whether MKG succeeds or fails:**

> **Accuracy track record, accumulated over time, demonstrable to buyers.**

Every other challenge — pricing, distribution, technology, compliance — has a known solution if sufficient funding and time are available. But accuracy is uniquely existential:

- **If MKG's propagation predictions are accurate** (≥70% hit rate on direction, within 2x on magnitude), the product sells itself through word-of-mouth among event-driven fund PMs. One analyst tells another: "This tool predicted the NVIDIA impact from the TSMC event before anyone else, and it was right." That's the sales pitch.

- **If MKG's predictions are inaccurate** (<60% hit rate), no amount of marketing, pricing, or features will save the product. Bloomberg-native PMs have seen dozens of "AI-powered insight" tools flame out because the predictions were noise dressed as signal. Trust, once lost, is unrecoverable.

The entire product strategy — from NER accuracy (Dr. Ibrahim's evaluation infrastructure), to pipeline reliability (no lost articles), to weight calibration (feedback loop from outcomes), to competitive moat (12+ months of track record) — converges on this single metric.

**Build the accuracy measurement infrastructure first.** Track every propagation event. Compare every prediction to the actual market outcome within 30 days. Publish the results to every client, every month. Make accuracy the brand identity: "MKG: 74% accuracy on second-order supply chain impact predictions." That number, accumulated over time, is the only moat that Bloomberg cannot instantly replicate.

---

## Final Recommendation from 10 Experts

**BUILD — but not as currently specified.**

The Speed 3 market gap is real and validated by the buy-side expert (7/10). The semiconductor beachhead is correct. The propagation engine concept is sound. But the current specification is a feature list masquerading as a product plan. It needs:

1. **Scope reduction**: 20 MVP requirements, not 300. Ship the ranked impact table, not the graph.
2. **Moat strategy**: Start accumulating accuracy data from day 1. Build tribal knowledge input in v1.
3. **Financial realism**: $500K–$1M seed round is required. Plan for 18–24 months to $500K ARR.
4. **Go-to-market**: 20 discovery calls before writing code. 5 design partners before launching.
5. **Legal clarity**: Get the investment adviser opinion before committing to portfolio overlay features.
6. **Pipeline reliability**: At-least-once delivery, DLQ, cost governance — non-negotiable for data integrity.
7. **Operational automation**: A 1–2 person team cannot run a 24/7 platform without extreme automation.
8. **Competitive awareness**: Bloomberg can build this in 12 months if they want to. Win with data depth and accuracy, not with features.

The product that should be built is narrower than what's specified, takes longer than planned, costs more than anticipated, and succeeds only if the intelligence it produces is demonstrably accurate. That's not a reason not to build it — it's a reason to build it right.

---

*End of MKG Expert Panel Review — 10 of 10 iterations complete.*
*183 new requirements identified. 99 at P0. Overall viability: 4.3/10 for specification; high for concept.*
