'use client';

import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import type { Signal, MarketType } from '@/lib/types';
import { useSignalStore } from '@/store/signalStore';
import { usePreferencesStore } from '@/store/preferencesStore';
import { api } from '@/lib/api';
import { SignalCard } from './SignalCard';
import { SimpleSignalCard } from './SimpleSignalCard';
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
type TimeframeFilter = 'all' | 'short' | 'medium' | 'long';

const FILTER_OPTIONS: { value: FilterType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

const TIMEFRAME_OPTIONS: { value: TimeframeFilter; label: string; desc: string }[] = [
  { value: 'all', label: 'Any', desc: 'All timeframes' },
  { value: 'short', label: 'Short', desc: 'Hours to days' },
  { value: 'medium', label: 'Medium', desc: '1-4 weeks' },
  { value: 'long', label: 'Long', desc: 'Months' },
];

/** Classify signal timeframe string into short/medium/long */
function classifyTimeframe(tf?: string): 'short' | 'medium' | 'long' {
  if (!tf) return 'medium';
  const lower = tf.toLowerCase();
  if (lower.includes('hour') || lower.includes('minute') || lower.includes('1 day') || lower.includes('1-2 day') || lower.includes('intraday')) return 'short';
  if (lower.includes('month') || lower.includes('quarter') || lower.includes('6') || lower.includes('year')) return 'long';
  return 'medium';
}

export function SignalFeed({ signals, isLoading, error }: SignalFeedProps) {
  const defaultFilter = usePreferencesStore((s) => s.defaultMarketFilter);
  const setDefaultMarketFilter = usePreferencesStore((s) => s.setDefaultMarketFilter);
  const [filter, setFilter] = useState<FilterType>(defaultFilter);
  const [timeframeFilter, setTimeframeFilter] = useState<TimeframeFilter>('all');
  const [search, setSearch] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const total = useSignalStore((s) => s.total);
  const appendSignals = useSignalStore((s) => s.appendSignals);
  const hasMore = total != null && signals.length < total;

  const handleFilterChange = useCallback((f: 'all' | 'stock' | 'crypto' | 'forex') => {
    setFilter(f);
    setDefaultMarketFilter(f);
  }, [setDefaultMarketFilter]);

  const handleFocusSearch = useCallback(() => {
    searchRef.current?.focus();
  }, []);

  const { showHelp, setShowHelp } = useKeyboardShortcuts({
    onFilterChange: handleFilterChange,
    onFocusSearch: handleFocusSearch,
  });

  const viewMode = usePreferencesStore((s) => s.viewMode);

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
    if (timeframeFilter !== 'all') {
      result = result.filter((s) => classifyTimeframe(s.timeframe) === timeframeFilter);
    }
    if (search.trim()) {
      const q = search.trim().toUpperCase();
      result = result.filter((s) => s.symbol.toUpperCase().includes(q));
    }
    // Sort by confidence (default)
    result = [...result].sort((a, b) => b.confidence - a.confidence);
    return result;
  }, [signals, filter, timeframeFilter, search]);

  return (
    <div className="space-y-4">
      {/* Header + Filters */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-xl font-display font-semibold">Active Signals</h2>
        <div className="flex items-center gap-2" data-tour="signal-filters">
          {/* Market filter */}
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { setFilter(opt.value); setDefaultMarketFilter(opt.value); }}
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

      {/* Timeframe filter (U10-2) */}
      <div className="flex items-center gap-2 flex-wrap -mt-1">
        <span className="text-[10px] text-text-muted">Timeframe:</span>
        {TIMEFRAME_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setTimeframeFilter(opt.value)}
            title={opt.desc}
            className={`px-2 py-1 text-[10px] rounded-full border transition-colors ${
              timeframeFilter === opt.value
                ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                : 'border-border-default text-text-muted hover:border-border-hover'
            }`}
          >
            {opt.label}
          </button>
        ))}
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
          <p className="text-3xl">
            {filter === 'stock' ? '📈' : filter === 'crypto' ? '🪙' : filter === 'forex' ? '💱' : '📊'}
          </p>
          <p className="text-text-secondary text-sm">
            No {filter === 'all' ? '' : filter + ' '}signals right now.
          </p>
          <p className="text-text-muted text-xs max-w-md mx-auto">
            {filter === 'stock'
              ? 'Indian stock signals are generated during NSE market hours (9:15 AM – 3:30 PM IST, Mon–Fri). Check back during trading hours.'
              : filter === 'crypto'
              ? 'Crypto signals fire 24/7, typically during high volatility periods. New signals are generated every 5 minutes.'
              : filter === 'forex'
              ? 'Forex signals are active during global market hours (Mon–Fri). Major pairs like EUR/USD are most active during London and New York sessions.'
              : 'Signals are generated every 5 minutes across stocks, crypto, and forex. Try filtering by market or check back soon.'}
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-xs pt-1">
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
            viewMode === 'simple'
              ? <SimpleSignalCard key={signal.id} signal={signal} />
              : <SignalCard key={signal.id} signal={signal} />
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
