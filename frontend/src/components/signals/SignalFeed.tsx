'use client';

import { useState, useMemo, useRef, useCallback } from 'react';
import type { Signal, MarketType } from '@/lib/types';
import { useSignalStore } from '@/store/signalStore';
import { api } from '@/lib/api';
import { SignalCard } from './SignalCard';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { KeyboardHelpModal } from '@/components/shared/KeyboardHelpModal';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import Link from 'next/link';

interface SignalFeedProps {
  signals: Signal[];
  isLoading: boolean;
  error: string | null;
}

type FilterType = 'all' | MarketType;
type SortType = 'newest' | 'confidence' | 'reward';

const FILTER_OPTIONS: { value: FilterType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

const SORT_OPTIONS: { value: SortType; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'confidence', label: 'Confidence' },
  { value: 'reward', label: 'Reward' },
];

export function SignalFeed({ signals, isLoading, error }: SignalFeedProps) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<SortType>('newest');
  const [search, setSearch] = useState('');
  const [loadingMore, setLoadingMore] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const total = useSignalStore((s) => s.total);
  const appendSignals = useSignalStore((s) => s.appendSignals);
  const hasMore = total != null && signals.length < total;

  const handleFilterChange = useCallback((f: 'all' | 'stock' | 'crypto' | 'forex') => {
    setFilter(f);
  }, []);

  const handleFocusSearch = useCallback(() => {
    searchRef.current?.focus();
  }, []);

  const { showHelp, setShowHelp } = useKeyboardShortcuts({
    onFilterChange: handleFilterChange,
    onFocusSearch: handleFocusSearch,
  });

  const handleLoadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const res = await api.getSignals(new URLSearchParams({ offset: String(signals.length), limit: '20' })) as { data: Signal[]; meta: { total?: number } };
      appendSignals(res.data, res.meta.total);
    } catch {
      // silently fail
    } finally {
      setLoadingMore(false);
    }
  }, [signals.length, appendSignals]);

  const filtered = useMemo(() => {
    let result = signals;
    if (filter !== 'all') {
      result = result.filter((s) => s.market_type === filter);
    }
    if (search.trim()) {
      const q = search.trim().toUpperCase();
      result = result.filter((s) => s.symbol.toUpperCase().includes(q));
    }
    // Sort
    result = [...result].sort((a, b) => {
      if (sortBy === 'confidence') return b.confidence - a.confidence;
      if (sortBy === 'reward') {
        const rewardA = Math.abs((parseFloat(a.target_price) - parseFloat(a.current_price)) / parseFloat(a.current_price));
        const rewardB = Math.abs((parseFloat(b.target_price) - parseFloat(b.current_price)) / parseFloat(b.current_price));
        return rewardB - rewardA;
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
    return result;
  }, [signals, filter, search, sortBy]);

  return (
    <div className="space-y-4">
      {/* Header + Filters */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-display font-semibold">Active Signals</h2>
        <div className="flex items-center gap-3">
          {/* Sort */}
          <div className="flex gap-1">
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setSortBy(opt.value)}
                aria-label={`Sort by ${opt.label}`}
                aria-pressed={sortBy === opt.value}
                className={`px-2 py-0.5 text-xs rounded border transition-colors ${
                  sortBy === opt.value
                    ? 'border-accent-purple/50 text-accent-purple bg-accent-purple/10'
                    : 'border-transparent text-text-muted hover:text-text-secondary'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {/* Market filter */}
          <div className="flex gap-2">
            {FILTER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value)}
                aria-label={`Filter by ${opt.label}`}
                aria-pressed={filter === opt.value}
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
      </div>

      {/* Symbol Search */}
      <div className="relative">
        <input
          type="text"
          ref={searchRef}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search symbol (e.g. HDFC, BTC, EUR)..."
          className="w-full bg-bg-card border border-border-default rounded-lg pl-8 pr-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple/50 font-mono"
        />
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted text-xs">🔍</span>
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary text-xs"
          >
            ✕
          </button>
        )}
      </div>
      {search && (
        <p className="text-xs text-text-muted -mt-2">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''} for &ldquo;{search}&rdquo;
          {filtered.length === 0 && <span> — try a shorter name or switch market filter</span>}
        </p>
      )}

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
        <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-4">
          <p className="text-3xl">📡</p>
          <p className="text-text-secondary text-sm">
            No {filter === 'all' ? '' : filter + ' '}signals right now. Signals are generated every 5 minutes.
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-xs">
            <a href="/how-it-works" className="text-accent-purple hover:underline">💡 Learn how signals work</a>
            <span className="text-text-muted">•</span>
            <a href="/alerts" className="text-accent-purple hover:underline">🔔 Set up alert preferences</a>
            <span className="text-text-muted">•</span>
            <a href="/history" className="text-accent-purple hover:underline">📜 View past signals</a>
          </div>
        </div>
      )}

      {!isLoading && (
        <div className="space-y-3">
          {filtered.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}

      {/* Pagination info + Load More */}
      {!isLoading && total != null && total > 0 && (
        <div className="text-center space-y-2 pt-2">
          <p className="text-xs text-text-muted">
            Showing {signals.length} of {total} signals
          </p>
          {hasMore && (
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="px-4 py-2 text-sm rounded-lg border border-accent-purple/50 text-accent-purple hover:bg-accent-purple/10 transition-colors disabled:opacity-50"
            >
              {loadingMore ? 'Loading...' : 'Load More'}
            </button>
          )}
        </div>
      )}

      <KeyboardHelpModal isOpen={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  );
}
