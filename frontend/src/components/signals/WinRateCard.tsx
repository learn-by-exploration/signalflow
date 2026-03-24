'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SignalStats, WeeklyTrendItem } from '@/lib/types';
import { WinRateCardSkeleton } from '@/components/shared/Skeleton';
import { Sparkline } from '@/components/markets/Sparkline';

export function WinRateCard() {
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [trend, setTrend] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [statsRes, trendRes] = await Promise.all([
          api.getSignalStats() as Promise<SignalStats>,
          api.getAccuracyTrend(8).catch(() => []),
        ]);
        setStats(statsRes);
        const items = Array.isArray(trendRes) ? trendRes : (trendRes as { data?: WeeklyTrendItem[] })?.data ?? [];
        setTrend((items as WeeklyTrendItem[]).map((i) => i.win_rate));
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
          <span className="text-xs text-text-muted uppercase tracking-wider">Win Rate</span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className={`text-sm font-mono font-bold ${returnColor}`}>
            {stats.avg_return_pct >= 0 ? '+' : ''}{stats.avg_return_pct.toFixed(2)}%
          </span>
          <span className="text-xs text-text-muted uppercase tracking-wider">Avg Return</span>
        </div>
        <a href="/history" className="text-xs text-accent-purple hover:underline ml-auto">
          {stats.total_signals} signals →
        </a>
        {trend.length >= 2 && (
          <Sparkline
            data={trend}
            width={60}
            height={24}
            positive={stats.win_rate >= 50}
            label={`Win rate trend: ${trend[trend.length - 1]?.toFixed(0) ?? ''}%`}
          />
        )}
      </div>
    </div>
  );
}
