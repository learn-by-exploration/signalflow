'use client';

import { useState, useMemo } from 'react';
import type { Signal, MarketType } from '@/lib/types';
import { SignalCard } from './SignalCard';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

interface SignalFeedProps {
  signals: Signal[];
  isLoading: boolean;
  error: string | null;
}

type FilterType = 'all' | MarketType;

const FILTER_OPTIONS: { value: FilterType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

export function SignalFeed({ signals, isLoading, error }: SignalFeedProps) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let result = signals;
    if (filter !== 'all') {
      result = result.filter((s) => s.market_type === filter);
    }
    if (search.trim()) {
      const q = search.trim().toUpperCase();
      result = result.filter((s) => s.symbol.toUpperCase().includes(q));
    }
    return result;
  }, [signals, filter, search]);

  return (
    <div className="space-y-4">
      {/* Header + Filters */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-display font-semibold">Active Signals</h2>
        <div className="flex gap-2">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                filter === opt.value
                  ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                  : 'border-border-default text-text-secondary hover:border-border-hover'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Symbol Search */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search symbol (e.g. HDFC, BTC, EUR)..."
          className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple/50 font-mono"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary text-xs"
          >
            ✕
          </button>
        )}
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {error && (
        <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-xl p-4 text-center">
          <p className="text-signal-sell text-sm">{error}</p>
        </div>
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center">
          <p className="text-text-muted text-sm">
            No {filter === 'all' ? '' : filter + ' '}signals right now. New signals are generated every 5 minutes.
          </p>
        </div>
      )}

      {!isLoading && (
        <div className="space-y-3">
          {filtered.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </div>
  );
}
