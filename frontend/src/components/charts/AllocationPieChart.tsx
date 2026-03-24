'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { PortfolioPosition } from '@/lib/types';

const MARKET_COLORS: Record<string, string> = {
  stock: '#6366F1',
  crypto: '#F59E0B',
  forex: '#10B981',
};

interface AllocationPieChartProps {
  positions: PortfolioPosition[];
  totalValue: number;
}

interface ChartEntry {
  name: string;
  value: number;
  color: string;
}

/**
 * Donut chart showing portfolio allocation by market type (stock/crypto/forex).
 */
export function AllocationPieChart({ positions, totalValue }: AllocationPieChartProps) {
  if (positions.length === 0 || totalValue <= 0) return null;

  // Aggregate by market_type
  const byMarket: Record<string, number> = {};
  for (const pos of positions) {
    const val = parseFloat(pos.value) || 0;
    byMarket[pos.market_type] = (byMarket[pos.market_type] ?? 0) + val;
  }

  const data: ChartEntry[] = Object.entries(byMarket)
    .filter(([, v]) => v > 0)
    .map(([market, value]) => ({
      name: market === 'stock' ? 'Stocks' : market === 'crypto' ? 'Crypto' : 'Forex',
      value: Math.round(value * 100) / 100,
      color: MARKET_COLORS[market] ?? '#9CA3AF',
    }))
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) return null;

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-4">
      <p className="text-xs text-text-muted mb-3 font-display">Market Allocation</p>
      <div className="h-48" data-testid="allocation-pie-chart">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
              nameKey="name"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#12131A',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [
                `${value.toLocaleString()} (${((value / totalValue) * 100).toFixed(1)}%)`,
                '',
              ]}
            />
            <Legend
              verticalAlign="bottom"
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => (
                <span className="text-xs text-text-secondary">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
