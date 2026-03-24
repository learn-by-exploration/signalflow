'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SignalStats } from '@/lib/types';
import { WinRateCardSkeleton } from '@/components/shared/Skeleton';

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
    return <WinRateCardSkeleton />;
  }

  if (!stats || stats.total_signals === 0) {
    return null;
  }

  const winColor = stats.win_rate >= 60 ? 'text-signal-buy' : stats.win_rate >= 40 ? 'text-signal-hold' : 'text-signal-sell';
  const returnColor = stats.avg_return_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';

  return (
    <div className="bg-bg-card border border-border-default rounded-lg px-4 py-2.5">
      <div className="flex items-center gap-6">
        <div className="flex items-baseline gap-1.5">
          <span className={`text-sm font-mono font-bold ${winColor}`}>
            {stats.win_rate.toFixed(1)}%
          </span>
          <span className="text-[10px] text-text-muted uppercase tracking-wider">Win Rate</span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className={`text-sm font-mono font-bold ${returnColor}`}>
            {stats.avg_return_pct >= 0 ? '+' : ''}{stats.avg_return_pct.toFixed(2)}%
          </span>
          <span className="text-[10px] text-text-muted uppercase tracking-wider">Avg Return</span>
        </div>
        <a href="/history" className="text-[10px] text-accent-purple hover:underline ml-auto">
          {stats.total_signals} signals →
        </a>
      </div>
    </div>
  );
}
