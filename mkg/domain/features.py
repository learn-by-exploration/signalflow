# mkg/domain/features.py
"""MKG feature catalog, competitive positioning, and application documentation.

This module embeds the core research content from the MKG problem definition,
market research, competitor analysis, supply chain application, and tribal
knowledge gap documents. It serves as the single source of truth for what
MKG is, what it does, and how it compares to every commercial alternative.

Source documents (core/):
  - MKG_Problem_Definition.html
  - MKG_Problem_Research-2.html
  - MKG_Market_Research.html
  - MKG_Competitor_Deep_Dive.html
  - MKG_SupplyChain_Application.html
  - MKG_Tribal_Knowledge_Gap.html
  - MKG_Niche_Definition_FINAL.html
  - MKG_REQUIREMENTS.md (Section 11: MiroFish Integration)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Core Identity
# ---------------------------------------------------------------------------

TAGLINE = (
    "The world runs on relationships. No tool maps them. MKG does."
)

ONE_LINE_NICHE = (
    "MKG is the first commercial system that reads live signals across "
    "13 languages, continuously adjusts the weights of company-to-company "
    "relationships in a dynamic knowledge graph, traverses that graph when "
    "any node is affected by a news event, and delivers a ranked impact "
    "list — with direction, confidence, and full causal explanation — "
    "in 60 seconds."
)

POWER_STATEMENT = (
    "Bloomberg tells you what happened. AlphaSense tells you what was said "
    "about it. RavenPack tells you how the market felt. FactSet Revere tells "
    "you who is statically connected. Interos tells you that your Tier 1 and "
    "partial Tier 2 suppliers are at risk. Palantir, if you have $5M and 18 "
    "months, will build you a graph.\n\n"
    "None of them can answer the question that matters: A news event just hit "
    "this entity. Which other entities are affected, in what direction, with "
    "what weight, through what path, at what confidence, over what time "
    "horizon? — and deliver that answer in 60 seconds.\n\n"
    "MKG can."
)

TRIBAL_KNOWLEDGE_STATEMENT = (
    "42% of institutional knowledge lives only in individual heads. When a "
    "15-year analyst leaves, their Bloomberg subscription transfers, their "
    "FactSet models export — but their mental map of 200+ relationship "
    "edges, calibrated heuristics, and cycle timing patterns are completely "
    "lost.\n\n"
    "MKG is the first commercial system designed to make tribal knowledge "
    "permanent — to encode it in a graph that updates continuously, "
    "traverses automatically, explains completely, and never retires."
)

# ---------------------------------------------------------------------------
# Three-Speed Market Thesis
# ---------------------------------------------------------------------------

THREE_SPEED_THESIS = {
    "summary": (
        "Markets have three speeds. Every commercial platform serves "
        "Speed 1 and Speed 2. No one serves Speed 3."
    ),
    "speeds": [
        {
            "name": "Speed 1 — Direct Entity Pricing",
            "latency": "<100ms",
            "description": (
                "HFT reprices entity-specific news in milliseconds. "
                "Fully arbitraged. Zero edge."
            ),
            "served_by": [
                "Bloomberg", "LSEG", "FactSet", "every terminal"
            ],
        },
        {
            "name": "Speed 2 — Intra-Industry Spillovers",
            "latency": "Hours to 3 days",
            "description": (
                "Sell-side analysts and sector desks reprice obvious "
                "industry peers. Well-covered: 440K+ earnings "
                "announcements across 6 markets."
            ),
            "served_by": [
                "Bloomberg", "AlphaSense", "RavenPack", "sell-side research"
            ],
        },
        {
            "name": "Speed 3A — Supply Chain Contagion",
            "latency": "~2 weeks",
            "description": (
                "Crash risk transmits customer→supplier with a 2-week "
                "delay (peer-reviewed: Production & Operations Management "
                "2024). Commercially unaddressed."
            ),
            "served_by": [],
            "mkg_advantage": (
                "MKG traverses the supply chain graph in 60 seconds — "
                "T+0 vs the market's T+10 days."
            ),
        },
        {
            "name": "Speed 3B — Non-Supply-Chain Relationship Contagion",
            "latency": "Weeks to months",
            "description": (
                "Board interlocks, joint ventures, licensing, shared "
                "regulatory exposure. Post-Earnings Announcement Drift "
                "documented since 1968 (Ball & Brown). 60% of Friday "
                "earnings response is delayed (DellaVigna & Pollett)."
            ),
            "served_by": [],
            "mkg_advantage": (
                "MKG's edge types cover 14 relationship categories "
                "including OWNS, PARTNERS_WITH, LICENSES_FROM."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Feature Matrix
# ---------------------------------------------------------------------------

@dataclass
class Feature:
    """A single MKG capability."""

    id: str
    name: str
    description: str
    category: str
    is_novel: bool = False  # True = exists in zero commercial platforms
    status: str = "implemented"  # implemented | planned | research


FEATURE_CATEGORIES = [
    "Relationship Graph",
    "Propagation Engine",
    "Temporal Infrastructure",
    "Explainability & Compliance",
    "Article Intelligence",
    "Tribal Knowledge",
    "Supply Chain",
    "Alert System",
]

FEATURES: list[Feature] = [
    # --- Relationship Graph ---
    Feature(
        id="RG-01",
        name="Dynamic Weighted Edges",
        description=(
            "Every edge carries weight (0.0-1.0), confidence (0.0-1.0), "
            "and temporal validity. Weights adjust continuously based on "
            "news signals and market events."
        ),
        category="Relationship Graph",
        is_novel=True,
    ),
    Feature(
        id="RG-02",
        name="14 Relationship Types",
        description=(
            "SUPPLIES, COMPETES_WITH, PARTNERS_WITH, SUBSIDIARY_OF, "
            "REGULATES, DEPENDS_ON, OWNS, INVESTS_IN, ACQUIRES, "
            "LICENSES_FROM, and more. Covers supply chain, corporate "
            "structure, regulatory, and financial relationships."
        ),
        category="Relationship Graph",
        is_novel=True,
    ),
    Feature(
        id="RG-03",
        name="Entity Deduplication",
        description="Canonical name resolution prevents duplicate entities.",
        category="Relationship Graph",
    ),
    Feature(
        id="RG-04",
        name="Multi-Hop Traversal (6 hops)",
        description=(
            "Traverse up to 6 relationship hops to discover hidden "
            "second, third, and fourth-order connections. Industry "
            "standard (where it exists) is 1-2 hops."
        ),
        category="Relationship Graph",
        is_novel=True,
    ),

    # --- Propagation Engine ---
    Feature(
        id="PE-01",
        name="60-Second Event Propagation",
        description=(
            "When a news event hits any entity, MKG traverses the graph "
            "and delivers a ranked impact list with direction, confidence, "
            "and causal path in under 60 seconds."
        ),
        category="Propagation Engine",
        is_novel=True,
    ),
    Feature(
        id="PE-02",
        name="Edge Weight Decay",
        description=(
            "Stale relationships automatically lose weight over time. "
            "A partnership announced 3 years ago with no recent signals "
            "decays. Active relationships strengthen."
        ),
        category="Propagation Engine",
        is_novel=True,
    ),
    Feature(
        id="PE-03",
        name="Causal Chain Building",
        description=(
            "Every propagation result includes the full causal chain: "
            "Event → Entity A → (relationship type, weight) → Entity B → "
            "predicted impact with confidence."
        ),
        category="Propagation Engine",
        is_novel=True,
    ),
    Feature(
        id="PE-04",
        name="Accuracy Tracking & Calibration",
        description=(
            "Predictions are tracked against actual market outcomes. "
            "Confidence scores are calibrated over time. Bad predictions "
            "reduce edge weights; accurate predictions strengthen them."
        ),
        category="Propagation Engine",
        is_novel=True,
    ),

    # --- Temporal Infrastructure ---
    Feature(
        id="TI-01",
        name="Edge Temporal Validity",
        description=(
            "Every edge has valid_from and valid_until timestamps. "
            "Queries can be scoped to any point in time."
        ),
        category="Temporal Infrastructure",
        is_novel=True,
    ),
    Feature(
        id="TI-02",
        name="Historical Pattern Replay",
        description=(
            "Replay past events through the graph to validate edge "
            "weights against historical outcomes."
        ),
        category="Temporal Infrastructure",
        is_novel=True,
        status="planned",
    ),

    # --- Explainability & Compliance ---
    Feature(
        id="EC-01",
        name="Full Audit Trail (SEBI 5-Year)",
        description=(
            "Every graph mutation, entity creation, edge weight change, "
            "and propagation event is recorded in a tamper-evident audit "
            "log retained for 5 years (1825 days) per SEBI requirements."
        ),
        category="Explainability & Compliance",
        is_novel=True,
    ),
    Feature(
        id="EC-02",
        name="Article-to-Signal Provenance",
        description=(
            "Complete lineage from source article → extracted entities → "
            "graph mutation → propagation event → signal output. "
            "Every recommendation is fully traceable."
        ),
        category="Explainability & Compliance",
        is_novel=True,
    ),
    Feature(
        id="EC-03",
        name="Regulatory Disclaimers",
        description=(
            "MiFID II and SEBI-compliant disclaimers auto-attached to "
            "every signal. Classification as 'AI-generated intelligence' "
            "not 'financial advice'."
        ),
        category="Explainability & Compliance",
    ),
    Feature(
        id="EC-04",
        name="PII Detection & Redaction",
        description=(
            "Automatic PII scanning and redaction in the article "
            "ingestion pipeline before entity extraction."
        ),
        category="Explainability & Compliance",
    ),

    # --- Article Intelligence ---
    Feature(
        id="AI-01",
        name="Multi-Source News Ingestion",
        description=(
            "Automated RSS/API ingestion from financial news sources "
            "with deduplication, PII redaction, and entity extraction."
        ),
        category="Article Intelligence",
    ),
    Feature(
        id="AI-02",
        name="NER/RE Pipeline",
        description=(
            "Named Entity Recognition and Relationship Extraction "
            "using tiered approach: regex (fast) → Claude API (accurate). "
            "Adapted from MiroFish NER for financial ontology."
        ),
        category="Article Intelligence",
    ),
    Feature(
        id="AI-03",
        name="Hallucination Verification",
        description=(
            "Extracted entities and relationships are verified against "
            "known graph data to reduce LLM hallucination."
        ),
        category="Article Intelligence",
    ),

    # --- Tribal Knowledge ---
    Feature(
        id="TK-01",
        name="Expert-Asserted Edges",
        description=(
            "Domain experts can manually assert relationships with "
            "confidence scores. These 'tribal knowledge' edges persist "
            "alongside algorithmically-discovered edges."
        ),
        category="Tribal Knowledge",
        is_novel=True,
    ),
    Feature(
        id="TK-02",
        name="Six Tribal Knowledge Types",
        description=(
            "Encodes: (1) Secret relationship maps, (2) CEO/CFO "
            "calibration biases, (3) Canary company detection, "
            "(4) Relationship decay signals, (5) Sector cycle timing, "
            "(6) Regulatory co-exposure."
        ),
        category="Tribal Knowledge",
        is_novel=True,
    ),

    # --- Supply Chain ---
    Feature(
        id="SC-01",
        name="Tier 2/3 Visibility",
        description=(
            "Map and monitor sub-suppliers and deep-chain dependencies "
            "beyond Tier 1. Only 6% of companies have full supply chain "
            "visibility. 40%+ lack even full Tier 1."
        ),
        category="Supply Chain",
        is_novel=True,
    ),
    Feature(
        id="SC-02",
        name="Disruption Propagation Scoring",
        description=(
            "When a disruption event hits any node in the supply chain, "
            "MKG propagates impact through weighted edges to score "
            "downstream/upstream exposure."
        ),
        category="Supply Chain",
        is_novel=True,
    ),

    # --- Alert System ---
    Feature(
        id="AL-01",
        name="Threshold-Based Alerts",
        description=(
            "Configurable alerts when propagation impact exceeds "
            "user-defined thresholds. Webhook and in-app delivery."
        ),
        category="Alert System",
    ),
    Feature(
        id="AL-02",
        name="Circuit Breaker Protection",
        description=(
            "Circuit breaker pattern protects against cascading failures "
            "in external service calls (LLM, news APIs)."
        ),
        category="Alert System",
    ),
]


# ---------------------------------------------------------------------------
# Competitive Comparison
# ---------------------------------------------------------------------------

@dataclass
class Competitor:
    """A competitor platform profile."""

    name: str
    tier: str  # "Tier 1 — Data Infrastructure" etc.
    revenue: str
    users: str
    price_per_seat: str
    strengths: list[str]
    weaknesses: list[str]  # gaps MKG fills
    threat_to_mkg: str
    threat_timeline: str


COMPETITORS: list[Competitor] = [
    Competitor(
        name="Bloomberg Terminal",
        tier="Tier 1 — Data Infrastructure",
        revenue="$10B+",
        users="325K subscribers",
        price_per_seat="$31,980/yr",
        strengths=[
            "Real-time data across all asset classes",
            "IB messaging network (300K+ users)",
            "Execution and portfolio analytics",
        ],
        weaknesses=[
            "Zero relationship graph",
            "No event propagation engine",
            "No dynamic edge weights",
            "No causal chain explanation",
        ],
        threat_to_mkg="Medium",
        threat_timeline="3-5 years",
    ),
    Competitor(
        name="LSEG Workspace (Refinitiv)",
        tier="Tier 1 — Data Infrastructure",
        revenue="£8.49B",
        users="400K+",
        price_per_seat="$15-22K/yr",
        strengths=[
            "Reuters news network",
            "StarMine quantitative models",
            "CodeBook Python SDK",
        ],
        weaknesses=[
            "No knowledge graph",
            "Cloud-only deployment",
            "Data quality gaps post Refinitiv merger",
        ],
        threat_to_mkg="Medium",
        threat_timeline="2-3 years (Microsoft partnership vector)",
    ),
    Competitor(
        name="FactSet Research",
        tier="Tier 1 — Data Infrastructure",
        revenue="$2.32B",
        users="237K",
        price_per_seat="~$12K/yr",
        strengths=[
            "Best-in-class fundamentals",
            "Revere: 40K+ static supply chain relationships (closest to MKG)",
        ],
        weaknesses=[
            "Revere is static — filing-sourced, no dynamic weights",
            "No propagation engine",
            "No event-driven traversal",
        ],
        threat_to_mkg="High",
        threat_timeline="2-4 years (highest Tier 1 threat)",
    ),
    Competitor(
        name="S&P Capital IQ",
        tier="Tier 1 — Data Infrastructure",
        revenue="~$14B (S&P Global)",
        users="Undisclosed (large)",
        price_per_seat="$15-25K/yr",
        strengths=[
            "Board/executive network (closest static graph)",
            "Panjiva trade data",
            "M&A database",
        ],
        weaknesses=[
            "Static graph only — no dynamic weights",
            "No event propagation",
        ],
        threat_to_mkg="High",
        threat_timeline="2-4 years (if they execute)",
    ),
    Competitor(
        name="AlphaSense",
        tier="Tier 2 — AI & News Intelligence",
        revenue="$500M ARR",
        users="6,500+ companies",
        price_per_seat="$10-20K/yr",
        strengths=[
            "500M+ documents indexed",
            "Tegus expert transcripts",
            "Deep Research agent",
            "$4B valuation, rapid growth",
        ],
        weaknesses=[
            "No knowledge graph",
            "No relationship traversal",
            "English-dominant",
            "Cloud-only",
        ],
        threat_to_mkg="Highest Overall",
        threat_timeline="18 months to 3 years",
    ),
    Competitor(
        name="RavenPack",
        tier="Tier 2 — AI & News Intelligence",
        revenue="~$25-37M",
        users="70%+ of top quantitative hedge funds",
        price_per_seat="Custom ($50K+/yr)",
        strengths=[
            "40K+ sources in 13 languages",
            "22 years of historical data",
            "Bigdata.com agent platform",
        ],
        weaknesses=[
            "Entity-level scores only (not edge/relationship scores)",
            "No graph structure",
            "No propagation engine",
        ],
        threat_to_mkg="Medium-High",
        threat_timeline="Potential M&A acquisition scenario",
    ),
    Competitor(
        name="Palantir Foundry",
        tier="Tier 3 — Enterprise Graph",
        revenue="$2.87B",
        users="Enterprise (limited count)",
        price_per_seat="$5M+ per deployment",
        strengths=[
            "On-premise deployment",
            "Ontology (graph-like data model)",
            "AIP (agent infrastructure)",
        ],
        weaknesses=[
            "$5M+ minimum cost",
            "20-person implementation team",
            "Not purpose-built for financial markets",
            "18-month deployment cycle",
        ],
        threat_to_mkg="Low-Medium",
        threat_timeline="Different segment entirely",
    ),
    Competitor(
        name="Interos.ai",
        tier="Tier 3 — Supply Chain Graph",
        revenue="Pre-revenue ($204M raised, $1B valuation)",
        users="Government + enterprise",
        price_per_seat="Enterprise pricing",
        strengths=[
            "Multi-tier supply chain graph",
            "6-category AI risk scoring",
        ],
        weaknesses=[
            "Not designed for investors",
            "No financial signals",
            "No propagation scoring",
        ],
        threat_to_mkg="Very Low",
        threat_timeline="Proof-of-concept validation for MKG",
    ),
    Competitor(
        name="FinDKG",
        tier="Academic Research",
        revenue="$0 (research prototype)",
        users="Academic community",
        price_per_seat="Free (open source)",
        strengths=[
            "Proves dynamic financial KG outperforms static methods",
            "Neural temporal link prediction",
        ],
        weaknesses=[
            "Non-commercial",
            "English-only",
            "No enterprise features",
        ],
        threat_to_mkg="Zero",
        threat_timeline="THE blueprint MKG is commercializing",
    ),
]


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

MARKET_DATA = {
    "total_addressable_market": "$15B+ (intersection of 5 segments)",
    "segments": [
        {"name": "Traditional Financial Data", "size": "$35B", "cagr": "8%"},
        {"name": "Alternative Data", "size": "$11.65B → $135B by 2030", "cagr": "63%"},
        {"name": "Market Intelligence (AI)", "size": "~$8B", "cagr": "16%"},
        {"name": "Knowledge Graph Technology", "size": "$1.1B → $6.9B by 2030", "cagr": "37%"},
        {"name": "Supply Chain Risk Mgmt", "size": "$4.52B → $9.2B by 2030", "cagr": "15.3%"},
    ],
    "key_stats": {
        "desk_annual_spend": "$525K-$900K/yr (10-seat desk on Bloomberg + FactSet + AlphaSense)",
        "alt_data_spend": "$1.6M/yr average (large funds), 43 datasets",
        "budget_outlook": "95% plan to maintain or increase alt data budgets",
    },
}


# ---------------------------------------------------------------------------
# Application Domains
# ---------------------------------------------------------------------------

APPLICATION_DOMAINS = [
    {
        "name": "Financial Markets — Alpha Generation",
        "description": (
            "Exploit the 2-week delay in supply chain contagion "
            "(Speed 3A) and the weeks-to-months delay in non-supply-chain "
            "relationship contagion (Speed 3B) for investment alpha."
        ),
        "buyer_profiles": [
            {"role": "Long/Short Equity PM", "severity": 95,
             "pain": "Blind to second-order beneficiaries in short book"},
            {"role": "Multi-PM Platform Risk Desk", "severity": 88,
             "pain": "12 pods with correlated risk they don't know they share"},
            {"role": "Thematic/Macro PM", "severity": 80,
             "pain": "Position always incomplete"},
            {"role": "Quant Signal Developer", "severity": 74,
             "pain": "Dynamic graphs proven to outperform static correlations (FinDKG)"},
            {"role": "Event-Driven Fund", "severity": 68,
             "pain": "Only sees direct catalyst, misses network effects"},
            {"role": "Macro Allocator", "severity": 60,
             "pain": "Country-level views miss company-level concentration"},
        ],
    },
    {
        "name": "Supply Chain — Disruption Intelligence",
        "description": (
            "Map and monitor Tier 2/3+ supply chain dependencies that "
            "are invisible to ERP systems and traditional SRM platforms. "
            "Only 6% of companies have full supply chain visibility."
        ),
        "buyer_profiles": [
            {"role": "Chief Procurement Officer", "severity": 96,
             "pain": "Only 6% have full SC visibility, 8% revenue lost per disruption"},
            {"role": "Head of SC Risk", "severity": 88,
             "pain": "70-80% of disruptions cascade from Tier 2+"},
            {"role": "VP Supply Chain / COO", "severity": 84,
             "pain": "45% of a decade's profits lost to disruptions"},
            {"role": "CISO", "severity": 76,
             "pain": "Cyber risk in sub-supplier networks invisible"},
            {"role": "Chief Compliance Officer", "severity": 72,
             "pain": "EU CSDD requires full supply chain due diligence"},
            {"role": "CFO", "severity": 64,
             "pain": "Cannot quantify supply chain concentration risk"},
        ],
        "case_studies": [
            {
                "name": "Red Sea Crisis",
                "mkg_advantage": "38 days early warning vs 3 days without",
                "value": "$2-15M avoided costs per event",
            },
            {
                "name": "Renesas Factory Fire",
                "mkg_advantage": "Single Tier-3 plant fire → $210B automotive revenue lost",
                "value": "MKG maps 3-hop impact in 60 seconds",
            },
            {
                "name": "China Rare Earth Restrictions (April 2025)",
                "mkg_advantage": "MKG reads Chinese regulatory filings 11 days before English coverage",
                "value": "11-day information advantage",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Tribal Knowledge Types
# ---------------------------------------------------------------------------

TRIBAL_KNOWLEDGE_TYPES = [
    {
        "type": "Secret Relationship Maps",
        "example": "AMAT always moves 2-3 weeks after ASML results. Not in any database.",
        "mkg_encoding": "Lead-lag edges with temporal weight and historical accuracy",
    },
    {
        "type": "CEO/CFO Calibration",
        "example": "This CFO always sandbagged Q3 by 12%.",
        "mkg_encoding": "Guidance bias model on management entity nodes",
        "precedent": "Fuller & Thaler built a $3B fund on this insight class",
    },
    {
        "type": "Canary Companies",
        "example": "A substrate supplier in Taiwan — 10 analysts cover it globally.",
        "mkg_encoding": "Canary flag on entity with alert threshold",
    },
    {
        "type": "Relationship Decay",
        "example": "That JV is still in the database but barely exists operationally.",
        "mkg_encoding": "Automatic edge weight decay function based on signal freshness",
    },
    {
        "type": "Sector Cycle Timing",
        "example": "We're at week 6 of a 14-week semi cycle pattern.",
        "mkg_encoding": "Cyclical temporal annotations on sector-level entities",
    },
    {
        "type": "Regulatory Co-Exposure",
        "example": "Both companies file under the same FERC docket number.",
        "mkg_encoding": "REGULATES edges with shared_docket metadata",
    },
]


# ---------------------------------------------------------------------------
# MiroFish Integration Status
# ---------------------------------------------------------------------------

MIROFISH_INTEGRATION = {
    "summary": (
        "MiroFish is a parallel behavioral simulation layer. MKG provides "
        "structural relationship intelligence (the knowledge graph). "
        "MiroFish provides behavioral simulation — 'How would market "
        "participants actually react?' It runs as a separate sidecar "
        "service with API boundary (AGPL-3.0 license isolation)."
    ),
    "reused_components": [
        {
            "component": "GraphStorage Interface",
            "source": "storage/graph_storage.py",
            "status": "adopted",
            "detail": "Abstract interface adopted → became SQLiteGraphStorage",
        },
        {
            "component": "NER/RE Pipeline",
            "source": "storage/ner_extractor.py",
            "status": "adapted",
            "detail": "Prompts adapted for financial ontology (Company, Facility, Regulation)",
        },
        {
            "component": "Entity Deduplication",
            "source": "Neo4j MERGE pattern",
            "status": "adopted",
            "detail": "ArticleDedup + graph MERGE pattern for canonical names",
        },
        {
            "component": "Hybrid Search",
            "source": "storage/search_service.py",
            "status": "planned",
            "detail": "0.7 vector + 0.3 BM25 — tuning for financial queries",
        },
        {
            "component": "Embedding Service",
            "source": "storage/embedding_service.py",
            "status": "planned",
            "detail": "nomic-embed-text (768d) or OpenAI ada-002",
        },
        {
            "component": "Graph Tools (InsightForge)",
            "source": "services/graph_tools.py",
            "status": "planned",
            "detail": "Sub-question decomposition reusable for graph queries",
        },
    ],
    "future_integration": [
        {
            "req_id": "R-MF2",
            "description": "Shared storage with isolated graph IDs",
            "priority": "P1",
        },
        {
            "req_id": "R-MF3",
            "description": "Cross-graph entity resolution (MKG ↔ MiroFish)",
            "priority": "P1",
        },
        {
            "req_id": "R-MF4",
            "description": "Feed MKG propagation events as MiroFish simulation inputs",
            "priority": "P1",
        },
        {
            "req_id": "R-MF5",
            "description": "MiroFish sentiment evolution → MKG confidence calibration",
            "priority": "P2",
        },
    ],
    "use_cases": [
        {
            "name": "Signal Validation",
            "description": (
                "MKG predicts 'TSMC disruption → NVIDIA impact -12%, confidence "
                "85%.' Feed into MiroFish → simulate 200 market agents reacting → "
                "compare sentiment evolution with MKG's prediction → calibrate."
            ),
        },
        {
            "name": "Scenario Planning",
            "description": (
                "'What if EU bans Chinese EV batteries?' MKG's propagation engine "
                "gives supply chain impact. MiroFish simulates market/political "
                "agent reactions."
            ),
        },
        {
            "name": "Tribal Knowledge Discovery",
            "description": (
                "Give MiroFish agents biases matching known tribal patterns → "
                "observe if simulation results correlate with historical outcomes → "
                "validate tribal knowledge assertions."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# What MKG Is NOT
# ---------------------------------------------------------------------------

NOT_MKG = [
    {"claim": "Not a Bloomberg replacement",
     "reason": "No real-time prices, bond yields, or execution. MKG is relationship intelligence."},
    {"claim": "Not a document search engine",
     "reason": "Not competing with AlphaSense. MKG extracts relationships from documents, not searching them."},
    {"claim": "Not an ERP/procurement tool",
     "reason": "Not replacing SAP Ariba. MKG maps supply chains, doesn't manage purchase orders."},
    {"claim": "Not an execution platform",
     "reason": "No OMS or order routing. Signals are advisory."},
    {"claim": "Not a general-purpose graph database",
     "reason": "Not competing with Neo4j. MKG is a financial intelligence application built on graph infrastructure."},
    {"claim": "Not a Palantir",
     "reason": "Deployable in weeks, not 18 months. Priced for $1-50B AUM, not $5M+ deployments."},
]


# ---------------------------------------------------------------------------
# Novel Capabilities (zero commercial platforms)
# ---------------------------------------------------------------------------

def get_novel_features() -> list[dict]:
    """Return features that exist in zero commercial platforms."""
    return [
        {"id": f.id, "name": f.name, "description": f.description, "category": f.category}
        for f in FEATURES
        if f.is_novel
    ]


def get_features_by_category() -> dict[str, list[dict]]:
    """Return all features grouped by category."""
    result: dict[str, list[dict]] = {}
    for f in FEATURES:
        cat_list = result.setdefault(f.category, [])
        cat_list.append({
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "is_novel": f.is_novel,
            "status": f.status,
        })
    return result


def get_full_profile() -> dict:
    """Return the complete MKG profile for API consumption."""
    return {
        "identity": {
            "tagline": TAGLINE,
            "one_line_niche": ONE_LINE_NICHE,
            "power_statement": POWER_STATEMENT,
            "tribal_knowledge_statement": TRIBAL_KNOWLEDGE_STATEMENT,
        },
        "three_speed_thesis": THREE_SPEED_THESIS,
        "features": get_features_by_category(),
        "novel_capabilities": get_novel_features(),
        "novel_count": len(get_novel_features()),
        "total_features": len(FEATURES),
        "competitors": [
            {
                "name": c.name,
                "tier": c.tier,
                "revenue": c.revenue,
                "price_per_seat": c.price_per_seat,
                "strengths": c.strengths,
                "weaknesses": c.weaknesses,
                "threat_to_mkg": c.threat_to_mkg,
                "threat_timeline": c.threat_timeline,
            }
            for c in COMPETITORS
        ],
        "market": MARKET_DATA,
        "applications": APPLICATION_DOMAINS,
        "tribal_knowledge_types": TRIBAL_KNOWLEDGE_TYPES,
        "mirofish": MIROFISH_INTEGRATION,
        "not_mkg": NOT_MKG,
    }
