/**
 * MKG (Market Knowledge Graph) TypeScript types.
 *
 * Matches the MKG REST API response shapes from mkg/api/routes/*.
 */

// ── Entity ──

export interface MKGEntity {
  id: string;
  entity_type: string;
  name: string;
  canonical_name: string;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  /** Extra properties from JSONB */
  [key: string]: unknown;
}

// ── Edge ──

export interface MKGEdge {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  weight: number;
  confidence: number;
  direction: string;
  tags: string[];
  valid_from: string | null;
  valid_until: string | null;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

// ── Subgraph ──

export interface MKGSubgraph {
  nodes: MKGEntity[];
  edges: MKGEdge[];
}

// ── Propagation ──

export interface PropagationRequest {
  trigger_entity_id: string;
  impact_score?: number;
  max_depth?: number;
  min_impact?: number;
  event_description?: string;
  relation_types?: string[];
}

export interface PropagationItem {
  entity_id: string;
  impact: number;
  depth: number;
  path: string[];
  direction: string;
}

export interface CausalChainItem {
  trigger: string;
  trigger_name: string;
  trigger_event: string;
  affected_entity: string;
  affected_name: string;
  impact_score: number;
  hops: number;
  path: string[];
  edge_labels: string[];
  narrative: string;
}

export interface ImpactTableRow {
  rank: number;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  impact_score: number;
  impact_pct: number;
  depth: number;
  path: string[];
}

export interface ImpactTable {
  rows: ImpactTableRow[];
  total: number;
  trigger: string | null;
}

export interface PropagationResult {
  propagation: PropagationItem[];
  causal_chains: CausalChainItem[];
  impact_table: ImpactTable;
}

// ── Alert ──

export interface MKGAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  impact_score: number;
  timestamp: string;
  source_chain: CausalChainItem;
}

// ── Graph Health ──

export interface GraphHealth {
  status: string;
  backend: string;
  entity_count: number;
  edge_count: number;
  [key: string]: unknown;
}

// ── API Response Envelope ──

export interface MKGResponse<T> {
  data: T;
  meta?: {
    count?: number;
    timestamp?: string;
    [key: string]: unknown;
  };
}

// ── Filter State ──

export interface GraphFilters {
  entityTypes: string[];
  relationTypes: string[];
  confidenceRange: [number, number];
  tags: string[];
}

// ── Severity thresholds ──

export const SEVERITY_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#6B7280',
} as const;

export const ENTITY_TYPE_COLORS: Record<string, string> = {
  Company: '#6366F1',
  Facility: '#06B6D4',
  Country: '#F59E0B',
  Person: '#EC4899',
  Sector: '#10B981',
  Product: '#8B5CF6',
  Regulation: '#F97316',
  Event: '#EF4444',
};
