'use client';

import type { Signal } from '@/lib/types';
import { formatDate, formatTime, shortSymbol, formatPrice } from '@/utils/formatters';
import { SIGNAL_COLORS } from '@/lib/constants';

interface AlertTimelineProps {
  signals: Signal[];
}

export function AlertTimeline({ signals }: AlertTimelineProps) {
  const recent = signals.slice(0, 10);

  if (recent.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-display font-semibold">Recent Alerts</h2>
        <div className="bg-bg-card border border-border-default rounded-xl p-4">
          <p className="text-text-muted text-sm">
            Alerts will appear here as signals are generated.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Recent Alerts</h2>
      <div className="space-y-2">
        {recent.map((signal) => {
          const color = SIGNAL_COLORS[signal.signal_type];
          const isBuy = signal.signal_type.includes('BUY');
          const emoji = isBuy ? '🟢' : signal.signal_type === 'HOLD' ? '🟡' : '🔴';

          return (
            <div
              key={signal.id}
              className="bg-bg-card border border-border-default rounded-lg p-3 hover:border-border-hover transition-colors"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{emoji}</span>
                  <span className="text-sm font-display font-medium text-text-primary">
                    {shortSymbol(signal.symbol)}
                  </span>
                  <span
                    className="text-xs font-mono font-semibold"
                    style={{ color }}
                  >
                    {signal.signal_type.replace('_', ' ')}
                  </span>
                </div>
                <span className="text-xs text-text-muted">{formatTime(signal.created_at)}</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-text-secondary">
                <span>{formatPrice(signal.current_price, signal.market_type)}</span>
                <span className="text-text-muted">•</span>
                <span style={{ color }}>{signal.confidence}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
