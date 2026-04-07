/**
 * ScenarioCards — pre-built "What If?" simulation scenarios.
 *
 * One-click buttons for common supply chain disruption events.
 * Clicking a card pre-fills the ImpactSimulator and auto-runs.
 */
'use client';

import { useState, useCallback } from 'react';
import { mkgApi } from '@/lib/mkg-api';
import type { PropagationResult } from '@/lib/mkg-types';

export interface Scenario {
  id: string;
  emoji: string;
  title: string;
  description: string;
  triggerSearch: string;
  eventDescription: string;
  maxDepth: number;
  minImpact: number;
}

export const PRESET_SCENARIOS: Scenario[] = [
  {
    id: 'taiwan-quake',
    emoji: '⚡',
    title: 'Taiwan Earthquake',
    description: 'Major earthquake disrupts semiconductor production in Taiwan.',
    triggerSearch: 'TSMC',
    eventDescription: 'Major earthquake disrupts semiconductor production in Taiwan',
    maxDepth: 4,
    minImpact: 0.05,
  },
  {
    id: 'samsung-fab-fire',
    emoji: '🔥',
    title: 'Samsung Fab Fire',
    description: 'Major fabrication facility fire halts chip production.',
    triggerSearch: 'Samsung',
    eventDescription: 'Major fabrication facility fire halts Samsung chip production',
    maxDepth: 4,
    minImpact: 0.05,
  },
  {
    id: 'us-china-trade',
    emoji: '🇨🇳',
    title: 'US-China Trade Escalation',
    description: 'New export controls on advanced semiconductor technology.',
    triggerSearch: 'China',
    eventDescription: 'New US export controls on advanced technology to China',
    maxDepth: 4,
    minImpact: 0.05,
  },
  {
    id: 'rbi-rate-hike',
    emoji: '🏦',
    title: 'RBI Rate Hike',
    description: 'Unexpected interest rate increase impacts banking sector.',
    triggerSearch: 'RBI',
    eventDescription: 'RBI announces unexpected 50bps interest rate hike',
    maxDepth: 3,
    minImpact: 0.05,
  },
  {
    id: 'it-sector-slowdown',
    emoji: '💻',
    title: 'IT Sector Slowdown',
    description: 'Global IT spending cuts affect Indian IT companies.',
    triggerSearch: 'Indian IT',
    eventDescription: 'Global IT spending cuts and layoffs across the sector',
    maxDepth: 3,
    minImpact: 0.05,
  },
  {
    id: 'crypto-crash',
    emoji: '📉',
    title: 'Crypto Market Crash',
    description: 'Bitcoin drops 40% triggering cascade across crypto sector.',
    triggerSearch: 'BTC',
    eventDescription: 'Bitcoin drops 40% in 24 hours triggering mass liquidations',
    maxDepth: 3,
    minImpact: 0.05,
  },
];

interface ScenarioCardsProps {
  onScenarioRun: (result: PropagationResult, triggerId: string, scenario: Scenario) => void;
}

export function ScenarioCards({ onScenarioRun }: ScenarioCardsProps) {
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClick = useCallback(
    async (scenario: Scenario) => {
      setRunningId(scenario.id);
      setError(null);
      try {
        // Find trigger entity by name
        const entities = await mkgApi.searchEntities(scenario.triggerSearch, undefined, 1);
        if (entities.length === 0) {
          setError(`Entity "${scenario.triggerSearch}" not found in graph.`);
          setRunningId(null);
          return;
        }
        const triggerId = entities[0].id;

        // Run propagation
        const result = await mkgApi.runPropagation({
          trigger_entity_id: triggerId,
          impact_score: 1.0,
          max_depth: scenario.maxDepth,
          min_impact: scenario.minImpact,
          event_description: scenario.eventDescription,
        });

        onScenarioRun(result, triggerId, scenario);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Simulation failed');
      } finally {
        setRunningId(null);
      }
    },
    [onScenarioRun],
  );

  return (
    <div>
      <h3 className="text-sm font-display font-semibold text-text-primary mb-3">
        Quick Scenarios
      </h3>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {PRESET_SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => handleClick(scenario)}
            disabled={runningId !== null}
            className="group text-left p-4 rounded-xl border border-border-default bg-bg-secondary
                       hover:border-accent-purple/30 hover:bg-accent-purple/5
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            <div className="text-xl mb-1.5">
              {runningId === scenario.id ? (
                <span className="inline-block w-5 h-5 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
              ) : (
                scenario.emoji
              )}
            </div>
            <div className="text-sm font-medium text-text-primary group-hover:text-accent-purple transition-colors mb-0.5">
              {scenario.title}
            </div>
            <div className="text-xs text-text-muted line-clamp-2">
              {scenario.description}
            </div>
          </button>
        ))}
      </div>
      {error && (
        <div className="mt-3 px-4 py-2 rounded-lg bg-signal-sell/10 text-signal-sell text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
