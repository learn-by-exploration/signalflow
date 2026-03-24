import { SIGNAL_COLORS } from '@/lib/constants';
import type { SignalType } from '@/lib/types';

interface SignalBadgeProps {
  signalType: SignalType;
}

const BADGE_LABELS: Record<SignalType, string> = {
  STRONG_BUY: 'STRONG BUY',
  BUY: 'BUY',
  HOLD: 'HOLD',
  SELL: 'SELL',
  STRONG_SELL: 'STRONG SELL',
};

const BADGE_ICONS: Record<SignalType, string> = {
  STRONG_BUY: '▲▲',
  BUY: '▲',
  HOLD: '◆',
  SELL: '▼',
  STRONG_SELL: '▼▼',
};

export function SignalBadge({ signalType }: SignalBadgeProps) {
  const label = BADGE_LABELS[signalType];
  const icon = BADGE_ICONS[signalType];
  const color = SIGNAL_COLORS[signalType];

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-display font-semibold"
      style={{ backgroundColor: `${color}20`, color }}
      role="status"
      aria-label={`Signal: ${label}`}
    >
      <span aria-hidden="true">{icon}</span> {label}
    </span>
  );
}
