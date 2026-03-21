'use client';

import { useMarketStore } from '@/store/marketStore';
import { shortSymbol, formatPercent } from '@/utils/formatters';
import { MARKET_LABELS } from '@/lib/constants';
import type { MarketSnapshot } from '@/lib/types';

function HeatmapCell({ snapshot }: { snapshot: MarketSnapshot }) {
  const pct = parseFloat(String(snapshot.change_pct));
  const absPct = Math.abs(pct);
  // Intensity: 0.15 (base) to 0.6 (max intensity at 5%+)
  const intensity = Math.min(0.15 + (absPct / 5) * 0.45, 0.6);
  const bg = pct >= 0
    ? `rgba(0, 230, 118, ${intensity})`
    : `rgba(255, 82, 82, ${intensity})`;
  const textColor = pct >= 0 ? 'text-signal-buy' : 'text-signal-sell';

  return (
    <div
      className="rounded-md px-2 py-1.5 text-center cursor-default transition-colors hover:brightness-125"
      style={{ backgroundColor: bg }}
      title={`${shortSymbol(snapshot.symbol)}: ${formatPercent(pct)}`}
    >
      <div className="text-[10px] font-display font-medium text-text-primary leading-tight">
        {shortSymbol(snapshot.symbol)}
      </div>
      <div className={`text-[10px] font-mono font-semibold leading-tight ${textColor}`}>
        {formatPercent(pct)}
      </div>
    </div>
  );
}

export function MarketHeatmap() {
  const { stocks, crypto, forex } = useMarketStore();
  const hasData = stocks.length + crypto.length + forex.length > 0;

  if (!hasData) return null;

  const sections: { key: string; label: string; data: MarketSnapshot[] }[] = [
    { key: 'stock', label: MARKET_LABELS.stock, data: stocks },
    { key: 'crypto', label: MARKET_LABELS.crypto, data: crypto },
    { key: 'forex', label: MARKET_LABELS.forex, data: forex },
  ].filter((s) => s.data.length > 0);

  return (
    <div className="bg-bg-card border border-border-default rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-display font-medium text-text-secondary">Market Pulse</h3>
      {sections.map((section) => (
        <div key={section.key}>
          <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{section.label}</p>
          <div className="grid grid-cols-4 sm:grid-cols-5 gap-1">
            {section.data.map((snapshot) => (
              <HeatmapCell key={snapshot.symbol} snapshot={snapshot} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
