import type { Signal } from '@/lib/types';

interface TargetProgressBarProps {
  signal: Signal;
  livePrice?: number;
}

/**
 * Horizontal bar showing current price position between stop-loss and target.
 * Left edge = stop-loss, right edge = target. Dot marks current position.
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
        <span className="text-signal-sell">🛑 Stop</span>
        <span className="text-signal-buy">🎯 Target</span>
      </div>
      <div className="relative w-full h-1.5 rounded-full bg-bg-secondary overflow-visible">
        {/* Gradient bar: red on left, green on right */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: isBuyish
              ? 'linear-gradient(to right, #FF5252, #FFD740, #00E676)'
              : 'linear-gradient(to right, #00E676, #FFD740, #FF5252)',
          }}
        />
        {/* Current price marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-text-primary border-2 border-bg-primary shadow-sm transition-all duration-500"
          style={{ left: `calc(${progress}% - 5px)` }}
        />
      </div>
    </div>
  );
}
