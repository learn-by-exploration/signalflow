'use client';

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

  return (
    <div className="flex items-center gap-2 whitespace-nowrap">
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

  // Show top symbols from each market
  const topStocks = stocks.slice(0, 3);
  const topCrypto = crypto.slice(0, 3);
  const topForex = forex.slice(0, 3);

  const hasData = topStocks.length + topCrypto.length + topForex.length > 0;

  return (
    <div className="bg-bg-secondary/60 border-b border-border-default px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2 shrink-0">
          {/* Connection status dot */}
          <div className="flex items-center gap-1" title={statusStyle.label}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
            <span className="text-[10px] text-text-muted font-mono">{statusStyle.label}</span>
          </div>
          {lastUpdated && (
            <span className={`text-[10px] font-mono ${isStale ? 'text-signal-sell' : 'text-text-muted'}`}>
              · {new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              {isStale && ' (stale)'}
            </span>
          )}
        </div>

        {isLoading && !hasData ? (
          <div className="flex gap-4 text-xs text-text-muted animate-pulse">
            <span>Loading markets...</span>
          </div>
        ) : (
          <div className="flex items-center gap-6 overflow-x-auto scrollbar-none">
            {topStocks.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-text-muted uppercase tracking-wider">{MARKET_LABELS.stock}</span>
                {topStocks.map((s) => (
                  <MarketTicker key={s.symbol} snapshot={s} />
                ))}
              </div>
            )}
            {topCrypto.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-text-muted uppercase tracking-wider">{MARKET_LABELS.crypto}</span>
                {topCrypto.map((s) => (
                  <MarketTicker key={s.symbol} snapshot={s} />
                ))}
              </div>
            )}
            {topForex.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-text-muted uppercase tracking-wider">{MARKET_LABELS.forex}</span>
                {topForex.map((s) => (
                  <MarketTicker key={s.symbol} snapshot={s} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {fetchError && (
        <div className="max-w-7xl mx-auto px-4 py-1">
          <p className="text-[10px] text-signal-hold">⚠️ {fetchError}</p>
        </div>
      )}
    </div>
  );
}
