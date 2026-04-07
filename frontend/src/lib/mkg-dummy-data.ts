/**
 * Dummy data fixtures for MKG components.
 *
 * Use these for:
 * - Skeleton / loading-state visual testing
 * - Storybook stories
 * - Component development without a running backend
 * - Unit tests that need realistic data shapes
 *
 * All IDs use deterministic UUIDs so snapshots are stable.
 */

import type {
  MKGEntity,
  MKGEdge,
  MKGSubgraph,
  MKGAlert,
  GraphHealth,
  PropagationResult,
  PropagationItem,
  CausalChainItem,
  ImpactTableRow,
} from './mkg-types';

// ── Entities ──

export const DUMMY_ENTITIES: MKGEntity[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    entity_type: 'company',
    name: 'TSMC',
    canonical_name: 'Taiwan Semiconductor Manufacturing Company',
    tags: ['semiconductor', 'foundry', 'taiwan'],
    created_at: '2026-01-15T08:30:00Z',
    updated_at: '2026-03-20T12:00:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    entity_type: 'company',
    name: 'Samsung Electronics',
    canonical_name: 'Samsung Electronics Co., Ltd.',
    tags: ['semiconductor', 'memory', 'south-korea'],
    created_at: '2026-01-15T08:30:00Z',
    updated_at: '2026-03-18T09:15:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000003',
    entity_type: 'company',
    name: 'Reliance Industries',
    canonical_name: 'Reliance Industries Limited',
    tags: ['conglomerate', 'energy', 'india', 'nse'],
    created_at: '2026-01-16T10:00:00Z',
    updated_at: '2026-03-25T14:30:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000004',
    entity_type: 'sector',
    name: 'Indian IT',
    canonical_name: 'Indian Information Technology Sector',
    tags: ['sector', 'it', 'india'],
    created_at: '2026-01-15T08:30:00Z',
    updated_at: '2026-02-10T11:00:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000005',
    entity_type: 'regulator',
    name: 'RBI',
    canonical_name: 'Reserve Bank of India',
    tags: ['regulator', 'central-bank', 'india'],
    created_at: '2026-01-15T08:30:00Z',
    updated_at: '2026-03-28T16:45:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000006',
    entity_type: 'crypto',
    name: 'BTC',
    canonical_name: 'Bitcoin',
    tags: ['crypto', 'layer-1', 'store-of-value'],
    created_at: '2026-01-15T08:30:00Z',
    updated_at: '2026-04-01T00:00:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000007',
    entity_type: 'company',
    name: 'Infosys',
    canonical_name: 'Infosys Limited',
    tags: ['it-services', 'india', 'nse'],
    created_at: '2026-01-16T10:00:00Z',
    updated_at: '2026-03-22T13:20:00Z',
  },
  {
    id: '00000000-0000-0000-0000-000000000008',
    entity_type: 'commodity',
    name: 'Crude Oil',
    canonical_name: 'Brent Crude Oil',
    tags: ['commodity', 'energy', 'global'],
    created_at: '2026-01-17T09:00:00Z',
    updated_at: '2026-04-02T07:30:00Z',
  },
];

// ── Edges ──

const now = new Date().toISOString();
const oneWeekAgo = new Date(Date.now() - 7 * 86400000).toISOString();
const oneMonthAgo = new Date(Date.now() - 30 * 86400000).toISOString();
const sixMonthsAgo = new Date(Date.now() - 180 * 86400000).toISOString();

export const DUMMY_EDGES: MKGEdge[] = [
  {
    id: 'e0000000-0000-0000-0000-000000000001',
    source_id: '00000000-0000-0000-0000-000000000001',
    target_id: '00000000-0000-0000-0000-000000000002',
    relation_type: 'competes_with',
    weight: 0.85,
    confidence: 0.95,
    direction: 'bidirectional',
    tags: ['semiconductor', 'foundry'],
    valid_from: oneMonthAgo,
    valid_until: null,
    created_at: oneMonthAgo,
    updated_at: oneWeekAgo,
    source: 'reuters_extraction',
  },
  {
    id: 'e0000000-0000-0000-0000-000000000002',
    source_id: '00000000-0000-0000-0000-000000000001',
    target_id: '00000000-0000-0000-0000-000000000007',
    relation_type: 'supplies_to',
    weight: 0.70,
    confidence: 0.88,
    direction: 'directed',
    tags: ['chip-supply'],
    valid_from: sixMonthsAgo,
    valid_until: null,
    created_at: sixMonthsAgo,
    updated_at: oneMonthAgo,
    source: 'seed_curated',
  },
  {
    id: 'e0000000-0000-0000-0000-000000000003',
    source_id: '00000000-0000-0000-0000-000000000005',
    target_id: '00000000-0000-0000-0000-000000000003',
    relation_type: 'regulates',
    weight: 0.90,
    confidence: 0.98,
    direction: 'directed',
    tags: ['regulation', 'monetary-policy'],
    valid_from: sixMonthsAgo,
    valid_until: null,
    created_at: sixMonthsAgo,
    updated_at: now,
    source: null,
  },
  {
    id: 'e0000000-0000-0000-0000-000000000004',
    source_id: '00000000-0000-0000-0000-000000000008',
    target_id: '00000000-0000-0000-0000-000000000003',
    relation_type: 'impacts',
    weight: 0.75,
    confidence: 0.82,
    direction: 'directed',
    tags: ['energy', 'input-cost'],
    valid_from: oneMonthAgo,
    valid_until: null,
    created_at: oneMonthAgo,
    updated_at: oneWeekAgo,
    source: 'claude_extraction',
  },
  {
    id: 'e0000000-0000-0000-0000-000000000005',
    source_id: '00000000-0000-0000-0000-000000000004',
    target_id: '00000000-0000-0000-0000-000000000007',
    relation_type: 'contains',
    weight: 0.95,
    confidence: 0.99,
    direction: 'directed',
    tags: ['sector-member'],
    valid_from: sixMonthsAgo,
    valid_until: null,
    created_at: sixMonthsAgo,
    updated_at: sixMonthsAgo,
    source: 'seed_curated',
  },
  {
    id: 'e0000000-0000-0000-0000-000000000006',
    source_id: '00000000-0000-0000-0000-000000000006',
    target_id: '00000000-0000-0000-0000-000000000003',
    relation_type: 'correlates_with',
    weight: 0.40,
    confidence: 0.55,
    direction: 'bidirectional',
    tags: ['market-sentiment'],
    valid_from: oneWeekAgo,
    valid_until: null,
    created_at: oneWeekAgo,
    updated_at: now,
    source: 'llm_inference',
  },
];

// ── Subgraph ──

export const DUMMY_SUBGRAPH: MKGSubgraph = {
  nodes: DUMMY_ENTITIES.slice(0, 5),
  edges: DUMMY_EDGES.slice(0, 4),
};

// ── Graph Health ──

export const DUMMY_GRAPH_HEALTH: GraphHealth = {
  status: 'healthy',
  backend: 'postgresql',
  entity_count: 48,
  edge_count: 49,
  uptime_seconds: 86400,
};

// ── Propagation ──

export const DUMMY_PROPAGATION_ITEMS: PropagationItem[] = [
  {
    entity_id: '00000000-0000-0000-0000-000000000002',
    impact: 0.85,
    depth: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002'],
    direction: 'downstream',
  },
  {
    entity_id: '00000000-0000-0000-0000-000000000007',
    impact: 0.60,
    depth: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000007'],
    direction: 'downstream',
  },
  {
    entity_id: '00000000-0000-0000-0000-000000000004',
    impact: 0.35,
    depth: 2,
    path: [
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000007',
      '00000000-0000-0000-0000-000000000004',
    ],
    direction: 'downstream',
  },
];

export const DUMMY_CAUSAL_CHAINS: CausalChainItem[] = [
  {
    trigger: '00000000-0000-0000-0000-000000000001',
    trigger_name: 'TSMC',
    trigger_event: 'Major earthquake disrupts fabrication facilities in Hsinchu',
    affected_entity: '00000000-0000-0000-0000-000000000002',
    affected_name: 'Samsung Electronics',
    impact_score: 0.85,
    hops: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002'],
    edge_labels: ['competes_with'],
    narrative:
      'TSMC production halt would temporarily boost Samsung foundry orders as customers diversify supply chains.',
  },
  {
    trigger: '00000000-0000-0000-0000-000000000001',
    trigger_name: 'TSMC',
    trigger_event: 'Major earthquake disrupts fabrication facilities in Hsinchu',
    affected_entity: '00000000-0000-0000-0000-000000000007',
    affected_name: 'Infosys',
    impact_score: 0.60,
    hops: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000007'],
    edge_labels: ['supplies_to'],
    narrative:
      'Chip shortage from TSMC disruption would raise hardware procurement costs for Infosys data centers and client projects.',
  },
  {
    trigger: '00000000-0000-0000-0000-000000000001',
    trigger_name: 'TSMC',
    trigger_event: 'Major earthquake disrupts fabrication facilities in Hsinchu',
    affected_entity: '00000000-0000-0000-0000-000000000004',
    affected_name: 'Indian IT',
    impact_score: 0.35,
    hops: 2,
    path: [
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000007',
      '00000000-0000-0000-0000-000000000004',
    ],
    edge_labels: ['supplies_to', 'contains'],
    narrative:
      'Second-order effect: semiconductor shortage propagates through Infosys to broader Indian IT sector sentiment.',
  },
];

export const DUMMY_IMPACT_TABLE_ROWS: ImpactTableRow[] = [
  {
    rank: 1,
    entity_id: '00000000-0000-0000-0000-000000000002',
    entity_name: 'Samsung Electronics',
    entity_type: 'company',
    impact_score: 0.85,
    impact_pct: 85,
    depth: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002'],
  },
  {
    rank: 2,
    entity_id: '00000000-0000-0000-0000-000000000007',
    entity_name: 'Infosys',
    entity_type: 'company',
    impact_score: 0.60,
    impact_pct: 60,
    depth: 1,
    path: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000007'],
  },
  {
    rank: 3,
    entity_id: '00000000-0000-0000-0000-000000000004',
    entity_name: 'Indian IT',
    entity_type: 'sector',
    impact_score: 0.35,
    impact_pct: 35,
    depth: 2,
    path: [
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000007',
      '00000000-0000-0000-0000-000000000004',
    ],
  },
  {
    rank: 4,
    entity_id: '00000000-0000-0000-0000-000000000003',
    entity_name: 'Reliance Industries',
    entity_type: 'company',
    impact_score: 0.20,
    impact_pct: 20,
    depth: 2,
    path: [
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000002',
      '00000000-0000-0000-0000-000000000003',
    ],
  },
  {
    rank: 5,
    entity_id: '00000000-0000-0000-0000-000000000006',
    entity_name: 'BTC',
    entity_type: 'crypto',
    impact_score: 0.10,
    impact_pct: 10,
    depth: 3,
    path: [
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000003',
      '00000000-0000-0000-0000-000000000006',
    ],
  },
];

export const DUMMY_PROPAGATION_RESULT: PropagationResult = {
  propagation: DUMMY_PROPAGATION_ITEMS,
  causal_chains: DUMMY_CAUSAL_CHAINS,
  impact_table: {
    rows: DUMMY_IMPACT_TABLE_ROWS,
    total: 5,
    trigger: '00000000-0000-0000-0000-000000000001',
  },
};

// ── Alerts ──

export const DUMMY_ALERTS: MKGAlert[] = [
  {
    id: 'a0000000-0000-0000-0000-000000000001',
    severity: 'critical',
    title: 'TSMC Fabrication Disruption',
    message:
      'Major earthquake near Hsinchu has disrupted TSMC fabrication facilities. Impact propagates to 12 downstream entities including Samsung, Infosys, and the broader Indian IT sector.',
    impact_score: 0.92,
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    source_chain: DUMMY_CAUSAL_CHAINS[0],
  },
  {
    id: 'a0000000-0000-0000-0000-000000000002',
    severity: 'high',
    title: 'RBI Rate Hike — Banking Sector Impact',
    message:
      'RBI announced 25bps rate hike. Banking sector margins expected to improve while real estate and auto sectors face headwinds.',
    impact_score: 0.78,
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    source_chain: {
      trigger: '00000000-0000-0000-0000-000000000005',
      trigger_name: 'RBI',
      trigger_event: '25bps repo rate hike',
      affected_entity: '00000000-0000-0000-0000-000000000003',
      affected_name: 'Reliance Industries',
      impact_score: 0.78,
      hops: 1,
      path: ['00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000003'],
      edge_labels: ['regulates'],
      narrative: 'Higher rates increase borrowing costs for Reliance capex plans.',
    },
  },
  {
    id: 'a0000000-0000-0000-0000-000000000003',
    severity: 'medium',
    title: 'Crude Oil Price Surge',
    message:
      'Brent crude crossed $95/barrel. Energy-intensive sectors face margin compression. Beneficial for upstream producers.',
    impact_score: 0.55,
    timestamp: new Date(Date.now() - 14400000).toISOString(),
    source_chain: {
      trigger: '00000000-0000-0000-0000-000000000008',
      trigger_name: 'Crude Oil',
      trigger_event: 'Price surge above $95/barrel',
      affected_entity: '00000000-0000-0000-0000-000000000003',
      affected_name: 'Reliance Industries',
      impact_score: 0.55,
      hops: 1,
      path: ['00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000003'],
      edge_labels: ['impacts'],
      narrative: 'Mixed impact on Reliance — benefits upstream O2C segment, pressures downstream retail.',
    },
  },
  {
    id: 'a0000000-0000-0000-0000-000000000004',
    severity: 'low',
    title: 'BTC-Reliance Correlation Weakening',
    message:
      'Historical correlation between BTC and Reliance Industries has weakened from 0.6 to 0.4 over the past month.',
    impact_score: 0.25,
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    source_chain: {
      trigger: '00000000-0000-0000-0000-000000000006',
      trigger_name: 'BTC',
      trigger_event: 'Correlation shift with Indian equities',
      affected_entity: '00000000-0000-0000-0000-000000000003',
      affected_name: 'Reliance Industries',
      impact_score: 0.25,
      hops: 1,
      path: ['00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000003'],
      edge_labels: ['correlates_with'],
      narrative: 'Decoupling may reduce crypto contagion risk for Indian equity portfolios.',
    },
  },
];

// ── Helpers ──

/** Get a single dummy entity by index (wraps around). */
export function dummyEntity(index = 0): MKGEntity {
  return DUMMY_ENTITIES[index % DUMMY_ENTITIES.length];
}

/** Get a single dummy edge by index (wraps around). */
export function dummyEdge(index = 0): MKGEdge {
  return DUMMY_EDGES[index % DUMMY_EDGES.length];
}

/** Get a single dummy alert by index (wraps around). */
export function dummyAlert(index = 0): MKGAlert {
  return DUMMY_ALERTS[index % DUMMY_ALERTS.length];
}

/** Get N dummy entities starting from the given offset. */
export function dummyEntities(count: number, offset = 0): MKGEntity[] {
  return Array.from({ length: count }, (_, i) => dummyEntity(offset + i));
}

/** Get N dummy edges starting from the given offset. */
export function dummyEdges(count: number, offset = 0): MKGEdge[] {
  return Array.from({ length: count }, (_, i) => dummyEdge(offset + i));
}

/** Build a dummy subgraph with the given entity/edge counts. */
export function dummySubgraph(entityCount = 5, edgeCount = 4): MKGSubgraph {
  return {
    nodes: dummyEntities(entityCount),
    edges: dummyEdges(edgeCount),
  };
}
