'use client';

import { SIGNAL_COLORS } from '@/lib/constants';
import type { SignalType } from '@/lib/types';

interface ConfidenceBreakdownProps {
  technicalScore: number;
  sentimentScore: number;
  signalType: SignalType;
}

/**
 * Stacked bar showing the breakdown of confidence: technical (60%) vs sentiment (40%).
 */
export function ConfidenceBreakdown({ technicalScore, sentimentScore, signalType }: ConfidenceBreakdownProps) {
  const color = SIGNAL_COLORS[signalType];
  const techWidth = Math.max(technicalScore, 2);
  const sentWidth = Math.max(sentimentScore, 2);

  return (
    <div className="space-y-2">
      <p className="text-xs font-display font-medium text-text-muted">Confidence Breakdown</p>
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted w-20">Technical</span>
          <div className="flex-1 h-2.5 bg-bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${techWidth}%`, backgroundColor: color }}
            />
          </div>
          <span className="text-xs font-mono text-text-secondary w-10 text-right">{technicalScore}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted w-20">Sentiment</span>
          <div className="flex-1 h-2.5 bg-bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${sentWidth}%`, backgroundColor: '#6366F1' }}
            />
          </div>
          <span className="text-xs font-mono text-text-secondary w-10 text-right">{sentimentScore}%</span>
        </div>
      </div>
      <p className="text-xs text-text-muted">
        Final = Technical × 60% + Sentiment × 40%
      </p>
    </div>
  );
}
