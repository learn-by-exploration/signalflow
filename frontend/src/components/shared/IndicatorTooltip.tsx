'use client';

import { useState } from 'react';

const INDICATOR_EXPLANATIONS: Record<string, string> = {
  'RSI': 'Relative Strength Index — measures if a stock is overbought (>70) or oversold (<30). Range: 0-100.',
  'RSI (14)': 'Relative Strength Index (14-period) — measures if a stock is overbought (>70) or oversold (<30). Range: 0-100.',
  'MACD': 'Moving Average Convergence Divergence — shows trend direction and momentum. Bullish when MACD crosses above signal line.',
  'Bollinger': 'Bollinger Bands — price channels based on volatility. Near lower band = potential buy, near upper band = potential sell.',
  'Volume': 'Trading volume relative to average. High volume (>1.5x) confirms price moves; low volume suggests weak trends.',
  'SMA Cross': 'Simple Moving Average Crossover — when short-term SMA crosses above long-term SMA (Golden Cross) it signals uptrend.',
  'SMA': 'Simple Moving Average — smoothed price trend. Golden Cross (20>50) is bullish, Death Cross (20<50) is bearish.',
  'ATR': 'Average True Range — measures price volatility. Higher ATR = more volatile. Used to set targets and stop-losses.',
  'Target': 'The price level where you should consider taking profit. Calculated using 2× ATR above entry price.',
  'Stop-Loss': 'The price level where you should exit to limit losses. Calculated using 1× ATR below entry price. Always set a stop-loss.',
  'Confidence': 'How strongly technical indicators and AI sentiment agree on the signal direction. Higher = stronger consensus, not probability of profit.',
  'Win Rate': 'Percentage of past signals that hit their target price before hitting the stop-loss or expiring.',
};

interface IndicatorTooltipProps {
  term: string;
  children: React.ReactNode;
}

export function IndicatorTooltip({ term, children }: IndicatorTooltipProps) {
  const [show, setShow] = useState(false);
  const explanation = INDICATOR_EXPLANATIONS[term];

  if (!explanation) return <>{children}</>;

  return (
    <span
      className="relative inline-flex items-center gap-0.5 cursor-help"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      tabIndex={0}
      role="button"
      aria-describedby={show ? `tooltip-${term}` : undefined}
    >
      {children}
      <svg className="w-3 h-3 text-text-muted/50 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {show && (
        <span
          id={`tooltip-${term}`}
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-text-primary bg-bg-secondary border border-border-default rounded-lg shadow-xl max-w-[240px] whitespace-normal leading-relaxed animate-fade-in-down"
        >
          {explanation}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-bg-secondary" />
        </span>
      )}
    </span>
  );
}
