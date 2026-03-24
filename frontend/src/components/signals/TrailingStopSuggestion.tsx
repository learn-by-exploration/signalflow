'use client';

import type { Signal } from '@/lib/types';

interface TrailingStopProps {
  signal: Signal;
  livePrice?: number;
}

/**
 * Suggests trailing stop-loss levels based on ATR and current price movement.
 * Shows initial stop, and adaptive trailing stops at 25%, 50%, 75% of target.
 */
export function TrailingStopSuggestion({ signal, livePrice }: TrailingStopProps) {
  const entry = parseFloat(signal.current_price);
  const target = parseFloat(signal.target_price);
  const stop = parseFloat(signal.stop_loss);
  const current = livePrice ?? entry;

  if (!entry || !target || !stop) return null;

  const isBuy = signal.signal_type.includes('BUY');
  const range = Math.abs(target - entry);
  const stopDistance = Math.abs(entry - stop);

  // Progress toward target (0 = at entry, 1 = at target)
  const progress = isBuy
    ? (current - entry) / (target - entry)
    : (entry - current) / (entry - target);
  const progressPct = Math.max(0, Math.min(progress * 100, 100));

  // Trailing stop levels at milestones
  const levels = [
    { milestone: 'Entry', pct: 0, stop: stop, active: true },
    {
      milestone: '25% to target',
      pct: 25,
      stop: isBuy ? entry + range * 0.05 : entry - range * 0.05,
      active: progressPct >= 25,
    },
    {
      milestone: '50% to target',
      pct: 50,
      stop: isBuy ? entry + range * 0.2 : entry - range * 0.2,
      active: progressPct >= 50,
    },
    {
      milestone: '75% to target',
      pct: 75,
      stop: isBuy ? entry + range * 0.4 : entry - range * 0.4,
      active: progressPct >= 75,
    },
  ];

  const currentLevel = [...levels].reverse().find((l) => l.active) ?? levels[0];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-base">📏</span>
        <h3 className="text-sm font-display font-semibold">Trailing Stop Suggestion</h3>
      </div>

      {/* Current status */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-text-muted">Progress to target:</span>
        <span className={`font-mono ${progressPct > 50 ? 'text-signal-buy' : 'text-text-secondary'}`}>
          {progressPct.toFixed(1)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-purple rounded-full transition-all duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Trailing stop levels */}
      <div className="space-y-1.5">
        {levels.map((level) => (
          <div
            key={level.milestone}
            className={`flex items-center justify-between text-xs px-2 py-1.5 rounded-lg ${
              currentLevel.milestone === level.milestone
                ? 'bg-accent-purple/10 border border-accent-purple/30'
                : level.active
                  ? 'bg-bg-secondary'
                  : 'opacity-40'
            }`}
          >
            <span className={level.active ? 'text-text-secondary' : 'text-text-muted'}>
              {currentLevel.milestone === level.milestone && '→ '}
              {level.milestone}
            </span>
            <span className="font-mono text-text-primary">
              Stop: {level.stop.toFixed(signal.market_type === 'forex' ? 4 : 2)}
            </span>
          </div>
        ))}
      </div>

      <p className="text-xs text-text-muted">
        Move your stop-loss up as price approaches target to lock in gains.
        {currentLevel.pct > 0 && (
          <span className="text-accent-purple">
            {' '}Suggested stop now: {currentLevel.stop.toFixed(signal.market_type === 'forex' ? 4 : 2)}
          </span>
        )}
      </p>
    </div>
  );
}
