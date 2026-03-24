'use client';

import { useEffect, useRef } from 'react';
import type { MarketSnapshot } from '@/lib/types';
import { formatPrice, formatPercent, changeDirection, shortSymbol } from '@/utils/formatters';
import { MARKET_LABELS } from '@/lib/constants';
import { useMarketStore } from '@/store/marketStore';

interface MarketOverviewProps {
  stocks: MarketSnapshot[];
  crypto: MarketSnapshot[];
  forex: MarketSnapshot[];
  isLoading: boolean;
  lastUpdated: string | null;
}

const STATUS_STYLES = {
  connected: { dot: 'bg-signal-buy', label: 'Live' },
  connecting: { dot: 'bg-signal-hold animate-pulse', label: 'Connecting' },
  reconnecting: { dot: 'bg-signal-hold animate-pulse', label: 'Reconnecting' },
  disconnected: { dot: 'bg-signal-sell', label: 'Offline' },
} as const;

function MarketTicker({ snapshot }: { snapshot: MarketSnapshot }) {
  const dir = changeDirection(snapshot.change_pct);
  const pctColor =
    dir === 'up' ? 'text-signal-buy' : dir === 'down' ? 'text-signal-sell' : 'text-text-muted';
  const prevPriceRef = useRef<string>(snapshot.price);
  const flashRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (prevPriceRef.current !== snapshot.price && flashRef.current) {
      const newPrice = parseFloat(snapshot.price);
      const oldPrice = parseFloat(prevPriceRef.current);
      const cls = newPrice > oldPrice ? 'price-flash-up' : 'price-flash-down';
      flashRef.current.classList.remove('price-flash-up', 'price-flash-down');
      // Force reflow to restart animation
      void flashRef.current.offsetWidth;
      flashRef.current.classList.add(cls);
      prevPriceRef.current = snapshot.price;
    }
  }, [snapshot.price]);

  return (
    <div ref={flashRef} className="flex items-center gap-2 whitespace-nowrap rounded px-1">
      <span className="text-text-muted text-xs">{shortSymbol(snapshot.symbol)}</span>
      <span className="font-mono text-xs text-text-primary">
        {formatPrice(snapshot.price, snapshot.market_type)}
      </span>
      <span className={`font-mono text-xs ${pctColor}`}>{formatPercent(snapshot.change_pct)}</span>
    </div>
  );
}

export function MarketOverview({ stocks, crypto, forex, isLoading, lastUpdated }: MarketOverviewProps) {
  const wsStatus = useMarketStore((s) => s.wsStatus);
  const fetchError = useMarketStore((s) => s.fetchError);
  const statusStyle = STATUS_STYLES[wsStatus];

  // Detect stale data (>5 minutes old)
  const isStale = lastUpdated && (Date.now() - new Date(lastUpdated).getTime()) > 5 * 60 * 1000;

  // Show top 3 symbols from each market
  const topStocks = stocks.slice(0, 3);
  const topCrypto = crypto.slice(0, 3);
  const topForex = forex.slice(0, 3);

  const hasData = topStocks.length + topCrypto.length + topForex.length > 0;

  return (
    <div className="bg-bg-secondary/60 border-b border-border-default px-4 py-2">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 sm:gap-0">
        <div className="flex items-center gap-2 shrink-0">
          {/* Connection status dot */}
          <div className="flex items-center gap-1" title={statusStyle.label}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
          </div>
          {lastUpdated && (
            <span className={`text-[10px] font-mono ${isStale ? 'text-signal-sell' : 'text-text-muted'}`}>
              {new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              {isStale && ' (stale)'}
            </span>
          )}
        </div>

        {isLoading && !hasData ? (
          <div className="flex gap-4 text-xs text-text-muted animate-pulse">
            <span>Loading markets...</span>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-6 overflow-x-auto scrollbar-none">
            {topStocks.length > 0 && (
              <MarketSection label={MARKET_LABELS.stock} snapshots={topStocks} />
            )}
            {topCrypto.length > 0 && (
              <MarketSection label={MARKET_LABELS.crypto} snapshots={topCrypto} />
            )}
            {topForex.length > 0 && (
              <MarketSection label={MARKET_LABELS.forex} snapshots={topForex} />
            )}
          </div>
        )}
      </div>
      {fetchError && (
        <div className="max-w-7xl mx-auto px-4 py-1">
          <p className="text-[10px] text-signal-hold">{fetchError}</p>
        </div>
      )}
    </div>
  );
}

function MarketSection({ label, snapshots }: { label: string; snapshots: MarketSnapshot[] }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[10px] text-text-muted uppercase tracking-wider">{label}</span>
      {snapshots.map((s) => (
        <MarketTicker key={s.symbol} snapshot={s} />
      ))}
    </div>
  );
}
