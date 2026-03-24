'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import Link from 'next/link';

interface BriefData {
  date: string;
  market_summary: string;
  top_signals: { symbol: string; signal_type: string; confidence: number }[];
  key_events: string[];
}

export default function MorningBriefPage() {
  const [brief, setBrief] = useState<BriefData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBrief() {
      try {
        const res = (await api.get('/api/v1/signals?limit=5')) as { data: { symbol: string; signal_type: string; confidence: number; market_type: string }[] };
        const signals = res.data ?? [];
        const now = new Date();
        const hour = now.getHours();

        setBrief({
          date: now.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
          market_summary: hour < 12
            ? 'Good morning! Here\'s your market overview for today.'
            : hour < 17
              ? 'Here\'s your afternoon market update.'
              : 'Here\'s your evening market wrap-up.',
          top_signals: signals.slice(0, 5).map((s) => ({
            symbol: s.symbol.replace('.NS', '').replace('USDT', ''),
            signal_type: s.signal_type,
            confidence: s.confidence,
          })),
          key_events: [
            hour < 10 ? 'NSE market opens at 9:15 AM IST' : hour < 15 ? 'NSE market open until 3:30 PM IST' : 'NSE market closed',
            'Crypto markets: 24/7 active',
            'Forex: Open Sunday 5:30 PM IST to Saturday 3:30 AM IST',
          ],
        });
      } catch {
        setError('Could not load morning brief. Try again later.');
      } finally {
        setLoading(false);
      }
    }
    fetchBrief();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-signal-sell">{error}</p>
          <Link href="/" className="text-accent-purple text-sm hover:underline">← Back to Dashboard</Link>
        </div>
      </main>
    );
  }

  const signalColor = (type: string) => {
    if (type.includes('BUY')) return 'text-signal-buy';
    if (type.includes('SELL')) return 'text-signal-sell';
    return 'text-signal-hold';
  };

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <div>
          <h1 className="text-2xl font-display font-semibold">📰 Daily Brief</h1>
          {brief && <p className="text-sm text-text-muted mt-1">{brief.date}</p>}
        </div>

        {brief && (
          <>
            {/* Greeting */}
            <div className="bg-bg-card border border-border-default rounded-xl p-5">
              <p className="text-sm text-text-secondary leading-relaxed">{brief.market_summary}</p>
            </div>

            {/* Top Signals */}
            {brief.top_signals.length > 0 && (
              <div className="bg-bg-card border border-border-default rounded-xl p-5">
                <h2 className="text-sm font-display font-semibold mb-3">🎯 Top Signals Today</h2>
                <div className="space-y-2">
                  {brief.top_signals.map((sig, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between bg-bg-secondary rounded-lg px-3 py-2"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono font-medium text-text-primary">{sig.symbol}</span>
                        <span className={`text-xs font-mono font-semibold ${signalColor(sig.signal_type)}`}>
                          {sig.signal_type.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="text-xs font-mono text-text-secondary">{sig.confidence}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Market Status */}
            <div className="bg-bg-card border border-border-default rounded-xl p-5">
              <h2 className="text-sm font-display font-semibold mb-3">🕐 Market Status</h2>
              <ul className="space-y-1.5">
                {brief.key_events.map((event, i) => (
                  <li key={i} className="text-xs text-text-secondary flex items-center gap-2">
                    <span className="text-text-muted">•</span>
                    {event}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex items-center justify-between">
              <Link href="/" className="text-xs text-accent-purple hover:underline">← Dashboard</Link>
              <Link href="/history" className="text-xs text-accent-purple hover:underline">Signal History →</Link>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
