# MKG Expert Panel Review — Iterations 5 & 6

> **Review Date:** 31 March 2026  
> **Document Under Review:** `core/MKG_REQUIREMENTS.md`  
> **Review Scope:** Full requirements document (Sections 1–15)  
> **Review Type:** Expert Panel — Iterations 5 & 6 of 10  
> **Previous Iterations:** [Iteration 1-2](iteration-1-2.md) (Hedge Fund PM + Supply Chain VP), [Iteration 3-4](iteration-3-4.md) (Graph DB Architect + NLP Scientist)

---

## Cumulative Findings Entering This Iteration

| Expert | Score | Critical Gaps |
|--------|-------|---------------|
| Marcus Chen (Hedge Fund PM) | 7/10 | No portfolio overlay, backtesting must be P0, SOM 10–50x overstated |
| Dr. Priya Sharma (Supply Chain VP) | 6/10 | No BOM-level granularity, no disruption duration, cross-domain data isolation |
| Dr. Kai Müller (Graph DB Architect) | 5/10 | Neo4j CE can't deliver 5+ requirements, temporal versioning unspecified, Decimal impossible, edge embeddings unsupported, no consistency model |
| Dr. Aisha Ibrahim (NLP Scientist) | 4/10 | Tail entity NER at 60–75% F1, RE at 65–75% F1, 4-hop ~24% all-correct, LLM hallucination 8–15%, 13-language NER multi-year, NLP costs ~$10K/month unbudgeted, no evaluation loop |
| **Cumulative** | | 62 new requirements identified, 34 at P0 |

---

## Panel Members — This Iteration

| # | Expert | Role | Perspective |
|---|--------|------|-------------|
| 5 | **Megan Torres** | Enterprise PM & GTM Strategist, 15 years (Palantir → Databricks → own B2B SaaS) | Product-market fit, go-to-market, enterprise sales |
| 6 | **James Wright** | CISO & Financial Compliance Officer, 18 years, ex-CISO Goldman Sachs | Security, regulatory compliance, institutional procurement |

---
---

# EXPERT 5: Megan Torres — Enterprise Product Manager & GTM Strategist

*Background: 5 years at Palantir leading Foundry's financial services GTM ($0→$80M ARR in financial vertical). 4 years at Databricks as Group PM for Data Intelligence products ($200M ARR segment). Then founded and sold a B2B SaaS for supply chain analytics ($12M ARR at exit). Deeply experienced in enterprise sales cycles, buyer psychology, vertical SaaS pricing, and the brutal math of early-stage B2B revenue.*

---

## A. Concept-Requirement Alignment — Score: 3/10

**What the document gets right:**

- The Speed 3 framework is an excellent narrative device. It clearly frames the market gap. At Palantir, we spent millions trying to articulate Foundry's value proposition, and it never had a framework this clean. If I were presenting this to a VC, the Speed 3 slide would be the strongest in the deck.
- The buyer profile table (Section 7) shows real thought about who pays. Most technical founders skip this entirely and build "for everyone." The fact that 12 specific buyer profiles exist, with willingness-to-pay ranges, is better than 95% of pre-product specs I've reviewed.
- The competitive analysis (Section 3.2) correctly identifies the empty quadrant. The positioning is defensible — on paper.

**Why this is a 3/10 despite good narrative:**

The document is a **technology specification masquerading as a product specification.** It describes what to build with extraordinary technical detail (13 languages! 5,000 nodes! Graph attention networks!) but is almost entirely silent on:

- How to sell it
- Who signs the check (not who uses it — who *approves the purchase order*)
- What the minimum product is to close the first deal
- How long enterprise sales cycles actually take
- What procurement requires before they'll sign
- What happens between "demo" and "revenue"

I've seen this exact pattern kill 20+ promising B2B startups. They build an impressive demo. They get VC funding on the demo. They discover that enterprise procurement takes 6–18 months. They run out of runway. The technology was never the problem.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Dual-Vertical Focus is a Startup Killer — STRATEGIC ERROR

The document targets BOTH financial markets AND supply chain intelligence in Year 1. This is the most dangerous strategic mistake in the entire spec.

**Why dual-vertical kills focus:**

| Dimension | Financial Markets | Supply Chain Intelligence |
|-----------|------------------|--------------------------|
| **Buyer** | PM, CIO, Head of Research | VP Supply Chain, CPO, CSCO |
| **Sales motion** | Relationship-driven, conference circuit (SALT, Milken), reference-dependent | RFP-driven, vendor panel, compliance-heavy |
| **Decision timeline** | 3–6 months (fast for enterprise) | 9–18 months (procurement layers) |
| **Data requirements** | Real-time news, filings, events | BOM data, trade data, facility data — completely different |
| **Data isolation** | Portfolio data is top-secret | Supplier data is trade-secret |
| **Success metric** | Alpha (returns vs benchmark) | Disruption avoided (MTTR, cost save) |
| **Competitive displacement** | Bloomberg/AlphaSense/RavenPack (entrenched) | Interos/Resilinc/Everstream (younger) |
| **Pricing psychology** | $/seat/year (individual user) | $/enterprise/year (site license) |
| **Proof of value timeline** | 60–90 days (one market event validates) | 6–12 months (a disruption must happen to prove it works) |
| **Support requirements** | Self-serve + occasional analyst call | Dedicated CSM + onboarding + data integration |

**The problem is not building two features — it's running two sales motions simultaneously.** Each vertical needs:
- Different sales playbooks
- Different demo scripts
- Different reference customers
- Different pricing conversations
- Different onboarding flows
- Different success metrics
- Different marketing content

A 2-person founding team (implied by the spec) cannot execute both. At Palantir, we had *separate 50-person teams* for financial services and supply chain. At Databricks, each vertical had its own PM, sales engineers, and marketing.

**Recommendation:** Pick ONE beachhead vertical. The financial markets vertical is the better choice because:
1. Shorter sales cycle (3–6 months vs 9–18 months)
2. Faster proof of value (one market event validates the product)
3. Higher willingness to pay per seat at lower deal complexity
4. The data requirements (news, filings, transcripts) are all public — no customer data integration needed
5. Reference customers in finance amplify via word-of-mouth (PMs talk at conferences)

Missing requirement:
> **R-PM-1**: Product must define a single beachhead vertical with full go-to-market plan. The non-beachhead vertical is explicitly deprioritized for Year 1. Supply chain features may remain in the product but must not drive roadmap, pricing, or sales strategy until beachhead vertical achieves $300K+ ARR.

### B2. Beachhead Buyer — Only 2 of 12 Profiles Matter

The 12 buyer profiles are intellectually interesting but operationally useless until narrowed to 2–3 beachhead personas. Not all buyers are equal in willingness to pilot, speed of procurement, and referencability.

**Ranking the 6 financial market personas by "beachhead-ability":**

| Persona | Sales Velocity | Champion Power | Reference Value | Beachhead Score |
|---------|---------------|---------------|-----------------|-----------------|
| 3. Event-Driven Fund | ★★★★★ | ★★★★★ | ★★★★ | **#1** |
| 1. Multi-Strategy Hedge Fund PM | ★★★★ | ★★★★ | ★★★★★ | **#2** |
| 4. Credit Risk Analyst | ★★★ | ★★ | ★★★ | **#3** |
| 2. Equity Research Analyst | ★★★ | ★ | ★★★ | #4 |
| 5. Portfolio Risk Manager | ★★ | ★★ | ★★ | #5 |
| 6. Sell-Side Strategist | ★ | ★ | ★★ | #6 |

**Why Event-Driven Fund is #1:**
- They feel the Speed 3 pain *the most* — their entire strategy is trading on cascading events
- The PM has budget authority (typically $100K–$300K/year for data/tools)
- They evaluate tools fast (weeks, not months) because time-to-alpha is their metric
- They're concentrated: there are ~200 event-driven funds globally with >$500M AUM
- One reference customer (e.g., "Used by a top-20 event-driven fund") opens 50 doors

**Why Multi-Strategy HF PM is #2:**
- Similar pain point but more diversified (so evaluation takes longer)
- The "TSMC fab fire" use case in the spec is exactly their workflow
- Many multi-strat funds already have research teams — MKG augments rather than replaces

**Drop personas 5 and 6 entirely.** Portfolio Risk Managers buy risk systems (MSCI, Axioma), not intelligence tools. Sell-Side Strategists don't control budgets and need firm-level procurement.

Missing requirement:
> **R-PM-2**: Beachhead personas are (1) Event-Driven Fund PM and (2) Multi-Strategy Hedge Fund PM. All MVP features, demo scripts, and Year 1 marketing must be validated against these two personas. Other personas are expansion targets for Year 2+.

### B3. The 24-Week Timeline Produces a Demo, Not Revenue — TIMELINE FANTASY

The phase plan (Section 13) gives 24 weeks to reach "end-to-end demo." Here's what actually happens after the demo:

```
Week 24: Demo ready
Week 24-28: First outreach to prospects
Week 28-32: First meetings, NDAs, security questionnaires
Week 32-36: Proof of concept / pilot agreements signed
Week 36-44: POC evaluation period (fund runs MKG alongside existing tools)
Week 44-48: Commercial negotiation, legal review, MSA
Week 48-52: Contract signed, onboarding, initial deployment
Week 52+: First invoice paid

That's 52-60 weeks to first revenue, not 24.
```

**$500K ARR at Year 1 requires 10 enterprise contracts averaging $50K each.** Even with a perfect product and aggressive sales execution:

| Metric | Realistic Estimate |
|--------|-------------------|
| Weeks to demo-ready | 24 |
| Weeks for first meeting | +4 |
| Weeks for first POC | +8 |
| POC-to-close conversion rate | 30% |
| Average deal size | $50K/year |
| Deals needed for $500K ARR | 10 |
| POCs needed at 30% conversion | 34 |
| Meetings needed (10% conversion to POC) | 340 |
| Outreach needed (5% response rate) | 6,800 |

**This is a full-time sales operation.** A technical founder doing outreach while also building the product will achieve maybe 20% of these numbers. Realistic Year 1 ARR: **$50K–$150K** (1–3 paying customers, several pilots).

The previous iterations already flagged the SOM as overstated (consensus: $1M–$3M Year 1). I'm going further: **Year 1 revenue of $500K requires a full-time enterprise salesperson starting no later than Week 16.** If the founder is the only seller, expect $50K–$100K Year 1.

Missing requirements:
> **R-PM-3**: Define revenue timeline with realistic enterprise sales cycle assumptions: minimum 12 weeks from first meeting to POC start, minimum 8 weeks POC, minimum 4 weeks legal/procurement. Year 1 revenue projection must account for a 28-week sales cycle after demo readiness.
>
> **R-PM-4**: Define go-to-market staffing plan. If Year 1 revenue target exceeds $100K, a dedicated enterprise account executive must be budgeted starting no later than 4 months after demo readiness.

### B4. MVP Definition is Missing — WHAT ACTUALLY SHIPS?

The requirements document has ~150 requirements across 60+ R-IDs. No enterprise buyer evaluates 150 features. They evaluate 5–8 capabilities against their specific pain point.

**The MVP for the event-driven fund beachhead:**

| Must Have (MVP) | Nice to Have (v1.1) | Cut (v2.0+) |
|-----------------|---------------------|-------------|
| Semiconductor supply chain graph (500 entities) | Multi-sector coverage | 13-language NER |
| English-only news ingestion (5 sources) | Additional news sources | Multilingual anything |
| NER/RE for Company + Facility + Product | Person/Regulation NER | Tribal knowledge encoding |
| 3 relation types (SUPPLIES_TO, DEPENDS_ON, COMPETES_WITH) | All 7 relation types | GAT-based weight adjustment |
| Rule-based weight adjustment | Decay functions, contradiction | MiroFish simulation integration |
| 3-hop propagation with causal chains | 4-hop, multi-trigger | Historical propagation replay |
| REST API (JSON output) | WebSocket real-time | Interactive graph visualization |
| Watchlist alerts ("my 20 companies") | Full dashboard | Scenario simulation |
| Backtesting for semiconductor events (2023–2025) | Multi-sector backtest | Portfolio overlay (needs OMS integration) |

**This is maybe 40% of the requirements document.** The other 60% is Phase 2+ or should be cut entirely.

Missing requirement:
> **R-PM-5**: Define explicit MVP feature set — maximum 20 requirements that constitute the minimum product for beachhead buyer persona evaluation. All other requirements are explicitly Phase 2+ and must not delay MVP delivery. MVP must be demonstrable within 16 weeks (not 24).

### B5. Pricing Has No Validation — DANGEROUS ASSUMPTION

The pricing table says $50K–$500K/year. This range is so wide it's meaningless. Worse, there's no validation evidence:

**What enterprise buyers actually care about in pricing:**

1. **Value metric** — What are they paying per unit of? Per seat? Per query? Per entity monitored? Per alert? The spec doesn't define a value metric. Without one, pricing conversations are guesswork.

2. **Procurement precedent** — Enterprise buyers compare new spend against existing line items. If MKG replaces nothing (it's additive), the budget must come from somewhere. Where? Is this "data spend" (CIO budget)? "Research tools" (Head of Research budget)? "Risk management" (CRO budget)? Each budget line has different approval authority and ceiling.

3. **Pilot pricing** — No fund pays $50K/year for an unproven tool. Pilots are typically free (30 days), deeply discounted ($5K–$10K for 90 days), or barter (access in exchange for feedback + referencability). The spec mentions no pilot pricing or land-and-expand strategy.

4. **Competitive anchoring** — Bloomberg is $24K/seat/year. AlphaSense is $30K–$100K/year. RavenPack is $50K–$200K/year. MKG would need to anchor against one of these. For a new product with no track record, the realistic entry price for a first customer is **$2K–$5K/month ($24K–$60K/year)** — at the LOW end of "comparable" tools.

5. **Total cost of ownership** — Buyers at this price point ask: "How much does implementation cost? How long? Do I need to assign internal resources?" If MKG requires API integration, data engineering support, or custom entity configuration, the TCO exceeds the license price. No TCO model exists.

Missing requirements:
> **R-PM-6**: Define pricing model with specific value metric (per seat, per entity monitored, or per query tier). Document competitive anchor pricing. Include pilot/POC pricing tier (free or deeply discounted for 60–90 days).
>
> **R-PM-7**: Define total cost of ownership model including: license fee, implementation/onboarding time, customer time investment, ongoing support requirements, and data integration costs (if any).

### B6. Competitive Moat — "First Mover in Empty Quadrant" is Not a Moat

"We're the first to do X" is a go-to-market advantage, not a competitive moat. First-mover advantage in enterprise software lasts 12–18 months at best. Then:

- **AlphaSense** (>$500M ARR, 400+ engineers) will build graph-based relationship intelligence once MKG proves demand exists. They already have the NER pipeline, the customer base, and the distribution.
- **Bloomberg** has been investing in alternative data. Their "Supply Chain Analysis" product could add propagation capabilities with a 20-person engineering team inside 12 months.
- **Palantir Foundry** already does graph traversal. A financial services customer could configure Foundry for supply chain propagation as a professional services engagement.
- **Two new well-funded startups** will appear within 18 months of MKG's first press coverage. I've watched this happen with every B2B category we created at Palantir.

**Real moats in this space:**
1. **Data moat**: Proprietary supply chain relationships that nobody else has. This takes 3+ years to build.
2. **Network effect**: If customers contribute data back (validated relationships, tribal knowledge), each new customer makes the graph more valuable. But this requires >50 customers to be meaningful.
3. **Accuracy moat**: If MKG achieves >80% propagation accuracy while competitors are at 50%, accuracy becomes the moat. But this requires the evaluation infrastructure that Iteration 4 flagged as missing.
4. **Integration moat**: If MKG is embedded in customer workflows (OMS, risk systems, PMS), switching costs keep them locked in. But this requires deep integration engineering.

None of these moats exist at launch. All of them take 2–5 years to build.

Missing requirement:
> **R-PM-8**: Define competitive moat strategy and 3-year milestone plan. Must specify which moat type (data, network, accuracy, integration) the product will build toward, and what measurable milestones indicate moat formation. "First mover" is not a sustainable moat and must not be relied upon.

### B7. Go-to-Market Motion — COMPLETELY ABSENT

The specification has zero go-to-market strategy. For a product targeting $50K–$500K/year enterprise customers, you need:

**Channel strategy:** Direct sales (required for $50K+ deals — self-serve doesn't work at this price point). This means:
- A sales engineer who can demo and customize
- A sales process (discovery → demo → POC → proposal → negotiation → close)
- CRM and pipeline tracking
- Proposal/contract templates
- Security questionnaire response capability (every enterprise buyer sends one)
- Reference customers for late-stage evaluation

**Marketing strategy:** For financial services, the channels are:
- Industry conferences (SALT, SPC Impact, QuantMinds — $10K–$50K per booth/sponsorship)
- Direct outreach via LinkedIn/email to target personas
- Thought leadership via research papers/blog posts
- Warm introductions from advisors/investors in hedge fund networks

**Pricing strategy:** As discussed in B5 — pilot pricing, land-and-expand, annual contracts.

**Implementation strategy:** Onboarding playbook, time-to-value targets, customer success.

None of this exists in the requirements.

Missing requirements:
> **R-PM-9**: Define go-to-market motion: direct sales with enterprise account executive starting no later than 4 months post-demo. Include: sales process stages, average cycle time per stage, conversion rate targets, and Year 1 pipeline targets.
>
> **R-PM-10**: Define marketing plan and budget for Year 1. Must include: 2–3 target conferences, content marketing cadence, and direct outreach volume targets.

### B8. What Happens When It's Wrong? — No Trust Recovery Plan

This is the question every PM should ask that nobody does: **What happens the first time MKG produces a confidently wrong propagation alert?**

A fund acts on a STRONG impact alert. The propagation chain was based on a hallucinated DEPENDS_ON edge (8–15% hallucination rate from Iteration 4). The fund takes a position. The event doesn't cascade as predicted. The fund loses money.

What happens next?

1. The fund never trusts MKG again (relationship destroyed)
2. They tell 5–10 other PMs at conferences (reputation damage cascades — ironic for a propagation product)
3. If they're litigious, they explore whether MKG has liability

There is no:
- Error correction protocol (how do you tell the customer the signal was wrong?)
- Post-mortem process (how do you analyze why the propagation was wrong and prevent recurrence?)
- Accuracy disclosure (does MKG publish its hit rate?)
- Liability protection (terms of service, no-advice disclaimers)

Missing requirements:
> **R-PM-11**: Define error handling protocol for incorrect high-confidence propagation alerts. Must include: post-mortem analysis process, customer communication template, and accuracy disclosure policy. Every alert must carry a visible accuracy disclaimer and historical hit rate.
>
> **R-PM-12**: Terms of service must explicitly disclaim MKG as investment advice. All outputs must carry regulatory disclaimers meeting SEC/FCA standards for financial information services. Legal review of disclaimer language required before any customer-facing deployment.

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **Section 15**: $500K ARR at Year 1 | Enterprise sales cycles for new-category products average 9–15 months from first contact to first payment. At best, 2–4 customers will be paying by end of Year 1 ($100K–$200K ARR). $500K requires either 10 deals at $50K (impossible in Year 1 without a sales team) or 1–2 deals at $250K (impossible without a track record). |
| **Section 15**: 50+ daily active users | Enterprise deployment means 5–10 users per customer. At 2–3 customers, that's 10–30 users. 50+ DAUs requires 8–10 deployed customers, which is Year 2–3 territory. |
| **Section 7**: 12 buyer profiles addressed | Each persona needs dedicated discovery calls, demo workflows, success criteria, and onboarding. Addressing 12 personas is a product team of 6+ PMs. Focus on 2. |
| **Section 10**: 20 "zero competitor" capabilities at launch | You need 3–5 to win the beachhead. The other 15 are optional. Trying to build all 20 spreads engineering too thin and delays the 5 that matter. |
| **Section 13**: Phase 6 includes "MiroFish Integration" | MiroFish simulation integration is a science project, not an MVP feature. No buyer persona listed it as a decision criterion. Cut it from the first 12 months entirely. |
| **R-OUT3**: Interactive graph visualization (P1) | Hedge fund PMs don't want to pan/zoom a force-directed graph. They want a ranked table: "Top 10 impacted entities, sorted by impact score, with causal chain." Graph visualization is impressive in demos but not used in production by financial professionals. |

### C2. Underspecified

| Requirement | What's Missing |
|-------------|---------------|
| All of Section 7 (Buyer Profiles) | Buyer profiles describe use cases but not the *buying process*: Who is the economic buyer vs the champion? What is the approval chain? What existing tools must MKG integrate with? What's the budget source? |
| Section 15 (Success Metrics) | Revenue target exists but no pipeline metrics: leads → meetings → POCs → deals. No retention target. No NPS target. No time-to-value target. |
| Nowhere | No customer success requirements. Enterprise products need: onboarding playbook, check-in cadence, escalation path, health scoring, churn prevention triggers. |
| Nowhere | No competitive win/loss tracking requirement. If you lose 7 out of 10 POCs, you need to know why — and the product must adapt. |
| Nowhere | No pricing experimentation framework. The first pricing structure will be wrong. The spec needs a mechanism to test and iterate on pricing without re-engineering the product. |

### C3. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| $500K ARR (Section 15) | At what customer count? Average deal size? Gross margin? Revenue ≠ sustainable business without unit economics. |
| 50+ DAUs (Section 15) | What constitutes "active"? Login? API call? Alert consumption only? Dashboard visit? The definition changes the number by 3–5x. |
| >65% prediction accuracy (Section 15) | Accuracy measured by whom? User-reported outcomes? Automated price tracking? What constitutes a "correct" prediction if the target is hit on day 3 but was underwater for days 1–2? |
| 10 enterprise customers (implied) | What constitutes "enterprise customer"? Pilot? Paid POC? Annual contract? MRR threshold? |

---

## D. New Requirements

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| **R-PM-1** | Define single beachhead vertical with full GTM plan. Non-beachhead vertical deprioritized until $300K+ ARR in beachhead. | P0 | Dual-vertical focus kills startups; can't run two enterprise sales motions simultaneously |
| **R-PM-2** | Beachhead personas: (1) Event-Driven Fund PM, (2) Multi-Strategy HF PM. All MVP features validated against these two. | P0 | 10 of 12 personas are expansion targets, not launch targets |
| **R-PM-3** | Revenue timeline with realistic enterprise sales cycle: 28-week average from demo to closed deal. | P0 | $500K Year 1 is fantasy without acknowledging 9–15 month sales cycles |
| **R-PM-4** | GTM staffing plan: dedicated AE budgeted if Year 1 revenue target exceeds $100K. | P1 | Founder-led sales caps at $100K–$150K Year 1 |
| **R-PM-5** | Explicit MVP feature set: maximum 20 requirements for beachhead buyer evaluation. All other reqs are Phase 2+. | P0 | 150+ requirements ≠ MVP; focus is survival |
| **R-PM-6** | Pricing model with value metric, competitive anchoring, and pilot/POC tier. | P0 | "$50K–$500K" range is not a pricing model |
| **R-PM-7** | Total cost of ownership model: license + implementation + customer resources + support. | P1 | Enterprise buyers evaluate TCO, not list price |
| **R-PM-8** | Competitive moat strategy and 3-year milestone plan. Must specify moat type being built. | P1 | First-mover advantage expires in 12–18 months |
| **R-PM-9** | Go-to-market motion definition: sales process, cycle time targets, conversion rates, Year 1 pipeline targets. | P0 | Zero GTM strategy = zero revenue |
| **R-PM-10** | Year 1 marketing plan and budget: target conferences, content cadence, outreach volumes. | P1 | Enterprise buyers don't find you — you find them |
| **R-PM-11** | Error handling protocol for incorrect high-confidence propagation alerts: post-mortem process, customer communication, accuracy disclosure. | P0 | One wrong alert to a hedge fund destroys the product's reputation |
| **R-PM-12** | Terms of service with SEC/FCA-compliant disclaimers. Legal review before any customer deployment. | P0 | Financial information services have regulatory disclaimer requirements |
| **R-PM-13** | Customer success requirements: onboarding playbook, time-to-value targets (< 14 days to first valuable alert), health scoring, escalation path. | P1 | Enterprise churn without CS infrastructure approaches 40%/year |
| **R-PM-14** | Competitive win/loss tracking: structured post-mortem for every lost deal or failed POC. Product roadmap must respond to loss patterns. | P1 | Product must evolve based on market signal, not internal assumptions |
| **R-PM-15** | Pricing experimentation framework: ability to change pricing tiers, value metrics, and packaging without re-engineering the product (feature flags, tier configuration). | P1 | First pricing will be wrong; product must be decoupled from pricing |

---

## E. Architecture Risks — From a Product-Market Perspective

### Risk 1: Technology-Market Fit Gap (CRITICAL)

The spec describes an incredibly sophisticated system: temporal graph versioning, multi-hop propagation, 13-language NER, GAT-based weight adjustment, MiroFish behavioral simulation. This is 5+ years of engineering.

The market doesn't wait 5 years. The window for "first mover in the empty quadrant" is 18–24 months before well-funded competitors enter.

**The gap:** Week 24 produces a demo. Week 52 produces first revenue. Week 78 (Month 18) is when the product is mature enough for enterprise deployment at scale. But by Month 18, a well-funded competitor ($20M+ raised) could have a comparable product with better distribution (existing customer base).

**The math:** If MKG raises $2M seed at Month 6, that gives 18–24 months of runway. At $186K+/year infrastructure cost (cumulative from previous iterations), $120K+/year for a sales hire, and founder salary, the burn rate is $400K–$600K/year. $2M gives 3–4 years of runway but only 18–24 months of competitive moat.

**Probability:** 70% chance a well-funded competitor appears within 24 months.  
**Impact:** If MKG doesn't have 5+ paying customers and a data/accuracy moat by then, the market opportunity closes.  
**Mitigation:** Ship MVP in 16 weeks (not 24). Cut scope aggressively. Prioritize features that build data moat (customer-contributed relationships, validated edges) over technological sophistication.

### Risk 2: The Product Is Built for the Builder, Not the Buyer (HIGH)

The spec reads like it was written by someone who loves knowledge graphs, NLP, and financial data. The buyer personas are listed but the product is designed around the *technology*, not around *buyer workflows*.

A hedge fund PM's actual workflow:
1. Event hits (TSMC fab fire)
2. PM needs to know: "Do I have exposure? How much? Through whom?"
3. PM needs actionable intelligence in <5 minutes
4. PM discusses with analyst, decides to hedge/exit/add
5. PM needs audit trail for risk committee

The spec answers step 3 but ignores steps 1, 2, 4, and 5. There's no:
- Integration with where PMs already live (Bloomberg Terminal, email, Slack, Symphony)
- Integration with portfolio management systems (where step 2 happens)
- Collaborative features (step 4 — sharing analysis with analysts)
- Report generation for risk committees (step 5)

**Probability:** 60% chance early users say "this is cool but doesn't fit my workflow."  
**Impact:** POC failure → no conversion → no reference customers → death spiral.  
**Mitigation:** R-PM-13 (customer success). More importantly: before writing code, do 20 discovery calls with target personas. Understand their actual workflows. Map MKG's features to their existing tools and processes. Build integration points, not features.

### Risk 3: The "Aha Moment" Requires a Market Event (MEDIUM)

MKG's value is demonstrated when a supply chain event happens and the propagation engine correctly predicts cascading impact. But market events are unpredictable. During a POC:

- If a relevant event happens → MKG demonstrates value → POC converts
- If no relevant event happens → MKG sits idle → POC expires → "Nice tool but we didn't see the value"

**This is the fundamental challenge of event-driven intelligence products.** At Palantir, we solved this with simulation: "Here's what Gotham would have found if the Boston Marathon bombing happened during your evaluation period." MKG has a version of this in the backtest capability, but it's P2.

**Probability:** 50% chance a POC period has no relevant market event.  
**Impact:** 50% unnecessary POC failure rate.  
**Mitigation:** (1) Upgrade backtesting to P0 (consensus from Iteration 1). (2) Run every POC with a "what would have happened" replay of the last 3 major supply chain events (TSMC earthquake Feb 2024, chip shortage 2021, Suez Canal blockage 2021). This is the sales engineer's demo, not a product feature.

---

## F. Critical Questions — Make or Break

1. **"Have you done 20 discovery calls with event-driven fund PMs?"** If not, every assumption about buyer pain, willingness to pay, and feature priority is unvalidated. The entire product spec is a hypothesis. At this stage, the #1 investment should be market validation, not engineering. You need 20 conversations with the target buyer to know if the Speed 3 narrative resonates with people who would actually pay for it.

2. **"What is the minimum product that would convince one event-driven fund PM to pay $24K/year?"** Not $50K, not $100K — what would convince them to pay Bloomberg-equivalent pricing for one seat? If the answer requires more than 16 weeks of engineering, you're building too much.

3. **"Who is your sales person?"** Enterprise B2B at $50K+ ACV cannot be sold founder-only beyond the first 2–3 deals. Do you have a plan to hire a sales engineer who understands financial markets and can run a technical demo? This person costs $150K–$250K/year (base + OTE).

4. **"What is your planned raise, and when?"** The spec describes $186K+/year in infrastructure alone (from previous iterations). Plus engineering salaries, sales, marketing. Total burn: $500K–$800K/year minimum. How is this funded? At what milestone will you raise, and how much?

5. **"Can you demo this to a hedge fund PM today?"** Not in 24 weeks — today. Even a mockup, a slide deck, a Figma prototype. If you can't show the buyer what they'll get, you can't validate whether they want it. Build the demo first, then build the product.

---
---

# EXPERT 6: James Wright — CISO & Financial Compliance Officer

*Background: 18 years in financial services security. 8 years at Goldman Sachs (VP → SVP in Information Security), then CISO at two mid-sized hedge funds ($5B and $12B AUM). Now runs a compliance advisory practice serving fintechs selling to institutional buyers. Has personally evaluated 200+ vendor security assessments for hedge fund and bank procurement. Holds CISSP, CISM, and CRISC certifications. Member of ISAC-FI (Financial Services Information Sharing and Analysis Council).*

---

## A. Concept-Requirement Alignment — Score: 3/10

**What the security section gets right:**
- JWT authentication is a reasonable choice for API security (R-SEC1)
- Audit logging of graph mutations is essential (R-SEC4)
- Encryption at rest and in transit is table stakes, correctly included (R-SEC5)
- Rate limiting is good (R-SEC6)
- Prompt injection prevention is forward-thinking and necessary for LLM-based systems (R-SEC3)
- "No PII in graph" is a reasonable aspiration (R-SEC7)

**Why this is a 3/10:**

The security section reads like a developer's checklist, not an institutional security posture. It covers the basics that would satisfy a SaaS startup serving SMBs. But MKG's target buyers are **hedge funds and large enterprises** — the most security-paranoid buyers in the commercial world.

When I was CISO at Goldman, every vendor went through:
1. Initial security questionnaire (200+ questions, SIG or CAIQ format)
2. Penetration test report review
3. SOC 2 Type II report review
4. Architecture review by internal security engineering
5. Legal review of data handling practices
6. Data classification and handling confirmation
7. Incident response plan review
8. Business continuity and DR plan review
9. Subprocessor review (who else touches the data?)
10. Annual re-certification

MKG's current security specification would fail at step 1. Let me be very specific about why.

---

## B. Gap Analysis — Critical Missing Requirements

### B1. Security Certifications — TABLE STAKES FOR INSTITUTIONAL SALES

No hedge fund with >$1B AUM and no OEM with a public company parent will procure MKG without at minimum:

| Certification | What It Is | Required For | Estimated Cost | Timeline |
|--------------|-----------|-------------|---------------|----------|
| **SOC 2 Type I** | Point-in-time control attestation | Any enterprise procurement | $30K–$80K | 3–6 months |
| **SOC 2 Type II** | 6-month operational attestation | Ongoing compliance | $40K–$100K/year | 6–12 months after Type I |
| **Penetration Test** | Annual third-party pentest | Enterprise security review | $15K–$40K/year | 2–4 weeks |
| **ISO 27001** | Information security management system | European enterprises, some US | $30K–$60K + ongoing | 6–12 months |
| **VAPT Report** | Vulnerability Assessment + Pen Test | Indian financial institutions | $10K–$25K | 2–3 weeks |

**The bare minimum for Year 1 sales:**
1. SOC 2 Type I report (achievable in 3–6 months with a compliance automation platform like Vanta, Drata, or Secureframe)
2. Annual penetration test by a reputable firm (NCC Group, Bishop Fox, Coalfire)
3. Formal information security policy document

**Without SOC 2 Type I, MKG cannot pass procurement at any institutional buyer.** Full stop. I have rejected 100+ vendors at Goldman and at both hedge funds I served as CISO for lacking SOC 2. It is not negotiable.

Missing requirements:
> **R-SEC-8**: SOC 2 Type I attestation must be achieved within 6 months of first customer deployment. SOC 2 Type II attestation within 18 months. Budget: $50K–$100K Year 1.
>
> **R-SEC-9**: Annual penetration test by a qualified third-party firm. Report must be shareable with prospective customers under NDA. Budget: $15K–$40K/year.
>
> **R-SEC-10**: Formal Information Security Policy document covering: access management, data classification, incident response, vulnerability management, change management, business continuity, vendor management, and acceptable use. Must be board-approved (or founder-approved) and version-controlled.

### B2. Cross-Domain Data Isolation — INFORMATION BARRIERS ARE NON-NEGOTIABLE

MKG's architecture puts financial intelligence (hedge fund portfolio implications) and supply chain intelligence (OEM supplier data) in the **same graph database**. This is the single most dangerous security decision in the entire specification.

**Why this matters:**

**Scenario 1 — Insider Trading Risk:**
- Hedge Fund A subscribes to MKG. Their portfolio positions are overlaid on the graph (per Iteration 1's R-PORT requirement).
- OEM X subscribes to MKG. They input their Tier 2/3 supplier relationships (proprietary data).
- MKG's propagation engine uses OEM X's supplier data to generate impact alerts for Hedge Fund A's portfolio.
- Hedge Fund A now has advance knowledge of supply chain disruptions affecting OEM X — knowledge derived from OEM X's proprietary data.
- **This is potentially material non-public information (MNPI).** If Hedge Fund A trades on it, this could constitute insider trading under SEC Rule 10b-5.

**Scenario 2 — Data Leakage Between Competitors:**
- Competitor Hedge Fund B also subscribes. The same graph processing that serves Fund A also serves Fund B.
- If MKG's confidence scores or alert timing differ between Fund A and Fund B for the same event, one fund has an information advantage created by the platform — not by their own analysis.
- **This creates a duty of fairness that MKG is not structured to fulfill.**

**Scenario 3 — Regulatory Scrutiny:**
- A regulator (SEC, FCA, ESMA) investigates algorithmic trading patterns and subpoenas MKG's data.
- MKG must demonstrate that no client received MNPI derived from another client's proprietary data.
- Without architectural isolation, this demonstration is impossible.

**What institutional clients actually require:**

At Goldman, every data vendor who handled data from multiple clients was required to:
1. **Logically isolate** client data with provable separation (not just `WHERE client_id = X`)
2. **Physically isolate** sensitive data (separate databases, separate encryption keys)
3. **Demonstrate isolation** via penetration test (tester with Client A credentials attempts to access Client B data)
4. **No cross-pollination** — intelligence generated for Client A must not be influenced by Client B's proprietary inputs
5. **Audit trail** showing which client data contributed to which outputs

The current architecture (single Neo4j instance, property-level graph_id isolation) fails all 5 requirements. Iteration 3's Dr. Müller already flagged this — Neo4j CE doesn't support multi-database, and property-level isolation is one missing `WHERE` clause away from a data breach.

Missing requirements:
> **R-SEC-11**: Multi-tenant data isolation architecture must provide provable separation between client data. Options: (a) separate Neo4j instances per client, (b) Neo4j Enterprise with multi-database, (c) client data never touches the shared graph (client-specific views only). Architecture decision must pass penetration test validation.
>
> **R-SEC-12**: Information barrier specification: if MKG serves both buy-side (hedge funds) and corporate (OEMs) clients, proprietary input data from corporate clients must NEVER influence outputs delivered to buy-side clients. This requires separate data processing pipelines, not just access control.
>
> **R-SEC-13**: No client portfolio positions or proprietary supplier data may be stored in the shared knowledge graph. Client-specific data must reside in client-isolated storage (separate databases or encrypted, client-keyed tables).

### B3. LLM Data Leakage to Third Parties — CRITICAL FOR INSTITUTIONAL CLIENTS

MKG sends financial data to Anthropic's Claude API for NER/RE, sentiment analysis, and reasoning. This means:

1. **News articles about client-watched entities** are sent to Anthropic's servers.
2. **Entity names and relationships** are in Claude prompts.
3. If portfolio overlay is implemented (R-PORT), **client portfolio positions** could be referenced in Claude prompts for reasoning.
4. Anthropic's data retention policy determines whether this data persists in their systems.

**Institutional client concerns:**

| Concern | Reality |
|---------|---------|
| "Does Anthropic see our data?" | Yes — all Claude API inputs are processed by Anthropic's infrastructure. |
| "Does Anthropic retain our data?" | Anthropic's API Terms of Service (as of March 2026) state they do NOT train on API inputs. But data passes through their systems and may be subject to logging, debugging, and legal compliance. |
| "Does Anthropic have access to our portfolio?" | Not if the product is designed correctly. But the current spec doesn't specify what data is and isn't sent to Claude. |
| "What if Anthropic is breached?" | Client entity lists, relationship patterns, and watchlist data would be exposed. |
| "What happens if the US government subpoenas Anthropic?" | API logs including MKG's financial data requests could be disclosed. |

**What institutional clients will require:**

1. **Data processing agreement (DPA)** with Anthropic specifying: no training on inputs, data retention limits, breach notification obligations, data residency guarantees.
2. **Minimization**: Only the minimum necessary data sent to Claude. Never portfolio positions or client identities.
3. **Opt-out / self-hosted option**: Some clients will require that NO data leaves MKG's infrastructure. This means Ollama or self-hosted LLM as a mandatory capability, not a fallback.
4. **Data flow diagram**: A clear document showing exactly what data flows to Anthropic, when, and what controls prevent sensitive data exposure.

Missing requirements:
> **R-SEC-14**: Data processing agreement (DPA) with Anthropic must be established before any client deployment. DPA must cover: no training on inputs, maximum data retention period, breach notification <72 hours, and data residency specification.
>
> **R-SEC-15**: LLM data minimization policy: Claude API calls must NEVER include client portfolio positions, client identity, proprietary client data, or any data classified as "Confidential" or above. Only public-source content (news articles, public filings) may be sent to external LLM APIs.
>
> **R-SEC-16**: Self-hosted LLM capability (Ollama or equivalent) must be available as a deployment option for clients requiring zero external data transmission. This is not a fallback — it is a primary deployment mode for some institutional clients.
>
> **R-SEC-17**: Data flow diagram documenting all external data transmissions (Anthropic Claude, Alpha Vantage, news sources, embedding services). Each flow must specify: what data is sent, data classification, encryption in transit, retention at destination, and client consent requirements.

### B4. MNPI and Market Abuse Risk — POTENTIAL REGULATORY SHOWSTOPPER

MKG's core value proposition is generating **information advantages** — knowing the impact of events before the market prices them in. This puts MKG in a regulatory gray zone.

**Relevant regulations:**

| Regulation | Jurisdiction | Relevance |
|------------|-------------|-----------|
| SEC Rule 10b-5 | United States | Prohibits trading on material non-public information. If MKG's signals constitute MNPI derived from non-public inputs (e.g., proprietary supplier data from OEM clients), users trading on those signals could be in violation. |
| EU Market Abuse Regulation (MAR) | European Union | Article 7 defines "inside information." If MKG aggregates signals from multiple clients and produces insights that constitute inside information, distribution of those insights may be unlawful. |
| FCA MAR | United Kingdom | Similar to EU MAR. Additionally, the FCA has pursued cases against data providers whose products facilitated market abuse. |
| SEBI FUTP Regulations | India | SEBI regulations on unfair trade practices. If MKG targets Indian markets (NIFTY 50 per SignalFlow), SEBI regulatory compliance is required. |

**The key question:** Is MKG an "investment adviser" under SEC regulations?

If MKG provides "advice or analyses concerning securities" to clients who are "natural persons," it may be required to register as an investment adviser under the Investment Advisers Act of 1940. The "publisher's exemion" (which Bloomberg relies on) applies only to general circulation publications, not to customized intelligence targeted at specific portfolios.

**If MKG overlays client portfolios (R-PORT) and generates alerts specific to a client's positions, this looks like personalized investment advice** — which triggers registration requirements, fiduciary duties, and SEC examination authority.

**Practical implications:**
1. Consult a securities law attorney before ANY client deployment
2. Consider structuring MKG as "general market intelligence" (no portfolio overlay) to stay within publisher's exemption
3. Or register as an investment adviser (expensive, heavy compliance burden, but legitimate)
4. At minimum, include robust disclaimers (as noted by R-PM-12 from Iteration 5)

Missing requirements:
> **R-SEC-18**: Legal opinion from a qualified securities attorney on whether MKG's intelligence products constitute "investment advice" under the Investment Advisers Act of 1940 (US), MAR (EU/UK), or SEBI FUTP (India). Must be obtained before first customer deployment.
>
> **R-SEC-19**: If MKG provides portfolio-specific alerts (R-PORT), evaluate whether investment adviser registration is required. If registration is required, budget compliance costs ($100K–$300K setup + $50K–$100K/year ongoing).
>
> **R-SEC-20**: Market abuse prevention framework: MKG must not distribute MNPI derived from Client A's proprietary data to Client B. System must be auditable to demonstrate that all outputs are derived exclusively from public sources or from the querying client's own data.

### B5. "Person" Entities and Privacy Compliance — GDPR/DPDP RISK

The spec defines "Person" as a node type with attributes: name, title, company_affiliations, influence_score. R-SEC7 says "No PII in graph (people tracked as public figures only)."

**Problems:**

1. **"Public figure" is not a defined legal category under GDPR.** The GDPR applies to all "natural persons" regardless of public status. Even the CEO of a Fortune 500 company has GDPR data subject rights if they are an EU resident.

2. **R-SEC7's exclusion is unenforceable.** How does the NER pipeline know if a person extracted from a news article is a "public figure"? A mid-level executive at a Tier 3 supplier is not a public figure but may be mentioned in a trade publication. The NER pipeline will extract their name, title, and company affiliation — which constitutes personal data under GDPR.

3. **Career history tracking ("company_affiliations")** constitutes profiling under GDPR Article 22. If MKG systematically tracks where executives have worked and uses this to infer hidden relationship networks (Section 4.1, Type 2), this is automated profiling of natural persons.

4. **"Influence_score"** calculated for individuals is editorial decision-making about natural persons based on automated processing — arguably a fully automated decision with significant effects under GDPR Article 22.

5. **India's Digital Personal Data Protection Act (DPDP) 2023** also applies if MKG processes data of Indian residents (which it will, given targets like NSE companies and Indian executives).

**Regulatory requirements:**

| Requirement | GDPR Article | Implication for MKG |
|-------------|-------------|-------------------|
| Lawful basis for processing | Art. 6 | Legitimate interest is defensible for public figures, but requires documented assessment |
| Data subject rights (access, erasure, rectification) | Art. 15-17 | Any person in the graph can request to see, correct, or delete their data |
| Data minimization | Art. 5(1)(c) | Only process personal data that is necessary. "Influence_score" may fail this test |
| Automated decision-making | Art. 22 | If influence_score affects outputs visible to clients, individual has right to human review |
| Cross-border transfer | Art. 46 | EU person data stored on non-EU servers requires adequacy decision or SCCs |
| Data Protection Impact Assessment | Art. 35 | Required if processing involves profiling of natural persons at scale |

Missing requirements:
> **R-SEC-21**: GDPR Data Protection Impact Assessment (DPIA) for "Person" entity processing. DPIA must cover: lawful basis (likely legitimate interest under Art. 6(1)(f)), data minimization justification, automated profiling assessment, data subject rights implementation, and cross-border transfer mechanism.
>
> **R-SEC-22**: Data subject rights implementation for Person entities: ability to process access requests (Art. 15), rectification requests (Art. 17), and erasure requests ("right to be forgotten") within 30 days. System must be able to delete or anonymize all data associated with a specific natural person.
>
> **R-SEC-23**: Define "public figure" threshold for Person entity creation. Recommendation: only create Person entities for individuals who are (a) named executive officers in SEC filings, (b) listed in company annual reports, or (c) quoted in 3+ news sources. Document the threshold and apply consistently.

### B6. Data Provenance and Intellectual Property — LEGAL EXPOSURE

MKG ingests data from 50+ sources (R-IA1) including web scraping (R-IA14). The intelligence outputs are derived from these inputs. Legal questions:

1. **Copyright:** Reproducing article text in Claude prompts for NER/RE may constitute copying. Even if the extracted entities/relationships are facts (not copyrightable), the processing pipeline copies copyrighted text. Under US law, this is a gray area (fair use defense is fact-specific). Under EU Database Directive, systematic extraction from proprietary databases is prohibited.

2. **Data licensing:** Financial data from Bloomberg, Reuters, FactSet typically comes with strict redistribution clauses. If MKG ingests data from these sources (even via public-facing articles), the aggregation may constitute a derivative work subject to licensing restrictions.

3. **Web scraping legality:** As noted in Iteration 4 (Risk 5), web scraping has evolving legal status. The hiQ v. LinkedIn case (US) permitted scraping of public data, but the Ryanair v. PR Aviation case (EU) prohibited systematic extraction from databases.

4. **Provenance trail:** Can MKG prove that every intelligence output is derived from legitimate public sources? If a client is challenged by a regulator ("How did you know about this supply chain disruption before it was public?"), MKG must provide a complete provenance chain from public source → NER extraction → graph update → propagation → alert.

Missing requirements:
> **R-SEC-24**: Data source licensing review: every ingestion source must be evaluated for terms of service, redistribution rights, and legal scraping status. Sources requiring licenses must be budgeted. Non-compliant sources must not be used.
>
> **R-SEC-25**: Full provenance chain for every intelligence output: from source article/filing → NER extraction (with source sentence) → graph update → propagation calculation → output/alert. Provenance must be queryable by client request and preservable for regulatory examination.
>
> **R-SEC-26**: Legal opinion on fair use / database right implications of processing copyrighted articles through LLM-based NER/RE pipeline. Must cover US fair use, EU Database Directive, and applicable law for each major source jurisdiction.

### B7. Export Control and Sanctions Compliance — OVERLOOKED RISK

MKG plans multilingual scraping of Chinese, Japanese, Korean, and other sources (R-IA9). MKG tracks semiconductor supply chains involving entities in China, Taiwan, Russia, and other jurisdictions subject to sanctions regimes.

**Relevant regulations:**

| Regulation | Risk |
|------------|------|
| US EAR (Export Administration Regulations) | MKG's intelligence about semiconductor supply chains could be classified as controlled technology information. Sharing analysis of TSMC/SMIC capacity with certain parties could violate EAR. |
| OFAC (Office of Foreign Assets Control) | If MKG creates entity nodes for SDN-listed companies (e.g., Huawei, SMIC in certain contexts), providing intelligence services about these entities to US persons may require OFAC review. |
| EU Anti-Coercion / Russia Sanctions | If MKG tracks Russian entities in the supply chain, providing intelligence about circumvention pathways could violate EU sanctions. |
| BIS Entity List | Providing "knowledge" about Entity List companies (including relationship intelligence) to non-US persons could trigger deemed export concerns. |

**Practical implications:**
- MKG must screen all entity nodes against OFAC SDN and BIS Entity Lists
- Intelligence outputs involving sanctioned entities must carry compliance warnings
- Access restrictions must prevent prohibited persons from querying sanctioned entity data
- The sanctions landscape changes frequently — compliance must be continuously updated

Missing requirements:
> **R-SEC-27**: OFAC/SDN screening of all Company entities in the graph. Sanctioned entities must be flagged and access-restricted. Intelligence outputs involving sanctioned entities must carry compliance warnings.
>
> **R-SEC-28**: Export control assessment for semiconductor supply chain intelligence. Legal opinion on whether MKG's outputs constitute controlled information under EAR for specific entity combinations (e.g., TSMC + SMIC + advanced node capacity analysis).

### B8. RBAC Is Grossly Insufficient — Enterprise Access Control

The spec defines 3 roles: admin, analyst, viewer (R-SEC2). For an enterprise product serving 50+ users across multiple organizations, this is woefully inadequate.

**What institutional buyers actually need:**

| Capability | Current Spec | Enterprise Requirement |
|------------|-------------|----------------------|
| Role granularity | 3 roles | 8–15 roles: super-admin, org-admin, analyst, junior-analyst, viewer, auditor, API-only, external-guest, compliance-officer, data-steward |
| Attribute-based access | None | Access by: entity type, market sector, geography, data sensitivity, source classification |
| Row-level security | None | User A sees only entities in their watchlist/sector. User B sees different entities. |
| Team/group management | None | Teams of analysts share workspaces. Team A cannot see Team B's private annotations. |
| API key management | Not specified | Per-user API keys with separate scopes, rate limits, and audit trails |
| Session management | Basic JWT | SSO/SAML for enterprise IdP integration (Okta, Azure AD, Ping). MFA mandatory. Session timeout configurable. Concurrent session limits. |
| Audit trail granularity | Graph mutations only | Every data access (read), every query, every export must be logged. Not just writes. |
| Data export controls | None | Some data cannot be downloaded/exported (screen-only access for compliance-sensitive data). Export requires approval workflow. |
| Temporal access | None | Grant access to entity data only for a specified date range (compliance restriction). |

**SSO/SAML integration is a hard requirement for enterprise clients.** No institution with >100 employees will allow username/password authentication for a data vendor. They require:
- SAML 2.0 or OIDC integration with their identity provider (Okta, Azure AD, OneLogin)
- Provisioning via SCIM for automated user lifecycle management
- MFA enforcement via their existing MFA provider (Duo, RSA, Microsoft Authenticator)

**Without SSO/SAML, MKG fails the security questionnaire at question 5 of 200.**

Missing requirements:
> **R-SEC-29**: SSO/SAML 2.0 integration with enterprise identity providers (Okta, Azure AD, OneLogin, Ping). MUST be available before first enterprise deployment — this is a procurement gate, not a nice-to-have.
>
> **R-SEC-30**: MFA enforcement for all user accounts. Support for TOTP, WebAuthn/FIDO2, and push-based MFA. Must integrate with client's existing MFA provider via SSO.
>
> **R-SEC-31**: Role-based access control must expand to minimum 8 roles: super-admin, org-admin, analyst, junior-analyst, read-only, auditor, API-only, compliance-officer. Roles must be configurable per client organization.
>
> **R-SEC-32**: Attribute-based access control (ABAC) for entity-level data: access restrictions by entity type, sector, geography, and data sensitivity classification. E.g., "Analyst A can only query semiconductor sector entities."
>
> **R-SEC-33**: Comprehensive audit logging of ALL data access events (not just mutations): queries, views, exports, API calls, search queries, alert deliveries. Logs must be immutable, retained for 7 years (SEC Rule 17a-4 equivalent), and exportable in standard format (CEF, JSON).
>
> **R-SEC-34**: Data export controls: configurable restrictions on data download, copy-paste, screenshot (watermarking), and API bulk extraction. Enterprise clients may require "view-only" access modes for compliance reasons.

### B9. Incident Response and Business Continuity — ABSENT

No incident response plan. No disaster recovery specification. No business continuity requirements. For a product that claims 24/7 operation (R-NF7: 99.5% uptime) and serves financial institutions during market hours, this is a critical omission.

**What institutional procurement requires:**

1. **Incident Response Plan (IRP):** Documented procedure for security incidents. Must include: detection, classification, containment, eradication, recovery, post-incident review. Must specify notification timelines (72 hours for GDPR, "promptly" for SEC, "as soon as practicable" for most MSAs).

2. **Disaster Recovery Plan (DRP):** RPO (Recovery Point Objective) and RTO (Recovery Time Objective) for all system components. For financial intelligence: RPO < 1 hour, RTO < 4 hours during market hours.

3. **Business Continuity Plan (BCP):** What happens if Railway goes down? If Anthropic's API is unavailable? If Neo4j corrupts? For each failure mode, documented recovery procedure and maximum acceptable downtime.

4. **Security incident breach notification:** Contractual obligation to notify clients within 24–72 hours of a data breach. This is a standard MSA clause that every institutional buyer will require.

Missing requirements:
> **R-SEC-35**: Incident Response Plan (IRP) documented and tested annually. Must include: detection via monitoring, severity classification (P1-P4), containment procedures, client notification within 72 hours for data breaches, and post-incident review.
>
> **R-SEC-36**: Disaster Recovery: RPO < 1 hour, RTO < 4 hours during market hours. Must specify recovery procedure for each critical component (Neo4j, PostgreSQL, API, Celery workers). DR plan must be tested quarterly.
>
> **R-SEC-37**: Business Continuity Plan for key dependency failures: Claude API unavailability (fallback to Ollama), Neo4j failure (read-only mode from PostgreSQL cache), Railway outage (multi-region failover or documented RTO). Each failure mode must have a documented response.

### B10. Vendor and Subprocessor Management — MISSING

MKG relies on multiple third-party services:
- Anthropic (Claude API) — processes financial data
- Railway — hosts infrastructure
- Alpha Vantage / Binance / Yahoo Finance — data sources
- Google/Bing — news sources
- Sentry — error monitoring (may capture financial data in error payloads)

**Under GDPR and SOC 2, every subprocessor that handles client data must be:**
1. Listed in a subprocessor register
2. Covered by a Data Processing Agreement
3. Assessed for security posture
4. Subject to client notification if subprocessor changes

**Sentry is particularly concerning:** error monitoring tools routinely capture request bodies, headers, and stack traces that may contain financial data, entity names, or client identifiers. Without explicit data scrubbing, Sentry becomes an uncontrolled copy of sensitive data.

Missing requirements:
> **R-SEC-38**: Subprocessor register documenting all third-party services that process, store, or transmit client data. Each entry must include: data types processed, DPA status, security assessment date, and client notification requirement for subprocessor changes.
>
> **R-SEC-39**: Error monitoring (Sentry) must implement data scrubbing rules to prevent capture of: entity names from client queries, portfolio data, API keys, authentication tokens, and any data classified as Confidential or above.

---

## C. Requirement Challenges

### C1. Unrealistic or Overambitious

| Requirement | Issue |
|-------------|-------|
| **R-SEC2**: 3 roles (admin/analyst/viewer) | Grossly insufficient for enterprise. Enterprise RBAC requires 8–15 roles with attribute-based policies, SSO, and per-organization administration. Implementing proper IAM is a 3–6 month project. |
| **R-SEC7**: "No PII in graph" | Unenforceable as stated. The NER pipeline will extract person names, titles, and company affiliations from news articles. These are PII under GDPR. Need DPIA instead of a blanket prohibition. |
| **R-NF7**: 99.5% uptime on Neo4j CE single-instance | CE has no HA, no read replicas, offline-only backups. 99.5% requires planned maintenance windows, which for financial intelligence must avoid market hours. On a single instance with no failover, an unexpected crash during market hours = unplanned downtime. Achievable with monitoring + auto-restart for non-critical systems, but not for systems where a 4-hour outage during a market event is catastrophic. |
| **R-SC4**: Multi-tenant with isolated graph views per tier | Multi-tenancy with proper data isolation requires either Enterprise multi-database or completely separate deployments per client. Property-level isolation (WHERE client_id = X) fails penetration test scrutiny. |

### C2. Missing Success Criteria

| Requirement | Missing Criterion |
|-------------|-------------------|
| R-SEC1 (JWT auth) | Token expiry policy, refresh token rotation, revocation capability, key rotation schedule. |
| R-SEC4 (Audit logs) | Log retention period, immutability guarantee, access control on logs themselves, tamper evidence. |
| R-SEC5 (Encryption) | Encryption algorithm specification, key management (KMS?), key rotation schedule, client-managed keys option. |
| R-SEC6 (Rate limiting) | Per-user, per-IP, per-API-key limits. Burst handling. Rate limit response format. |
| R-SEC3 (Prompt injection) | What defense techniques? Input sanitization? Output validation? Prompt isolation? Canary tokens? No specification of the actual defense layer. |

---

## D. New Requirements

| Req ID | Requirement | Priority | Rationale |
|--------|-------------|----------|-----------|
| **R-SEC-8** | SOC 2 Type I within 6 months of first deployment. SOC 2 Type II within 18 months. Budget $50K–$100K Year 1. | P0 | Table stakes for institutional procurement; every buyer will ask |
| **R-SEC-9** | Annual third-party penetration test. Report shareable under NDA. Budget $15K–$40K/year. | P0 | Required by every enterprise security questionnaire |
| **R-SEC-10** | Formal Information Security Policy covering 8+ domains. Board/founder-approved, version-controlled. | P0 | Foundation for all other security controls; required for SOC 2 |
| **R-SEC-11** | Multi-tenant data isolation architecture: separate instances, Enterprise multi-database, or client-specific views. Must pass penetration test. | P0 | Property-level isolation fails pentest; unacceptable for institutional clients |
| **R-SEC-12** | Information barrier: proprietary corporate client data must NEVER influence buy-side client outputs. Separate processing pipelines. | P0 | Without this, platform creates MNPI / insider trading liability |
| **R-SEC-13** | No client portfolio positions or proprietary supplier data in shared graph. Client data in isolated storage. | P0 | Data co-mingling creates legal liability and trust failure |
| **R-SEC-14** | DPA with Anthropic: no training on inputs, max retention, breach notification <72hrs, data residency. | P0 | Third-party data processing without DPA violates GDPR and institutional MSAs |
| **R-SEC-15** | LLM data minimization: never send portfolio positions, client identity, or Confidential+ data to Claude API. | P0 | Prevents MNPI leakage through third-party API |
| **R-SEC-16** | Self-hosted LLM (Ollama) as primary deployment mode for clients requiring zero external data transmission. Not a fallback. | P0 | Many institutional clients prohibit ANY data leaving their network |
| **R-SEC-17** | Data flow diagram: all external transmissions with data classification, encryption, retention, and consent requirements. | P0 | Required for SOC 2, security questionnaires, and client trust |
| **R-SEC-18** | Legal opinion on investment adviser registration requirement (SEC/FCA/SEBI). Before first deployment. | P0 | Potential regulatory showstopper; must be resolved before revenue |
| **R-SEC-19** | If portfolio-specific alerts require IA registration, budget $100K–$300K setup + $50K–$100K/year. | P1 | Registration is expensive but may be legally mandatory |
| **R-SEC-20** | Market abuse prevention: outputs derived only from public sources or querying client's own data. Auditable. | P0 | SEC/FCA/ESMA scrutiny of algorithmic intelligence providers is increasing |
| **R-SEC-21** | GDPR DPIA for Person entity processing: lawful basis, minimization, profiling assessment, rights implementation. | P0 | Person entity processing constitutes automated profiling under GDPR |
| **R-SEC-22** | Data subject rights for Person entities: access/rectification/erasure within 30 days. | P0 | GDPR Art. 15-17 compliance; fines for non-compliance up to €20M or 4% revenue |
| **R-SEC-23** | Define "public figure" threshold for Person entity creation with documented criteria. | P1 | Prevents scope creep into general population tracking |
| **R-SEC-24** | Data source licensing review per ingestion source: ToS, redistribution rights, scraping legality. | P0 | Unlicensed data ingestion creates legal exposure |
| **R-SEC-25** | Full provenance chain for every output: source → extraction → graph update → propagation → alert. Queryable and preservable. | P0 | Required for regulatory examination and client trust verification |
| **R-SEC-26** | Legal opinion on fair use / database rights for LLM processing of copyrighted articles. | P1 | Evolving legal landscape; must be assessed before scale |
| **R-SEC-27** | OFAC/SDN screening of all Company entities. Sanctioned entities flagged and access-restricted. | P0 | Providing intelligence services about sanctioned entities creates legal exposure |
| **R-SEC-28** | Export control assessment for semiconductor supply chain intelligence under EAR. | P1 | Advanced semiconductor intelligence may be controlled under EAR |
| **R-SEC-29** | SSO/SAML 2.0 integration. MUST be available before first enterprise deployment. | P0 | Hard procurement gate; no enterprise buys without SSO |
| **R-SEC-30** | MFA enforcement: TOTP, WebAuthn/FIDO2, push-based. Must integrate with client MFA via SSO. | P0 | MFA is baseline requirement since 2020; non-negotiable |
| **R-SEC-31** | RBAC expansion: minimum 8 roles, configurable per organization. | P1 | 3 roles insufficient for enterprise with 50+ users |
| **R-SEC-32** | ABAC for entity-level access: restrictions by sector, geography, data sensitivity. | P1 | Enterprise access control must be granular |
| **R-SEC-33** | Comprehensive audit logging of ALL access events (reads, queries, exports). Immutable. 7-year retention. | P0 | SEC Rule 17a-4 equivalent; institutional buyers require read-access audit |
| **R-SEC-34** | Data export controls: configurable restrictions on download, copy-paste, API bulk extraction. | P1 | Compliance clients require "view-only" modes |
| **R-SEC-35** | Incident Response Plan: documented, tested annually, client notification within 72 hours of breach. | P0 | Required for SOC 2 and every enterprise MSA |
| **R-SEC-36** | Disaster Recovery: RPO <1 hour, RTO <4 hours during market hours. Tested quarterly. | P0 | Financial intelligence during market hours is time-sensitive |
| **R-SEC-37** | Business Continuity Plan: documented response for each key dependency failure (Claude, Neo4j, Railway). | P1 | Single points of failure need documented fallbacks |
| **R-SEC-38** | Subprocessor register: all third parties handling data, DPA status, security assessment, change notification. | P0 | GDPR Article 28; SOC 2 requirement; MSA clause |
| **R-SEC-39** | Error monitoring (Sentry) data scrubbing: prevent capture of entity names, portfolio data, auth tokens. | P0 | Uncontrolled data in monitoring tools is a common breach vector |

---

## E. Architecture Risks — Security Perspective

### Risk 1: Cross-Tenant Data Leakage Creates Regulatory Liability (CRITICAL)

The single Neo4j instance with property-level isolation is architecturally equivalent to a SQL database with a `client_id` column and no row-level security. Any developer who writes a Cypher query without the `WHERE node.client_id = $clientId` filter leaks data across tenants. Any bug in the access control middleware exposes all tenants' data.

For a product handling hedge fund intelligence and corporate supply chain data, a cross-tenant data leak is:
- A contractual breach (MSA violation)
- Potentially an SEC/FCA violation (MNPI distribution)
- A career-ending event for the buyer's CISO who approved the vendor
- Front-page-news material if a hedge fund's positions leak to a competitor

**Probability:** Without Enterprise multi-database or separate instances: 80%+ within 24 months.  
**Impact:** Catastrophic — loss of all clients, potential regulatory action, possible litigation.  
**Mitigation:** R-SEC-11 (separate instances per client). Accept the infrastructure cost.

### Risk 2: LLM-Mediated Data Leakage (HIGH)

Claude API processes data from all clients through the same API key. Even if MKG's internal data isolation is perfect, the Claude API call for Client A's query and Client B's query share the same API endpoint, same model, and (potentially) same context window if batched.

While Anthropic does not train on API inputs, the data passes through their infrastructure. A breach at Anthropic, a government subpoena, or an Anthropic employee with access to API logs could expose financial intelligence for all MKG clients simultaneously.

**Probability:** Low for direct breach, medium for subpoena/regulatory access.  
**Impact:** Total client trust destruction.  
**Mitigation:** R-SEC-16 (self-hosted LLM option). For the highest-sensitivity clients, Claude API must not be used at all.

### Risk 3: Investment Adviser Classification (HIGH)

If MKG is classified as an investment adviser by the SEC, the product must:
- Register with the SEC (or state regulator for <$100M AUM under advisory)
- Appoint a Chief Compliance Officer
- Implement a compliance program (Code of Ethics, insider trading prevention, personal trading restrictions)
- Undergo SEC examination
- Provide Form ADV disclosure to all clients
- Accept fiduciary duty to clients

This changes the entire business model. It adds $200K–$500K/year in compliance costs and fundamentally restricts product design (every feature must be reviewed by compliance before release).

**Probability:** 40% if portfolio overlay is implemented; 15% without it.  
**Impact:** Transformative — either budget for compliance or remove portfolio overlay.  
**Mitigation:** R-SEC-18 (legal opinion). Get the answer before building portfolio features.

### Risk 4: GDPR Enforcement on Person Entity Processing (MEDIUM)

MKG creates Person entities for executives extracted from news articles. Under GDPR:
- Each person has the right to know their data is being processed (Art. 14 notification for data not collected from the individual)
- Each person has the right to erasure (Art. 17)
- Systematic profiling of natural persons without their knowledge triggers DPIA requirements

A GDPR complaint from a European executive whose career history and "influence_score" are tracked in MKG's graph could result in a regulatory investigation. GDPR fines are up to €20M or 4% of global revenue — whichever is higher.

**Probability:** Medium — increases with graph size and visibility. Once an executive discovers they're profiled with an "influence_score," the complaint is likely.  
**Impact:** Significant financial penalty, forced cessation of Person entity processing for EU subjects, reputational damage.  
**Mitigation:** R-SEC-21 (DPIA), R-SEC-22 (data subject rights), R-SEC-23 (public figure threshold). Consider removing "influence_score" property entirely — it is the highest-risk attribute.

### Risk 5: Source Data Licensing Liability (MEDIUM)

If MKG scrapes Reuters or Bloomberg syndicated content for NER/RE without a data license, and then generates intelligence outputs derived from that content, the content owners may:
1. Send cease-and-desist, terminating a key data source
2. Pursue damages for unauthorized commercial use
3. Block MKG's IP addresses, cutting off ingestion

News organizations have become increasingly aggressive about protecting their content from AI scraping (NYT v. OpenAI, 2023–2024).

**Probability:** High — news organizations are actively pursuing scrapers.  
**Impact:** Loss of critical data sources, legal costs.  
**Mitigation:** R-SEC-24 (source licensing review). Budget for licensed data feeds rather than scraping.

---

## F. Critical Questions — Make or Break

1. **"Can you complete a SOC 2 Type I assessment within 6 months of first deployment?"** If not, you cannot sell to institutional buyers. GS, Citadel, Point72, Millennium — none of them will sign a purchase order without SOC 2 or an equivalent attestation. Start the compliance process now, not after the product is built. A compliance automation platform (Vanta: ~$15K/year, Drata: ~$12K/year) can accelerate this.

2. **"Have you consulted a securities attorney about investment adviser classification?"** This is not an optional consultation. If MKG is classified as an investment adviser and is operating without registration, you are committing a federal crime (Section 203A of the Investment Advisers Act). The SEC has prosecuted fintech companies for unregistered advisory activity. Get the legal opinion before building portfolio overlay features.

3. **"How do you prevent information barriers from being breached through the shared graph?"** The scenario is concrete: Hedge Fund A sees a propagation alert that was influenced by OEM X's proprietary supplier data. Neither party consented to this. How does MKG's architecture prevent this? "We filter by client_id" is not an acceptable answer — it must be provably isolated, pen-tested, and architecturally guaranteed.

4. **"What happens when Anthropic receives a government subpoena for Claude API logs?"** Your clients' entity queries, relationship patterns, and watchlist activity are in those logs. Do your terms of service address this? Does your DPA with Anthropic specify notification obligations? Have your clients consented to external LLM processing?

5. **"Have you screened your entity list against OFAC SDN and BIS Entity List?"** If MKG tracks SMIC, Huawei, or entities in sanctioned jurisdictions (Crimea, North Korea, Iran), and US persons use MKG to trade based on intelligence about these entities, you may have export control exposure. This is not theoretical — the semiconductor supply chain is ground zero for US-China tech sanctions.

---
---

# CROSS-EXPERT SYNTHESIS — Iterations 5 & 6

## Areas of Agreement

| Finding | Megan Torres (Product/GTM) | James Wright (CISO/Compliance) | Implication |
|---------|---------------------------|-------------------------------|-------------|
| **The product cannot serve both verticals in Year 1** | Two sales motions, two data models, two types of buyers | Two isolation requirements, two compliance regimes, two security postures | R-PM-1: Pick financial markets as beachhead |
| **$500K Year 1 revenue is fantasy** | Enterprise sales cycles are 9–15 months; realistic: $50K–$150K | SOC 2 alone takes 6 months; can't sell before it's done | Realistic Year 1 revenue: $50K–$100K |
| **The current security spec is insufficient for institutional buyers** | Buyers won't procure without SOC 2, pentest, security policy | Current security = SaaS SMB level, not institutional grade | 10+ hard security requirements gating sales |
| **Portfolio overlay creates regulatory risk** | If personalized alerts = investment advice, registration required | SEC Rule 10b-5 exposure if proprietary data influences signals | Get legal opinion before building portfolio features |
| **The product spec ignores everything after "build"** | No GTM, no sales process, no customer success | No incident response, no DR, no vendor management | Technical spec ≠ product spec ≠ business plan |

## Areas of Divergence

| Topic | Megan Torres | James Wright | Resolution |
|-------|-------------|-------------|------------|
| **Priority of graph visualization** | Cut it — PMs want ranked tables, not interactive graphs | Neutral on UX, cares about screen-capture prevention | Make it P2; if built, add watermarking |
| **MiroFish integration value** | Zero market value — no buyer asked for "behavioral simulation" | Adds attack surface and data isolation complexity | Cut from Year 1 entirely |
| **Self-hosted LLM** | Nice-to-have for sales flexibility | MUST-have for institutional clients who prohibit external data | P0 — some clients literally cannot use Claude API |
| **Biggest risk** | Running out of runway before first revenue | Cross-tenant data leak creating legal liability | Both existential — PMF risk vs compliance risk |

## Cumulative Gap Summary (Iterations 1–6)

| Gap | First Identified | Impact | Status |
|-----|-----------------|--------|--------|
| Portfolio overlay missing | Iteration 1 (Marcus) | SHOW-STOPPER for financial vertical | Needs R-PORT1–R-PORT3, but may trigger IA registration (Iteration 6) |
| BOM-level granularity missing | Iteration 2 (Priya) | SHOW-STOPPER for supply chain vertical | Deprioritized if financial markets = beachhead (Iteration 5) |
| Cross-domain data isolation | Iterations 2, 5, 6 | CRITICAL — regulatory + information barrier | R-SEC-11, R-SEC-12, R-SEC-13: provable isolation required |
| SOM overstated 10–50x | Iterations 1, 2, 5 | Business planning error | Consensus: $50K–$150K Year 1 (further revised down from Iterations 1-2) |
| 24-week plan = demo only | Iterations 1, 2, 5 | Expectation management | First revenue at week 52+, not week 24 |
| Neo4j CE limitations | Iteration 3 (Kai) | ARCHITECTURAL — 5+ requirements undeliverable | R-GRAPH-1: edition decision |
| Temporal versioning unspecified | Iteration 3 (Kai) | ARCHITECTURAL — 3–6 month project | R-GRAPH-2 |
| Decimal precision impossible | Iteration 3 (Kai) | DATA INTEGRITY | R-GRAPH-5 |
| NER/RE accuracy targets missing | Iteration 4 (Aisha) | QUALITY — no measurement = no improvement | R-NLP-1, R-NLP-3 |
| LLM hallucination 8–15% | Iteration 4 (Aisha) | INTEGRITY — poisoned graph | R-NLP-8, R-NLP-9, R-NLP-10 |
| 13-language NER = multi-year | Iteration 4 (Aisha) | SCOPE — blocks launch | R-NLP-13: phase English-first |
| NLP costs ~$10K/month | Iteration 4 (Aisha) | FINANCIAL — unbudgeted | R-NLP-11 |
| No evaluation infrastructure | Iteration 4 (Aisha) | OPERATIONAL | R-NLP-15 |
| **No beachhead vertical selected** | **Iteration 5 (Megan)** | **STRATEGIC — dual-vertical kills focus** | **R-PM-1: pick one** |
| **No GTM strategy** | **Iteration 5 (Megan)** | **EXISTENTIAL — no sales = no revenue** | **R-PM-9: define sales motion** |
| **No MVP defined** | **Iteration 5 (Megan)** | **SCOPE — 150 requirements ≠ MVP** | **R-PM-5: max 20 MVP requirements** |
| **No pricing validation** | **Iteration 5 (Megan)** | **FINANCIAL — pricing range meaningless** | **R-PM-6: define value metric** |
| **SOC 2 / pentest missing** | **Iteration 6 (James)** | **PROCUREMENT GATE — blocks all institutional sales** | **R-SEC-8, R-SEC-9** |
| **SSO/SAML missing** | **Iteration 6 (James)** | **PROCUREMENT GATE — hard stop** | **R-SEC-29** |
| **Information barriers not implemented** | **Iteration 6 (James)** | **REGULATORY — MNPI / insider trading risk** | **R-SEC-12, R-SEC-20** |
| **Investment adviser classification unresolved** | **Iteration 6 (James)** | **REGULATORY SHOWSTOPPER** | **R-SEC-18: legal opinion required** |
| **LLM data leakage to Anthropic** | **Iteration 6 (James)** | **TRUST — institutional clients block Claude API** | **R-SEC-14, R-SEC-15, R-SEC-16** |
| **GDPR non-compliance for Person entities** | **Iteration 6 (James)** | **REGULATORY — €20M fine exposure** | **R-SEC-21, R-SEC-22** |
| **OFAC/sanctions compliance missing** | **Iteration 6 (James)** | **LEGAL — potential criminal exposure** | **R-SEC-27** |
| **No incident response or DR plan** | **Iteration 6 (James)** | **OPERATIONAL — unacceptable for 24/7 system** | **R-SEC-35, R-SEC-36** |

## New Requirements Count

| Iteration | Expert | New Requirements | Critical (P0) |
|-----------|--------|-----------------|---------------|
| 1 | Marcus Chen (Hedge Fund PM) | 15 | 9 |
| 2 | Dr. Priya Sharma (Supply Chain VP) | 15 | 6 |
| 3 | Dr. Kai Müller (Graph DB Architect) | 12 | 7 |
| 4 | Dr. Aisha Ibrahim (NLP/NER Scientist) | 20 | 12 |
| 5 | Megan Torres (Enterprise PM / GTM) | 15 | 7 |
| 6 | James Wright (CISO / Compliance) | 32 | 21 |
| **Total** | | **109** | **62** |

## Top 7 Cumulative Risks (Updated from all 6 experts)

1. **The product fails commercially because there is no go-to-market strategy.** The spec describes what to build but not how to sell. No beachhead vertical selected, no sales motion defined, no pipeline targets, no customer success infrastructure. Technology without distribution is a hobby project. *(NEW — Iteration 5)*

2. **Cross-tenant data leakage creates legal liability.** Property-level isolation on a single Neo4j instance is one missing WHERE clause from disaster. For a product handling hedge fund intelligence and corporate supply chain data simultaneously, a data leak is regulatory catastrophe. *(Escalated — Iterations 2, 3, 6)*

3. **Investment adviser classification as a regulatory showstopper.** If MKG provides personalized portfolio-specific alerts, it may be an unregistered investment adviser — a federal crime. Legal opinion required before building portfolio features. *(NEW — Iteration 6)*

4. **Institutional buyers cannot procure without SOC 2, SSO, and penetration test.** These are non-negotiable procurement gates. Without them, every sales process terminates at the security questionnaire. SOC 2 Type I takes 3–6 months. SSO/SAML implementation takes 4–8 weeks. These must start in parallel with product development, not after. *(NEW — Iteration 6)*

5. **The NLP pipeline produces confident wrong answers.** 8–15% relation hallucination rate + 25–35% RE error rate = a graph with substantial incorrect edges. A 4-hop propagation has ~24% probability of all-correct path. The system will produce authoritative-looking intelligence based on wrong data. *(Iteration 4, corroborated by 5)*

6. **Costs are fatally underspecified.** Infrastructure: $186K+/year (Neo4j + Claude API + compute). Compliance: $95K–$220K Year 1 (SOC 2 + pentest + legal opinions). Sales: $150K–$250K/year for AE. Legal: $50K+ for IA and securities opinions. **Total Year 1 burn: $500K–$800K** before the founder draws salary. *(Cumulative — Iterations 3, 4, 5, 6)*

7. **The 24-week timeline does not produce a sellable product.** Week 24 = demo. Week 24 + SOC 2 (6 months) = Week 48 before security-ready. Week 48 + sales cycle (9–15 months) = Week 84–108 before first revenue. **That's 20–26 months from project start to first dollar.** Revenue targets must align with this reality. *(Cumulative — Iterations 1, 2, 5, 6)*

---

## Recommended Priority Actions (Updated — Cumulative from all 6 experts)

### TIER 1 — Do Before Writing Any Code

1. **GET LEGAL OPINION: Investment adviser classification** — If the answer is "you must register," this fundamentally changes the product design, cost structure, and timeline. Must know before building portfolio features. *(R-SEC-18)*

2. **PICK BEACHHEAD: Financial markets, event-driven fund persona** — Stop designing for 12 buyer profiles and 2 verticals. One persona. One vertical. One value proposition validated through 20 discovery calls. *(R-PM-1, R-PM-2)*

3. **VALIDATE BUYER WILLINGNESS TO PAY** — 20 discovery calls with event-driven fund PMs. Show the Speed 3 framework. Ask: "Would you pay $24K/year for a tool that does this?" If <50% say yes, the product hypothesis is wrong. *(R-PM-6)*

4. **START SOC 2 PROCESS** — Begin compliance automation (Vanta/Drata) on day 1. SOC 2 Type I takes 6 months. Starting this in parallel with product development is the only way to be sales-ready within 12 months. *(R-SEC-8)*

### TIER 2 — Decide Before Building Architecture

5. **DECIDE: Neo4j edition** — CE vs Enterprise vs alternative. This gates data isolation architecture, RBAC, HA, and backup strategy. *(R-GRAPH-1)*

6. **DECIDE: Data isolation architecture** — Separate instances per client, or never store client data in the shared graph. Must be pen-testable. *(R-SEC-11)*

7. **DECIDE: Self-hosted LLM as primary mode** — If institutional clients prohibit Claude API, Ollama is not a fallback — it's the default. Architect accordingly. *(R-SEC-16)*

8. **DEFINE: MVP feature set** — Maximum 20 requirements. Semiconductor supply chain + English only + 3 relation types + rule-based weights + 3-hop propagation + REST API + email/Slack alerts. Everything else is Phase 2+. *(R-PM-5)*

### TIER 3 — Build During Phase 1

9. **IMPLEMENT: SSO/SAML** — Must ship with the MVP. Without SSO, no enterprise client can adopt. Plan 4–8 weeks. *(R-SEC-29, R-SEC-30)*

10. **IMPLEMENT: NER/RE accuracy benchmarks** — Define F1 targets, create 500-article evaluation dataset, build accuracy dashboard. Can't improve what you can't measure. *(R-NLP-1, R-NLP-3, R-NLP-15)*

11. **IMPLEMENT: Hallucination defense** — Span verification + evidence sentences + multi-source corroboration. Non-negotiable for financial intelligence. *(R-NLP-8, R-NLP-9)*

12. **BUDGET: Acknowledge Year 1 costs** — Infrastructure ($186K) + compliance ($150K) + sales ($200K) + legal ($50K) = **$586K+ minimum** + founder salary. Plan fundraising accordingly. *(Cumulative)*

---

*Next iteration: Experts 7 & 8 — Quantitative Research Lead (systematic strategy firm) + Chief Data Officer (financial data vendor)*
