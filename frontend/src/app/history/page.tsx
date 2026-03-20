'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SignalHistoryItem, Signal } from '@/lib/types';
import { formatPrice, formatPercent, formatDate, shortSymbol } from '@/utils/formatters';
import { SIGNAL_COLORS } from '@/lib/constants';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import Link from 'next/link';

interface HistoryResponse {
  data: (SignalHistoryItem & { signal?: Signal })[];
  meta: { timestamp: string; count: number };
}

const OUTCOME_LABELS: Record<string, { emoji: string; label: string; color: string }> = {
  hit_target: { emoji: '🎯', label: 'Target Hit', color: '#00E676' },
  hit_stop: { emoji: '🛑', label: 'Stop Hit', color: '#FF5252' },
  expired: { emoji: '⏰', label: 'Expired', color: '#FFD740' },
  pending: { emoji: '⏳', label: 'Pending', color: '#9CA3AF' },
};

export default function HistoryPage() {
  const [history, setHistory] = useState<(SignalHistoryItem & { signal?: Signal })[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-display font-semibold mb-6">Signal History</h1>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : history.length === 0 ? (
          <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center">
            <p className="text-text-muted">
              No signal history yet. Signals will appear here once they are resolved.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Table header */}
            <div className="grid grid-cols-6 gap-4 px-4 py-2 text-xs text-text-muted font-display uppercase tracking-wider">
              <span>Symbol</span>
              <span>Signal</span>
              <span>Outcome</span>
              <span className="text-right">Return</span>
              <span className="text-right">Exit Price</span>
              <span className="text-right">Resolved</span>
            </div>

            {history.map((item) => {
              const outcome = OUTCOME_LABELS[item.outcome ?? 'pending'];
              const returnPct = item.return_pct ? parseFloat(item.return_pct) : null;

              return (
                <div
                  key={item.id}
                  className="grid grid-cols-6 gap-4 bg-bg-card border border-border-default rounded-lg px-4 py-3 items-center hover:border-border-hover transition-colors"
                >
                  <span className="text-sm font-display font-medium text-text-primary">
                    {item.signal ? shortSymbol(item.signal.symbol) : '—'}
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
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
