import type { Signal } from '@/lib/types';

interface TargetProgressBarProps {
  signal: Signal;
  livePrice?: number;
}

/**
 * Horizontal bar showing current price position between stop-loss and target.
 * Left edge = stop-loss, right edge = target. Dot marks current position.
 *
 * Colorblind accessibility:
 * - Diagonal hatch pattern on the stop-loss zone (distinguishable without color)
 * - Text labels "Stop" and "Target" at each end
 * - ▲ marker icon on the current price dot
 */
export function TargetProgressBar({ signal, livePrice }: TargetProgressBarProps) {
  const stop = parseFloat(signal.stop_loss);
  const target = parseFloat(signal.target_price);
  const current = livePrice ?? parseFloat(signal.current_price);

  if (!stop || !target || !current || target === stop) return null;

  const range = target - stop;
  const progress = Math.max(0, Math.min(100, ((current - stop) / range) * 100));

  const isBuyish = signal.signal_type.includes('BUY');

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[10px] font-mono text-text-muted mb-0.5">
        <span className="text-signal-sell">⛔ Stop</span>
        <span className="text-signal-buy">🎯 Target</span>
      </div>
      <div
        className="relative w-full h-2 rounded-full bg-bg-secondary overflow-hidden"
        role="img"
        aria-label={`Price at ${Math.round(progress)}% between stop-loss and target`}
      >
        {/* Gradient bar */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: isBuyish
              ? 'linear-gradient(to right, #FF5252, #FFD740, #00E676)'
              : 'linear-gradient(to right, #00E676, #FFD740, #FF5252)',
          }}
        />
        {/* Diagonal hatch on stop-loss zone for colorblind accessibility */}
        <svg className="absolute inset-0 w-full h-full" aria-hidden="true">
          <defs>
            <pattern id="stop-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="4" stroke="rgba(0,0,0,0.25)" strokeWidth="1.5" />
            </pattern>
          </defs>
          {/* Hatch covers the stop-loss third of the bar */}
          <rect
            x={isBuyish ? '0' : '66.6%'}
            y="0"
            width="33.4%"
            height="100%"
            fill="url(#stop-hatch)"
          />
        </svg>
        {/* Current price marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-text-primary border-2 border-bg-primary shadow-sm"
          style={{ left: `calc(${progress}% - 5px)`, transition: 'left 0.7s ease-out' }}
        />
      </div>
    </div>
  );
}
