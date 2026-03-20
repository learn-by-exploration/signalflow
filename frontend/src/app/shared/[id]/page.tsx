'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';

interface SharedSignalData {
  symbol: string;
  market_type: string;
  signal_type: string;
  confidence: number;
  current_price: string;
  target_price: string;
  stop_loss: string;
  timeframe: string | null;
  ai_reasoning: string;
  created_at: string;
}

export default function SharedSignalPage() {
  const params = useParams();
  const shareId = params.id as string;
  const [signal, setSignal] = useState<SharedSignalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = (await api.getSharedSignal(shareId)) as { data: SharedSignalData };
        setSignal(res.data);
      } catch {
        setError('Signal not found or link has expired.');
      } finally {
        setLoading(false);
      }
    }
    if (shareId) load();
  }, [shareId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-text-secondary">Loading signal...</div>
      </div>
    );
  }

  if (error || !signal) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg">{error}</p>
          <a href="/" className="text-accent-purple text-sm mt-4 inline-block hover:underline">
            Go to SignalFlow Dashboard →
          </a>
        </div>
      </div>
    );
  }

  const isBuy = signal.signal_type.includes('BUY');
  const isSell = signal.signal_type.includes('SELL');
  const badgeColor = isBuy
    ? 'bg-signal-buy/15 text-signal-buy'
    : isSell
      ? 'bg-signal-sell/15 text-signal-sell'
      : 'bg-signal-hold/15 text-signal-hold';

  return (
    <main className="min-h-screen p-4 sm:p-8 flex items-center justify-center">
      <div className="max-w-lg w-full">
        <div className="rounded-xl bg-bg-card border border-border-default p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold font-mono">
              {signal.symbol.replace('.NS', '').replace('USDT', '')}
            </h1>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${badgeColor}`}>
              {signal.signal_type.replace('_', ' ')}
            </span>
          </div>

          <div className="text-3xl font-mono">
            {signal.confidence}%
            <span className="text-sm text-text-muted ml-2">confidence</span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center text-sm">
            <div className="bg-bg-secondary rounded-lg p-2">
              <p className="text-text-muted text-xs">Price</p>
              <p className="font-mono mt-1">{parseFloat(signal.current_price).toLocaleString()}</p>
            </div>
            <div className="bg-bg-secondary rounded-lg p-2">
              <p className="text-text-muted text-xs">Target</p>
              <p className="font-mono mt-1 text-signal-buy">{parseFloat(signal.target_price).toLocaleString()}</p>
            </div>
            <div className="bg-bg-secondary rounded-lg p-2">
              <p className="text-text-muted text-xs">Stop-Loss</p>
              <p className="font-mono mt-1 text-signal-sell">{parseFloat(signal.stop_loss).toLocaleString()}</p>
            </div>
          </div>

          {signal.timeframe && (
            <p className="text-sm text-text-secondary">⏱ Timeframe: {signal.timeframe}</p>
          )}

          <div className="bg-bg-secondary rounded-lg p-3">
            <p className="text-xs text-text-muted mb-1">🤖 AI Reasoning</p>
            <p className="text-sm text-text-secondary leading-relaxed">{signal.ai_reasoning}</p>
          </div>

          <p className="text-xs text-text-muted text-center">
            Shared from SignalFlow AI • {new Date(signal.created_at).toLocaleDateString()}
          </p>

          <p className="text-xs text-text-muted text-center">
            ⚠️ AI-generated analysis, not financial advice.
          </p>
        </div>

        <div className="text-center mt-4">
          <a href="/" className="text-accent-purple text-sm hover:underline">
            Try SignalFlow AI →
          </a>
        </div>
      </div>
    </main>
  );
}
