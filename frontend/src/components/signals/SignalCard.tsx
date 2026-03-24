'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { Signal } from '@/lib/types';
import { formatPrice, formatDate, shortSymbol, formatTimeRemaining } from '@/utils/formatters';
import { SIGNAL_COLORS, MARKET_LABELS, BADGE_LABELS } from '@/lib/constants';
import { useMarketStore } from '@/store/marketStore';
import { AIReasoningPanel } from './AIReasoningPanel';
import { TargetProgressBar } from './TargetProgressBar';

const BADGE_ICONS: Record<string, string> = {
  STRONG_BUY: '▲▲',
  BUY: '▲',
  HOLD: '◆',
  SELL: '▼',
  STRONG_SELL: '▼▼',
};

interface SignalCardProps {
  signal: Signal;
}

export function SignalCard({ signal }: SignalCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const color = SIGNAL_COLORS[signal.signal_type];

  // Live price from market store
  const normalizedSymbol = shortSymbol(signal.symbol);
  const { stocks, crypto, forex } = useMarketStore();
  const allSnapshots = [...stocks, ...crypto, ...forex];
  const liveSnapshot = allSnapshots.find(
    (s) => shortSymbol(s.symbol) === normalizedSymbol,
  );
  const signalPrice = parseFloat(signal.current_price);
  const livePrice = liveSnapshot ? parseFloat(String(liveSnapshot.price)) : null;
  const priceChangePct = livePrice ? ((livePrice - signalPrice) / signalPrice) * 100 : null;

  // Expiry countdown
  const expiresAt = signal.expires_at ? new Date(signal.expires_at).getTime() : null;
  const timeRemaining = expiresAt ? expiresAt - Date.now() : null;
  const isExpiringSoon = timeRemaining !== null && timeRemaining > 0 && timeRemaining < 24 * 3600000;

  // Signal age warning
  const ageHours = (Date.now() - new Date(signal.created_at).getTime()) / 3600000;
  const ageDays = Math.floor(ageHours / 24);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      className="bg-bg-card/[0.04] border border-border-default rounded-xl p-4 hover:border-border-hover hover:-translate-y-px hover:shadow-lg hover:shadow-black/10 transition-all duration-200 cursor-pointer"
      style={{ borderLeftColor: color, borderLeftWidth: 3 }}
      onClick={() => setIsExpanded(!isExpanded)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsExpanded(!isExpanded); } }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-sm font-display font-semibold text-text-primary">
            {shortSymbol(signal.symbol)}
          </span>
          <span
            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-display font-semibold"
            style={{ backgroundColor: `${color}20`, color }}
          >
            <span aria-hidden="true">{BADGE_ICONS[signal.signal_type] ?? ''}</span>{' '}
            {BADGE_LABELS[signal.signal_type]} · {signal.confidence}%
          </span>
        </div>

        <div className="text-right">
          <p className="text-sm font-mono text-text-primary">
            {formatPrice(signal.current_price, signal.market_type)}
          </p>
          <p className="text-xs text-text-muted">
            {signal.timeframe ?? '—'}
          </p>
        </div>
      </div>

      {/* Market + date + Target/Stop row */}
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-xs text-text-muted">
          {MARKET_LABELS[signal.market_type]} · {formatDate(signal.created_at)}
        </span>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-signal-buy">
            {formatPrice(signal.target_price, signal.market_type)}
          </span>
          <span className="text-signal-sell">
            {formatPrice(signal.stop_loss, signal.market_type)}
          </span>
          {isExpiringSoon && timeRemaining !== null && timeRemaining > 0 && (
            <span className="text-signal-sell">
              {formatTimeRemaining(timeRemaining)}
            </span>
          )}
        </div>
      </div>

      {/* ── EXPANDED CONTENT (3 sections: progress, AI, action) ── */}

      {/* Progress section: live delta + target progress bar */}
      <div
        className="grid transition-all duration-300 ease-in-out"
        style={{ gridTemplateRows: isExpanded ? '1fr' : '0fr' }}
      >
        <div className="overflow-hidden">
        {isExpanded && (
        <div className="mt-3 pt-3 border-t border-border-default animate-fade-in-down">
          {livePrice != null && priceChangePct != null && Math.abs(priceChangePct) >= 0.01 && (
            <p className="text-xs font-mono mb-2">
              <span className="text-text-muted">Live:</span>{' '}
              <span className={priceChangePct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}>
                {formatPrice(String(livePrice), signal.market_type)} ({priceChangePct >= 0 ? '+' : ''}{priceChangePct.toFixed(2)}%)
              </span>
            </p>
          )}
          <TargetProgressBar signal={signal} livePrice={livePrice ?? undefined} />
          {ageHours > 48 && (
            <p className="text-xs mt-1.5 text-signal-hold">
              {ageHours > 120
                ? `Signal is ${ageDays}d old — verify before acting`
                : `Signal is ${ageDays}d old — check conditions`}
            </p>
          )}
        </div>
      )}
        </div>
      </div>

      {/* AI Reasoning */}
      <AIReasoningPanel reasoning={signal.ai_reasoning} isExpanded={isExpanded} />

      {/* Action link */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-border-default animate-fade-in-down" onClick={(e) => e.stopPropagation()}>
          <Link href={`/signal/${signal.id}`} className="text-xs text-accent-purple hover:underline">
            View full analysis →
          </Link>
        </div>
      )}

    </div>
  );
}
