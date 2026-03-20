'use client';

import { useState } from 'react';
import type { AlertConfig, MarketType, SignalType } from '@/lib/types';

interface AlertConfigProps {
  config: AlertConfig | null;
  onSave: (data: Partial<AlertConfig>) => void;
  onClose: () => void;
}

const MARKET_OPTIONS: { value: MarketType; label: string }[] = [
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

const SIGNAL_OPTIONS: { value: SignalType; label: string }[] = [
  { value: 'STRONG_BUY', label: 'Strong Buy' },
  { value: 'BUY', label: 'Buy' },
  { value: 'SELL', label: 'Sell' },
  { value: 'STRONG_SELL', label: 'Strong Sell' },
];

export function AlertConfigModal({ config, onSave, onClose }: AlertConfigProps) {
  const [markets, setMarkets] = useState<MarketType[]>(config?.markets ?? ['stock', 'crypto', 'forex']);
  const [minConfidence, setMinConfidence] = useState(config?.min_confidence ?? 60);
  const [signalTypes, setSignalTypes] = useState<SignalType[]>(
    config?.signal_types ?? ['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL']
  );

  const toggleMarket = (m: MarketType) => {
    setMarkets((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]));
  };

  const toggleSignalType = (s: SignalType) => {
    setSignalTypes((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  };

  const handleSave = () => {
    onSave({ markets, min_confidence: minConfidence, signal_types: signalTypes });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-bg-secondary border border-border-default rounded-2xl p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-display font-semibold mb-4">Alert Preferences</h3>

        {/* Markets */}
        <div className="mb-4">
          <label className="text-sm text-text-secondary mb-2 block">Markets</label>
          <div className="flex gap-2">
            {MARKET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => toggleMarket(opt.value)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  markets.includes(opt.value)
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-muted'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Min confidence */}
        <div className="mb-4">
          <label className="text-sm text-text-secondary mb-2 block">
            Minimum Confidence: <span className="font-mono text-accent-purple">{minConfidence}%</span>
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
            className="w-full accent-accent-purple"
          />
        </div>

        {/* Signal types */}
        <div className="mb-6">
          <label className="text-sm text-text-secondary mb-2 block">Signal Types</label>
          <div className="flex flex-wrap gap-2">
            {SIGNAL_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => toggleSignalType(opt.value)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  signalTypes.includes(opt.value)
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-muted'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-accent-purple text-white rounded-lg hover:bg-accent-purple/90 transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
