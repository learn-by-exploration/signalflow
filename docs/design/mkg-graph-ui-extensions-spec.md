# MKG Graph UI Extensions — Expert Panel Design Spec

> **Status**: Brainstorm complete — ready for implementation prioritization  
> **Date**: 7 April 2026  
> **Author**: AI-assisted design (Claude + 10-person expert panel simulation)  
> **Module**: Market Knowledge Graph (MKG) Web Interface — Extensions  
> **Predecessor**: [mkg-graph-ui-spec.md](mkg-graph-ui-spec.md) (original spec, pre-implementation)

---

## Executive Summary

The MKG Graph UI shipped its P0 MVP: entity explorer, neighborhood graph, relationship browser, and impact simulator — all functional across 4 pages and 10 components. This spec identifies the **next wave** of extensions, evaluated by a 10-person expert panel against the question: *"What's missing that would make a finance professional actually rely on this tool for daily trading decisions?"*

### What Exists Today (Implemented)

| Page | Key Features | Status |
|------|-------------|--------|
| `/knowledge-graph` | EntitySearch, health stats, entity directory grid, quick action cards | ✅ Live |
| `/knowledge-graph/entity/[id]` | EntityCard, React Flow neighborhood graph (1-3 hops), FilterPanel, connected entities grid, RelationshipTable | ✅ Live |
| `/knowledge-graph/relationships` | Stats summary, relation type pills, entity filter, sortable RelationshipTable | ✅ Live |
| `/knowledge-graph/simulate` | ImpactSimulator (entity selector, event input, parameters), ImpactTable, CausalNarratives, optional graph overlay | ✅ Live |

**Components**: EntitySearch, EntityCard, EntityNode, RelationEdge, GraphCanvas, FilterPanel, RelationshipTable, ImpactSimulator, ImpactTable, CausalNarratives

**Backend APIs surfaced**: entity CRUD, edge CRUD, graph search, neighbors, subgraph, propagation, causal chains, impact table, alerts, graph health

**Backend APIs NOT yet surfaced**: articles pipeline, tribal knowledge input, compliance/audit, lineage/provenance, accuracy tracking, weight adjustment, event feed, graph export, contradiction detection, source credibility, PII detection, webhook delivery, pipeline observability, cost governance

---

## 1. Expert Panel — Individual Assessments

### 1.1 Supply Chain Analyst (Dr. Anita Rao)

> *"The simulator is good. But I can't answer the most important supply chain question: 'Where are the single points of failure?'"*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Single-Point-of-Failure (SPoF) Detection** | "If one entity is removed, how many downstream entities lose ALL supply paths? This is THE question for risk." Traders need to know concentration risk before entering positions. | 5 | 3 | 15 |
| 2 | **Path Finder (A→B)** | "Show me all paths between TSMC and Apple. How many intermediaries? How robust is the connection?" Essential for understanding indirect dependencies. | 4 | 3 | 12 |
| 3 | **Temporal Edge Awareness** | "Relationships change. Show me which edges are current (< 90 days fresh) vs stale. Stale data is worse than no data." | 4 | 4 | 16 |
| 4 | **Edge Provenance Indicators** | "Was this relationship AI-extracted from a news article or manually verified by a domain expert? I trust them differently." The `source` and `confidence` fields exist but aren't shown. | 4 | 5 | 20 |
| 5 | **Comparison Simulations** | "What if TSMC goes down vs Samsung? Side-by-side impact comparison for scenario planning." | 3 | 3 | 9 |

**Table Stakes Missing**: Edge freshness/staleness indicator on every relationship. The `valid_from`/`valid_until` and `updated_at` fields exist in the data model but are invisible in the UI.

---

### 1.2 Financial Trader (Vikram Mehta)

> *"I don't have time to explore a graph. Show me what I need to know, NOW. Connect this to my portfolio."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Signal ↔ Graph Bridge** | "When I see a STRONG_BUY on NVIDIA, I want one click to see its supply chain context. Why did MKG influence this signal?" The SignalBridge backend exists — zero UI for it. | 5 | 4 | 20 |
| 2 | **Watchlist Supply Chain Overlay** | "Show me which of my watchlist stocks share supply chain dependencies. If 5 of my stocks all depend on TSMC, that's concentration risk I need to see." | 5 | 3 | 15 |
| 3 | **Alert Feed Page** | "When a critical supply chain event fires, I need to see it immediately — not dig through the graph. Push it to me." The AlertSystem backend generates alerts; no UI consumes them. | 4 | 4 | 16 |
| 4 | **Quick Impact Check from Signal Page** | "From any signal detail page, let me run a 'what if this company has a problem?' simulation without navigating away." | 4 | 4 | 16 |
| 5 | **Graph Changes Feed ("What's New")** | "When I open the graph page, show me what changed since my last visit: new entities, updated edges, new articles processed." | 3 | 3 | 9 |

**Table Stakes Missing**: There is no connection between the main SignalFlow dashboard (signals, watchlist) and the MKG graph. They are completely separate worlds. The bridge is the #1 gap.

---

### 1.3 UX Designer (Meera Iyer)

> *"The building blocks are good. But the experience lacks flow — there's no narrative. Users do tasks, not browse features."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Guided Scenario Walkthroughs** | "Pre-built 'what-if' scenarios with step-by-step narration. 'Let's see what happens when oil prices spike.' Reduces the cold-start problem for new users." | 4 | 4 | 16 |
| 2 | **Context Panel (Entity Sidebar)** | "When clicking a node in the graph, don't navigate away. Open a slide-out panel with entity details, key relationships, and action buttons. Preserve the user's spatial context." | 5 | 4 | 20 |
| 3 | **Unified Search → Action Flow** | "Search should be omnipresent. From search results, offer actions: 'View Graph', 'Run Impact Sim', 'See Relationships'. Not just navigate to entity detail." | 4 | 4 | 16 |
| 4 | **Empty States & Onboarding** | "When the graph has no data, what does the user see? When they first visit, is there a guided intro? Currently it's a blank grid." | 3 | 5 | 15 |
| 5 | **Mobile-Optimized Impact Summary** | "On mobile, the graph canvas is useless. But the ImpactTable and CausalNarratives work perfectly in text/card format. Make simulate page mobile-first." | 3 | 4 | 12 |

**Table Stakes Missing**: No slide-over or sidebar detail panel. Every click is a full page navigation. This breaks spatial context in graph exploration.

---

### 1.4 Data Visualization Expert (Prof. Rajesh Kumar)

> *"React Flow works for 50 nodes. But the real value is in visual encodings that surface patterns — not just showing topology."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Impact Heatmap Overlay on Graph** | "After running a simulation, color every node by its impact score on the existing graph canvas. Red = high impact, blue = low. Instant visual pattern recognition." The simulate page already fetches the subgraph — just needs color mapping. | 5 | 5 | 25 |
| 2 | **Confidence-Weighted Edge Rendering** | "High-confidence edges (>0.8) should be solid and bold. Low-confidence (<0.5) should be dashed and faint. Currently all edges look the same." The RelationEdge component has `confidence` in props but doesn't use it visually. | 4 | 5 | 20 |
| 3 | **Node Size by Degree/Centrality** | "Highly connected entities (nodes with many edges) should appear larger. This instantly reveals hubs and potential SPoFs without any computation." | 4 | 4 | 16 |
| 4 | **Cluster/Group by Entity Type** | "Color-coded grouping already exists per entity type. Add visual clustering: draw a faint convex hull around same-type nodes." | 3 | 3 | 9 |
| 5 | **Graph Export (PNG/SVG/CSV)** | "Analysts need to put supply chain maps in reports. Export current view as image, or export node/edge data as CSV." Backend `GraphExporter` exists (JSON + CSV). Need PDF/SVG frontend export. | 3 | 3 | 9 |

**Table Stakes Missing**: The RelationEdge component already receives `confidence` and `weight` as data, but renders all edges identically. This is a quick win — just map confidence to opacity/dash-style and weight to thickness.

---

### 1.5 Risk Manager (Shreya Desai)

> *"The Impact Simulator answers 'what if one event happens.' But risk management is about concentration and correlation across multiple exposures."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Concentration Risk Dashboard** | "Aggregate by country, sector, or entity type: what % of the graph's edges flow through each? If 60% of semiconductor supply goes through Taiwan, that's systemic." | 5 | 3 | 15 |
| 2 | **Node Removal Simulation ("Resilience Test")** | "Different from event propagation. This is: 'What if TSMC disappears from the graph entirely? How many paths break? Which entities become isolated?' Structural fragility analysis." | 4 | 2 | 8 |
| 3 | **Risk Score per Entity** | "Composite score: centrality × (1/edge diversity) × geographic risk × confidence. One number that says 'this entity is a risk hotspot.'" | 4 | 3 | 12 |
| 4 | **Historical Simulation Replay** | "We ran a simulation 3 months ago. What happened in reality? Show prediction vs actual. Builds trust in the system." Accuracy tracker backend exists. | 3 | 2 | 6 |
| 5 | **Portfolio Overlap Analysis** | "If I give you my portfolio of 10 stocks, show me which ones share supply chain dependencies. A matrix of 'stocks A and B both depend on entities X, Y, Z.'" | 4 | 2 | 8 |

**Table Stakes Missing**: No risk scoring visible anywhere. Entities are shown as equally important, but clearly TSMC is more systemically important than a small component supplier.

---

### 1.6 Product Manager (Arjun Nair)

> *"Ship features that create daily habit loops. The graph is visited once for curiosity, never again. Fix that."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **"What Changed" Feed on Graph Landing** | "When users return to /knowledge-graph, show: '3 new entities added, 5 edges updated, 2 articles processed since your last visit.' Creates a reason to come back daily." | 4 | 3 | 12 |
| 2 | **Signal ↔ Graph Bridge (Cross-linking)** | "This is THE retention driver. Every signal detail page should show 'Supply Chain Context' with a link back to the graph. Every entity page should show 'Active signals for this entity.'" | 5 | 4 | 20 |
| 3 | **Shareable Simulation Results** | "Signal sharing already exists. Let users share an impact simulation result via URL. 'If Taiwan earthquake hits, here's the cascade.' Social proof and virality." | 3 | 3 | 9 |
| 4 | **Tier Gating** | "Free tier: entity search + entity cards. Pro tier: graph exploration, simulation, alerts. This is the monetization path for the MKG feature." | 3 | 4 | 12 |
| 5 | **Graph Health Badge on Navbar** | "Small status indicator on the Knowledge Graph nav item: green pulse if pipeline is active, orange if stale, red if down. Shows the system is alive." | 2 | 5 | 10 |

**Table Stakes Missing**: No cross-linking between SignalFlow core features (signals, watchlist, alerts) and MKG. They exist in parallel universes.

---

### 1.7 Target User — Priya (M.Com, New Trader)

> *"I understand finance. I don't understand graph theory. I need this to tell me things, not make me explore."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **"Why This Signal?" Supply Chain Context** | "When I see a signal, I want to understand the supply chain reasoning behind it. Show me: 'This STRONG_BUY was influenced by supply chain tailwinds: NVIDIA's key supplier TSMC reported capacity expansion.'" | 5 | 4 | 20 |
| 2 | **Plain-English Entity Summary** | "Instead of just showing entity name, type, and tags — give me a one-sentence AI-generated summary: 'TSMC is the world's largest semiconductor foundry, supplying chips to Apple, NVIDIA, and AMD.'" | 4 | 3 | 12 |
| 3 | **Pre-Built Simulation Scenarios** | "I don't know what to type in the simulator. Give me buttons: 'Taiwan earthquake', 'Oil price spike', 'US-China trade war', 'Samsung fab fire'. One click, instant results." | 5 | 5 | 25 |
| 4 | **Entity-to-Signal Link** | "When I'm looking at an entity (say TSMC), show me: 'Active signals: NVIDIA STRONG_BUY (92%), AMD BUY (71%)'. Connect the dots for me." | 4 | 3 | 12 |
| 5 | **Educational Tooltips** | "What does 'SUPPLIES_TO' mean exactly? What does confidence 0.72 mean? Hover tooltips that explain every concept in plain English." | 3 | 5 | 15 |

**Table Stakes Missing**: Pre-built simulation scenarios. The Impact Simulator requires the user to know what to type. Most new traders don't know which events to simulate.

---

### 1.8 Quantitative Analyst (Dr. Ankit Sharma)

> *"The propagation engine is a BFS with weight decay. The UI should expose structural metrics that reveal graph quality and risk topology."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Graph Statistics Panel** | "Node count by type, edge count by type, average degree, max-degree nodes (hubs), density, connected components. These reveal whether the graph is useful or empty." The health endpoint gives entity_count and edge_count — need a richer breakdown. | 4 | 4 | 16 |
| 2 | **Degree Distribution Chart** | "Histogram of node degrees. Power-law distribution = realistic. Uniform = probably artificial seed data. Quick quality indicator." | 3 | 4 | 12 |
| 3 | **Prediction Accuracy Dashboard** | "The AccuracyTracker records predicted vs actual impact. Show a calibration chart: 'When we predicted 70% impact, actual was X%.' Builds trust with data." | 4 | 3 | 12 |
| 4 | **Weight Distribution Analysis** | "Edge weight histogram. Are all edges at 0.5 (suspicious) or properly distributed? Reveals data quality issues." | 2 | 4 | 8 |
| 5 | **Contradiction Detection View** | "ContradictionDetector finds opposing signals for the same entity. Surface these: 'Conflicting intelligence: Source A says positive impact, Source B says negative.'" Backend exists, no UI. | 3 | 4 | 12 |

**Table Stakes Missing**: The health stats on the landing page show only 3 numbers (entity count, edge count, status). This is insufficient for quality assessment.

---

### 1.9 News/Intelligence Analyst (Priyanka Shah)

> *"The MKG processes articles to extract entities and edges. But the article pipeline is completely invisible. I can't see what the system is reading."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Article Pipeline Dashboard** | "Show me: articles ingested, articles processed, articles in DLQ, extraction success rate, source breakdown. The article_pipeline and article_dedup services exist — surface them." | 4 | 4 | 16 |
| 2 | **Entity Provenance/Lineage View** | "Click an entity → see 'Extracted from 3 articles: [Article1 from Reuters], [Article2 from Bloomberg].' The lineage_tracer service exists, just needs UI." | 4 | 4 | 16 |
| 3 | **Source Credibility Indicators** | "Not all sources are equal. Show source credibility tier (Reuters=Tier 1, Reddit=Tier 3) on entities and edges. SourceCredibilityScorer backend exists." | 3 | 4 | 12 |
| 4 | **News-to-Graph Connection** | "On the existing /news page, add a 'View in Graph' button that shows which entities were extracted from that news article. Cross-link news ↔ entities." | 3 | 3 | 9 |
| 5 | **Extraction Review Queue** | "Show me recently AI-extracted entities/edges that need human verification. Low-confidence extractions should be flagged for review." Partly in tribal knowledge audit trail. | 3 | 3 | 9 |

**Table Stakes Missing**: The entire article ingestion pipeline is invisible to the user. 50% of the backend serves articles/extraction, but the UI has zero article-related surfaces.

---

### 1.10 Frontend Engineer (Karthik Venkat)

> *"The architecture is clean — React Flow, Zustand, TypeScript strict mode. Here's what I'd build next, prioritized by technical payoff."*

**Feature Ideas:**

| # | Feature | Why It Matters | Impact | Feasibility | Score |
|---|---------|---------------|--------|-------------|-------|
| 1 | **Entity Detail Sidebar (Drawer)** | "Replace full-page navigation for entity clicks with a slide-out drawer. Keeps graph context visible. react-flow + slide-over is a well-tested pattern. Biggest UX win with minimal code." | 5 | 5 | 25 |
| 2 | **React Query Integration** | "Currently all data fetching is raw `useEffect` + `useState`. Switch to React Query (TanStack Query) for: caching, deduplication, background refetch, loading/error states. The main SignalFlow app already uses it." | 4 | 4 | 16 |
| 3 | **Graph Layout Options** | "Add a layout toggle: force-directed (current), hierarchical (dagre), radial. Different layouts reveal different patterns. Layout computation should run in requestAnimationFrame, not blocking." | 3 | 3 | 9 |
| 4 | **Subgraph Caching in Zustand** | "Cache previously fetched subgraphs with a 5-min TTL. When navigating back to a previously viewed entity, show cached data instantly, refetch in background." | 3 | 4 | 12 |
| 5 | **Skeleton Loading States** | "The graph page shows nothing during loading. Add skeleton components matching the existing SignalFlow skeleton pattern for entity cards, tables, and graph canvas." | 3 | 5 | 15 |

**Table Stakes Missing**: No loading skeletons, no data caching, `useEffect` fetch patterns instead of React Query. These are infrastructure improvements that affect every page.

---

## 2. Synthesis — Prioritized Feature Tiers

### Cross-Panel Scoring Summary

Features scored by (sum of Impact × Feasibility across relevant panelists) + consensus votes:

| Feature | Panelists Advocating | Avg Score | Consensus |
|---------|---------------------|-----------|-----------|
| Pre-Built Simulation Scenarios | Priya, UX, PM | 25 | Strong |
| Entity Detail Sidebar (Drawer) | UX, FE, all | 25 | Universal |
| Impact Heatmap Overlay on Graph | Viz, Trader, Risk | 25 | Strong |
| Signal ↔ Graph Bridge | Trader, PM, Priya, PM | 20 | Universal |
| Confidence-Weighted Edge Rendering | Viz, SC Analyst | 20 | Strong |
| Edge Provenance Indicators | SC Analyst, News | 20 | Strong |
| Context Panel from Graph | UX, FE | 20 | Strong |
| Alert Feed Page | Trader, PM | 16 | Moderate |
| Guided Scenario Walkthroughs | UX, Priya | 16 | Moderate |
| Graph Statistics Panel | Quant, SC Analyst | 16 | Moderate |
| Article Pipeline Dashboard | News, Quant | 16 | Moderate |
| Entity Provenance/Lineage View | News, SC Analyst | 16 | Moderate |
| Temporal Edge Awareness | SC Analyst, Risk | 16 | Moderate |
| Educational Tooltips | Priya, UX | 15 | Moderate |
| Skeleton Loading States | FE, UX | 15 | Moderate |
| SPoF Detection | SC Analyst, Risk | 15 | Moderate |
| Watchlist Supply Chain Overlay | Trader, Risk | 15 | Moderate |

---

### Tier 1 — Must-Have (Highest Impact × Feasibility, Fill Real Gaps)

#### T1.1: Pre-Built Simulation Scenarios

**Panel consensus**: 3 panelists (Priya, UX, PM). Score: 25. *"Most users don't know what to type. Give them buttons."*

**What it looks like:**
- On the `/knowledge-graph/simulate` page, add a **"Quick Scenarios"** section above the custom input form
- 6-8 pre-built scenario cards in a responsive grid:
  - ⚡ "Taiwan Earthquake" → trigger: TSMC, event: "Major earthquake disrupts semiconductor production"
  - 🛢️ "Oil Price Spike (+50%)" → trigger: Crude Oil, event: "Global oil prices surge 50%"
  - 🇨🇳 "US-China Trade Escalation" → trigger: China, event: "New export controls on advanced technology"
  - 🔥 "Samsung Fab Fire" → trigger: Samsung, event: "Major fabrication facility fire"
  - ⚡ "Power Grid Failure (India)" → trigger: India, event: "Widespread power outages affect manufacturing"
  - 📉 "Rare Earth Supply Shock" → trigger: China, event: "Rare earth export restrictions imposed"
  - 🏭 "Major Auto Recall" → trigger: Toyota, event: "Global vehicle recall due to defective components"
  - 💻 "Cloud Provider Outage" → trigger: AWS, event: "Extended cloud infrastructure outage"
- Each card shows: emoji icon, scenario title, 1-line description, estimated entities affected (badge)
- Clicking a card pre-fills the ImpactSimulator with trigger entity + event description and auto-runs

**Data/API needs:**
- No new API endpoints. Uses existing `POST /propagate`
- Scenario definitions are purely frontend data (static array of `{title, emoji, trigger_entity_id, event_description, max_depth, min_impact}`)
- Need to ensure the seed data includes the trigger entities referenced by scenarios (TSMC, Samsung, China, etc.)

**Integration:**
- Rendered as a sibling component to `ImpactSimulator` on the simulate page
- On click: calls `ImpactSimulator`'s `onScenarioSelect` callback to pre-fill form and auto-submit
- Alternatively, directly calls `mkgApi.runPropagation()` and displays results inline

**Key interactions:**
- Default state: scenario grid visible, custom form collapsed
- After selecting a scenario: results appear below, custom form expands for tweaking parameters
- "Customize" button on each scenario opens the form pre-filled but doesn't auto-run

**States:**
- Loading: scenario cards with skeleton animation while checking entity existence
- Error: if trigger entity not found in graph → card shows "Entity not in graph yet" with disabled state
- Success: results render identically to custom simulation

---

#### T1.2: Entity Detail Sidebar (Drawer)

**Panel consensus**: Universal (UX, FE, all). Score: 25. *"Full-page navigation for every entity click is the #1 UX problem."*

**What it looks like:**
- When clicking any entity node on the GraphCanvas or any entity name in ImpactTable/RelationshipTable → instead of navigating to `/knowledge-graph/entity/[id]`, open a slide-out panel (400px wide) from the right
- Sidebar contains:
  - Entity name + type badge (colored by type)
  - Tags pill list
  - Key stats: confidence, # connections, # incoming, # outgoing
  - **Quick Actions**: "Open Full Page", "Run Impact Sim", "View in Graph"
  - **Top Relationships** (first 5 edges, sorted by weight): source/target name, relation type, weight bar, confidence indicator
  - **Recent Activity**: last 3 edges added/updated involving this entity (if available from audit log)
- Sidebar overlay with backdrop on mobile (full-screen), slide-out with graph visible on desktop
- Close: click outside, Escape key, or X button
- Clicking "Open Full Page" navigates to `/knowledge-graph/entity/[id]` for full neighborhood graph

**Data/API needs:**
- No new API endpoints. Uses existing:
  - `GET /entities/{id}` for entity data
  - `GET /edges?source_id={id}` + `GET /edges?target_id={id}` for relationships (or `GET /graph/neighbors/{id}`)
- Could use a lightweight endpoint that returns entity + top-5 edges in a single call (optimization, not required)

**Integration:**
- New component: `EntityDrawer.tsx` in `components/graph/`
- GraphCanvas `onNodeClick` → opens drawer instead of `router.push()`
- ImpactTable entity name clicks → opens drawer
- RelationshipTable entity name clicks → opens drawer
- Entity detail page retains full functionality for deep exploration
- Zustand store: add `drawerEntityId: string | null` and `setDrawerEntityId` action

**Key interactions:**
- Open: slide from right, 300ms ease transition
- Close: slide out right, or click backdrop
- Navigate: clicking entity inside the drawer opens drawer for THAT entity (stacks breadcrumb-style or replaces)
- "Open Full Page" → closes drawer, navigates to full entity page
- "Run Impact Sim" → closes drawer, navigates to `/knowledge-graph/simulate?entity={id}`

**States:**
- Closed: drawer hidden, no overlay
- Loading: drawer open, skeleton placeholder for entity data
- Loaded: full entity card + relationships
- Error: "Failed to load entity" with retry button

---

#### T1.3: Impact Heatmap Overlay on Graph

**Panel consensus**: 3 panelists (Viz, Trader, Risk). Score: 25. *"After simulation, the graph should visually scream the answer."*

**What it looks like:**
- After running an impact simulation on `/knowledge-graph/simulate`, the graph overlay panel (already exists, `lg:col-span-2`) colors each node by its impact score:
  - Impact ≥ 0.7: **Red** (#EF4444) with pulsing glow animation
  - Impact 0.4–0.69: **Orange** (#F97316) 
  - Impact 0.1–0.39: **Yellow** (#EAB308)
  - Impact < 0.1: **Gray** (#6B7280, dimmed)
  - Trigger entity: **White** (#FFFFFF) with starburst border
- Node size scales with impact: `baseSize + (impact × 20px)` for radius
- Edges on the propagation path are highlighted with signal color (red for negative, green for positive); non-path edges dimmed to 20% opacity
- A **color legend** bar at the bottom of the graph: gradient from gray → yellow → orange → red with labels "Low Impact" → "Critical"
- Toggle button: "Show Impact Overlay" / "Show Normal View"

**Data/API needs:**
- No new endpoints. The `POST /propagate` response already contains `propagation` array with `{entity_id, impact, depth, path}` for every affected entity
- The simulate page already builds an `impactMap: Map<string, number>` and fetches the subgraph — it just doesn't use the map for coloring

**Integration:**
- Modify `EntityNode.tsx` component: accept optional `impactScore?: number` prop
  - When present, override bg color with impact-based color
  - Scale node size proportionally
- Modify `GraphCanvas.tsx`: accept optional `impactOverlay?: Map<string, number>` prop
  - Pass impact score to each EntityNode
  - Update edge styling for path edges
- Modify `simulate/page.tsx`: pass `graphData.impactMap` to GraphCanvas as overlay
- Add toggle state: `const [showOverlay, setShowOverlay] = useState(true)`

**Key interactions:**
- Overlay appears automatically after simulation completes
- Toggle switch to disable overlay and view normal graph topology
- Hovering an impacted node shows tooltip: "Impact: 72% | Depth: 2 hops | Path: TSMC → Apple → Foxconn"
- Clicking an impacted node opens Entity Drawer (T1.2)

**States:**
- No simulation: normal graph rendering (no overlay)
- Simulation running: graph shows loading skeleton
- Simulation complete: overlay active by default
- Toggle off: normal rendering restored

---

#### T1.4: Signal ↔ Graph Bridge

**Panel consensus**: Universal (Trader, PM, Priya, PM). Score: 20. *"The #1 gap — signals and graph live in separate worlds."*

**What it looks like:**

**Part A — On Signal Detail Page (`/signal/[id]`):**
- New collapsible section: **"Supply Chain Context"** below the AI Reasoning panel
- Shows (when MKG has data for this symbol):
  - Supply chain risk score: gauge (0–100%), color-coded
  - Risk factors: 2-3 bullet points from `SignalBridge.enrich_signal()` output
  - Affected companies: top 3 with impact scores
  - "Explore Supply Chain →" link to `/knowledge-graph/entity/{matched_entity_id}`
  - "Run Impact Simulation →" link to `/knowledge-graph/simulate?entity={matched_entity_id}`
- When MKG has NO data for this symbol: show a subtle note: "No supply chain data available for this symbol yet."

**Part B — On Entity Detail Page (`/knowledge-graph/entity/[id]`):**
- New section: **"Active Trading Signals"** showing SignalFlow signals whose symbol matches this entity
- Shows: signal type badge (BUY/SELL/HOLD), confidence gauge, current price, created date
- Each signal links to `/signal/[id]` for full detail
- When no signals match: "No active signals for this entity."

**Data/API needs:**
- **Part A**: New lightweight endpoint or use existing `SignalBridge.enrich_signal()`:
  - Option 1 (preferred): `GET /api/v1/signals/{id}/supply-chain-context` → returns enrichment data
  - Option 2: Frontend calls MKG search API to find matching entity, then fetches neighbors
  - Entity matching: needs a symbol → entity_id lookup. Could search MKG entities by symbol name
- **Part B**: Frontend calls SignalFlow API `GET /api/v1/signals?symbol={entity_name}` to find matching signals
  - May need fuzzy matching: entity name "Taiwan Semiconductor" should match signal symbol "TSM" or "TSMC"

**Integration:**
- Part A: New component `SupplyChainContext.tsx` in `components/signals/`
- Part B: New component `EntitySignals.tsx` in `components/graph/`
- Part A added to signal detail page (`/signal/[id]/page.tsx`)
- Part B added to entity detail page (`/knowledge-graph/entity/[id]/page.tsx`)

**Key interactions:**
- Part A: initially collapsed to not overwhelm; expand to see full context
- Part B: shows top 3 most recent active signals; "View all signals" link if more exist
- Both sections have loading and empty states

**States:**
- Loading: skeleton placeholder
- Data available: full context rendered
- No data: subtle empty state message (not an error)
- Error: "Failed to load supply chain context" with retry

---

#### T1.5: Confidence-Weighted Edge Rendering

**Panel consensus**: 2 panelists (Viz, SC Analyst). Score: 20. *"All edges look the same. This is a 30-minute fix with massive visual payoff."*

**What it looks like:**
- In `RelationEdge.tsx` (custom React Flow edge component):
  - **Confidence → Stroke style**:
    - confidence > 0.8: solid line
    - 0.5 ≤ confidence ≤ 0.8: dashed line (`strokeDasharray: "8,4"`)
    - confidence < 0.5: dotted line (`strokeDasharray: "2,4"`)
  - **Weight → Stroke width**:
    - `strokeWidth = 1 + (weight × 3)` (range: 1px to 4px)
  - **Confidence → Opacity**:
    - `opacity = 0.3 + (confidence × 0.7)` (range: 0.3 to 1.0)
- Edge label shows relation type + confidence badge (e.g., "SUPPLIES_TO · 87%")
- Hovering an edge shows tooltip with full details: weight, confidence, source, valid_from/valid_until

**Data/API needs:**
- No new endpoints. `confidence` and `weight` are already in every edge object from `GET /edges` and `GET /graph/subgraph`

**Integration:**
- Modify `RelationEdge.tsx`: use `data.confidence` and `data.weight` for visual encoding
- No other components change

**Key interactions:**
- Purely visual — no new interactions
- FilterPanel confidence slider already filters edges; this adds visual feedback for included edges
- Edge tooltip on hover (enhance existing or add)

---

### Tier 2 — High Value (Strong Impact, Moderate Effort)

#### T2.1: Edge Provenance Indicators

**What it looks like:**
- On every edge (in graph view and relationship table), show a small badge:
  - 🤖 "AI-extracted" (source = article extraction)
  - 👤 "Expert-verified" (source = tribal knowledge)
  - 📊 "Seed data" (source = seed_loader)
- On every entity, same badge system
- In RelationshipTable: new "Source" column with badge + source name

**Data/API needs:**
- Edges already have `source` field in metadata. Need to standardize values
- Entity lineage available via `GET /lineage/entity/{id}`
- Might need `source_type` field added to edge schema (or infer from `source` string)

**Integration:**
- New component: `ProvenanceBadge.tsx` — renders appropriate icon + label
- Add to `RelationEdge.tsx`, `EntityCard.tsx`, `RelationshipTable.tsx`

---

#### T2.2: Alert Feed Page

**What it looks like:**
- New page: `/knowledge-graph/alerts`
- Vertical feed of alert cards, newest first
- Each alert card:
  - Severity badge (critical/high/medium/low with SEVERITY_COLORS)
  - Title and message
  - Impact score bar (0–1)
  - Timestamp (relative: "2 hours ago")
  - "View in Graph" button → opens affected entity with impact overlay
  - Expandable: causal chain narrative
- Filter bar at top: severity filter (multi-select pills), date range
- Badge count on navigation: "Knowledge Graph" nav item shows unseen alert count

**Data/API needs:**
- Uses existing `GET /alerts?limit=N` endpoint
- Alerts are generated by `AlertSystem.generate_alerts()` from causal chains
- Need to trigger alert generation periodically or on propagation events
- May need `GET /alerts?since=ISO&severity=critical,high` for filtering

**Integration:**
- New page: `/knowledge-graph/alerts/page.tsx`
- New component: `AlertCard.tsx` in `components/graph/`
- Add route to navigation
- Zustand store: `alerts[]` and `unseenAlertCount` (already in `graphStore.ts`)
- Nav "Knowledge Graph" item shows alert badge

---

#### T2.3: Guided Scenario Walkthroughs

**What it looks like:**
- On the `/knowledge-graph` landing page, new section: **"Learn by Exploring"**
- 3-4 guided walkthrough cards:
  - 🏭 "Semiconductor Supply Chain" — "Explore how chips flow from Taiwan to your phone."
  - 🛢️ "Oil Price Ripple Effects" — "See how energy prices cascade through manufacturing."
  - 🚗 "EV Battery Dependencies" — "Trace the critical minerals powering electric vehicles."
- Clicking a walkthrough opens a step-by-step guided experience:
  1. Step 1: "Let's start with TSMC" → highlights TSMC entity, shows card
  2. Step 2: "Expand to see its customers" → expands graph 1 hop
  3. Step 3: "Now let's simulate a disruption" → auto-fills impact simulator
  4. Step 4: "See the results" → shows impact table with narrated insights
- Each step has: instruction text, highlighted UI elements, "Next" / "Back" buttons
- Powered by a simple state machine: `{steps: [], currentStep: number}`

**Data/API needs:**
- No new endpoints. Walkthrough scripts are static frontend data
- Need pre-validated entity IDs that exist in the seed data
- Steps reference existing API calls (getEntity, getSubgraph, runPropagation)

**Integration:**
- New component: `GuidedTour.tsx` (or extend existing `GuidedTour` from shared components)
- Walkthrough definitions: static JSON/TS objects in `lib/mkg-walkthroughs.ts`
- Added to landing page as a section

---

#### T2.4: Graph Statistics Panel (Enhanced Health)

**What it looks like:**
- On `/knowledge-graph` landing page, replace the 3 simple stat cards with an expandable **"Graph Health"** panel:
  - **Summary row**: Entity count, Edge count, Status (existing)
  - **Expandable detail** (click "Show Details"):
    - By entity type: bar chart (Company: 45, Facility: 12, Country: 8, ...)
    - By relation type: bar chart (SUPPLIES_TO: 67, DEPENDS_ON: 34, ...)
    - Average weight: number
    - Average confidence: number with quality indicator (>0.7 = "Good", <0.5 = "Needs Review")
    - Most connected entities (top 5 by degree): name + degree count
    - Data freshness: "Newest edge: 2 hours ago" / "Most edges older than 30 days"
- Optionally accessible as a `/knowledge-graph/admin` page with fuller metrics

**Data/API needs:**
- Existing `GET /graph/health` returns basic counts
- Need new endpoint: `GET /graph/stats` returning:
  ```json
  {
    "entity_counts_by_type": {"Company": 45, "Facility": 12, ...},
    "edge_counts_by_type": {"SUPPLIES_TO": 67, ...},
    "avg_weight": 0.62,
    "avg_confidence": 0.74,
    "top_entities_by_degree": [{"id": "...", "name": "TSMC", "degree": 23}, ...],
    "newest_edge_timestamp": "2026-04-07T10:30:00Z",
    "oldest_edge_timestamp": "2026-01-15T08:00:00Z"
  }
  ```
- This is a new backend endpoint aggregating from `find_entities()` and `find_edges()`

**Integration:**
- New component: `GraphStatsPanel.tsx` in `components/graph/`
- Uses Recharts (already in frontend dependencies) for bar charts
- Replaces or extends the health stats section on landing page

---

#### T2.5: Temporal Edge Awareness

**What it looks like:**
- In RelationshipTable: new "Freshness" column showing age of each edge
  - "2 days ago" (green text) → fresh
  - "45 days ago" (yellow text) → aging
  - "6 months ago" (red text) → stale
  - "No date" (gray text) → unknown
- In graph view: edges older than 90 days are rendered with a faint orange tint + dashed style
- In FilterPanel: add **"Freshness"** toggle:
  - "All edges" (default)
  - "Fresh only (< 30 days)"
  - "Exclude stale (< 90 days)"
- Edge tooltip shows `valid_from`, `valid_until`, and `updated_at` dates

**Data/API needs:**
- No new endpoints. `valid_from`, `valid_until`, `created_at`, `updated_at` are already on every edge from `GET /edges`
- Freshness is computed client-side from `updated_at` vs current date

**Integration:**
- Modify `RelationshipTable.tsx`: add freshness column
- Modify `RelationEdge.tsx`: use `updated_at` for staleness styling
- Modify `FilterPanel.tsx`: add freshness filter option
- Zustand store: add `freshnessFilter: 'all' | 'fresh' | 'exclude-stale'` to filters

---

#### T2.6: Entity Provenance/Lineage View

**What it looks like:**
- On entity detail page and in entity drawer: new **"Data Sources"** section
- Shows a provenance chain:
  - "This entity was extracted from:"
    - 📰 "TSMC Q3 Earnings Report" (Reuters, 2026-03-15) — confidence: 0.92
    - 📰 "Semiconductor Supply Chain Analysis" (Bloomberg, 2026-02-28) — confidence: 0.87
  - "Verified by:"
    - 👤 "Dr. Kapoor" (Expert annotation, 2026-03-20)
- Each source article is clickable → opens article detail (if article pipeline UI exists) or shows article URL

**Data/API needs:**
- Uses existing `GET /lineage/entity/{entity_id}` from compliance routes
- Lineage tracer backend already tracks entity → article mappings

**Integration:**
- New component: `EntityLineage.tsx` in `components/graph/`
- Added to entity detail page and entity drawer
- New MKG API client function: `mkgApi.getEntityLineage(id)`

---

#### T2.7: Skeleton Loading States

**What it looks like:**
- Every data-loading section gets a skeleton placeholder matching its loaded layout:
  - Entity card: gray rectangle for image, gray lines for name/type/tags
  - Graph canvas: subtle animated placeholder with faint node/edge outlines
  - Impact table: 5 rows of gray animated bars
  - Statistics panel: gray number blocks with shimmer animation
- Match existing SignalFlow `<Skeleton>` component patterns

**Data/API needs:** None — purely frontend.

**Integration:**
- Import/extend existing `Skeleton` component from `components/shared/Skeleton`
- Add skeleton variants to: EntityCard, ImpactTable, RelationshipTable, GraphCanvas, health stats
- Replace current "Loading..." text or blank states

---

#### T2.8: React Query Integration

**What it looks like:**
- No visual changes — infrastructure improvement
- Replace `useEffect` + `useState` fetch patterns with `useQuery` / `useMutation` from TanStack Query
- Benefits: automatic caching, dedup, background refetch, loading/error states, retry logic
- New hook file: `hooks/useMKGQueries.ts` with typed query hooks:
  - `useEntity(id)` → `useQuery(['mkg-entity', id], () => mkgApi.getEntity(id))`
  - `useSubgraph(id, depth)` → `useQuery(['mkg-subgraph', id, depth], ...)`
  - `useGraphHealth()` → `useQuery(['mkg-health'], ...)`
  - `useEntitySearch(query)` → `useQuery(['mkg-search', query], ..., { enabled: query.length > 0 })`
  - `usePropagation()` → `useMutation(mkgApi.runPropagation)`
  - `useAlerts(limit)` → `useQuery(['mkg-alerts', limit], ...)`

**Data/API needs:** None — wraps existing API client.

**Integration:**
- Uses existing `QueryProvider` (React Query provider already set up in main SignalFlow app)
- Migrate each page from `useEffect` to `useQuery` hooks
- Can be done incrementally: one page at a time

---

### Tier 3 — Nice-to-Have (Good Ideas, Lower Priority or Higher Effort)

#### T3.1: Path Finder (A → B)

- Enter two entities → find all paths up to N hops
- **Needs new backend endpoint**: `GET /graph/paths/{sourceId}/{targetId}?max_depth=4`
- Backend needs all-paths BFS algorithm (not currently in graph storage interface)
- UI: path list with cumulative weight, highlight selected path on graph canvas

#### T3.2: Watchlist Supply Chain Overlay

- Cross-reference user's SignalFlow watchlist symbols with MKG entities
- Show shared dependencies between watchlisted stocks
- **Needs**: symbol → entity matching logic, watchlist API integration
- High value but requires non-trivial cross-system integration

#### T3.3: Node Removal Simulation ("Resilience Test")

- "Remove Entity X from the graph → how many paths break?"
- **Needs new backend endpoint**: structural fragility analysis (not event propagation)
- Different from Impact Simulator: this is graph topology analysis, not event cascading

#### T3.4: Concentration Risk Dashboard

- Aggregate edges by country/sector → show concentration percentages
- **Needs**: entity metadata with country/sector tags consistently populated
- Pie charts / treemaps by geography and sector
- High value for portfolio managers, but depends on data quality

#### T3.5: Graph Export (PNG/SVG/CSV)

- Export current graph view as image (React Flow has `toObject()` for SVG)
- Export entity/edge lists as CSV (backend `GraphExporter` already supports JSON/CSV)
- "Share as image" for reports
- **Needs**: `reactflow.toObject()` → SVG conversion, download handler

#### T3.6: Prediction Accuracy Dashboard

- Show historical accuracy: predicted impact vs actual outcome
- Calibration chart: "When we predicted 70%, actual was X%"
- **Uses existing**: `GET /accuracy` endpoint + AccuracyTracker
- **Needs**: Recharts calibration curve component, may need more historical data

#### T3.7: Contradiction Detection View

- Surface conflicting intelligence: "Source A says positive, Source B says negative"
- **Uses existing**: `ContradictionDetector` service
- **Needs**: New API endpoint to expose contradictions, UI component to display them

#### T3.8: "What Changed" Feed

- Show graph mutations since last visit: new entities, updated edges, new articles
- **Needs new backend endpoint**: `GET /graph/diff?since=ISO` returning changelog
- Could use audit logger entries as data source
- Daily email/notification potential

#### T3.9: Article Pipeline Dashboard

- Articles ingested/processed/failed, DLQ depth, extraction success rate
- **Uses existing**: `GET /articles/stats/summary`, `GET /articles/dlq`
- More relevant for admin/ops users than traders
- Could live on `/knowledge-graph/admin`

#### T3.10: Educational Tooltips

- Hover tooltips on every graph concept: "SUPPLIES_TO", "confidence: 0.72", "propagation depth"
- Static content, no API needed
- Important for Priya persona but can be added incrementally

---

## 3. Anti-Patterns to Avoid

| Anti-Pattern | Description | Prevention |
|---|---|---|
| **Parallel Universes** | Signals and graph exist in separate navigational worlds with no cross-links | T1.4 (Signal ↔ Graph Bridge) must be in v1 |
| **Build It and They'll Explore** | Assuming users will freely explore a graph because it exists | T1.1 pre-built scenarios + T2.3 guided walkthroughs |
| **Equal Edges Fallacy** | Rendering all edges identically despite having confidence and weight data | T1.5 (confidence-weighted rendering) is a 30-minute fix |
| **Page-Per-Click** | Navigating to a new page for every entity click, losing spatial context | T1.2 (entity drawer) — slide-out preserves context |
| **Stale Data Silence** | Showing 6-month-old relationships without any freshness indicator | T2.5 (temporal edge awareness) |
| **Admin-First** | Building article pipeline dashboards and audit trails before user-facing features | Prioritize Tier 1 (user-facing) before Tier 3 (admin) |
| **Feature Gating Last** | Building everything ungated, then retroactively adding tier restrictions | Design tier gates into components from the start |
| **Desktop-Only Graph** | Building interactive graph features that break on mobile | Keep ImpactTable and CausalNarratives as mobile-first; GraphCanvas is desktop bonus |

---

## 4. Implementation Sequence Recommendation

```
Phase 1 — Quick Wins (1-2 days each, massive UX improvement)
├── T1.5: Confidence-Weighted Edge Rendering (30 min)
├── T1.3: Impact Heatmap Overlay (2-3 hours, data already flows)
├── T2.7: Skeleton Loading States (2-3 hours)
└── T2.5: Temporal Edge Awareness (3-4 hours)

Phase 2 — Core Extensions (1-2 days each)
├── T1.1: Pre-Built Simulation Scenarios (half day)
├── T1.2: Entity Detail Sidebar/Drawer (1 day)
├── T2.1: Edge Provenance Indicators (half day)
└── T2.8: React Query Integration (1 day, incremental)

Phase 3 — Bridge & Discovery (1-2 days each, cross-system)
├── T1.4: Signal ↔ Graph Bridge (1-2 days, needs entity matching)
├── T2.2: Alert Feed Page (1 day)
├── T2.4: Graph Statistics Panel (1 day, needs new backend endpoint)
└── T2.6: Entity Provenance/Lineage View (half day)

Phase 4 — Guided Experience
├── T2.3: Guided Scenario Walkthroughs (1-2 days)
├── T3.10: Educational Tooltips (incremental)
└── T3.8: "What Changed" Feed (1 day + new backend endpoint)

Phase 5 — Advanced (2+ days each, new backend work)
├── T3.1: Path Finder
├── T3.2: Watchlist Overlay
├── T3.3: Resilience Test
├── T3.4: Concentration Risk Dashboard
└── T3.5: Graph Export
```

---

## 5. New Components Summary

| Component | File | Used By |
|-----------|------|---------|
| `ScenarioCards.tsx` | `components/graph/ScenarioCards.tsx` | Simulate page |
| `EntityDrawer.tsx` | `components/graph/EntityDrawer.tsx` | All graph pages, impact table |
| `ProvenanceBadge.tsx` | `components/graph/ProvenanceBadge.tsx` | EntityCard, RelationEdge, RelationshipTable |
| `AlertCard.tsx` | `components/graph/AlertCard.tsx` | Alert feed page |
| `GraphStatsPanel.tsx` | `components/graph/GraphStatsPanel.tsx` | Landing page |
| `EntityLineage.tsx` | `components/graph/EntityLineage.tsx` | Entity detail, entity drawer |
| `SupplyChainContext.tsx` | `components/signals/SupplyChainContext.tsx` | Signal detail page |
| `EntitySignals.tsx` | `components/graph/EntitySignals.tsx` | Entity detail page |

---

## 6. New API Endpoints Needed

| Endpoint | Method | Purpose | Tier |
|----------|--------|---------|------|
| `GET /graph/stats` | GET | Detailed graph statistics (counts by type, degree distribution, top nodes) | T2.4 |
| `GET /graph/paths/{source}/{target}` | GET | All paths between two entities | T3.1 |
| `GET /graph/diff?since=ISO` | GET | Change log since timestamp | T3.8 |
| `GET /signals/{id}/supply-chain-context` | GET | MKG enrichment data for a signal | T1.4 |

All Tier 1 and most Tier 2 features work with **existing API endpoints**.

---

## 7. Zustand Store Extensions

```typescript
// Additions to graphStore.ts

interface GraphState {
  // ... existing state ...
  
  // Entity Drawer
  drawerEntityId: string | null;
  setDrawerEntityId: (id: string | null) => void;

  // Impact overlay
  impactOverlay: Map<string, number> | null;
  showImpactOverlay: boolean;
  setImpactOverlay: (overlay: Map<string, number> | null) => void;
  setShowImpactOverlay: (show: boolean) => void;

  // Freshness filter
  freshnessFilter: 'all' | 'fresh' | 'exclude-stale';
  setFreshnessFilter: (filter: 'all' | 'fresh' | 'exclude-stale') => void;

  // Unseen alert count
  unseenAlertCount: number;
  setUnseenAlertCount: (count: number) => void;
}
```

---

## 8. Existing Code Modifications Required

| File | Change | Tier |
|------|--------|------|
| `RelationEdge.tsx` | Map confidence → dash style, weight → width, confidence → opacity | T1.5 |
| `EntityNode.tsx` | Accept `impactScore` prop → color/size node | T1.3 |
| `GraphCanvas.tsx` | Accept `impactOverlay` prop → pass to nodes/edges | T1.3 |
| `simulate/page.tsx` | Add ScenarioCards section, pass impactMap to GraphCanvas | T1.1, T1.3 |
| `entity/[id]/page.tsx` | Add EntitySignals section, use EntityDrawer for inner navigation | T1.4, T1.2 |
| `knowledge-graph/page.tsx` | Add guided walkthrough section, enhanced stats panel | T2.3, T2.4 |
| `RelationshipTable.tsx` | Add freshness column, provenance column | T2.5, T2.1 |
| `FilterPanel.tsx` | Add freshness filter toggle | T2.5 |
| `graphStore.ts` | Add drawer state, overlay state, freshness filter | T1.2, T1.3, T2.5 |
| Signal detail page (`/signal/[id]`) | Add SupplyChainContext component | T1.4 |

---

*This spec was generated from a simulated 10-person expert panel brainstorm. Each feature was independently evaluated for Impact (1-5) × Feasibility (1-5) and cross-validated for consistency. Implementation should proceed in the phase order described in Section 4.*
