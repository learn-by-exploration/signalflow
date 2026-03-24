'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface EquityCurveProps {
  data: { date: string; value: number }[];
  height?: number;
  showZeroLine?: boolean;
  label?: string;
  color?: string;
}

export function EquityCurve({ data, height = 200, showZeroLine = true, label = 'Portfolio Value', color = '#6366F1' }: EquityCurveProps) {
  if (data.length < 2) {
    return (
      <div className="text-center py-8 text-xs text-text-muted">
        Not enough data for equity curve
      </div>
    );
  }

  const startValue = data[0].value;
  const endValue = data[data.length - 1].value;
  const isPositive = endValue >= startValue;
  const lineColor = isPositive ? '#00E676' : '#FF5252';

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-4">
      <h3 className="text-sm font-display font-semibold mb-3">{label}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id={`equityGrad-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={lineColor} stopOpacity={0.2} />
              <stop offset="95%" stopColor={lineColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 9, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 9, fill: '#6B7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v.toLocaleString()}
          />
          {showZeroLine && <ReferenceLine y={startValue} stroke="#6B7280" strokeDasharray="3 3" strokeOpacity={0.5} />}
          <Tooltip content={<EquityTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            fill={`url(#equityGrad-${color})`}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function EquityTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { date: string; value: number } }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-text-muted">{d.date}</p>
      <p className="text-text-primary font-mono font-semibold">{d.value.toLocaleString()}</p>
    </div>
  );
}
