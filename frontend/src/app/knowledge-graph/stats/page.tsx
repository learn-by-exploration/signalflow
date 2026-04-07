/**
 * /knowledge-graph/stats — Graph analytics and statistics.
 */
'use client';

import Link from 'next/link';
import { GraphStatsPanel } from '@/components/graph/GraphStatsPanel';
import { EntityDrawer } from '@/components/graph/EntityDrawer';

export default function GraphStatsPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-4">
          <Link href="/knowledge-graph" className="hover:text-text-secondary">
            Supply Chain Map
          </Link>
          <span>›</span>
          <span className="text-text-primary">Statistics</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-display font-semibold text-text-primary mb-1">
            📊 Graph Analytics
          </h1>
          <p className="text-sm text-text-muted">
            Overview of the knowledge graph — entity types, relationship distribution, and key hubs.
          </p>
        </div>

        <GraphStatsPanel />

        <p className="mt-8 text-xs text-text-muted text-center">
          Statistics reflect the current state of the knowledge graph.
        </p>
      </div>

      <EntityDrawer />
    </main>
  );
}
