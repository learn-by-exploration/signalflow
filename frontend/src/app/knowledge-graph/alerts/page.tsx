/**
 * /knowledge-graph/alerts — Supply chain alert feed.
 */
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGAlert } from '@/lib/mkg-types';
import { SEVERITY_COLORS } from '@/lib/mkg-types';
import { EntityDrawer } from '@/components/graph/EntityDrawer';
import { useGraphStore } from '@/store/graphStore';

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const EMOJI: Record<string, string> = { critical: '🔴', high: '🟠', medium: '🟡', low: '⚪' };

function AlertCard({ alert }: { alert: MKGAlert }) {
  const setDrawerEntityId = useGraphStore((s) => s.setDrawerEntityId);
  const color = SEVERITY_COLORS[alert.severity] || '#6B7280';
  const chain = alert.source_chain;

  return (
    <div className="p-4 rounded-xl border border-border-default bg-bg-secondary hover:bg-white/[0.02] transition-colors">
      <div className="flex items-start gap-3">
        <span className="text-lg shrink-0">{EMOJI[alert.severity] || '⚪'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-display font-semibold text-text-primary truncate">
              {alert.title}
            </h3>
            <span
              className="px-2 py-0.5 text-[10px] rounded-full font-mono uppercase shrink-0"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {alert.severity}
            </span>
          </div>
          <p className="text-xs text-text-secondary mb-2 line-clamp-2">{alert.message}</p>

          {/* Impact + chain info */}
          <div className="flex items-center gap-3 text-xs text-text-muted">
            <span className="font-mono" style={{ color }}>
              {Math.round(alert.impact_score * 100)}% impact
            </span>
            {chain && (
              <span>
                <button
                  onClick={() => setDrawerEntityId(chain.trigger)}
                  className="hover:text-accent-purple"
                >
                  {chain.trigger_name}
                </button>
                {' → '}
                <button
                  onClick={() => setDrawerEntityId(chain.affected_entity)}
                  className="hover:text-accent-purple"
                >
                  {chain.affected_name}
                </button>
                {chain.hops > 1 && ` (${chain.hops} hops)`}
              </span>
            )}
            <span className="ml-auto">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>

          {/* Narrative */}
          {chain?.narrative && (
            <p className="mt-2 text-xs text-text-muted italic border-l-2 pl-2"
               style={{ borderColor: `${color}50` }}>
              {chain.narrative}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<MKGAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await mkgApi.listAlerts(50);
        setAlerts(data);
      } catch {
        // fail silently
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const filtered = filterSeverity
    ? alerts.filter((a) => a.severity === filterSeverity)
    : alerts;

  const sorted = [...filtered].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4),
  );

  const severityCounts = alerts.reduce(
    (acc, a) => {
      acc[a.severity] = (acc[a.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-xs text-text-muted mb-4">
          <Link href="/knowledge-graph" className="hover:text-text-secondary">
            Supply Chain Map
          </Link>
          <span>›</span>
          <span className="text-text-primary">Alerts</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-display font-semibold text-text-primary mb-1">
            🚨 Supply Chain Alerts
          </h1>
          <p className="text-sm text-text-muted">
            AI-generated alerts on supply chain disruptions and risk events.
          </p>
        </div>

        {/* Severity filter pills */}
        {!isLoading && alerts.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            <button
              onClick={() => setFilterSeverity('')}
              className={`px-3 py-1.5 text-xs rounded-lg border transition-colors
                ${!filterSeverity
                  ? 'bg-accent-purple/10 text-accent-purple border-accent-purple/30 font-medium'
                  : 'border-border-default text-text-muted hover:border-border-hover'}`}
            >
              All ({alerts.length})
            </button>
            {['critical', 'high', 'medium', 'low'].map((sev) => {
              const count = severityCounts[sev] || 0;
              if (count === 0) return null;
              const color = SEVERITY_COLORS[sev as keyof typeof SEVERITY_COLORS];
              return (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(filterSeverity === sev ? '' : sev)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors flex items-center gap-1.5
                    ${filterSeverity === sev
                      ? 'font-medium'
                      : 'border-border-default text-text-muted hover:border-border-hover'}`}
                  style={filterSeverity === sev ? {
                    backgroundColor: `${color}15`,
                    color,
                    borderColor: `${color}40`,
                  } : undefined}
                >
                  {EMOJI[sev]} {sev.charAt(0).toUpperCase() + sev.slice(1)} ({count})
                </button>
              );
            })}
          </div>
        )}

        {/* Alert list */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-bg-secondary animate-pulse rounded-xl" />
            ))}
          </div>
        ) : sorted.length > 0 ? (
          <div className="space-y-3">
            {sorted.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-4xl mb-3 opacity-30">🔔</div>
            <p className="text-text-muted text-sm">
              {filterSeverity
                ? `No ${filterSeverity} alerts.`
                : 'No supply chain alerts yet. Run an impact simulation to generate alerts.'}
            </p>
          </div>
        )}

        <p className="mt-8 text-xs text-text-muted text-center">
          Alerts are AI-generated and may contain inaccuracies. Not investment advice.
        </p>
      </div>

      <EntityDrawer />
    </main>
  );
}
