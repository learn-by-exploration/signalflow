'use client';

import { useState } from 'react';
import type { Signal } from '@/lib/types';
import { formatPrice, formatPercent, formatDate, shortSymbol, formatTimeRemaining } from '@/utils/formatters';
import { SIGNAL_COLORS, MARKET_LABELS } from '@/lib/constants';
import { SignalBadge } from './SignalBadge';
import { ConfidenceGauge } from './ConfidenceGauge';
import { AIReasoningPanel } from './AIReasoningPanel';
import { RiskCalculator } from './RiskCalculator';
import { ShareButton } from './ShareButton';
import { TargetProgressBar } from './TargetProgressBar';
import { Sparkline } from '@/components/markets/Sparkline';
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
  const recentCloses = (signal.technical_data?.recent_closes ?? []) as number[];
  const isBuyish = signal.signal_type.includes('BUY');

  // Sentiment from AI engine
  const sentimentData = signal.sentiment_data as Record<string, unknown> | null;
  const marketImpact = sentimentData?.market_impact as string | undefined;
  const sentimentScore = sentimentData?.sentiment_score as number | undefined;
  const sentimentLabel = marketImpact
    ? `${marketImpact === 'positive' ? 'Bullish' : marketImpact === 'negative' ? 'Bearish' : 'Neutral'}${sentimentScore != null ? ` (${sentimentScore})` : ''}`
    : null;
  const sentimentSignal: 'buy' | 'sell' | 'neutral' =
    marketImpact === 'positive' ? 'buy' : marketImpact === 'negative' ? 'sell' : 'neutral';

  // Expiry countdown
  const expiresAt = signal.expires_at ? new Date(signal.expires_at).getTime() : null;
  const timeRemaining = expiresAt ? expiresAt - Date.now() : null;
  const isExpiringSoon = timeRemaining !== null && timeRemaining > 0 && timeRemaining < 24 * 3600000;

  return (
    <div
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      className="bg-bg-card border border-border-default rounded-xl p-4 hover:border-border-hover transition-all duration-200 cursor-pointer"
      style={{ borderLeftColor: color, borderLeftWidth: 3 }}
      onClick={() => setIsExpanded(!isExpanded)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsExpanded(!isExpanded); } }}
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

        <div className="text-right flex items-center gap-2">
          {recentCloses.length >= 2 && (
            <Sparkline data={recentCloses} positive={isBuyish} width={50} height={18} />
          )}
          <div>
            <p className="text-sm font-mono text-text-primary">
              {formatPrice(signal.current_price, signal.market_type)}
            </p>
            <p className="text-xs text-text-muted">
              {signal.timeframe ?? '—'}
            </p>
          </div>
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
        {timeRemaining !== null && timeRemaining > 0 && (
          <span className={`ml-auto ${isExpiringSoon ? 'text-signal-sell' : 'text-text-muted'}`}>
            ⏱ {formatTimeRemaining(timeRemaining)}
          </span>
        )}
      </div>

      {/* Target progress bar */}
      <TargetProgressBar signal={signal} />

      {/* Technical indicators + sentiment (collapsed) */}
      {(rsi || macd || volume || sentimentLabel) && (
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
          {sentimentLabel && (
            <IndicatorPill
              label="Sentiment"
              value={sentimentLabel}
              signal={sentimentSignal}
            />
          )}
        </div>
      )}

      {/* AI Reasoning (expanded) */}
      <AIReasoningPanel reasoning={signal.ai_reasoning} isExpanded={isExpanded} />

      {/* Quick Action Guide (expanded) */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-border-default">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">💡</span>
            <p className="text-xs font-display font-medium text-accent-purple">What To Do</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-text-secondary">
            <div className="flex items-start gap-1.5">
              <span className="text-accent-purple font-bold">1.</span>
              <span>Use the risk calculator below to decide your position size</span>
            </div>
            <div className="flex items-start gap-1.5">
              <span className="text-accent-purple font-bold">2.</span>
              <span>Set your stop-loss at <span className="text-signal-sell font-mono">{formatPrice(signal.stop_loss, signal.market_type)}</span> to limit downside</span>
            </div>
            <div className="flex items-start gap-1.5">
              <span className="text-accent-purple font-bold">3.</span>
              <span>Watch for target at <span className="text-signal-buy font-mono">{formatPrice(signal.target_price, signal.market_type)}</span> — {signal.timeframe ?? 'check back regularly'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Risk Calculator (expanded) */}
      {isExpanded && <RiskCalculator signal={signal} />}

      {/* Share button (expanded) */}
      {isExpanded && (
        <div className="flex justify-end mt-2" onClick={(e) => e.stopPropagation()}>
          <ShareButton signalId={signal.id} />
        </div>
      )}

      {/* Expand indicator */}
      <div className="flex justify-center mt-2">
        <span className={`text-text-muted text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </div>
    </div>
  );
}
