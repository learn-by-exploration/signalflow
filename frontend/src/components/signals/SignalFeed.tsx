'use client';

import { useState, useMemo, useRef, useCallback } from 'react';
import type { Signal, MarketType } from '@/lib/types';
import { useSignalStore } from '@/store/signalStore';
import { api } from '@/lib/api';
import { SignalCard } from './SignalCard';
import { SignalFeedSkeleton } from '@/components/shared/Skeleton';
import { KeyboardHelpModal } from '@/components/shared/KeyboardHelpModal';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import Link from 'next/link';

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
  const [searchOpen, setSearchOpen] = useState(false);
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
    // Sort by confidence (default)
    result = [...result].sort((a, b) => b.confidence - a.confidence);
    return result;
  }, [signals, filter, search]);

  return (
    <div className="space-y-4">
      {/* Header + Filters */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-display font-semibold">Active Signals</h2>
        <div className="flex items-center gap-2">
          {/* Market filter */}
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              aria-label={`Filter by ${opt.label}`}
              aria-pressed={filter === opt.value}
              className={`min-h-[44px] min-w-[44px] px-3 py-2 text-xs rounded-full border transition-colors ${
                filter === opt.value
                  ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                  : 'border-border-default text-text-secondary hover:border-border-hover'
              }`}
            >
              {opt.label}
            </button>
          ))}
          {/* Search toggle */}
          <button
            onClick={() => { setSearchOpen(!searchOpen); if (searchOpen) setSearch(''); }}
            aria-label="Search symbols"
            className={`min-h-[44px] min-w-[44px] p-2.5 rounded-full border transition-colors ${
              searchOpen
                ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                : 'border-border-default text-text-muted hover:border-border-hover hover:text-text-secondary'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expandable search input */}
      {searchOpen && (
        <div className="relative">
          <input
            type="text"
            ref={searchRef}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search symbol..."
            autoFocus
            className="w-full bg-bg-card border border-border-default rounded-lg pl-3 pr-8 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple/50 font-mono"
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
      )}
      {search && (
        <p className="text-xs text-text-muted -mt-2">
          {filtered.length} result{filtered.length !== 1 ? 's' : ''} for &ldquo;{search}&rdquo;
          {filtered.length === 0 && <span> — try a shorter name or switch market filter</span>}
        </p>
      )}

      {/* Content */}
      {isLoading && (
        <SignalFeedSkeleton count={5} />
      )}

      {error && (
        <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-xl p-4 text-center">
          <p className="text-signal-sell text-sm">{error}</p>
        </div>
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
          <p className="text-text-secondary text-sm">
            No {filter === 'all' ? '' : filter + ' '}signals right now. Signals are generated every 5 minutes.
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-xs">
            <a href="/how-it-works" className="text-accent-purple hover:underline">Learn how signals work</a>
            <span className="text-text-muted">·</span>
            <a href="/alerts" className="text-accent-purple hover:underline">Set up alerts</a>
            <span className="text-text-muted">·</span>
            <a href="/history" className="text-accent-purple hover:underline">Past signals</a>
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
