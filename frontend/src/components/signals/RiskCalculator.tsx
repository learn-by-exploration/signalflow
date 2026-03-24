'use client';

import { useState } from 'react';
import type { Signal } from '@/lib/types';
import { formatPrice } from '@/utils/formatters';

interface RiskCalculatorProps {
  signal: Signal;
}

const PRESET_AMOUNTS = [10000, 25000, 50000, 100000];

export function RiskCalculator({ signal }: RiskCalculatorProps) {
  const [amount, setAmount] = useState(10000);
  const [customInput, setCustomInput] = useState('');

  const price = parseFloat(signal.current_price);
  const target = parseFloat(signal.target_price);
  const stop = parseFloat(signal.stop_loss);

  if (!price || !target || !stop) return null;

  const isBuy = signal.signal_type.includes('BUY');
  const maxGain = isBuy ? ((target - price) / price) * amount : ((price - target) / price) * amount;
  const maxLoss = isBuy ? ((price - stop) / price) * amount : ((stop - price) / price) * amount;
  const riskReward = maxLoss > 0 ? (maxGain / maxLoss) : 0;
  const gainPct = (maxGain / amount) * 100;
  const lossPct = (maxLoss / amount) * 100;

  const currencySymbol = signal.market_type === 'stock' ? '₹' : signal.market_type === 'crypto' ? '$' : '';

  return (
    <div className="mt-3 pt-3 border-t border-border-default">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-base">🧮</span>
        <p className="text-xs font-display font-medium text-accent-purple">Risk Calculator</p>
      </div>

      {/* Amount selector */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {PRESET_AMOUNTS.map((preset) => (
          <button
            key={preset}
            onClick={(e) => { e.stopPropagation(); setAmount(preset); setCustomInput(''); }}
            className={`px-2 py-0.5 text-xs font-mono rounded border transition-colors ${
              amount === preset && !customInput
                ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                : 'border-border-default text-text-muted hover:border-border-hover'
            }`}
          >
            {currencySymbol}{(preset / 1000).toFixed(0)}K
          </button>
        ))}
        <input
          type="number"
          value={customInput}
          placeholder="Custom"
          aria-label="Custom investment amount"
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            setCustomInput(e.target.value);
            const v = parseFloat(e.target.value);
            if (v > 0) setAmount(v);
          }}
          className="w-20 px-2 py-0.5 text-xs font-mono rounded border border-border-default text-text-primary bg-bg-secondary placeholder:text-text-muted"
        />
      </div>

      {/* Risk/Reward display */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-signal-buy text-sm font-mono font-bold">
            +{currencySymbol}{maxGain.toFixed(0)}
          </div>
          <div className="text-xs text-text-muted">
            Max Gain ({gainPct.toFixed(1)}%)
          </div>
        </div>
        <div>
          <div className="text-signal-sell text-sm font-mono font-bold">
            -{currencySymbol}{maxLoss.toFixed(0)}
          </div>
          <div className="text-xs text-text-muted">
            Max Loss ({lossPct.toFixed(1)}%)
          </div>
        </div>
        <div>
          <div className="text-accent-purple text-sm font-mono font-bold">
            1:{riskReward.toFixed(1)}
          </div>
          <div className="text-xs text-text-muted">
            Risk:Reward
          </div>
        </div>
      </div>
    </div>
  );
}
