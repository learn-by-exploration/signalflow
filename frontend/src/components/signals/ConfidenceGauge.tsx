import { SIGNAL_COLORS } from '@/lib/constants';
import type { SignalType } from '@/lib/types';

interface ConfidenceGaugeProps {
  confidence: number;
  signalType: SignalType;
  size?: number;
}

const SIGNAL_LABELS: Record<SignalType, string> = {
  STRONG_BUY: 'Strongly Bullish',
  BUY: 'Bullish',
  HOLD: 'Hold',
  SELL: 'Bearish',
  STRONG_SELL: 'Strongly Bearish',
};

export function ConfidenceGauge({ confidence, signalType, size = 56 }: ConfidenceGaugeProps) {
  const color = SIGNAL_COLORS[signalType];
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (confidence / 100) * circumference;
  const center = size / 2;
  const label = SIGNAL_LABELS[signalType];

  return (
    <div
      className="relative flex items-center justify-center group"
      style={{ width: size, height: size }}
      title={`Signal Strength ${confidence}% — measures how strongly technical indicators and AI sentiment agree. Higher = stronger consensus, not probability of profit.`}
    >
      <svg
        width={size}
        height={size}
        className="-rotate-90"
        role="img"
        aria-label={`Confidence: ${confidence} percent, ${label}`}
      >
        {/* Background track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={3}
          className="text-border-default"
        />
        {/* Progress arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span
        className="absolute text-xs font-mono font-bold"
        style={{ color }}
      >
        {confidence}%
      </span>
    </div>
  );
}
