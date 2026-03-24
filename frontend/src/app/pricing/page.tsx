'use client';

import { TIER_CONFIG, FEATURE_LABELS, type UserTier } from '@/lib/tiers';
import { useTierStore } from '@/store/tierStore';

export default function PricingPage() {
  const currentTier = useTierStore((s) => s.tier);
  const setTier = useTierStore((s) => s.setTier);

  const tiers: { key: UserTier; highlight: boolean }[] = [
    { key: 'free', highlight: false },
    { key: 'pro', highlight: true },
  ];

  const allFeatures = Object.keys(FEATURE_LABELS);

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
                  <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-accent-purple bg-accent-purple/10 px-2 py-0.5 rounded-full">
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
                  onClick={() => setTier(key)}
                  disabled={isCurrent}
                  className={`w-full py-2.5 text-sm rounded-lg font-medium transition-colors ${
                    isCurrent
                      ? 'bg-bg-secondary text-text-muted cursor-default'
                      : highlight
                      ? 'bg-accent-purple text-white hover:bg-accent-purple/90'
                      : 'bg-bg-secondary text-text-primary border border-border-default hover:border-border-hover'
                  }`}
                >
                  {isCurrent ? 'Current Plan' : key === 'pro' ? 'Upgrade to Pro' : 'Downgrade to Free'}
                </button>
              </div>
            );
          })}
        </div>

        <div className="text-center space-y-2">
          <p className="text-xs text-text-muted">
            Pro plan is currently in preview. Switching plans takes effect immediately.
          </p>
          <p className="text-xs text-text-muted">
            Payment integration (Razorpay/Stripe) coming soon.
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
