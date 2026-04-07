/**
 * GraphStatsPanel — overview statistics of the knowledge graph.
 *
 * Shows entity/edge counts by type, average confidence/weight,
 * and top-connected entities. Uses existing API endpoints.
 */
'use client';

import { useState, useEffect, useMemo } from 'react';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGEntity, MKGEdge, GraphHealth } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';
import { useGraphStore } from '@/store/graphStore';

interface GraphStats {
  health: GraphHealth;
  entityCounts: Map<string, number>;
  relationCounts: Map<string, number>;
  avgConfidence: number;
  avgWeight: number;
  topEntities: { id: string; name: string; type: string; degree: number }[];
}

export function GraphStatsPanel() {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const setDrawerEntityId = useGraphStore((s) => s.setDrawerEntityId);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [health, entitiesRes, edges] = await Promise.all([
          mkgApi.getGraphHealth(),
          mkgApi.listEntities(undefined, 500, 0),
          mkgApi.listEdges(undefined, undefined, undefined, 500),
        ]);
        if (cancelled) return;

        const entities = entitiesRes.data;

        // Entity counts by type
        const entityCounts = new Map<string, number>();
        for (const e of entities) {
          entityCounts.set(e.entity_type, (entityCounts.get(e.entity_type) || 0) + 1);
        }

        // Relation counts by type
        const relationCounts = new Map<string, number>();
        for (const e of edges) {
          relationCounts.set(e.relation_type, (relationCounts.get(e.relation_type) || 0) + 1);
        }

        // Averages
        const avgConfidence = edges.length > 0
          ? edges.reduce((s, e) => s + e.confidence, 0) / edges.length
          : 0;
        const avgWeight = edges.length > 0
          ? edges.reduce((s, e) => s + e.weight, 0) / edges.length
          : 0;

        // Top entities by degree (connections)
        const degreeMap = new Map<string, number>();
        for (const e of edges) {
          degreeMap.set(e.source_id, (degreeMap.get(e.source_id) || 0) + 1);
          degreeMap.set(e.target_id, (degreeMap.get(e.target_id) || 0) + 1);
        }
        const entityMap = new Map(entities.map((e) => [e.id, e]));
        const topEntities = Array.from(degreeMap.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([id, degree]) => {
            const e = entityMap.get(id);
            return {
              id,
              name: e?.name || id.slice(0, 16),
              type: e?.entity_type || 'Unknown',
              degree,
            };
          });

        setStats({ health, entityCounts, relationCounts, avgConfidence, avgWeight, topEntities });
      } catch {
        // fail silently
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-bg-secondary rounded-xl" />
          ))}
        </div>
        <div className="h-40 bg-bg-secondary rounded-xl" />
      </div>
    );
  }

  if (!stats) {
    return <div className="text-center py-8 text-text-muted text-sm">Failed to load graph stats.</div>;
  }

  const totalEntities = stats.health.entity_count ?? 0;
  const totalEdges = stats.health.edge_count ?? 0;

  return (
    <div className="space-y-6">
      {/* Overview cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatBox label="Entities" value={totalEntities.toLocaleString()} />
        <StatBox label="Connections" value={totalEdges.toLocaleString()} />
        <StatBox label="Avg Confidence" value={`${Math.round(stats.avgConfidence * 100)}%`} />
        <StatBox label="Avg Weight" value={`${Math.round(stats.avgWeight * 100)}%`} />
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {/* Entity types */}
        <div className="rounded-xl border border-border-default bg-bg-secondary p-4">
          <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3">Entity Types</h3>
          <div className="space-y-2">
            {Array.from(stats.entityCounts.entries())
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => {
                const color = ENTITY_TYPE_COLORS[type] || '#6B7280';
                const pct = totalEntities > 0 ? (count / totalEntities) * 100 : 0;
                return (
                  <div key={type} className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs text-text-secondary flex-1">{type}</span>
                    <span className="text-xs font-mono text-text-muted">{count}</span>
                    <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Relation types */}
        <div className="rounded-xl border border-border-default bg-bg-secondary p-4">
          <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3">Relation Types</h3>
          <div className="space-y-2">
            {Array.from(stats.relationCounts.entries())
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => {
                const pct = totalEdges > 0 ? (count / totalEdges) * 100 : 0;
                return (
                  <div key={type} className="flex items-center gap-2">
                    <span className="text-xs text-text-secondary flex-1">
                      {type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-mono text-text-muted">{count}</span>
                    <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-accent-purple"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Most connected */}
        <div className="rounded-xl border border-border-default bg-bg-secondary p-4">
          <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3">
            Most Connected
          </h3>
          <div className="space-y-2">
            {stats.topEntities.map((e, i) => {
              const color = ENTITY_TYPE_COLORS[e.type] || '#6B7280';
              return (
                <button
                  key={e.id}
                  onClick={() => setDrawerEntityId(e.id)}
                  className="w-full text-left flex items-center gap-2 p-2 rounded-lg
                             hover:bg-white/[0.04] transition-colors"
                >
                  <span className="text-xs font-mono text-text-muted w-4">{i + 1}.</span>
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs text-text-primary font-medium flex-1 truncate">
                    {e.name}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">
                    {e.degree} links
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-4 py-3 rounded-xl border border-border-default bg-bg-secondary">
      <div className="text-lg font-mono text-text-primary">{value}</div>
      <div className="text-xs text-text-muted">{label}</div>
    </div>
  );
}
