/**
 * /knowledge-graph/simulate — Impact Simulator page.
 */
'use client';

import { useState, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGSubgraph, PropagationResult } from '@/lib/mkg-types';
import { ImpactSimulator } from '@/components/graph/ImpactSimulator';
import { GraphCanvas } from '@/components/graph/GraphCanvas';
import { ScenarioCards } from '@/components/graph/ScenarioCards';
import type { Scenario } from '@/components/graph/ScenarioCards';
import { ImpactTable } from '@/components/graph/ImpactTable';
import { CausalNarratives } from '@/components/graph/CausalNarratives';
import { EntityDrawer } from '@/components/graph/EntityDrawer';

function SimulateContent() {
  const searchParams = useSearchParams();
  const presetEntityId = searchParams.get('entity');

  const [graphData, setGraphData] = useState<{
    subgraph: MKGSubgraph;
    impactMap: Map<string, number>;
    triggerId: string;
  } | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<{
    result: PropagationResult;
    scenario: Scenario;
  } | null>(null);
  const [scenarioTab, setScenarioTab] = useState<'table' | 'narratives'>('table');

  const handleResultsReady = useCallback(
    async (result: PropagationResult, triggerId: string) => {
      // Build impact map from propagation results
      const impactMap = new Map<string, number>();
      for (const item of result.propagation) {
        impactMap.set(item.entity_id, item.impact);
      }
      // Mark trigger entity at max impact
      impactMap.set(triggerId, 1.0);

      // Fetch affected subgraph
      try {
        const sg = await mkgApi.getSubgraph(triggerId, 3);
        setGraphData({ subgraph: sg, impactMap, triggerId });
        setShowGraph(true);
      } catch {
        // Graph view is optional
      }
    },
    [],
  );

  const handleScenarioRun = useCallback(
    async (result: PropagationResult, triggerId: string, scenario: Scenario) => {
      // Build impact map
      const impactMap = new Map<string, number>();
      for (const item of result.propagation) {
        impactMap.set(item.entity_id, item.impact);
      }
      impactMap.set(triggerId, 1.0);

      setScenarioResult({ result, scenario });

      // Fetch subgraph for graph view
      try {
        const sg = await mkgApi.getSubgraph(triggerId, 3);
        setGraphData({ subgraph: sg, impactMap, triggerId });
        setShowGraph(true);
      } catch {
        // Graph is optional
      }
    },
    [],
  );

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-4">
          <Link href="/knowledge-graph" className="hover:text-text-secondary">
            Supply Chain Map
          </Link>
          <span>›</span>
          <span className="text-text-primary">Impact Simulator</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-display font-semibold text-text-primary mb-1">
            ⚡ Impact Simulator
          </h1>
          <p className="text-sm text-text-muted">
            Select a trigger event and trace how it ripples through supply chain connections.
          </p>
        </div>

        {/* Quick Scenarios */}
        <div className="mb-8">
          <ScenarioCards onScenarioRun={handleScenarioRun} />
        </div>

        {/* Scenario results */}
        {scenarioResult && (
          <div className="mb-8 space-y-4">
            <div className="flex items-center gap-3">
              <h3 className="text-base font-display font-semibold text-text-primary">
                {scenarioResult.scenario.emoji} {scenarioResult.scenario.title}
              </h3>
              <span className="text-xs text-text-muted font-mono">
                {scenarioResult.result.impact_table.rows.length} entities affected
              </span>
              <button
                onClick={() => setScenarioResult(null)}
                className="text-xs text-text-muted hover:text-text-secondary ml-auto"
              >
                Clear
              </button>
            </div>
            <div className="flex gap-1 p-1 rounded-lg bg-bg-secondary border border-border-default w-fit">
              <button
                onClick={() => setScenarioTab('table')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                  ${scenarioTab === 'table' ? 'bg-accent-purple text-white' : 'text-text-muted hover:text-text-secondary'}`}
              >
                Impact Table
              </button>
              <button
                onClick={() => setScenarioTab('narratives')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                  ${scenarioTab === 'narratives' ? 'bg-accent-purple text-white' : 'text-text-muted hover:text-text-secondary'}`}
              >
                Chain Analysis
              </button>
            </div>
            {scenarioTab === 'table' && (
              <ImpactTable
                rows={scenarioResult.result.impact_table.rows}
                trigger={scenarioResult.result.impact_table.trigger}
              />
            )}
            {scenarioTab === 'narratives' && (
              <CausalNarratives chains={scenarioResult.result.causal_chains} />
            )}
          </div>
        )}

        {/* Main content */}
        <div className="grid lg:grid-cols-5 gap-6">
          {/* Simulator (3/5 width) */}
          <div className="lg:col-span-3">
            <ImpactSimulator onResultsReady={handleResultsReady} />
          </div>

          {/* Graph visualization (2/5 width) */}
          <div className="lg:col-span-2">
            {showGraph && graphData ? (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-display font-semibold text-text-primary">
                    Impact Graph
                  </h3>
                  <button
                    onClick={() => setShowGraph(false)}
                    className="text-xs text-text-muted hover:text-text-secondary"
                  >
                    Hide
                  </button>
                </div>
                <GraphCanvas
                  subgraph={graphData.subgraph}
                  triggerId={graphData.triggerId}
                  impactMap={graphData.impactMap}
                />
              </div>
            ) : (
              <div className="hidden lg:flex h-[500px] rounded-xl border border-dashed border-border-default items-center justify-center">
                <div className="text-center">
                  <div className="text-3xl mb-2 opacity-30">🕸️</div>
                  <p className="text-sm text-text-muted">
                    Run a simulation to see the<br />impact graph here.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <EntityDrawer />
    </main>
  );
}

export default function SimulatePage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen pb-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="h-8 w-48 bg-bg-secondary animate-pulse rounded mb-4" />
          <div className="h-64 bg-bg-secondary animate-pulse rounded-xl" />
        </div>
      </main>
    }>
      <SimulateContent />
    </Suspense>
  );
}
