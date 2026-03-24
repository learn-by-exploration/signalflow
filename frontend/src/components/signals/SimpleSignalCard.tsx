'use client';

import Link from 'next/link';
import type { Signal } from '@/lib/types';
import { shortSymbol } from '@/utils/formatters';
import { SIGNAL_COLORS, BADGE_LABELS } from '@/lib/constants';

const BADGE_ICONS: Record<string, string> = {
  STRONG_BUY: '▲▲',
  BUY: '▲',
  HOLD: '◆',
  SELL: '▼',
  STRONG_SELL: '▼▼',
};

const SIMPLE_ACTION: Record<string, string> = {
  STRONG_BUY: 'Consider buying — strong signals',
  BUY: 'Consider buying',
  HOLD: 'Wait and watch',
  SELL: 'Consider selling',
  STRONG_SELL: 'Consider selling — strong signals',
};

interface SimpleSignalCardProps {
  signal: Signal;
}

export function SimpleSignalCard({ signal }: SimpleSignalCardProps) {
  const color = SIGNAL_COLORS[signal.signal_type];
  const icon = BADGE_ICONS[signal.signal_type];

  return (
    <Link
      href={`/signal/${signal.id}`}
      className="block bg-bg-card/[0.04] border border-border-default rounded-xl p-4 hover:border-border-hover hover:-translate-y-px hover:shadow-lg hover:shadow-black/10 transition-all duration-200"
      style={{ borderLeftColor: color, borderLeftWidth: 3 }}
    >
      {/* Symbol + Action */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2.5">
          <span className="text-base font-display font-bold text-text-primary">
            {shortSymbol(signal.symbol)}
          </span>
          <span
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-display font-semibold"
            style={{ backgroundColor: `${color}20`, color }}
          >
            <span aria-hidden="true">{icon}</span> {BADGE_LABELS[signal.signal_type]}
          </span>
        </div>
        <span className="text-sm font-mono" style={{ color }}>
          {signal.confidence}%
        </span>
      </div>

      {/* Plain English action */}
      <p className="text-sm text-text-secondary font-display mb-2">
        {SIMPLE_ACTION[signal.signal_type]}
      </p>

      {/* AI reasoning (truncated) */}
      <p className="text-xs text-text-muted leading-relaxed line-clamp-2">
        {signal.ai_reasoning}
      </p>
    </Link>
  );
}
