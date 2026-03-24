'use client';

import { useState } from 'react';
import type { Signal } from '@/lib/types';

interface PipCalculatorProps {
  signal: Signal;
}

/**
 * Pip calculator for forex signals.
 * Calculates pip value, risk in pips, and potential P&L based on lot size.
 */
export function PipCalculator({ signal }: PipCalculatorProps) {
  const [lotSize, setLotSize] = useState(0.1);

  const entry = parseFloat(signal.current_price);
  const target = parseFloat(signal.target_price);
  const stop = parseFloat(signal.stop_loss);

  if (!entry || !target || !stop) return null;

  // Standard pip size: for JPY pairs, pip = 0.01; for others, pip = 0.0001
  const isJPY = signal.symbol.toUpperCase().includes('JPY');
  const pipSize = isJPY ? 0.01 : 0.0001;

  const isBuy = signal.signal_type.includes('BUY');
  const targetPips = Math.abs(target - entry) / pipSize;
  const stopPips = Math.abs(entry - stop) / pipSize;

  // Standard lot = 100,000 units, pip value = lot * pipSize
  const pipValuePerLot = isJPY ? 1000 : 10; // Approximate USD per pip for standard lot
  const pipValue = lotSize * pipValuePerLot;

  const potentialProfit = targetPips * pipValue;
  const potentialLoss = stopPips * pipValue;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-base">💱</span>
        <h3 className="text-sm font-display font-semibold">Pip Calculator</h3>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-xs text-text-muted">Lot Size:</label>
        <div className="flex gap-1">
          {[0.01, 0.1, 0.5, 1.0].map((lot) => (
            <button
              key={lot}
              onClick={() => setLotSize(lot)}
              className={`px-2 py-1 text-[10px] rounded border transition-colors ${
                lotSize === lot
                  ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                  : 'border-border-default text-text-muted hover:border-border-hover'
              }`}
            >
              {lot}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
        <div className="bg-bg-secondary rounded-lg p-2">
          <p className="text-[10px] text-text-muted">{isBuy ? 'Target' : 'Target'} Distance</p>
          <p className="text-sm font-mono text-signal-buy">{targetPips.toFixed(1)} pips</p>
        </div>
        <div className="bg-bg-secondary rounded-lg p-2">
          <p className="text-[10px] text-text-muted">Stop Distance</p>
          <p className="text-sm font-mono text-signal-sell">{stopPips.toFixed(1)} pips</p>
        </div>
        <div className="bg-bg-secondary rounded-lg p-2">
          <p className="text-[10px] text-text-muted">Potential Profit</p>
          <p className="text-sm font-mono text-signal-buy">${potentialProfit.toFixed(2)}</p>
        </div>
        <div className="bg-bg-secondary rounded-lg p-2">
          <p className="text-[10px] text-text-muted">Potential Loss</p>
          <p className="text-sm font-mono text-signal-sell">${potentialLoss.toFixed(2)}</p>
        </div>
      </div>

      <p className="text-[10px] text-text-muted">
        Pip value: ${pipValue.toFixed(2)}/pip at {lotSize} lot{lotSize !== 1 ? 's' : ''}
        {' · '}R:R = 1:{(targetPips / stopPips).toFixed(1)}
      </p>
    </div>
  );
}
