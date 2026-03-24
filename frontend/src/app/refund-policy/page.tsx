import Link from 'next/link';

export const metadata = {
  title: 'Refund & Cancellation Policy — SignalFlow AI',
};

export default function RefundPolicyPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-display font-bold mb-2">
          Refund &amp; Cancellation Policy
        </h1>
        <p className="text-xs text-text-muted mb-8">Last updated: 24 March 2026</p>

        <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              1. Free Tier
            </h2>
            <p>
              The Free tier is available at no cost and requires no payment information. You may
              use the Free tier indefinitely without any financial obligation.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              2. Pro Tier Subscription
            </h2>
            <p>
              The Pro tier is a monthly subscription billed at the price displayed on the{' '}
              <Link href="/pricing" className="text-accent-purple hover:underline">
                Pricing page
              </Link>
              . All prices are inclusive of applicable GST (18%).
            </p>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              3. Cancellation
            </h2>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                You may cancel your Pro subscription at any time from your account settings.
              </li>
              <li>
                Cancellation takes effect at the end of your current billing period — you will
                retain Pro access until then.
              </li>
              <li>
                After cancellation, your account reverts to the Free tier with its associated
                limits.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              4. Refunds
            </h2>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Within 7 days of first payment:</strong>{' '}
                If you are not satisfied with the Pro tier, you may request a full refund within
                7 days of your first subscription payment.
              </li>
              <li>
                <strong className="text-text-primary">After 7 days:</strong> No refunds are
                available for the current billing period. You may cancel to prevent future
                charges.
              </li>
              <li>
                <strong className="text-text-primary">Service issues:</strong> If the platform
                experiences extended outages (more than 48 consecutive hours), you may request a
                pro-rated refund for the affected period.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              5. How to Request a Refund
            </h2>
            <p>
              Email{' '}
              <a
                href="mailto:support@signalflow.ai"
                className="text-accent-purple hover:underline"
              >
                support@signalflow.ai
              </a>{' '}
              with your registered email address and reason for the refund request. Refunds are
              processed within 5-7 business days to the original payment method.
            </p>
          </section>

          <section className="bg-signal-hold/5 border border-signal-hold/20 rounded-xl p-4">
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              ⚠ Important Note
            </h2>
            <p>
              Subscriptions provide access to analysis tools and AI-generated market analysis.
              They do <strong className="text-text-primary">not</strong> guarantee trading
              profits or investment returns. Trading losses are not grounds for a refund.
            </p>
          </section>

          <div className="pt-4 border-t border-border-default flex items-center gap-4 text-xs">
            <Link href="/pricing" className="text-accent-purple hover:underline">
              Pricing
            </Link>
            <Link href="/terms" className="text-accent-purple hover:underline">
              Terms of Service
            </Link>
            <Link href="/" className="text-text-muted hover:text-text-primary">
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
