/**
 * ImpactSimulator — "What If?" event simulation tool.
 *
 * User selects a trigger entity + describes an event → runs propagation →
 * displays results in ImpactTable + CausalNarratives + optional graph overlay.
 */
'use client';

import { useState, useCallback } from 'react';
import { mkgApi } from '@/lib/mkg-api';
import { useGraphStore } from '@/store/graphStore';
import type { MKGEntity, PropagationResult } from '@/lib/mkg-types';
import { EntitySearch } from './EntitySearch';
import { ImpactTable } from './ImpactTable';
import { CausalNarratives } from './CausalNarratives';

interface ImpactSimulatorProps {
  onResultsReady?: (result: PropagationResult, triggerId: string) => void;
}

export function ImpactSimulator({ onResultsReady }: ImpactSimulatorProps) {
  const [triggerEntity, setTriggerEntity] = useState<MKGEntity | null>(null);
  const [eventDescription, setEventDescription] = useState('');
  const [maxDepth, setMaxDepth] = useState(4);
  const [minImpact, setMinImpact] = useState(5);
  const [result, setResult] = useState<PropagationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'table' | 'narratives'>('table');

  const { isSimulating, setIsSimulating, setSimulationResult } = useGraphStore();

  const handleSimulate = useCallback(async () => {
    if (!triggerEntity) return;
    setIsSimulating(true);
    setError(null);
    setResult(null);

    try {
      const res = await mkgApi.runPropagation({
        trigger_entity_id: triggerEntity.id,
        impact_score: 1.0,
        max_depth: maxDepth,
        min_impact: minImpact / 100,
        event_description: eventDescription || undefined,
      });
      setResult(res);
      setSimulationResult(res);
      onResultsReady?.(res, triggerEntity.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setIsSimulating(false);
    }
  }, [triggerEntity, eventDescription, maxDepth, minImpact, setIsSimulating, setSimulationResult, onResultsReady]);

  const handleReset = () => {
    setTriggerEntity(null);
    setEventDescription('');
    setResult(null);
    setError(null);
    setSimulationResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Input section */}
      <div className="rounded-xl border border-border-default bg-bg-secondary p-5">
        <h3 className="text-base font-display font-semibold text-text-primary mb-4">
          ⚡ Impact Simulator
        </h3>

        {/* Step 1: Select trigger entity */}
        <div className="mb-4">
          <label className="block text-xs text-text-muted mb-1.5 uppercase tracking-wider">
            Trigger Entity
          </label>
          {triggerEntity ? (
            <div className="flex items-center gap-2">
              <span className="px-3 py-2 rounded-lg bg-accent-purple/10 text-accent-purple text-sm font-medium">
                {triggerEntity.name}
              </span>
              <span className="text-xs text-text-muted">{triggerEntity.entity_type}</span>
              <button
                onClick={() => setTriggerEntity(null)}
                className="text-text-muted hover:text-text-primary text-xs ml-auto"
              >
                Change
              </button>
            </div>
          ) : (
            <EntitySearch
              onSelect={setTriggerEntity}
              placeholder="Search for a company, facility, or event..."
            />
          )}
        </div>

        {/* Step 2: Describe event */}
        <div className="mb-4">
          <label className="block text-xs text-text-muted mb-1.5 uppercase tracking-wider">
            Event Description (optional)
          </label>
          <input
            type="text"
            value={eventDescription}
            onChange={(e) => setEventDescription(e.target.value)}
            placeholder="e.g., Factory fire, export ban, earnings miss..."
            className="w-full px-4 py-2.5 rounded-lg bg-bg-primary border border-border-default
                       text-text-primary placeholder-text-muted text-sm
                       focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple"
          />
        </div>

        {/* Parameters */}
        <div className="flex flex-wrap gap-4 mb-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">Max Depth</label>
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className="px-3 py-1.5 rounded bg-bg-primary border border-border-default text-text-primary text-sm"
            >
              {[1, 2, 3, 4, 5, 6].map((d) => (
                <option key={d} value={d}>{d} hop{d > 1 ? 's' : ''}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Min Impact</label>
            <select
              value={minImpact}
              onChange={(e) => setMinImpact(Number(e.target.value))}
              className="px-3 py-1.5 rounded bg-bg-primary border border-border-default text-text-primary text-sm"
            >
              {[1, 5, 10, 20, 30].map((p) => (
                <option key={p} value={p}>{p}%</option>
              ))}
            </select>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleSimulate}
            disabled={!triggerEntity || isSimulating}
            className="px-5 py-2.5 rounded-lg bg-accent-purple text-white font-medium text-sm
                       hover:bg-accent-purple/90 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {isSimulating ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Simulating...
              </span>
            ) : (
              'Run Simulation'
            )}
          </button>
          {result && (
            <button
              onClick={handleReset}
              className="px-4 py-2.5 rounded-lg border border-border-default text-text-secondary text-sm
                         hover:bg-white/5 transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {error && (
          <div className="mt-3 px-4 py-2 rounded-lg bg-signal-sell/10 text-signal-sell text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-text-muted">
        Impact simulations are estimates based on known supply chain relationships.
        Actual market impact may differ significantly. Not investment advice.
      </p>

      {/* Results section */}
      {result && (
        <div className="space-y-4">
          {/* Summary stats */}
          <div className="flex flex-wrap gap-3 text-xs font-mono">
            <span className="text-text-muted">
              {result.impact_table.rows.length} entities affected
            </span>
            <span className="text-text-muted">•</span>
            <span className="text-signal-sell">
              {result.impact_table.rows.filter((r) => r.impact_score >= 0.6).length} high+ impact
            </span>
            <span className="text-text-muted">•</span>
            <span className="text-text-secondary">
              {result.causal_chains.length} causal chains
            </span>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1 p-1 rounded-lg bg-bg-secondary border border-border-default w-fit">
            <button
              onClick={() => setActiveTab('table')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                ${activeTab === 'table'
                  ? 'bg-accent-purple text-white'
                  : 'text-text-muted hover:text-text-secondary'}`}
            >
              Impact Table
            </button>
            <button
              onClick={() => setActiveTab('narratives')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                ${activeTab === 'narratives'
                  ? 'bg-accent-purple text-white'
                  : 'text-text-muted hover:text-text-secondary'}`}
            >
              Chain Analysis
            </button>
          </div>

          {/* Tab content */}
          {activeTab === 'table' && (
            <ImpactTable
              rows={result.impact_table.rows}
              trigger={result.impact_table.trigger}
            />
          )}
          {activeTab === 'narratives' && (
            <CausalNarratives chains={result.causal_chains} />
          )}
        </div>
      )}
    </div>
  );
}
