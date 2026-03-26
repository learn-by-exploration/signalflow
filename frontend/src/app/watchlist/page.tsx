'use client';

import { useEffect, useState, useMemo } from 'react';
import { api } from '@/lib/api';
import type { Signal, MarketType } from '@/lib/types';
import { useToast } from '@/components/shared/Toast';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { SignalCard } from '@/components/signals/SignalCard';
import { SIGNAL_COLORS } from '@/lib/constants';

const SUGGESTED_SYMBOLS: { symbol: string; label: string; market: MarketType }[] = [
  { symbol: 'HDFCBANK.NS', label: 'HDFC Bank', market: 'stock' },
  { symbol: 'RELIANCE.NS', label: 'Reliance', market: 'stock' },
  { symbol: 'TCS.NS', label: 'TCS', market: 'stock' },
  { symbol: 'INFY.NS', label: 'Infosys', market: 'stock' },
  { symbol: 'BTCUSDT', label: 'Bitcoin', market: 'crypto' },
  { symbol: 'ETHUSDT', label: 'Ethereum', market: 'crypto' },
  { symbol: 'SOLUSDT', label: 'Solana', market: 'crypto' },
  { symbol: 'EUR/USD', label: 'EUR/USD', market: 'forex' },
  { symbol: 'USD/INR', label: 'USD/INR', market: 'forex' },
  { symbol: 'GBP/JPY', label: 'GBP/JPY', market: 'forex' },
];

function shortSymbol(s: string): string {
  return s.replace('.NS', '').replace('USDT', '');
}

export default function WatchlistPage() {
  const { toast } = useToast();
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [newSymbol, setNewSymbol] = useState('');

  async function loadData() {
    try {
      const [watchRes, sigRes] = await Promise.all([
        api.getWatchlist() as Promise<{ data: string[] }>,
        api.getSignals() as Promise<{ data: Signal[] }>,
      ]);
      setWatchlist(Array.isArray(watchRes.data) ? watchRes.data : []);
      setSignals(sigRes.data ?? []);
    } catch {
      toast('Failed to load watchlist', 'error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const watchlistSignals = useMemo(
    () => signals.filter((s) => watchlist.includes(s.symbol)),
    [signals, watchlist],
  );

  async function addSymbol(symbol: string) {
    const s = symbol.toUpperCase().trim();
    if (!s || watchlist.includes(s)) return;
    try {
      await api.updateWatchlist(s, 'add');
      setWatchlist((prev) => [...prev, s]);
      setNewSymbol('');
      toast(`${shortSymbol(s)} added to watchlist`, 'success');
    } catch {
      toast('Failed to add symbol', 'error');
    }
  }

  async function removeSymbol(symbol: string) {
    try {
      await api.updateWatchlist(symbol, 'remove');
      setWatchlist((prev) => prev.filter((s) => s !== symbol));
      toast(`${shortSymbol(symbol)} removed`, 'success');
    } catch {
      toast('Failed to remove symbol', 'error');
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-display font-semibold">Watchlist</h1>
          <span className="text-xs text-text-muted">{watchlist.length} symbol{watchlist.length !== 1 ? 's' : ''}</span>
        </div>

        {/* Add symbol */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && addSymbol(newSymbol)}
            placeholder="Add symbol (e.g. HDFCBANK.NS, BTCUSDT)"
            className="flex-1 bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
          />
          <button
            onClick={() => addSymbol(newSymbol)}
            disabled={!newSymbol.trim()}
            className="px-4 py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
          >
            + Add
          </button>
        </div>

        {/* Quick add suggestions */}
        {watchlist.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-text-muted">Quick add popular symbols:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_SYMBOLS.map((s) => (
                <button
                  key={s.symbol}
                  onClick={() => addSymbol(s.symbol)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-secondary hover:border-accent-purple/50 hover:text-accent-purple transition-colors"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Watchlist symbols */}
        {watchlist.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {watchlist.map((symbol) => {
              const hasSignal = watchlistSignals.some((s) => s.symbol === symbol);
              return (
                <div
                  key={symbol}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors ${
                    hasSignal
                      ? 'border-accent-purple/30 bg-accent-purple/5'
                      : 'border-border-default bg-bg-card'
                  }`}
                >
                  <span className="text-sm font-mono">{shortSymbol(symbol)}</span>
                  {hasSignal && (
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" title="Has active signal" />
                  )}
                  <button
                    onClick={() => removeSymbol(symbol)}
                    className="text-text-muted hover:text-signal-sell text-xs ml-1 transition-colors"
                    aria-label={`Remove ${shortSymbol(symbol)}`}
                  >
                    ✕
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Watchlist signals */}
        <section className="space-y-3">
          <h2 className="text-lg font-display font-semibold">
            Signals for Your Watchlist
            {watchlistSignals.length > 0 && (
              <span className="text-sm text-text-muted font-normal ml-2">
                ({watchlistSignals.length} active)
              </span>
            )}
          </h2>

          {watchlistSignals.length > 0 ? (
            <div className="space-y-3">
              {watchlistSignals
                .sort((a, b) => b.confidence - a.confidence)
                .map((signal) => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
            </div>
          ) : watchlist.length > 0 ? (
            <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
              <p className="text-3xl">🔍</p>
              <p className="text-text-secondary text-sm">
                No active signals for your watched symbols right now.
              </p>
              <p className="text-text-muted text-xs">
                Signals for {watchlist.map(shortSymbol).join(', ')} will appear here
                when they are generated. Signals update every 5 minutes.
              </p>
              <a href="/alerts" className="inline-block text-accent-purple text-xs hover:underline">
                Set up Telegram alerts to get notified →
              </a>
            </div>
          ) : (
            <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
              <p className="text-3xl">⭐</p>
              <p className="text-text-secondary text-sm">Add symbols to your watchlist to see personalized signals.</p>
              <p className="text-text-muted text-xs">
                Use the search bar above or click a suggestion to get started.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
