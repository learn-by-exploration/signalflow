# MKG Expert Panel Review — Iterations 7 & 8

> **Review Date:** 31 March 2026  
> **Document Under Review:** `core/MKG_REQUIREMENTS.md`  
> **Review Scope:** Full requirements document (Sections 1–15)  
> **Review Type:** Expert Panel — Iterations 7 & 8 of 10  
> **Previous Iterations:** [Iteration 1-2](iteration-1-2.md) (Hedge Fund PM + Supply Chain VP), [Iteration 3-4](iteration-3-4.md) (Graph DB Architect + NLP Scientist), [Iteration 5-6](iteration-5-6.md) (Enterprise PM/GTM + CISO/Compliance)

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
| **Cumulative** | | 109 new requirements identified, 62 at P0 |

---

## Panel Members — This Iteration

| # | Expert | Role | Perspective |
|---|--------|------|-------------|
| 7 | **Ethan Kowalski** | Data Pipeline Architect, 14 years (Netflix Data Platform → Confluent → Stripe streaming infra) | Streaming architecture, exactly-once semantics, pipeline reliability, cost optimization |
| 8 | **Yuki Tanaka** | Financial UX Designer, 12 years (Bloomberg Terminal UX → Citadel frontend → own fintech design studio) | Graph visualization, information density, progressive disclosure, real-time UI, analyst workflows |

---
---

# EXPERT 7: Ethan Kowalski — Data Pipeline Architect

*Background: 5 years at Netflix building the data platform that processes 1.5 trillion events/day — designed the backpressure and dead-letter systems for their real-time recommendation pipeline. 4 years at Confluent as Principal Architect on Kafka Connect and ksqlDB for financial services customers. Last 3 years at Stripe designing the streaming infrastructure for real-time fraud detection (50ms SLA, exactly-once financial transaction processing). Has deployed production NLP/ML pipelines at all three companies. Deeply experienced in the gap between "the architecture diagram" and "what actually runs at 3 AM on a Sunday."*

---

## A. Concept-Requirement Alignment — Score: 4/10

**What aligns well:**

- The pipeline concept is sound in principle: news sources → NER/RE extraction → entity deduplication → graph mutation → weight adjustment → propagation. This is a textbook stream processing topology. At Netflix, our recommendation pipeline had a similar shape: event sources → feature extraction → model inference → personalization → delivery. The stages are right.

- The Celery + Redis choice (Section 12.1) makes sense for a prototype. It's the known quantity from SignalFlow. At low volume (100 articles/day during Phase 2), Celery will work fine. I've seen dozens of teams prototype successfully on Celery before migrating.

- The market hours awareness requirement (existing in SignalFlow's Celery scheduler) is a genuinely thoughtful operational detail that most pipeline architects forget. The market-awareness gating means you're not wasting compute or API budget during closed hours. This carries over well to MKG's news pipeline — article flow drops 80% outside market hours.

**Why this is 4/10 — the pipeline architecture has fundamental gaps:**

1. **There is no pipeline architecture.** The document describes pipeline *stages* (Layer 1 through Layer 4) and pipeline *SLAs* (R-NF1 through R-NF8), but there is no specification of the pipeline *topology*, *failure semantics*, *ordering guarantees*, or *processing model*. This is like specifying a building's rooms without specifying the plumbing.

2. **Celery is the wrong tool for the core pipeline once you need reliability guarantees.** Celery + Redis is a task queue, not a stream processing framework. It has at-most-once delivery by default. Redis as a broker can lose messages on restart. There is no native exactly-once processing, no dead-letter queue, no backpressure mechanism, no stream replay. For a system that claims to produce "[intelligence] before anyone else connects the dots" — losing articles silently is existential.

3. **The spec treats the LLM (Claude API) as a stateless function call, not as the most expensive, most unreliable, highest-latency stage in the pipeline.** At Stripe, we learned this lesson with ML model inference: the model is never "just a function." It has variable latency (200ms–30s), rate limits (100 calls/hour per R-IA documentation), cost constraints ($10K/month per Dr. Ibrahim's estimate), and failure modes that don't map to standard retry logic (partial JSON responses, hallucinated entities, prompt injection in source articles).

4. **There is no concept of pipeline observability.** The spec mentions Sentry + Prometheus (Section 12.1) but doesn't define what pipeline metrics to track. At Netflix, our pipeline had 47 distinct metrics. Here there are zero defined. Without metrics, you can't answer: "Is the pipeline healthy? Are we keeping up with article flow? What's the extraction error rate? What's the graph mutation throughput?"

5. **The 10,000 articles/day target (R-IA10, R-SC2) requires a pipeline that can handle bursts, not averages.** 10K/day is 7 articles/minute sustained. But news follows power-law distributions: an OPEC announcement or TSMC earthquake generates 200+ articles in 30 minutes. The pipeline must handle 100x burst over sustained average. The document doesn't mention burst capacity anywhere.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Pipeline Topology — NO SPECIFICATION EXISTS

The document describes four layers but doesn't specify how data flows between them. At minimum, a pipeline spec must define:

**What's missing — the complete data flow:**

```
SOURCE STAGE         EXTRACTION STAGE        GRAPH STAGE          OUTPUT STAGE
┌──────────┐        ┌──────────────┐        ┌──────────────┐     ┌─────────────┐
│ RSS/API  │──┐     │              │        │              │     │             │
│ Scrapers │  │     │  Dedup +     │        │  Entity      │     │ Propagation │
│ Filings  │  ├────►│  NER/RE      ├───────►│  Resolution  ├────►│ Engine      │
│ Transcr. │  │     │  (Claude)    │        │  + Graph     │     │ + Alerts    │
│ Social   │──┘     │              │        │  Mutation    │     │             │
└──────────┘        └──────────────┘        └──────────────┘     └─────────────┘
     ▲                     │                       │                    │
     │                     ▼                       ▼                    ▼
     │              ┌──────────────┐        ┌──────────────┐     ┌─────────────┐
     │              │  DLQ         │        │ Weight Audit  │     │ WebSocket / │
     │              │  (failures)  │        │ Log (PG)      │     │ API / Alert │
     │              └──────────────┘        └──────────────┘     └─────────────┘
     │
  ┌──────────────┐
  │  Source       │
  │  Registry    │
  │  (schedule,  │
  │   health)    │
  └──────────────┘
```

Each stage needs: input schema, output schema, ordering guarantee, failure behavior, retry policy, timeout, concurrency model, and backpressure signal.

> **R-PIPE-1** (P0): System must define an explicit pipeline topology document specifying every stage, its input/output schemas, failure mode, retry policy, ordering guarantee, and concurrency model. Each stage must be independently deployable and testable.

> **R-PIPE-2** (P0): System must implement a pipeline DAG (directed acyclic graph) with typed channels between stages. Each channel must define: message schema (Pydantic or Avro), serialization format, maximum message size, and TTL.

### B2. Processing Semantics — AT-MOST-ONCE IS UNACCEPTABLE

Celery + Redis with default configuration provides at-most-once delivery:
- If a worker crashes mid-task, the message is lost.
- If Redis restarts, unacknowledged messages in the queue can be lost.
- If the Claude API returns a partial response and the worker crashes before writing it, the article is never retried.

For a financial intelligence system, losing a signal — even one article — can mean missing a cascading event. At Stripe, losing a single fraud signal could mean millions in losses; we built exactly-once processing over Kafka with idempotent producers and transactional consumers.

MKG doesn't need Stripe-level guarantees for all stages. But it needs **at-least-once** semantics for the source→extraction pipeline, and **idempotent write** semantics for the graph mutation stage (which Neo4j's MERGE pattern already provides for entity creation, but not for weight updates).

> **R-PIPE-3** (P0): Source ingestion through NER/RE extraction must guarantee at-least-once processing. No article that enters the pipeline can be silently dropped. Failed extractions must be routed to a dead-letter queue with the original article, failure reason, timestamp, and retry count.

> **R-PIPE-4** (P0): Graph mutation stage must be idempotent. Processing the same extraction result twice must not corrupt graph state, create duplicate edges, or double-count weight adjustments. Idempotency key = `(article_id, entity_pair, relationship_type)`.

> **R-PIPE-5** (P1): System must support pipeline replay — the ability to reprocess all articles from a given time range through the extraction pipeline. This is essential for: (a) re-running after NER/RE model improvements, (b) backfilling after outages, (c) building evaluation datasets. Requires durable article storage (not just in the processing queue).

### B3. The Claude API Is a Pipeline Bottleneck — Not a Function Call

R-IA10 requires 10,000 articles/day. The Claude API is rate-limited to 100 calls/hour (per the existing SignalFlow cost control rules). At 10 articles per Claude call (batching), that's 1,000 batches/day = 42 batches/hour. This is within the 100 calls/hour limit. But:

**The real constraints:**

| Constraint | Value | Pipeline Impact |
|------------|-------|-----------------|
| Claude rate limit | 100 calls/hour | 42 batches/hour = theoretical max 10K articles/day with perfect batching |
| Claude latency | 2–15 seconds per call | 42 batches × ~8s avg = 336 seconds of serial processing per hour = 5.6 min/hour blocked |
| Claude cost | ~$0.30 per 10-article batch (Sonnet, ~4K tokens in, ~1K out) | 1,000 batches/day × $0.30 = **$300/day = $9,000/month** |
| Claude failure rate | 1–3% (rate limit, timeout, malformed response) | 10–30 failed batches/day = 100–300 articles needing retry |
| Claude context overflow | 8K–100K tokens depending on article length | Long articles must be truncated or chunked — extraction quality degrades |
| Burst capacity | 100+ articles in 30 min during major events | Can only process ~21 batches in 30 min = 210 articles — 50% will be delayed |

**The missing architecture:** The Claude API stage must be treated as a bounded, rate-limited, expensive resource with its own:
- Admission control (prioritize high-credibility sources during burst)
- Request queue with priority ordering (breaking news > routine article)
- Circuit breaker (if Claude returns 5 consecutive errors, stop sending for 60s)
- Cost accumulator with kill switch (if daily spend exceeds $X, switch to fallback)
- Fallback extraction mode (regex-based entity extraction for degraded operation)

> **R-PIPE-6** (P0): The LLM extraction stage must implement a rate-aware request scheduler with: (a) priority queue (source credibility × article recency), (b) admission control during burst periods, (c) circuit breaker with configurable error threshold, (d) daily cost accumulator with automatic fallback to non-LLM extraction when budget threshold is reached.

> **R-PIPE-7** (P0): System must define a fallback extraction mode that operates without the Claude API. Minimum capability: regex/rule-based entity recognition for the top 500 known entities, relationship extraction from structured data (SEC filings XBRL, earnings transcript speaker tags), and sentiment from headline keywords. This ensures the pipeline never fully stops.

> **R-PIPE-8** (P1): System must implement request coalescing — when multiple articles about the same event arrive within a configurable window (default 5 minutes), batch them into a single Claude API call with a multi-article prompt. This reduces API calls during bursts and produces better cross-article entity resolution.

### B4. Dead Letter Queue — NO ERROR HANDLING FOR PIPELINE FAILURES

The document mentions "prompt injection prevention" (R-IA13) and "source credibility scoring" (R-IA12) but has no specification for what happens when pipeline stages fail. At Netflix, 2–5% of events failed some processing stage on any given day. The question isn't whether failures happen — it's whether you detect them, preserve the failed inputs, and have a path to recovery.

**Failure modes the document doesn't address:**

| Stage | Failure Mode | Current Handling | Required Handling |
|-------|--------------|------------------|-------------------|
| Source ingestion | RSS feed returns 500 | Unknown — probably swallowed | Retry 3x with exponential backoff, then mark source unhealthy |
| Source ingestion | Scraper blocked (403/CAPTCHA) | Unknown | Alert + circuit breaker on that source + DLQ entry |
| Article dedup | Dedup service crashes | Unknown | At-least-once with idempotent downstream = safe to re-deliver |
| NER/RE extraction | Claude returns malformed JSON | Unknown | Parse with lenient JSON, log partial result, DLQ remainder |
| NER/RE extraction | Claude hallucinates entity that doesn't exist | Unknown — goes into graph | Verification stage: entity must exist in known-entity index OR be flagged as "unverified" |
| Graph mutation | Neo4j connection pool exhausted | Unknown | Retry with backoff, queue mutations in Redis, alert if queue depth > threshold |
| Graph mutation | Concurrent weight updates to same edge | Unknown — last write wins | Optimistic locking: read current weight, compute delta, CAS (compare-and-swap) |
| Weight adjustment | Signal references entity not in graph | Unknown | Create stub entity with `discovered_via = "signal"`, flag for verification |
| Propagation | Propagation takes >60s (R-PE6 violation) | Unknown | Timeout + return partial results + log which paths were not traversed |

> **R-PIPE-9** (P0): System must implement a dead-letter queue (DLQ) for every pipeline stage. Each DLQ entry must contain: original message payload, stage name, failure reason, failure timestamp, retry count, and source article metadata. DLQ must be queryable and support manual reprocessing.

> **R-PIPE-10** (P0): System must implement a pipeline health dashboard showing in real-time: (a) articles ingested per source per hour, (b) extraction success/failure rate, (c) average extraction latency (p50, p95, p99), (d) DLQ depth per stage, (e) Claude API spend (hourly/daily/monthly), (f) graph mutation throughput, (g) end-to-end pipeline latency (article publication → graph update). Minimum 15 metrics.

### B5. Backpressure — THE PIPELINE CAN'T PUSH BACK

When a downstream stage becomes slow (Claude API rate-limited, Neo4j under heavy query load, network partition), upstream stages must slow down. Without backpressure, the pipeline either:
- **Drops messages** (at-most-once) — losing financial signals
- **OOMs** (out of memory) — queues grow unboundedly until worker crashes
- **Creates cascading failure** — Redis fills up, Celery workers can't ACK, everything stops

Celery has no native backpressure mechanism. The worker prefetch count (`worker_prefetch_multiplier`) is the only lever, and it's static — it can't adapt to downstream pressure.

> **R-PIPE-11** (P0): System must implement backpressure between pipeline stages. When the extraction stage cannot keep up with ingestion (queue depth exceeds configurable threshold), the ingestion stage must reduce polling frequency. When the graph mutation stage is slow, extraction results must be buffered durably (not just in Redis memory). A stuck stage must not cause upstream OOM or downstream starvation.

> **R-PIPE-12** (P1): System must define maximum queue depth per stage, with alerts at 50%, 80%, and 100% capacity. At 100%, the stage must apply admission control (drop lowest-priority articles first, based on source credibility).

### B6. Ordering Guarantees — PARTIALLY SPECIFIED

For most articles, processing order doesn't matter — the graph converges regardless of whether you process article A or article B first. But two scenarios require ordering:

1. **Contradictory signals**: Article A says "TSMC expands capacity" → edge weight up. Article B (published 2 hours later) says "TSMC denies expansion" → edge weight down. If processed out of order, the graph ends up in the wrong state.

2. **Weight decay**: If article B's timestamp is used for decay computation, processing article A after article B will decay from the wrong baseline.

> **R-PIPE-13** (P1): System must guarantee per-entity ordering — all articles mentioning the same entity must be processed in publication-timestamp order within that entity's partition. Cross-entity ordering is not required. Implementation: partition extraction queue by primary entity, with per-partition FIFO processing.

### B7. Cost Governance — THE $10K/MONTH ELEPHANT

Dr. Ibrahim (Iteration 4) identified ~$10K/month in Claude API costs. My analysis above confirms $9K/month at 10K articles/day with Sonnet. But the document's budget section (from SignalFlow's $30/month) doesn't address MKG at all.

At Stripe, our ML inference pipeline ran at $40K/month for fraud models. We built an explicit cost governance layer with:
- Per-model cost tracking (cost per inference, cost per positive detection)
- Budget allocation per team/use-case
- Automatic degradation when budget is 80% consumed
- Weekly cost reports to engineering leadership

MKG needs the same discipline.

> **R-PIPE-14** (P0): System must implement a cost governance layer for the Claude API with: (a) real-time spend tracking per stage (NER, RE, sentiment, reasoning), (b) configurable daily/monthly budget caps, (c) automatic fallback to non-LLM extraction at 80% of daily budget, (d) complete shutdown of LLM calls at 100% of daily budget, (e) cost-per-article and cost-per-entity metrics.

> **R-PIPE-15** (P1): System must implement a cost-efficiency optimization loop: (a) track extraction quality by source — if a source consistently yields low-value entities (0 new relationships per 100 articles), reduce its polling priority, (b) track Claude API cost per *useful extraction* (extractions that create or update graph edges), (c) monthly report showing cost-per-useful-edge-update by source, entity type, and relationship type.

### B8. Source Management — TREATED AS STATIC

The document lists data sources (R-DS1 through R-DS8) as if they're static configuration. In reality, sources are the most operationally volatile part of any news pipeline:

- RSS feeds change URLs, break, go stale, or get rate-limited
- Web scrapers break when sites redesign (happens monthly for major news sites)
- API keys expire, get revoked, or hit undocumented rate limits
- New sources emerge (a new industry blog becomes the best source for specialty glass supply chain intelligence)
- Source credibility changes over time (a previously reliable source starts publishing sponsored content)

At Confluent, we built a "Source Registry" — a database-backed catalog of every data source with health tracking, schema validation, and automatic circuit-breaking.

> **R-PIPE-16** (P0): System must implement a Source Registry tracking for each data source: URL/endpoint, type (RSS/API/scraper), polling frequency, last successful fetch, consecutive failure count, average articles per fetch, health status (healthy/degraded/dead), credibility score, and cost per article. Sources with >5 consecutive failures must be automatically marked as degraded and polling frequency reduced.

> **R-PIPE-17** (P1): System must support dynamic source addition and removal via admin API without pipeline restart. New sources must go through a 24-hour "probation" period where extracted entities are flagged as low-confidence before entering the active pipeline.

### B9. Data Durability — ARTICLES ARE NOT STORED

The current architecture processes articles through the pipeline and stores only the extracted entities/relationships in Neo4j. The original article text is not specified to be stored anywhere.

This is a critical gap because:
- **Pipeline replay** requires the original articles (R-PIPE-5)
- **Audit trail** for regulatory compliance requires proving which article produced which edge (R-EXP2)
- **NER/RE improvement** requires a corpus of source articles with annotations
- **Hallucination detection** requires comparing Claude's extractions against the source text
- **Legal defensibility** — if a client trades on MKG intelligence and it's wrong, you need to show what article produced that signal

> **R-PIPE-18** (P0): System must store all ingested articles in a durable, append-only store (PostgreSQL or object storage) with: article_id, source_url, fetch_timestamp, publication_timestamp, full text, language, source credibility score at time of ingestion. Retention: minimum 2 years. This store is the "source of truth" for pipeline replay and regulatory audit.

---

## C. Requirement Challenges

### C1. Celery-to-Stream Migration Path

The decision to start with Celery + Redis is pragmatic — it's known from SignalFlow. But every constraint above pushes toward a streaming architecture:

| Need | Celery + Redis | Kafka / Pulsar / Redis Streams |
|------|---------------|-------------------------------|
| At-least-once delivery | ❌ Redis can lose messages | ✅ Durable log with offset tracking |
| Dead-letter queue | ❌ Must build custom | ✅ Native DLQ support |
| Backpressure | ❌ No native mechanism | ✅ Consumer groups with lag monitoring |
| Per-entity ordering | ❌ No partition concept | ✅ Key-based partitioning |
| Pipeline replay | ❌ Messages are consumed and gone | ✅ Replay from any offset |
| Pipeline metrics | ⚠️ Celery Flower (basic) | ✅ Consumer lag, throughput, errors |
| Horizontal scaling | ⚠️ Worker-level only, no partition awareness | ✅ Partition-based parallelism |

**Recommendation:** Start with Celery for Phase 1–2 prototype. But architect the pipeline stages behind an abstract `PipelineStage` interface so that the broker can be swapped to Redis Streams (available in Redis 5+, already deployed) or Kafka without rewriting business logic.

> **R-PIPE-19** (P1): Pipeline stages must be implemented behind a `PipelineStage` abstract interface with methods: `process(message) → result`, `on_failure(message, error) → DLQ entry`, `health_check() → status`. The broker (Celery/Redis Streams/Kafka) must be a pluggable transport layer, not coupled to business logic.

### C2. Scaling from 10K to 100K Articles/Day

R-SC2 requires scaling from 10K to 100K articles/day "with horizontal scaling." But:

- 100K articles/day × $0.03/article (Claude Sonnet) = **$3,000/day = $90K/month** in LLM costs alone
- 100K articles/day = ~70/minute sustained, ~700/minute during bursts
- Claude API rate limit of 100 calls/hour = 1,000 batched articles/hour = 24K articles/day theoretical max with single API key

At 100K/day, you'd need either:
- 5 separate Anthropic API keys running in parallel (against ToS?)
- A self-hosted LLM (which Dr. Ibrahim noted has 15–25% lower accuracy)
- A tiered extraction strategy: top 20% articles get Claude, remaining 80% get a local model

> **R-PIPE-20** (P1): System must define a tiered extraction strategy for scaling beyond 10K articles/day. Tier 1 (high-credibility sources + breaking news): Claude API. Tier 2 (medium-credibility, routine articles): self-hosted LLM (Mistral/Llama). Tier 3 (low-credibility, monitoring only): regex/rule-based extraction. The tier assignment must be automatic based on source credibility score × article novelty score.

### C3. Exactly-Once Weight Updates — Hard Problem

R-KG9 requires auditable weight changes. R-WAN7 requires <30 seconds for weight updates. But concurrent weight updates to the same edge from different pipeline workers create a race condition:

```
Worker A reads edge(TSMC→Apple).weight = 0.7
Worker B reads edge(TSMC→Apple).weight = 0.7
Worker A computes delta +0.1, writes 0.8
Worker B computes delta -0.05, writes 0.65  ← overwrites A's update
```

The correct result should be 0.7 + 0.1 - 0.05 = 0.75. But with last-write-wins, you get 0.65.

> **R-PIPE-21** (P0): Edge weight updates must use compare-and-swap (CAS) semantics or serialized per-edge writes. Implementation options: (a) Neo4j's `SET e.weight = e.weight + $delta` (atomic increment in Cypher), (b) per-edge write lock with Redis distributed lock, (c) single-writer-per-entity architecture with partitioned workers. The chosen approach must be documented with correctness proof and performance benchmarks.

---

## D. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Celery silently drops articles during Redis restarts, losing critical signals | HIGH | HIGH | R-PIPE-3: at-least-once delivery; R-PIPE-18: durable article store |
| 2 | Claude API cost exceeds $10K/month as article volume grows from development to production | HIGH | HIGH | R-PIPE-14: cost governance; R-PIPE-15: cost optimization; R-PIPE-20: tiered extraction |
| 3 | Pipeline cannot handle burst traffic during major market events (100+ articles in 30 min) | HIGH | MEDIUM | R-PIPE-6: admission control; R-PIPE-11: backpressure; R-PIPE-12: queue depth limits |
| 4 | Race conditions in concurrent weight updates produce incorrect graph state | MEDIUM | HIGH | R-PIPE-21: CAS semantics for weight updates |
| 5 | No dead-letter queue means failed extractions are silently lost — graph has blind spots | HIGH | HIGH | R-PIPE-9: DLQ per stage; R-PIPE-10: pipeline health dashboard |
| 6 | Source feeds break (URL changes, blocks, schema drift) with no detection mechanism | HIGH | MEDIUM | R-PIPE-16: Source Registry with health tracking; R-PIPE-17: dynamic source management |
| 7 | Original articles not stored — cannot prove extraction correctness for audits or replay pipeline | MEDIUM | HIGH | R-PIPE-18: durable article store with 2-year retention |
| 8 | Pipeline observability is bolted on post-launch, not designed in — issues are discovered by clients, not engineers | HIGH | HIGH | R-PIPE-10: 15+ defined metrics from day 1 |

---

## E. Five Critical Questions

1. **What is the SLA for article loss?** Is it acceptable to lose 1% of articles? 0.1%? Zero? The answer determines whether Celery + Redis is viable or whether you need a durable log (Kafka/Pulsar). The cost and complexity difference between "mostly reliable" and "zero loss" is 5–10x.

2. **What happens when Claude API is down for 2 hours during a major market event?** The current spec has no fallback extraction mode. If TSMC has a catastrophic fab fire and Claude is experiencing a service outage, MKG goes blind during the exact moment it's needed most. R-PIPE-7 addresses this, but the fallback quality threshold must be defined — is 60% extraction accuracy acceptable in degraded mode?

3. **Who owns pipeline operations?** At Netflix, the data pipeline had a dedicated 6-person on-call rotation. At Stripe, 4 engineers. A 10K articles/day pipeline with LLM inference, graph mutations, and real-time propagation needs 24/7 operational attention. If this is a 1–2 person team, the pipeline reliability ambitions are unrealistic without significant automation (auto-healing, auto-scaling, self-monitoring).

4. **What is the acceptable end-to-end latency distribution, not just the target?** R-NF1 says "<5 minutes" for article-to-graph. Is this the p50? p99? If 95% of articles are processed in 2 minutes but 5% take 45 minutes (because they hit Claude rate limits during burst), is that acceptable? For Speed 3 alpha, 45-minute stragglers during major events could be the difference between capturing and missing the opportunity.

5. **How do you validate that the pipeline is producing correct results?** There is no end-to-end pipeline test specification. How do you know that today's pipeline run didn't miss 500 articles, hallucinate 200 entities, duplicate 50 edges, and silently drop 30 weight updates? Without continuous validation (checksums per batch, reconciliation jobs, extraction accuracy sampling), you have no idea whether the graph reflects reality.

---
---

# EXPERT 8: Yuki Tanaka — Financial UX Designer

*Background: 6 years on the Bloomberg Terminal UX team (2014–2020) — redesigned the security analysis workflow used by 325,000 subscribers, introduced the "Launchpad" customizable dashboard that became Bloomberg's most-adopted UI update in a decade. 3 years at Citadel's internal tools team building real-time portfolio dashboards for event-driven PMs processing 500+ signals/day. Then founded a fintech design studio specializing in data-dense financial interfaces for institutional clients (Two Sigma, D.E. Shaw, Bridgewater front-office tools). Has shipped 30+ dense financial UIs. Voted "Designer to Watch" by Finance Technologist 2024.*

---

## A. Concept-Requirement Alignment — Score: 4/10

**What aligns well:**

- The core information architecture — event trigger → impact list → causal chain — is the right conceptual flow for analyst workflows. At Bloomberg, the security analysis workflow follows the same pattern: trigger (news/event) → who's affected → why → what to do. MKG maps to this mental model well.

- The "Speed 3" framing gives designers a clear constraint: the user has *hours*, not milliseconds. This is a fundamentally different UX from Bloomberg's terminal (Speed 1–2, real-time reaction) and means MKG's UI can afford to be more explanatory and educational. Bloomberg's UI assumes the user already knows what they're looking at. MKG can guide the user through a causal chain at a pace that builds understanding.

- Having both REST and WebSocket endpoints (R-OUT1, R-OUT2) means the UI can show a static snapshot (initial load) and then update incrementally (new signals arrive). This is the correct pattern — we used it for Bloomberg's portfolio monitor and Citadel's real-time P&L dashboard.

**Why this is 4/10 — the visualization specification is dangerously thin:**

1. **R-OUT3 is one line that describes a multi-month engineering and design challenge:** "Interactive graph visualization (force-directed layout, filter by entity type, zoom to subgraph)." This is like saying "build a spreadsheet" in one line. Force-directed graph visualization at the stated scale (5K–50K nodes) is a known-hard problem in both performance and information design. At Bloomberg, we spent 14 months building the supply chain visualization for a simpler graph (200 entities, 1,000 edges). The document allocates exactly zero design requirements to this.

2. **There is no information hierarchy specified.** A financial analyst under time pressure (incoming market event, 60-second window to assess impact) cannot parse a 5,000-node force-directed graph. The document doesn't specify: What is the first thing the user sees? What is the second? How deep can they drill? What level of detail is shown by default vs on demand? Without information hierarchy, the UI will be a beautiful, unusable hairball.

3. **There is no specification for the core user workflow.** The document defines buyer profiles (Section 7) and system capabilities but never defines: Where does the user start? What do they click first? What question are they trying to answer? How does the UI support the decision they make after seeing the answer? At Citadel, every dashboard was designed around a specific "decision flow" — the UI wasn't an information display; it was a decision tool.

4. **"Interactive graph visualization" + "real-time updates" is a UX anti-pattern for financial decision-making.** If the graph is constantly shifting (nodes moving, edges appearing, weights changing) while the analyst is trying to trace a causal chain, the visualization becomes adversarial. At Bloomberg, we learned that real-time updates in spatial visualizations cause "visual vertigo" — users lose their mental model of where things are. The document doesn't address this tension at all.

5. **No mobile specification whatsoever.** The SignalFlow spec explicitly says "she'll check it on her phone." For MKG targeting hedge fund PMs, mobile is equally important — event-driven PMs check alerts on their phones 60% of the time outside market hours. Complex graph visualization on mobile is a distinct design challenge with different constraints.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Information Hierarchy — THE MOST CRITICAL MISSING SPECIFICATION

When a propagation event fires (e.g., "TSMC fab disruption detected"), the user needs to consume information in a specific order:

**Level 1 — The Alert (2 seconds):** What happened? How big? → "TSMC: Fab fire detected. Impact: SEVERE. 47 entities affected."

**Level 2 — The Impact Summary (10 seconds):** Who's most affected? → Ranked table: #1 NVIDIA (-15.2%, confidence 89%), #2 Apple (-8.7%, confidence 76%), #3 AMD (-6.1%, confidence 72%)... top 10.

**Level 3 — The Causal Chain (30 seconds):** Why is NVIDIA affected? → "TSMC → (SUPPLIES_TO, w=0.91) → NVIDIA → N100 GPU depends on TSMC N3 process exclusively → no alternative supplier → 3-month production halt estimated."

**Level 4 — The Evidence (2 minutes):** What data supports this? → Source articles, edge weight history, confidence breakdown, contradictory signals.

**Level 5 — The Context (5 minutes):** How does this compare to previous events? → Historical propagation comparisons, backtested outcomes.

**Level 6 — The Graph (as needed):** Show me the full network. → Interactive graph filtered to this event's impact zone.

The document jumps straight to Level 6 (graph visualization) without specifying Levels 1–5. In my experience, 80% of analyst interactions will happen at Levels 1–3. The graph is the least-used view, but the one everyone demos. This is the classic "demo-driven design" trap.

> **R-VIZ-1** (P0): System must implement a 6-level progressive disclosure information hierarchy: (1) Alert notification with severity + entity count, (2) Ranked impact table with entity, score, confidence, direction, (3) Expandable causal chain view per entity with edge weights and relationship types, (4) Evidence panel with source articles and confidence breakdown, (5) Historical context with comparable past events and outcomes, (6) Interactive graph visualization. Levels 1–3 must be visible without any clicks from the alert.

> **R-VIZ-2** (P0): The default landing view after a propagation event must be a **ranked table**, not a graph. The table must show: rank, entity name, impact score (%), direction (↑↓), confidence (%), primary causal path (abbreviated), and time since detection. Sortable by any column. The graph view must be explicitly accessed via a "View Graph" action.

### B2. Graph Visualization Performance — 5K+ NODES IS A HARD PROBLEM

Force-directed layout (mentioned in R-OUT3 and Section 12.1: "D3.js force-directed or vis.js") has severe performance problems at 5,000+ nodes:

| Metric | 500 nodes | 5,000 nodes | 50,000 nodes |
|--------|-----------|-------------|--------------|
| D3.js force layout (CPU) | ~60fps | ~5fps | Unusable (<1fps) |
| vis.js (Canvas) | ~60fps | ~15fps | ~3fps |
| WebGL (deck.gl, Sigma.js) | ~60fps | ~60fps | ~30fps |
| Memory (100 edges/node avg) | ~20MB | ~200MB | ~2GB |
| Initial layout convergence | <1s | ~10s | ~2min |

D3.js and vis.js cannot render 5,000+ nodes interactively. This is a known limitation documented extensively. For MKG's stated scale, the visualization layer must use WebGL-based rendering (Sigma.js, Cosmos, or custom WebGL).

But performance isn't even the main problem — **information density** is. A 5,000-node force-directed graph looks like a ball of yarn. No analyst can extract insight from it. The visualization must implement:

- **Semantic zoom**: At full zoom-out, show clusters/sectors, not individual nodes. At mid-zoom, show company names in the focused sector. At full zoom, show edge labels, weights, and confidence.
- **Focus + context**: The event's impact zone is highlighted (focus), surrounding graph is dimmed (context). The impact zone is a subgraph of 20–100 nodes, not 5,000.
- **Level-of-detail rendering**: At any zoom level, render at most 200–300 visible nodes with full labels. Everything else is dots-and-lines.

> **R-VIZ-3** (P0): Graph visualization must use WebGL-based rendering (Sigma.js, GPU-accelerated deck.gl, or equivalent). D3.js SVG and vis.js Canvas are prohibited for the primary graph view at the stated scale (5K–50K nodes). Frame rate must be ≥30fps at 5,000 rendered nodes.

> **R-VIZ-4** (P0): Graph visualization must implement semantic zoom with at least 3 levels of detail: (a) macro (sector/cluster view — nodes are pie charts showing aggregate impact by sector), (b) entity (company-level with names, impact scores, and key edge weights visible), (c) detail (full node metadata, all edges, weight history, and source articles on hover/click).

> **R-VIZ-5** (P1): Graph visualization must implement "impact focus mode" — when triggered by a propagation event, the graph auto-focuses on the impact zone (entities within the propagation radius), dims non-impacted entities to 10% opacity, and arranges impacted entities in a hierarchical layout (trigger at center, hop-1 in ring 1, hop-2 in ring 2, etc.) rather than force-directed layout. Force-directed is for exploration; hierarchical radial is for event analysis.

### B3. Real-Time Update Strategy — "ANIMATION IS THE ENEMY"

R-OUT2 specifies WebSocket for real-time updates. But real-time updates + spatial visualization = chaos. At Bloomberg, we developed the "Stable Map" principle after extensive user research:

**The principle:** Users build a spatial mental model of a visualization. When nodes move (because the force-directed layout recalculates after an edge change), users lose their mental model and must rebuild it. This takes 5–15 seconds — longer than reading the update itself.

**The solution:** Real-time data updates must NEVER cause spatial (positional) changes in the graph layout. Instead:

1. **New edges**: Animate in (fade-in, 300ms) without moving existing nodes. New edge connects to existing node positions.
2. **Weight changes**: Update the visual encoding (edge thickness, color intensity) without moving anything.
3. **New nodes**: Place at a deterministic position (based on sector membership or entity type) without recalculating the force layout for existing nodes.
4. **Removed/decayed edges**: Fade out (300ms), do not remove from layout. Ghost edges remain as faint lines.

The layout should only recalculate when the user explicitly requests it (a "Relayout" button).

> **R-VIZ-6** (P0): Real-time graph updates via WebSocket must NOT trigger layout recalculation. New edges and weight changes must be animated in-place (fade-in, color transition) without moving existing nodes. Layout recalculation must only occur on explicit user action ("Relayout" button) or when the user navigates to the graph view for the first time after a batch of updates.

> **R-VIZ-7** (P1): System must implement a "change digest" panel adjacent to the graph showing real-time updates as a chronological list: "10:42:03 — New edge: TSMC → NVIDIA weight increased 0.72 → 0.88 (source: Reuters article #4521)". This gives the analyst a temporal narrative of changes without disrupting the spatial view.

### B4. Annotation and Collaboration — ANALYSTS DON'T JUST VIEW, THEY MARK UP

In every financial workflow I've designed, the analyst's interaction with data is not passive consumption — it's active markup. At Citadel, event-driven PMs:
- Highlight entities they have positions in
- Draw circles around "zones of interest"
- Add text notes to edges ("This alliance is weakening — spoke to IR yesterday")
- Tag entities for their watchlist
- Share a view with colleagues ("Look at this causal chain — what do you think?")

The MKG spec has no annotation capability. R-OUT3 says "interactive graph visualization" but "interactive" means only zoom/filter/select. True analyst interaction requires persistent annotations tied to the graph state.

> **R-VIZ-8** (P1): System must support user annotations on graph entities and edges: (a) text notes attached to nodes/edges, (b) visual highlighting (pin a node, change its color), (c) manual grouping (draw a boundary around N entities to create an ad-hoc cluster), (d) snapshot bookmarking with annotations preserved. Annotations are user-private by default with optional sharing.

> **R-VIZ-9** (P1): System must support "view sharing" — an analyst can capture the current graph view (layout, zoom level, focus, filters, annotations) as a shareable URL that another analyst can open and see the identical view. The shared state must be serialized (JSON-encoded view descriptor), not a screenshot.

### B5. The Core Analyst Workflow — MISSING ENTIRELY

The document doesn't define the primary user journey. Based on the buyer profiles (Section 7), I'll propose the two most common workflows:

**Workflow A — Reactive (Event-Driven PM)**
```
1. ALERT arrives (push notification / Telegram / WebSocket)
   → "TSMC: Fab disruption detected. 47 entities impacted."
2. PM opens MKG dashboard → sees ranked impact table (Level 2)
3. PM scans top 10 impacted entities → checks which overlap with portfolio
4. PM clicks on NVIDIA (highest portfolio exposure) → causal chain view (Level 3)
5. PM reads chain: TSMC → NVIDIA → N100 GPU supply at risk
6. PM checks evidence (Level 4): 3 Reuters articles, 1 TSMC press release
7. PM checks confidence: 89%, based on direct SUPPLIES_TO edge weight 0.91
8. PM decides: hedge NVIDIA position, increase ASML option position
9. PM annotates chain with trade decision for compliance log
10. PM closes alert. Total time: 2–5 minutes.
```

**Workflow B — Proactive (Research Analyst)**
```
1. Analyst opens MKG dashboard → "Explore" view
2. Searches "NVIDIA supply chain" → sees subgraph of 30 entities
3. Notices heavy concentration: 3 critical suppliers all in Taiwan
4. Opens "What-if" tool: simulates "Taiwan Strait blockade" scenario
5. Propagation runs: 120 entities impacted, top 10 are all mega-cap US tech
6. Analyst exports impact report (PDF) for morning note
7. Sets alert: "Notify me if any Taiwan-based supplier's risk score exceeds 0.8"
8. Total time: 15–30 minutes.
```

Neither workflow is documented or supported by the current requirements.

> **R-VIZ-10** (P0): System must explicitly design and implement two primary user workflows: (a) Reactive — from alert to trade decision in <5 minutes (alert → impact table → causal chain → evidence → decide), (b) Proactive — from exploration to insight in <30 minutes (search → subgraph → what-if → export → alert setup). Each workflow must be testable end-to-end with defined entry points, exit points, and maximum click counts per step.

### B6. Information Density Calibration — THE BLOOMBERG LESSON

The most common design mistake in financial UIs is either too dense (Bloomberg Terminal — 8-point font, no whitespace, 4,000 data points per screen) or too sparse (modern fintech apps — beautiful, empty, 6 data points per screen).

MKG serves both personas:
- **Time-pressured PM** (Workflow A): Needs maximum information density. Every pixel must convey signal. Prefers tables over graphs. Wants to see 20 entities at once with scores, directions, confidence, and primary chain — without scrolling.
- **Research analyst** (Workflow B): Needs moderate density with exploration tools. Prefers graphs for discovery. Wants to zoom in/out fluidly.

> **R-VIZ-11** (P1): System must support at least two density modes: (a) "Terminal" mode — maximum information density, tables preferred, minimal white space, keyboard-navigable, inspired by Bloomberg Terminal conventions (familiar to target users), (b) "Explorer" mode — moderate density, graph-centric, larger touch targets, more visual encoding of data (color, size, animation). The user must be able to switch modes with a single toggle. Both modes must display identical underlying data.

> **R-VIZ-12** (P1): The impact table (Level 2 view) must display a minimum of 20 entities simultaneously without scrolling on a 1920×1080 display. Each row must show: rank, entity name, ticker, sector, impact score (% with directional arrow), confidence (numerical + bar), primary causal path (abbreviated to 3 nodes max), and last updated timestamp. Total: 8 data fields per row × 20 rows = 160 data points visible at once.

### B7. Keyboard Navigation — NON-NEGOTIABLE FOR TRADERS

Bloomberg Terminal users navigate exclusively with keyboard shortcuts. Switching to a mouse is considered slow. Any tool targeting institutional finance users must support full keyboard navigation.

> **R-VIZ-13** (P0): System must support full keyboard navigation of the impact table and causal chain views. Minimum shortcuts: arrow keys to navigate rows/columns, Enter to expand causal chain, Escape to collapse, Tab to cycle between panels, number keys 1–6 for information hierarchy levels, `/` for search, `?` for shortcut reference. The graph view may require mouse for spatial interaction, but all non-graph views must be fully keyboard-accessible.

### B8. Color Design — ACCESSIBILITY AND CONVENTION

Financial UIs have strong color conventions that users expect. Violating them causes cognitive friction.

> **R-VIZ-14** (P1): Color encoding must follow financial conventions: (a) positive impact/gain: green (#00E676 or equivalent), (b) negative impact/loss: red (#FF5252 or equivalent), (c) neutral/unchanged: gray or amber, (d) confidence encoding: saturation intensity (high confidence = vivid, low confidence = washed out). The color palette must pass WCAG 2.1 AA contrast requirements against both dark and light backgrounds. Must include a deuteranopia-safe alternate palette (avoid red-green differentiation as sole encoding — always pair with shape or pattern).

---

## C. Requirement Challenges

### C1. Graph Visualization Technology Choice

The spec mentions "D3.js force-directed or vis.js" (Section 12.1). Neither can handle the stated scale:

| Library | Rendering | Max Interactive Nodes | MKG Scale Fit |
|---------|-----------|----------------------|---------------|
| D3.js (SVG) | SVG DOM | ~500 nodes | ❌ 10x below minimum |
| vis.js (Canvas) | Canvas 2D | ~2,000 nodes | ❌ 2.5x below minimum |
| Sigma.js 2.x (WebGL) | WebGL | ~50,000 nodes | ✅ |
| Cosmos (WebGL) | WebGL | ~1,000,000 nodes | ✅ (overkill but future-proof) |
| G6 (Canvas + WebGL) | Canvas/WebGL hybrid | ~10,000 nodes | ✅ |
| Gephi Lite (WebGL) | WebGL | ~100,000 nodes | ✅ |
| deck.gl (WebGL) | WebGL + GPU compute | ~1,000,000 nodes | ✅ (overkill) |

**Recommendation:** Sigma.js 2.x. It's purpose-built for large graph visualization in the browser, has WebGL rendering, supports semantic zoom, and has a mature plugin ecosystem (layout algorithms, search, export). It's the de facto standard for web-based graph UIs at financial scale.

### C2. The "What-If" Tool Can't Be Simple

R-OUT5 says "user inputs hypothetical event, sees projected impact." But designing a "What-if" input that is both powerful enough for analysts and constrained enough to produce reliable results is a significant UX challenge:

- What is the input format? Free text? ("What if TSMC has a fab fire") → Requires NLP to parse into a structured trigger event
- How does the user specify magnitude? Default? Slider?
- How does the user specify which entity is the trigger? Dropdown + autocomplete?
- How are results differentiated from real propagation results? (Must be visually distinct — "hypothetical" overlay)
- Can the user chain what-ifs? ("What if TSMC fab fire AND simultaneously EU sanctions on Chinese chips?")

This is a dedicated design project, not a single feature.

> **R-VIZ-15** (P1): "What-if" scenario tool must use structured input (not free text): (a) entity selector (autocomplete), (b) event type selector (disruption, regulatory, financial, partnership), (c) magnitude slider (minor/moderate/severe/catastrophic), (d) optional duration field. Results must be visually distinguished from real propagation results with a persistent "SIMULATED" banner and a distinct color palette (blue tint). What-if results must never be stored in the production graph or mixed with real signals.

---

## D. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Graph visualization becomes the demo centerpiece but is rarely used in production — engineering effort wasted on impressiveness over utility | HIGH | HIGH | R-VIZ-1, R-VIZ-2: Table-first design; graph is Level 6, not Level 1 |
| 2 | D3.js or vis.js chosen for graph rendering, hits performance wall at 5K nodes, requires costly rewrite | HIGH | HIGH | R-VIZ-3: Mandate WebGL from day 1 |
| 3 | Real-time graph updates cause "visual vertigo" — nodes shifting positions makes the UI adversarial to analysts | HIGH | MEDIUM | R-VIZ-6: Stable layout principle; no auto-relayout |
| 4 | No information hierarchy — the UI dumps everything on screen simultaneously, overwhelming time-pressured PMs | HIGH | HIGH | R-VIZ-1: 6-level progressive disclosure |
| 5 | No keyboard navigation — Bloomberg-native users reject the tool as amateur | MEDIUM | HIGH | R-VIZ-13: Full keyboard navigation for non-graph views |
| 6 | Color palette fails accessibility standards or contradicts financial conventions — cognitive friction for traders | MEDIUM | MEDIUM | R-VIZ-14: Convention-compliant, WCAG 2.1 AA, deuteranopia-safe |
| 7 | "What-if" tool accepts free-text input, produces unreliable results, users lose trust in the entire system | MEDIUM | HIGH | R-VIZ-15: Structured input only; no NLP parsing for scenarios |
| 8 | No analyst workflow designed — the UI is a feature collection, not a decision tool | HIGH | HIGH | R-VIZ-10: Two explicit workflows with defined steps and click budgets |

---

## E. Five Critical Questions

1. **What percentage of user time will be spent on the graph view vs the table view?** If the answer is "less than 20% on the graph" (which is my estimate based on Bloomberg Terminal usage analytics), then the graph visualization is a P2 feature, not P1 — and engineering time should be invested in making the impact table and causal chain views world-class instead. Do user research before committing to graph implementation.

2. **Can you ship without graph visualization?** The first 10 customers (event-driven PMs per Megan Torres's beachhead recommendation) need: alerts + ranked impact tables + causal chains + evidence. They don't need a graph — they need speed and accuracy. Could MKG v1 be table-only with graph as a v2 feature? This would save 3–4 months of engineering.

3. **How do you handle classification conflicts in visualization?** When an entity has contradictory signals (one source says TSMC supply relationship strengthening, another says weakening), how is this visualized? Dual-colored edges? Warning icons? A split-view? The current spec (R-EXP4) says "show both sides" but doesn't specify the visual language.

4. **What is the maximum number of causal chains a user can cognitively process?** If a propagation event produces 47 impacted entities, each with a 3–4 hop causal chain, that's 47 chain visualizations. No user will read all 47. What's the design constraint — show top 5 with full chains, show all 47 as one-line summaries, or paginate? This decision drives the entire Level 3 view design.

5. **Is the target user holding a Bloomberg Terminal open simultaneously?** If yes (likely for hedge fund PMs), MKG is a *companion tool*, not a replacement. This means MKG's UI should complement Bloomberg's conventions — same keyboard shortcuts where possible, same color conventions, dark theme mandatory. MKG should feel like a natural Bloomberg extension, not a foreign application. Has any Bloomberg UX compatibility audit been done?

---
---

# Cross-Expert Synthesis — Iterations 7 & 8

## Areas of Agreement

| Finding | Ethan Kowalski (Pipeline) | Yuki Tanaka (UX) | Implication |
|---------|---------------------------|-------------------|-------------|
| **The spec describes features, not architecture** | Pipeline has stages listed but no topology, error handling, or ordering guarantees | UI has "graph viz" listed but no information hierarchy, workflows, or density calibration | Both layers need design-first, not feature-list-first |
| **The happy path is specified; failure modes are ignored** | No DLQ, no fallback extraction, no source health tracking, no pipeline replay | No error states, no empty states, no degraded-mode visualization, no offline behavior | The system will appear broken under real-world conditions |
| **Cost is the hidden constraint that governs everything** | Claude API at $9K–$10K/month for 10K articles/day; $90K/month at 100K/day | WebGL graph rendering + real-time WebSocket updates require significant frontend engineering investment | Both layers must be designed with explicit cost ceilings |
| **The "demo" and the "product" are different things** | The happy-path pipeline (100 articles, no failures, Claude always available) demos well but isn't production-ready | The graph visualization demos beautifully but analysts spend 80% of time in tables | Risk of building a great demo that nobody uses in production |

## Areas of Divergence

| Topic | Ethan Kowalski | Yuki Tanaka | Resolution |
|-------|----------------|-------------|------------|
| **Priority of real-time updates** | WebSocket for pipeline status is P1 — batch metrics are more useful than streaming | WebSocket for graph updates is dangerous — causes visual vertigo | Both agree: batch > stream for most use cases. Real-time only for alert delivery. |
| **Celery viability** | Phase 1 yes, production no — must migrate to durable broker | No opinion on backend — cares about data freshness guarantees to the UI | Pipeline abstraction (R-PIPE-19) enables migration without UI rewrite |
| **Graph visualization priority** | No opinion — outside domain | P2, not P1 — table-first design, graph for exploration only | Controversial — contradicts R-OUT3 (P1). Recommend user research to settle. |
| **Biggest risk** | Silent data loss during pipeline failures — the graph has invisible holes | Building an impressive demo that nobody uses for actual decisions | Both existential — one is data integrity, the other is product-market fit |

## Cumulative Gap Summary (Iterations 1–8)

| Gap | First Identified | Impact | Status |
|-----|-----------------|--------|--------|
| Portfolio overlay missing | Iteration 1 (Marcus) | SHOW-STOPPER for financial vertical | Needs R-PORT1–R-PORT3, but may trigger IA registration (Iteration 6) |
| BOM-level granularity missing | Iteration 2 (Priya) | SHOW-STOPPER for supply chain vertical | Deprioritized if financial markets = beachhead (Iteration 5) |
| Cross-domain data isolation | Iterations 2, 5, 6 | CRITICAL — regulatory + information barrier | R-SEC-11, R-SEC-12, R-SEC-13: provable isolation required |
| SOM overstated 10–50x | Iterations 1, 2, 5 | Business planning error | Consensus: $50K–$150K Year 1 |
| 24-week plan = demo only | Iterations 1, 2, 5 | Expectation management | First revenue at week 52+ |
| Neo4j CE limitations | Iteration 3 (Kai) | ARCHITECTURAL — 5+ requirements undeliverable | R-GRAPH-1: edition decision |
| Temporal versioning unspecified | Iteration 3 (Kai) | ARCHITECTURAL — 3–6 month project | R-GRAPH-2 |
| Decimal precision impossible | Iteration 3 (Kai) | DATA INTEGRITY | R-GRAPH-5 |
| NER/RE accuracy targets missing | Iteration 4 (Aisha) | QUALITY — no measurement = no improvement | R-NLP-1, R-NLP-3 |
| LLM hallucination 8–15% | Iteration 4 (Aisha) | INTEGRITY — poisoned graph | R-NLP-8, R-NLP-9, R-NLP-10 |
| 13-language NER = multi-year | Iteration 4 (Aisha) | SCOPE — blocks launch | R-NLP-13: phase English-first |
| NLP costs ~$10K/month | Iteration 4 (Aisha) | FINANCIAL — unbudgeted | R-NLP-11 |
| No evaluation infrastructure | Iteration 4 (Aisha) | OPERATIONAL | R-NLP-15 |
| No beachhead vertical selected | Iteration 5 (Megan) | STRATEGIC — dual-vertical kills focus | R-PM-1: pick one |
| No GTM strategy | Iteration 5 (Megan) | EXISTENTIAL — no sales = no revenue | R-PM-9: define sales motion |
| No MVP defined | Iteration 5 (Megan) | SCOPE — 150 requirements ≠ MVP | R-PM-5: max 20 MVP requirements |
| No pricing validation | Iteration 5 (Megan) | FINANCIAL — pricing range meaningless | R-PM-6: define value metric |
| SOC 2 / pentest missing | Iteration 6 (James) | PROCUREMENT GATE — blocks all institutional sales | R-SEC-8, R-SEC-9 |
| SSO/SAML missing | Iteration 6 (James) | PROCUREMENT GATE — hard stop | R-SEC-29 |
| Information barriers not implemented | Iteration 6 (James) | REGULATORY — MNPI / insider trading risk | R-SEC-12, R-SEC-20 |
| Investment adviser classification unresolved | Iteration 6 (James) | REGULATORY SHOWSTOPPER | R-SEC-18: legal opinion required |
| LLM data leakage to Anthropic | Iteration 6 (James) | TRUST — institutional clients block Claude API | R-SEC-14, R-SEC-15, R-SEC-16 |
| GDPR non-compliance for Person entities | Iteration 6 (James) | REGULATORY — €20M fine exposure | R-SEC-21, R-SEC-22 |
| OFAC/sanctions compliance missing | Iteration 6 (James) | LEGAL — potential criminal exposure | R-SEC-27 |
| No incident response or DR plan | Iteration 6 (James) | OPERATIONAL — unacceptable for 24/7 system | R-SEC-35, R-SEC-36 |
| **No pipeline topology or failure semantics** | **Iteration 7 (Ethan)** | **ARCHITECTURAL — pipeline is specified as stages, not as a system** | **R-PIPE-1, R-PIPE-2** |
| **At-most-once delivery: articles can be lost** | **Iteration 7 (Ethan)** | **DATA INTEGRITY — silent signal loss** | **R-PIPE-3, R-PIPE-4** |
| **No DLQ: failed extractions vanish** | **Iteration 7 (Ethan)** | **OPERATIONAL — invisible pipeline holes** | **R-PIPE-9** |
| **No pipeline observability defined** | **Iteration 7 (Ethan)** | **OPERATIONAL — can't detect failures** | **R-PIPE-10: 15+ metrics** |
| **Claude API as bottleneck unaddressed** | **Iteration 7 (Ethan)** | **COST + RELIABILITY — $10K/month, single point of failure** | **R-PIPE-6, R-PIPE-7, R-PIPE-14** |
| **No backpressure mechanism** | **Iteration 7 (Ethan)** | **RELIABILITY — burst traffic causes OOM/cascade** | **R-PIPE-11, R-PIPE-12** |
| **No durable article storage** | **Iteration 7 (Ethan)** | **AUDIT + REPLAY — can't prove or reproduce extractions** | **R-PIPE-18** |
| **Source feeds treated as static** | **Iteration 7 (Ethan)** | **OPERATIONAL — sources break monthly** | **R-PIPE-16, R-PIPE-17** |
| **No information hierarchy in UI** | **Iteration 8 (Yuki)** | **UX — analyst overwhelmed, can't find what matters** | **R-VIZ-1, R-VIZ-2** |
| **Graph viz tech (D3/vis.js) can't handle 5K nodes** | **Iteration 8 (Yuki)** | **PERFORMANCE — UI unusable at stated scale** | **R-VIZ-3: mandate WebGL** |
| **No user workflow defined** | **Iteration 8 (Yuki)** | **UX — feature collection, not decision tool** | **R-VIZ-10: two explicit workflows** |
| **Real-time graph updates cause visual vertigo** | **Iteration 8 (Yuki)** | **UX — adversarial visualization** | **R-VIZ-6: stable layout principle** |
| **No keyboard navigation** | **Iteration 8 (Yuki)** | **UX — rejected by Bloomberg-native users** | **R-VIZ-13** |

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
| **Total** | | **145** | **80** |

## Top 9 Cumulative Risks (Updated from all 8 experts)

1. **The product fails commercially because there is no go-to-market strategy.** Technology without distribution is a hobby project. No beachhead vertical selected, no sales motion defined, no pipeline targets, no customer success infrastructure. *(Iteration 5, corroborated by 7 and 8)*

2. **Cross-tenant data leakage creates legal liability.** Property-level isolation on a single Neo4j instance is one missing WHERE clause from disaster. *(Iterations 2, 3, 6)*

3. **Investment adviser classification as a regulatory showstopper.** If MKG provides personalized portfolio-specific alerts, it may be an unregistered investment adviser — a federal crime. *(Iteration 6)*

4. **Institutional buyers cannot procure without SOC 2, SSO, and penetration test.** Non-negotiable procurement gates. Without them, every sales process terminates at the security questionnaire. *(Iteration 6)*

5. **The NLP pipeline produces confident wrong answers.** 8–15% relation hallucination + 25–35% RE error rate = a graph with substantial incorrect edges. 4-hop all-correct probability ~24%. *(Iteration 4, corroborated by 7)*

6. **The data pipeline silently loses articles and has no recovery mechanism.** At-most-once delivery with Celery + Redis, no DLQ, no article storage, no pipeline replay. The graph will have invisible holes that nobody can detect or repair. *(NEW — Iteration 7)*

7. **Costs are fatally underspecified.** Infrastructure: $186K+/year. Compliance: $95K–$220K. Sales: $150K–$250K. Claude API: $108K–$120K/year for 10K articles/day. **Total Year 1 burn: $600K–$900K.** *(Cumulative — Iterations 3, 4, 5, 6, 7)*

8. **The UI is designed around a demo (graph visualization), not around the analyst workflow (ranked tables + causal chains).** 80% of usage will be in Levels 1–3 (alerts, tables, chains), but engineering effort gravitates toward the impressive Level 6 (graph). *(NEW — Iteration 8)*

9. **The 24-week timeline does not produce a sellable product.** Week 24 = demo. Week 48 = security-ready. Week 84–108 = first revenue. That's 20–26 months from start to first dollar. *(Cumulative — Iterations 1, 2, 5, 6)*

---

## Recommended Priority Actions (Updated — Cumulative from all 8 experts)

### TIER 1 — Do Before Writing Any Code

1. **GET LEGAL OPINION: Investment adviser classification** — If the answer is "you must register," the product design, cost structure, and timeline change fundamentally. *(R-SEC-18)*

2. **PICK BEACHHEAD: Financial markets, event-driven fund persona** — One persona. One vertical. One value proposition validated through 20 discovery calls. *(R-PM-1, R-PM-2)*

3. **VALIDATE BUYER WILLINGNESS TO PAY** — 20 discovery calls with event-driven fund PMs. *(R-PM-6)*

4. **START SOC 2 PROCESS** — Compliance automation on day 1. *(R-SEC-8)*

5. **DESIGN USER WORKFLOWS BEFORE UI** — Define the two primary workflows (reactive PM, proactive analyst) with click budgets and step counts. Validate with 5 target users. Build UI to support workflows, not features. *(R-VIZ-10)*

### TIER 2 — Decide Before Building Architecture

6. **DECIDE: Neo4j edition** — CE vs Enterprise vs alternative. *(R-GRAPH-1)*

7. **DECIDE: Data isolation architecture** — Separate instances per client, or never store client data in the shared graph. *(R-SEC-11)*

8. **DECIDE: Self-hosted LLM as primary mode** — If institutional clients prohibit Claude API, Ollama is not a fallback — it's the default. *(R-SEC-16)*

9. **DEFINE: MVP feature set** — Maximum 20 requirements. *(R-PM-5)*

10. **DESIGN: Pipeline topology with failure semantics** — Define every stage, its input/output, failure mode, retry policy, and observability metrics *before* writing the first Celery task. *(R-PIPE-1, R-PIPE-2)*

11. **DECIDE: Graph visualization technology** — WebGL mandatory (Sigma.js recommended). Document the choice with performance benchmarks at 5K and 50K nodes. *(R-VIZ-3)*

### TIER 3 — Build During Phase 1

12. **IMPLEMENT: SSO/SAML** — Must ship with the MVP. *(R-SEC-29, R-SEC-30)*

13. **IMPLEMENT: NER/RE accuracy benchmarks** — Define F1 targets, create evaluation dataset, build accuracy dashboard. *(R-NLP-1, R-NLP-3, R-NLP-15)*

14. **IMPLEMENT: Hallucination defense** — Span verification + evidence sentences + multi-source corroboration. *(R-NLP-8, R-NLP-9)*

15. **IMPLEMENT: Pipeline DLQ + observability** — Dead-letter queue for every stage, 15+ defined pipeline metrics, pipeline health dashboard. *(R-PIPE-9, R-PIPE-10)*

16. **IMPLEMENT: Durable article storage** — All ingested articles stored with 2-year retention for audit, replay, and evaluation. *(R-PIPE-18)*

17. **IMPLEMENT: Claude API cost governance** — Real-time spend tracking, daily/monthly caps, automatic fallback to rule-based extraction. *(R-PIPE-14)*

18. **IMPLEMENT: Table-first information hierarchy** — Levels 1–3 (alert → impact table → causal chain) before any graph visualization work. *(R-VIZ-1, R-VIZ-2)*

19. **BUDGET: Acknowledge Year 1 costs** — Infrastructure ($186K) + compliance ($150K) + sales ($200K) + legal ($50K) + Claude API ($108K) = **$694K+ minimum** + founder salary. Plan fundraising accordingly. *(Cumulative)*

---

*Next iteration: Experts 9 & 10 — to be determined based on remaining gap priorities.*
