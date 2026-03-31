# MKG — System Requirements Document (SRD)

> **Version:** 1.0  
> **Date:** 31 March 2026  
> **Status:** Expert-Reviewed (10 iterations, 10 domain experts)  
> **Source Documents:** `core/MKG_REQUIREMENTS.md`, Expert Panel Iterations 1–10  
> **Total Requirements:** 303 (120 original + 183 expert-contributed)  
> **Beachhead MVP Requirements:** 20

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Expert Panel Summary](#2-expert-panel-summary)
3. [Top 10 Showstoppers](#3-top-10-showstoppers)
4. [Beachhead MVP — 20 Requirements](#4-beachhead-mvp--20-requirements)
5. [Full Requirements Catalog](#5-full-requirements-catalog)
   - 5.1 [Intelligence Agent (NER/RE Pipeline)](#51-intelligence-agent--nerro-pipeline)
   - 5.2 [Knowledge Graph](#52-knowledge-graph)
   - 5.3 [Weight Adjustment Network](#53-weight-adjustment-network)
   - 5.4 [Propagation Engine](#54-propagation-engine)
   - 5.5 [Output & Explainability](#55-output--explainability)
   - 5.6 [NLP Pipeline Quality](#56-nlp-pipeline-quality)
   - 5.7 [Graph Architecture](#57-graph-architecture)
   - 5.8 [Data Pipeline & Reliability](#58-data-pipeline--reliability)
   - 5.9 [Security & Compliance](#59-security--compliance)
   - 5.10 [Product & Go-to-Market](#510-product--go-to-market)
   - 5.11 [Visualization & UX](#511-visualization--ux)
   - 5.12 [Competitive & Moat Strategy](#512-competitive--moat-strategy)
   - 5.13 [Platform & Infrastructure](#513-platform--infrastructure)
   - 5.14 [Supply Chain Vertical](#514-supply-chain-vertical)
   - 5.15 [Portfolio & Financial Integration](#515-portfolio--financial-integration)
   - 5.16 [Data Sources & Coverage](#516-data-sources--coverage)
   - 5.17 [Tribal Knowledge](#517-tribal-knowledge)
   - 5.18 [Non-Functional Requirements](#518-non-functional-requirements)
   - 5.19 [MiroFish Integration](#519-mirofish-integration)
6. [Risk Matrix](#6-risk-matrix)
7. [Revised Timeline](#7-revised-timeline)
8. [Cost Model](#8-cost-model)
9. [Strategic Decisions Required](#9-strategic-decisions-required)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

### Product

**Market Knowledge Graph (MKG)** is a dynamic relationship intelligence system that continuously maps, weights, and traverses hidden connections between global entities — delivering ranked impact predictions with causal chains in under 60 seconds.

**Core Promise:** When Event X happens, MKG tells you: Who gets hit? How hard? In what direction? Through what chain? With what confidence? — before anyone else connects the dots.

### Expert Panel Verdict

**BUILD — but not as currently specified.**

The Speed 3 market gap is real and validated. The semiconductor beachhead is correct. The propagation engine concept is sound. But the original specification describes a 24-week build plan for a product that requires 52+ weeks, $500K–$1.1M in capital, and ~300 requirements — of which only 20 should be in a beachhead MVP.

### Key Numbers

| Metric | Value |
|--------|-------|
| Expert panel average score | 4.3/10 (specification quality, not concept quality) |
| Original requirements | ~120 across 60+ R-IDs |
| Expert-contributed new requirements | 183 (99 at P0) |
| Total consolidated requirements | ~303 |
| Beachhead MVP requirements | 20 |
| Realistic time to first revenue | 37–42 weeks |
| Realistic time to $500K ARR | 18–24 months |
| Year 1 infrastructure cost | $122K–$149K (at 10 clients) |
| Year 1 Claude API cost (dominant) | $108K–$120K (75–80% of infra) |
| Year 1 revenue (realistic) | $53K–$138K |
| Funding requirement | $500K–$1M seed round |

---

## 2. Expert Panel Summary

### Panel Composition

| # | Expert | Domain | Score | Key Finding |
|---|--------|--------|-------|-------------|
| 1 | Marcus Chen | Hedge Fund PM (20yr, $5B AUM) | 7/10 | Portfolio overlay missing; backtesting must be P0; SOM 10–50x overstated |
| 2 | Dr. Priya Sharma | VP Supply Chain Risk, Top-5 Automotive OEM | 6/10 | No BOM-level granularity; no disruption duration; cross-domain data isolation is dealbreaker |
| 3 | Dr. Kai Müller | Graph DB Architect, ex-Neo4j | 5/10 | Neo4j CE can't deliver 5+ requirements (RBAC, HA, backup, multi-DB, multi-tenant); temporal versioning unspecified; Decimal impossible in Neo4j |
| 4 | Dr. Aisha Ibrahim | NLP/NER Scientist, ex-Reuters/Two Sigma | 4/10 | Tail entity NER 60–75% F1; RE 65–75% F1; 4-hop all-correct ~24%; LLM hallucination 8–15%; 13-language NER is multi-year; NLP costs ~$10K/month |
| 5 | Megan Torres | Enterprise PM, ex-Palantir/Databricks | 3/10 | Dual-vertical is startup killer; no GTM strategy; no MVP defined; $500K Y1 ARR is fantasy (realistic: $50K–$150K); pricing unvalidated |
| 6 | James Wright | CISO, ex-Goldman Sachs | 4/10 | SOC 2 + SSO non-negotiable for institutional sales; cross-tenant data = insider trading liability; LLM data leakage blocks institutional sales; GDPR issues with Person entities |
| 7 | Ethan Kowalski | Data Pipeline Architect, ex-Netflix/Stripe | 4/10 | No pipeline topology; at-most-once delivery unacceptable; Claude API $10K/month bottleneck; no DLQ, backpressure, or observability |
| 8 | Yuki Tanaka | Financial UX Designer, ex-Bloomberg | 4/10 | No information hierarchy; D3.js can't render 5K+ nodes (WebGL mandatory); no user workflow mapping; no keyboard navigation |
| 9 | Sophia Nakamura | Competitive Intel, ex-Bloomberg/AlphaSense | 3/10 | Zero durable moat; Bloomberg "Cascade" project evaluated same gap; technology replicable in 24–36 months; distribution strategy absent |
| 10 | Rajesh Krishnamurthy | Platform Engineer, ex-AWS/Stripe | 3/10 | Multi-tenancy unspecified; infra costs $122K–$149K/yr; Year 1 gap $525K–$839K costs vs $53K–$138K revenue; no CI/CD or DR plan |

### Score Pattern

Scores decline from user perspective (7/10) to builder perspective (3/10). The closer an expert is to implementation reality, the more gaps they find. **The concept is strong; the specification is inadequate.**

### Requirements Contribution

| Iteration | Expert(s) | New Requirements | Critical (P0) |
|-----------|-----------|-----------------|---------------|
| 1–2 | Hedge Fund PM + Supply Chain VP | 30 | 15 |
| 3–4 | Graph DB Architect + NLP Scientist | 32 | 19 |
| 5–6 | Enterprise PM + CISO | 47 | 28 |
| 7–8 | Pipeline Architect + UX Designer | 36 | 18 |
| 9–10 | Competitive Intel + Platform Engineer | 38 | 19 |
| **Total** | **10 experts** | **183** | **99** |

---

## 3. Top 10 Showstoppers

Ranked by Severity × Likelihood. **Each must be resolved before or during the beachhead MVP.**

| Rank | Showstopper | Expert(s) | Impact If Unresolved |
|------|-------------|-----------|---------------------|
| **1** | **No competitive moat** — technology is replicable, data is public, zero network effects | Sophia (9) | Bloomberg or AlphaSense replicates within 24–36 months; MKG loses all clients |
| **2** | **No go-to-market strategy** — product exists but nobody knows, sales cycle unplanned, zero distribution | Megan (5), Sophia (9) | Product built, nobody buys it, runway exhausted |
| **3** | **Investment adviser classification unresolved** — portfolio overlay + personalized alerts may require SEC registration | James (6) | Federal crime if unregistered; product scope must change if registration required |
| **4** | **NLP accuracy fundamentally insufficient** — 4-hop all-correct ~24%, RE at 65–75% F1, hallucination 8–15% | Aisha (4) | Graph filled with incorrect relationships; propagation results wrong; clients lose trust |
| **5** | **Claude API: single vendor dependency** at $108K–$120K/yr, no fallback, 75–80% of infrastructure cost | Ethan (7), Rajesh (10) | Anthropic price increase, API outage, or policy change threatens entire business |
| **6** | **Institutional procurement gates missing** — no SOC 2, no SSO, no penetration test report | James (6), Rajesh (10) | Every enterprise sales process terminates at security questionnaire |
| **7** | **Year 1 financial gap** — $525K–$839K costs vs $53K–$138K revenue | Megan (5), Rajesh (10) | Business runs out of money before reaching product-market fit |
| **8** | **Pipeline has no reliability guarantees** — at-most-once delivery, no DLQ, no observability, no backpressure | Ethan (7) | Articles silently lost; graph has invisible holes; impossible to detect or repair |
| **9** | **Multi-tenancy undesigned** — one missing WHERE clause = tribal knowledge leak between competing hedge funds | Kai (3), James (6), Rajesh (10) | Client trust destroyed; legal liability; career-ending for client compliance officers |
| **10** | **24-week plan produces a demo, not a product** — first revenue at Month 15–18, not Month 6 | Megan (5), Sophia (9), Rajesh (10) | Expectations misaligned; investor/stakeholder disappointment |

---

## 4. Beachhead MVP — 20 Requirements

**Target buyer:** Event-Driven Hedge Fund PM ($500M–$5B AUM)  
**Target price:** $30K–$50K/year  
**Target timeline:** 42 weeks to first paid client  
**Vertical:** Financial Markets only (semiconductor beachhead)

### What's IN (20 requirements)

| # | Requirement | Source | Rationale |
|---|-------------|--------|-----------|
| 1 | Semiconductor entity graph: 500 companies, 5,000 edges | R-KG1, R-KG2, R-KG3 | Minimum graph for useful propagation |
| 2 | English-only NER/RE from SEC filings + earnings transcripts + 5 news sources | R-IA1 (scoped), R-IA3, R-IA4 | English only, 5 sources (not 50) |
| 3 | Entity deduplication (canonical name resolution) | R-IA5, R-KG7, R-NLP-5 | Graph integrity depends on entity resolution |
| 4 | Edge weight 0.0–1.0 with confidence and source tracking | R-KG4 | Core data model for propagation quality |
| 5 | Rule-based weight adjustment (no GAT) | R-WAN1, R-WAN2 | Interpretable, debuggable, shippable in weeks |
| 6 | Propagation engine: trigger → ranked impact list, 4 hops, <60 seconds | R-PE1–R-PE3, R-PE6 | Core product value — this is the sale |
| 7 | Causal chain explainability per impacted entity | R-PE5, R-EXP1 | Non-negotiable for PM trust and compliance |
| 8 | At-least-once pipeline delivery with DLQ | R-PIPE-3, R-PIPE-9 | Data integrity — no silent article loss |
| 9 | Claude API cost governance + fallback extraction | R-PIPE-6, R-PIPE-7 | Business survival — cannot allow unbounded API spend |
| 10 | Durable article storage (2-year retention) | R-PIPE-18 | Data moat starts accumulating from day 1 |
| 11 | REST API with versioning, pagination, error format | R-OUT1, R-PLAT-5 | Quant integration — the stickiest deployment pattern |
| 12 | Webhook delivery for propagation events | R-PLAT-6 | Core alert mechanism for API-integrated clients |
| 13 | Ranked impact table as primary view (not graph viz) | R-VIZ-1, R-VIZ-2 | Table-first: 80% of usage is levels 1–3 information density |
| 14 | Accuracy tracking from day 1 | R-COMP-3, R-EXP5 | Moat building — after 12 months, unreplicable |
| 15 | Tribal knowledge input (manual expert assertions) | R-TK1, R-TK2, R-TK5 | Switching cost + data moat — private only in v1 |
| 16 | JWT authentication + tenant isolation (hybrid model) | R-SEC1, R-PLAT-1 | Enterprise security minimum |
| 17 | Automated backup + disaster recovery | R-PLAT-8, R-PLAT-9 | Operational survival |
| 18 | CI/CD pipeline with zero-downtime deployment | R-PLAT-11, R-PLAT-12 | 24/7 reliability without manual deployment risk |
| 19 | Pipeline observability (15+ metrics + health dashboard) | R-PIPE-10 | Operational awareness — detect failures before clients do |
| 20 | Alert system: configurable propagation event triggers | R-OUT7 | Core user-facing feature — PM sets watchlist, gets notified |

### What's OUT (defer to v2+)

| Feature | Original Priority | Why Cut |
|---------|-------------------|---------|
| Graph visualization (force-directed / WebGL) | P1 | 3–4 months engineering; 80% of usage is tables |
| What-if scenario simulation | P1 | Complex UX + unreliable without calibration data |
| Temporal versioning (query graph at time T) | P0 | 3–6 month project (Expert #3); defer to v2 |
| Multilingual NER (13 languages) | P0/P1 | Multi-year NLP effort; English-only for beachhead |
| GAT-based weight adjustment (Layer 3 ML) | P2 | Rule-based sufficient and interpretable for v1 |
| 10,000 articles/day ingestion | P1 | Start with 1,000/day; scale when pipeline proven |
| MiroFish simulation layer | P0–P2 | Separate product; adds complexity without core value |
| Supply chain vertical features | Various | Financial markets is beachhead; supply chain is v2 |
| SSO/SAML | P0 | Required for enterprise; first 5 clients use JWT; add at client #6 |
| SOC 2 certification | P0 | Start process during MVP; complete during v2 |
| Excel/Sheets/Slack integrations | P1 | Not launch-blocking; add by Month 9 |
| Portfolio overlay | P0 (Expert #1) | Defer until investment adviser status legally resolved |
| Community knowledge layer | P1 | Requires 10+ clients contributing; add when base supports it |
| On-prem deployment support | P2 | Architecture allows it; don't build until demanded |

---

## 5. Full Requirements Catalog

### Priority Key

| Priority | Meaning |
|----------|---------|
| **P0** | Must have for MVP / beachhead launch |
| **P1** | Required within 6 months of launch (v1.1–v1.3) |
| **P2** | Required within 12–18 months (v2.0+) |
| **P3** | Nice-to-have / research |

### Source Key

| Prefix | Source |
|--------|--------|
| R-IA, R-KG, R-WAN, R-PE, R-OUT, R-EXP, R-SEC, R-NF, R-SC, R-DS, R-TK, R-MF | Original MKG_REQUIREMENTS.md |
| R-PORT, R-BT, R-DQ, R-LIQ, R-LAT, R-FP, R-ATT | Expert #1 (Hedge Fund PM) |
| R-PROD, R-DUR, R-MIT, R-INT, R-GEO, R-COMP (supply chain), R-FIN, R-INV | Expert #2 (Supply Chain VP) |
| R-GRAPH-1 through R-GRAPH-12 | Expert #3 (Graph DB Architect) |
| R-NLP-1 through R-NLP-20 | Expert #4 (NLP/NER Scientist) |
| R-PM-1 through R-PM-15 | Expert #5 (Enterprise PM) |
| R-SEC-8 through R-SEC-39 | Expert #6 (CISO) |
| R-PIPE-1 through R-PIPE-21 | Expert #7 (Pipeline Architect) |
| R-VIZ-1 through R-VIZ-15 | Expert #8 (UX Designer) |
| R-COMP-1 through R-COMP-15 | Expert #9 (Competitive Intel) |
| R-PLAT-1 through R-PLAT-23 | Expert #10 (Platform Engineer) |

---

### 5.1 Intelligence Agent — NER/RE Pipeline

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-IA1 | Ingest news from 50+ sources across 13 languages | P2 | ❌ Scoped to 5 English sources for MVP | Original |
| R-IA2 | Support source types: news, SEC filings, earnings transcripts, press releases, social media, trade data | P0 | ✅ (filings + transcripts + 5 news only) | Original |
| R-IA3 | NER for: Company, Person, Product, Facility, Country, Regulation | P0 | ✅ | Original |
| R-IA4 | RE for: SUPPLIES_TO, COMPETES_WITH, MANUFACTURES_AT, REGULATES, INVESTS_IN, PARTNERS_WITH, DEPENDS_ON | P0 | ✅ (3 types MVP: SUPPLIES_TO, DEPENDS_ON, COMPETES_WITH) | Original |
| R-IA5 | Entity deduplication across sources (canonical name resolution) | P0 | ✅ | Original |
| R-IA6 | News article deduplication (same event, different sources) | P0 | ✅ | Original |
| R-IA7 | Extract sentiment and impact magnitude from each signal | P0 | ✅ | Original |
| R-IA8 | Extract temporal information (when did/will event happen) | P1 | ❌ | Original |
| R-IA9 | Multilingual NER/RE — EN, ZH-CN, ZH-TW, JA, KO, DE, FR | P2 | ❌ English-only for beachhead | Original |
| R-IA10 | Process minimum 10,000 articles/day at steady state | P1 | ❌ Start at 500–1,000/day | Original |
| R-IA11 | Max latency from article publication to graph update: 5 minutes | P0 | ✅ | Original |
| R-IA12 | Source credibility scoring (Reuters > random blog) | P1 | ❌ | Original |
| R-IA13 | Prompt injection prevention on all LLM-processed inputs | P0 | ✅ | Original |
| R-IA14 | RSS, API, and web scraping ingestion methods | P0 | ✅ | Original |

### 5.2 Knowledge Graph

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-KG1 | Graph database: Neo4j (leveraging MiroFish patterns) | P0 | ✅ | Original |
| R-KG2 | Support 5,000 entity nodes at launch, scalable to 50,000+ | P0 | ✅ (500 for MVP) | Original |
| R-KG3 | Support 50,000 relationship edges at launch, scalable to 500,000+ | P0 | ✅ (5,000 for MVP) | Original |
| R-KG4 | Every edge: weight (0.0–1.0), confidence, source, last_updated, valid_from, valid_until | P0 | ✅ | Original |
| R-KG5 | Temporal versioning — query "state of graph at time T" | P1 | ❌ 3–6 month project | Original |
| R-KG6 | Graph snapshots at minimum daily granularity | P1 | ❌ | Original |
| R-KG7 | Entity dedup by canonical name (MERGE on insert) | P0 | ✅ | Original |
| R-KG8 | Hybrid search: vector similarity + BM25, configurable weights | P0 | ✅ | Original |
| R-KG9 | Edge provenance: every weight change records source, timestamp, old/new weight | P0 | ✅ | Original |
| R-KG10 | Manual expert assertions alongside automated signals | P0 | ✅ | Original |
| R-KG11 | All financial values as Decimal, never float | P0 | ✅ (see R-GRAPH-5 for implementation) | Original |
| R-KG12 | Ontology stored per graph (extensible types) | P1 | ❌ | Original |
| R-KG13 | Full graph export/import for backup and migration | P1 | ❌ | Original |
| R-KG14 | Embedding vectors on nodes and edges for semantic search | P0 (nodes) / P2 (edges) | ✅ Nodes only | Original |

### 5.3 Weight Adjustment Network

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-WAN1 | Input: signal event → Output: set of edge weight deltas | P0 | ✅ | Original |
| R-WAN2 | Phase 1: Rule-based weight adjustment | P0 | ✅ | Original |
| R-WAN3 | Phase 2: GAT-based weight adjustment (learned) | P2 | ❌ | Original |
| R-WAN4 | Weight changes logged with full audit trail | P0 | ✅ | Original |
| R-WAN5 | Configurable decay function for edge weights | P1 | ❌ | Original |
| R-WAN6 | Contradiction handling (latest wins, average, credibility-weighted) | P1 | ❌ | Original |
| R-WAN7 | Max latency: signal receipt to all edge weights updated: 30 seconds | P0 | ✅ | Original |
| R-WAN8 | "Shock events" — immediate weight adjustment bypassing pipeline | P1 | ❌ | Original |

### 5.4 Propagation Engine

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PE1 | Input: trigger entity + event type + magnitude → Output: ranked impacted entities | P0 | ✅ | Original |
| R-PE2 | Max propagation depth: configurable, default 4 hops | P0 | ✅ | Original |
| R-PE3 | Impact attenuation: edge weight × attenuation factor (default 0.7/hop) | P0 | ✅ | Original |
| R-PE4 | Direction-aware: positive vs negative impact | P0 | ✅ | Original |
| R-PE5 | Full causal chain for every impacted entity | P0 | ✅ | Original |
| R-PE6 | Latency: trigger → full ranked list in <60 seconds | P0 | ✅ | Original |
| R-PE7 | Cycle detection (handle circular dependencies) | P0 | ✅ | Original |
| R-PE8 | Configurable minimum impact threshold | P1 | ❌ | Original |
| R-PE9 | Historical propagation replay ("if event on date T...") | P1 (upgraded from P2) | ❌ | Original + Expert #1 |
| R-PE10 | Simultaneous multi-trigger scenarios | P2 | ❌ | Original |

### 5.5 Output & Explainability

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-OUT1 | REST API returning ranked impact lists in JSON | P0 | ✅ | Original |
| R-OUT2 | WebSocket for real-time signal stream + propagation results | P1 | ❌ | Original |
| R-OUT3 | Interactive graph visualization | P2 | ❌ | Original |
| R-OUT4 | Impact timeline (scores evolving over time) | P1 | ❌ | Original |
| R-OUT5 | "What-if" scenario tool | P2 | ❌ | Original |
| R-OUT6 | Export: CSV, JSON, PDF | P1 | ❌ | Original |
| R-OUT7 | Alert system with configurable triggers | P0 | ✅ | Original |
| R-EXP1 | Every impact score has human-readable causal chain | P0 | ✅ | Original |
| R-EXP2 | Every weight change traceable to source signal(s) | P0 | ✅ | Original |
| R-EXP3 | Confidence scoring on all outputs | P0 | ✅ | Original |
| R-EXP4 | Contradiction highlighting | P1 | ❌ | Original |
| R-EXP5 | Historical accuracy tracking (compare predictions vs outcomes) | P0 (upgraded from P1) | ✅ | Original + Experts #1, #9 |
| R-EXP6 | Debug mode: step-by-step propagation trace | P0 | ✅ | Original |

### 5.6 NLP Pipeline Quality

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-NLP-1 | NER minimum F1 targets per entity type: Company ≥85%, Product ≥70%, Facility ≥65%, Person ≥80%, Country ≥90%, Regulation ≥65% | P0 | ✅ | Expert #4 |
| R-NLP-2 | Entity-type-specific accuracy dashboard (precision, recall, F1 per type/lang/source — updated weekly) | P1 | ❌ | Expert #4 |
| R-NLP-3 | RE minimum F1 targets per relation type. DEPENDS_ON ≥60% before inclusion in propagation. Below-target flagged "low confidence" | P0 | ✅ | Expert #4 |
| R-NLP-4 | Human-in-the-loop validation for extracted relations below confidence 0.7 | P1 | ❌ | Expert #4 |
| R-NLP-5 | Entity disambiguation priority: (1) ticker/ISIN/LEI, (2) canonical alias table, (3) embedding similarity ≥0.92, (4) fuzzy match with manual confirm | P0 | ✅ | Expert #4 |
| R-NLP-6 | Canonical entity registry: all known aliases, tickers, identifiers, cross-lingual mappings. Manually curated for initial 500 entities | P0 | ✅ | Expert #4 |
| R-NLP-7 | Track entity merge/split events (Facebook→Meta, HP split) with identity chains | P1 | ❌ | Expert #4 |
| R-NLP-8 | LLM-extracted entities validated against source text via span-level verification. Unverified → flagged "inferred" | P0 | ✅ | Expert #4 |
| R-NLP-9 | LLM-extracted relations must include supporting sentence(s). No evidence → "inferred", decay 3x faster | P0 | ✅ | Expert #4 |
| R-NLP-10 | Track hallucination rate per entity type, relation type, LLM model, language. Monthly 200-article human sample | P1 | ❌ | Expert #4 |
| R-NLP-11 | Monthly NLP pipeline cost budget with breakdown by NER/RE, sentiment, disambiguation, signal extraction | P0 | ✅ | Expert #4 |
| R-NLP-12 | LLM routing strategy: Claude for high-value/ambiguous, Ollama for low-priority/clear-cut. Criteria: language, source credibility, entity novelty | P1 | ❌ | Expert #4 |
| R-NLP-13 | NER evaluation dataset: 1,000+ manually annotated articles for benchmarking | P0 | ✅ (500 for MVP) | Expert #4 |
| R-NLP-14 | RE evaluation dataset: 500+ annotated relation pairs | P0 | ✅ (200 for MVP) | Expert #4 |
| R-NLP-15 | Evaluation cadence: monthly re-evaluation against test set; automated regression detection | P1 | ❌ | Expert #4 |
| R-NLP-16 | Cross-lingual entity resolution: match same entity across languages (TSMC = 台積電) | P2 | ❌ | Expert #4 |
| R-NLP-17 | Financial terminology dictionary for extraction improvement (industry-specific terms) | P1 | ❌ | Expert #4 |
| R-NLP-18 | Confidence score per extracted entity and relation (not just per article) | P0 | ✅ | Expert #4 |
| R-NLP-19 | Batch processing with context: multiple articles about same event in single LLM call for cross-article entity resolution | P1 | ❌ | Expert #4 |
| R-NLP-20 | Error classification taxonomy: distinguish missing entities, wrong entities, wrong relations, hallucinated entities, hallucinated relations | P1 | ❌ | Expert #4 |

### 5.7 Graph Architecture

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-GRAPH-1 | Document Neo4j edition decision (CE vs Enterprise vs Aura) with requirement mapping per edition. CE workarounds for RBAC, online backup, graph isolation, HA | P0 | ✅ | Expert #3 |
| R-GRAPH-2 | Specify temporal versioning approach (bitemporal vs snapshot vs event sourcing) with trade-off documentation | P0 | ✅ (decision doc; implementation P1) | Expert #3 |
| R-GRAPH-3 | Temporal data retention policy: duration, storage cost model, purge strategy | P1 | ❌ | Expert #3 |
| R-GRAPH-4 | Edge weight audit trail in PostgreSQL (not Neo4j). Neo4j edges: current-state only | P0 | ✅ | Expert #3 |
| R-GRAPH-5 | Financial values as integers in minor units (cents/basis points) in Neo4j, or exclusively in PostgreSQL | P0 | ✅ | Expert #3 |
| R-GRAPH-6 | Edge embedding storage: reify edges as nodes OR use PostgreSQL+pgvector. Node embeddings P0; edge embeddings P2 | P0 | ✅ (node embeddings only) | Expert #3 |
| R-GRAPH-7 | Consistency model for concurrent reads during weight updates. Propagation queries see consistent weight snapshot | P0 | ✅ | Expert #3 |
| R-GRAPH-8 | Neo4j memory allocation plan at 5K, 50K, 500K node scales (JVM heap, page cache, vector index) | P1 | ❌ | Expert #3 |
| R-GRAPH-9 | Entity matching strategy for MERGE: exact match fields, fuzzy threshold, cross-language canonical form, identifier priority (ticker > LEI > name) | P0 | ✅ | Expert #3 |
| R-GRAPH-10 | Neo4j index design: which labels get which index types (range, text, full-text, vector, point). Document count and size | P1 | ❌ | Expert #3 |
| R-GRAPH-11 | Schema evolution strategy: new node/edge types, data migration, temporal history compatibility | P1 | ❌ | Expert #3 |
| R-GRAPH-12 | Bulk data loading strategy for seed phase (Admin Import vs LOAD CSV vs APOC batch) with expected times | P1 | ❌ | Expert #3 |

### 5.8 Data Pipeline & Reliability

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PIPE-1 | Explicit pipeline topology document: every stage, I/O schemas, failure mode, retry policy, ordering, concurrency | P0 | ✅ | Expert #7 |
| R-PIPE-2 | Pipeline DAG with typed channels. Each channel: message schema, serialization, max size, TTL | P0 | ✅ | Expert #7 |
| R-PIPE-3 | Source→extraction must guarantee at-least-once processing. No silent drops. Failed → DLQ | P0 | ✅ | Expert #7 |
| R-PIPE-4 | Graph mutation idempotent. Same extraction twice → no corruption. Key: (article_id, entity_pair, relation_type) | P0 | ✅ | Expert #7 |
| R-PIPE-5 | Pipeline replay: reprocess articles from time range (for model improvements, backfills, outages). Requires durable article storage | P1 | ❌ | Expert #7 |
| R-PIPE-6 | LLM extraction stage: rate-aware scheduler with priority queue, admission control, circuit breaker, daily cost accumulator with fallback | P0 | ✅ | Expert #7 |
| R-PIPE-7 | Fallback extraction mode (no Claude): regex/rule-based for top 500 known entities, XBRL from filings, headline keywords for sentiment | P0 | ✅ | Expert #7 |
| R-PIPE-8 | Request coalescing: batch articles about same event within 5-minute window into single Claude call | P1 | ❌ | Expert #7 |
| R-PIPE-9 | DLQ per pipeline stage: original payload, stage, failure reason, timestamp, retry count, source metadata. Queryable + manual reprocess | P0 | ✅ | Expert #7 |
| R-PIPE-10 | Pipeline health dashboard (real-time): articles/source/hour, extraction success/fail rate, latency p50/p95/p99, DLQ depth, Claude spend, graph mutation throughput, e2e latency. ≥15 metrics | P0 | ✅ | Expert #7 |
| R-PIPE-11 | Backpressure between stages. Extraction can't keep up → ingestion reduces polling. Graph mutation slow → extraction buffers durably | P0 | ✅ | Expert #7 |
| R-PIPE-12 | Max queue depth per stage with alerts at 50%/80%/100%. At 100% → admission control (drop lowest-priority first) | P1 | ❌ | Expert #7 |
| R-PIPE-13 | Per-entity ordering: articles mentioning same entity processed in publication-timestamp order. Cross-entity ordering not required | P1 | ❌ | Expert #7 |
| R-PIPE-14 | Claude API cost governance: daily/monthly budget with kill switch. Tiered extraction budget allocation. Cost-per-article tracking | P0 | ✅ | Expert #7 |
| R-PIPE-15 | Article deduplication using embedding similarity (>0.95 cosine = duplicate). Dedup before LLM extraction to save cost | P0 | ✅ | Expert #7 |
| R-PIPE-16 | Source registry: per-source health tracking, schedule, last success, error rate, circuit breaker. Unhealthy → skip + alert | P1 | ❌ | Expert #7 |
| R-PIPE-17 | Extraction result schema (Pydantic): entities[], relations[], sentiment, confidence, source_sentences[]. Validated before graph write | P0 | ✅ | Expert #7 |
| R-PIPE-18 | Durable article storage: every processed article stored with metadata (source, timestamp, extraction results, processing status). 2-year retention minimum | P0 | ✅ | Expert #7 |
| R-PIPE-19 | PipelineStage interface: abstract class with process(), health_check(), metrics(). Each stage independently deployable and testable | P1 | ❌ | Expert #7 |
| R-PIPE-20 | Tiered extraction: Tier 1 (Claude) for top-credibility sources + novel entities; Tier 2 (Ollama/local) for routine/known entities; Tier 3 (regex) for structured data | P1 | ❌ | Expert #7 |
| R-PIPE-21 | Monthly pipeline cost report: per-source ingestion cost, per-article extraction cost, per-entity graph mutation cost. Track cost-per-insight | P1 | ❌ | Expert #7 |

### 5.9 Security & Compliance

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-SEC1 | JWT authentication for all API endpoints | P0 | ✅ | Original |
| R-SEC2 | Role-based access control (admin, analyst, viewer) | P0 | ✅ (app-level on CE) | Original |
| R-SEC3 | Prompt injection prevention on all LLM inputs | P0 | ✅ | Original |
| R-SEC4 | Audit log of all graph mutations | P0 | ✅ | Original |
| R-SEC5 | Encryption at rest and in transit | P0 | ✅ | Original |
| R-SEC6 | API rate limiting per user/tier | P0 | ✅ | Original |
| R-SEC7 | No PII in graph (public figures only) | P0 | ✅ | Original |
| R-SEC-8 | SOC 2 Type I within 6 months of first deployment. Type II within 18 months | P0 (start process during MVP) | ❌ (complete during v2) | Expert #6 |
| R-SEC-9 | Annual penetration test by qualified third-party. Report shareable under NDA | P0 | ❌ (first test pre-launch) | Expert #6 |
| R-SEC-10 | Formal Information Security Policy (access management, data classification, IR, vulnerability mgmt, change mgmt, BC, vendor mgmt, acceptable use) | P0 | ✅ (document) | Expert #6 |
| R-SEC-11 | Investment adviser classification: obtain legal opinion on whether portfolio overlay + personalized alerts triggers SEC 202 registration | P0 | ✅ (legal opinion before build) | Expert #6 |
| R-SEC-12 | All LLM prompts treated as confidential. Claude API calls must not include client portfolio data or proprietary tribal knowledge unless contractually permitted | P0 | ✅ | Expert #6 |
| R-SEC-13 | Cross-tenant data isolation: financial client data never enriches supply chain client intelligence and vice versa | P0 | ✅ | Expert #6 |
| R-SEC-14 | Terms of service: explicitly disclaim MKG as investment advice. SEC/FCA-compliant disclaimers. Legal review before customer deployment | P0 | ✅ | Expert #6 |
| R-SEC-15 | GDPR compliance for Person entities: lawful basis determination, data subject rights process, DPO appointment if required | P1 | ❌ | Expert #6 |
| R-SEC-16 | OFAC/sanctions screening: entities in graph must not facilitate sanctions evasion. Flag sanctioned entities | P1 | ❌ | Expert #6 |
| R-SEC-17 | SSO/SAML support for enterprise clients | P1 | ❌ (add at client #6) | Expert #6 |
| R-SEC-18 | Client data handling agreement template (DPA) | P0 | ✅ (template) | Expert #6 |
| R-SEC-19 | Incident response plan: detection, containment, eradication, recovery, notification (72-hour GDPR) | P0 | ✅ (document) | Expert #6 |
| R-SEC-20 | Data residency documentation: where is data stored, processed, backed up. Required for compliance questionnaires | P0 | ✅ | Expert #6 |
| R-SEC-21 | Vulnerability disclosure policy (public page for security researchers) | P1 | ❌ | Expert #6 |
| R-SEC-22 | Subprocessor list: all third parties that touch client data (Anthropic, Railway, etc.) with DPAs for each | P0 | ✅ | Expert #6 |
| R-SEC-23 | API key rotation capability: clients can rotate API keys without downtime | P1 | ❌ | Expert #6 |
| R-SEC-24 | Session management: token expiry, refresh, revocation | P0 | ✅ | Expert #6 |
| R-SEC-25 | Full provenance chain for every intelligence output: source → NER extraction → graph update → propagation → alert. Queryable by client, preservable for regulatory examination | P0 | ✅ (see also R-EXP1, R-EXP2) | Expert #6 |
| R-SEC-26 | Legal opinion on fair use / database right implications of processing copyrighted articles through LLM-based NER/RE pipeline (US fair use, EU Database Directive) | P1 | ❌ | Expert #6 |
| R-SEC-27 | OFAC/SDN screening of all Company entities in graph. Sanctioned entities flagged and access-restricted. Intelligence outputs involving sanctioned entities carry compliance warnings | P0 | ❌ (see also R-SEC-16) | Expert #6 |
| R-SEC-28 | Export control assessment for semiconductor supply chain intelligence under EAR. Legal opinion on whether MKG outputs constitute controlled information for specific entity combinations | P1 | ❌ | Expert #6 |
| R-SEC-29 | SSO/SAML 2.0 integration with enterprise identity providers (Okta, Azure AD, OneLogin, Ping). Required before first enterprise deployment | P0 | ❌ (see also R-SEC-17; add at client #6) | Expert #6 |
| R-SEC-30 | MFA enforcement for all user accounts: TOTP, WebAuthn/FIDO2, push-based. Must integrate with client MFA provider via SSO | P0 | ❌ (add with SSO) | Expert #6 |
| R-SEC-31 | RBAC expansion to minimum 8 roles: super-admin, org-admin, analyst, junior-analyst, read-only, auditor, API-only, compliance-officer. Configurable per client organization | P1 | ❌ | Expert #6 |
| R-SEC-32 | Attribute-based access control (ABAC) for entity-level data: access restrictions by entity type, sector, geography, data sensitivity classification | P1 | ❌ | Expert #6 |
| R-SEC-33 | Comprehensive audit logging of ALL data access events (reads, queries, exports, API calls, alert deliveries). Immutable, 7-year retention (SEC Rule 17a-4 equivalent), exportable in CEF/JSON | P0 | ❌ (partial: R-SEC4 covers mutations only) | Expert #6 |
| R-SEC-34 | Data export controls: configurable restrictions on download, copy-paste, screenshot (watermarking), API bulk extraction. Enterprise "view-only" access modes | P1 | ❌ | Expert #6 |
| R-SEC-35 | Incident Response Plan: documented, tested annually, severity classification (P1-P4), containment procedures, client notification within 72 hours of breach, post-incident review | P0 | ✅ (document; see also R-SEC-19) | Expert #6 |
| R-SEC-36 | Disaster Recovery: RPO <1 hour, RTO <4 hours during market hours. Recovery procedure per component (Neo4j, PostgreSQL, API, Celery). Tested quarterly | P0 | ✅ (see also R-PLAT-8, R-PLAT-9) | Expert #6 |
| R-SEC-37 | Business Continuity Plan: documented response for each key dependency failure — Claude API (fallback to Ollama), Neo4j (read-only from PG cache), Railway (documented RTO) | P1 | ❌ | Expert #6 |
| R-SEC-38 | Subprocessor register: all third-party services processing/storing/transmitting client data with DPA status, security assessment date, change notification requirement | P0 | ✅ (see also R-SEC-22) | Expert #6 |
| R-SEC-39 | Error monitoring (Sentry) data scrubbing rules: prevent capture of entity names from client queries, portfolio data, API keys, auth tokens, and confidential-classified data | P0 | ✅ | Expert #6 |

### 5.10 Product & Go-to-Market

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PM-1 | Define single beachhead vertical with full GTM plan. Non-beachhead deprioritized until $300K+ ARR | P0 | ✅ (Financial Markets / Semiconductor) | Expert #5 |
| R-PM-2 | Beachhead personas: (1) Event-Driven Fund PM, (2) Multi-Strategy HF PM. All MVP validated against these two | P0 | ✅ | Expert #5 |
| R-PM-3 | Revenue timeline with realistic enterprise sales cycle: 28-week average from demo to closed deal | P0 | ✅ | Expert #5 |
| R-PM-4 | GTM staffing: dedicated AE budgeted if Year 1 revenue target exceeds $100K | P1 | ❌ | Expert #5 |
| R-PM-5 | Explicit MVP feature set: max 20 requirements for beachhead buyer evaluation | P0 | ✅ (this document) | Expert #5 |
| R-PM-6 | Pricing model: value metric (per-seat vs per-entity vs hybrid), tier structure (3 tiers), pilot pricing (50–70% of list for first 5), annual commitment default | P0 | ✅ | Expert #5 |
| R-PM-7 | Total cost of ownership model: license + implementation + customer time + support | P1 | ❌ | Expert #5 |
| R-PM-8 | Competitive moat strategy with 3-year milestones. Must specify moat type being built | P1 | ❌ | Expert #5 |
| R-PM-9 | GTM motion: direct sales process, cycle time targets, conversion rates, Year 1 pipeline targets | P0 | ✅ | Expert #5 |
| R-PM-10 | Year 1 marketing plan: 2–3 target conferences (SALT, Alpha Conference, QuantMinds), content cadence, outreach volumes | P1 | ❌ | Expert #5 |
| R-PM-11 | Error handling protocol for incorrect high-confidence alerts: post-mortem, customer communication template, accuracy disclosure | P0 | ✅ | Expert #5 |
| R-PM-12 | Customer success: onboarding playbook, time-to-value target (<14 days to first valuable alert), health scoring | P1 | ❌ | Expert #5 |
| R-PM-13 | Competitive win/loss tracking: structured post-mortem for lost deals/failed POCs | P1 | ❌ | Expert #5 |
| R-PM-14 | Pricing experimentation: feature flags + tier configuration decoupled from product engineering | P1 | ❌ | Expert #5 |
| R-PM-15 | 20 discovery calls with target personas before writing code (Phase 0 validation) | P0 | ✅ | Expert #5 |

### 5.11 Visualization & UX

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-VIZ-1 | Information hierarchy: 5-level progressive disclosure (Level 1: headline → Level 5: full evidence chains) | P0 | ✅ (Levels 1–3 for MVP) | Expert #8 |
| R-VIZ-2 | Primary view: ranked impact table (not graph). Sort by impact score, filter by hop depth, entity type, sector | P0 | ✅ | Expert #8 |
| R-VIZ-3 | Table row expansion: click row → show causal chain, evidence sentences, confidence breakdown, weight history sparkline | P0 | ✅ | Expert #8 |
| R-VIZ-4 | WebGL-based graph rendering (NOT D3.js/SVG) for graphs >500 nodes. Use deck.gl, Sigma.js, or Three.js | P2 | ❌ | Expert #8 |
| R-VIZ-5 | Graph visual: semantic zoom (zoom out = clusters, zoom in = individual entities), level-of-detail rendering | P2 | ❌ | Expert #8 |
| R-VIZ-6 | Entity detail panel: company profile, all incoming/outgoing edges, weight history chart, news feed, tribal knowledge entries | P1 | ❌ | Expert #8 |
| R-VIZ-7 | Dark theme (mandatory for financial terminals). Bloomberg-inspired color palette | P0 | ✅ | Expert #8 |
| R-VIZ-8 | Keyboard navigation: arrow keys for table, Enter for expand, Escape for close, / for search, ? for help | P1 | ❌ | Expert #8 |
| R-VIZ-9 | Real-time update animation: smooth weight change transitions (no jumpy re-renders). Visual "pulse" on newly updated edges | P2 | ❌ | Expert #8 |
| R-VIZ-10 | Print/export view: clean PDF of current impact table + causal chains for risk committee reports | P1 | ❌ | Expert #8 |
| R-VIZ-11 | Mobile-responsive impact table (basic read-only on phone) | P1 | ❌ | Expert #8 |
| R-VIZ-12 | Loading states: skeleton screens, never blank. Show partial results while propagation computes | P0 | ✅ | Expert #8 |
| R-VIZ-13 | Empty state design: clear what to do when no propagation events exist. Guided first-run experience | P1 | ❌ | Expert #8 |
| R-VIZ-14 | Annotation/collaboration: users can add notes to entities or propagation events (stored per-tenant) | P2 | ❌ | Expert #8 |
| R-VIZ-15 | User workflows documented: 3 primary workflows mapped (event response, portfolio check, research deep-dive) with UI flow diagrams | P0 | ✅ (documentation only) | Expert #8 |

### 5.12 Competitive & Moat Strategy

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-COMP-1 | Document competitive moat strategy: choose ≥1 from (a) shared tribal knowledge network, (b) accuracy track record, (c) workflow integration. Reflect in roadmap + pricing + sales | P0 | ✅ | Expert #9 |
| R-COMP-2 | Community knowledge layer: aggregated, anonymized relationship data shared across clients. Individual tribal knowledge private; community layer creates network effect | P1 | ❌ | Expert #9 |
| R-COMP-3 | Accuracy track record as first-class product feature: every propagation tracked to outcome. Display in dashboard (90-day rolling), in alerts (historical hit rate), in public "track record page" | P0 | ✅ | Expert #9 |
| R-COMP-4 | Accumulate historical extraction data from day 1. Every article, entity, edge permanently stored with timestamps. One day of delay = one day of data moat lost | P0 | ✅ | Expert #9 |
| R-COMP-5 | Historical backfill capability: process archived articles (SEC EDGAR 2020–2025). Backfilled data marked lower confidence | P1 | ❌ | Expert #9 |
| R-COMP-6 | Pricing model: value metric, 3-tier structure, pilot pricing (50–70% list for first 5 clients), annual commitment, expansion triggers | P0 | ✅ | Expert #9 |
| R-COMP-7 | Usage metering: track per-client API calls, entities, propagation events, scenarios, users, export volume. Enables future value-based pricing | P1 | ❌ | Expert #9 |
| R-COMP-8 | Distribution plan: target account list (20 firms), outreach strategy (conference circuit), design partner criteria, quarterly revenue forecast | P0 | ✅ | Expert #9 |
| R-COMP-9 | Self-serve demo environment: pre-loaded semiconductor graph (500 entities), curated historical events (TSMC 2024, NVIDIA export controls), "replay" mode | P1 | ❌ | Expert #9 |
| R-COMP-10 | Plan for incumbent replication within 24–36 months. Answer: when Bloomberg ships competing feature, why do clients stay? | P0 | ✅ (strategy doc) | Expert #9 |
| R-COMP-11 | Target "tail entity coverage" as differentiation: 500+ Tier 3/4 semiconductor companies that Bloomberg/AlphaSense/FactSet don't track | P1 | ❌ | Expert #9 |
| R-COMP-12 | Tribal knowledge export in proprietary format (not CSV). Data portable in principle, friction-laden in practice | P1 | ❌ | Expert #9 |
| R-COMP-13 | ≥3 integration connectors by Month 12: (a) Excel/Sheets plugin, (b) Slack/Teams bot, (c) Python + JS client SDKs | P1 | ❌ | Expert #9 |
| R-COMP-14 | Roadmap: moat-first, not feature-first. Tribal knowledge + accuracy tracking + 1 integration in v1 before graph viz, what-if, multilingual | P0 | ✅ | Expert #9 |
| R-COMP-15 | Stay below Bloomberg's radar first 18 months (<$5M ARR). Target mid-tier event-driven funds ($500M–$5B AUM), not Bloomberg's top 50 accounts | P0 | ✅ (strategy) | Expert #9 |

### 5.13 Platform & Infrastructure

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PLAT-1 | Hybrid multi-tenancy: shared read-only graph for public data + tenant-isolated storage for tribal knowledge, alerts, portfolio, usage, API keys. 100+ isolation boundary tests | P0 | ✅ | Expert #10 |
| R-PLAT-2 | Cost-per-tenant documented per tier. Infra cost per client vs contract value. Target: infra <30% of contract value | P0 | ✅ | Expert #10 |
| R-PLAT-3 | Complete infrastructure cost model: per-service cost at 10/50/100 clients, cost-per-client, Claude API %, monthly review cadence | P0 | ✅ | Expert #10 |
| R-PLAT-4 | Claude API cost optimization: response caching (>90% similarity), model cascading (Haiku → Sonnet), batch scheduling (off-peak) | P1 | ❌ | Expert #10 |
| R-PLAT-5 | API: versioning (URL-based /v1/), cursor-based pagination, standardized error format with machine-parseable codes, Idempotency-Key on mutations | P0 | ✅ | Expert #10 |
| R-PLAT-6 | Webhook delivery for propagation events: HMAC-SHA256 signature, retry 5x with exponential backoff, DLQ for failures, manual re-delivery via API | P0 | ✅ | Expert #10 |
| R-PLAT-7 | Auto-generated client SDKs (Python + JS) from OpenAPI spec. Typed models, auto-retry, rate limit handling. Publish to PyPI/npm | P1 | ❌ | Expert #10 |
| R-PLAT-8 | RTO/RPO defined per data store: Neo4j RTO <4hr / RPO <6hr; PostgreSQL RTO <1hr / RPO <1hr; Redis RTO <15min. Weekly backup verification (restore to test env) | P0 | ✅ | Expert #10 |
| R-PLAT-9 | Automated backup: Neo4j daily full + hourly incremental; PostgreSQL continuous WAL archiving with PITR. Backups in separate region/account | P0 | ✅ | Expert #10 |
| R-PLAT-10 | Graceful degradation for every external dependency. Claude down → fallback extraction. Neo4j down → cached results (read-only). Redis down → PG-backed queue. Dashboard shows degradation status | P1 | ❌ | Expert #10 |
| R-PLAT-11 | CI/CD pipeline: lint + type check → unit tests → integration tests → security scan → Docker build. Pipeline blocks on failure. Target <10 min | P0 | ✅ | Expert #10 |
| R-PLAT-12 | Zero-downtime deployment: blue-green with health check gate. Rollback instant. In-flight Celery tasks drain before old worker termination | P0 | ✅ | Expert #10 |
| R-PLAT-13 | Deployment audit log: who, when, what commit, tests passed, duration, rollback events. Admin API accessible. SOC 2 required | P1 | ❌ | Expert #10 |
| R-PLAT-14 | Support ≥2 integration patterns at launch: (a) Dashboard (web + WebSocket), (b) REST API (pagination, webhooks, SDK). Pattern 3 (Telegram/Slack alerts) in v1. Pattern 4 (data feed) P2 | P0 | ✅ | Expert #10 |
| R-PLAT-15 | API-first development: every feature available via API before/simultaneously with dashboard. Dashboard is reference client of API | P0 | ✅ | Expert #10 |
| R-PLAT-16 | Architecture must not preclude on-prem: no Railway-specific deps in code, all config via env vars + config files, Docker Compose as deployment unit, core works offline | P1 | ❌ (architecture decision now) | Expert #10 |
| R-PLAT-17 | "Dedicated SaaS" tier: separate Neo4j, PG, Redis, Celery per client for $5B+ AUM funds requiring physical isolation | P2 | ❌ | Expert #10 |
| R-PLAT-18 | Operational automation for 1–2 person team: automated backup + restore verify, cert renewal, disk monitoring, Celery health + restart, Claude budget alerts, single-command deploy with auto-rollback | P0 | ✅ | Expert #10 |
| R-PLAT-19 | Operational dashboards: (a) infra health, (b) pipeline health (R-PIPE-10 metrics), (c) business health (articles, entities, propagation, users, API calls), (d) cost health. Single URL, no manual setup | P1 | ❌ | Expert #10 |
| R-PLAT-20 | All graph operations behind GraphStorage interface (from MiroFish R-MF6). No Cypher outside Neo4j adapter. Covers: entity CRUD, edge CRUD, subgraph traversal, propagation, vector search, backup | P0 | ✅ | Expert #10 |
| R-PLAT-21 | Database migration readiness checklist: all graph ops behind interface, no Neo4j-specific code in business logic, integration tests against mock graph, migration script templates for CE→Enterprise and CE→Aura | P1 | ❌ | Expert #10 |
| R-PLAT-22 | Post-launch engineering: feature capacity reduced 50–70%. Sprint durations 2x pre-launch. Single engineer ≈15–20 hrs/week for features | P0 | ✅ (planning) | Expert #10 |
| R-PLAT-23 | Business financial model: monthly burn by category, revenue forecast by quarter for 24 months, funding requirement, break-even target, sensitivity analysis | P0 | ✅ | Expert #10 |

### 5.14 Supply Chain Vertical (Deferred to v2+)

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PROD1 | Graph: Component/Part nodes with part_number, specification, category, lifecycle_stage, qualification_status | P2 | ❌ | Expert #2 |
| R-PROD2 | BOM edges: SUBCOMPONENT_OF with quantity, criticality, qualified_supplier_count | P2 | ❌ | Expert #2 |
| R-PROD3 | SHIPS_VIA edges: logistics route, transit time, chokepoint flags | P2 | ❌ | Expert #2 |
| R-PROD4 | QUALIFIES_AS_ALTERNATIVE edges: status, time_to_qualify, cost_premium, capacity_available | P2 | ❌ | Expert #2 |
| R-DUR1 | Propagation: estimated disruption duration (P10/P50/P90) based on historical data + disruption type | P2 | ❌ | Expert #2 |
| R-DUR2 | Inventory buffer runway per affected component (weeks of supply remaining) | P2 | ❌ | Expert #2 |
| R-MIT1 | Ranked mitigation actions per disruption (dual-source, buffer, qualify alternative, redesign) | P2 | ❌ | Expert #2 |
| R-MIT2 | Mitigation action status tracking (recommended → in progress → completed) | P2 | ❌ | Expert #2 |
| R-INT1 | SAP S/4HANA integration for master supplier data + PO history | P2 | ❌ | Expert #2 |
| R-INT2 | BOM import from PLM systems (Teamcenter, Windchill) via STEP AP242 / JSON | P2 | ❌ | Expert #2 |
| R-GEO1 | Facility: sub-national location + natural disaster risk zone classification | P1 | ❌ | Expert #2 |
| R-GEO2 | Geographic map visualization with facility locations, shipping routes, risk zone overlays | P2 | ❌ | Expert #2 |
| R-COMP-SC1 | Regulatory compliance edges: REQUIRES_CERTIFICATION (IATF, REACH, RoHS) + status + expiry | P2 | ❌ | Expert #2 |
| R-FIN1 | Supplier financial health indicators: credit rating, Z-score proxy, payment behavior | P2 | ❌ | Expert #2 |
| R-INV1 | Propagation attenuation accounts for inventory buffer levels (zero impact until buffer exhausted) | P2 | ❌ | Expert #2 |

### 5.15 Portfolio & Financial Integration (Pending Legal Opinion)

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-PORT1 | Portfolio position import via API (quantity, entry price, exposure) | P1 (pending R-SEC-11) | ❌ | Expert #1 |
| R-PORT2 | Propagation results overlay portfolio positions with estimated PnL impact | P1 (pending R-SEC-11) | ❌ | Expert #1 |
| R-PORT3 | Alert on propagation event causing estimated portfolio risk limit breach | P1 (pending R-SEC-11) | ❌ | Expert #1 |
| R-BT1 | Historical backtesting of propagation signals vs actual price movements | P0 (upgraded from P2) | ❌ (Phase 5–6) | Expert #1 |
| R-BT2 | Backtest results: hit rate, avg return, Sharpe ratio, max drawdown, avg alpha decay | P1 | ❌ | Expert #1 |
| R-BT3 | Historical news/event data for backtesting (min 2 years, semiconductor) | P1 | ❌ | Expert #1 |
| R-DQ1 | Every edge weight: data quality score (source count, source diversity, recency) | P0 | ✅ | Expert #1 |
| R-DQ2 | Minimum edge coverage per sector before declaring "ready" | P1 | ❌ | Expert #1 |
| R-DQ3 | Edge weight staleness indicator (time since last confirming signal) | P0 | ✅ | Expert #1 |
| R-LIQ1 | Propagation results: liquidity scoring per entity (avg daily volume, market cap) | P1 | ❌ | Expert #1 |
| R-LAT1 | Direct news wire API integration (DJNS, Reuters) for <10s detection | P1 | ❌ | Expert #1 |
| R-FP1 | Track false positive rate per event type, sector, hop depth | P0 | ✅ | Expert #1 |
| R-FP2 | Target false positive rate <30% for high-confidence (>80%) propagation alerts | P0 | ✅ | Expert #1 |
| R-ATT1 | Impact attenuation configurable per edge type (SUPPLIES_TO ≠ COMPETES_WITH) | P0 | ✅ | Expert #1 |
| R-ATT2 | Empirical calibration of attenuation factors from backtesting data | P1 | ❌ | Expert #1 |

### 5.16 Data Sources & Coverage

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-DS1 | SEC EDGAR: 10-K, 10-Q, 8-K — supplier mentions, revenue concentration, risk factors | P0 | ✅ | Original |
| R-DS2 | Earnings call transcripts: supplier/customer mentions, capacity, guidance | P0 | ✅ | Original |
| R-DS3 | News APIs: minimum 3 diverse sources (Reuters, industry-specific) | P0 | ✅ | Original |
| R-DS4 | Trade data: import/export records for relationship discovery | P1 | ❌ | Original |
| R-DS5 | Patent filings: technology dependency discovery | P2 | ❌ | Original |
| R-DS6 | Satellite imagery: facility monitoring signals | P2 | ❌ | Original |
| R-DS7 | Social media: Twitter/X, Reddit for early signals | P1 | ❌ | Original |
| R-DS8 | Government gazettes: regulatory announcements | P1 | ❌ | Original |

### 5.17 Tribal Knowledge

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-TK1 | Manual expert input of relationship assertions with confidence scores | P0 | ✅ | Original |
| R-TK2 | Track provenance of each entry (who, when, what source) | P0 | ✅ | Original |
| R-TK3 | Configurable decay half-life per knowledge type | P1 | ❌ | Original |
| R-TK4 | Contradiction detection (new signal vs existing tribal knowledge) | P1 | ❌ | Original |
| R-TK5 | Distinguish verified (data), asserted (expert), inferred (LLM) edge sources | P0 | ✅ | Original |
| R-TK6 | Tribal knowledge upgrade to verified when supporting data arrives | P1 | ❌ | Original |

### 5.18 Non-Functional Requirements

| Req ID | Requirement | Target | Priority | Expert |
|--------|-------------|--------|----------|--------|
| R-NF1 | Signal ingestion to graph update | <5 minutes | P0 | Original |
| R-NF2 | Signal to edge weight adjustment | <30 seconds | P0 | Original |
| R-NF3 | Trigger to propagation result | <60 seconds | P0 | Original |
| R-NF4 | Graph query (entity subgraph) | <2 seconds | P0 | Original |
| R-NF5 | Hybrid search (vector + keyword) | <1 second | P0 | Original |
| R-NF6 | Dashboard page load | <3 seconds | P0 | Original |
| R-NF7 | System uptime | 99.5% (24/7) | P0 | Original |
| R-NF8 | Concurrent API users | 100+ | P1 | Original |
| R-SC1 | Graph: 5K → 50K nodes without architecture change | P0 | | Original |
| R-SC2 | Ingestion: 10K → 100K articles/day with horizontal scaling | P1 | | Original |
| R-SC3 | Users: 10 → 1,000 concurrent with load balancer | P1 | | Original |
| R-SC4 | Multi-tenant: isolated graph views per subscription tier | P0 (see R-PLAT-1) | | Original |

### 5.19 MiroFish Integration (Deferred to v2+)

| Req ID | Requirement | Priority | MVP | Expert |
|--------|-------------|----------|-----|--------|
| R-MF1 | MiroFish as separate sidecar service (AGPL-3.0 isolation) | P2 | ❌ | Original |
| R-MF2 | Shared Neo4j with isolated graph_ids (or separate instances — see R-GRAPH-1) | P2 | ❌ | Original |
| R-MF3 | Cross-graph entity resolution (MKG ↔ MiroFish) | P2 | ❌ | Original |
| R-MF4 | Feed MKG propagation events into MiroFish as simulation inputs | P2 | ❌ | Original |
| R-MF5 | Return MiroFish sentiment evolution for MKG confidence calibration | P2 | ❌ | Original |
| R-MF6 | Reuse MiroFish GraphStorage abstraction for MKG graph layer | P0 | ✅ (adopted as R-PLAT-20) | Original |
| R-MF7 | Adapt MiroFish NER/RE pipeline for financial entity types | P0 | ✅ | Original |
| R-MF8 | Reuse MiroFish hybrid search (0.7 vector + 0.3 BM25) | P0 | ✅ | Original |

---

## 6. Risk Matrix

### Critical Risks (Must Mitigate Before Launch)

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| 1 | Bloomberg/AlphaSense replicates in 24–36 months | HIGH (60%) | FATAL | Build moat: accuracy track record + tribal knowledge + integrations (R-COMP-1, R-COMP-3, R-COMP-14) | Founder |
| 2 | No GTM → product built, nobody buys | HIGH (80%) | FATAL | 20 discovery calls (R-PM-15), design partners, conference circuit (R-COMP-8) | Founder |
| 3 | Investment adviser classification blocks portfolio features | MEDIUM (40%) | HIGH | Legal opinion before build (R-SEC-11). If positive → registration ($50K+). If blocked → pivot to information-only | Lawyer |
| 4 | NLP accuracy insufficient for reliable propagation | HIGH (70%) | HIGH | Evaluation datasets (R-NLP-13, R-NLP-14), hallucination tracking (R-NLP-10), human-in-loop (R-NLP-4) | ML Engineer |
| 5 | Claude API cost/dependency threatens business | HIGH (60%) | HIGH | Cost governance (R-PIPE-14), fallback (R-PIPE-7), tiered extraction (R-PIPE-20), caching (R-PLAT-4) | CTO |
| 6 | SOC 2 missing → every sales process dies | HIGH (90%) | HIGH | Start SOC 2 prep during build (R-SEC-8). First pentest pre-launch (R-SEC-9) | Compliance |
| 7 | Cash gap: costs exceed revenue for 18+ months | HIGH (80%) | FATAL | Financial model (R-PLAT-23). Seed round $500K–$1M at Phase 1 | Founder |
| 8 | Pipeline loses articles silently → invisible graph holes | HIGH (60%) | HIGH | At-least-once (R-PIPE-3), DLQ (R-PIPE-9), observability (R-PIPE-10) | CTO |
| 9 | Tenant data leak destroys client trust | MEDIUM (40%) | FATAL | Hybrid isolation (R-PLAT-1), 100+ boundary tests, app-level RBAC | CTO |
| 10 | Demo ≠ product; first revenue 15–18 months not 6 | HIGH (90%) | MEDIUM | Realistic timeline (Section 7), set expectations accordingly | Founder |

### Operational Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 11 | Neo4j CE limitations force unplanned migration | HIGH (70%) | MEDIUM | GraphStorage interface (R-PLAT-20), migration readiness (R-PLAT-21) |
| 12 | Operational overhead consumes all engineering time post-launch | HIGH (80%) | MEDIUM | Automation (R-PLAT-18), realistic velocity (R-PLAT-22) |
| 13 | Railway platform outage during major market event | MEDIUM (30%) | HIGH | Architecture portability (R-PLAT-16), graceful degradation (R-PLAT-10) |
| 14 | D3.js/SVG can't render 5K+ node graphs | HIGH (90%) | MEDIUM | Table-first (R-VIZ-2), WebGL for v2 graph viz (R-VIZ-4) |
| 15 | Weight update storms during macro events overwhelm Neo4j | MEDIUM (30%) | HIGH | Write batching in Redis, read priority during storms (R-GRAPH-7) |

---

## 7. Revised Timeline

### Phase 0: Market Validation (Weeks 1–4)

| Deliverable | Exit Criteria |
|-------------|---------------|
| 20 discovery calls with event-driven fund PMs | 5 design partner verbal commitments |
| Investment adviser legal opinion | Legal green light (or scope adjustment) |
| Pricing validation ($30K–$50K range) | Price point validated through discovery |
| Seed round preparation (if needed) | Deck ready, 3–5 investor conversations started |

### Phase 1: Graph Foundation (Weeks 5–12)

| Deliverable | Exit Criteria |
|-------------|---------------|
| Neo4j setup with MKG schema (6 node types, 7 edge types) | Schema deployed, GraphStorage interface complete |
| 500 semiconductor entities seeded from SEC filings | "Show me TSMC suppliers" returns correct, sourced results |
| Entity CRUD + search API | API functional tests pass |
| Canonical entity registry (500 entities with aliases) | Dedup working for known entities |
| PostgreSQL: users, audit, weight history tables | Schema + migrations complete |

### Phase 2: Extraction Pipeline (Weeks 13–20)

| Deliverable | Exit Criteria |
|-------------|---------------|
| English NER/RE from 5 sources (SEC filings, transcripts, 3 news) | 500 articles/day auto-updating graph |
| At-least-once delivery with DLQ | No silent article drops in 7-day test |
| Claude API cost governance + fallback extraction | Spend <$3K/month; fallback produces usable output |
| Pipeline observability (15+ metrics) | Dashboard shows real-time pipeline health |
| Article dedup + durable storage | 2-year retention working |
| Hallucination verification (R-NLP-8) | 95%+ of extracted entities verified against source |

### Phase 3: Propagation + Alerts (Weeks 21–28)

| Deliverable | Exit Criteria |
|-------------|---------------|
| Propagation engine: 4-hop, cycle detection, causal chains | "TSMC fab fire" → ranked impact in <60 seconds |
| Ranked impact table view (primary UI) | Design partners can view and filter results |
| Alert system: configurable triggers + webhooks | PM sets watchlist, receives alerts |
| REST API: versioned, paginated, error format | Quant team can integrate via API |
| Accuracy tracking: every prediction logged vs outcome | Tracking running; no accuracy claims yet |

### Phase 4: Productization (Weeks 29–36)

| Deliverable | Exit Criteria |
|-------------|---------------|
| JWT auth + tenant isolation (hybrid model) | 100+ isolation boundary tests pass |
| Tribal knowledge input UI | Design partners entering expert assertions |
| CI/CD pipeline + zero-downtime deploy | All deploys automated; rollback tested |
| Automated backups + disaster recovery | Weekly restore verification passing |
| SOC 2 prep started (policies, controls) | Compliance platform configured; gap assessment complete |
| Operational automation (R-PLAT-18) | Single-command deploy, auto-alerts, auto-restart |

### Phase 5: Launch (Weeks 37–42)

| Deliverable | Exit Criteria |
|-------------|---------------|
| First 2–3 paid clients | Signed annual contracts at $30K–$50K/yr |
| Client onboarding playbook | Time-to-value <14 days |
| Error handling protocol | Post-mortem process for wrong alerts |
| Penetration test completed | Report shareable with prospects |

### Phase 6: Moat Building (Weeks 43–52)

| Deliverable | Exit Criteria |
|-------------|---------------|
| SSO/SAML (R-SEC-17) | Enterprise client deployable |
| SOC 2 Type I submitted | Audit in progress |
| Accuracy track record ≥6 months | Publishable hit rate |
| ≥1 integration (Excel/Sheets or Slack) | 1 connector live |
| 5–8 paying clients total | $150K–$400K ARR |
| Demo environment (R-COMP-9) | Self-serve for prospect evaluation |

**Total: 52 weeks (12 months) to first revenue at Week 37. 18–24 months to $500K ARR.**

---

## 8. Cost Model

### Year 1 (Months 1–12) — Founders as Engineers

| Category | Monthly Range | Annual Cost |
|----------|--------------|------------|
| Engineering (founders, no salary) | $0 | $0 (sweat equity) |
| Infrastructure (cloud, DB, monitoring) — ramps | $1.5K–$3K | $18K–$36K |
| Claude API (ramps from 500 → 2K articles/day) | $3K–$6K | $36K–$72K |
| Compliance (SOC 2 prep, pentest, legal) | varies | $50K–$100K |
| Sales & marketing (founder-led, 2 conferences) | $2.5K–$5K | $30K–$60K |
| Legal (investment adviser, contracts, IP) | varies | $30K–$50K |
| SaaS tools + misc | $1K–$2K | $10K–$20K |
| **Total Year 1** | | **$174K–$338K** |

### Year 2 (Months 13–24) — Scaling

| Category | Annual Cost |
|----------|------------|
| Engineering (founders or $100K–$200K if paying selves) | $0–$200K |
| Infrastructure (10+ clients, 10K articles/day) | $60K–$120K |
| Claude API (10K articles/day) | $108K–$120K |
| Compliance (annual SOC 2, pentest) | $30K–$50K |
| Sales & marketing (first AE + conferences) | $150K–$250K |
| Legal | $15K–$25K |
| Miscellaneous | $15K–$25K |
| **Total Year 2** | **$378K–$790K** |

### Cumulative 24-Month Cost

| Scenario | Total |
|----------|-------|
| Founders bootstrap (no salaries) | $552K–$1.13M |
| With engineering salaries | $802K–$1.53M |

### Revenue Projections (Realistic)

| Quarter | Clients | Revenue |
|---------|---------|---------|
| Year 1 Q1 | 0 (building) | $0 |
| Year 1 Q2 | 0 (beta with design partners) | $0 |
| Year 1 Q3 | 2–3 (first paid) | $15K–$38K |
| Year 1 Q4 | 5–8 (growing) | $38K–$100K |
| **Year 1 Total** | | **$53K–$138K** |
| Year 2 Q1 | 8–12 | $60K–$150K |
| Year 2 Q2 | 12–18 | $90K–$225K |
| Year 2 Q3 | 18–25 | $135K–$313K |
| Year 2 Q4 | 25–35 | $188K–$438K |
| **Year 2 Total** | | **$473K–$1.13M** |

### Funding Requirement

**$500K–$1M seed round** at Phase 0–1 completion. Break-even target: Month 24–30.

### Cost Dominance: Claude API

Claude API is 75–80% of infrastructure cost at scale. Cost optimization strategies (R-PLAT-4, R-PIPE-20) can reduce this to ~50% through:
- Response caching (estimated 20–30% cost reduction)
- Model cascading — Haiku for detection, Sonnet for extraction (estimated 30–40% reduction)
- Batch scheduling off-peak (estimated 10–15% reduction)

---

## 9. Strategic Decisions Required

These decisions must be made **before engineering begins** (Phase 0):

### Decision 1: Beachhead Vertical

**Recommended:** Financial Markets (semiconductor supply chain focus)

**Rationale:** Shorter sales cycle (3–6 months vs 9–18 for supply chain), faster proof of value (one market event validates), higher per-seat willingness-to-pay at lower deal complexity, public data only (no customer integration needed), conference circuit enables word-of-mouth.

**Implication:** Supply chain features (R-PROD*, R-DUR*, R-MIT*, R-INT*) are all P2. No BOM integration, no ERP connectors, no disruption duration estimation in v1.

### Decision 2: Neo4j Edition

**Recommendation:** Start with CE. Budget for Enterprise at client #5 or first $200K ARR.

| Decision | Implications |
|----------|-------------|
| Stay CE | App-level RBAC, offline backups only, single-instance (no HA), no multi-database isolation |
| Enterprise ($36K+/yr) | RBAC, online backup, clustering, multi-database. Required for enterprise clients |
| Aura (managed) | Reduces ops burden. $500–$2K/month. No self-hosting |

### Decision 3: Tribal Knowledge — Shared vs Private

**Recommendation:** Private in v1. Community knowledge layer (R-COMP-2) in v2 when client base supports it.

**Trade-off:** Private = no network effect moat. Shared = data moat but client trust risk. Resolution: raw entries private; aggregated statistics from public signals shared.

### Decision 4: Investment Adviser Status

**Action Required:** Obtain legal opinion (R-SEC-11) before building portfolio overlay features (R-PORT1–R-PORT3).

| Outcome | Implication |
|---------|-------------|
| Not investment adviser | Portfolio overlay can proceed |
| Investment adviser | Register with SEC ($50K+ annually) or remove personalized portfolio features |

### Decision 5: Pricing Model

**Recommended initial structure:**

| Tier | Price | Includes |
|------|-------|---------|
| Starter | $30K–$50K/yr | 1 vertical, 500 entities, API access, alerts, 1 user |
| Professional | $80K–$150K/yr | Full graph, what-if, API + webhooks, 5 users |
| Enterprise | $200K+/yr | Dedicated instance, SLA, SSO, custom integrations, unlimited users |
| Pilot | 50–70% of Starter | 60–90 days, feedback + case study rights required |

---

## 10. Appendices

### Appendix A: Expert Review Files

All detailed expert analysis documents are located at:

- `docs/design/mkg-expert-review/iteration-1-2.md` — Hedge Fund PM + Supply Chain VP (456 lines)
- `docs/design/mkg-expert-review/iteration-3-4.md` — Graph DB Architect + NLP Scientist (781 lines)
- `docs/design/mkg-expert-review/iteration-5-6.md` — Enterprise PM + CISO (1,011 lines)
- `docs/design/mkg-expert-review/iteration-7-8.md` — Pipeline Architect + UX Designer (708 lines)
- `docs/design/mkg-expert-review/iteration-9-10.md` — Competitive Intel + Platform Engineer (851 lines)

**Total expert analysis: 3,807 lines across 5 documents.**

### Appendix B: Original Requirements Source

`core/MKG_REQUIREMENTS.md` — 561 lines, synthesized from 7 MKG research documents (20,000+ words).

### Appendix C: Key Accuracy Benchmarks (Expert #4)

| Component | Head Entities (Top 500) | Tail Entities (Long Tail) |
|-----------|------------------------|--------------------------|
| Company NER | 94–97% F1 | 60–75% F1 |
| Product NER | 70–85% F1 | 40–60% F1 |
| Facility NER | 50–70% F1 | 30–50% F1 |
| Person NER | 85–92% F1 | 65–80% F1 |
| Country NER | 95%+ F1 | 90%+ F1 |
| Regulation NER | 60–80% F1 | 40–60% F1 |

| Relation Type | Expected F1 (English, LLM) |
|--------------|---------------------------|
| SUPPLIES_TO | 70–80% |
| COMPETES_WITH | 75–85% |
| MANUFACTURES_AT | 55–70% |
| REGULATES | 65–75% |
| INVESTS_IN | 80–90% |
| PARTNERS_WITH | 60–75% |
| DEPENDS_ON | 45–60% |

**4-hop all-correct probability:** ~(0.70)^4 = **24%** (at average 70% per-hop accuracy)

### Appendix D: Neo4j CE vs Enterprise Feature Gap (Expert #3)

| Capability | CE | Enterprise | Required By |
|------------|-----|-----------|------------|
| Role-based access control | ❌ | ✅ | R-SEC2 |
| Online backup (hot) | ❌ | ✅ | R-KG13 |
| Multi-database | ❌ | ✅ | R-MF2, isolation |
| Causal clustering (HA) | ❌ | ✅ | R-NF7 |
| Read replicas | ❌ | ✅ | R-NF8 |
| Property-level security | ❌ | ✅ | R-SC4 |

### Appendix E: Infrastructure Cost Breakdown (Expert #10)

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| Neo4j (shared graph) | 32GB RAM, 8 vCPU, 500GB SSD | $400–$800 |
| PostgreSQL + TimescaleDB | 16GB RAM, 4 vCPU, 200GB SSD | $200–$400 |
| Redis | 4GB RAM, 2 vCPU | $50–$100 |
| FastAPI (2 replicas) | 4GB RAM each | $100–$200 |
| Celery workers (3) | 4GB RAM each | $150–$300 |
| Next.js frontend | 2GB RAM | $30–$50 |
| Claude API | 10K articles/day | $9,000–$10,000 |
| Monitoring (Sentry, Prometheus) | | $100–$200 |
| Object storage | 50GB/month growth | $10–$20 |
| **Total** | | **$10,040–$12,070/month** |

### Appendix F: The Key Success Factor (Panel Consensus)

> **The single factor that determines whether MKG succeeds or fails: accuracy track record, accumulated over time, demonstrable to buyers.**
>
> If MKG's propagation predictions are accurate (≥70% hit rate on direction, within 2x on magnitude), the product sells itself through word-of-mouth among event-driven fund PMs.
>
> If MKG's predictions are inaccurate (<60% hit rate), no amount of marketing, pricing, or features saves the product.
>
> Build the accuracy measurement infrastructure first. Track every propagation event. Compare every prediction to actual market outcome within 30 days. Publish results monthly. Make accuracy the brand identity.
>
> That number, accumulated over time, is the only moat that Bloomberg cannot instantly replicate.

---

*End of MKG System Requirements Document v1.0*  
*303 requirements. 10 expert reviews. One actionable plan.*  
*Generated: 31 March 2026*
