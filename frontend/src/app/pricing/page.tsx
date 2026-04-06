'use client';

import { useState } from 'react';
import { TIER_CONFIG, FEATURE_LABELS, type UserTier } from '@/lib/tiers';
import { useTierStore } from '@/store/tierStore';
import { API_URL } from '@/lib/constants';

export default function PricingPage() {
  const currentTier = useTierStore((s) => s.tier);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tiers: { key: UserTier; highlight: boolean }[] = [
    { key: 'free', highlight: false },
    { key: 'pro', highlight: true },
  ];

  const allFeatures = Object.keys(FEATURE_LABELS);

  const handleUpgrade = async (plan: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_URL}/api/v1/payments/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        // Payment system not configured — show "Coming Soon"
        if (resp.status === 503) {
          setError('Payment system coming soon. Stay tuned!');
        } else {
          setError(data.detail || 'Failed to start subscription');
        }
        return;
      }
      if (data.data?.razorpay_subscription_id && data.data?.razorpay_key_id) {
        // Load Razorpay checkout dynamically
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = () => {
          const options = {
            key: data.data.razorpay_key_id,
            subscription_id: data.data.razorpay_subscription_id,
            name: 'SignalFlow AI',
            description: `${plan === 'annual' ? 'Annual' : 'Monthly'} Pro Plan`,
            handler: () => {
              window.location.reload();
            },
            theme: { color: '#6366F1' },
          };
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const rzp = new (window as any).Razorpay(options);
          rzp.open();
        };
        document.body.appendChild(script);
      } else {
        setError('Payment system is being configured. Please try again later.');
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-display font-bold">Choose Your Plan</h1>
          <p className="text-text-secondary text-sm max-w-lg mx-auto">
            Start free with 5 signals per day. Upgrade to Pro for unlimited access,
            AI Q&A, backtesting, and more.
          </p>
        </div>

        {error && (
          <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-lg p-3 max-w-2xl mx-auto">
            <p className="text-sm text-signal-sell text-center">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          {tiers.map(({ key, highlight }) => {
            const config = TIER_CONFIG[key];
            const isCurrent = currentTier === key;
            return (
              <div
                key={key}
                className={`rounded-xl p-6 space-y-5 ${
                  highlight
                    ? 'bg-accent-purple/5 border-2 border-accent-purple'
                    : 'bg-bg-card border border-border-default'
                }`}
              >
                {highlight && (
                  <span className="inline-block text-xs font-bold uppercase tracking-wider text-accent-purple bg-accent-purple/10 px-2 py-0.5 rounded-full">
                    Recommended
                  </span>
                )}
                <div>
                  <h2 className="text-xl font-display font-bold">{config.name}</h2>
                  <p className="text-2xl font-mono font-bold mt-1">
                    {config.price}
                    {key === 'pro' && <span className="text-sm text-text-muted font-normal"> /month</span>}
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    {config.signalsPerDay === null
                      ? 'Unlimited signals'
                      : `${config.signalsPerDay} signals/day`}
                  </p>
                </div>

                <ul className="space-y-2">
                  {allFeatures.map((feat) => {
                    const enabled = config.features[feat];
                    const label = FEATURE_LABELS[feat].label;
                    return (
                      <li key={feat} className="flex items-center gap-2 text-sm">
                        <span className={enabled ? 'text-signal-buy' : 'text-text-muted'}>
                          {enabled ? '✓' : '✗'}
                        </span>
                        <span className={enabled ? 'text-text-primary' : 'text-text-muted line-through'}>
                          {label}
                        </span>
                      </li>
                    );
                  })}
                </ul>

                <button
                  onClick={() => key === 'pro' && !isCurrent ? handleUpgrade('monthly') : undefined}
                  disabled={isCurrent || isLoading || key === 'free'}
                  className={`w-full py-2.5 text-sm rounded-lg font-medium transition-colors ${
                    isCurrent
                      ? 'bg-bg-secondary text-text-muted cursor-default'
                      : highlight
                      ? 'bg-accent-purple text-white hover:bg-accent-purple/90 disabled:opacity-50'
                      : 'bg-bg-secondary text-text-muted cursor-default'
                  }`}
                >
                  {isCurrent
                    ? 'Current Plan'
                    : isLoading
                    ? 'Processing...'
                    : key === 'pro'
                    ? 'Upgrade to Pro'
                    : 'Free Plan'}
                </button>
              </div>
            );
          })}
        </div>

        <div className="text-center">
          <p className="text-xs text-text-muted">
            Payments processed securely by Razorpay. Cancel anytime from Settings.
          </p>
        </div>

        <div className="bg-signal-hold/5 border border-signal-hold/20 rounded-xl p-4 max-w-2xl mx-auto">
          <p className="text-xs text-text-secondary text-center leading-relaxed">
            <span className="text-signal-hold font-semibold">⚠ Risk Disclosure:</span>{' '}
            SignalFlow AI is NOT registered with SEBI. All analysis is AI-generated for
            educational purposes only and does not constitute investment advice. Past
            performance does not guarantee future results. Trading involves substantial risk
            of loss. Prices shown are indicative and may differ from actual market prices.
          </p>
        </div>
      </div>
    </main>
  );
}
