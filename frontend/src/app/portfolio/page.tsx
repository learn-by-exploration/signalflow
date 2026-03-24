'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { PortfolioSummary, Trade } from '@/lib/types';
import { useToast } from '@/components/shared/Toast';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { EquityCurve } from '@/components/charts/EquityCurve';
import { useUserStore } from '@/store/userStore';

interface PortfolioData {
  summary: PortfolioSummary | null;
  trades: Trade[];
  loading: boolean;
  error: string | null;
}

export default function PortfolioPage() {
  const { toast } = useToast();
  const chatId = useUserStore((s) => s.chatId) ?? 1;
  const [data, setData] = useState<PortfolioData>({
    summary: null,
    trades: [],
    loading: true,
    error: null,
  });

  // Trade form state
  const [showForm, setShowForm] = useState(false);
  const [tradeSide, setTradeSide] = useState<'buy' | 'sell'>('buy');
  const [tradeSymbol, setTradeSymbol] = useState('');
  const [tradeQty, setTradeQty] = useState('');
  const [tradePrice, setTradePrice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function loadData() {
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

  useEffect(() => {
    setData((prev) => ({ ...prev, loading: true }));
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId]);

  async function logTrade() {
    if (!tradeSymbol.trim() || !tradeQty || !tradePrice) return;
    const symbol = tradeSymbol.toUpperCase().trim();
    const marketType = symbol.includes('USDT') ? 'crypto' : symbol.includes('/') ? 'forex' : 'stock';

    setSubmitting(true);
    try {
      await api.logTrade({
        telegram_chat_id: chatId,
        symbol,
        market_type: marketType,
        side: tradeSide,
        quantity: tradeQty,
        price: tradePrice,
      });
      toast(`${tradeSide.toUpperCase()} trade logged for ${symbol}`, 'success');
      setTradeSymbol('');
      setTradeQty('');
      setTradePrice('');
      setShowForm(false);
      await loadData();
    } catch {
      toast('Failed to log trade', 'error');
    } finally {
      setSubmitting(false);
    }
  }

  if (data.loading) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (data.error) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <div className="text-center">
          <p className="text-signal-sell">{data.error}</p>
          <button
            onClick={() => { setData((p) => ({ ...p, loading: true, error: null })); loadData(); }}
            className="mt-3 text-accent-purple text-sm hover:underline"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  const summary = data.summary;
  const pnlColor = summary && summary.total_pnl_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';
  const pnlSign = summary && summary.total_pnl_pct >= 0 ? '+' : '';

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-display font-semibold">Portfolio</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors"
          >
            {showForm ? 'Cancel' : '+ Log Trade'}
          </button>
        </div>

        {/* Trade logging form */}
        {showForm && (
          <section className="bg-bg-card border border-accent-purple/30 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-display font-semibold">Log a Trade</h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div>
                <label className="text-xs text-text-muted block mb-1">Side</label>
                <div className="flex gap-1">
                  <button
                    onClick={() => setTradeSide('buy')}
                    className={`flex-1 py-2 text-xs rounded-lg font-medium transition-colors ${
                      tradeSide === 'buy'
                        ? 'bg-signal-buy/20 text-signal-buy border border-signal-buy/30'
                        : 'bg-bg-secondary border border-border-default text-text-muted'
                    }`}
                  >
                    BUY
                  </button>
                  <button
                    onClick={() => setTradeSide('sell')}
                    className={`flex-1 py-2 text-xs rounded-lg font-medium transition-colors ${
                      tradeSide === 'sell'
                        ? 'bg-signal-sell/20 text-signal-sell border border-signal-sell/30'
                        : 'bg-bg-secondary border border-border-default text-text-muted'
                    }`}
                  >
                    SELL
                  </button>
                </div>
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">Symbol</label>
                <input
                  type="text"
                  value={tradeSymbol}
                  onChange={(e) => setTradeSymbol(e.target.value.toUpperCase())}
                  placeholder="HDFCBANK.NS"
                  className="w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">Quantity</label>
                <input
                  type="number"
                  value={tradeQty}
                  onChange={(e) => setTradeQty(e.target.value)}
                  placeholder="10"
                  className="w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">Price</label>
                <input
                  type="number"
                  value={tradePrice}
                  onChange={(e) => setTradePrice(e.target.value)}
                  placeholder="1678.90"
                  className="w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={logTrade}
                  disabled={submitting || !tradeSymbol.trim() || !tradeQty || !tradePrice}
                  className="w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
                >
                  {submitting ? 'Saving...' : 'Log Trade'}
                </button>
              </div>
            </div>
          </section>
        )}

        {/* Summary Cards */}
        {summary && (summary.positions.length > 0 || data.trades.length > 0) && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl bg-bg-card border border-border-default p-4">
              <p className="text-xs text-text-muted uppercase">Invested</p>
              <p className="text-lg font-mono mt-1">{parseFloat(summary.total_invested).toLocaleString()}</p>
            </div>
            <div className="rounded-xl bg-bg-card border border-border-default p-4">
              <p className="text-xs text-text-muted uppercase">Current Value</p>
              <p className="text-lg font-mono mt-1">{parseFloat(summary.current_value).toLocaleString()}</p>
            </div>
            <div className="rounded-xl bg-bg-card border border-border-default p-4">
              <p className="text-xs text-text-muted uppercase">P&L</p>
              <p className={`text-lg font-mono mt-1 ${pnlColor}`}>
                {pnlSign}{parseFloat(summary.total_pnl).toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl bg-bg-card border border-border-default p-4">
              <p className="text-xs text-text-muted uppercase">Return</p>
              <p className={`text-lg font-mono mt-1 ${pnlColor}`}>
                {pnlSign}{summary.total_pnl_pct}%
              </p>
            </div>
          </div>
        )}

        {/* Equity Curve */}
        {data.trades.length >= 2 && (
          <EquityCurve
            data={data.trades
              .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
              .reduce<{ date: string; value: number }[]>((acc, trade) => {
                const prev = acc.length > 0 ? acc[acc.length - 1].value : 0;
                const tradeValue = parseFloat(trade.price) * parseFloat(trade.quantity) * (trade.side === 'buy' ? 1 : -1);
                return [...acc, {
                  date: new Date(trade.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
                  value: prev + tradeValue,
                }];
              }, [])}
            label="📈 Portfolio Equity Curve"
          />
        )}

        {/* P&L Chart: Per-position bar chart */}
        {summary && summary.positions.length > 1 && (
          <section className="space-y-3">
            <h2 className="text-lg font-display font-semibold">P&L by Position</h2>

            {/* Allocation bar */}
            <div className="bg-bg-card border border-border-default rounded-xl p-4">
              <p className="text-xs text-text-muted mb-2">Portfolio Allocation</p>
              <div className="flex rounded-lg overflow-hidden h-6">
                {summary.positions.map((pos) => {
                  const value = parseFloat(pos.value);
                  const totalVal = parseFloat(summary.current_value) || 1;
                  const pct = (value / totalVal) * 100;
                  const isProfit = pos.pnl_pct >= 0;
                  return (
                    <div
                      key={pos.symbol}
                      className={`relative group ${isProfit ? 'bg-signal-buy/30' : 'bg-signal-sell/30'} border-r border-bg-primary last:border-r-0`}
                      style={{ width: `${Math.max(pct, 2)}%` }}
                      title={`${pos.symbol.replace('.NS', '').replace('USDT', '')} — ${pct.toFixed(1)}% of portfolio`}
                    >
                      {pct > 8 && (
                        <span className="absolute inset-0 flex items-center justify-center text-[9px] font-mono text-text-primary truncate px-1">
                          {pos.symbol.replace('.NS', '').replace('USDT', '')}
                        </span>
                      )}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                        <div className="bg-bg-secondary border border-border-default rounded px-2 py-1 text-[10px] text-text-secondary whitespace-nowrap shadow-lg">
                          <p className="font-mono font-semibold text-text-primary">{pos.symbol.replace('.NS', '').replace('USDT', '')}</p>
                          <p>{pct.toFixed(1)}% · {value.toLocaleString()}</p>
                          <p className={isProfit ? 'text-signal-buy' : 'text-signal-sell'}>{isProfit ? '+' : ''}{pos.pnl_pct}%</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* P&L waterfall bars */}
            <div className="bg-bg-card border border-border-default rounded-xl p-4">
              <p className="text-xs text-text-muted mb-3">P&L per Position</p>
              <div className="space-y-2">
                {[...summary.positions]
                  .sort((a, b) => parseFloat(b.pnl) - parseFloat(a.pnl))
                  .map((pos) => {
                    const pnl = parseFloat(pos.pnl);
                    const maxAbsPnl = Math.max(...summary.positions.map((p) => Math.abs(parseFloat(p.pnl))), 1);
                    const barWidth = Math.abs(pnl) / maxAbsPnl * 100;
                    const isProfit = pnl >= 0;
                    return (
                      <div key={pos.symbol} className="flex items-center gap-2">
                        <span className="text-xs font-mono text-text-secondary w-16 truncate text-right">
                          {pos.symbol.replace('.NS', '').replace('USDT', '')}
                        </span>
                        <div className="flex-1 h-5 relative">
                          <div
                            className={`h-full rounded ${isProfit ? 'bg-signal-buy/40' : 'bg-signal-sell/40'}`}
                            style={{ width: `${Math.max(barWidth, 2)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-mono w-20 text-right ${isProfit ? 'text-signal-buy' : 'text-signal-sell'}`}>
                          {isProfit ? '+' : ''}{pnl.toLocaleString()}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          </section>
        )}

        {/* Positions */}
        {summary && summary.positions.length > 0 && (
          <section>
            <h2 className="text-lg font-display font-semibold mb-3">Open Positions</h2>
            <div className="rounded-xl bg-bg-card border border-border-default overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-default text-text-muted text-xs uppercase">
                    <th className="text-left p-3">Symbol</th>
                    <th className="text-right p-3">Qty</th>
                    <th className="text-right p-3 hidden sm:table-cell">Avg Price</th>
                    <th className="text-right p-3">Value</th>
                    <th className="text-right p-3">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.positions.map((pos) => {
                    const posColor = pos.pnl_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';
                    const posSign = pos.pnl_pct >= 0 ? '+' : '';
                    return (
                      <tr key={pos.symbol} className="border-b border-border-default last:border-0 hover:bg-bg-card-hover transition-colors">
                        <td className="p-3 font-mono">
                          {pos.symbol.replace('.NS', '').replace('USDT', '')}
                          <span className="ml-2 text-xs text-text-muted">{pos.market_type}</span>
                        </td>
                        <td className="text-right p-3 font-mono">{parseFloat(pos.quantity).toLocaleString()}</td>
                        <td className="text-right p-3 font-mono hidden sm:table-cell">{parseFloat(pos.avg_price).toLocaleString()}</td>
                        <td className="text-right p-3 font-mono">{parseFloat(pos.value).toLocaleString()}</td>
                        <td className={`text-right p-3 font-mono ${posColor}`}>
                          {posSign}{pos.pnl_pct}%
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
            <h2 className="text-lg font-display font-semibold mb-3">Recent Trades</h2>
            <div className="space-y-2">
              {data.trades.slice(0, 20).map((trade) => {
                const isBuy = trade.side === 'buy';
                return (
                  <div
                    key={trade.id}
                    className="rounded-lg bg-bg-card border border-border-default p-3 flex items-center justify-between hover:border-border-hover transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${isBuy ? 'bg-signal-buy/15 text-signal-buy' : 'bg-signal-sell/15 text-signal-sell'}`}>
                        {trade.side.toUpperCase()}
                      </span>
                      <span className="font-mono text-sm">{trade.symbol.replace('.NS', '').replace('USDT', '')}</span>
                    </div>
                    <div className="text-right text-sm font-mono text-text-secondary">
                      {parseFloat(trade.quantity).toLocaleString()} × {parseFloat(trade.price).toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {!summary?.positions.length && data.trades.length === 0 && (
          <div className="text-center py-16 text-text-muted">
            <p className="text-4xl mb-3">💼</p>
            <p className="text-lg">No trades logged yet</p>
            <p className="mt-2 text-sm">Click "Log Trade" above or use the Telegram bot: <span className="font-mono text-accent-purple">/trade buy HDFCBANK 10 1678.90</span></p>
          </div>
        )}
      </div>
    </main>
  );
}
