'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SignalStats } from '@/lib/types';

export function WinRateCard() {
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await api.getSignalStats() as SignalStats;
        setStats(res);
        setError(null);
      } catch {
        setError('Failed to load signal stats');
      } finally {
        setIsLoading(false);
      }
    }
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-bg-card border border-border-default rounded-lg p-3 animate-pulse">
        <div className="h-4 bg-bg-secondary rounded w-48" />
      </div>
    );
  }

  if (!stats || stats.total_signals === 0) {
    if (error) {
      return (
        <div className="bg-bg-card border border-signal-hold/30 rounded-lg p-3 flex items-center justify-between">
          <span className="text-xs text-text-muted">Signal Performance</span>
          <button
            onClick={() => { setIsLoading(true); setError(null); api.getSignalStats().then((res) => { setStats(res as SignalStats); setError(null); }).catch(() => setError('Failed to load signal stats')).finally(() => setIsLoading(false)); }}
            className="text-xs text-accent-purple hover:underline"
          >
            Retry
          </button>
        </div>
      );
    }
    return (
      <div className="bg-bg-card border border-border-default rounded-lg p-3">
        <p className="text-xs text-text-muted">No resolved signals yet. Stats will appear once signals are tracked.</p>
      </div>
    );
  }

  const winColor = stats.win_rate >= 60 ? 'text-signal-buy' : stats.win_rate >= 40 ? 'text-signal-hold' : 'text-signal-sell';
  const returnColor = stats.avg_return_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';
  const resolved = stats.hit_target + stats.hit_stop;

  return (
    <div className="bg-bg-card border border-border-default rounded-lg px-4 py-3">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-6">
          {/* Win Rate */}
          <div className="flex items-baseline gap-1.5">
            <span className={`text-lg font-mono font-bold ${winColor}`}>
              {stats.win_rate.toFixed(1)}%
            </span>
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Win Rate</span>
          </div>

          {/* Avg Return */}
          <div className="flex items-baseline gap-1.5">
            <span className={`text-lg font-mono font-bold ${returnColor}`}>
              {stats.avg_return_pct >= 0 ? '+' : ''}{stats.avg_return_pct.toFixed(2)}%
            </span>
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Avg Return</span>
          </div>

          {/* Total */}
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-mono font-bold text-text-primary">
              {stats.total_signals}
            </span>
            <span className="text-[10px] text-text-muted uppercase tracking-wider">Signals</span>
          </div>
        </div>

        {/* Compact outcome counts + link */}
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-signal-buy" title="Hit target">{stats.hit_target} hit</span>
          <span className="text-text-muted">·</span>
          <span className="text-signal-sell" title="Hit stop-loss">{stats.hit_stop} stopped</span>
          {resolved > 0 && (
            <a href="/history" className="text-accent-purple hover:underline text-[10px]">View trend →</a>
          )}
        </div>
      </div>
    </div>
  );
}
