'use client';

import { useState } from 'react';
import type { Signal } from '@/lib/types';

interface RiskCalculatorProps {
  signal: Signal;
}

const PRESET_AMOUNTS = [10000, 25000, 50000, 100000];
const RISK_PRESETS = [1, 2, 5];

type CalcMode = 'pnl' | 'position';

export function RiskCalculator({ signal }: RiskCalculatorProps) {
  const [mode, setMode] = useState<CalcMode>('pnl');
  const [amount, setAmount] = useState(10000);
  const [customInput, setCustomInput] = useState('');

  // Position sizing state
  const [accountEquity, setAccountEquity] = useState('');
  const [riskPct, setRiskPct] = useState(2);

  const price = parseFloat(signal.current_price);
  const target = parseFloat(signal.target_price);
  const stop = parseFloat(signal.stop_loss);

  if (!price || !target || !stop) return null;

  const isBuy = signal.signal_type.includes('BUY');
  const currencySymbol = signal.market_type === 'stock' ? '₹' : signal.market_type === 'crypto' ? '$' : '';

  // Position sizing calculation
  const riskPerUnit = isBuy ? price - stop : stop - price;
  const equity = parseFloat(accountEquity) || 0;
  const maxRiskAmount = equity * (riskPct / 100);
  const recommendedQty = riskPerUnit > 0 ? Math.floor(maxRiskAmount / riskPerUnit) : 0;
  const recommendedInvestment = recommendedQty * price;
  const potentialGain = recommendedQty * (isBuy ? target - price : price - target);
  const potentialLoss = recommendedQty * riskPerUnit;

  // P&L mode calculation
  const maxGain = isBuy ? ((target - price) / price) * amount : ((price - target) / price) * amount;
  const maxLoss = isBuy ? ((price - stop) / price) * amount : ((stop - price) / price) * amount;
  const riskReward = maxLoss > 0 ? (maxGain / maxLoss) : 0;
  const gainPct = (maxGain / amount) * 100;
  const lossPct = (maxLoss / amount) * 100;

  return (
    <div className="mt-3 pt-3 border-t border-border-default">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-base">🧮</span>
          <p className="text-xs font-display font-medium text-accent-purple">Risk Calculator</p>
        </div>
        <div className="flex gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); setMode('pnl'); }}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${mode === 'pnl' ? 'bg-accent-purple/20 text-accent-purple' : 'text-text-muted hover:text-text-secondary'}`}
          >
            P&L
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setMode('position'); }}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${mode === 'position' ? 'bg-accent-purple/20 text-accent-purple' : 'text-text-muted hover:text-text-secondary'}`}
          >
            Size
          </button>
        </div>
      </div>

      {mode === 'pnl' ? (
        <>
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
        </>
      ) : (
        <>
          {/* Position Sizing Mode */}
          <div className="space-y-3">
            <div>
              <label className="text-xs text-text-muted block mb-1">Your Account Size ({currencySymbol || '$'})</label>
              <input
                type="number"
                value={accountEquity}
                placeholder="e.g. 500000"
                aria-label="Account equity"
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => setAccountEquity(e.target.value)}
                className="w-full px-3 py-1.5 text-sm font-mono rounded-lg border border-border-default text-text-primary bg-bg-secondary placeholder:text-text-muted"
              />
            </div>

            <div>
              <label className="text-xs text-text-muted block mb-1">Max Risk Per Trade</label>
              <div className="flex gap-1.5">
                {RISK_PRESETS.map((pct) => (
                  <button
                    key={pct}
                    onClick={(e) => { e.stopPropagation(); setRiskPct(pct); }}
                    className={`px-3 py-1 text-xs font-mono rounded border transition-colors ${
                      riskPct === pct
                        ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                        : 'border-border-default text-text-muted hover:border-border-hover'
                    }`}
                  >
                    {pct}%
                  </button>
                ))}
              </div>
            </div>

            {equity > 0 && (
              <div className="bg-bg-secondary rounded-lg p-3 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Max risk amount</span>
                  <span className="font-mono text-text-primary">{currencySymbol}{maxRiskAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Recommended quantity</span>
                  <span className="font-mono text-accent-purple font-bold">{recommendedQty.toLocaleString()} units</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Investment needed</span>
                  <span className="font-mono text-text-primary">{currencySymbol}{recommendedInvestment.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="border-t border-border-default pt-2 grid grid-cols-2 gap-2 text-center">
                  <div>
                    <div className="text-signal-buy text-xs font-mono font-bold">+{currencySymbol}{potentialGain.toFixed(0)}</div>
                    <div className="text-xs text-text-muted">If target hit</div>
                  </div>
                  <div>
                    <div className="text-signal-sell text-xs font-mono font-bold">-{currencySymbol}{potentialLoss.toFixed(0)}</div>
                    <div className="text-xs text-text-muted">If stop hit</div>
                  </div>
                </div>
                <p className="text-xs text-text-muted pt-1">
                  Risking {riskPct}% of {currencySymbol}{equity.toLocaleString(undefined, { maximumFractionDigits: 0 })} = {currencySymbol}{maxRiskAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })} max loss.
                  This is a guideline, not investment advice.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
