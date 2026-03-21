'use client';

import { useEffect, useState, useMemo } from 'react';
import { api } from '@/lib/api';
import type { SignalHistoryItem, Signal } from '@/lib/types';
import { formatPrice, formatPercent, formatDate, shortSymbol } from '@/utils/formatters';
import { SIGNAL_COLORS } from '@/lib/constants';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import Link from 'next/link';

interface HistoryResponse {
  data: (SignalHistoryItem & { signal?: Signal })[];
  meta: { timestamp: string; count: number; total?: number };
}

const OUTCOME_LABELS: Record<string, { emoji: string; label: string; color: string }> = {
  hit_target: { emoji: '🎯', label: 'Target Hit', color: '#00E676' },
  hit_stop: { emoji: '🛑', label: 'Stop Hit', color: '#FF5252' },
  expired: { emoji: '⏰', label: 'Expired', color: '#FFD740' },
  pending: { emoji: '⏳', label: 'Pending', color: '#9CA3AF' },
};

type OutcomeFilter = 'all' | 'hit_target' | 'hit_stop' | 'expired' | 'pending';
type MarketFilter = 'all' | 'stock' | 'crypto' | 'forex';
type SortCol = 'return' | 'resolved' | null;
type SortDir = 'asc' | 'desc';

const OUTCOME_FILTERS: { value: OutcomeFilter; label: string; emoji: string }[] = [
  { value: 'all', label: 'All', emoji: '📜' },
  { value: 'hit_target', label: 'Target Hit', emoji: '🎯' },
  { value: 'hit_stop', label: 'Stop Hit', emoji: '🛑' },
  { value: 'expired', label: 'Expired', emoji: '⏰' },
  { value: 'pending', label: 'Pending', emoji: '⏳' },
];

const MARKET_FILTERS: { value: MarketFilter; label: string }[] = [
  { value: 'all', label: 'All Markets' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

export default function HistoryPage() {
  const [history, setHistory] = useState<(SignalHistoryItem & { signal?: Signal })[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [outcomeFilter, setOutcomeFilter] = useState<OutcomeFilter>('all');
  const [marketFilter, setMarketFilter] = useState<MarketFilter>('all');
  const [sortCol, setSortCol] = useState<SortCol>(null);
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = (await api.getSignalHistory()) as HistoryResponse;
        setHistory(res.data);
      } catch {
        // Fail silently
      } finally {
        setIsLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const filtered = useMemo(() => {
    let items = history;
    if (outcomeFilter !== 'all') {
      items = items.filter((item) => item.outcome === outcomeFilter);
    }
    if (marketFilter !== 'all') {
      items = items.filter((item) => item.signal?.market_type === marketFilter);
    }
    if (sortCol) {
      items = [...items].sort((a, b) => {
        let cmp = 0;
        if (sortCol === 'return') {
          const aVal = a.return_pct ? parseFloat(a.return_pct) : -Infinity;
          const bVal = b.return_pct ? parseFloat(b.return_pct) : -Infinity;
          cmp = aVal - bVal;
        } else if (sortCol === 'resolved') {
          const aVal = a.resolved_at ? new Date(a.resolved_at).getTime() : 0;
          const bVal = b.resolved_at ? new Date(b.resolved_at).getTime() : 0;
          cmp = aVal - bVal;
        }
        return sortDir === 'desc' ? -cmp : cmp;
      });
    }
    return items;
  }, [history, outcomeFilter, marketFilter, sortCol, sortDir]);

  // Summary stats
  const stats = useMemo(() => {
    const hitTarget = history.filter((h) => h.outcome === 'hit_target').length;
    const hitStop = history.filter((h) => h.outcome === 'hit_stop').length;
    const expired = history.filter((h) => h.outcome === 'expired').length;
    const pending = history.filter((h) => h.outcome === 'pending').length;
    const resolved = hitTarget + hitStop;
    const winRate = resolved > 0 ? (hitTarget / resolved) * 100 : 0;
    return { hitTarget, hitStop, expired, pending, winRate, total: history.length };
  }, [history]);

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortCol(col);
      setSortDir('desc');
    }
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-display font-semibold mb-4">Signal History</h1>

        {/* Summary stats */}
        {!isLoading && stats.total > 0 && (
          <div className="flex flex-wrap items-center gap-3 mb-4 text-xs font-mono">
            <span className="text-signal-buy">🎯 {stats.hitTarget}</span>
            <span className="text-text-muted">•</span>
            <span className="text-signal-sell">🛑 {stats.hitStop}</span>
            <span className="text-text-muted">•</span>
            <span className="text-signal-hold">⏰ {stats.expired}</span>
            <span className="text-text-muted">•</span>
            <span className="text-text-muted">⏳ {stats.pending}</span>
            {stats.hitTarget + stats.hitStop > 0 && (
              <>
                <span className="text-text-muted">|</span>
                <span className={stats.winRate >= 50 ? 'text-signal-buy' : 'text-signal-sell'}>
                  Win Rate: {stats.winRate.toFixed(1)}%
                </span>
              </>
            )}
          </div>
        )}

        {/* Outcome filter pills */}
        {!isLoading && stats.total > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {OUTCOME_FILTERS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setOutcomeFilter(opt.value)}
                aria-pressed={outcomeFilter === opt.value}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  outcomeFilter === opt.value
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-secondary hover:border-border-hover'
                }`}
              >
                {opt.emoji} {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Market type filter pills */}
        {!isLoading && stats.total > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {MARKET_FILTERS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setMarketFilter(opt.value)}
                aria-pressed={marketFilter === opt.value}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  marketFilter === opt.value
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-muted hover:border-border-hover'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : history.length === 0 ? (
          <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
            <p className="text-3xl">📜</p>
            <p className="text-text-secondary text-sm">
              No signal history yet. Signals appear here once they hit their target, stop-loss, or expire.
            </p>
            <Link href="/" className="text-xs text-accent-purple hover:underline">← View active signals on the dashboard</Link>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
            <p className="text-3xl">{OUTCOME_FILTERS.find((o) => o.value === outcomeFilter)?.emoji ?? '📜'}</p>
            <p className="text-text-secondary text-sm">
              No signals with this outcome yet.
            </p>
            <button onClick={() => setOutcomeFilter('all')} className="text-xs text-accent-purple hover:underline">Show all history</button>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Table header — desktop only */}
            <div className="hidden sm:grid grid-cols-6 gap-4 px-4 py-2 text-xs text-text-muted font-display uppercase tracking-wider">
              <span>Symbol</span>
              <span>Signal</span>
              <span>Outcome</span>
              <SortableHeader label="Return" col="return" currentCol={sortCol} dir={sortDir} onSort={toggleSort} className="text-right" />
              <span className="text-right">Exit Price</span>
              <SortableHeader label="Resolved" col="resolved" currentCol={sortCol} dir={sortDir} onSort={toggleSort} className="text-right" />
            </div>

            {filtered.map((item) => {
              const outcome = OUTCOME_LABELS[item.outcome ?? 'pending'];
              const returnPct = item.return_pct ? parseFloat(item.return_pct) : null;

              return (
                <div
                  key={item.id}
                  className="bg-bg-card border border-border-default rounded-lg px-4 py-3 hover:border-border-hover transition-colors"
                >
                  {/* Desktop: grid row */}
                  <div className="hidden sm:grid grid-cols-6 gap-4 items-center">
                    <span className="text-sm font-display font-medium text-text-primary">
                      {item.signal ? (
                        <Link href={`/signal/${item.signal_id}`} className="hover:text-accent-purple transition-colors">
                          {shortSymbol(item.signal.symbol)}
                        </Link>
                      ) : '—'}
                    </span>
                    <span>
                      {item.signal ? (
                        <span
                          className="text-xs font-mono font-semibold"
                          style={{ color: SIGNAL_COLORS[item.signal.signal_type] }}
                        >
                          {item.signal.signal_type.replace('_', ' ')}
                        </span>
                      ) : (
                        '—'
                      )}
                    </span>
                    <span className="flex items-center gap-1">
                      <span>{outcome.emoji}</span>
                      <span className="text-xs" style={{ color: outcome.color }}>
                        {outcome.label}
                      </span>
                    </span>
                    <span className="text-right font-mono text-sm">
                      {returnPct !== null ? (
                        <span className={returnPct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}>
                          {formatPercent(returnPct)}
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </span>
                    <span className="text-right font-mono text-sm text-text-secondary">
                      {item.exit_price ? formatPrice(item.exit_price) : '—'}
                    </span>
                    <span className="text-right text-xs text-text-muted">
                      {item.resolved_at ? formatDate(item.resolved_at) : '—'}
                    </span>
                  </div>

                  {/* Mobile: card layout */}
                  <div className="sm:hidden space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-display font-medium text-text-primary">
                          {item.signal ? shortSymbol(item.signal.symbol) : '—'}
                        </span>
                        {item.signal && (
                          <span
                            className="text-xs font-mono font-semibold"
                            style={{ color: SIGNAL_COLORS[item.signal.signal_type] }}
                          >
                            {item.signal.signal_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <span className="flex items-center gap-1">
                        <span>{outcome.emoji}</span>
                        <span className="text-xs" style={{ color: outcome.color }}>
                          {outcome.label}
                        </span>
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-text-muted">
                        {item.resolved_at ? formatDate(item.resolved_at) : 'Pending'}
                      </span>
                      <div className="flex gap-3">
                        {returnPct !== null && (
                          <span className={returnPct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}>
                            {formatPercent(returnPct)}
                          </span>
                        )}
                        {item.exit_price && (
                          <span className="text-text-secondary">
                            Exit: {formatPrice(item.exit_price)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}

function SortableHeader({ label, col, currentCol, dir, onSort, className }: {
  label: string;
  col: SortCol;
  currentCol: SortCol;
  dir: SortDir;
  onSort: (col: SortCol) => void;
  className?: string;
}) {
  const isActive = currentCol === col;
  return (
    <button
      onClick={() => onSort(col)}
      className={`flex items-center gap-0.5 hover:text-text-primary transition-colors ${className ?? ''} ${isActive ? 'text-accent-purple' : ''}`}
    >
      {label}
      <span className="text-[8px]">
        {isActive ? (dir === 'desc' ? '▼' : '▲') : '⇅'}
      </span>
    </button>
  );
}
