'use client';

import { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { api } from '@/lib/api';
import type { SignalStats, WeeklyTrendItem, SignalHistoryItem, Signal } from '@/lib/types';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { SIGNAL_COLORS } from '@/lib/constants';

type HistoryEntry = SignalHistoryItem & { signal?: Signal };

interface HistoryResponse {
  data: HistoryEntry[];
  meta: { total?: number };
}

export default function TrackRecordPage() {
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [trend, setTrend] = useState<WeeklyTrendItem[]>([]);
  const [recentSignals, setRecentSignals] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, trendRes, historyRes] = await Promise.all([
          api.getSignalStats() as Promise<SignalStats>,
          api.getAccuracyTrend(12).catch(() => []),
          api.getSignalHistory(new URLSearchParams({ limit: '20' })).catch(() => ({ data: [] })),
        ]);
        setStats(statsRes);
        const items = Array.isArray(trendRes)
          ? trendRes
          : (trendRes as { data?: WeeklyTrendItem[] })?.data ?? [];
        setTrend(items as WeeklyTrendItem[]);
        const history = historyRes as HistoryResponse;
        setRecentSignals(history.data ?? []);
      } catch {
        setError('Failed to load track record data');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <div className="text-center">
          <p className="text-signal-sell">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-3 text-accent-purple text-sm hover:underline"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  const resolved = (stats?.hit_target ?? 0) + (stats?.hit_stop ?? 0);

  // Empty state — no signals resolved yet (new system or beta launch)
  if (resolved === 0 && (stats?.pending ?? 0) === 0 && recentSignals.length === 0) {
    return (
      <main className="min-h-screen pb-12">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-2xl font-display font-bold mb-6">Track Record</h1>
          <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-4">
            <div className="text-4xl">📊</div>
            <h2 className="text-lg font-display font-bold">Building Track Record</h2>
            <p className="text-text-secondary text-sm max-w-md mx-auto">
              SignalFlow AI is actively generating and monitoring signals. Once signals resolve
              (hit target, stop-loss, or expire), performance data will appear here.
            </p>
            <p className="text-text-muted text-xs">
              Signals typically resolve within 2-4 weeks. Check back soon for live accuracy metrics.
            </p>
          </div>
        </div>
      </main>
    );
  }

  const winColor =
    (stats?.win_rate ?? 0) >= 60
      ? 'text-signal-buy'
      : (stats?.win_rate ?? 0) >= 40
      ? 'text-signal-hold'
      : 'text-signal-sell';
  const returnColor = (stats?.avg_return_pct ?? 0) >= 0 ? 'text-signal-buy' : 'text-signal-sell';

  const outcomeDistribution = [
    { name: 'Hit Target', value: stats?.hit_target ?? 0, color: '#00E676' },
    { name: 'Hit Stop', value: stats?.hit_stop ?? 0, color: '#FF5252' },
    { name: 'Expired', value: stats?.expired ?? 0, color: '#FFD740' },
    { name: 'Pending', value: stats?.pending ?? 0, color: '#6366F1' },
  ];

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-display font-bold">Signal Track Record</h1>
          <p className="text-text-secondary text-sm max-w-lg mx-auto">
            Transparent performance history of all SignalFlow AI signals. Every signal is tracked
            from generation to resolution — no cherry-picking.
          </p>
        </div>

        {/* Hero Stats */}
        {stats && stats.total_signals > 0 ? (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard label="Win Rate" value={`${stats.win_rate.toFixed(1)}%`} color={winColor} />
              <StatCard
                label="Avg Return"
                value={`${stats.avg_return_pct >= 0 ? '+' : ''}${stats.avg_return_pct.toFixed(2)}%`}
                color={returnColor}
              />
              <StatCard label="Total Signals" value={String(stats.total_signals)} color="text-text-primary" />
              <StatCard label="Resolved" value={String(resolved)} color="text-text-primary" />
            </div>

            {/* Outcome Distribution */}
            <section className="bg-bg-card border border-border-default rounded-xl p-5">
              <h2 className="text-base font-display font-semibold mb-4">Signal Outcomes</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
                {/* Bar chart */}
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={outcomeDistribution} margin={{ top: 4, right: 4, bottom: 4, left: -10 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#9CA3AF' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#12131A',
                          border: '1px solid rgba(255,255,255,0.06)',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {outcomeDistribution.map((entry, idx) => (
                          <Cell key={idx} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="space-y-3">
                  {outcomeDistribution.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }} />
                        <span className="text-sm text-text-secondary">{item.name}</span>
                      </div>
                      <span className="text-sm font-mono text-text-primary">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Weekly Accuracy Trend */}
            {trend.length > 0 && (
              <section className="bg-bg-card border border-border-default rounded-xl p-5">
                <h2 className="text-base font-display font-semibold mb-4">📈 Weekly Accuracy Trend</h2>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={trend} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <defs>
                      <linearGradient id="trackWinGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00E676" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#00E676" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="week"
                      tick={{ fontSize: 10, fill: '#6B7280' }}
                      axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fontSize: 10, fill: '#6B7280' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v: number) => `${v}%`}
                    />
                    <Tooltip
                      formatter={(val: number) => [`${val.toFixed(1)}%`, 'Win Rate']}
                      contentStyle={{
                        backgroundColor: '#12131A',
                        border: '1px solid rgba(255,255,255,0.06)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <ReferenceLine y={50} stroke="rgba(255,255,255,0.1)" strokeDasharray="3 3" />
                    <Area
                      type="monotone"
                      dataKey="win_rate"
                      stroke="#00E676"
                      strokeWidth={2}
                      fill="url(#trackWinGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </section>
            )}

            {/* Recent Resolved Signals */}
            {recentSignals.length > 0 && (
              <section className="bg-bg-card border border-border-default rounded-xl p-5">
                <h2 className="text-base font-display font-semibold mb-4">Recent Signals</h2>
                <div className="space-y-2">
                  {recentSignals.map((entry) => {
                    const signal = entry.signal;
                    const outcomeLabel = entry.outcome === 'hit_target'
                      ? '🎯 Hit Target'
                      : entry.outcome === 'hit_stop'
                      ? '🛑 Hit Stop'
                      : entry.outcome === 'expired'
                      ? '⏱ Expired'
                      : '⏳ Pending';
                    const outcomeColor = entry.outcome === 'hit_target'
                      ? 'text-signal-buy'
                      : entry.outcome === 'hit_stop'
                      ? 'text-signal-sell'
                      : 'text-signal-hold';
                    const returnPct = entry.return_pct ? parseFloat(entry.return_pct) : null;
                    const signalColor = signal
                      ? SIGNAL_COLORS[signal.signal_type as keyof typeof SIGNAL_COLORS]
                      : '#6366F1';

                    return (
                      <div
                        key={entry.id ?? entry.signal_id}
                        className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-card-hover transition-colors border border-border-default"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className="text-xs font-bold px-2 py-0.5 rounded-full"
                            style={{ backgroundColor: `${signalColor}20`, color: signalColor }}
                          >
                            {signal?.signal_type ?? '—'}
                          </span>
                          <span className="font-mono text-sm">
                            {(signal?.symbol ?? '—').replace('.NS', '').replace('USDT', '')}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          {returnPct !== null && (
                            <span className={`text-xs font-mono ${returnPct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                              {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
                            </span>
                          )}
                          <span className={`text-xs ${outcomeColor}`}>{outcomeLabel}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </>
        ) : (
          /* Empty state */
          <div className="bg-bg-card border border-border-default rounded-xl p-12 text-center space-y-3">
            <p className="text-3xl">📊</p>
            <p className="text-lg text-text-secondary">No signals resolved yet</p>
            <p className="text-sm text-text-muted max-w-md mx-auto">
              As signals are generated and resolved (hitting target, stop, or expiring), their
              outcomes will appear here. Check back once the system has been running for a few days.
            </p>
            <a href="/" className="inline-block mt-2 text-accent-purple text-sm hover:underline">
              View active signals →
            </a>
          </div>
        )}

        {/* Methodology note */}
        <section className="bg-bg-secondary/30 border border-border-default rounded-xl p-5 text-center space-y-2">
          <h3 className="text-sm font-display font-semibold text-text-secondary">How We Track</h3>
          <p className="text-xs text-text-muted max-w-xl mx-auto leading-relaxed">
            Every signal includes a target price and stop-loss. A signal is resolved as
            &ldquo;Hit Target&rdquo; when the asset reaches the target price, &ldquo;Hit Stop&rdquo;
            when it hits the stop-loss, or &ldquo;Expired&rdquo; if neither is hit within the
            timeframe. All signals are tracked — there is no survivorship bias.
          </p>
        </section>
      </div>
    </main>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl bg-bg-card border border-border-default p-4 text-center">
      <p className="text-xs text-text-muted uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-mono font-bold mt-1 ${color}`}>{value}</p>
    </div>
  );
}
