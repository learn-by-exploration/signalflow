'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { PortfolioSummary, Trade } from '@/lib/types';

interface PortfolioData {
  summary: PortfolioSummary | null;
  trades: Trade[];
  loading: boolean;
  error: string | null;
}

export default function PortfolioPage() {
  const [data, setData] = useState<PortfolioData>({
    summary: null,
    trades: [],
    loading: true,
    error: null,
  });

  // Placeholder chat ID — in production this comes from auth
  const chatId = 1;

  useEffect(() => {
    async function load() {
      try {
        const [summaryRes, tradesRes] = await Promise.all([
          api.getPortfolioSummary(chatId) as Promise<{ data: PortfolioSummary }>,
          api.getTrades(chatId) as Promise<{ data: Trade[] }>,
        ]);
        setData({
          summary: summaryRes.data,
          trades: tradesRes.data,
          loading: false,
          error: null,
        });
      } catch {
        setData((prev) => ({ ...prev, loading: false, error: 'Failed to load portfolio' }));
      }
    }
    load();
  }, []);

  if (data.loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="animate-pulse text-[var(--text-secondary)]">Loading portfolio...</div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-red-400">{data.error}</div>
      </div>
    );
  }

  const summary = data.summary;
  const pnlColor = summary && summary.total_pnl_pct >= 0 ? 'text-[var(--signal-buy)]' : 'text-[var(--signal-sell)]';
  const pnlSign = summary && summary.total_pnl_pct >= 0 ? '+' : '';

  return (
    <main className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] p-4 sm:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        <h1 className="text-2xl font-semibold font-[var(--font-display)]">Portfolio</h1>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase">Invested</p>
              <p className="text-lg font-mono mt-1">{parseFloat(summary.total_invested).toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase">Current Value</p>
              <p className="text-lg font-mono mt-1">{parseFloat(summary.current_value).toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase">P&L</p>
              <p className={`text-lg font-mono mt-1 ${pnlColor}`}>
                {pnlSign}{parseFloat(summary.total_pnl).toLocaleString()}
              </p>
            </div>
            <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase">Return</p>
              <p className={`text-lg font-mono mt-1 ${pnlColor}`}>
                {pnlSign}{summary.total_pnl_pct}%
              </p>
            </div>
          </div>
        )}

        {/* Positions */}
        {summary && summary.positions.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3">Open Positions</h2>
            <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border-default)] text-[var(--text-muted)] text-xs uppercase">
                    <th className="text-left p-3">Symbol</th>
                    <th className="text-right p-3">Qty</th>
                    <th className="text-right p-3">Avg Price</th>
                    <th className="text-right p-3">Value</th>
                    <th className="text-right p-3">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.positions.map((pos) => {
                    const posColor = pos.pnl_pct >= 0 ? 'text-[var(--signal-buy)]' : 'text-[var(--signal-sell)]';
                    const posSign = pos.pnl_pct >= 0 ? '+' : '';
                    return (
                      <tr key={pos.symbol} className="border-b border-[var(--border-default)] last:border-0">
                        <td className="p-3 font-mono">
                          {pos.symbol.replace('.NS', '').replace('USDT', '')}
                          <span className="ml-2 text-xs text-[var(--text-muted)]">{pos.market_type}</span>
                        </td>
                        <td className="text-right p-3 font-mono">{parseFloat(pos.quantity).toLocaleString()}</td>
                        <td className="text-right p-3 font-mono">{parseFloat(pos.avg_price).toLocaleString()}</td>
                        <td className="text-right p-3 font-mono">{parseFloat(pos.value).toLocaleString()}</td>
                        <td className={`text-right p-3 font-mono ${posColor}`}>
                          {posSign}{parseFloat(pos.pnl).toLocaleString()} ({posSign}{pos.pnl_pct}%)
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Recent Trades */}
        {data.trades.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3">Recent Trades</h2>
            <div className="space-y-2">
              {data.trades.slice(0, 20).map((trade) => {
                const isBuy = trade.side === 'buy';
                return (
                  <div
                    key={trade.id}
                    className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-3 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${isBuy ? 'bg-green-900/40 text-[var(--signal-buy)]' : 'bg-red-900/40 text-[var(--signal-sell)]'}`}>
                        {trade.side.toUpperCase()}
                      </span>
                      <span className="font-mono">{trade.symbol.replace('.NS', '').replace('USDT', '')}</span>
                    </div>
                    <div className="text-right text-sm font-mono text-[var(--text-secondary)]">
                      {parseFloat(trade.quantity).toLocaleString()} × {parseFloat(trade.price).toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {!summary?.positions.length && data.trades.length === 0 && (
          <div className="text-center py-16 text-[var(--text-muted)]">
            <p className="text-lg">No trades logged yet</p>
            <p className="mt-2 text-sm">Use the Telegram bot: /trade buy HDFCBANK 10 1678.90</p>
          </div>
        )}
      </div>
    </main>
  );
}
