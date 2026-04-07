/**
 * MKG REST API client — talks to the Market Knowledge Graph backend.
 *
 * All endpoints proxied through Next.js: /mkg/api/v1/* → MKG backend.
 */

import type {
  MKGEntity,
  MKGEdge,
  MKGSubgraph,
  MKGAlert,
  MKGResponse,
  PropagationResult,
  GraphHealth,
} from './mkg-types';

const MKG_BASE = '/mkg/api/v1';

async function mkgFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${MKG_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`MKG API ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Entities ──

export async function searchEntities(
  query: string,
  entityType?: string,
  limit = 20,
): Promise<MKGEntity[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (entityType) params.set('entity_type', entityType);
  const res = await mkgFetch<MKGResponse<MKGEntity[]>>(
    `/graph/search?${params}`,
  );
  return res.data;
}

export async function getEntity(id: string): Promise<MKGEntity> {
  const res = await mkgFetch<MKGResponse<MKGEntity>>(`/entities/${id}`);
  return res.data;
}

export async function listEntities(
  entityType?: string,
  limit = 100,
  offset = 0,
): Promise<{ data: MKGEntity[]; meta: { count: number } }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (entityType) params.set('entity_type', entityType);
  return mkgFetch(`/entities?${params}`);
}

// ── Edges ──

export async function listEdges(
  sourceId?: string,
  targetId?: string,
  relationType?: string,
  limit = 100,
): Promise<MKGEdge[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (sourceId) params.set('source_id', sourceId);
  if (targetId) params.set('target_id', targetId);
  if (relationType) params.set('relation_type', relationType);
  const res = await mkgFetch<MKGResponse<MKGEdge[]>>(`/edges?${params}`);
  return res.data;
}

// ── Graph ──

export async function getNeighbors(
  entityId: string,
  relationType?: string,
  direction = 'both',
): Promise<MKGEntity[]> {
  const params = new URLSearchParams({ direction });
  if (relationType) params.set('relation_type', relationType);
  const res = await mkgFetch<MKGResponse<MKGEntity[]>>(
    `/graph/neighbors/${entityId}?${params}`,
  );
  return res.data;
}

export async function getSubgraph(
  entityId: string,
  maxDepth = 2,
  relationTypes?: string[],
): Promise<MKGSubgraph> {
  const params = new URLSearchParams({ max_depth: String(maxDepth) });
  if (relationTypes?.length) {
    params.set('relation_types', relationTypes.join(','));
  }
  const res = await mkgFetch<MKGResponse<MKGSubgraph>>(
    `/graph/subgraph/${entityId}?${params}`,
  );
  return res.data;
}

export async function getGraphHealth(): Promise<GraphHealth> {
  const res = await mkgFetch<MKGResponse<GraphHealth>>('/graph/health');
  return res.data;
}

// ── Propagation ──

export async function runPropagation(params: {
  trigger_entity_id: string;
  impact_score?: number;
  max_depth?: number;
  min_impact?: number;
  event_description?: string;
  relation_types?: string[];
}): Promise<PropagationResult> {
  const res = await mkgFetch<MKGResponse<PropagationResult>>('/propagate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
  return res.data;
}

// ── Alerts ──

export async function listAlerts(limit = 10): Promise<MKGAlert[]> {
  const res = await mkgFetch<MKGResponse<MKGAlert[]>>(
    `/alerts?limit=${limit}`,
  );
  return res.data;
}

// ── Lineage ──

export interface EntityLineage {
  entity_id: string;
  source_articles: string[];
  highest_confidence: number;
  extraction_tiers_used: string[];
  data_sources: { source: string; article_id: string; url?: string }[];
}

export async function getEntityLineage(entityId: string): Promise<EntityLineage> {
  const res = await mkgFetch<MKGResponse<EntityLineage>>(
    `/lineage/entity/${entityId}`,
  );
  return res.data;
}

// ── Convenience namespace ──

export const mkgApi = {
  searchEntities,
  getEntity,
  listEntities,
  listEdges,
  getNeighbors,
  getSubgraph,
  getGraphHealth,
  runPropagation,
  listAlerts,
  getEntityLineage,
};
