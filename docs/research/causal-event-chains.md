# Causal Event-Chain Intelligence: Research Review & System Design

> **Feature**: Neural Trader — Causal Event-Chain Mapping for Signal Generation  
> **Author**: Quantitative Research Review  
> **Date**: 24 March 2026  
> **Status**: DRAFT — Brainstorm / Research Phase  
> **Scope**: Enhancement to SignalFlow AI's sentiment pipeline  

---

## Executive Summary

SignalFlow's current AI pipeline reduces news to a single scalar — `sentiment_score ∈ [0,100]` — discarding the **causal structure** of how events propagate through markets. A repo rate decision doesn't just have "sentiment"; it cascades: RBI holds rate → bank NIMs stable → credit growth continues → HDFCBANK/ICICIBANK bullish. This document proposes an **Event-Chain Intelligence (ECI)** layer that extracts, stores, and scores structured causal pathways from news, producing richer features for signal generation.

The key constraint is a **$30/month Claude API budget** (~$1/day, approximately 100-150 sentiment-class calls/day at current token usage). The design must be ruthlessly efficient — extracting maximum causal structure per API call.

---

## Table of Contents

1. [Knowledge Graph Design](#1-knowledge-graph-design)
2. [Causal Inference](#2-causal-inference)
3. [NLP Pipeline Design](#3-nlp-pipeline-design)
4. [Temporal Modeling](#4-temporal-modeling)
5. [Feature Engineering](#5-feature-engineering)
6. [Budget-Efficient AI](#6-budget-efficient-ai)
7. [Data Model](#7-data-model)
8. [Evaluation Framework](#8-evaluation-framework)
9. [Scalability Concerns](#9-scalability-concerns)
10. [Concrete Algorithm](#10-concrete-algorithm)

---

## 1. Knowledge Graph Design

### 1.1 Node Taxonomy

The event-impact graph requires four node types, each with distinct attributes:

| Node Type | Description | Key Attributes | Examples |
|-----------|-------------|----------------|----------|
| **Event** | A discrete real-world occurrence | `timestamp`, `source`, `confidence`, `magnitude` | "RBI holds repo at 6.5%", "Panama Canal drought" |
| **Entity** | A tradeable instrument or organization | `symbol`, `market_type`, `sector`, `geography` | HDFCBANK.NS, BTCUSDT, EUR/USD |
| **Sector** | An industry grouping | `name`, `geography`, `market_type` | Indian Banking, Global Shipping, US Tech |
| **MacroFactor** | A persistent economic condition | `name`, `current_state`, `trend` | Interest Rates, Inflation, USD Strength |

### 1.2 Edge Taxonomy

Edges encode the **type and strength** of relationships:

| Edge Type | Semantics | Attributes | Example |
|-----------|-----------|------------|---------|
| **CAUSES** | Direct causal relationship | `confidence ∈ [0,1]`, `lag_hours`, `mechanism` | "RBI holds rate" →(CAUSES)→ "Bank margins stable" |
| **AFFECTS** | Impact on tradeable entity | `direction ∈ {bullish, bearish, neutral}`, `magnitude ∈ [0,1]`, `time_horizon` | "Bank margins stable" →(AFFECTS,bullish,0.7)→ HDFCBANK |
| **BELONGS_TO** | Entity-sector membership | `weight` (for multi-sector entities) | HDFCBANK →(BELONGS_TO)→ Indian Banking |
| **CORRELATES** | Statistical co-movement (not causal) | `correlation`, `lookback_period` | BTCUSDT ←(CORRELATES,0.85)→ ETHUSDT |
| **PRECEDES** | Temporal ordering without confirmed causation | `time_delta` | "Fed signals pause" →(PRECEDES)→ "USD weakens" |

### 1.3 Graph Structure

Event chains form **directed acyclic subgraphs** (DAGs) within a larger knowledge graph. A single news event can trigger multiple parallel chains:

```
Event: "RBI holds repo rate at 6.5%"
  ├──CAUSES──► "Bank lending margins stable"
  │               ├──AFFECTS(bullish,0.8)──► HDFCBANK.NS
  │               ├──AFFECTS(bullish,0.7)──► ICICIBANK.NS
  │               └──AFFECTS(bullish,0.6)──► SBIN.NS
  ├──CAUSES──► "Home loan rates unchanged"
  │               └──AFFECTS(bullish,0.4)──► Real Estate Sector
  └──CAUSES──► "Rupee stability supported"
                  └──AFFECTS(neutral→bullish,0.3)──► USD/INR
```

### 1.4 Graph Storage Recommendation

**For SignalFlow's scale (31 symbols, ~100 events/day), a full graph database is overkill.** Recommended approach:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **PostgreSQL + JSONB** (adjacency list) | Already in stack, ACID, joins with market_data | No native traversal | **Recommended** — sufficient for depth-3 chains |
| NetworkX (in-memory) | Fast traversal, pure Python | No persistence, memory-bound | Good for real-time chain scoring |
| Neo4j | Native graph, Cypher queries | New infra, overkill at this scale | Not recommended for MVP |
| SQLite + recursive CTEs | Lightweight, portable | Performance at scale | Alternative for dev/testing |

**Hybrid approach**: Store events and edges in PostgreSQL for persistence. Load active chains (last 7 days) into a NetworkX `DiGraph` on worker startup for fast traversal and scoring. This gives us relational integrity for storage and graph algorithms for scoring.

### 1.5 Academic References

- Ding et al. (2015) — "Deep Learning for Event-Driven Stock Prediction" — established the event→embedding→prediction pipeline
- Deng et al. (2019) — Knowledge-Driven Stock Trend Prediction framework; demonstrated that explicit knowledge graph relations improve prediction over bag-of-words sentiment by 8-12% directional accuracy
- Veličković et al. (2018) — Graph Attention Networks (GAT), relevant if we later move to learned edge weights

---

## 2. Causal Inference

### 2.1 The Fundamental Problem

News-based causal inference in finance faces a core epistemological challenge: **we observe correlations in co-temporal news and price movements, but causal identification requires counterfactual reasoning** ("what would the price have been without this event?").

For SignalFlow, we don't need academic-grade causal identification. We need **plausible causal narratives** that:
1. A finance professional (M.Com) would recognize as reasonable
2. Outperform a flat sentiment score in directional prediction
3. Can be extracted cheaply from Claude API calls

### 2.2 Causal Confidence Scoring

Assign a confidence score $c \in [0, 1]$ to each causal edge using a multi-factor rubric:

$$c_{\text{edge}} = w_1 \cdot f_{\text{mechanism}} + w_2 \cdot f_{\text{temporal}} + w_3 \cdot f_{\text{historical}} + w_4 \cdot f_{\text{consensus}}$$

Where:
- $f_{\text{mechanism}} \in [0,1]$: Is there a clear economic mechanism? (e.g., "rate cut → cheaper borrowing → more lending" has a clear mechanism; "CEO tweeted → stock moved" is weaker)
- $f_{\text{temporal}} \in [0,1]$: Does the temporal ordering make sense? Cause must precede effect. Penalize if timestamps are ambiguous.
- $f_{\text{historical}} \in [0,1]$: Has this causal pattern been observed before? A "rate hold → bank bullish" link that has fired 5 times with 4 correct outcomes gets $f_{\text{historical}} = 0.8$.
- $f_{\text{consensus}} \in [0,1]$: Do multiple news sources report the same causal pathway? Single-source chains get lower confidence.

**Recommended weights**: $w = [0.35, 0.20, 0.30, 0.15]$ — mechanism and historical evidence dominate.

### 2.3 Techniques from Causal Inference Literature

| Technique | Applicability to SignalFlow | Feasibility |
|-----------|----------------------------|-------------|
| **Granger Causality** | Test if lagged event occurrences predict price movements of specific symbols | High — can be computed offline on historical data |
| **Propensity Score Matching** | Compare stock behavior on days with/without specific event types | Medium — needs sufficient event history |
| **Difference-in-Differences** | Compare affected vs. unaffected stocks around sector-level events | Medium — natural for sector events (e.g., RBI decision affects banks vs. IT) |
| **Instrumental Variables** | Exogenous shocks as instruments (e.g., weather events for agriculture) | Low — hard to find valid instruments for most events |
| **Do-Calculus (Pearl)** | Full causal identification from observational data | Low — requires known DAG; our DAG *is* the thing we're estimating |

**Practical recommendation**: Start with **Granger causality tests** on historical event→price data to validate chain templates. Use a significance threshold of $p < 0.05$ with Holm-Bonferroni correction for multiple testing across 31 symbols.

### 2.4 Chain Validation via Backtesting

Every causal chain template (e.g., "RBI rate decision → bank stock impact") should accumulate a **track record**:

```
ChainTemplate: "central_bank_rate_hold → banking_sector_bullish"
  Historical occurrences: 12
  Correct direction: 9 (75%)
  Avg magnitude when correct: +1.8%
  Avg magnitude when wrong: -0.6%
  Confidence: 0.75
  Last updated: 2026-03-20
```

This historical evidence feeds back into $f_{\text{historical}}$ in the confidence formula.

---

## 3. NLP Pipeline Design

### 3.1 Current Pipeline Limitations

The existing Claude call structure in [prompts.py](../../../backend/app/services/ai_engine/prompts.py):

```python
# Current: 10 article headlines → single sentiment score
SENTIMENT_PROMPT → {"sentiment_score": 72, "key_factors": [...]}
```

**Information loss**: The current prompt asks Claude to *compress* 10 articles into one number. The causal chain between events and market impacts is lost. A single article about RBI policy and a separate article about banking NPAs produce the same output structure as two unrelated articles.

### 3.2 Proposed Two-Stage Pipeline

**Stage 1: Event Extraction + Chain Building** (replaces current sentiment call)

```
Input:  10 article headlines for HDFCBANK.NS
Output: Structured event-chain JSON
Cost:   ~500 input tokens + ~800 output tokens ≈ $0.0135/call
```

**Stage 2: Chain-Aware Signal Scoring** (new, lightweight)

```
Input:  Extracted chains + technical data (pre-formatted)
Output: Directional assessment with chain-backed reasoning
Cost:   ~300 input tokens + ~200 output tokens ≈ $0.004/call
```

### 3.3 Event Extraction Prompt (Stage 1)

```python
EVENT_CHAIN_PROMPT = """You are a financial event analyst. Extract causal event chains
from these news articles about {symbol} ({market_type}).

Articles:
{articles_text}

For each distinct event, trace its causal chain to market impact.

Respond ONLY with valid JSON (no markdown):
{{
  "events": [
    {{
      "id": "evt_1",
      "description": "<concise event description, max 15 words>",
      "category": "<macro_policy|earnings|sector|geopolitical|regulatory|technical|commodity>",
      "source_articles": [0, 2],
      "timestamp_approx": "<ISO date or 'recent'>",
      "chain": [
        {{
          "step": 1,
          "effect": "<intermediate effect, max 15 words>",
          "mechanism": "<economic mechanism, max 10 words>",
          "confidence": <0.0-1.0>
        }},
        {{
          "step": 2,
          "effect": "<next-order effect>",
          "mechanism": "<mechanism>",
          "confidence": <0.0-1.0>
        }}
      ],
      "affected_symbols": [
        {{
          "symbol": "{symbol}",
          "direction": "<bullish|bearish|neutral>",
          "magnitude": <0.0-1.0>,
          "time_horizon": "<hours|days|weeks|months>"
        }}
      ],
      "affected_sectors": ["<sector_name>"]
    }}
  ],
  "cross_event_interactions": [
    {{
      "events": ["evt_1", "evt_2"],
      "interaction": "<reinforcing|conflicting|independent>",
      "net_effect": "<description of combined effect>"
    }}
  ],
  "overall_direction": "<bullish|bearish|neutral>",
  "overall_confidence": <0.0-1.0>
}}"""
```

### 3.4 Why Structured JSON Extraction Works

Claude excels at structured extraction when:
1. **Schema is explicit** — the JSON template above is unambiguous
2. **Constraints are tight** — "max 15 words" prevents verbose outputs (saves tokens)
3. **Categories are finite** — 7 event categories guide extraction
4. **Confidence is requested** — Claude provides well-calibrated confidence when asked directly (Kadavath et al., 2022 — "Language Models (Mostly) Know What They Know")

### 3.5 Prompt Engineering Patterns for Causal Extraction

| Pattern | Description | Application |
|---------|-------------|-------------|
| **Chain-of-Thought** | Ask Claude to reason step-by-step through causal chain | Built into the `chain[].step` structure — each step forces explicit intermediate reasoning |
| **Constrained Generation** | Tight JSON schema with enumerated options | `direction ∈ {bullish, bearish, neutral}`, `category ∈ {7 options}` |
| **Few-Shot Anchoring** | Provide 1-2 examples in system prompt | Include one canonical example (RBI rate decision) to calibrate output format |
| **Decomposition** | Break complex task into subtasks | Stage 1 (extraction) + Stage 2 (scoring) rather than one monolithic prompt |
| **Self-Consistency** | Run same prompt N times, take majority | Not budget-feasible; instead, use `confidence` fields as self-assessed reliability |

### 3.6 Cross-Symbol Chain Detection

A key advantage of event chains: **one article can affect multiple symbols**. Currently, SignalFlow runs sentiment independently for each of 31 symbols. With event chains:

- Article about "RBI rate decision" is fetched for HDFCBANK
- Chain extraction identifies impact on ICICIBANK, SBIN, KOTAKBANK, USD/INR
- These chains are **propagated** to other symbols without additional Claude calls

This is a major budget efficiency gain. See Section 6.

---

## 4. Temporal Modeling

### 4.1 Event Impact Decay

Market impact of news events is not instantaneous — it follows a **decaying impulse response**. Empirical studies (Tetlock, 2007; Loughran & McDonald, 2011) show that news impact on price follows roughly exponential decay:

$$I(t) = I_0 \cdot e^{-\lambda t}$$

Where:
- $I_0$ = initial impact magnitude
- $\lambda$ = decay rate (event-type dependent)
- $t$ = time since event (hours)

### 4.2 Decay Constants by Event Category

Based on financial literature and empirical observation:

| Event Category | Half-life ($t_{1/2}$) | Decay Rate ($\lambda = \ln 2 / t_{1/2}$) | Rationale |
|----------------|----------------------|-------------------------------------------|-----------|
| Earnings/Results | 48–72 hours | 0.0096–0.0144 | Price adjusts within 2-3 trading sessions |
| Macro Policy (RBI, Fed) | 1–2 weeks | 0.0021–0.0041 | Gradual repricing of rate-sensitive assets |
| Geopolitical | 24–48 hours | 0.0144–0.0289 | Fast spike, rapid mean-reversion unless escalation |
| Regulatory | 2–4 weeks | 0.0010–0.0021 | Slow compliance impact, structural changes |
| Commodity Shock | 1–3 weeks | 0.0014–0.0041 | Supply chain propagation takes time |
| Technical/Crypto Event | 6–24 hours | 0.0289–0.1155 | Fast-moving markets, rapid info incorporation |
| Sector Rotation | 2–6 weeks | 0.0008–0.0021 | Slow institutional repositioning |

### 4.3 Multi-Order Effect Timing

First, second, and third-order effects in a causal chain have **compounding delays**:

```
Event: "Global oil prices spike +15%"
  ├── 1st order (hours):    Oil & gas stocks rally, airline stocks drop
  ├── 2nd order (days):     Input cost inflation fears → broader market caution
  └── 3rd order (weeks):    Central bank response speculation → rate-sensitive repricing
```

Model this as a **cascaded delay**:

$$I_{\text{chain}}(t) = \sum_{k=1}^{K} I_k \cdot e^{-\lambda_k (t - \tau_k)}$$

Where:
- $K$ = number of steps in chain
- $\tau_k$ = onset delay for step $k$ (cumulative)
- $I_k$ = magnitude of step $k$
- $\lambda_k$ = decay rate of step $k$

For a 3-step chain with $\tau = [0, 24, 168]$ hours:
- Step 1 fires immediately with fast decay
- Step 2 activates after ~1 day with medium decay
- Step 3 activates after ~1 week with slow decay

### 4.4 Practical Implementation

Store per-chain timing parameters and compute the **current active impact** at any moment:

```python
def chain_impact_at_time(chain: EventChain, now: datetime) -> float:
    """Compute net directional impact of a chain at current time."""
    total_impact = 0.0
    for step in chain.steps:
        hours_since_onset = (now - step.onset_time).total_seconds() / 3600
        if hours_since_onset < 0:
            continue  # step hasn't activated yet
        decay = math.exp(-step.decay_rate * hours_since_onset)
        step_impact = step.magnitude * step.direction_sign * decay
        total_impact += step_impact
    return total_impact
```

### 4.5 Half-Life Estimation from Data

After accumulating ~3 months of event-chain data with market outcomes, **estimate empirical half-lives** by:

1. Group resolved chains by event category
2. For each group, fit $I(t) = I_0 \cdot e^{-\lambda t}$ to observed price impact curves
3. Update the decay constants table quarterly

This creates a **feedback loop** where the temporal model self-calibrates.

---

## 5. Feature Engineering

### 5.1 Features Extractable from Event Chains

For each symbol at scoring time, compute these features from the active event graph:

| Feature | Type | Description | Computation |
|---------|------|-------------|-------------|
| `chain_net_direction` | float ∈ [-1, 1] | Net bullish/bearish pressure from all active chains | $\sum_i I_i(t) \cdot d_i$ where $d_i \in \{-1, +1\}$ |
| `chain_confidence` | float ∈ [0, 1] | Confidence-weighted average of chain confidences | $\bar{c} = \frac{\sum c_i \cdot |I_i(t)|}{\sum |I_i(t)|}$ |
| `chain_count` | int | Number of active chains affecting this symbol | Simple count |
| `chain_consensus` | float ∈ [0, 1] | Agreement between chains (1 = all same direction) | $1 - H(p_{\text{bull}}, p_{\text{bear}}) / \log 2$ where $H$ is entropy |
| `chain_max_magnitude` | float ∈ [0, 1] | Strongest single chain's current impact | $\max_i |I_i(t)|$ |
| `chain_depth_weighted` | float | Higher-order effects signal stronger macro driver | $\sum_i K_i \cdot |I_i(t)|$ where $K_i$ = chain depth |
| `cross_symbol_momentum` | float ∈ [-1, 1] | Average chain direction across related symbols | Mean direction of chains shared with correlated symbols |
| `event_novelty` | float ∈ [0, 1] | How unprecedented is this event pattern? | $1 - \text{sim}(\text{event}, \text{historical\_events})$ |
| `chain_recency` | float ∈ [0, 1] | Freshness of the most impactful chain | $e^{-\lambda \cdot t_{\text{newest}}}$ |

### 5.2 Integration with Existing Scoring

Current formula:

$$\text{final\_confidence} = \text{tech\_score} \times 0.60 + \text{sentiment\_score} \times 0.40$$

**Proposed evolution** — replace flat sentiment with chain-aware scoring:

$$\text{final\_confidence} = \text{tech\_score} \times 0.50 + \text{chain\_score} \times 0.35 + \text{sentiment\_residual} \times 0.15$$

Where:
- **tech_score** (0.50): Slightly reduced from 0.60 to make room for richer AI features — but technical analysis remains dominant as it's the most reliable short-term signal
- **chain_score** (0.35): Derived from chain features above, maps to [0, 100]
- **sentiment_residual** (0.15): The "mood" component not captured by explicit chains — overall market tone, fear/greed index behavior

### 5.3 Chain Score Computation

$$\text{chain\_score} = 50 + 50 \times \tanh\left(\alpha \cdot \text{chain\_net\_direction} \cdot \text{chain\_confidence} \cdot \text{chain\_consensus}\right)$$

The $\tanh$ squashes the output to $[0, 100]$ centered at 50 (neutral). The parameter $\alpha$ controls sensitivity — start with $\alpha = 2.0$ and tune via backtest.

### 5.4 Feature Interaction Effects

Some chain features should interact with technical indicators:

- **Chain direction + RSI divergence**: If chains are bullish but RSI is overbought (>70), this is a *conflicting signal* — reduce chain weight by 50%
- **Chain consensus + Volume**: High chain consensus + high volume = confirmation; high consensus + low volume = skepticism
- **Chain depth + SMA crossover**: Deep chains (3+ steps) affecting macro factors should increase the timeframe of the signal (shift from "days" to "weeks")

These interactions are best modeled as multiplicative terms rather than adding more complexity to the linear scoring formula.

---

## 6. Budget-Efficient AI

### 6.1 Current Budget Analysis

With the current pipeline:

| Call Type | Tokens (in/out) | Cost/call | Calls/day | Daily Cost | Monthly Cost |
|-----------|-----------------|-----------|-----------|------------|--------------|
| Sentiment (31 symbols × 1/hr for active markets) | ~400/200 | $0.0042 | ~150 | $0.63 | $18.90 |
| Signal Reasoning (per signal generated) | ~500/200 | $0.0045 | ~30 | $0.14 | $4.05 |
| Morning Brief | ~800/400 | $0.0084 | 1 | $0.008 | $0.25 |
| Evening Wrap | ~800/400 | $0.0084 | 1 | $0.008 | $0.25 |
| AI Q&A (on demand) | ~600/300 | $0.0063 | ~5 | $0.03 | $0.95 |
| **Total** | | | | **~$0.82** | **~$24.40** |

**Remaining headroom**: ~$5.60/month for event-chain extraction.

### 6.2 Budget Allocation Strategy

**Key insight**: Replace sentiment calls with event-chain calls (not add them alongside). Event chains produce a *superset* of sentiment information.

| Call Type | New Approach | Tokens (in/out) | Cost/call | Calls/day | Monthly |
|-----------|-------------|-----------------|-----------|-----------|---------|
| **Event-Chain Extraction** (replaces sentiment) | Batch 3-5 symbols per call when they share news | ~600/800 | $0.0138 | ~60 | $24.84 |
| Signal Reasoning (with chain context) | Include chain summary in prompt | ~400/200 | $0.0045 | ~30 | $4.05 |
| Briefs + Q&A | Unchanged | — | — | — | $1.45 |
| **Total** | | | | | **~$30.34** |

This is tight but feasible. The key optimization: **batch symbols that share news events into a single extraction call**.

### 6.3 What Should Run Locally vs. API

| Task | Local or API | Rationale |
|------|-------------|-----------|
| **News deduplication** | Local | String similarity (Jaccard, cosine on TF-IDF) is trivial |
| **Event deduplication** | Local | Compare extracted event descriptions with cached events via embedding similarity |
| **Chain propagation** | Local | Graph traversal on NetworkX — purely algorithmic |
| **Impact decay computation** | Local | Exponential decay is simple math |
| **Chain→feature scoring** | Local | All feature computations are mathematical |
| **Template matching** | Local | Compare new events against known chain templates |
| **Event extraction from news** | API (Claude) | Requires NLU — the core irreducible AI task |
| **Novel chain validation** | API (Claude) | When a new causal path is proposed, validate economic plausibility |
| **Briefing generation** | API (Claude) | Natural language generation for user-facing text |

### 6.4 Efficiency Techniques

1. **Cross-symbol batching**: If HDFCBANK, ICICIBANK, and SBIN all have news about "RBI rate decision", make ONE Claude call with all articles and ask for multi-symbol chain extraction. This reduces 3 calls to 1.

2. **Chain template caching**: Once a chain like "RBI rate hold → bank margins stable → banking stocks bullish" has been seen 5+ times, store it as a template. When a new "RBI rate hold" event is detected locally (via keyword matching), **instantiate the template without an API call** — only call Claude if the new articles suggest a deviation from the template.

3. **Incremental extraction**: If 3 new articles arrive but 7 from the previous batch are unchanged, only send the 3 new articles plus a summary of previously extracted chains. Ask Claude to *update* rather than re-extract.

4. **Tiered symbol priority**: Not all 31 symbols need event-chain analysis every hour. Prioritize:
   - **Tier 1** (every cycle): Symbols with active signals or high recent volatility
   - **Tier 2** (every 2 hours): Remaining NIFTY 50 stocks
   - **Tier 3** (every 4 hours): Low-volatility forex pairs

### 6.5 Emergency Budget Protection

If monthly spend exceeds 80% of budget before the 24th of the month:
- Fall back to **template-only mode**: Use cached chain templates, no new Claude extraction calls
- Technical analysis continues uninterrupted (no API cost)
- Signal confidence capped at 60% (existing behavior when AI unavailable)

---

## 7. Data Model

### 7.1 Database Schema

Four new tables, designed to integrate with the existing PostgreSQL + TimescaleDB setup:

```sql
-- ══════════════════════════════════════════════════════
-- Table: events
-- Extracted real-world events from news articles
-- ══════════════════════════════════════════════════════
CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description     VARCHAR(200) NOT NULL,
    category        VARCHAR(30) NOT NULL 
                    CHECK (category IN (
                        'macro_policy', 'earnings', 'sector', 
                        'geopolitical', 'regulatory', 'technical', 'commodity'
                    )),
    source_articles JSONB NOT NULL DEFAULT '[]',    -- [{title, url, source}]
    source_count    INTEGER NOT NULL DEFAULT 1,
    event_time      TIMESTAMPTZ NOT NULL,           -- when the event occurred/was reported
    extracted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence      DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',             -- flexible: geography, magnitude, etc.
    
    -- Deduplication: prevent re-extracting the same event
    content_hash    VARCHAR(64) UNIQUE NOT NULL      -- SHA-256 of normalized description
);

CREATE INDEX idx_events_active_time ON events (is_active, event_time DESC);
CREATE INDEX idx_events_category ON events (category, event_time DESC);
CREATE INDEX idx_events_hash ON events (content_hash);

-- ══════════════════════════════════════════════════════
-- Table: causal_edges
-- Directed edges in the event-impact graph
-- ══════════════════════════════════════════════════════
CREATE TABLE causal_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    
    -- Target can be another event (intermediate effect) or a symbol
    target_type     VARCHAR(10) NOT NULL 
                    CHECK (target_type IN ('event', 'symbol', 'sector')),
    target_event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    target_symbol   VARCHAR(20),            -- populated when target_type = 'symbol'
    target_sector   VARCHAR(50),            -- populated when target_type = 'sector'
    
    edge_type       VARCHAR(15) NOT NULL DEFAULT 'CAUSES'
                    CHECK (edge_type IN ('CAUSES', 'AFFECTS', 'PRECEDES')),
    direction       VARCHAR(10)             -- 'bullish', 'bearish', 'neutral'
                    CHECK (direction IN ('bullish', 'bearish', 'neutral')),
    magnitude       DECIMAL(4,3) DEFAULT 0.500,  -- 0.0 to 1.0
    confidence      DECIMAL(4,3) DEFAULT 0.500,  -- 0.0 to 1.0
    mechanism       VARCHAR(200),           -- brief causal mechanism description
    
    -- Temporal attributes
    lag_hours       INTEGER DEFAULT 0,      -- expected delay before effect manifests
    decay_rate      DECIMAL(8,6),           -- λ for exponential decay
    time_horizon    VARCHAR(10) DEFAULT 'days'
                    CHECK (time_horizon IN ('hours', 'days', 'weeks', 'months')),
    
    chain_id        UUID NOT NULL,          -- groups edges belonging to same chain
    step_order      INTEGER NOT NULL,       -- position in chain (1, 2, 3...)
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure either target_event_id or target_symbol is populated
    CHECK (
        (target_type = 'event' AND target_event_id IS NOT NULL) OR
        (target_type = 'symbol' AND target_symbol IS NOT NULL) OR
        (target_type = 'sector' AND target_sector IS NOT NULL)
    )
);

CREATE INDEX idx_edges_source ON causal_edges (source_event_id);
CREATE INDEX idx_edges_target_symbol ON causal_edges (target_symbol, created_at DESC)
    WHERE target_type = 'symbol';
CREATE INDEX idx_edges_chain ON causal_edges (chain_id, step_order);

-- ══════════════════════════════════════════════════════
-- Table: event_chains
-- Aggregated chain metadata for fast lookup
-- ══════════════════════════════════════════════════════
CREATE TABLE event_chains (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    root_event_id   UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    chain_depth     INTEGER NOT NULL DEFAULT 1,
    affected_symbols JSONB NOT NULL DEFAULT '[]',    -- ["HDFCBANK.NS", "ICICIBANK.NS"]
    net_direction   VARCHAR(10) NOT NULL DEFAULT 'neutral'
                    CHECK (net_direction IN ('bullish', 'bearish', 'neutral')),
    net_confidence  DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    net_magnitude   DECIMAL(4,3) NOT NULL DEFAULT 0.500,
    
    -- Temporal envelope
    onset_time      TIMESTAMPTZ NOT NULL,   -- when first effect activates
    peak_time       TIMESTAMPTZ,            -- estimated time of max impact
    expiry_time     TIMESTAMPTZ,            -- when chain impact decays below threshold
    
    -- Track record (updated as outcomes are observed)
    template_id     UUID REFERENCES chain_templates(id),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chains_active ON event_chains (is_active, onset_time DESC);
CREATE INDEX idx_chains_symbols ON event_chains USING GIN (affected_symbols);

-- ══════════════════════════════════════════════════════
-- Table: chain_templates
-- Reusable causal patterns learned from history
-- ══════════════════════════════════════════════════════
CREATE TABLE chain_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     VARCHAR(500) NOT NULL,
    category        VARCHAR(30) NOT NULL,
    pattern         JSONB NOT NULL,         -- abstract chain structure
    
    -- Track record
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    correct_count   INTEGER NOT NULL DEFAULT 0,
    accuracy        DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE WHEN occurrence_count > 0 
             THEN correct_count::DECIMAL / occurrence_count 
             ELSE 0.0 END
    ) STORED,
    avg_return_pct  DECIMAL(8,4) DEFAULT 0.0,
    
    -- Temporal parameters (learned from history)
    typical_half_life_hours DECIMAL(8,2),
    typical_magnitude       DECIMAL(4,3),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_category ON chain_templates (category, accuracy DESC);
```

### 7.2 Indexing Strategy

The primary access patterns and their indexes:

| Query Pattern | Frequency | Index Used |
|---------------|-----------|------------|
| "All active chains affecting symbol X" | Every scoring cycle (~5 min) | `idx_edges_target_symbol` + `idx_chains_active` |
| "All active chains" (for graph loading) | Worker startup / daily | `idx_chains_active` |
| "Deduplicate incoming event" | Every extraction | `idx_events_hash` |
| "Chain template by category" | Every event extraction | `idx_templates_category` |
| "Historical chains for backtesting" | On demand | `idx_chains_active` with date range |

### 7.3 Data Lifecycle

| Data | Retention | Cleanup |
|------|-----------|---------|
| Events | 90 days active, archived indefinitely | `is_active = FALSE` after `expiry_time` |
| Causal edges | Same as parent event | CASCADE delete with event |
| Event chains | 90 days active | Deactivate after `expiry_time`, keep for backtest |
| Chain templates | Permanent | Only deactivated if accuracy drops below 40% |

---

## 8. Evaluation Framework

### 8.1 Core Question

> Does event-chain scoring improve signal quality vs. flat sentiment scoring?

### 8.2 Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Directional Accuracy** | % of signals where predicted direction matches actual price movement at `time_horizon` | >55% (vs. current baseline) |
| **Confidence Calibration** | Correlation between confidence score and actual outcome probability (Brier score) | Brier < 0.22 |
| **Hit Rate (targets)** | % of signals that reach `target_price` before `stop_loss` | >40% |
| **Information Coefficient (IC)** | Rank correlation between signal confidence and forward returns | IC > 0.05 |
| **Sharpe Improvement** | Sharpe ratio of chain-enhanced signals vs. sentiment-only signals | >0.15 improvement |
| **Chain Unique Alpha** | % of correct chain signals that sentiment-only scored as HOLD | >20% |

### 8.3 Backtesting Methodology

**A/B comparison** on historical data:

```
Period:     2025-06 to 2026-03 (9 months of historically available data)
Universe:   31 tracked symbols
Signals:    Only where event-chain signal ≠ sentiment-only signal
Benchmark:  Sentiment-only confidence → same threshold → same targets

For each signal where chain_confidence ≠ sentiment_confidence:
  1. Record: symbol, direction, chain_confidence, sentiment_confidence, 
             entry_price, target, stop_loss, timeframe
  2. Track: which hit first (target or stop_loss), at what time
  3. Compare: chain hit_rate vs. sentiment hit_rate
```

**Statistical significance**: Use McNemar's test (paired comparison of correctness) since the same events are scored by both methods. Require $p < 0.05$.

### 8.4 Ablation Studies

Test the contribution of each component:

| Ablation | What to Remove | Expected Impact |
|----------|---------------|-----------------|
| No chains, sentiment only | Current system | Baseline |
| Chains without temporal decay | Remove decay model | Lower accuracy for multi-day events |
| Chains without cross-symbol propagation | Disable shared chains | Miss sector-wide impacts |
| Chains without templates | No historical templates | Lower confidence calibration |
| Chains without mechanism scoring | Remove $f_{\text{mechanism}}$ | More false causal links, lower precision |

### 8.5 Online Evaluation (Post-Launch)

After deployment, track:
- **Rolling 30-day directional accuracy**: Should not degrade below sentiment-only baseline
- **Chain template accuracy drift**: Alert if any template drops below 40% accuracy
- **Novel chain discovery rate**: How many new chain patterns are being created vs. template reuse
- **Budget utilization vs. signal improvement**: Marginal cost per percentage point of accuracy improvement

---

## 9. Scalability Concerns

### 9.1 Data Volume Estimates

| Data Type | Volume/Day | Volume/Month | Volume/Year |
|-----------|-----------|-------------|-------------|
| News articles fetched | ~300 (31 symbols × ~10 articles) | ~9,000 | ~108,000 |
| Events extracted | ~50-100 (many articles → same event) | ~1,500-3,000 | ~18,000-36,000 |
| Causal edges | ~150-300 (avg 3 edges per event) | ~4,500-9,000 | ~54,000-108,000 |
| Event chains | ~50-100 (1:1 with events) | ~1,500-3,000 | ~18,000-36,000 |
| Chain templates | ~2-5 new/month (most are reuse) | ~5 | ~60 |

**Total new rows per month**: ~15,000-20,000 across all ECI tables. This is trivially small for PostgreSQL.

### 9.2 Memory Footprint (NetworkX Graph)

Active graph (7-day window):
- Nodes: ~700 events + 31 symbols + ~20 sectors = ~750 nodes
- Edges: ~2,100 causal edges
- Memory: ~5-10 MB with attributes

This fits comfortably in a Celery worker's memory. No special handling needed.

### 9.3 Computational Bottleneck

The bottleneck is **Claude API latency**, not compute:

| Operation | Latency | Bottleneck? |
|-----------|---------|-------------|
| Claude event extraction | 3-8 seconds per call | **Yes** — limits throughput to ~10 calls/minute |
| Graph traversal (NetworkX) | <1ms for depth-3 on 750 nodes | No |
| Feature computation | <1ms per symbol | No |
| Database writes | <10ms per batch | No |
| News fetching (HTTP) | 1-5 seconds per source | Parallelizable |

**Mitigation**: Run extraction calls asynchronously. Process symbols in priority tiers (Section 6.4). Cache aggressively.

### 9.4 Growth Path

If SignalFlow scales beyond 31 symbols:

| Scale | Change Needed |
|-------|--------------|
| 50 symbols | No changes; tiered prioritization absorbs growth |
| 100 symbols | Increase API budget to ~$50/month; add sector-level extraction (1 call per sector instead of per symbol) |
| 500+ symbols | Need local NLP model (fine-tuned DistilBERT or similar) for initial event classification; Claude only for novel/ambiguous events |
| 1000+ symbols | Graph database (Neo4j/TigerGraph), dedicated event extraction workers, streaming architecture |

For the current 31-symbol scope, **all proposed changes fit within existing infrastructure** (PostgreSQL, Redis, Celery, single backend container).

---

## 10. Concrete Algorithm

### 10.1 End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT-CHAIN INTELLIGENCE PIPELINE             │
│                                                                  │
│  ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐ │
│  │  NEWS   │────►│  DEDUP   │────►│  EXTRACT │────►│  STORE  │ │
│  │  FETCH  │     │  & BATCH │     │  (Claude)│     │  EVENTS │ │
│  └─────────┘     └──────────┘     └──────────┘     └────┬────┘ │
│                                                          │      │
│  ┌─────────┐     ┌──────────┐     ┌──────────┐     ┌────▼────┐ │
│  │ SIGNAL  │◄────│  SCORE   │◄────│  BUILD   │◄────│  MATCH  │ │
│  │   GEN   │     │ FEATURES │     │  GRAPH   │     │TEMPLATES│ │
│  └─────────┘     └──────────┘     └──────────┘     └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Step-by-Step Algorithm

```
ALGORITHM: EventChainSignalPipeline
═══════════════════════════════════

INPUT: symbol S, market_type M, technical_data T
OUTPUT: (confidence, signal_type, chain_reasoning)

─── Phase 1: News Acquisition ───

1. articles ← fetch_news(S, M, max=10)
2. articles ← deduplicate(articles, method=jaccard_similarity, threshold=0.7)
3. IF |articles| = 0:
     RETURN score_technical_only(T)

─── Phase 2: Cross-Symbol Batching ───

4. related_symbols ← get_sector_peers(S)  // e.g., S=HDFCBANK → [ICICIBANK, SBIN, KOTAKBANK]
5. peer_articles ← {sym: fetch_cached_articles(sym) for sym in related_symbols}
6. shared_articles ← articles ∩ ∪(peer_articles.values())  // articles appearing for multiple symbols
7. IF |shared_articles| > 3:
     batch_symbols ← {S} ∪ {sym for sym in related_symbols if overlap(articles, peer_articles[sym]) > 2}
   ELSE:
     batch_symbols ← {S}

─── Phase 3: Event Extraction (Claude API) ───

8. cache_key ← hash(sorted(articles) + sorted(batch_symbols))
9. IF cache_hit(cache_key):
     extracted ← cache_get(cache_key)
10. ELSE:
     extracted ← claude_extract_events(articles, batch_symbols)  // EVENT_CHAIN_PROMPT
     cache_set(cache_key, extracted, ttl=3600)
     cost_tracker.record(extracted.token_usage)

─── Phase 4: Event Deduplication & Storage ───

11. FOR event IN extracted.events:
      content_hash ← sha256(normalize(event.description))
      IF event_exists(content_hash):
        existing ← get_event(content_hash)
        merge_sources(existing, event)  // add new article sources
        CONTINUE
      ELSE:
        store_event(event)

─── Phase 5: Template Matching ───

12. FOR event IN extracted.events:
      template ← find_matching_template(event.category, event.description)
      IF template AND template.accuracy > 0.5:
        // Use historical template parameters
        chain ← instantiate_template(template, event)
        chain.confidence *= template.accuracy  // weight by track record
      ELSE:
        // Novel chain — use Claude's extracted chain directly
        chain ← build_chain_from_extraction(event, extracted)
      store_chain(chain)

─── Phase 6: Graph Construction ───

13. G ← load_active_graph(lookback_days=7)  // NetworkX DiGraph
14. FOR chain IN get_active_chains(S):
      add_chain_to_graph(G, chain)

─── Phase 7: Feature Computation ───

15. now ← current_time()
16. active_impacts ← []
17. FOR chain IN chains_affecting(G, S):
      impact ← chain_impact_at_time(chain, now)  // Section 4.4 formula
      IF |impact| > 0.01:  // above noise threshold
        active_impacts.append({
          direction: sign(impact),
          magnitude: |impact|,
          confidence: chain.net_confidence,
          depth: chain.chain_depth,
          category: chain.root_event.category
        })

18. features ← {
      chain_net_direction:    sum(i.direction * i.magnitude for i in active_impacts) / max(sum(i.magnitude), ε),
      chain_confidence:       weighted_mean(i.confidence, weights=i.magnitude for i in active_impacts),
      chain_count:            len(active_impacts),
      chain_consensus:        1 - entropy([i.direction for i in active_impacts]),
      chain_max_magnitude:    max(i.magnitude for i in active_impacts) if active_impacts else 0,
      chain_depth_weighted:   sum(i.depth * i.magnitude for i in active_impacts),
      event_novelty:          1 - max_template_similarity(active_impacts)
    }

─── Phase 8: Signal Scoring ───

19. tech_score ← compute_technical_score(T)  // existing function
20. chain_score ← 50 + 50 * tanh(2.0 * features.chain_net_direction 
                                       * features.chain_confidence 
                                       * features.chain_consensus)
21. sentiment_residual ← extracted.overall_confidence * 100  // fallback mood score

22. // Interaction effects
    IF features.chain_net_direction > 0 AND T.rsi.value > 70:
      chain_score *= 0.7  // bullish chain + overbought RSI → discount chain
    IF features.chain_net_direction < 0 AND T.rsi.value < 30:
      chain_score *= 0.7  // bearish chain + oversold RSI → discount chain
    IF features.chain_consensus > 0.8 AND T.volume.signal == "buy":
      chain_score = chain_score * 0.8 + tech_score * 0.2  // boost if volume confirms

23. final_confidence ← tech_score * 0.50 + chain_score * 0.35 + sentiment_residual * 0.15
24. final_confidence ← clip(round(final_confidence), 0, 100)
25. signal_type ← threshold_to_signal(final_confidence)  // existing SIGNAL_THRESHOLDS

─── Phase 9: Reasoning Generation ───

26. chain_summary ← format_top_chains(active_impacts, max=3)
27. reasoning ← claude_generate_reasoning(S, signal_type, final_confidence, T, chain_summary)
    // Or, if budget constrained:
    reasoning ← template_reasoning(S, signal_type, chain_summary)

RETURN (final_confidence, signal_type, reasoning)
```

### 10.3 Complexity Analysis

| Phase | Time Complexity | API Calls | Notes |
|-------|----------------|-----------|-------|
| News Acquisition | O(sources) | 0 (HTTP only) | Parallelized |
| Cross-Symbol Batching | O(|peers| × |articles|) | 0 | Set intersection |
| Event Extraction | O(1) per call | **1** | The core Claude call |
| Event Dedup & Storage | O(|events|) | 0 | Hash lookup |
| Template Matching | O(|events| × |templates|) | 0 | Can be optimized with category index |
| Graph Construction | O(E + V) | 0 | NetworkX loading |
| Feature Computation | O(|active_chains|) | 0 | Linear scan |
| Signal Scoring | O(1) | 0 | Arithmetic |
| Reasoning | O(1) | **0-1** | Optional Claude call |

**Total Claude API calls per symbol scoring: 1-2** (vs. current 1-2). Budget-neutral.

### 10.4 Pseudocode for Key Subroutines

**chain_impact_at_time** (temporal decay):

```python
import math
from datetime import datetime

DECAY_RATES = {
    "macro_policy": 0.0030,   # ~10-day half-life
    "earnings":     0.0100,   # ~3-day half-life
    "sector":       0.0050,   # ~6-day half-life
    "geopolitical": 0.0200,   # ~1.5-day half-life
    "regulatory":   0.0020,   # ~14-day half-life
    "technical":    0.0500,   # ~14-hour half-life
    "commodity":    0.0030,   # ~10-day half-life
}

def chain_impact_at_time(chain, now: datetime) -> float:
    hours_elapsed = (now - chain.onset_time).total_seconds() / 3600
    if hours_elapsed < 0:
        return 0.0
    
    decay_rate = DECAY_RATES.get(chain.category, 0.0050)
    decay = math.exp(-decay_rate * hours_elapsed)
    
    # Direction: +1 bullish, -1 bearish
    direction = 1.0 if chain.net_direction == "bullish" else -1.0
    
    return chain.net_magnitude * chain.net_confidence * direction * decay
```

**find_matching_template** (template lookup):

```python
def find_matching_template(category: str, description: str) -> ChainTemplate | None:
    # 1. Filter templates by category
    candidates = get_templates_by_category(category)
    
    # 2. Compute similarity between event description and template descriptions
    # Using simple token overlap (no external model needed)
    best_match = None
    best_score = 0.0
    
    desc_tokens = set(description.lower().split())
    for template in candidates:
        template_tokens = set(template.description.lower().split())
        jaccard = len(desc_tokens & template_tokens) / max(len(desc_tokens | template_tokens), 1)
        if jaccard > best_score and jaccard > 0.4:  # minimum similarity threshold
            best_score = jaccard
            best_match = template
    
    return best_match
```

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- Database migrations for 4 new tables
- Event and chain data models (SQLAlchemy)
- Pydantic schemas for event extraction response
- Unit tests for all new models

### Phase 2: Extraction Pipeline (Week 3-4)
- EVENT_CHAIN_PROMPT implementation and testing
- Event deduplication (content hashing)
- Cross-symbol batching logic
- Integration with existing news fetcher
- Replace sentiment Celery task with event-chain task

### Phase 3: Graph & Scoring (Week 5-6)
- NetworkX graph construction from DB
- Temporal decay computation
- Feature extraction from event graph
- New scoring formula (50/35/15 blend)
- Chain template storage and matching

### Phase 4: Evaluation (Week 7-8)
- Backtesting framework for chain vs. sentiment comparison
- A/B metric collection
- Template accuracy tracking
- Dashboard integration (show chain reasoning in signal detail)

### Phase 5: Optimization (Week 9-10)
- Budget monitoring for new call pattern
- Template auto-learning from resolved chains
- Decay constant calibration from historical data
- Cross-symbol propagation tuning

---

## 12. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Claude extracts unreliable causal chains | Medium | High — bad chains → bad signals | Template validation + confidence thresholds + historical track records |
| Budget overrun from verbose chain extraction | Medium | Medium — caps signals at 60% | Token counting per call + tiered symbol priority + template caching |
| Spurious causation (correlation ≠ causation) | High | Medium — false causal links | Granger causality validation + human-readable chain display for manual review |
| Over-fitting to historical chain patterns | Medium | Medium — templates become stale | Quarterly template review + decay of template confidence over time |
| Latency increase in signal pipeline | Low | Low — users tolerate 5s delay | Async extraction + graph preloading |
| Complexity makes debugging harder | Medium | Medium — harder to trace signal reasoning | Structured logging with chain IDs + full chain display in signal detail |

---

## 13. Open Questions for Discussion

1. **Weight tuning**: Should the 50/35/15 split (tech/chain/residual) be fixed or learned from data? If learned, minimum sample size before adjustment?

2. **Chain depth limit**: Should we cap at 3 hops? Deeper chains have compounding uncertainty: confidence at depth $k$ is roughly $c^k$ — at depth 4 with $c=0.7$, chain confidence is only $0.24$.

3. **Cross-market chains**: How should chains that cross market types be handled? (e.g., "Fed rate hike → USD strengthens → USD/INR moves → Rupee-denominated stocks affected"). Should cross-market propagation have a penalty factor?

4. **User-facing display**: How much of the causal chain should be shown in the signal card? Full chain? Just root event and final impact? What about in Telegram alerts?

5. **Manual chain injection**: Should the user be able to input a causal hypothesis (e.g., "I think Jio's 5G launch will hurt Airtel") and have the system track it?

6. **Template seeding**: Should we pre-seed ~20 common chain templates (rate decisions, earnings, geopolitical) or let them emerge organically from extraction?

---

*This document is a research review for brainstorming purposes. No code changes should be made based on this document without an implementation plan review.*
