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
} from 'recharts';
import { api } from '@/lib/api';
import type { WeeklyTrendItem } from '@/lib/types';

export function AccuracyChart() {
  const [data, setData] = useState<WeeklyTrendItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.getAccuracyTrend(8)
      .then((res) => {
        const items = Array.isArray(res) ? res : (res as { data?: WeeklyTrendItem[] })?.data ?? [];
        setData(items as WeeklyTrendItem[]);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-bg-card border border-border-default rounded-xl p-4">
        <h3 className="text-sm font-display font-semibold mb-2">Accuracy Trend</h3>
        <div className="h-32 flex items-center justify-center">
          <span className="text-xs text-text-muted animate-pulse">Loading…</span>
        </div>
      </div>
    );
  }

  if (error || data.length === 0) {
    return (
      <div className="bg-bg-card border border-border-default rounded-xl p-4">
        <h3 className="text-sm font-display font-semibold mb-2">Accuracy Trend</h3>
        <p className="text-xs text-text-muted text-center py-6">
          {error ? 'Could not load trend data.' : 'Not enough resolved signals for a trend yet.'}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-4">
      <h3 className="text-sm font-display font-semibold mb-3">📈 Accuracy Trend</h3>
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="winRateGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00E676" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00E676" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="week"
            tick={{ fontSize: 9, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 9, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <ReferenceLine y={50} stroke="#6B7280" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Tooltip content={<TrendTooltip />} />
          <Area
            type="monotone"
            dataKey="win_rate"
            stroke="#00E676"
            strokeWidth={2}
            fill="url(#winRateGrad)"
            dot={{ r: 3, fill: '#00E676', strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function TrendTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: WeeklyTrendItem }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-text-primary font-mono font-semibold">{d.week}</p>
      <p className="text-text-secondary">
        Win Rate: <span className={d.win_rate >= 50 ? 'text-signal-buy' : 'text-signal-sell'}>{d.win_rate}%</span>
      </p>
      <p className="text-text-muted">{d.hit_target}/{d.total} hit target</p>
    </div>
  );
}
