import { SIGNAL_COLORS } from '@/lib/constants';

interface IndicatorPillProps {
  label: string;
  value: string;
  signal?: 'buy' | 'sell' | 'neutral';
}

export function IndicatorPill({ label, value, signal }: IndicatorPillProps) {
  const color =
    signal === 'buy'
      ? SIGNAL_COLORS.BUY
      : signal === 'sell'
        ? SIGNAL_COLORS.SELL
        : SIGNAL_COLORS.HOLD;

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-mono"
      style={{ backgroundColor: `${color}15`, color }}
    >
      <span className="text-text-muted font-display">{label}</span>
      {value}
    </span>
  );
}
