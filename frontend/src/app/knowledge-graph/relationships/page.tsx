/**
 * /knowledge-graph/relationships — Browse all relationships in the graph.
 */
'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGEdge, MKGEntity } from '@/lib/mkg-types';
import { RelationshipTable } from '@/components/graph/RelationshipTable';
import { EntityDrawer } from '@/components/graph/EntityDrawer';

interface EntityInfo {
  id: string;
  name: string;
  entity_type: string;
}

export default function RelationshipsPage() {
  const [edges, setEdges] = useState<MKGEdge[]>([]);
  const [entities, setEntities] = useState<MKGEntity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [relationFilter, setRelationFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [edgeData, entityData] = await Promise.all([
          mkgApi.listEdges(undefined, undefined, undefined, 500),
          mkgApi.listEntities(undefined, 500, 0).then((r) => r.data),
        ]);
        setEdges(edgeData);
        setEntities(entityData);
      } catch {
        // fail silently
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  // Build entity lookup map
  const entityMap = useMemo(() => {
    const map = new Map<string, EntityInfo>();
    for (const e of entities) {
      map.set(e.id, { id: e.id, name: e.name, entity_type: e.entity_type });
    }
    return map;
  }, [entities]);

  // Relation type stats
  const relationStats = useMemo(() => {
    const counts = new Map<string, number>();
    for (const e of edges) {
      counts.set(e.relation_type, (counts.get(e.relation_type) || 0) + 1);
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [edges]);

  // Filter edges by entity name search
  const filteredEdges = useMemo(() => {
    if (!entityFilter) return edges;
    const q = entityFilter.toLowerCase();
    return edges.filter((e) => {
      const srcInfo = entityMap.get(e.source_id);
      const tgtInfo = entityMap.get(e.target_id);
      return (
        srcInfo?.name.toLowerCase().includes(q) ||
        tgtInfo?.name.toLowerCase().includes(q) ||
        e.source_id.toLowerCase().includes(q) ||
        e.target_id.toLowerCase().includes(q)
      );
    });
  }, [edges, entityFilter, entityMap]);

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-4">
          <Link href="/knowledge-graph" className="hover:text-text-secondary">
            Supply Chain Map
          </Link>
          <span>›</span>
          <span className="text-text-primary">Relationships</span>
        </nav>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-display font-semibold text-text-primary mb-1">
            All Relationships
          </h1>
          <p className="text-sm text-text-muted">
            Browse every connection in the supply chain knowledge graph.
          </p>
        </div>

        {/* Stats summary */}
        {!isLoading && (
          <div className="flex flex-wrap gap-3 mb-6">
            <div className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary">
              <div className="text-lg font-mono text-text-primary">{edges.length}</div>
              <div className="text-xs text-text-muted">Total Relationships</div>
            </div>
            <div className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary">
              <div className="text-lg font-mono text-text-primary">{relationStats.length}</div>
              <div className="text-xs text-text-muted">Relationship Types</div>
            </div>
            <div className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary">
              <div className="text-lg font-mono text-text-primary">
                {edges.length > 0
                  ? `${(edges.reduce((s, e) => s + e.confidence, 0) / edges.length * 100).toFixed(0)}%`
                  : '—'}
              </div>
              <div className="text-xs text-text-muted">Avg Confidence</div>
            </div>
          </div>
        )}

        {/* Relationship type breakdown */}
        {!isLoading && relationStats.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-display font-semibold text-text-primary mb-3">
              By Type
            </h2>
            <div className="flex flex-wrap gap-2">
              {relationStats.map(([type, count]) => (
                <button
                  key={type}
                  onClick={() => setRelationFilter(relationFilter === type ? '' : type)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors flex items-center gap-2
                    ${relationFilter === type
                      ? 'bg-accent-purple/10 text-accent-purple border-accent-purple/30 font-medium'
                      : 'border-border-default text-text-muted hover:border-border-hover'}`}
                >
                  <span>{type.replace(/_/g, ' ')}</span>
                  <span className="font-mono text-text-muted">{count}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Entity filter */}
        <div className="mb-4">
          <input
            type="text"
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            placeholder="Filter by entity name..."
            className="w-full max-w-md px-4 py-2.5 rounded-lg bg-bg-secondary border border-border-default
                       text-text-primary placeholder-text-muted text-sm
                       focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple"
          />
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 rounded-lg bg-bg-secondary animate-pulse" />
            ))}
          </div>
        ) : (
          <RelationshipTable
            edges={relationFilter ? filteredEdges.filter((e) => e.relation_type === relationFilter) : filteredEdges}
            entityMap={entityMap}
            title={relationFilter ? `${relationFilter.replace(/_/g, ' ')} relationships` : undefined}
          />
        )}

        <p className="mt-8 text-xs text-text-muted text-center">
          Relationships are AI-extracted from financial documents and news. Verify independently.
        </p>
      </div>

      <EntityDrawer />
    </main>
  );
}
