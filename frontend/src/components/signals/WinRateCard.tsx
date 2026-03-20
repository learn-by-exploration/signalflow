'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SignalStats } from '@/lib/types';

export function WinRateCard() {
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await api.getSignalStats() as SignalStats;
        setStats(res);
      } catch {
        // Non-critical — silently fail
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
      <div className="bg-bg-card border border-border-default rounded-xl p-4 animate-pulse">
        <div className="h-4 bg-bg-secondary rounded w-24 mb-3" />
        <div className="h-8 bg-bg-secondary rounded w-16" />
      </div>
    );
  }

  if (!stats || stats.total_signals === 0) {
    return (
      <div className="bg-bg-card border border-border-default rounded-xl p-4">
        <h3 className="text-sm font-display font-medium text-text-muted mb-1">Signal Performance</h3>
        <p className="text-xs text-text-muted">No resolved signals yet. Stats will appear once signals are tracked.</p>
      </div>
    );
  }

  const winColor = stats.win_rate >= 60 ? 'text-signal-buy' : stats.win_rate >= 40 ? 'text-signal-hold' : 'text-signal-sell';
  const returnColor = stats.avg_return_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';
  const resolved = stats.hit_target + stats.hit_stop;

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-display font-medium text-text-secondary">Signal Performance</h3>

      <div className="grid grid-cols-3 gap-3">
        {/* Win Rate */}
        <div className="text-center">
          <div className={`text-2xl font-mono font-bold ${winColor}`}>
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-[10px] text-text-muted uppercase tracking-wider mt-0.5">Win Rate</div>
        </div>

        {/* Avg Return */}
        <div className="text-center">
          <div className={`text-2xl font-mono font-bold ${returnColor}`}>
            {stats.avg_return_pct >= 0 ? '+' : ''}{stats.avg_return_pct.toFixed(2)}%
          </div>
          <div className="text-[10px] text-text-muted uppercase tracking-wider mt-0.5">Avg Return</div>
        </div>

        {/* Total Signals */}
        <div className="text-center">
          <div className="text-2xl font-mono font-bold text-text-primary">
            {stats.total_signals}
          </div>
          <div className="text-[10px] text-text-muted uppercase tracking-wider mt-0.5">Total</div>
        </div>
      </div>

      {/* Outcome Breakdown */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="text-signal-buy">🎯 {stats.hit_target}</span>
        <span className="text-text-muted">•</span>
        <span className="text-signal-sell">🛑 {stats.hit_stop}</span>
        <span className="text-text-muted">•</span>
        <span className="text-signal-hold">⏰ {stats.expired}</span>
        <span className="text-text-muted">•</span>
        <span className="text-text-muted">⏳ {stats.pending}</span>
      </div>

      {/* Win Rate Bar */}
      {resolved > 0 && (
        <div className="w-full bg-signal-sell/20 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-signal-buy h-full rounded-full transition-all duration-500"
            style={{ width: `${stats.win_rate}%` }}
          />
        </div>
      )}

      {stats.last_updated && (
        <div className="text-[10px] text-text-muted">
          Last resolved: {new Date(stats.last_updated).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}
