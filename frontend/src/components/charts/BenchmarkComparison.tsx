'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface BenchmarkDataPoint {
  date: string;
  strategy: number;
  benchmark: number;
}

interface BenchmarkComparisonProps {
  strategyReturns: number;
  benchmarkName: string;
  benchmarkReturns: number;
  totalSignals: number;
  startDate: string;
  endDate: string;
}

/**
 * Compares backtest strategy returns against a benchmark (e.g., Nifty 50, BTC).
 * Shows side-by-side line chart and outperformance metrics.
 */
export function BenchmarkComparison({
  strategyReturns,
  benchmarkName,
  benchmarkReturns,
  totalSignals,
  startDate,
  endDate,
}: BenchmarkComparisonProps) {
  const outperformance = strategyReturns - benchmarkReturns;

  // Generate simulated comparison curve
  const points = Math.max(totalSignals, 10);
  const data: BenchmarkDataPoint[] = Array.from({ length: points }, (_, i) => {
    const progress = (i + 1) / points;
    const sd = new Date(startDate);
    const ed = new Date(endDate);
    const d = new Date(sd.getTime() + (ed.getTime() - sd.getTime()) * progress);
    return {
      date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
      strategy: Math.round((10000 * (1 + (strategyReturns / 100) * progress)) * 100) / 100,
      benchmark: Math.round((10000 * (1 + (benchmarkReturns / 100) * progress)) * 100) / 100,
    };
  });

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-display font-semibold">📊 vs {benchmarkName}</h3>
        <span className={`text-xs font-mono ${outperformance >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
          {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}% alpha
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-[10px] text-text-muted">Strategy</p>
          <p className={`text-sm font-mono ${strategyReturns >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
            {strategyReturns >= 0 ? '+' : ''}{strategyReturns.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="text-[10px] text-text-muted">{benchmarkName}</p>
          <p className={`text-sm font-mono ${benchmarkReturns >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
            {benchmarkReturns >= 0 ? '+' : ''}{benchmarkReturns.toFixed(2)}%
          </p>
        </div>
        <div>
          <p className="text-[10px] text-text-muted">Alpha</p>
          <p className={`text-sm font-mono font-semibold ${outperformance >= 0 ? 'text-accent-purple' : 'text-signal-sell'}`}>
            {outperformance >= 0 ? '+' : ''}{outperformance.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-40" data-testid="benchmark-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#6B7280' }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9, fill: '#6B7280' }} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#12131A',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '8px',
                fontSize: '11px',
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
            />
            <Legend verticalAlign="top" iconType="line" iconSize={12} />
            <Line
              type="monotone"
              dataKey="strategy"
              name="Strategy"
              stroke="#6366F1"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              name={benchmarkName}
              stroke="#9CA3AF"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
