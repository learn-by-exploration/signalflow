/**
 * /knowledge-graph — main entry: Entity Explorer + quick actions.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGEntity, GraphHealth } from '@/lib/mkg-types';
import { EntitySearch } from '@/components/graph/EntitySearch';
import { EntityCard } from '@/components/graph/EntityCard';
import { EntityDrawer } from '@/components/graph/EntityDrawer';
import { GuidedScenario } from '@/components/graph/GuidedScenario';

export default function KnowledgeGraphPage() {
  const [recentEntities, setRecentEntities] = useState<MKGEntity[]>([]);
  const [health, setHealth] = useState<GraphHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<MKGEntity | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [entities, h] = await Promise.all([
          mkgApi.listEntities(undefined, 12, 0).then((r) => r.data),
          mkgApi.getGraphHealth(),
        ]);
        setRecentEntities(entities);
        setHealth(h);
      } catch {
        // fail silently
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleSearchSelect = useCallback((entity: MKGEntity) => {
    setSelectedEntity(entity);
  }, []);

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-display font-semibold text-text-primary mb-1">
            Supply Chain Map
          </h1>
          <p className="text-sm text-text-muted">
            Explore company connections, trace supply chain risks, and simulate event impacts.
          </p>
        </div>

        {/* Quick stats */}
        {health && (
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary">
              <div className="text-lg font-mono text-text-primary">{health.entity_count?.toLocaleString() ?? 0}</div>
              <div className="text-xs text-text-muted">Entities</div>
            </div>
            <Link
              href="/knowledge-graph/relationships"
              className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary
                         hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
            >
              <div className="text-lg font-mono text-text-primary">{health.edge_count?.toLocaleString() ?? 0}</div>
              <div className="text-xs text-text-muted">Connections →</div>
            </Link>
            <div className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary">
              <div className="text-lg font-mono text-text-primary capitalize">{health.status}</div>
              <div className="text-xs text-text-muted">Status</div>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="mb-6">
          <EntitySearch onSelect={handleSearchSelect} />
        </div>

        {/* Selected entity quick view */}
        {selectedEntity && (
          <div className="mb-6">
            <EntityCard entity={selectedEntity} />
          </div>
        )}

        {/* Quick action cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <Link
            href="/knowledge-graph/simulate"
            className="group p-5 rounded-xl border border-border-default bg-bg-secondary
                       hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
          >
            <div className="text-2xl mb-2">⚡</div>
            <h3 className="text-base font-display font-semibold text-text-primary mb-1 group-hover:text-accent-purple transition-colors">
              Impact Simulator
            </h3>
            <p className="text-sm text-text-muted">
              Simulate &quot;what if&quot; scenarios — trace how an event ripples through supply chains.
            </p>
          </Link>
          <Link
            href="/knowledge-graph/relationships"
            className="group p-5 rounded-xl border border-border-default bg-bg-secondary
                       hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
          >
            <div className="text-2xl mb-2">🔗</div>
            <h3 className="text-base font-display font-semibold text-text-primary mb-1 group-hover:text-accent-purple transition-colors">
              Browse Relationships
            </h3>
            <p className="text-sm text-text-muted">
              Explore all supply chain connections — filter by type, sort by weight and confidence.
            </p>
          </Link>
          <Link
            href="/knowledge-graph/alerts"
            className="group p-5 rounded-xl border border-border-default bg-bg-secondary
                       hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
          >
            <div className="text-2xl mb-2">🚨</div>
            <h3 className="text-base font-display font-semibold text-text-primary mb-1 group-hover:text-accent-purple transition-colors">
              Supply Chain Alerts
            </h3>
            <p className="text-sm text-text-muted">
              AI-generated alerts on disruptions, concentration risks, and supply chain events.
            </p>
          </Link>
        </div>

        {/* Quick action row — stats link */}
        <div className="flex gap-3 mb-8">
          <Link
            href="/knowledge-graph/stats"
            className="px-4 py-2.5 rounded-lg border border-border-default bg-bg-secondary text-sm text-text-secondary
                       hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
          >
            📊 Graph Analytics
          </Link>
        </div>

        {/* Guided Walkthroughs */}
        <div className="mb-8">
          <h2 className="text-lg font-display font-semibold text-text-primary mb-4">
            📚 Getting Started
          </h2>
          <GuidedScenario />
        </div>

        {/* Entity directory */}
        <div>
          <h2 className="text-lg font-display font-semibold text-text-primary mb-4">
            Recent Entities
          </h2>

          {isLoading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-16 rounded-lg bg-bg-secondary animate-pulse" />
              ))}
            </div>
          ) : recentEntities.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {recentEntities.map((entity) => (
                <EntityCard key={entity.id} entity={entity} compact />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-text-muted text-sm">
              No entities in the knowledge graph yet. Seed the graph to get started.
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <p className="mt-8 text-xs text-text-muted text-center">
          Supply chain data is AI-extracted and may contain inaccuracies. Verify independently before making investment decisions.
        </p>
      </div>

      <EntityDrawer />
    </main>
  );
}
