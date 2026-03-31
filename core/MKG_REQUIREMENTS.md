# MKG — Complete Requirements Document

> Extracted from: MKG_Problem_Definition, MKG_Problem_Research-2, MKG_Market_Research, MKG_Competitor_Deep_Dive, MKG_Tribal_Knowledge_Gap, MKG_SupplyChain_Application, MKG_Niche_Definition_FINAL, and MiroFish-Offline review.
>
> Date: 31 March 2026

---

## 1. Product Vision

**Market Knowledge Graph (MKG)** is a dynamic relationship intelligence system that continuously maps, weights, and traverses hidden connections between 5,000+ global entities — delivering ranked impact predictions with causal chains in under 60 seconds.

**Core promise:** When Event X happens, MKG tells you: Who gets hit? How hard? In what direction? Through what chain? With what confidence? — before anyone else connects the dots.

**Two verticals:**
- **Financial Markets** — Speed 3 alpha generation (PEAD exploitation, supply chain contagion trading)
- **Supply Chain Intelligence** — Tier 2/3+ disruption prediction and hidden dependency discovery

---

## 2. The Problem (from Problem Definition + Problem Research-2)

### 2.1 Three-Speed Market Framework

| Speed | Window | Example | Current Tools |
|-------|--------|---------|---------------|
| Speed 1 | <100ms | Earnings beat/miss | HFT algos — fully competed |
| Speed 2 | 100ms–4hrs | Headline → sector reaction | Bloomberg Terminal, RavenPack — crowded |
| Speed 3 | 4hrs–14 days | Second/third-order supply chain effects | **NOTHING** — human analysts only |

**MKG targets Speed 3** — the empty quadrant where no commercial tool operates.

### 2.2 Four Core Problems

1. **The Relationship Blindness Problem** — Markets see companies as isolated nodes, not as a connected graph. When TSMC has a fab disruption, human analysts take 3-7 days to manually trace the impact through NVIDIA → cloud providers → SaaS companies.

2. **The Weight Estimation Problem** — Even when a relationship is known (e.g., Apple depends on TSMC), nobody quantifies the real-time weight of that dependency. Is it 30% or 70% of Apple's chip supply? Existing tools don't track this dynamically.

3. **The Propagation Speed Problem** — By the time a human analyst traces a 3-hop supply chain disruption, the market has already moved. The 4-hour to 14-day window is where alpha exists but current tools can't operate at graph speed.

4. **The Tribal Knowledge Problem** — Critical relationship intelligence (unofficial alliances, cultural risk factors, executive relationship networks, regulatory intent signals) exists only in expert heads, not in any database.

### 2.3 Seven Critical Gaps in Current Market

1. No tool maps latent, multi-hop company dependencies continuously
2. No tool dynamically weights relationships from live signals
3. No tool propagates event impact through supply chain graphs in real time
4. No tool encodes tribal/tacit knowledge into queryable structures
5. No tool provides causal chain explainability for each impact prediction
6. No tool offers temporal graph versioning (state of relationships at time T)
7. No tool provides cross-domain intelligence (financial + supply chain in one graph)

### 2.4 Academic Evidence

- **PEAD (Ball & Brown, 1968 → Bernard & Thomas, 1989)**: Post-Earnings Announcement Drift — markets take 60-90 days to fully price in earnings surprises. MKG exploits this by predicting second-order effects before they're priced.
- **POM (Hsu et al., 2024)**: "Propagation of Macro Shocks" — documented that supply chain contagion effects persist for weeks and are predictable.
- **UC San Diego (2025)**: "Hidden Supply Chain Risk" paper showed that Tier 2/3 supplier disruptions cause 2-5x larger stock drops than direct supplier disruptions, because they're invisible.
- **TSMC Case Study**: February 2024 earthquake → 14-day cascading effect through NVIDIA → AMD → cloud providers → enterprise SaaS. Human analysts identified the full chain in 7 days. MKG target: 60 seconds.

---

## 3. Market Opportunity (from Market Research + Competitor Deep Dive)

### 3.1 Market Size

- **TAM**: $35B (financial data + supply chain intelligence combined)
- **SAM**: $8.2B (relationship intelligence specifically)
- **SOM (Year 1)**: $50M–$100M (semiconductor + automotive supply chain focus)

### 3.2 Competitive Landscape — 9 Analyzed Platforms

| Platform | Revenue | Pricing | What They Do | What They DON'T Do |
|----------|---------|---------|--------------|-------------------|
| **Bloomberg Terminal** | $12B/yr | $24K/yr/seat | Real-time financial data | No graph relationships, no supply chain, no propagation |
| **LSEG (Refinitiv)** | $7.2B/yr | ESG + data feeds | Financial data, ESG scoring | No dynamic weights, no causal chains |
| **FactSet** | $2.1B/yr | ~$12K/yr/seat | Financial modeling, screening | Static relationships only, no propagation |
| **S&P Capital IQ** | (part of $9B) | ~$18K/yr/seat | Company fundamentals | Static org charts, no live weights |
| **AlphaSense** | ~$500M ARR | $30-100K/yr | AI search over documents | Search, not graph — finds mentions, not relationships |
| **RavenPack** | ~$100M ARR | $50-200K/yr | NLP news sentiment | Event detection only, no relationship mapping |
| **Palantir Foundry** | $2.2B/yr | $1M+/yr | General graph analytics | Requires 6-12 month implementation, not financial-specific |
| **Interos** | ~$50M ARR | $100-500K/yr | Supply chain mapping | Static maps, no live signals, no financial cross-over |
| **FinDKG** | Research | Free | Academic knowledge graph | Static, no live signals, no propagation, prototype only |

### 3.3 The Empty Quadrant

No existing commercial product sits at the intersection of:
- ✅ Dynamic relationship weights (updated from live signals)
- ✅ Multi-hop propagation engine (cascading impact prediction)
- ✅ Causal chain explainability (transparent reasoning)
- ✅ Cross-domain (financial + supply chain in one graph)

**MKG is the first product to occupy this quadrant.**

---

## 4. Tribal Knowledge Requirements (from Tribal Knowledge Gap)

### 4.1 Eight Types of Tribal Knowledge to Encode

**Financial Domain (4 types):**

1. **Unofficial Business Alliances** — "Everyone on the Street knows Samsung and Google have an informal exclusivity on Tensor chips, but it's never in any filing." Encode as weighted edge with source = "industry expert" and confidence level.

2. **Executive Relationship Networks** — "The CFO of Company A used to be VP at Company B. When they need emergency supply, that relationship gets activated." Encode as person→company edges with historical role metadata.

3. **Cultural/Geopolitical Risk Factors** — "Japanese suppliers will never publicly admit capacity constraints until it's too late — you need to read between the lines of their guidance language." Encode as country→behavior pattern edges with linguistic signal mappings.

4. **Regulatory Intent Signals** — "The EU commissioner's speech pattern shifted from 'exploring' to 'implementing' — that's a 6-month regulatory timeline signal." Encode as regulator→regulation edges with NLP-tracked intent progression.

**Supply Chain Domain (4 types):**

5. **Hidden Tier 2/3 Dependencies** — "Everyone knows Apple uses TSMC, but nobody tracks that TSMC depends on ASML, who depends on Zeiss for optics, who depends on Schott for specialty glass." Encode as multi-hop supplier edges discovered from earnings transcripts + trade data.

6. **Capacity Utilization Intelligence** — "That fab is running at 94% utilization — one more order and they're capacity-constrained." Encode as facility→capacity edges updated from satellite imagery + shipping data + earnings calls.

7. **Logistics Chokepoint Knowledge** — "90% of advanced chip packaging goes through a single facility in Penang, Malaysia." Encode as product→facility→geography edges with concentration risk scores.

8. **Substitution Feasibility** — "You can't just switch from TSMC N3 to Samsung 3nm — the design rules are incompatible and revalidation takes 18 months." Encode as supplier→alternative_supplier edges with switching cost and timeline metadata.

### 4.2 Requirements for Tribal Knowledge Encoding

- R-TK1: System must support manual expert input of relationship assertions with confidence scores
- R-TK2: System must track provenance of each tribal knowledge entry (who said it, when, what source)
- R-TK3: System must allow tribal knowledge to decay over time (configurable half-life per knowledge type)
- R-TK4: System must support contradiction detection (new signal contradicts existing tribal knowledge)
- R-TK5: System must distinguish between "verified" (from data), "asserted" (from expert), and "inferred" (from LLM) edge sources
- R-TK6: System must allow tribal knowledge to be upgraded to verified status when supporting data arrives

---

## 5. Architecture Requirements (from all documents)

### 5.1 Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: OUTPUT & DEBUG                                     │
│  Dashboard │ API │ Alerts │ Explainability │ Audit Trail     │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: WEIGHT ADJUSTMENT NETWORK (WAN)                    │
│  GAT-based neural network │ edge weight updates │ training   │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: KNOWLEDGE GRAPH                                    │
│  Neo4j │ 6 node types │ 7 edge types │ temporal versioning  │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: INTELLIGENCE AGENT                                 │
│  Multilingual scraping │ NER/RE │ Signal extraction │ 13 langs│
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Layer 1 — Intelligence Agent

**Purpose:** Continuously ingest news, filings, transcripts, trade data → extract entities and relationships → feed into Knowledge Graph.

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-IA1 | Ingest news from 50+ sources across 13 languages | P0 |
| R-IA2 | Support source types: news articles, SEC/regulatory filings, earnings transcripts, press releases, social media (Twitter/X), trade data feeds | P0 |
| R-IA3 | Named Entity Recognition (NER) for: Company, Person, Product, Facility, Country, Regulation | P0 |
| R-IA4 | Relation Extraction (RE) for: SUPPLIES_TO, COMPETES_WITH, MANUFACTURES_AT, REGULATES, INVESTS_IN, PARTNERS_WITH, DEPENDS_ON | P0 |
| R-IA5 | Deduplication of entities across sources (canonical name resolution) | P0 |
| R-IA6 | Deduplication of news articles (same event, different sources) | P0 |
| R-IA7 | Extract sentiment and impact magnitude from each signal | P0 |
| R-IA8 | Extract temporal information (when did/will the event happen) | P1 |
| R-IA9 | Multilingual NER/RE — at minimum: English, Chinese (Simplified + Traditional), Japanese, Korean, German, French | P1 |
| R-IA10 | Process a minimum of 10,000 articles/day at steady state | P1 |
| R-IA11 | Maximum latency from article publication to graph update: 5 minutes | P0 |
| R-IA12 | Source credibility scoring (Reuters > random blog) | P1 |
| R-IA13 | Prompt injection prevention on all LLM-processed inputs | P0 |
| R-IA14 | RSS, API, and web scraping ingestion methods | P0 |

### 5.3 Layer 2 — Knowledge Graph

**Purpose:** Store and maintain the global entity-relationship graph with temporal versioning.

#### 5.3.1 Node Types (6)

| Node Type | Key Attributes | Example |
|-----------|---------------|---------|
| **Company** | name, ticker, market_cap, sector, country, founded, revenue | TSMC (TSM) |
| **Product** | name, category, lifecycle_stage, key_specs | A16 Bionic chip |
| **Facility** | name, location, type (fab/warehouse/HQ), capacity, utilization | TSMC Fab 18, Tainan |
| **Person** | name, title, company_affiliations, influence_score | Jensen Huang, CEO NVIDIA |
| **Country/Region** | name, iso_code, regulatory_regime, geopolitical_risk_score | Taiwan |
| **Regulation** | name, jurisdiction, status (proposed/enacted/enforced), effective_date | EU AI Act |

#### 5.3.2 Edge Types (7)

| Edge Type | Source → Target | Key Attributes |
|-----------|----------------|----------------|
| **SUPPLIES_TO** | Company → Company | weight (0-1), product_category, volume_pct, contract_end_date |
| **COMPETES_WITH** | Company → Company | overlap_score, market_segments |
| **MANUFACTURES_AT** | Company → Facility | product_lines, capacity_allocation_pct |
| **REGULATES** | Regulation → Company/Country | compliance_status, deadline, penalty_risk |
| **INVESTS_IN** | Company/Person → Company | stake_pct, investment_type, date |
| **PARTNERS_WITH** | Company → Company | partnership_type, exclusivity, start_date |
| **DEPENDS_ON** | Company → Product/Company | criticality (low/medium/high/critical), substitution_difficulty |

#### 5.3.3 Graph Requirements

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-KG1 | Graph database: Neo4j (leveraging existing MiroFish patterns) | P0 |
| R-KG2 | Support minimum 5,000 entity nodes at launch, scalable to 50,000+ | P0 |
| R-KG3 | Support minimum 50,000 relationship edges at launch, scalable to 500,000+ | P0 |
| R-KG4 | Every edge must have: weight (0.0–1.0), confidence (0.0–1.0), source, last_updated, valid_from, valid_until | P0 |
| R-KG5 | Temporal versioning — ability to query "state of graph at time T" | P0 |
| R-KG6 | Graph snapshots at minimum daily granularity | P0 |
| R-KG7 | Entity deduplication by canonical name (MERGE on insert, like MiroFish pattern) | P0 |
| R-KG8 | Hybrid search: vector similarity + keyword (BM25), configurable weights | P0 |
| R-KG9 | Edge provenance: every weight change must record source signal, timestamp, old_weight, new_weight | P0 |
| R-KG10 | Support for manual expert assertions (tribal knowledge) alongside automated signals | P0 |
| R-KG11 | All financial values as Decimal, never float | P0 |
| R-KG12 | Ontology stored per graph (extensible entity types + relation types) | P1 |
| R-KG13 | Full graph export/import for backup and migration | P1 |
| R-KG14 | Embedding vectors on both nodes and edges for semantic search | P0 |

### 5.4 Layer 3 — Weight Adjustment Network (WAN)

**Purpose:** When a new signal arrives (news article, filing, data point), dynamically adjust the relevant edge weights in the graph.

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-WAN1 | Input: signal event (entity, sentiment, magnitude, source credibility) → Output: set of edge weight deltas | P0 |
| R-WAN2 | Phase 1: Rule-based weight adjustment (interpretable, debuggable) | P0 |
| R-WAN3 | Phase 2: GAT (Graph Attention Network) based weight adjustment (learned from historical signal→price data) | P2 |
| R-WAN4 | Weight changes must be logged with full audit trail (signal → weight change → reason) | P0 |
| R-WAN5 | Configurable decay function: edge weights decay toward baseline if no confirming signals arrive | P1 |
| R-WAN6 | Contradiction handling: when two signals disagree on an edge's weight, apply configurable resolution strategy (latest wins, average, credibility-weighted) | P1 |
| R-WAN7 | Maximum latency from signal receipt to all affected edge weights updated: 30 seconds | P0 |
| R-WAN8 | Support for "shock events" that immediately adjust weights without waiting for normal pipeline | P1 |

### 5.5 Layer 4 — Propagation Engine

**Purpose:** When an event triggers, traverse the graph from the trigger entity outward, computing cascading impact scores at each hop.

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-PE1 | Input: trigger entity + event type + magnitude → Output: ranked list of impacted entities with scores | P0 |
| R-PE2 | Maximum propagation depth: configurable, default 4 hops | P0 |
| R-PE3 | Impact attenuation: each hop multiplies by edge weight × attenuation factor (default 0.7 per hop) | P0 |
| R-PE4 | Direction-aware: distinguish between "positive" and "negative" impact propagation | P0 |
| R-PE5 | Full causal chain for every impacted entity: "Entity A → (SUPPLIES_TO, weight 0.8) → Entity B → (DEPENDS_ON, weight 0.6) → Entity C" | P0 |
| R-PE6 | Latency target: trigger → full ranked impact list in <60 seconds | P0 |
| R-PE7 | Cycle detection: handle circular dependencies (A supplies B, B supplies C, C supplies A) without infinite loops | P0 |
| R-PE8 | Configurable minimum impact threshold: don't return entities below X% impact score | P1 |
| R-PE9 | Historical propagation replay: "If this event had happened on date T, what would the impact have been?" | P2 |
| R-PE10 | Support for simultaneous multi-trigger scenarios (two events happening at once) | P2 |

---

## 6. Output Layer Requirements (from Niche Definition)

### 6.1 Dashboard & API

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-OUT1 | REST API returning ranked impact lists in standard JSON format | P0 |
| R-OUT2 | WebSocket for real-time signal stream + propagation results | P0 |
| R-OUT3 | Interactive graph visualization (force-directed layout, filter by entity type, zoom to subgraph) | P1 |
| R-OUT4 | Impact timeline: show how impact scores evolve over hours/days after trigger | P1 |
| R-OUT5 | "What-if" scenario tool: user inputs hypothetical event, sees projected impact | P1 |
| R-OUT6 | Export: CSV, JSON, PDF for impact reports | P1 |
| R-OUT7 | Alert system: configurable triggers (entity X impact score exceeds threshold → notify) | P0 |

### 6.2 Explainability & Audit

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-EXP1 | Every impact score must have a human-readable causal chain explanation | P0 |
| R-EXP2 | Every edge weight change must be traceable to the source signal(s) | P0 |
| R-EXP3 | Confidence scoring on all outputs: "85% confidence based on 12 corroborating signals from 4 sources" | P0 |
| R-EXP4 | Contradiction highlighting: when signals disagree, show both sides | P1 |
| R-EXP5 | Historical accuracy tracking: compare past predictions vs actual outcomes | P1 |
| R-EXP6 | Debug mode: full step-by-step propagation trace for any impact calculation | P0 |

---

## 7. Buyer Profiles & Use Cases (from Niche Definition)

### 7.1 Financial Markets Vertical (6 buyer profiles)

| # | Buyer Profile | Use Case | Willingness to Pay |
|---|--------------|----------|-------------------|
| 1 | **Multi-Strategy Hedge Fund PM** | "TSMC fab fire — show me every portfolio position affected through the supply chain in 60 seconds" | $50K–$200K/yr per seat |
| 2 | **Equity Research Analyst** | "Give me the hidden Tier 2/3 supplier dependencies for NVIDIA that aren't in any filing" | $30K–$80K/yr |
| 3 | **Event-Driven Fund** | "When EU announces China EV battery ban, show me the ranked impact across my watchlist" | $100K–$300K/yr |
| 4 | **Credit Risk Analyst** | "Which of our counterparties have hidden exposure to this bankrupt supplier?" | $40K–$100K/yr |
| 5 | **Portfolio Risk Manager** | "Show me my portfolio's concentration risk through shared Tier 2 suppliers" | $30K–$60K/yr |
| 6 | **Sell-Side Strategist** | "Generate a supply chain contagion analysis for my morning note" | $20K–$50K/yr |

### 7.2 Supply Chain Vertical (6 buyer profiles)

| # | Buyer Profile | Use Case | Willingness to Pay |
|---|--------------|----------|-------------------|
| 7 | **VP Supply Chain, Electronics OEM** | "Which of my Tier 3 suppliers are concentrated in the Taiwan Strait zone?" | $100K–$500K/yr |
| 8 | **Chief Procurement Officer** | "Rank my suppliers by substitution difficulty × geopolitical risk score" | $80K–$300K/yr |
| 9 | **Supply Chain Risk Analyst** | "Alert me when any signal changes the risk score for my critical path suppliers" | $40K–$100K/yr |
| 10 | **Logistics Director** | "Map every chokepoint in my supply chain and show single-point-of-failure risks" | $50K–$150K/yr |
| 11 | **M&A Due Diligence Team** | "Show me the target company's full supplier dependency graph and hidden risks" | $30K–$80K/yr (per engagement) |
| 12 | **Business Continuity Planner** | "Simulate: what happens to our production if Facility X goes offline for 90 days?" | $40K–$100K/yr |

---

## 8. Data Requirements

### 8.1 Seed Data (Phase 1 — Semiconductor Focus)

| Data Category | Count | Source |
|--------------|-------|--------|
| Companies | 500 initial (semiconductor ecosystem) | SEC filings, company databases |
| Relationships | ~5,000 initial edges | Earnings transcripts, trade data, news |
| Products | ~200 key components | Component databases, teardown reports |
| Facilities | ~100 key fabs/facilities | Industry reports, satellite imagery refs |
| Countries | 30 (major manufacturing + regulatory) | Standard reference |
| Regulations | 50 (key trade/tech regulations) | Government sources |

### 8.2 Initial Entity Universe (Semiconductor Demo Case)

**Tier 0 (the trigger):** TSMC
**Tier 1 (direct):** Apple, NVIDIA, AMD, Qualcomm, Broadcom, MediaTek, Intel (as customer)
**Tier 2:** ASML, Applied Materials, Lam Research, Tokyo Electron, KLA Corp
**Tier 3:** Zeiss (optics for ASML), Schott (specialty glass), Entegris (materials), JSR (photoresists)
**Cross-domain:** Cloud providers (AWS, Azure, GCP), major SaaS companies, automotive (NXP, Infineon, Renesas)

### 8.3 Data Source Requirements

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-DS1 | SEC EDGAR: 10-K, 10-Q, 8-K filings — extract supplier mentions, revenue concentration, risk factors | P0 |
| R-DS2 | Earnings call transcripts: extract supplier/customer mentions, capacity commentary, guidance signals | P0 |
| R-DS3 | News APIs: minimum 3 diverse sources (Reuters, Bloomberg syndication, industry-specific) | P0 |
| R-DS4 | Trade data: import/export records for supply chain relationship discovery | P1 |
| R-DS5 | Patent filings: technology dependency and licensing relationship discovery | P2 |
| R-DS6 | Satellite imagery providers: facility monitoring signals (parking lots, shipping volume) | P2 |
| R-DS7 | Social media: Twitter/X, Reddit, WeChat for early signal detection | P1 |
| R-DS8 | Government gazettes: regulatory announcements across major jurisdictions | P1 |

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Req ID | Requirement | Target |
|--------|-------------|--------|
| R-NF1 | Signal ingestion to graph update | <5 minutes |
| R-NF2 | Signal to edge weight adjustment | <30 seconds |
| R-NF3 | Trigger to full propagation result | <60 seconds |
| R-NF4 | Graph query (single entity subgraph) | <2 seconds |
| R-NF5 | Hybrid search (vector + keyword) | <1 second |
| R-NF6 | Dashboard page load | <3 seconds |
| R-NF7 | System uptime | 99.5% (24/7 operation) |
| R-NF8 | Concurrent API users | 100+ |

### 9.2 Security

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-SEC1 | JWT authentication for all API endpoints | P0 |
| R-SEC2 | Role-based access control (admin, analyst, viewer) | P0 |
| R-SEC3 | Prompt injection prevention on all LLM inputs (from MiroFish NER pipeline) | P0 |
| R-SEC4 | Audit log of all graph mutations | P0 |
| R-SEC5 | Data encryption at rest and in transit | P0 |
| R-SEC6 | API rate limiting per user/tier | P0 |
| R-SEC7 | No PII in graph (people tracked as public figures only) | P0 |

### 9.3 Scalability

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-SC1 | Graph: 5,000 nodes → 50,000 nodes without architecture change | P0 |
| R-SC2 | Ingestion: 10,000 articles/day → 100,000/day with horizontal scaling | P1 |
| R-SC3 | Users: 10 → 1,000 concurrent with load balancer | P1 |
| R-SC4 | Multi-tenant: isolated graph views per subscription tier | P1 |

---

## 10. 20 "NEW" Capabilities (from Niche Definition — Zero Commercial Competitors)

These are capabilities where MKG has **no commercial competitor** as of February 2026:

| # | Capability | What It Does |
|---|-----------|-------------|
| 1 | **Dynamic Relationship Weights** | Edge weights update in real-time from live news/signals (not static annual mapping) |
| 2 | **Multi-Hop Propagation Engine** | Cascading impact calculation through 3-4 hops of supply chain |
| 3 | **Causal Chain Explainability** | Full A→B→C→D chain shown for every impact prediction |
| 4 | **Tribal Knowledge Encoding** | Manual expert assertions stored as weighted, time-decaying graph edges |
| 5 | **Temporal Graph Versioning** | Query "state of relationships at any historical date" |
| 6 | **Cross-Domain Intelligence** | Financial + supply chain in a single unified graph |
| 7 | **Contradiction Detection** | When signals disagree on an edge, surface both sides |
| 8 | **Signal-to-Weight Audit Trail** | Every weight change traceable to source signal |
| 9 | **Substitution Difficulty Scoring** | How hard is it to replace Supplier X? scored 0-100 |
| 10 | **Hidden Dependency Discovery** | Automated Tier 2/3/4 supplier detection from filings + transcripts |
| 11 | **Concentration Risk Scoring** | Portfolio-level shared supplier concentration analysis |
| 12 | **Regulatory Intent Tracking** | NLP-tracked progression: exploring → considering → implementing → enforcing |
| 13 | **Geopolitical Risk Overlay** | Geographic risk scores applied to facility/supplier concentration |
| 14 | **Capacity Utilization Intelligence** | Facility-level capacity tracking from multiple signals |
| 15 | **Executive Relationship Network** | Person→Company career paths as hidden influence channels |
| 16 | **Chokepoint Detection** | Automatic identification of single-points-of-failure in supply chains |
| 17 | **What-If Scenario Simulation** | "If Event X happens, what's the impact?" — without the event actually happening |
| 18 | **Backtestable Graph** | Historical graph state enables "would this signal have predicted that outcome?" |
| 19 | **Confidence Calibration** | Track prediction accuracy over time, adjust confidence scoring |
| 20 | **Multi-Language Signal Fusion** | Combine signals from Chinese, Japanese, Korean, European sources into unified graph |

---

## 11. Parallel Graph Integration: MiroFish Simulation Layer

### 11.1 Purpose

MiroFish-Offline runs as a **parallel simulation graph** alongside MKG's knowledge graph. While MKG provides structural relationship intelligence, MiroFish provides **behavioral simulation** — "How would market participants actually react?"

### 11.2 Integration Requirements

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| R-MF1 | MiroFish runs as a separate sidecar service with API boundary (AGPL-3.0 license isolation) | P0 |
| R-MF2 | Shared Neo4j instance with isolated graph_ids (MKG graph_ids vs MiroFish simulation graph_ids) | P1 |
| R-MF3 | Cross-graph entity resolution: MKG entity "TSMC" ↔ MiroFish entity "TSMC" | P1 |
| R-MF4 | Feed MKG propagation events into MiroFish as simulation inputs | P1 |
| R-MF5 | Return MiroFish sentiment evolution results as validation signals for MKG confidence calibration | P2 |
| R-MF6 | Reuse MiroFish GraphStorage abstraction pattern for MKG's graph layer | P0 |
| R-MF7 | Adapt MiroFish NER/RE pipeline for financial entity types (Company, Facility, Regulation) | P0 |
| R-MF8 | Reuse MiroFish hybrid search (0.7 vector + 0.3 BM25) for MKG graph queries | P0 |

### 11.3 Three Integration Use Cases

1. **Signal Validation** — MKG predicts "TSMC disruption → NVIDIA impact -12%, confidence 85%." Feed into MiroFish → simulate 200 market agents reacting → compare sentiment evolution with MKG's prediction → calibrate.

2. **Scenario Planning** — User asks "What if EU bans Chinese EV batteries?" MKG's propagation engine gives supply chain impact. MiroFish simulates market/political agent reactions.

3. **Tribal Knowledge Discovery** — Give MiroFish agents biases matching known tribal patterns → observe if simulation results correlate with historical outcomes → validate tribal knowledge assertions.

### 11.4 Reusable MiroFish Components

| Component | MiroFish File | MKG Reuse |
|-----------|---------------|-----------|
| GraphStorage interface | `storage/graph_storage.py` | Adopt directly — same abstract interface |
| Neo4j implementation | `storage/neo4j_storage.py` | Extend with weight/confidence/propagation fields |
| NER/RE extractor | `storage/ner_extractor.py` | Adapt prompts for financial ontology |
| Hybrid search | `storage/search_service.py` | Adopt — tune weights for financial queries |
| Entity dedup | Neo4j MERGE pattern | Adopt directly |
| Embedding service | `storage/embedding_service.py` | Adopt — may swap embedding model |
| Graph tools (InsightForge) | `services/graph_tools.py` | Adapt — sub-question decomposition is reusable |

---

## 12. Technology Stack

### 12.1 Recommended Stack (leveraging SignalFlow + MiroFish patterns)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Graph DB** | Neo4j CE 5.18+ | MiroFish already has working integration, temporal support, vector indexes |
| **Backend API** | FastAPI (Python 3.11+) | SignalFlow's stack, async, production-ready |
| **Task Queue** | Celery + Redis | SignalFlow's ingestion pipeline — reusable for MKG news pipeline |
| **LLM (NER/RE)** | Claude API (claude-sonnet) + Ollama fallback | Claude for accuracy on financial NER, Ollama for local dev/cost control |
| **Embeddings** | nomic-embed-text (Ollama) or OpenAI ada-002 | MiroFish uses nomic-embed-text (768d), works well for hybrid search |
| **Cache** | Redis | Fast signal dedup, weight caching |
| **RDBMS** | PostgreSQL + TimescaleDB | SignalFlow's existing DB — for user data, audit logs, signal history |
| **Frontend** | Next.js 14 (TypeScript) | SignalFlow's dashboard — extend with graph visualization |
| **Graph Viz** | D3.js force-directed or vis.js | Interactive graph rendering |
| **Alerts** | Telegram + Email + WebSocket | SignalFlow's existing alert system |
| **Monitoring** | Sentry + Prometheus | SignalFlow's existing monitoring |
| **Deployment** | Docker Compose (dev), Railway (prod) | SignalFlow's existing deployment |

### 12.2 Dual Database Architecture

```
┌─────────────┐     ┌─────────────┐
│  Neo4j CE   │     │ PostgreSQL  │
│             │     │ + TimescaleDB│
│ Knowledge   │     │             │
│ Graph       │     │ Users       │
│ Entities    │     │ Audit logs  │
│ Edges       │     │ Signals     │
│ Weights     │     │ Predictions │
│ Embeddings  │     │ Accuracy    │
│ Temporal    │     │ API keys    │
│ Snapshots   │     │ Subscriptions│
└─────────────┘     └─────────────┘
```

---

## 13. Phase Plan (Recommended Build Sequence)

### Phase 1: Graph Foundation (Weeks 1-4)
- Neo4j setup with MKG schema (6 node types, 7 edge types)
- GraphStorage abstraction (adapted from MiroFish)
- Seed 500 semiconductor entities with manual data
- Basic Cypher queries: subgraph retrieval, neighbor traversal
- Entity CRUD API endpoints
- **Exit criteria:** Can query "show me all TSMC suppliers" and get correct results

### Phase 2: News Ingestion + NER/RE (Weeks 5-8)
- News fetcher pipeline (adapt SignalFlow's Celery task pattern)
- Financial NER/RE (adapt MiroFish's NER extractor with financial ontology)
- Entity deduplication and canonical name resolution
- Signal extraction: sentiment, magnitude, entity mentions
- **Exit criteria:** 100 articles/day automatically creating/updating graph edges

### Phase 3: Weight Adjustment (Rule-Based) (Weeks 9-12)
- Rule-based WAN: signal → edge weight delta calculation
- Weight audit trail (every change logged with source)
- Weight decay functions (configurable half-life)
- Contradiction detection
- **Exit criteria:** Edge weights change in response to real news signals with full traceability

### Phase 4: Propagation Engine (Weeks 13-16)
- BFS/DFS traversal with impact attenuation
- Cycle detection
- Causal chain construction
- Ranked impact list output
- **Exit criteria:** "TSMC fab fire" → ranked impact list across 50+ entities in <60 seconds

### Phase 5: Temporal Versioning + Explainability (Weeks 17-20)
- Daily graph snapshots
- Historical graph state queries
- Full causal chain explainability for every prediction
- Confidence scoring with historical accuracy tracking
- **Exit criteria:** Can query "what did the TSMC supply chain look like 30 days ago"

### Phase 6: Dashboard + Alerts + MiroFish Integration (Weeks 21-24)
- Graph visualization (interactive force-directed)
- Alert rules engine
- MiroFish sidecar deployment
- What-if scenario tool
- **Exit criteria:** End-to-end demo: event trigger → graph update → propagation → dashboard → alert

---

## 14. What MKG Is NOT (Boundaries from Niche Definition)

- ❌ **Not a Bloomberg Terminal competitor** — MKG doesn't provide raw market data (prices, quotes, trades)
- ❌ **Not an NLP news sentiment tool** — MKG doesn't just score articles; it maps entities to graph edges
- ❌ **Not a static supply chain mapper** — MKG's graph is dynamic, updated continuously
- ❌ **Not a trading system** — MKG provides intelligence, not trade execution
- ❌ **Not a general-purpose knowledge graph** — MKG is specifically for financial + supply chain relationships
- ❌ **Not an AI chatbot** — MKG answers structured queries over a knowledge graph, not general conversation
- ❌ **Not a consulting service** — MKG is a software product, not custom analysis

---

## 15. Success Metrics

| Metric | Target (Year 1) |
|--------|-----------------|
| Entities in graph | 5,000+ |
| Edges in graph | 50,000+ |
| Signal ingestion volume | 10,000 articles/day |
| Propagation latency | <60 seconds |
| Prediction accuracy (hit rate) | >65% |
| Daily active users | 50+ analysts |
| Revenue | $500K ARR (10 enterprise customers) |
| Historical accuracy tracking | 90-day rolling calibration |

---

*This document synthesizes requirements from 7 MKG research documents (20,000+ words of analysis) and the MiroFish-Offline codebase review into a single actionable specification.*
