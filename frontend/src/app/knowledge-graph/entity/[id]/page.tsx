/**
 * /knowledge-graph/entity/[id] — Entity detail with neighborhood graph.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import { useGraphStore } from '@/store/graphStore';
import type { MKGEntity, MKGEdge, MKGSubgraph } from '@/lib/mkg-types';
import { EntityCard } from '@/components/graph/EntityCard';
import { GraphCanvas } from '@/components/graph/GraphCanvas';
import { FilterPanel } from '@/components/graph/FilterPanel';
import { RelationshipTable } from '@/components/graph/RelationshipTable';
import { EntityLineage } from '@/components/graph/EntityLineage';
import {
  EntityCardSkeleton,
  GraphCanvasSkeleton,
  EntityCardCompactSkeleton,
  RelationshipTableSkeleton,
} from '@/components/graph/GraphSkeletons';
import { EntityDrawer } from '@/components/graph/EntityDrawer';

export default function EntityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const entityId = params.id as string;

  const [entity, setEntity] = useState<MKGEntity | null>(null);
  const [subgraph, setSubgraph] = useState<MKGSubgraph | null>(null);
  const [neighbors, setNeighbors] = useState<MKGEntity[]>([]);
  const [entityEdges, setEntityEdges] = useState<MKGEdge[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [graphDepth, setGraphDepth] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const { pushBreadcrumb, breadcrumbs, filters } = useGraphStore();

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const [e, sg, nb, outEdges, inEdges] = await Promise.all([
          mkgApi.getEntity(entityId),
          mkgApi.getSubgraph(entityId, graphDepth),
          mkgApi.getNeighbors(entityId),
          mkgApi.listEdges(entityId, undefined, undefined, 200),
          mkgApi.listEdges(undefined, entityId, undefined, 200),
        ]);
        setEntity(e);
        setSubgraph(sg);
        setNeighbors(nb);
        // Merge outgoing + incoming, dedup by edge ID
        const edgeMap = new Map<string, MKGEdge>();
        for (const edge of [...outEdges, ...inEdges]) {
          edgeMap.set(edge.id, edge);
        }
        setEntityEdges(Array.from(edgeMap.values()));
        pushBreadcrumb({ id: e.id, name: e.name });
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [entityId, graphDepth, pushBreadcrumb]);

  const { setDrawerEntityId } = useGraphStore();

  const handleNodeClick = useCallback(
    (clicked: MKGEntity) => {
      if (clicked.id !== entityId) {
        setDrawerEntityId(clicked.id);
      }
    },
    [entityId, setDrawerEntityId],
  );

  // Apply filters to subgraph for display
  const filteredSubgraph: MKGSubgraph | null = subgraph
    ? {
        nodes:
          filters.entityTypes.length > 0
            ? subgraph.nodes.filter(
                (n) =>
                  filters.entityTypes.includes(n.entity_type) || n.id === entityId,
              )
            : subgraph.nodes,
        edges: subgraph.edges.filter((e) => {
          if (
            filters.relationTypes.length > 0 &&
            !filters.relationTypes.includes(e.relation_type)
          )
            return false;
          if (e.confidence < filters.confidenceRange[0]) return false;
          return true;
        }),
      }
    : null;

  // Only include nodes that are connected by visible edges
  const visibleNodeIds = new Set<string>();
  if (filteredSubgraph) {
    visibleNodeIds.add(entityId);
    for (const e of filteredSubgraph.edges) {
      visibleNodeIds.add(e.source_id);
      visibleNodeIds.add(e.target_id);
    }
  }
  const displaySubgraph: MKGSubgraph | null = filteredSubgraph
    ? {
        nodes: filteredSubgraph.nodes.filter((n) => visibleNodeIds.has(n.id)),
        edges: filteredSubgraph.edges,
      }
    : null;

  if (isLoading) {
    return (
      <main className="min-h-screen pb-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="h-4 w-48 bg-bg-secondary animate-pulse rounded mb-4" />
          <EntityCardSkeleton />
          <div className="mt-6">
            <GraphCanvasSkeleton />
          </div>
          <div className="mt-6 grid md:grid-cols-2 lg:grid-cols-3 gap-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <EntityCardCompactSkeleton key={i} />
            ))}
          </div>
          <div className="mt-6">
            <RelationshipTableSkeleton rows={4} />
          </div>
        </div>
      </main>
    );
  }

  if (!entity) {
    return (
      <main className="min-h-screen pb-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center">
          <p className="text-text-muted text-sm">Entity not found.</p>
          <Link href="/knowledge-graph" className="text-accent-purple text-sm mt-2 inline-block">
            ← Back to Supply Chain Map
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-4 flex-wrap">
          <Link href="/knowledge-graph" className="hover:text-text-secondary">
            Supply Chain Map
          </Link>
          {breadcrumbs.map((b, i) => (
            <span key={b.id} className="flex items-center gap-1.5">
              <span>›</span>
              {i < breadcrumbs.length - 1 ? (
                <Link
                  href={`/knowledge-graph/entity/${b.id}`}
                  className="hover:text-text-secondary"
                >
                  {b.name}
                </Link>
              ) : (
                <span className="text-text-primary">{b.name}</span>
              )}
            </span>
          ))}
        </nav>

        {/* Entity card */}
        <div className="mb-6">
          <EntityCard entity={entity} neighborCount={neighbors.length} />
        </div>

        {/* Graph toolbar */}
        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <h2 className="text-base font-display font-semibold text-text-primary">
            Connection Graph
          </h2>
          <div className="flex gap-1 ml-auto">
            {[1, 2, 3].map((d) => (
              <button
                key={d}
                onClick={() => setGraphDepth(d)}
                className={`px-3 py-1 text-xs rounded-md border transition-colors
                  ${graphDepth === d
                    ? 'bg-accent-purple/10 text-accent-purple border-accent-purple/30'
                    : 'border-border-default text-text-muted hover:border-border-hover'}`}
              >
                {d} hop{d > 1 ? 's' : ''}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-3 py-1 text-xs rounded-md border transition-colors
              ${showFilters
                ? 'bg-accent-purple/10 text-accent-purple border-accent-purple/30'
                : 'border-border-default text-text-muted hover:border-border-hover'}`}
          >
            Filters
          </button>
        </div>

        {/* Graph + filters layout */}
        <div className="flex gap-4">
          <div className="flex-1 min-w-0">
            {displaySubgraph && displaySubgraph.nodes.length > 0 ? (
              <GraphCanvas
                subgraph={displaySubgraph}
                centerId={entityId}
                onNodeClick={handleNodeClick}
              />
            ) : (
              <div className="h-[500px] rounded-xl border border-border-default bg-bg-primary flex items-center justify-center">
                <p className="text-text-muted text-sm">No connections to display.</p>
              </div>
            )}
          </div>
          {showFilters && (
            <div className="w-64 shrink-0 hidden lg:block">
              <FilterPanel />
            </div>
          )}
        </div>

        {/* Neighbors list (mobile-friendly) */}
        <div className="mt-6">
          <h3 className="text-sm font-display font-semibold text-text-primary mb-3">
            Connected Entities ({neighbors.length})
          </h3>
          {neighbors.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2">
              {neighbors.map((n) => (
                <EntityCard key={n.id} entity={n} compact />
              ))}
            </div>
          ) : (
            <p className="text-text-muted text-sm">No direct connections.</p>
          )}
        </div>

        {/* Relationships table */}
        {entityEdges.length > 0 && (
          <div className="mt-6">
            <RelationshipTable
              edges={entityEdges}
              entityMap={(() => {
                const m = new Map<string, { id: string; name: string; entity_type: string }>();
                if (entity) m.set(entity.id, { id: entity.id, name: entity.name, entity_type: entity.entity_type });
                for (const n of neighbors) {
                  m.set(n.id, { id: n.id, name: n.name, entity_type: n.entity_type });
                }
                // Also use subgraph nodes
                if (subgraph) {
                  for (const n of subgraph.nodes) {
                    if (!m.has(n.id)) m.set(n.id, { id: n.id, name: n.name, entity_type: n.entity_type });
                  }
                }
                return m;
              })()}
              title={`Relationships (${entityEdges.length})`}
            />
          </div>
        )}

        {/* Data Lineage */}
        <div className="mt-6">
          <h3 className="text-sm font-display font-semibold text-text-primary mb-3">
            📜 Data Lineage
          </h3>
          <EntityLineage entityId={entityId} />
        </div>

        {/* Simulate CTA */}
        <div className="mt-6 p-4 rounded-xl border border-dashed border-border-default text-center">
          <Link
            href={`/knowledge-graph/simulate?entity=${entityId}`}
            className="text-sm text-accent-purple hover:text-accent-purple/80 font-medium"
          >
            ⚡ Simulate impact from {entity.name} →
          </Link>
        </div>

        <p className="mt-6 text-xs text-text-muted text-center">
          Supply chain data is AI-extracted and may contain inaccuracies. Not investment advice.
        </p>
      </div>

      <EntityDrawer />
    </main>
  );
}
