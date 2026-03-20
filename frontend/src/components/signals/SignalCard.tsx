'use client';

import { useState } from 'react';
import type { Signal } from '@/lib/types';
import { formatPrice, formatPercent, formatDate, shortSymbol } from '@/utils/formatters';
import { SIGNAL_COLORS, MARKET_LABELS } from '@/lib/constants';
import { SignalBadge } from './SignalBadge';
import { ConfidenceGauge } from './ConfidenceGauge';
import { AIReasoningPanel } from './AIReasoningPanel';
import { IndicatorPill } from '@/components/shared/IndicatorPill';

interface SignalCardProps {
  signal: Signal;
}

export function SignalCard({ signal }: SignalCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const color = SIGNAL_COLORS[signal.signal_type];

  const technicalData = signal.technical_data as Record<string, Record<string, unknown>>;
  const rsi = technicalData?.rsi;
  const macd = technicalData?.macd;
  const volume = technicalData?.volume;

  return (
    <div
      className="bg-bg-card border border-border-default rounded-xl p-4 hover:border-border-hover transition-all cursor-pointer"
      style={{ borderLeftColor: color, borderLeftWidth: 3 }}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <ConfidenceGauge
            confidence={signal.confidence}
            signalType={signal.signal_type}
            size={48}
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-display font-semibold text-text-primary">
                {shortSymbol(signal.symbol)}
              </span>
              <SignalBadge signalType={signal.signal_type} />
            </div>
            <span className="text-xs text-text-muted">
              {MARKET_LABELS[signal.market_type]} · {formatDate(signal.created_at)}
            </span>
          </div>
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

      {/* Target and stop-loss row */}
      <div className="flex items-center gap-4 text-xs font-mono mt-1">
        <span className="text-signal-buy">
          🎯 {formatPrice(signal.target_price, signal.market_type)}
        </span>
        <span className="text-signal-sell">
          🛑 {formatPrice(signal.stop_loss, signal.market_type)}
        </span>
      </div>

      {/* Technical indicators (collapsed) */}
      {(rsi || macd || volume) && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {rsi?.value != null && (
            <IndicatorPill
              label="RSI"
              value={String(rsi.value)}
              signal={rsi.signal as 'buy' | 'sell' | 'neutral'}
            />
          )}
          {macd?.signal != null && (
            <IndicatorPill
              label="MACD"
              value={String(macd.signal === 'buy' ? 'Bullish' : macd.signal === 'sell' ? 'Bearish' : 'Neutral')}
              signal={macd.signal as 'buy' | 'sell' | 'neutral'}
            />
          )}
          {volume?.ratio != null && (
            <IndicatorPill
              label="Vol"
              value={`${volume.ratio}x`}
              signal={volume.signal as 'buy' | 'sell' | 'neutral'}
            />
          )}
        </div>
      )}

      {/* AI Reasoning (expanded) */}
      <AIReasoningPanel reasoning={signal.ai_reasoning} isExpanded={isExpanded} />

      {/* Expand indicator */}
      <div className="flex justify-center mt-2">
        <span className={`text-text-muted text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </div>
    </div>
  );
}
