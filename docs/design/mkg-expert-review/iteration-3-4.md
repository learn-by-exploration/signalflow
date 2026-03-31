# MKG Expert Panel Review — Iterations 3 & 4

> **Review Date:** 31 March 2026  
> **Document Under Review:** `core/MKG_REQUIREMENTS.md`  
> **Review Scope:** Full requirements document (Sections 1–15)  
> **Review Type:** Expert Panel — Iterations 3 & 4 of 10  
> **Previous Iterations:** [Iteration 1-2](iteration-1-2.md) — Hedge Fund PM + Supply Chain VP

---

## Panel Members — This Iteration

| # | Expert | Role | Perspective |
|---|--------|------|-------------|
| 3 | **Dr. Kai Müller** | Graph Database Architect, ex-Neo4j Solutions Architect, LinkedIn graph infra | Neo4j architecture, scalability, temporal modeling |
| 4 | **Dr. Aisha Ibrahim** | NLP/NER Research Scientist, ex-Thomson Reuters/Refinitiv, Two Sigma NER pipelines | Financial NER/RE, multilingual NLP, pipeline reliability |

---
---

# EXPERT 3: Dr. Kai Müller — Graph Database Architect

*Background: 8 years at Neo4j (Solutions Architect → Principal Architect), then 4 years at LinkedIn scaling the Economic Graph (1B+ nodes, 10B+ edges). Deep expertise in graph data modeling, Cypher optimization, temporal graphs, vector search, and Neo4j operational characteristics. Has deployed Neo4j at scale in financial services for 6 clients including two top-10 banks.*

---

## A. Concept-Requirement Alignment — Score: 5/10

**What aligns well:**
- Using Neo4j as the graph substrate for a financial knowledge graph is a reasonable choice given the stated scale (5K–50K nodes, 50K–500K edges). This is well within Neo4j's operational sweet spot. Neo4j handles relationship-heavy traversals far better than relational databases or document stores.
- The 6 node types / 7 edge types ontology is clean and well-designed. The MERGE-on-insert pattern from MiroFish is exactly right for entity deduplication.
- Hybrid search (vector + BM25) on Neo4j 5.18+ is supported. The MiroFish pattern of 0.7 vector + 0.3 BM25 is a sensible starting point.
- The dual-database architecture (Neo4j for graph + PostgreSQL for relational) is the correct pattern. Storing audit logs, user data, and time-series in PostgreSQL while keeping the knowledge graph in Neo4j avoids fighting Neo4j's weaknesses.

**Where the architecture diverges from reality:**

1. **Neo4j Community Edition has critical limitations the spec ignores.** CE lacks role-based access control, online backups, clustering (no read replicas), and — most critically — has no built-in support for multi-database (available only in Enterprise). If MiroFish simulation runs in the same Neo4j instance with "isolated graph_ids" (R-MF2), that's a *logical* isolation only, not a database-level isolation. CE gives you one database. Everything is in that one database.

2. **Temporal versioning is not a Neo4j feature — it's a custom implementation.** The spec says "temporal versioning" and "daily graph snapshots" (R-KG5, R-KG6) as if these are configuration options. They are not. In Neo4j, temporal versioning requires one of: (a) a bitemporal property model where every node/edge stores valid_from/valid_until and every query includes a time filter, (b) full graph copies (one database per snapshot — Enterprise only), or (c) an event-sourcing log in PostgreSQL with graph reconstruction. Each approach has severe trade-offs the spec doesn't acknowledge.

3. **The spec conflates "edge weight" with "edge properties" and doesn't model the weight-update lifecycle.** R-KG4 says every edge must have weight, confidence, source, last_updated, valid_from, valid_until. R-KG9 says every weight change must record old_weight and new_weight. But in Neo4j, updating a relationship property is a destructive overwrite — there's no built-in property history. The audit trail must be implemented externally (e.g., a `WEIGHT_CHANGE` node chain, or PostgreSQL logging). The spec treats this as a given.

4. **Embedding vectors on nodes AND edges (R-KG14) is a significant architectural decision that is underspecified.** Neo4j 5.18 supports vector indexes on nodes. Vector indexes on *relationships* are NOT natively supported as of Neo4j 5.x. Edge embeddings would require a workaround — either reifying edges as intermediate nodes or storing edge embeddings in PostgreSQL with a cross-reference.

5. **The "4-hop traversal in <60 seconds" claim (R-PE6) is trivially easy at stated scale — but misleading.** 50K nodes with 500K edges is a small graph. A 4-hop BFS from a single source will visit at most a few thousand nodes. The real question is: what is the *computational cost per hop* when each hop involves weight multiplication, attenuation calculation, impact score aggregation, cycle detection, and causal chain construction? The traversal isn't the bottleneck — the business logic at each node is.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Neo4j Edition Selection — ARCHITECTURAL RISK

The spec says "Neo4j CE 5.18+" (Section 12.1). Community Edition is free but has these missing capabilities that directly conflict with stated requirements:

| Capability | Required By | CE Support | Enterprise Support |
|------------|------------|------------|-------------------|
| Role-based access control | R-SEC2 | ❌ No | ✅ Yes |
| Online backup (hot) | R-KG13 | ❌ No (offline only) | ✅ Yes |
| Multi-database | R-MF2 (graph isolation) | ❌ No (single DB) | ✅ Yes |
| Causal clustering (HA) | R-NF7 (99.5% uptime) | ❌ No | ✅ Yes |
| Read replicas | R-NF8 (100+ concurrent) | ❌ No | ✅ Yes |
| Property-level security | R-SC4 (multi-tenant) | ❌ No | ✅ Yes |
| Composite databases (federated) | Cross-graph entity resolution | ❌ No | ✅ Yes |

**The gap:** At least 5 stated requirements (R-SEC2, R-KG13, R-MF2, R-NF7, R-SC4) cannot be implemented on CE as specified. The document needs to either:
- Budget for Neo4j Enterprise (starts at ~$36K/year for a small deployment, $100K+ for production)
- Redesign requirements to work within CE limitations (remove multi-tenant, accept offline backups, implement app-level access control)
- Consider Neo4j Aura (managed cloud) or an alternative like Amazon Neptune / TigerGraph

Missing requirement:
> **R-GRAPH-1**: System must document Neo4j edition decision (CE vs Enterprise vs Aura) with explicit mapping of which requirements are achievable under the chosen edition. If CE is selected, app-level workarounds must be specified for: RBAC, online backup, graph isolation, and high availability.

### B2. Temporal Versioning Implementation — UNDERSPECIFIED

R-KG5 ("query state of graph at time T") and R-KG6 ("daily snapshots") are stated as requirements but have no implementation specification. This is one of the hardest problems in graph databases.

**Three viable approaches, each with trade-offs:**

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **A. Bitemporal properties** | Every node/edge gets `valid_from`, `valid_until`. Queries add `WHERE n.valid_from <= $T AND (n.valid_until IS NULL OR n.valid_until > $T)` | No data duplication, works on CE | Every query becomes 2-3x more complex, indexes must include temporal fields, current-state queries pay the tax even when you don't need history, deletes become soft-deletes, Cypher becomes very verbose |
| **B. Snapshot copy** | Full graph copy per snapshot. Query the snapshot database for historical state. | Clean separation, simple queries | Enterprise only (multi-database), storage grows linearly (50K nodes × 365 days = 18M node-copies/year), APOC export/import is slow for daily snapshots |
| **C. Event sourcing** | Store an append-only changelog in PostgreSQL. Current graph is the "materialized view." Reconstruct any historical state by replaying events up to time T. | Storage-efficient, flexible, works on CE | Reconstruction is slow for distant past (O(n) events), complex to implement, query latency for historical state is high |

**Recommendation:** Approach A (bitemporal) for edges (which change frequently) combined with Approach C (event sourcing in PostgreSQL) for full-graph reconstruction. But this is an architectural decision, not a trivial implementation detail.

Missing requirements:
> **R-GRAPH-2**: System must specify temporal versioning implementation approach (bitemporal properties vs snapshot vs event sourcing) and document trade-offs for: query complexity, storage growth, historical query latency, and CE compatibility.
> 
> **R-GRAPH-3**: System must specify retention policy for temporal data (how far back can you query? forever? 1 year? configurable?) and the storage cost model over time.

### B3. Edge Weight Audit Trail — ARCHITECTURE GAP

R-KG9 requires that every weight change records source signal, timestamp, old_weight, and new_weight. But Neo4j has no native property versioning.

**The options:**

1. **Weight change node chain**: For each edge weight update, create a `(:WeightChange {old_weight, new_weight, timestamp, signal_id})` node linked to the relationship. Problem: you can't attach a relationship to a relationship in Neo4j. You'd need to link the WeightChange to both endpoints of the edge + the edge type. This is messy and explodes node count (500K edges × avg 10 updates = 5M WeightChange nodes).

2. **PostgreSQL audit table**: Log all weight changes in a PostgreSQL table `(edge_source, edge_target, edge_type, old_weight, new_weight, signal_id, timestamp)`. Cross-reference by edge identity. Problem: cross-database joins for audit queries.

3. **JSON array property**: Store weight history as a JSON list on the edge property itself: `change_history: [{old: 0.3, new: 0.7, signal: "...", ts: "..."}]`. Problem: property size grows unbounded, no indexing on array contents, slow to append in Neo4j.

**Recommendation:** PostgreSQL audit table (Option 2). Neo4j should store only current weight, confidence, and last_updated on the edge. All historical weight data lives in PostgreSQL with proper indexing and retention policies. This keeps the graph fast and the audit trail queryable.

Missing requirement:
> **R-GRAPH-4**: Edge weight audit trail must be stored in PostgreSQL, not Neo4j, with a cross-reference key (source_entity_id, target_entity_id, edge_type). Neo4j edge properties must contain only current-state values.

### B4. Financial Decimal Precision — FUNDAMENTAL TYPE MISMATCH

R-KG11 states: "All financial values as Decimal, never float." But **Neo4j stores all floating-point numbers as IEEE 754 doubles internally.** There is no `DECIMAL` type in Neo4j's type system.

This means:
- A value like `$1,234,567.89` stored as a Neo4j `Double` could represent as `1234567.8900000001` due to floating-point representation
- Weight values (0.0–1.0) are fine as doubles — precision loss is negligible
- Revenue, market_cap, and price values are NOT fine as doubles if used in financial calculations
- Comparing two price values for equality (`n.price = 1234.56`) is unreliable with doubles

**Impact:**
- Node attributes like `market_cap`, `revenue`, `capacity_allocation_pct` are financial values that lose precision
- If these values are used downstream in PnL calculations (R-PORT2 from iteration 1-2), errors compound

**Workarounds:**
1. Store financial values as **strings** in Neo4j (e.g., `"1234567.89"`) and parse to Decimal on the application layer. Ugly but precise.
2. Store financial values as **integers in minor units** (cents, basis points). `$1,234,567.89` → `123456789` (integer). Integer arithmetic is exact in Neo4j.
3. Store financial values in **PostgreSQL only** and reference by entity_id. Keep Neo4j for graph structure and relationships only.

Missing requirement:
> **R-GRAPH-5**: Financial values (revenue, market_cap, prices) must be stored as integers in minor units (cents/paise) in Neo4j, or stored exclusively in PostgreSQL with entity_id cross-reference. The chosen approach must be documented and consistently applied across all node types.

### B5. Vector Index Limitations on CE 5.18 — PARTIAL SUPPORT

Neo4j 5.18 CE supports vector indexes, but with constraints:

- ✅ Vector indexes on node properties — supported
- ❌ Vector indexes on relationship properties — **not supported** (R-KG14 says "embedding vectors on both nodes and edges")
- Vector similarity search is `HNSW` only (no IVF, no PQ compression)
- Maximum vector dimension: 4096 (sufficient for most embedding models)
- No built-in hybrid search — vector search and BM25 (full-text) are separate indexes. Hybrid search requires application-level merging of result sets (MiroFish pattern does this correctly)
- Vector index does not support filtering during search (post-filter only), which can be expensive for temporal queries ("find similar nodes that were valid at time T")

**Impact on R-KG14:** Edge embeddings require either:
1. Reifying edges as intermediate nodes (e.g., `(:Company)-[:HAS_RELATIONSHIP]->(:Relationship {type: "SUPPLIES_TO", embedding: [...]})-[:TO]->(:Company)`). This doubles the graph's node count and changes every traversal query.
2. Storing edge embeddings in PostgreSQL with a vector extension (pgvector) and doing cross-database similarity search. More practical but adds latency.

Missing requirement:
> **R-GRAPH-6**: Edge embedding storage strategy must be explicitly chosen: (a) reify edges as nodes with vector-indexed properties, or (b) store edge embeddings in PostgreSQL with pgvector, cross-referenced by edge identity. Approach must be benchmarked for impact on traversal query performance.

### B6. Concurrent Reads During Weight Updates — NO ISOLATION

R-WAN7 requires "30 seconds from signal to all affected edge weights updated." During those 30 seconds, the graph is in an inconsistent state — some edges have new weights, others still have old weights. A propagation query running concurrently could read a mix of old and new weights.

**Neo4j CE's isolation:**
- Single-instance, no read replicas
- Transactions provide per-transaction consistency, but a long-running weight update that touches 100 edges across many relationships is NOT atomic unless wrapped in a single transaction
- Large single transactions cause lock contention and can block reads
- Neo4j does not support snapshot isolation across multiple transactions

**Practical impact:**
- If a propagation query for "TSMC disruption" runs while TSMC-related edge weights are being updated, the query may see a partially-updated graph
- For a 4-hop traversal touching 200 edges, if 50 are updated and 150 aren't, the impact scores are meaningless

**Solutions:**
1. **Batch weight updates in a single transaction**: Possible for small batches (<1000 edges), but large batches cause lock contention
2. **Double-buffering**: Maintain `weight_current` and `weight_pending` properties. Update `weight_pending`, then swap atomically. Requires query awareness of which property to read.
3. **Version counter**: Global version counter. Each weight update increments the counter and tags the edge with the version. Propagation queries pin to a specific version.

Missing requirement:
> **R-GRAPH-7**: System must specify consistency model for concurrent reads during weight updates. Must guarantee that any single propagation query sees a consistent snapshot of edge weights — either all pre-update or all post-update, never a mix.

### B7. Memory Requirements — UNDERESTIMATED

Neo4j is a memory-hungry database. For 50K nodes with embeddings:

| Component | Calculation | Memory |
|-----------|-------------|--------|
| Node storage (50K nodes × ~500 bytes avg properties) | 50,000 × 500B | ~25 MB |
| Relationship storage (500K edges × ~200 bytes avg) | 500,000 × 200B | ~100 MB |
| Node embeddings (50K × 768 dims × 4 bytes float32) | 50,000 × 3,072B | ~150 MB |
| Edge embeddings (if reified: 500K × 768 × 4) | 500,000 × 3,072B | ~1.5 GB |
| Vector index (HNSW, ~4x embedding size) | ~4 × 150MB (nodes only) | ~600 MB |
| Page cache (recommended: 2x data size) | ~2 × 1.8GB | ~3.6 GB |
| JVM heap (Neo4j recommendation) | | 4–8 GB |
| Full-text indexes (BM25) | ~20% of text data | ~50 MB |
| **Total minimum** | | **~6–10 GB RAM** |

This is manageable on a single server. But if edge embeddings are stored in Neo4j (reified), it jumps by 1.5GB + 6GB HNSW index = ~8GB additional, pushing total to **14–18 GB**.

At the 50K→500K node scale target (R-SC1), memory requirements grow roughly linearly. 500K nodes would need ~60–100 GB RAM for Neo4j alone, which starts requiring dedicated hardware.

Missing requirement:
> **R-GRAPH-8**: System must document Neo4j memory allocation plan: JVM heap, page cache, and vector index memory budgets. Growth model must show memory requirements at 5K, 50K, and 500K node scales. Deployment must specify minimum server RAM at each scale tier.

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **R-KG14**: Embedding vectors on both nodes AND edges | Edge-level vector indexing is not supported in Neo4j 5.x. This is either a research project (reify edges as nodes, accept 2x node count and query complexity increase) or requires a separate vector store. Should be split: node embeddings P0, edge embeddings P2. |
| **R-KG5 + R-KG6**: Temporal versioning + daily snapshots | This is a multi-month engineering effort on top of Neo4j, not a configuration option. The requirements treat it as a checkbox item. A realistic timeline for production-grade temporal versioning: 8–12 weeks of dedicated engineering. |
| **R-MF2**: Shared Neo4j instance with isolated graph_ids | CE doesn't support multi-database. "Isolated graph_ids" means property-level isolation (every node has a `graph_id` property, every query filters by it). This works but is fragile — one missing `WHERE` clause leaks data across graphs. Enterprise multi-database or separate Neo4j instances are the safe options. |
| **R-NF7**: 99.5% uptime | On CE with a single instance, there's no failover. A JVM crash = downtime until restart. 99.5% = max 43.8 hours downtime/year. Achievable with monitoring + auto-restart for non-critical apps, but not for a financial intelligence system where a 4-hour outage during a market event means missed signals. Enterprise HA or Aura is needed. |
| **R-SC1**: 5K → 50K nodes without architecture change | The graph operations scale, but the temporal versioning, vector indexes, and audit trail do NOT scale linearly. A 10x node increase means 10x more daily snapshot data, 10x more weight change events, 10x more embedding storage. The "without architecture change" claim only holds for the core Neo4j graph, not the surrounding infrastructure. |

### C2. Underspecified

| Requirement | What's Missing |
|-------------|---------------|
| **R-KG7**: Entity dedup by canonical name (MERGE) | MERGE is a Cypher clause, not a strategy. What's the matching logic? Exact string match? Fuzzy match? Multiple identifiers (ticker + name + LEI)? Cross-language matching ("台灣積體電路" = "TSMC")? The dedup quality determines graph quality. |
| **R-KG8**: Hybrid search with configurable weights | Configurable by whom? Per query? Per user? Per entity type? Is the 0.7/0.3 ratio tuned empirically or a guess? No A/B testing requirement. No relevance evaluation metric (NDCG, MRR). |
| **R-KG12**: "Ontology stored per graph" | How is the ontology stored? As Neo4j constraint definitions? As a separate document? In PostgreSQL? Can it be hot-swapped? What happens to existing data when the ontology changes (schema migration)? |
| **R-KG3**: 500K+ edges | What's the edge type distribution? If 400K of 500K edges are SUPPLIES_TO, the graph has very different characteristics than if edges are evenly distributed. Distribution affects index design, traversal patterns, and query performance. |
| **R-WAN7**: 30-second weight update latency | 30 seconds for how many edges? If a single signal triggers 5 edge updates, 30s is generous. If a macro event triggers 5,000 edge updates, 30s is aggressive. No specification of expected update fan-out per signal type. |

### C3. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| R-KG6 (daily snapshots) | How long does the snapshot take? If it takes 2 hours, the database is impacted for 2 hours daily. What's the maximum acceptable snapshot duration? |
| R-PE6 (<60s propagation) | At what percentile? P50? P99? If P50 is 10s but P99 is 300s, the requirement is met 50% of the time but fails catastrophically for complex subgraphs. |
| R-KG8 (hybrid search <1s) | At what recall? If you get results in 200ms but miss 40% of relevant entities, the speed is useless. No precision/recall target for search. |
| R-NF4 (subgraph query <2s) | For what subgraph radius? A 1-hop subgraph of TSMC is ~50 nodes. A 3-hop subgraph is ~5,000 nodes. The query time depends entirely on the subgraph size, which isn't constrained. |

### C4. Missing Edge Cases

- **Schema evolution**: What happens when a new node type is added (e.g., "RawMaterial" as a 7th type)? How does this affect existing indexes, queries, and temporal snapshots? No schema migration strategy.
- **Orphaned nodes**: When a company is acquired or delisted, what happens to its node? Soft delete? Archive? The temporal model needs to handle entity lifecycle events.
- **Edge type reclassification**: A PARTNERS_WITH relationship becomes SUPPLIES_TO. Is this a weight change on the existing edge or deletion + creation? The audit trail must handle type changes.
- **Bulk load**: The seed phase loads 500 companies + 5,000 edges. What's the load strategy? `LOAD CSV`? Batch `CREATE`? The Neo4j import tool is orders of magnitude faster than Cypher for bulk loads but requires a stopped database (CE) or APOC.
- **Character encoding**: Entity names in CJK characters, Cyrillic, Arabic. Neo4j supports UTF-8, but full-text indexes may not tokenize non-Latin scripts correctly for BM25. The MiroFish pattern may not handle this.

---

## D. New Requirements to Add

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| **R-GRAPH-1** | Document Neo4j edition decision (CE vs Enterprise vs Aura) with explicit mapping of achievable requirements per edition. If CE, specify app-level workarounds for RBAC, online backup, graph isolation, HA. | P0 | 5+ requirements are impossible on CE as currently specified |
| **R-GRAPH-2** | Specify temporal versioning approach (bitemporal properties vs snapshot copy vs event sourcing) with documented trade-offs for query complexity, storage growth, and CE compatibility. | P0 | Temporal versioning is the hardest architectural decision and has zero specification |
| **R-GRAPH-3** | Define temporal data retention policy (duration, storage cost model, purge strategy). | P1 | Storage grows linearly; without retention policy, it grows unbounded |
| **R-GRAPH-4** | Edge weight audit trail must be stored in PostgreSQL with cross-reference key, not in Neo4j. Neo4j edges store current-state only. | P0 | Neo4j has no property versioning; audit trail in Neo4j degrades performance |
| **R-GRAPH-5** | Financial values stored as integers in minor units (cents/basis points) in Neo4j, or exclusively in PostgreSQL. Document and enforce consistently. | P0 | Neo4j stores doubles, violating R-KG11 (Decimal precision) |
| **R-GRAPH-6** | Specify edge embedding storage strategy: reify edges as nodes (with performance benchmark) or use PostgreSQL+pgvector. Node embeddings P0; edge embeddings P2. | P0 | Neo4j 5.x doesn't support vector indexes on relationships |
| **R-GRAPH-7** | Define consistency model for concurrent read/write: version counters, double-buffering, or single-transaction batching. Propagation queries must see consistent weight snapshots. | P0 | Partial weight updates produce garbage propagation results |
| **R-GRAPH-8** | Document Neo4j memory allocation plan at 5K, 50K, and 500K node scales (JVM heap, page cache, vector index memory). Specify minimum server RAM per tier. | P1 | Memory planning prevents production OOM failures |
| **R-GRAPH-9** | Define entity matching strategy for MERGE: exact match fields, fuzzy matching threshold, cross-language canonical form, identifier priority (ticker > LEI > name). | P0 | MERGE without matching strategy causes duplicates or false merges |
| **R-GRAPH-10** | Specify Neo4j index design: which node labels get which index types (range, text, full-text, vector, point). Document expected index count and size. | P1 | Missing indexes make queries slow; too many indexes make writes slow |
| **R-GRAPH-11** | Define schema evolution strategy: how new node/edge types are added, how existing data is migrated, how temporal history handles schema changes. | P1 | Ontology changes (R-KG12) affect all downstream queries and snapshots |
| **R-GRAPH-12** | Specify bulk data loading strategy for seed phase (Neo4j Admin Import Tool vs Cypher LOAD CSV vs APOC batch import) with expected load times. | P1 | Wrong approach can make seeding take hours instead of minutes |

---

## E. Architecture Risks — What Breaks First

### Risk 1: Temporal Versioning Becomes the Entire Project (CRITICAL)

Temporal graph versioning on Neo4j CE is essentially building a custom temporal database on top of Neo4j. I've seen this attempted at 3 clients. Every one either: abandoned temporal versioning, switched to Enterprise edition with snapshot databases, or moved to a purpose-built temporal graph (TypeDB, Datomic). On CE, the bitemporal property approach works but makes *every single Cypher query* more complex and slower. The engineering effort for production-grade temporal versioning is 3–6 months, not a few weeks.

**Probability:** 80% chance temporal versioning significantly delays the project.  
**Impact:** High — R-KG5 and R-KG6 are P0 requirements. If they can't be met, the "backtestable graph" capability and historical analysis collapse.  
**Mitigation:** Start with Approach A (bitemporal properties on edges only — nodes rarely change). Skip daily full-graph snapshots; instead, implement edge-level temporal queries only. Full graph reconstruction from event log (Approach C) as a background batch process, not a real-time query.

### Risk 2: MiroFish Graph Isolation is Fiction on CE (HIGH)

R-MF2 says "shared Neo4j instance with isolated graph_ids." On CE, this is a `WHERE node.graph_id = $graphId` filter on every query. One missing filter in one query in one code path = data leak between MKG and MiroFish graphs. This is exactly the class of bug that persists through code review because it's a missing constraint, not a visible error.

**Probability:** 70% chance of at least one cross-graph data leak during development.  
**Impact:** Medium for internal use, HIGH if MKG serves external clients and MiroFish simulation data contaminates intelligence output.  
**Mitigation:** Run MKG and MiroFish in separate Neo4j instances. The memory/cost overhead of two CE instances is minimal compared to the data isolation risk. Or use Enterprise with multi-database.

### Risk 3: Propagation Performance Degrades Non-Linearly (MEDIUM)

The propagation engine (R-PE1–R-PE10) runs BFS/DFS with per-hop computation. At 500K edges, a 4-hop traversal from a high-degree node (TSMC has ~50 direct edges → ~250 2-hop → ~1,250 3-hop → ~6,250 4-hop) touches ~8,000 edges. If each hop involves:
- Reading edge weight
- Checking temporal validity
- Computing attenuation
- Building causal chain string
- Checking for cycles
- Aggregating impact scores

That's ~8,000 × 6 operations = ~48,000 individual computations. In Cypher, this is a single query with APOC path expanders. The Cypher query optimizer will not optimize the business logic — it'll be a procedural traversal.

At this scale, the <60s target is EASILY met. But at 500K nodes / 5M edges (the next scale boundary), the same traversal from a high-degree node touches ~500K edges and 60s may not be achievable with Cypher. The solution is to pre-compute propagation results for high-frequency trigger entities.

**Probability:** Low at current scale, high at 10x scale.  
**Impact:** Core feature degradation.  
**Mitigation:** Pre-compute and cache propagation results for the top 50 most-connected entities. Invalidate cache on weight change. Live traversal only for cache misses.

### Risk 4: Weight Update Storms (MEDIUM)

A macro event (e.g., "China invades Taiwan") could trigger weight updates on thousands of edges simultaneously. If the WAN receives 500 signals in 5 minutes, each triggering 10 edge updates, that's 5,000 concurrent writes to Neo4j. On a single CE instance, this causes:
- Write lock contention
- Transaction queue buildup
- Propagation queries blocked by write locks
- Possible OOM if too many transactions queue up

**Probability:** Medium — macro events happen 2–5 times per year.  
**Impact:** System becomes unresponsive exactly when it's needed most.  
**Mitigation:** Implement write batching (accumulate weight deltas in Redis for 5s, then apply as a single Neo4j transaction). Prioritize reads (propagation queries) over writes during storm events.

### Risk 5: Backup and Recovery is Painful (MEDIUM)

CE only supports offline backups (`neo4j-admin dump`). This requires stopping the database. For a "24/7 operation" system (R-NF7), stopping Neo4j for a daily backup means planned downtime. `neo4j-admin dump` for a 5GB database takes 2–5 minutes. At 50GB (500K nodes with embeddings), it takes 20–40 minutes.

**Probability:** 100% — this is a known limitation of CE.  
**Impact:** 20–40 minutes of daily downtime in a system claiming 99.5% uptime.  
**Mitigation:** Use filesystem-level snapshots (LVM/ZFS) instead of `neo4j-admin dump`. These are near-instantaneous and don't require stopping Neo4j. But they're infrastructure-level, not Neo4j-level, and require specific deployment setup.

---

## F. Critical Questions — Make or Break

1. **"Have you budgeted for Neo4j Enterprise?"** CE limitations conflict with at least 5 stated requirements (RBAC, online backup, HA, multi-database, multi-tenant). Enterprise starts at ~$36K/year. If not budgeted, which requirements are you dropping?

2. **"Who is building the temporal versioning layer?"** This is a 3–6 month project within the project. It requires deep Cypher expertise, careful index design, and extensive testing of bitemporal query correctness. Is there a graph database specialist on the team, or is this being delegated to generalist backend engineers?

3. **"How will you validate that temporal queries return correct historical state?"** If I ask "show me TSMC's supply chain as of January 15, 2026" and the answer is wrong because a bitemporal filter missed an edge, how would you even know it's wrong? What is the testing strategy for temporal correctness?

4. **"What is your Neo4j operational experience?"** Running Neo4j in production requires JVM tuning, GC monitoring, page cache sizing, transaction log management, and query profiling. I've seen teams without Neo4j ops experience spend 3–4 months just getting the database stable before writing any business logic. Who on the team has Neo4j production experience?

5. **"Have you considered alternatives to Neo4j for the temporal + vector requirements?"** TypeDB natively supports temporal reasoning. Amazon Neptune supports property graph + vector. Memgraph is compatible with Cypher but has different performance characteristics. NebulaGraph handles larger scales. The MiroFish legacy isn't worth inheriting if Neo4j CE is the wrong tool for the actual requirements.

---
---

# EXPERT 4: Dr. Aisha Ibrahim — NLP/NER Research Scientist

*Background: 6 years at Thomson Reuters/Refinitiv building financial NER pipelines for 50,000+ article/day ingestion. Then 3 years at Two Sigma building entity extraction for alternative data feeds. PhD in Computational Linguistics from Edinburgh. Published 12 papers on financial NER, multilingual entity resolution, and relation extraction. The Reuters pipeline she built processes 8 languages and achieves 94% F1 on English financial NER.*

---

## A. Concept-Requirement Alignment — Score: 4/10

**What aligns well:**
- The entity type selection (Company, Product, Facility, Person, Country, Regulation) is well-chosen for financial/supply chain intelligence. This is close to the Thomson Reuters TRIT-5 ontology, which has been validated in production for a decade.
- The relation types (SUPPLIES_TO, COMPETES_WITH, etc.) are the right abstraction level. Not too granular (which leads to sparse data), not too coarse (which loses information).
- Source credibility scoring (R-IA12) is often ignored in academic systems but is critical in production. A Reuters article and a random Substack post should not carry equal weight. Good that this is included.
- The MiroFish NER/RE pipeline reuse (Section 11.4) is pragmatic. Re-implementing NER from scratch is wasteful when a working pipeline exists.

**Where the NLP architecture is deeply problematic:**

1. **The requirements treat NER and RE as a single pipeline stage, but they are fundamentally different problems with vastly different accuracy profiles.** NER for well-known financial entities (Apple, TSMC, NVIDIA) achieves 92–96% F1 with modern LLMs. But the *system doesn't need NER for Apple — it needs NER for "Longsheng Chemical" mentioned in a Chinese-language article about a niche polymer supplier.* The accuracy for tail entities — the ones that actually provide Speed 3 alpha — will be dramatically lower (60–75% F1). The requirements don't distinguish head vs. tail entity accuracy.

2. **Relation extraction accuracy is wildly overambitious for an LLM-based pipeline.** State-of-the-art RE on financial text achieves ~70–80% F1 for binary relations (does a relation exist?) and ~55–65% F1 for typed relations (what *kind* of relation?). The requirements list 7 relation types and assume they can be extracted accurately. In practice, distinguishing SUPPLIES_TO from DEPENDS_ON from PARTNERS_WITH in a single news sentence is ambiguous even for human annotators. No accuracy targets are specified (a critical omission).

3. **Multilingual NER across 13 languages is a research program, not a feature.** The spec says "R-IA9: Multilingual NER/RE — at minimum: English, Chinese (Simplified + Traditional), Japanese, Korean, German, French" at P1. This is 6+ language families with completely different tokenization, entity boundary detection, and co-reference resolution challenges. Japanese NER for financial entities has ~85% F1 in research settings with dedicated models. Chinese financial NER has ~88% F1. Cross-lingual entity resolution ("台積電" = "TSMC" = "台湾セミコンダクター") is a PhD-thesis-level problem for each language pair. At Thomson Reuters, adding Japanese NER to our English pipeline took a team of 4 NLP engineers 14 months.

4. **10,000 articles/day with Claude API for NER/RE has severe cost and latency implications the spec doesn't acknowledge.** Claude Sonnet at ~$3/million input tokens + $15/million output tokens, with an average financial article at ~2,000 tokens input + ~500 tokens structured output per article:
   - Input cost: 10,000 × 2,000 tokens = 20M tokens/day × $3/M = **$60/day**
   - Output cost: 10,000 × 500 tokens = 5M tokens/day × $15/M = **$75/day**
   - **Total: ~$135/day = ~$4,050/month** just for NER/RE
   - Plus sentiment analysis, reasoning, edge weight signals = easily **$6,000–$8,000/month** total LLM costs
   - The spec doesn't have a cost budget for the NLP pipeline

5. **The 5-minute latency target (R-IA11) is unrealistic for LLM-based NER/RE at scale.** Claude API has a cold-start latency of 1–3 seconds per request. Processing a single article through NER + RE + sentiment + dedup takes 5–15 seconds. If 100 articles arrive in a 5-minute window (peak news hour), sequential processing takes ~500–1,500 seconds (8–25 minutes). Parallel API calls are limited by rate limits (Claude: ~60 requests/minute on standard tier). To hit 5-minute processing latency at peak load, you need either: batch processing (lower quality), parallel API calls with elevated rate limits (higher cost), or a local model (Ollama — lower accuracy).

---

## B. Gap Analysis — Critical Missing Requirements

### B1. NER Accuracy Differentiation — FUNDAMENTAL GAP

The requirements treat NER as a binary capability ("we have NER"). In reality, NER accuracy varies dramatically by:

| Entity Class | Head Entities (Top 500) | Tail Entities (Long tail) | Why It Matters |
|-------------|------------------------|--------------------------|----------------|
| Company | 94–97% F1 | 60–75% F1 | Speed 3 alpha comes from tail entities |
| Product | 70–85% F1 | 40–60% F1 | Product names are ambiguous ("M2"=chip or MacBook?) |
| Facility | 50–70% F1 | 30–50% F1 | Facility names are rarely standardized in news |
| Person | 85–92% F1 | 65–80% F1 | Common names cause false matches |
| Country/Region | 95%+ F1 | 90%+ F1 | Well-solved problem |
| Regulation | 60–80% F1 | 40–60% F1 | Regulation names are inconsistent across sources |

**The graph's quality is bounded by the worst NER accuracy in the pipeline.** If Facility NER runs at 50% F1, then half the MANUFACTURES_AT edges are wrong. Propagation through wrong edges produces wrong impact scores. The spec gives no accuracy targets, no evaluation framework, and no degradation strategy.

Missing requirements:
> **R-NLP-1**: System must define minimum F1 score targets for each entity type: Company ≥85%, Product ≥70%, Facility ≥65%, Person ≥80%, Country ≥90%, Regulation ≥65%. Accuracy must be evaluated on a held-out test set per entity type quarterly.
>
> **R-NLP-2**: System must maintain an entity-type-specific accuracy dashboard showing precision, recall, and F1 per entity type, per language, per source type, updated weekly.

### B2. Relation Extraction Quality — SHOW-STOPPER

RE is significantly harder than NER. The requirements list 7 relation types without any accuracy targets. Based on published benchmarks and my Thomson Reuters experience:

| Relation Type | Expected F1 (English, LLM-based) | Key Challenge |
|--------------|----------------------------------|---------------|
| SUPPLIES_TO | 70–80% | Distinguishing supply from distribution from licensing |
| COMPETES_WITH | 75–85% | Often implicit — "rival" vs "peer" vs "competitor" |
| MANUFACTURES_AT | 55–70% | Facility-level attribution is rarely explicit in news |
| REGULATES | 65–75% | Regulatory scope ambiguity (does the EU AI Act regulate a company or a product?) |
| INVESTS_IN | 80–90% | Well-structured in financial news — easiest relation |
| PARTNERS_WITH | 60–75% | "Partnership" is overloaded — JV, co-development, marketing deal, MOU |
| DEPENDS_ON | 45–60% | Almost never explicitly stated — inferred from context. Hardest relation. |

**Average across 7 types: ~65–75% F1.** This means 25–35% of extracted relations are wrong.

**Impact on propagation:** If 30% of edges are incorrect, a 4-hop propagation path has a ~(0.70)^4 = 24% probability of all edges being correct. The propagation engine is building castles on sand unless RE accuracy is far above the state-of-the-art, which is unlikely with an LLM-based approach.

Missing requirements:
> **R-NLP-3**: System must define minimum F1 score targets for each relation type. DEPENDS_ON (the hardest but most valuable) must achieve ≥60% F1 before being included in propagation. Relations below target must be flagged as "low confidence" and excluded from high-confidence propagation alerts.
>
> **R-NLP-4**: System must implement human-in-the-loop validation for extracted relations below a configurable confidence threshold (default: 0.7). Validated relations become training examples for pipeline improvement.

### B3. Entity Disambiguation at Scale — UNDERSPECIFIED

R-IA5 says "deduplication of entities across sources (canonical name resolution)." This is described as if it were a solved problem. It is not.

**Entity disambiguation challenges:**

1. **Acronyms and abbreviations**: "TSMC" = "Taiwan Semiconductor Manufacturing Company" = "台積電" = "TSM" (ticker). Need a comprehensive alias table.
2. **Name variations**: "Samsung Electronics" vs "Samsung" vs "Samsung SDI" vs "Samsung Electro-Mechanics" — these are DIFFERENT companies with the same parent name.
3. **Cross-lingual matching**: "台灣積體電路製造股份有限公司" (Traditional Chinese) = "台湾集成电路制造股份有限公司" (Simplified Chinese) = "TSMC" (English) = "台湾セミコンダクター・マニュファクチャリング" (Japanese).
4. **Temporal identity**: "Facebook" became "Meta" in 2021. Historical articles reference "Facebook" — should these map to the same entity?
5. **Subsidiary disambiguation**: "Apple" (the company) vs "Apple Music" (a product/subsidiary) — mentioned in different contexts.
6. **Homographs**: "Mercury" — a chemical element, a planet, a car brand, and multiple companies.

At Thomson Reuters, our entity disambiguation system used a combination of: ticker symbol lookup, LEI (Legal Entity Identifier) matching, Wikipedia entity linking, and a custom alias table with 200K+ entries. It took 3 years to reach 92% accuracy on English entities. Cross-lingual resolution added another 18 months per language.

Missing requirements:
> **R-NLP-5**: System must implement entity disambiguation using a priority hierarchy: (1) ticker/ISIN/LEI exact match, (2) canonical alias table lookup, (3) contextual embedding similarity with threshold ≥0.92, (4) fuzzy string matching with manual confirmation.
>
> **R-NLP-6**: System must maintain a canonical entity registry with all known aliases, tickers, identifiers, and cross-lingual name mappings. Registry must be manually curated for the initial 500 seed entities and semi-automatically expanded thereafter.
>
> **R-NLP-7**: System must track entity merge/split events (e.g., Facebook→Meta, HP→HP Inc + HP Enterprise) and maintain identity chains so historical references resolve correctly.

### B4. LLM-Based NER/RE Hallucination — CRITICAL RISK

Using Claude for NER/RE introduces a class of error that doesn't exist in traditional (spaCy, BERT-based) NER pipelines: **hallucination.** Claude may:

1. **Invent entities that don't exist in the article**: "Based on context, this likely involves Company X" — but Company X was never mentioned.
2. **Infer relations that aren't stated**: "Since Company A supplies Company B, and Company B supplies Company C, Company A likely supplies Company C" — transitive inference that may be wrong.
3. **Confuse entities across articles**: If processing a batch of articles, Claude may bleed entities from one article into another.
4. **Generate plausible but wrong entity attributes**: Claude generates a facility name that sounds correct but doesn't exist, or attributes a product to the wrong manufacturer.
5. **Confidently extract from ambiguous text**: "Apple is working with the chip company" → Claude extracts `PARTNERS_WITH(Apple, TSMC)` when the article meant Qualcomm.

**Impact:** A hallucinated entity or relation gets inserted into the knowledge graph. If nobody validates it, it persists. If a propagation query traverses a hallucinated edge, it produces a confident-looking but completely wrong result. The user trusts it because it has a "causal chain" and confidence score. This is worse than having no data.

At Two Sigma, we measured LLM hallucination rates for financial NER/RE:
- Entity hallucination: 2–5% of extracted entities don't appear in the source text
- Relation hallucination: 8–15% of extracted relations are inferred/hallucinated rather than stated
- These rates INCREASE with: longer articles, more entities in context, multilingual text, and ambiguous language

Missing requirements:
> **R-NLP-8**: Every LLM-extracted entity must be validated against the source text using span-level verification: the entity name must appear as a substring in the original article (exact or fuzzy match within edit distance 2). Entities failing verification are flagged as "inferred" and excluded from high-confidence propagation.
>
> **R-NLP-9**: Every LLM-extracted relation must include the source sentence(s) from the original article that support the extraction. Relations without supporting evidence text are classified as "inferred" (R-TK5 distinction) and decay 3x faster than "verified" relations.
>
> **R-NLP-10**: System must track and report hallucination rate per entity type, relation type, LLM model, and language, measured against a monthly human-annotated sample of 200 articles.

### B5. Cost Model for NLP Pipeline — MISSING

The spec mentions Claude API + Ollama fallback but provides no cost model for the NLP pipeline.

**Detailed cost estimate for 10,000 articles/day:**

| Operation | Per Article | Daily Total | Monthly Cost |
|-----------|-----------|------------|-------------|
| NER/RE extraction (Claude) | ~2,500 input + ~600 output tokens | 25M in + 6M out tokens | $75 input + $90 output = **$165/day** |
| Sentiment analysis (Claude) | ~1,500 input + ~200 output tokens | 15M in + 2M out tokens | $45 + $30 = **$75/day** |
| Entity disambiguation (Claude for edge cases) | ~500 tokens (20% of articles) | 1M tokens | **$5/day** |
| Signal/impact extraction (Claude) | ~1,000 input + ~300 output tokens | 10M in + 3M out tokens | $30 + $45 = **$75/day** |
| Re-processing failures (~5% retry) | | 5% overhead | **$16/day** |
| **Total Claude API** | | | **$336/day ≈ $10,080/month** |

Plus embedding generation:
- 50K nodes × 768 dims, re-embedded monthly: ~$50/month (OpenAI ada-002) or free (local Ollama)
- Article embeddings for dedup: ~$30/month

**Total NLP pipeline cost: ~$10,000–$10,500/month.** This is 10x higher than any budget mentioned in the requirements.

The Ollama fallback reduces cost but at significant accuracy loss. A Llama 3.1 70B model running locally achieves ~80–85% of Claude's NER accuracy on English financial text, and ~60–70% on non-English text. This is a quality-cost trade-off that needs explicit specification.

Missing requirements:
> **R-NLP-11**: System must define monthly NLP pipeline cost budget with breakdown by: NER/RE, sentiment, disambiguation, and signal extraction. Budget must include Claude API costs at projected article volume.
>
> **R-NLP-12**: System must define an LLM routing strategy: which articles go to Claude (high-value, English, ambiguous) vs Ollama (low-priority, clear-cut, non-critical). Routing criteria must include: language, source credibility, entity novelty, and expected extraction difficulty.

### B6. Multilingual Pipeline Architecture — FANTASY AT 13 LANGUAGES

R-IA1 and R-IA9 claim support for 13 languages at P1. The practical implications:

| Language | NER Challenge | Expected F1 Drop vs English | Engineering Effort |
|----------|-------------|---------------------------|-------------------|
| Chinese (Simplified) | No word boundaries, entity boundaries ambiguous | -8 to -12% F1 | 4–6 months with Chinese NLP specialist |
| Chinese (Traditional) | Same as Simplified + different character set | -8 to -12% F1 | 2–3 months if Simplified exists |
| Japanese | Three writing systems (kanji, hiragana, katakana), entity suffixes (株式会社, Co., Ltd.) | -10 to -15% F1 | 6–8 months with Japanese NLP specialist |
| Korean | Agglutinative morphology, entity names mixed with particles | -8 to -12% F1 | 4–5 months |
| German | Compound nouns ("Halbleiterindustrie"), case inflection | -5 to -8% F1 | 2–3 months |
| French | Similar to English but different entity conventions | -3 to -5% F1 | 1–2 months |
| Other 7 languages | Varying difficulty | -10 to -20% F1 | 2–4 months each |

**Realistic timeline for 6 core languages (EN, ZH-CN, ZH-TW, JA, KO, DE): 18–24 months** with a team of 3 NLP engineers and language-specific annotators.

**Cross-lingual entity resolution** (matching the same entity across languages) adds another 6–12 months. The entity "Samsung Electronics" must resolve consistently whether it appears as "삼성전자" (Korean), "サムスン電子" (Japanese), "三星电子" (Chinese), or "Samsung Electronics" (English/German/French).

**Claude's multilingual capability helps but doesn't solve the problem.** Claude handles multilingual NER reasonably well (~85% F1 on Chinese financial NER), but:
- Output quality is inconsistent across languages — Claude is better at Chinese than Japanese financial NER
- Prompt engineering must be language-specific (different entity conventions per language)
- Evaluation requires language-specific annotators (someone who reads Japanese financial news)

Missing requirements:
> **R-NLP-13**: Multilingual NER/RE must be phased: Phase 1 English only (P0), Phase 2 add Chinese Simplified + Japanese (P1), Phase 3 add Korean + German (P2), Phase 4 remaining languages (P3). Each phase requires language-specific evaluation datasets and accuracy acceptance criteria.
>
> **R-NLP-14**: Cross-lingual entity resolution must use a canonical entity registry (R-NLP-6) with language-specific alias tables maintained by language domain experts, not auto-generated.

### B7. Training Data — WHERE DOES IT COME FROM?

The spec assumes NER/RE accuracy but specifies no training or evaluation data.

For LLM-based NER/RE (few-shot or zero-shot with Claude), you technically don't need traditional training data. But you DO need:

1. **Evaluation test sets**: To measure accuracy (the F1 scores I've been quoting), you need human-annotated articles. Minimum viable evaluation set: 500 articles × 6 entity types × 7 relation types = a significant annotation effort (2–4 person-months for English alone).

2. **Few-shot examples for prompts**: Claude performs best with 3–5 high-quality examples per entity/relation type in the prompt. These examples drive extraction quality and must be authored by financial domain experts, not NLP engineers.

3. **Error correction data**: When the pipeline makes errors, corrected examples should feed back into prompt improvement. This requires a review interface where analysts flag wrong extractions.

4. **Benchmark datasets**: Financial NER has published benchmarks (FiNER, SEC-BERT NER, BBN-FinNER) that can be used for comparison but NOT for production evaluation (domain gap between benchmark data and MKG's actual source mix).

Missing requirements:
> **R-NLP-15**: System must establish a human-annotated evaluation dataset of ≥500 articles with gold-standard entity and relation annotations, reviewed by a financial domain expert. Evaluation must run quarterly against this test set.
>
> **R-NLP-16**: System must implement an analyst review interface where NER/RE extractions can be corrected. Corrections feed back into prompt few-shot examples (for Claude) or fine-tuning data (for local models).

### B8. Article Deduplication Quality — UNDERSPECIFIED

R-IA6 says "deduplication of news articles (same event, different sources)." This is much harder than it sounds:

- **Same event, different angles**: Reuters reports "TSMC capacity issues" focusing on financial impact; Nikkei reports the same event focusing on technology implications; a Chinese outlet reports the same event with government response context. Are these duplicates or distinct signals?
- **Evolving events**: At T+0, "fire at TSMC fab." At T+2h, "TSMC confirms fab fire, no injuries." At T+6h, "TSMC fab fire contained, production impact assessment underway." Are these updates to one event or separate events?
- **Near-duplicates**: Syndicated articles (AP wire → 50 outlets verbatim or lightly edited). These are trivial duplicates but a common source of noise.

**The dedup strategy determines signal quality.** Over-dedup loses important detail from multiple sources. Under-dedup creates noise that inflates confidence scores (same event counted as 5 corroborating signals).

Missing requirements:
> **R-NLP-17**: Article deduplication must distinguish between: (a) exact/syndication duplicates (merge, keep highest-credibility source), (b) same-event different-angle articles (link to same event, extract incremental entities from each), (c) event updates (link to same event thread with temporal ordering). Each category requires a different processing strategy.
>
> **R-NLP-18**: Event threading must group related articles into event chains with temporal progression tracking ("fire detected" → "fire confirmed" → "production impact assessed" → "production resumed"). Each update may produce new entity/relation extractions.

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **R-IA1**: 50+ sources, 13 languages, P0 | Building reliable ingestion adapters for 50+ diverse sources (API formats, scraping targets, authentication, rate limits, paywall handling) is a 6-month project alone. Many financial data sources require paid licenses ($5K–$500K/year each). At Thomson Reuters, our source adapter team was 4 engineers maintaining ~30 sources full-time. |
| **R-IA10**: 10,000 articles/day | Achievable technically, but the cost ($10K+/month in Claude API) and quality implications (at this volume, every day ~1,000–1,500 articles will have NER/RE errors) need explicit acknowledgment. Start with 1,000 articles/day from 5 high-quality English sources. Scale after accuracy is validated. |
| **R-IA11**: 5-minute article-to-graph latency | With Claude API (1–3s per request, rate-limited to ~60 RPM on standard tier), processing a burst of 50 articles takes ~50s sequentially. Including graph update, entity resolution, and weight adjustment → 5 minutes is tight but achievable for small bursts. During peak news (earnings season, macro events), 200+ articles in 30 minutes → queue depth causes some articles to exceed 5 minutes. Need to specify P50 vs P99 latency targets. |
| **R-IA9**: Multilingual NER/RE | As analyzed in B6 above: English P0, Chinese+Japanese P1, everything else P2+. The spec should explicitly state that non-English NER accuracy will be 10–15% lower than English and that this is acceptable. |
| **R-IA3 + R-IA4**: NER + RE as single-pass LLM extraction | Combining NER and RE in a single Claude prompt (the MiroFish approach) is efficient but produces lower accuracy than a two-pass approach (first extract entities, then extract relations between extracted entities). The single-pass approach misses ~10% of relations compared to two-pass. The spec should choose: faster (single-pass) or more accurate (two-pass). |

### C2. Underspecified

| Requirement | What's Missing |
|-------------|---------------|
| **R-IA7**: "Extract sentiment and impact magnitude from each signal" | Sentiment is well-defined (positive/negative/neutral + score). But "impact magnitude" is not defined. Magnitude of what? Revenue impact? Stock price impact? Disruption duration? The unit of magnitude determines the extraction prompt and the downstream scoring model. |
| **R-IA12**: "Source credibility scoring" | What's the scoring model? Static (Reuters=0.9, Blog=0.3) or dynamic (source's historical accuracy)? How does credibility flow into edge confidence? If a 0.3-credibility source is the *only* source for a Tier 3 supplier relationship, does that edge get created with low confidence, or not created at all? |
| **R-IA13**: "Prompt injection prevention on all LLM-processed inputs" | Good that it's included, but incomplete. News articles may contain adversarial text (planted to manipulate NER output — firms have been caught planting positive mentions in news). Need to specify: input sanitization strategy, LLM prompt isolation pattern, output validation against input, and defense against indirect injection via article content. |
| **R-IA14**: "RSS, API, and web scraping ingestion methods" | Web scraping is legally complex. Many news sites have Terms of Service prohibiting scraping. Some jurisdictions (EU) have database rights that restrict systematic collection. The spec needs legal compliance requirements per source type. |
| **R-IA8**: "Extract temporal information" | This is P1 but critically important for event threading and signal decay. "TSMC will expand capacity in 2027" vs "TSMC expanded capacity in 2024" produces very different signals. Future vs past temporal extraction accuracy is ~70–80% F1 even for English. No accuracy target specified. |

### C3. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| R-IA3 (NER) | No precision/recall/F1 targets per entity type. No evaluation frequency. No minimum evaluation set size. |
| R-IA4 (RE) | No accuracy targets per relation type. No definition of what constitutes "correct" for ambiguous relations (PARTNERS_WITH vs SUPPLIES_TO for contract manufacturing). |
| R-IA5 (Entity dedup) | No duplicate detection rate target. No false merge rate target (merging two different entities into one is worse than missing a duplicate). |
| R-IA6 (Article dedup) | No dedup precision/recall targets. No definition of "same event" vs "related event." |
| R-IA11 (5-min latency) | At what percentile? During what load conditions? If P50=2min and P99=15min during earnings season, is that acceptable? |
| R-IA7 (Sentiment) | No sentiment accuracy target. Financial sentiment is domain-specific — "Apple beat estimates" is positive, "Apple beat employees" is negative. Standard sentiment models fail on financial text. What accuracy is acceptable? |

### C4. Missing Edge Cases

- **Retracted articles**: A news source publishes, then retracts, an article. If MKG already extracted entities/relations from it, do those get removed? There's no "retraction processing" pipeline.
- **Satire/opinion**: Financial satire (The Onion-style), opinion columns, and analyst speculation should be handled differently from factual reporting. No content type classification.
- **Press releases vs news**: Company press releases are inherently biased (positive framing). News articles about the same event may contradict the press release. No requirement to distinguish source intent.
- **Earnings call transcripts**: These are 10,000+ words with extremely dense entity/relation information. A single Claude API call with the full transcript will cost $0.03–$0.05 per transcript and may exceed context limits. Need chunking strategy specific to long-form documents.
- **Image/chart data**: Financial articles often contain critical information in images (supply chain diagrams, org charts) that a text-only NER pipeline misses entirely. Not addressed.
- **Embargoed/delayed data**: Some financial data sources have delayed feeds (15-min delay for certain exchanges). The pipeline must track data freshness, not just ingestion time.

---

## D. New Requirements to Add

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| **R-NLP-1** | Define minimum F1 score targets per entity type: Company ≥85%, Product ≥70%, Facility ≥65%, Person ≥80%, Country ≥90%, Regulation ≥65%. Evaluate quarterly on held-out test set. | P0 | Without accuracy targets, there's no way to measure or improve pipeline quality |
| **R-NLP-2** | Maintain entity-type-specific accuracy dashboard (precision, recall, F1) per entity type, per language, per source type. Update weekly. | P0 | Operational visibility into pipeline quality |
| **R-NLP-3** | Define minimum F1 score targets per relation type. DEPENDS_ON must achieve ≥60% F1 before inclusion in propagation. Low-confidence relations excluded from high-confidence alerts. | P0 | RE accuracy directly determines propagation quality |
| **R-NLP-4** | Implement human-in-the-loop validation for relations below confidence threshold (default: 0.7). Validated relations become few-shot examples. | P1 | Quality control loop — without it, accuracy cannot improve |
| **R-NLP-5** | Entity disambiguation using priority hierarchy: ticker/ISIN/LEI match → canonical alias table → embedding similarity (≥0.92) → fuzzy string match with manual confirmation. | P0 | Entity dedup is the foundation of graph quality |
| **R-NLP-6** | Maintain canonical entity registry with all aliases, tickers, identifiers, and cross-lingual name mappings. Manually curate for seed 500 entities, semi-auto expand thereafter. | P0 | Cross-lingual entity resolution requires explicit mappings |
| **R-NLP-7** | Track entity merge/split events (Facebook→Meta) with identity chains for historical reference resolution. | P1 | Historical articles must resolve to current entities |
| **R-NLP-8** | Every LLM-extracted entity must undergo span-level verification: entity name must appear in source text (exact or edit distance ≤2). Non-verified entities flagged as "inferred." | P0 | Primary defense against LLM hallucination |
| **R-NLP-9** | Every LLM-extracted relation must include supporting source sentence(s). Relations without evidence text classified as "inferred," decay 3x faster. | P0 | Hallucination mitigation + explainability |
| **R-NLP-10** | Track hallucination rate per entity type, relation type, LLM model, and language. Measure against monthly 200-article human-annotated sample. | P0 | Can't fix what you can't measure |
| **R-NLP-11** | Define monthly NLP pipeline cost budget with breakdown by operation type (NER/RE, sentiment, disambiguation, signal extraction). | P0 | Projected $10K/month needs explicit acknowledgment and budgeting |
| **R-NLP-12** | Define LLM routing strategy: Claude for high-value/ambiguous/English, Ollama for low-priority/clear-cut. Routing criteria: language, source credibility, entity novelty, extraction difficulty. | P1 | Cost optimization without uniform quality loss |
| **R-NLP-13** | Phase multilingual NER: Phase 1 English (P0), Phase 2 Chinese+Japanese (P1), Phase 3 Korean+German (P2), Phase 4 remaining (P3). Each phase requires language-specific eval datasets. | P0 | Prevents unrealistic 13-language promise from blocking launch |
| **R-NLP-14** | Cross-lingual entity resolution must use canonical registry with language-specific alias tables maintained by language domain experts. | P1 | Auto-generated cross-lingual mappings are unreliable for financial entities |
| **R-NLP-15** | Establish human-annotated evaluation dataset of ≥500 articles with gold-standard entity and relation annotations. Quarterly evaluation against test set. | P0 | No evaluation data = no accountability for accuracy claims |
| **R-NLP-16** | Implement analyst review interface for NER/RE corrections. Corrections feed back into Claude prompt examples or local model fine-tuning data. | P1 | Continuous improvement loop |
| **R-NLP-17** | Article deduplication must distinguish: (a) exact/syndication duplicates (merge), (b) same-event different-angle (link, extract incremental info), (c) event updates (thread temporally). | P0 | Over-dedup loses signal; under-dedup inflates confidence |
| **R-NLP-18** | Event threading: group related articles into event chains with temporal ordering. Each update may produce new entity/relation extractions. | P1 | Events evolve — pipeline must track evolution, not just first mention |
| **R-NLP-19** | Define article retraction processing: when a source retracts an article, entities/relations extracted from it must be flagged and reviewed for removal or confidence reduction. | P1 | Retracted articles create false edges |
| **R-NLP-20** | Define long-document chunking strategy for earnings transcripts and regulatory filings (10K+ words). Specify chunk size, overlap, and entity co-reference resolution across chunks. | P1 | Single-call processing exceeds context limits; naive chunking misses cross-chunk entities |

---

## E. Pipeline Risks — What Fails Silently

### Risk 1: Silent Accuracy Degradation (CRITICAL)

LLM-based NER/RE accuracy degrades silently. There's no crash, no error message — the F1 score just drops because:
- Claude model update changes extraction behavior (Anthropic updates Sonnet without notice)
- Source content changes (new publication uses different formatting/terminology)
- Domain drift (new entity types not in the few-shot examples)
- Prompt context overflow (too many few-shot examples + long article = truncation)

At Two Sigma, we experienced a 12% F1 drop over 6 months in our NER pipeline because nobody was measuring accuracy continuously. We only noticed when a trader complained that entity extraction was "worse lately."

**Probability:** 90% within first year.  
**Impact:** Graph quality degrades, propagation becomes unreliable, users lose trust.  
**Mitigation:** R-NLP-2 (accuracy dashboard) + R-NLP-15 (evaluation dataset) + automated alerts when F1 drops below threshold.

### Risk 2: Entity Resolution Catastrophic Merges (HIGH)

A false merge (combining two different entities into one node) is worse than a missed duplicate. If "Samsung Electronics" and "Samsung SDI" are merged into one node, every SUPPLIES_TO and DEPENDS_ON edge is wrong. Propagation from a Samsung SDI event will incorrectly activate Samsung Electronics' edges.

With MERGE on insert (the Neo4j pattern), a fuzzy matching threshold of 0.85 will merge "Samsung Electronics" and "Samsung Electro-Mechanics" because their string similarity exceeds 0.85. This creates a catastrophic false node.

**Probability:** Very high (50%+) without a comprehensive alias table and strict matching rules.  
**Impact:** Silent — the graph looks fine but produces wrong propagation results. Only discoverable by domain expert review.  
**Mitigation:** R-NLP-5 (disambiguation hierarchy) + R-NLP-6 (canonical registry) + NEVER fuzzy match for entity creation — only exact match or manual confirmation.

### Risk 3: Hallucinated Relations Poisoning the Graph (HIGH)

As measured at Two Sigma: 8–15% of LLM-extracted relations are hallucinated. In a graph with 50K edges, that's 4,000–7,500 wrong edges. These wrong edges participate in propagation. A single hallucinated DEPENDS_ON edge between two major companies could create a phantom supply chain link that produces high-confidence, completely wrong propagation alerts.

**The insidious part:** Hallucinated relations look exactly like correct ones in the graph. There's no distinguishing property unless the system explicitly records the source sentence and validates it.

**Probability:** 100% — hallucination is inherent to LLM-based extraction.  
**Impact:** Catastrophic for user trust if a high-confidence alert is based on a hallucinated edge.  
**Mitigation:** R-NLP-8 (span verification) + R-NLP-9 (evidence sentences) + R-NLP-10 (hallucination tracking). Also: never create an edge from a single source article. Require ≥2 corroborating sources for edge creation, or flag single-source edges as "unconfirmed."

### Risk 4: Cost Overruns from Volume Spikes (MEDIUM)

During major market events (earnings season, geopolitical crises), article volume can spike 5–10x above normal. If normal is 10K articles/day at $135/day Claude cost, a spike to 50K–100K articles/day means $675–$1,350/day — potentially $40K/month during a busy month.

**Probability:** High — major events happen quarterly (earnings season alone is 4 weeks × 4 quarters).  
**Impact:** Budget overrun, or forced degradation (articles dropped/queued beyond latency SLA).  
**Mitigation:** R-NLP-12 (LLM routing) + circuit breaker on Claude spending (hard cap with fallback to Ollama) + priority queue (high-credibility sources first, low-credibility delayed/skipped during spikes).

### Risk 5: Regulatory Risk from Web Scraping (MEDIUM)

R-IA14 includes "web scraping" as an ingestion method. Systematically scraping news sites without permission risks:
- Terms of Service violations (most sites prohibit automated scraping)
- Copyright infringement (reproducing article text in the NER pipeline)
- GDPR concerns if scraping European sources that mention individuals
- Potential legal action from publishers (hiQ Labs v. LinkedIn notwithstanding, the legal landscape is evolving)

**Probability:** Medium — depends on scraping targets and jurisdiction.  
**Impact:** Legal exposure, source access revocation, potential cease-and-desist.  
**Mitigation:** Prioritize API-based and licensed data sources. For scraping: use only article excerpts/summaries, respect robots.txt, don't store full article text, transform extracted data beyond reproduction. Legal review of scraping strategy before launch.

---

## F. Critical Questions — Make or Break

1. **"What is your NER/RE accuracy on tail entities — the ones that actually matter?"** MKG's value proposition is discovering hidden Tier 2/3 dependencies. These involve companies that NER models have never seen in training data. If your pipeline can't accurately extract "Longsheng Chemical" from a Chinese article and resolve it to the correct entity, the entire Speed 3 thesis collapses. What's your plan for tail-entity accuracy?

2. **"How will you prevent LLM hallucination from poisoning the knowledge graph?"** One hallucinated DEPENDS_ON edge between Apple and a random chemical company could trigger a false propagation alert that costs a trader millions. What is your defense-in-depth against hallucinated extractions? Span verification alone is necessary but not sufficient.

3. **"Where is your evaluation data coming from?"** You can't measure accuracy without gold-standard annotations. Who is annotating? At what scale? How often? Financial NER annotation requires domain expertise — you can't use Mechanical Turk. A financial domain annotator costs $80–120/hour. 500 articles at 30 minutes each = $20K–$30K for one evaluation cycle.

4. **"What happens to the pipeline when Claude's model changes?"** Anthropic updates Claude periodically without warning. A model update can change extraction behavior, altering entity boundaries, relation types, and confidence calibration. Do you have regression tests? Can you pin to a specific model version? What's your response playbook for a model-change-induced accuracy drop?

5. **"How do you handle the cost-quality trade-off?"** At $10K/month in Claude API costs, you're spending $120K/year on NER/RE alone — before any other infrastructure costs. Ollama fallback reduces cost but also reduces accuracy. What's the quality floor you'll accept for cost savings? How does the routing decision get made — per article or per batch? Who monitors the quality metrics?

---
---

# CROSS-EXPERT SYNTHESIS — Iterations 3 & 4

## Areas of Agreement

| Finding | Dr. Müller (Graph DB) | Dr. Ibrahim (NLP/NER) | Implication |
|---------|----------------------|----------------------|-------------|
| **Requirements underspecify accuracy/quality targets** | No query performance targets at specific graph sizes | No NER/RE F1 targets per entity/relation type | Add measurable acceptance criteria to every core requirement |
| **Costs are unacknowledged** | Neo4j Enterprise may be required (~$36K+/year) | Claude API for NER/RE: ~$10K/month | Combined infrastructure cost: $156K+/year before compute, hosting, or staffing |
| **The spec treats hard problems as checkbox items** | Temporal versioning is a 3–6 month project described in 2 sentences | Multilingual NER across 13 languages is a multi-year effort listed as P1 | Scope into phases with explicit multi-quarter timelines |
| **Silent failure modes are the biggest risk** | Partial weight updates produce garbage propagation | Hallucinated relations poison the graph silently | Both domains need continuous monitoring, not just alerting on crashes |
| **Data quality determines system quality** | Financial decimals stored as doubles lose precision | 25–35% of extracted relations may be wrong | Garbage in one layer propagates through all downstream layers |
| **The 24-week plan produces a demo** | Temporal versioning alone takes 8–12 weeks of dedicated work | Multilingual NER with evaluation infrastructure takes 18+ months | Align expectations: Week 24 = working English-only demo, not production system |

## Areas of Divergence

| Topic | Dr. Müller (Graph DB) | Dr. Ibrahim (NLP/NER) | Resolution Needed |
|-------|----------------------|----------------------|-------------------|
| **Biggest risk** | Temporal versioning becomes the entire project | Silent accuracy degradation and hallucination poisoning | Both are valid — temporal versioning is a build risk, accuracy is a runtime risk |
| **Neo4j suitability** | CE is inadequate but Neo4j itself is fine at this scale | Largely neutral on DB choice — cares about entity resolution layer | Edition decision (CE vs Enterprise) must happen before any graph code is written |
| **MiroFish reuse value** | Graph storage patterns are solid; NER prompts need rework | NER pipeline is a starting point but needs significant rework for financial accuracy targets | Reuse code structure, but don't inherit accuracy assumptions |
| **Scaling concern** | Memory and performance at 10x scale (500K nodes) | Cost and latency at 10x volume (100K articles/day) | Both scale dimensions must be planned — graph AND pipeline |

## Cumulative Gap Summary (Iterations 1–4)

| Gap | First Identified | Impact | Status |
|-----|-----------------|--------|--------|
| Portfolio overlay missing | Iteration 1 (Marcus) | SHOW-STOPPER for financial vertical | Needs R-PORT1–R-PORT3 |
| BOM-level granularity missing | Iteration 2 (Priya) | SHOW-STOPPER for supply chain vertical | Needs R-PROD1–R-PROD4 |
| Cross-domain data isolation concern | Iteration 2 (Priya) | CRITICAL — hedge fund data + supply chain data | Architecture decision required |
| SOM overstated (10–50x) | Iterations 1 & 2 | Business planning error | Restate to $1M–$3M Year 1 |
| 24-week plan = demo only | Iterations 1 & 2 | Expectation management | Align: 24 weeks = English-only demo |
| Neo4j CE limitations conflict with 5+ requirements | **Iteration 3 (Kai)** | ARCHITECTURAL — cannot implement RBAC, HA, multi-DB, online backup | R-GRAPH-1: edition decision required |
| Temporal versioning completely unspecified | **Iteration 3 (Kai)** | ARCHITECTURAL — 3–6 month project with zero specification | R-GRAPH-2, R-GRAPH-3 |
| Financial Decimal precision impossible in Neo4j | **Iteration 3 (Kai)** | DATA INTEGRITY — violates R-KG11 | R-GRAPH-5: store as integer or in PostgreSQL |
| Edge embeddings unsupported in Neo4j 5.x | **Iteration 3 (Kai)** | FEATURE GAP — R-KG14 partially impossible | R-GRAPH-6: reify or use pgvector |
| No NER/RE accuracy targets | **Iteration 4 (Aisha)** | QUALITY — no way to measure or improve pipeline | R-NLP-1, R-NLP-3 |
| LLM hallucination poisoning the graph | **Iteration 4 (Aisha)** | INTEGRITY — 8–15% of relations may be hallucinated | R-NLP-8, R-NLP-9, R-NLP-10 |
| Multilingual NER is multi-year, not P1 | **Iteration 4 (Aisha)** | SCOPE — 13 languages in 24 weeks is fantasy | R-NLP-13: phase English-first |
| NLP pipeline costs ~$10K/month unbudgeted | **Iteration 4 (Aisha)** | FINANCIAL — $120K/year in Claude API alone | R-NLP-11, R-NLP-12 |
| No evaluation data or accuracy monitoring | **Iteration 4 (Aisha)** | OPERATIONAL — can't measure accuracy without gold data | R-NLP-15, R-NLP-16 |
| Entity disambiguation is a PhD problem, not a feature | **Iteration 4 (Aisha)** | QUALITY — determines graph quality | R-NLP-5, R-NLP-6 |

## New Requirements Count

| Iteration | Expert | New Requirements | Critical (P0) |
|-----------|--------|-----------------|---------------|
| 1 | Marcus Chen (Hedge Fund PM) | 15 | 9 |
| 2 | Dr. Priya Sharma (Supply Chain VP) | 15 | 6 |
| 3 | Dr. Kai Müller (Graph DB Architect) | 12 | 7 |
| 4 | Dr. Aisha Ibrahim (NLP/NER Scientist) | 20 | 12 |
| **Total** | | **62** | **34** |

## Top 5 Cumulative Risks (from all 4 experts)

1. **The product is two products pretending to be one.** Financial and supply chain verticals need different data models (company-level vs BOM-level), different outputs (impact scores vs disruption duration), different data isolation guarantees (shared vs proprietary), and different sales cycles. Building both in one 24-week sprint guarantees neither works well. *(Iterations 1, 2, 3)*

2. **The NLP pipeline is the quality bottleneck for the entire system.** Graph quality = NER/RE quality. At ~65–75% F1 for relation extraction, 25–35% of edges are wrong. A 4-hop propagation through a graph with 30% wrong edges has a ~24% chance of all-correct path. The system will produce confident-looking wrong answers that destroy user trust. *(Iteration 4)*

3. **Neo4j CE cannot deliver 5+ stated requirements.** The spec was written assuming Neo4j Enterprise capabilities (RBAC, HA, multi-database, online backup) while choosing CE. Either budget $36K+/year for Enterprise, or accept significant capability reductions and app-level workarounds. *(Iteration 3)*

4. **No evaluation infrastructure planned.** Neither the graph layer (temporal query correctness) nor the NLP layer (NER/RE F1 scores) have evaluation frameworks specified. Without measurement, there is no quality — only hope. Historical accuracy tracking (R-EXP5) is listed but the evaluation methodology is absent. *(Iterations 3, 4)*

5. **Cost model is missing.** Neo4j Enterprise: ~$36K+/year. Claude API for NER/RE: ~$120K/year. Compute/hosting for Neo4j + PostgreSQL + Celery + API: ~$30K+/year. Total infrastructure: ~$186K+ before any engineering salaries. This is not acknowledged in the spec and may be incompatible with the pricing/revenue targets. *(Iterations 3, 4)*

---

## Recommended Priority Actions (Cumulative)

*Updated to include findings from all 4 experts:*

1. **DECIDE: Neo4j CE vs Enterprise vs Alternative** — Block all graph development until the edition is selected and requirements are remapped to what's achievable. *(New from Iteration 3)*

2. **DECIDE: Data isolation architecture** — Financial vs supply chain data separation model must be resolved before ANY data enters the graph. *(From Iteration 2, reinforced by Iteration 3)*

3. **SPECIFY: Temporal versioning approach** — Choose bitemporal vs event sourcing vs snapshot. This is a 3–6 month project that gates backtesting, historical analysis, and graph replay. *(New from Iteration 3)*

4. **SPECIFY: NER/RE accuracy targets and evaluation infrastructure** — Define F1 targets per entity/relation type. Budget for evaluation dataset creation (~$20K–$30K). Build accuracy dashboard. *(New from Iteration 4)*

5. **BUILD: Hallucination defense layer** — Span verification + evidence sentences + multi-source corroboration before any edge is created in the graph. Non-negotiable for financial intelligence. *(New from Iteration 4)*

6. **BUDGET: Acknowledge $186K+/year infrastructure costs** — Include in business model. Validate that Year 1 pricing and revenue targets can sustain this burn rate. *(New from Iterations 3, 4)*

7. **PHASE: Multilingual NER** — English only at launch (P0). Chinese + Japanese at +6 months (P1). All others P2+. Do not attempt 13 languages in parallel. *(New from Iteration 4)*

8. **SPLIT: Vertical-specific requirement addenda** — As recommended in Iteration 1-2. Now reinforced: the graph layer and NLP layer are shared, but output schemas, data models (BOM vs company-level), and integration requirements must be specified per vertical. *(From Iterations 1, 2)*

9. **UPGRADE: Backtesting to P0** — No user persona (financial or supply chain) adopts without historical validation. *(From Iteration 1, supported by all subsequent experts)*

10. **RESTATE: SOM to $1M–$3M Year 1** — Now supported by 4/4 experts as the realistic range. *(Consensus from all iterations)*

---

*Next iteration: Experts 5 & 6 — Quantitative Research Lead (systematic strategy firm) + Chief Data Officer (financial data vendor)*
