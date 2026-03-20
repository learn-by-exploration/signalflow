import { SIGNAL_COLORS } from '@/lib/constants';
import type { SignalType } from '@/lib/types';

interface SignalBadgeProps {
  signalType: SignalType;
}

const BADGE_LABELS: Record<SignalType, { emoji: string; label: string }> = {
  STRONG_BUY: { emoji: '🟢', label: 'STRONG BUY' },
  BUY: { emoji: '🟢', label: 'BUY' },
  HOLD: { emoji: '🟡', label: 'HOLD' },
  SELL: { emoji: '🔴', label: 'SELL' },
  STRONG_SELL: { emoji: '🔴', label: 'STRONG SELL' },
};

export function SignalBadge({ signalType }: SignalBadgeProps) {
  const { emoji, label } = BADGE_LABELS[signalType];
  const color = SIGNAL_COLORS[signalType];

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-display font-semibold"
      style={{ backgroundColor: `${color}20`, color }}
    >
      <span>{emoji}</span>
      {label}
    </span>
  );
}
