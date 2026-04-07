/**
 * useMKGQueries — React Query hooks for MKG API calls.
 *
 * Provides typed query hooks with automatic caching, refetching,
 * and loading/error states for all MKG data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mkgApi } from '@/lib/mkg-api';
import type { EntityLineage } from '@/lib/mkg-api';
import type {
  MKGEntity,
  MKGEdge,
  MKGSubgraph,
  MKGAlert,
  GraphHealth,
  PropagationResult,
} from '@/lib/mkg-types';

// ── Query Key Factory ──

export const mkgKeys = {
  all: ['mkg'] as const,
  entities: () => [...mkgKeys.all, 'entities'] as const,
  entityList: (type?: string, limit?: number, offset?: number) =>
    [...mkgKeys.entities(), { type, limit, offset }] as const,
  entityDetail: (id: string) => [...mkgKeys.entities(), id] as const,
  entitySearch: (query: string, type?: string) =>
    [...mkgKeys.entities(), 'search', { query, type }] as const,
  edges: () => [...mkgKeys.all, 'edges'] as const,
  edgeList: (sourceId?: string, targetId?: string, relationType?: string) =>
    [...mkgKeys.edges(), { sourceId, targetId, relationType }] as const,
  graph: () => [...mkgKeys.all, 'graph'] as const,
  neighbors: (entityId: string, relationType?: string) =>
    [...mkgKeys.graph(), 'neighbors', entityId, { relationType }] as const,
  subgraph: (entityId: string, depth: number) =>
    [...mkgKeys.graph(), 'subgraph', entityId, depth] as const,
  health: () => [...mkgKeys.graph(), 'health'] as const,
  alerts: (limit?: number) => [...mkgKeys.all, 'alerts', { limit }] as const,
  lineage: (entityId: string) => [...mkgKeys.all, 'lineage', entityId] as const,
};

// ── Entity Hooks ──

export function useEntity(entityId: string) {
  return useQuery({
    queryKey: mkgKeys.entityDetail(entityId),
    queryFn: () => mkgApi.getEntity(entityId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!entityId,
  });
}

export function useEntityList(entityType?: string, limit = 100, offset = 0) {
  return useQuery({
    queryKey: mkgKeys.entityList(entityType, limit, offset),
    queryFn: () => mkgApi.listEntities(entityType, limit, offset),
    staleTime: 5 * 60 * 1000,
  });
}

export function useEntitySearch(query: string, entityType?: string) {
  return useQuery({
    queryKey: mkgKeys.entitySearch(query, entityType),
    queryFn: () => mkgApi.searchEntities(query, entityType),
    staleTime: 2 * 60 * 1000,
    enabled: query.length >= 2,
  });
}

// ── Edge Hooks ──

export function useEdgeList(
  sourceId?: string,
  targetId?: string,
  relationType?: string,
  limit = 100,
) {
  return useQuery({
    queryKey: mkgKeys.edgeList(sourceId, targetId, relationType),
    queryFn: () => mkgApi.listEdges(sourceId, targetId, relationType, limit),
    staleTime: 5 * 60 * 1000,
  });
}

// ── Graph Hooks ──

export function useNeighbors(entityId: string, relationType?: string) {
  return useQuery({
    queryKey: mkgKeys.neighbors(entityId, relationType),
    queryFn: () => mkgApi.getNeighbors(entityId, relationType),
    staleTime: 5 * 60 * 1000,
    enabled: !!entityId,
  });
}

export function useSubgraph(entityId: string, depth = 2) {
  return useQuery({
    queryKey: mkgKeys.subgraph(entityId, depth),
    queryFn: () => mkgApi.getSubgraph(entityId, depth),
    staleTime: 5 * 60 * 1000,
    enabled: !!entityId,
  });
}

export function useGraphHealth() {
  return useQuery({
    queryKey: mkgKeys.health(),
    queryFn: () => mkgApi.getGraphHealth(),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// ── Alert Hooks ──

export function useAlerts(limit = 10) {
  return useQuery({
    queryKey: mkgKeys.alerts(limit),
    queryFn: () => mkgApi.listAlerts(limit),
    staleTime: 60 * 1000, // 1 minute
  });
}

// ── Lineage Hooks ──

export function useEntityLineage(entityId: string) {
  return useQuery({
    queryKey: mkgKeys.lineage(entityId),
    queryFn: () => mkgApi.getEntityLineage(entityId),
    staleTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!entityId,
  });
}

// ── Mutation Hooks ──

export function usePropagation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: mkgApi.runPropagation,
    onSuccess: () => {
      // Invalidate alerts after propagation (may generate new ones)
      queryClient.invalidateQueries({ queryKey: mkgKeys.alerts() });
    },
  });
}
