# MKG Graph Visualization UI — Design & Requirements Spec

> **Status**: Draft — Brainstorm & Expert Panel Review  
> **Date**: 7 April 2026  
> **Author**: AI-assisted design (Claude + domain review)  
> **Module**: Market Knowledge Graph (MKG) Web Interface  

---

## Executive Summary

The MKG currently has a powerful backend (50+ REST endpoints, propagation engine, causal chain builder, alert system) but **zero visual interface**. Users interact only through raw API calls or indirect signal enrichment.

This spec proposes a web interface that lets users **see, explore, and act on** the supply chain knowledge graph — turning a hidden analytical engine into a visible strategic advantage.

**Core thesis**: The graph UI is not a data visualization tool — it's a **decision-support surface** that answers: *"If event X happens, who gets hurt, who benefits, and what should I trade?"*

---

## 1. Expert Panel Review

### 1.1 Supply Chain Analyst

**Priorities:**
1. **Multi-hop dependency tracing** — "Show me everything 3 hops downstream from TSMC." When a tsunami hits Taiwan, I need to see not just TSMC's direct customers but the cascade: TSMC → Apple → Foxconn → component suppliers.
2. **Single-point-of-failure detection** — Highlight entities where removing one node fractures the graph. If 80% of advanced chips flow through one foundry, that's a systemic risk.
3. **Temporal edge awareness** — Supply relationships change. A "SUPPLIES_TO" edge from 2023 might be stale. Show me which relationships are current vs historical.
4. **Concentration heat mapping** — "What percentage of my portfolio's supply chain runs through Country X?" Aggregate by geography, sector, or entity type.

**Concerns:**
- Stale data is worse than no data. Every edge needs a freshness indicator.
- The graph must distinguish confirmed relationships from AI-extracted (lower confidence) ones.

### 1.2 Financial Trader / Portfolio Manager

**Priorities:**
1. **Event impact simulation** — "If Taiwan earthquake happens, show me the downstream P&L impact on my watchlist." This is THE killer feature — connecting graph topology to portfolio positions.
2. **Signal-to-graph linking** — When I see a STRONG_BUY signal for NVIDIA, I want one click to see its supply chain graph and understand WHY the signal fired (MKG context).
3. **Alert-driven graph highlighting** — When a critical alert fires (e.g., "Samsung fab shutdown"), the affected subgraph should light up in real-time on the dashboard.
4. **Pair trade discovery** — "Show me companies that compete with Apple's suppliers." Graph structure reveals non-obvious competitive relationships for pair trading.

**Concerns:**
- Speed matters more than beauty. If the graph takes 3 seconds to load, I'll never use it.
- Don't drown me in nodes. Default views must be curated, not "show everything."

### 1.3 UX/UI Designer

**Priorities:**
1. **Progressive disclosure** — Start with the simplest useful view (entity card + immediate neighbors). Let users drill deeper on demand. Never show 10K nodes at once.
2. **Context-preserving navigation** — When I click an entity, keep my previous context visible. Breadcrumb trail or split-pane, not full page replace.
3. **Semantic zoom** — At high zoom: show entity names, confidence scores, edge labels. At low zoom: aggregate clusters by sector/geography, show density heatmap.
4. **Mobile-first graph summary** — Full graph interaction is desktop. On mobile, show text-based impact lists and simplified relationship cards, not a force-directed graph.
5. **Consistent dark theme** — Must match SignalFlow's existing terminal aesthetic (bg: #0A0B0F, accents: #6366F1 purple, green/red for buy/sell).

**Concerns:**
- Force-directed layouts are chaotic for large graphs. Consider hierarchical or radial layouts for supply chains.
- Avoid the "hairball" anti-pattern — dense graphs with no structure are useless.
- Every graph element needs a hover tooltip, not just decoration.

### 1.4 Data Engineer

**Priorities:**
1. **Client-side performance** — At 50K entities, you cannot render all nodes. Implement server-side subgraph extraction with max 500 nodes per view. Paginate or cluster the rest.
2. **Lazy loading** — Initial load should fetch only the entity + 1-hop neighbors. Each "expand" click fetches the next hop. Never pre-fetch the whole graph.
3. **WebSocket for real-time** — When the propagation engine fires (new event → graph mutation), push incremental updates to the UI. Don't require page refresh.
4. **Caching strategy** — Subgraph payloads should be cacheable for 5 minutes. Entity metadata rarely changes, cache aggressively. Edge weights change more often, shorter TTL.

**Concerns:**
- Graph layout computation is expensive. Do it server-side or in a Web Worker — never block the main thread.
- Serialization matters: a 500-node subgraph with properties could be 500KB as JSON. Consider field selection or a denser format.

### 1.5 Knowledge Graph Expert

**Priorities:**
1. **Path exploration** — "Find all paths between Entity A and Entity B." This is fundamental for understanding indirect dependencies.
2. **Graph statistics panel** — Node degree distribution, average path length, clustering coefficient, connected components. These reveal structural health of the knowledge base.
3. **Entity resolution UI** — When the system detects potential duplicates ("TSMC" vs "Taiwan Semiconductor Manufacturing Company"), surface them for human review.
4. **Confidence-weighted rendering** — High-confidence edges should be bold/solid. Low-confidence edges should be dashed/faded. Let users filter by confidence threshold.
5. **Schema/ontology view** — A meta-view showing entity types and relationship types as a schema diagram. "We have 8 entity types connected by 14 relationship types."

**Concerns:**
- Don't confuse network visualization with knowledge graph exploration. The UI must support structured queries, not just pretty pictures.
- Allow SPARQL-like structured querying for power users (e.g., "Find all companies that SUPPLIES_TO any entity that COMPETES_WITH NVIDIA").

### 1.6 Risk Manager

**Priorities:**
1. **Concentration risk dashboard** — "What percentage of my supply chain graph is concentrated in one country/sector/entity?" Flag when a single node's degree exceeds a threshold.
2. **Scenario simulation** — "What if we remove entity X? How many paths break? Which downstream entities lose all inbound edges?" This is a fragility/resilience analysis.
3. **Historical event replay** — "Show me the graph state as of the 2024 Taiwan earthquake. What propagated? Was our prediction accurate?" Replay past events for learning.
4. **Risk scoring overlay** — Each entity should show an aggregate risk score based on: supply chain centrality, edge confidence, geographical concentration, and recent event frequency.

**Concerns:**
- Risk data must be current. A "green" risk indicator based on month-old data gives false confidence.
- Must clearly distinguish between "data-driven risk" and "modeled risk" (propagation estimates).

### 1.7 Product Manager

**Priorities:**
1. **MVP is the Impact Simulator** — The single feature that justifies the graph UI is: "Type an event → see the ripple." Everything else is supporting cast. Ship this first.
2. **Engagement hook: "Your portfolio's hidden risks"** — First-time users should see a pre-computed analysis of their watchlist's supply chain dependencies. Instant value.
3. **Shareability** — Signal sharing already exists. Add "Share this supply chain analysis" with a public link showing a static graph snapshot.
4. **Retention driver: "Daily graph mutations"** — Show users what changed in their graph today: 3 new edges added, 2 confidence scores updated, 1 new entity extracted from news.

**Concerns:**
- Don't build a generic graph explorer. 90% of users won't explore. Build opinionated views that answer specific questions.
- Feature gating: Free tier sees entity cards only. Pro tier gets full graph exploration and simulation.

### 1.8 Accessibility Expert

**Priorities:**
1. **Text alternatives for graphs** — Every graph view must have an equivalent tabular/text representation. Screen readers can't parse SVG node-link diagrams.
2. **Keyboard navigation** — Tab through entities, Enter to expand, Escape to go back. Arrow keys for graph traversal.
3. **Color-blind safe palettes** — Don't rely on red/green alone. Use shape, pattern, and label to encode entity types and edge directions.
4. **Focus management** — When expanding a node, move focus to the newly revealed content. Don't lose the user's place.

**Concerns:**
- Interactive graph visualizations are inherently accessibility-challenged. The tabular fallback must be genuinely usable, not a checkbox exercise.

### 1.9 Finance Educator

**Priorities:**
1. **"What is this?" tooltips** — Every entity type, relationship type, and metric should have a plain-English explanation. "SUPPLIES_TO means Company A provides materials or components to Company B."
2. **Guided scenarios** — Pre-built "What happens if..." walkthroughs. Example: "Let's trace what happens when oil prices spike. Click on 'Crude Oil' to see which companies are affected."
3. **Confidence score education** — When showing a 72% confidence edge, explain: "This relationship was extracted from 3 news articles and confirmed by 1 expert. The confidence reflects the certainty of this supply chain link."
4. **Impact chain narratives** — The CausalChainBuilder already generates narratives. Surface them prominently alongside the graph, not as metadata.

**Concerns:**
- Don't assume the user knows what a "knowledge graph" is. Frame it as "supply chain map" or "connection map."

### 1.10 Security & Compliance Officer

**Priorities:**
1. **Data provenance visibility** — Every entity/edge should link back to its source (which article, which extraction, which confidence score). The lineage API already exists — surface it.
2. **PII redaction in views** — If a Person entity has been flagged by the PII detector, redact sensitive details in the UI.
3. **Audit trail** — Log every graph interaction (who viewed what, when). Use the existing audit logger.
4. **Disclaimer on every page** — "Data sourced from AI extraction. Not verified. Not investment advice."
5. **Tier gating enforcement** — Sensitive graph data (detailed edge weights, propagation scores) should be gated behind Pro tier.

**Concerns:**
- The graph could reveal material non-public information if fed with privileged data sources. Ensure SEBI/regulatory compliance disclaimers are prominent.

---

## 2. User Personas & Use Cases

### Persona 1: Priya — Active Trader (Primary User)

**Background**: M.Com in Finance, 28, beginning active trading. Uses SignalFlow daily for signals. Checks on phone during commute, laptop at home.

**Technical sophistication**: Moderate. Understands financial concepts deeply but not graph theory.

**Key questions she wants answered:**
- "Why did SignalFlow give NVIDIA a STRONG_BUY? What supply chain factors drove it?"
- "I'm considering buying Tata Motors. What are its hidden supply chain risks?"
- "Breaking news: earthquake in Japan. Which of my watchlist stocks are affected?"
- "How reliable are these supply chain connections?"

**Workflows:**
1. **Signal drill-down**: Sees STRONG_BUY → clicks signal → sees "MKG Context" section → views supply chain for that symbol → understands reasoning
2. **Event reaction**: Hears news event → opens Impact Simulator → types event → sees affected entities → checks if any match her portfolio
3. **Research before buying**: Searches for a company → sees its supply chain neighborhood → identifies risks before entering a position

**Mobile needs**: Text-based impact summaries, entity cards with key metrics. No graph interaction on phone.

### Persona 2: Raj — Portfolio Manager (Power User)

**Background**: CFA, 35, manages a ₹50Cr portfolio. Needs systematic risk assessment across holdings.

**Technical sophistication**: High. Comfortable with data tools, has used Bloomberg Terminal.

**Key questions:**
- "Across my portfolio of 25 stocks, what's my concentration risk in semiconductors?"
- "If China imposes export controls on rare earths, which of my holdings are affected and by how much?"
- "Show me the shortest path between Company A and Company B — are they supply chain connected?"
- "What changed in my supply chains this week?"

**Workflows:**
1. **Portfolio overlay**: Uploads/links portfolio → sees aggregate supply chain heatmap → identifies concentration risk
2. **Scenario planning**: Selects a simulated event → sees impact propagation across entire portfolio → adjusts positions
3. **Weekly review**: Checks "Graph Changes" feed → sees new entities, updated confidence, broken chains

### Persona 3: Meera — Research Analyst

**Background**: MBA, 30, works at a brokerage. Creates research reports on sectors.

**Technical sophistication**: High. Needs exportable data and shareable views.

**Key questions:**
- "Map the entire semiconductor supply chain, 4 levels deep."
- "Which companies are single points of failure in the EV battery supply chain?"
- "How has TSMC's supplier network changed over the past 6 months?"
- "Export this graph as an image for my research report."

**Workflows:**
1. **Sector deep dive**: Selects "Semiconductor" sector → explores full ecosystem graph → exports key subgraphs
2. **SPoF analysis**: Runs fragility analysis → identifies high-centrality nodes → documents in report
3. **Temporal comparison**: Views graph at two time points → compares structural changes

### Persona 4: Amit — System Administrator

**Background**: DevOps engineer, 32, maintains SignalFlow infrastructure.

**Technical sophistication**: Very high. Needs operational views, not market insights.

**Key questions:**
- "How many entities and edges are in the graph? Is storage growing as expected?"
- "Are the extraction pipelines working? What's the DLQ depth?"
- "Which data sources have the lowest confidence? Are there stale edges?"
- "What's the API latency for graph queries?"

**Workflows:**
1. **Health monitoring**: Checks graph health dashboard → reviews entity/edge counts, pipeline metrics, error rates
2. **Data quality review**: Filters entities by confidence < 0.5 → reviews potential extraction errors → manually corrects or removes
3. **Source audit**: Reviews which news sources contributed the most entities → checks source credibility scores

### Persona 5: Dr. Kapoor — Domain Expert (Tribal Knowledge Contributor)

**Background**: 55, retired semiconductor industry veteran. Contributes tribal knowledge to the graph.

**Technical sophistication**: Low for tech tools, extremely high for domain.

**Key questions:**
- "The system says Company X supplies chips to Company Y. That's wrong — they stopped in 2023. How do I correct this?"
- "I know that GlobalFoundries has a secret second-source agreement with AMD. How do I add this?"
- "Show me all the relationships the AI extracted this week so I can verify them."

**Workflows:**
1. **Review & correct**: Browses recently extracted entities/edges → verifies or disputes → adds corrections with notes
2. **Add knowledge**: Opens tribal knowledge input → adds a relationship with confidence and notes → sees it appear in graph
3. **Quality audit**: Filters by AI-extracted (low confidence) → reviews for accuracy → approves or rejects

---

## 3. Feature Requirements

### P0 — MVP (Must Have)

#### F1: Impact Simulator ("What If?" Tool)
- **Description**: User types a natural-language event or selects a trigger entity → system runs propagation → displays affected entities with impact scores, causal narratives, and severity ratings.
- **User value**: Answers "If X happens, who gets hurt?" — the single most valuable graph feature.
- **Example**: User types "TSMC fab shutdown" → sees: Apple (72% impact), NVIDIA (68%), AMD (55%), Qualcomm (48%), with narrative chains and a ranked impact table.
- **Technical complexity**: Medium — backend propagation + causal chain APIs already exist. Need UI for input, results rendering, and optional graph overlay.
- **Dependencies**: `/api/v1/propagate`, `/api/v1/graph/subgraph`

#### F2: Entity Explorer (Search + Detail Card)
- **Description**: Searchable entity directory with rich detail cards. Search by name (fuzzy), filter by type/tags. Each entity card shows: name, type, tags, confidence, source count, neighbor count, key relationships.
- **User value**: "Tell me about this company's graph position."
- **Technical complexity**: Low — CRUD APIs exist, need search UI + cards.
- **Dependencies**: `/api/v1/entities`, `/api/v1/graph/search`

#### F3: Neighborhood Graph View
- **Description**: When viewing an entity, show its immediate neighborhood (1-2 hops) as an interactive node-link diagram. Click nodes to recenter. Edges show relation type and weight.
- **User value**: "Show me who this company is connected to."
- **Technical complexity**: Medium — need graph rendering library, layout algorithm, interaction handlers.
- **Dependencies**: `/api/v1/graph/subgraph`, `/api/v1/graph/neighbors`

#### F4: Signal ↔ Graph Bridge
- **Description**: On the existing signal detail page (`/signal/[id]`), add an "MKG Context" section showing: supply chain risk score, affected companies, risk factors, and a link to explore the full graph for that symbol.
- **User value**: "Why did this signal fire? What supply chain context informed it?"
- **Technical complexity**: Low — enrichment data already flows into signals. Need a UI component.
- **Dependencies**: `/api/v1/signals/enrich`, existing signal detail page

#### F5: Impact Results Table
- **Description**: Tabular view of propagation results. Columns: Rank, Entity, Type, Impact %, Depth, Path. Sortable, filterable. Always available as an alternative to the graph view (accessibility).
- **User value**: Structured data for analysis, screen-reader compatible, exportable.
- **Technical complexity**: Low — ImpactTableBuilder API exists.
- **Dependencies**: `/api/v1/propagate`

#### F6: Graph Health Dashboard (Admin)
- **Description**: Shows: total entities, total edges, by-type breakdowns, pipeline health, DLQ depth, source credibility, recent mutations, storage growth.
- **User value**: "Is the knowledge graph working correctly?"
- **Technical complexity**: Low — health/metrics APIs exist.
- **Dependencies**: `/api/v1/graph/health`, `/api/v1/pipeline/health`, `/api/v1/articles/stats/summary`

### P1 — High Value

#### F7: Event Alert Feed with Graph Context
- **Description**: Real-time feed of propagation alerts (critical/high/medium/low severity). Each alert links to the affected subgraph and shows the causal narrative. Push notifications for critical alerts.
- **User value**: "Something just happened. How does it affect my world?"
- **Technical complexity**: Medium — AlertSystem exists, need WebSocket integration for real-time delivery + UI feed component.
- **Dependencies**: `/api/v1/alerts`, WebSocket endpoint

#### F8: Confidence & Provenance Overlay
- **Description**: Toggle overlay showing: edge confidence (line thickness/opacity), entity confidence, data source (AI-extracted, tribal knowledge, seed data), provenance trail (click to see source articles).
- **User value**: "How reliable is this data? Where did it come from?"
- **Technical complexity**: Medium — lineage/provenance APIs exist. Need visual encoding.
- **Dependencies**: `/api/v1/lineage/entity`, provenance tracker

#### F9: Watchlist Integration
- **Description**: User's existing SignalFlow watchlist is overlayed on the graph. Watchlisted entities are highlighted. Propagation can be filtered to "only show impact on my watchlist."
- **User value**: "Do I care about this event? Is my portfolio affected?"
- **Technical complexity**: Medium — need to cross-reference SignalFlow watchlist with MKG entities.
- **Dependencies**: SignalFlow watchlist API, entity matching

#### F10: Edge & Entity Filtering Panel
- **Description**: Side panel with filters: entity types (multi-select), relation types (multi-select), confidence range slider, tags (typeahead), temporal range (date picker for valid_from/until).
- **User value**: "Show me only SUPPLIES_TO relationships with >80% confidence."
- **Technical complexity**: Low-Medium — filters applied to subgraph queries.
- **Dependencies**: Existing find_entities/find_edges APIs

#### F11: Graph Diff ("What Changed?")
- **Description**: Daily/weekly diff view showing: new entities, new edges, updated weights, removed entities. Filterable by type and time range.
- **User value**: "What changed in the knowledge graph since my last visit?"
- **Technical complexity**: Medium — need a changelog/mutation log or timestamp-based diffing.
- **Dependencies**: Audit logger entries, entity/edge timestamps

#### F12: Tribal Knowledge Input UI
- **Description**: Forms for domain experts to: add entities, add edges, override confidence, annotate entities, correct relationships. Shows pending reviews and audit trail.
- **User value**: "I know something the AI doesn't. Let me contribute."
- **Technical complexity**: Low — tribal knowledge API already exists. Need forms + review queue.
- **Dependencies**: `/api/v1/tribal/*`

### P2 — Nice to Have

#### F13: Path Finder
- **Description**: Enter two entities → find all paths between them up to N hops. Highlight shortest path, show alternate routes, display cumulative weight for each path.
- **User value**: "How are Company A and Company B connected? Through which intermediaries?"
- **Technical complexity**: Medium — need a new backend endpoint for all-paths query (not just BFS from one source).
- **Dependencies**: New API endpoint

#### F14: Sector/Geography Cluster View
- **Description**: Aggregate nodes by sector or country into cluster bubbles. Bubble size = entity count. Edges between clusters show cross-sector/cross-geography dependencies.
- **User value**: "High-level view: where is risk concentrated by sector and geography?"
- **Technical complexity**: High — need server-side clustering + new layout algorithm.
- **Dependencies**: Entity tags/properties for sector/country

#### F15: Graph Export
- **Description**: Export current view as: PNG/SVG image, CSV (entity list + edge list), JSON (raw graph data). For research reports and offline analysis.
- **User value**: "I need this for my research report."
- **Technical complexity**: Low-Medium — SVG/Canvas export is library-dependent.
- **Dependencies**: Graph rendering library's export API

#### F16: Scenario Comparison
- **Description**: Run two different simulations side-by-side. Compare impact tables. "What if TSMC shuts down vs what if Samsung shuts down — which affects Apple more?"
- **User value**: "Compare alternative scenarios for risk planning."
- **Technical complexity**: Medium — two propagation runs + comparison UI.
- **Dependencies**: Impact Simulator (F1)

#### F17: Graph Statistics Panel
- **Description**: Network metrics: total nodes, total edges, average degree, max degree (supernodes), connected components, density, average path length.
- **User value**: "How healthy and complete is the knowledge graph?"
- **Technical complexity**: Low-Medium — some metrics computable from existing data, some need new queries.
- **Dependencies**: Graph health API

#### F18: Accuracy Calibration View
- **Description**: Show historical prediction accuracy: past propagation predictions vs actual market movements. Calibration curve and confusion matrix.
- **User value**: "How often has this system been right about supply chain impacts?"
- **Technical complexity**: Medium — accuracy tracker exists, need visualization.
- **Dependencies**: `/api/v1/accuracy`

### P3 — Future Vision

#### F19: Natural Language Graph Query
- **Description**: "Show me all semiconductor companies that supply to Apple and operate in Taiwan." Parsed by AI into structured graph query, executed, results visualized.
- **User value**: "Ask the graph questions in English."
- **Technical complexity**: High — NL-to-query translation via Claude.
- **Dependencies**: Claude API, graph query engine

#### F20: Real-Time Graph Mutation Stream
- **Description**: WebSocket-powered live view of graph changes as news articles are processed. Watch new entities and edges appear in real-time.
- **User value**: "See the knowledge graph evolving in real-time."
- **Technical complexity**: High — need event streaming from pipeline to frontend.
- **Dependencies**: EventFeed service, WebSocket

#### F21: Portfolio Risk Heatmap
- **Description**: Upload/link portfolio → overlay each holding on the graph → compute aggregate supply chain risk → visualize as a heatmap by sector, geography, and entity.
- **User value**: "What's my portfolio's total supply chain exposure?"
- **Technical complexity**: High — need portfolio-to-entity mapping + aggregate analysis.
- **Dependencies**: Portfolio API, entity matching

#### F22: Graph-Powered Signal Generation
- **Description**: When graph topology changes significantly (new critical path, broken dependency), automatically generate trading signals based on affected entities.
- **User value**: "Get signals directly from supply chain intelligence."
- **Technical complexity**: Very High — connects graph mutations to signal pipeline.
- **Dependencies**: Signal engine integration

---

## 4. Page / View Architecture

### 4.1 New Pages

```
/knowledge-graph               → Main entry: search + Impact Simulator
/knowledge-graph/entity/[id]   → Entity detail + neighborhood graph
/knowledge-graph/simulate      → Full Impact Simulator page
/knowledge-graph/alerts        → Event alert feed with graph context
/knowledge-graph/admin          → Graph health, pipeline stats, data quality (admin only)
/knowledge-graph/tribal         → Tribal knowledge input + review queue
```

### 4.2 Integration Points (Existing Pages)

| Existing Page | Integration |
|---|---|
| `/signal/[id]` (Signal Detail) | Add "Supply Chain Context" section with MKG enrichment data + link to entity graph |
| `/` (Dashboard) | Add "Supply Chain Alerts" widget showing recent critical/high alerts |
| `/watchlist` | Add "Supply Chain Risk" column showing aggregate risk score per symbol |
| `/news` | Link news articles to extracted entities; "View in Graph" button |

### 4.3 Navigation

Add to existing sidebar/nav:
```
📊 Dashboard
📈 Signals
🔔 Alerts
📰 News
🕸️ Knowledge Graph  ← NEW top-level nav item
   ├── Explorer       (F2 + F3: search + neighborhood view)
   ├── Impact Sim     (F1: "What If?" tool)
   ├── Alert Feed     (F7: real-time event alerts)
   └── Admin          (F6: health dashboard, gated to admin role)
```

### 4.4 Mobile Strategy

| View | Mobile Treatment |
|---|---|
| Impact Simulator | Full support — input field + impact table (no graph rendering) |
| Entity Explorer | Full support — search + entity cards (list view, no graph) |
| Entity Detail | Card layout with collapsible relationship lists |
| Neighborhood Graph | Desktop only. Mobile shows text-based neighbor list |
| Alert Feed | Full support — card-based alert feed |
| Admin | Desktop only |

---

## 5. Interaction Patterns

### 5.1 Graph Exploration Flow

```
Search for "TSMC"
    → Entity card with key stats
    → Click "View Graph"
    → Neighborhood graph (1 hop, ~15 nodes)
    → Click a neighbor (e.g., "Apple")
    → Graph recenters on Apple, expands to 1 hop from Apple
    → Previous context preserved (TSMC stays visible, dimmed)
    → Breadcrumb: TSMC → Apple
    → Click "Expand all" → 2-hop view
    → Right-click edge → see confidence, source, temporal validity
```

### 5.2 Impact Simulation Flow

```
Open Impact Simulator
    → Type: "Taiwan earthquake magnitude 7.0"
    → OR select trigger entity: "TSMC" + select event type: "Facility Shutdown"
    → Set parameters: max depth=4, min impact=5%
    → Click "Simulate"
    → Results appear as:
        1. Impact Table (ranked list with severity colors)
        2. Graph View (affected subgraph with impact-colored nodes)
        3. Causal Narratives (plain-English chain explanations)
    → Click any entity in the table → jumps to Entity Detail
    → Click "Filter to my watchlist" → table shows only portfolio-relevant impacts
    → Click "Share analysis" → generates shareable public URL
```

### 5.3 Alert-Driven Flow

```
Critical alert fires: "Samsung fab fire — 4 entities critically affected"
    → Notification badge on "Knowledge Graph" nav item
    → Alert feed shows full narrative
    → Click alert → opens affected subgraph with impact overlay
    → Affected entities colored by severity (red=critical, orange=high, yellow=medium)
    → Click affected entity → see its SignalFlow signals + price movement
    → "Create signal from this event" → bridges to signal generation
```

### 5.4 Filtering Interaction

```
Filter panel (collapsible sidebar):
    Entity Types: [✓ Company] [✓ Facility] [ ] Person] [✓ Country]
    Relation Types: [✓ SUPPLIES_TO] [✓ DEPENDS_ON] [ ] COMPETES_WITH]
    Confidence: [====|======] 0.6 — 1.0
    Tags: [semiconductor] [x] [critical] [x]  [+ add]
    Temporal: [2024-01-01] to [2026-04-07]
    → Apply → graph updates to show only matching nodes/edges
    → "Reset" clears all filters
```

---

## 6. Visual Design Direction

### 6.1 Graph Layout Algorithms

| Layout | When to Use | Pros | Cons |
|---|---|---|---|
| **Force-directed (d3-force)** | Default neighborhood view (< 100 nodes) | Organic, shows clustering naturally | Unstable with many nodes, no hierarchy |
| **Hierarchical (dagre)** | Supply chain depth view (source → consumer) | Shows upstream/downstream flow clearly | Assumes direction; messy with bidi edges |
| **Radial/Concentric** | Entity-centered exploration | Clear center entity, rings = hop distance | Wastes space, hard with many 1-hop neighbors |
| **Cluster/Group** | Sector or geography grouping | Reduces cognitive load at scale | Requires meaningful categories |

**Recommendation**: Default to **force-directed** for ≤ 50 nodes. Switch to **hierarchical** for supply chain flows. Offer layout toggle.

### 6.2 Color Coding

| Element | Color Strategy |
|---|---|
| Entity types | Distinct hue per type: Company=#6366F1 (purple), Facility=#06B6D4 (cyan), Country=#F59E0B (amber), Person=#EC4899 (pink), Sector=#10B981 (green), Product=#8B5CF6 (violet), Regulation=#F97316 (orange), Event=#EF4444 (red) |
| Edge weight | Opacity: 0.2 (low weight) → 1.0 (high weight) |
| Edge confidence | Stroke style: dashed (< 0.5), dotted-dash (0.5-0.8), solid (> 0.8) |
| Impact severity | #EF4444 critical, #F97316 high, #EAB308 medium, #6B7280 low |
| Watchlisted entities | Gold ring/halo around node |
| Selected entity | Bright white border + scale up 1.2x |
| AI-extracted vs Expert-added | Subtle icon badge: 🤖 vs 👤 |

### 6.3 Information Density by Zoom Level

| Zoom Level | Shown | Hidden |
|---|---|---|
| **Far (overview)** | Colored circles only, cluster labels | Names, edge labels, metrics |
| **Medium** | Entity names, edge lines, type icons | Edge labels, confidence, tags |
| **Close (detail)** | Everything: names, edge labels, weight, confidence, tags, source badge | — |

### 6.4 Edge Rendering for Dense Graphs

- **Bundling**: When multiple edges connect the same clusters, bundle them into a single thick edge with a count badge.
- **Edge hiding**: Below a confidence threshold (user-configurable, default 0.3), hide edges entirely.
- **Curved edges**: Use quadratic Bézier curves for parallel edges (same source/target, different relation types).
- **Arrowheads**: Small, subtle arrowheads for directed edges. Bidirectional edges get arrows on both ends.

### 6.5 Dark Theme Integration

Matches existing SignalFlow palette:

```css
/* Graph-specific tokens */
--graph-bg: #0A0B0F;                /* Same as dashboard */
--graph-node-bg: rgba(255,255,255, 0.06);
--graph-node-border: rgba(255,255,255, 0.12);
--graph-edge-default: rgba(255,255,255, 0.15);
--graph-edge-active: rgba(99, 102, 241, 0.6);
--graph-label-primary: #F9FAFB;
--graph-label-secondary: #9CA3AF;
--graph-tooltip-bg: #1E1F2B;
```

---

## 7. Technical Recommendations

### 7.1 Graph Visualization Libraries

| Library | Stars | React Support | Pros | Cons | Recommendation |
|---|---|---|---|---|---|
| **React Flow** | 25K+ | Native React | Excellent DX, built-in controls, customizable nodes, great docs | Designed for flowcharts more than knowledge graphs | **Best for MVP** — fastest to build, most React-native |
| **Cytoscape.js** | 10K+ | Via wrapper | Mature graph library, good algorithms, handles large graphs | Steeper learning curve, React integration is a wrapper | **Best for advanced features** — consider for P1/P2 |
| **Sigma.js** | 11K+ | react-sigma | WebGL rendering, handles 100K+ nodes | Less interactive customization, canvas/WebGL limits tooltips | **Best for scale** — if 10K+ nodes needed in view |
| **D3.js (d3-force)** | 110K+ | Manual integration | Maximum control, force simulation | Boilerplate-heavy, no React integration out of box | Too low-level for this project |
| **vis-network** | 3K+ | Via wrapper | Easy setup, decent defaults | Fewer features, smaller community | Not recommended |

**Recommendation**: Start with **React Flow** for MVP (F1-F6). It handles the neighborhood graph views easily with custom nodes/edges. If performance demands increase (> 500 nodes in view), evaluate migrating to **Cytoscape.js** with a React wrapper.

### 7.2 Performance Strategy

1. **Server-side subgraph extraction**: Never send the full graph. API always returns bounded subgraphs (max 500 nodes).
2. **Lazy expansion**: Initially render 1-hop. Fetch next hop only on click.
3. **Web Worker layout**: Run force simulation in a Web Worker to avoid blocking the UI thread.
4. **Virtual rendering**: For tables (impact results), use virtualized lists (TanStack Virtual).
5. **Query debouncing**: Debounce search queries (300ms) and filter changes (200ms).
6. **React.memo**: Memoize node and edge components to prevent unnecessary re-renders during layout animation.
7. **Subgraph caching**: Cache fetched subgraphs in Zustand store with 5-minute TTL.

### 7.3 New API Endpoints Needed

| Endpoint | Method | Purpose | Priority |
|---|---|---|---|
| `GET /api/v1/graph/subgraph/{id}` | GET | Already exists | P0 |
| `POST /api/v1/propagate` | POST | Already exists | P0 |
| `GET /api/v1/graph/search` | GET | Already exists | P0 |
| `GET /api/v1/graph/stats` | GET | **NEW** — node/edge counts by type, avg degree, max degree | P1 |
| `GET /api/v1/graph/paths/{source}/{target}` | GET | **NEW** — all paths between two entities | P2 |
| `GET /api/v1/graph/diff?since=ISO` | GET | **NEW** — entities/edges changed since timestamp | P1 |
| `GET /api/v1/graph/clusters?group_by=sector` | GET | **NEW** — clustered/aggregated view | P2 |
| `WS /ws/graph` | WS | **NEW** — real-time graph mutation events | P3 |

### 7.4 Frontend Architecture

```
frontend/src/
├── app/
│   └── knowledge-graph/
│       ├── page.tsx              # Main entry: search + quick actions
│       ├── entity/[id]/page.tsx  # Entity detail + neighborhood graph
│       ├── simulate/page.tsx     # Impact Simulator
│       ├── alerts/page.tsx       # Alert feed
│       └── admin/page.tsx        # Health dashboard
├── components/
│   └── graph/
│       ├── GraphCanvas.tsx         # React Flow wrapper + layout engine
│       ├── EntityNode.tsx          # Custom node: icon, name, type badge
│       ├── RelationEdge.tsx        # Custom edge: label, weight, confidence
│       ├── ImpactSimulator.tsx     # Event input + propagation trigger
│       ├── ImpactTable.tsx         # Ranked results table
│       ├── CausalNarratives.tsx    # Plain-English chain display
│       ├── EntityCard.tsx          # Rich entity detail card
│       ├── EntitySearch.tsx        # Fuzzy search with autocomplete
│       ├── FilterPanel.tsx         # Type, relation, confidence, tags, temporal
│       ├── GraphControls.tsx       # Zoom, layout toggle, export
│       ├── GraphMinimap.tsx        # Overview minimap for large graphs
│       ├── ProvenanceBadge.tsx     # AI/Expert source indicator
│       └── GraphHealthPanel.tsx    # Admin health metrics
├── hooks/
│   └── useGraphData.ts            # React Query hooks for graph APIs
├── store/
│   └── graphStore.ts              # Zustand: selected entity, filter state, cache
└── lib/
    └── graph-api.ts               # REST client for MKG API (port 8001)
```

### 7.5 State Management

New Zustand store:

```typescript
interface GraphStore {
  // Selected entity
  selectedEntityId: string | null;
  selectedEntity: Entity | null;

  // Graph data
  subgraph: { nodes: Entity[]; edges: Edge[] } | null;
  
  // Filters
  filters: {
    entityTypes: string[];
    relationTypes: string[];
    confidenceRange: [number, number];
    tags: string[];
    temporalRange: [Date | null, Date | null];
  };
  
  // Impact simulation
  simulationResult: PropagationResult | null;
  isSimulating: boolean;
  
  // Alert feed
  alerts: Alert[];
  unseenAlertCount: number;
  
  // Actions
  selectEntity: (id: string) => void;
  loadSubgraph: (id: string, depth: number) => Promise<void>;
  runSimulation: (params: SimulationParams) => Promise<void>;
  setFilter: (key: string, value: any) => void;
  clearFilters: () => void;
}
```

---

## 8. Anti-Patterns to Avoid

### 8.1 The Hairball

**What**: Showing 1000+ nodes in a force-directed layout where everything overlaps. Looks like a tangled ball of yarn.
**Why it happens**: Developers load the full graph to demonstrate capability.
**Prevention**: Hard cap at 200 nodes per view. Beyond that, force clustering or paginated exploration.

### 8.2 The Graph-for-Graph's-Sake

**What**: Building a generic graph explorer because "it's cool" without answering specific user questions.
**Why it happens**: Engineers love graph visualization. Users need answers.
**Prevention**: Every view must answer a specific question. If it doesn't, it's not worth building.

### 8.3 The Information Overload

**What**: Showing entity type + name + confidence + tags + source + temporal range + 5 properties on every node simultaneously.
**Why it happens**: Treating nodes as data dumps.
**Prevention**: Progressive disclosure. Default: name + type icon. Hover: key metrics. Click: full detail panel.

### 8.4 The Desktop-Only Trap

**What**: Building an amazing interactive graph that's completely useless on mobile.
**Why it happens**: Graphs are inherently spatial/interactive.
**Prevention**: Design mobile-first text/card views that convey the same information. Graph canvas is desktop-only bonus.

### 8.5 The Stale Data Trap

**What**: Rendering a beautiful graph from data extracted 6 months ago, presented as current truth.
**Why it happens**: No freshness indicators on edges/entities.
**Prevention**: Every edge/entity must show a freshness indicator. Gray out or dash edges older than a configurable threshold.

### 8.6 The False Precision Trap

**What**: Displaying "Impact: 72.3456%" as if the model is that precise.
**Why it happens**: Raw float output from propagation engine.
**Prevention**: Round to meaningful precision (whole % for impact). Use qualitative labels alongside numbers: "High Impact (72%)".

### 8.7 The "Build Everything First" Trap

**What**: Spending 3 months building F1-F22 before shipping anything.
**Why it happens**: Planning too much, building too little.
**Prevention**: Ship F1 (Impact Simulator) + F2 (Entity Explorer) + F5 (Impact Table) in Sprint 1. Everything else is iteration.

---

## 9. Implementation Roadmap

### Sprint 1 — Foundations (MVP)
- **F2**: Entity Explorer (search + cards)
- **F5**: Impact Table (tabular propagation results)
- **F1**: Impact Simulator (event input → propagation → table + narratives)
- **F4**: Signal ↔ Graph bridge component
- GraphCanvas component with React Flow (neighborhood graph, ≤ 50 nodes)
- Zustand graph store + API client for MKG

### Sprint 2 — Depth
- **F3**: Full neighborhood graph view with expand/recenter
- **F10**: Filter panel (types, relations, confidence, tags)
- **F6**: Admin health dashboard
- **F8**: Confidence/provenance overlay

### Sprint 3 — Real-Time + Polish
- **F7**: Alert feed with graph context
- **F9**: Watchlist integration
- **F11**: Graph diff view
- **F12**: Tribal knowledge input UI
- Mobile text-based views

### Sprint 4+ — Power Features
- F13-F18 (path finder, cluster view, export, scenario comparison, stats, accuracy calibration)

---

## 10. Success Metrics

| Metric | Target | How to Measure |
|---|---|---|
| Impact Simulator usage | ≥ 3 simulations/user/week | API call count |
| Time to first graph interaction | < 10 seconds from page load | Performance monitoring |
| Graph-to-signal click-through | ≥ 20% of signal views include graph context | Click tracking |
| Tribal knowledge contributions | ≥ 5 corrections/additions per week | Audit log count |
| Graph subgraph load time | < 1 second for 100-node subgraph | API latency metrics |
| Mobile engagement | ≥ 40% of impact table views from mobile | Device tracking |
| Alert-driven graph views | ≥ 50% of critical alerts lead to graph exploration | Click tracking |

---

## Appendix A: Glossary for Users

The UI should use these user-friendly terms, not technical graph terminology:

| Technical Term | User-Facing Label |
|---|---|
| Knowledge Graph | Supply Chain Map |
| Entity/Node | Company / Organization / Entity |
| Edge/Relationship | Connection / Link |
| Subgraph | Neighborhood / Network |
| Traversal | Trace / Follow |
| Propagation | Impact Ripple / Cascade |
| BFS | Trace connections |
| Confidence | Reliability Score |
| Weight | Connection Strength |
| Hop / Depth | Steps Away |
| Supernode | Key Hub |

## Appendix B: Compliance Disclaimers (Required on Every Graph Page)

1. **Header disclaimer**: "Supply chain data is AI-extracted and may contain inaccuracies. Verify independently before making investment decisions."
2. **Impact simulator disclaimer**: "Impact simulations are estimates based on known supply chain relationships. Actual market impact may differ significantly."
3. **Footer**: "Not investment advice. See full disclaimer."
4. **Data source badge**: Each entity/edge shows its source (AI-extracted, expert-verified, seed data) with confidence score.
