import Link from 'next/link';

export const metadata = {
  title: 'Privacy Policy — SignalFlow AI',
};

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-display font-bold mb-2">Privacy Policy</h1>
        <p className="text-xs text-text-muted mb-8">Last updated: 24 March 2026</p>

        <div className="space-y-8 text-sm text-text-secondary leading-relaxed">
          {/* 1 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              1. Data We Collect
            </h2>
            <p className="mb-2">
              SignalFlow AI collects and processes the following personal data to deliver our
              services:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Email address</strong> — used for
                authentication via Google OAuth or credentials sign-in.
              </li>
              <li>
                <strong className="text-text-primary">Telegram chat ID</strong> — used solely
                for delivering signal alerts and market digests to your Telegram account.
              </li>
              <li>
                <strong className="text-text-primary">Trade logs</strong> — symbol, entry/exit
                prices, and P&L data you voluntarily submit through the Portfolio feature.
              </li>
              <li>
                <strong className="text-text-primary">Watchlist symbols</strong> — the list of
                symbols you choose to track for filtered alerts.
              </li>
              <li>
                <strong className="text-text-primary">Alert preferences</strong> — your chosen
                markets, minimum confidence threshold, quiet hours, and signal-type filters.
              </li>
              <li>
                <strong className="text-text-primary">IP addresses</strong> — logged
                automatically by our servers for security and abuse prevention.
              </li>
            </ul>
            <p className="mt-2">
              We also store preferences (theme, text size, view mode) in your browser&apos;s
              localStorage. This data never leaves your device.
            </p>
          </section>

          {/* 2 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              2. How We Use Your Data
            </h2>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Authentication</strong> — to verify your
                identity and protect your account.
              </li>
              <li>
                <strong className="text-text-primary">Alert delivery</strong> — to send signal
                notifications, morning briefs, and weekly digests to your Telegram.
              </li>
              <li>
                <strong className="text-text-primary">Portfolio tracking</strong> — to display
                your trade history and performance.
              </li>
              <li>
                <strong className="text-text-primary">Service improvement</strong> — aggregated,
                anonymized usage patterns help us improve signal quality.
              </li>
            </ul>
            <p className="mt-2">
              We do <strong className="text-text-primary">not</strong> sell, rent, or share your
              personal data with any third party for marketing purposes.
            </p>
          </section>

          {/* 3 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              3. Data Storage &amp; Security
            </h2>
            <p>
              Your data is stored in a PostgreSQL database hosted on Railway (cloud
              infrastructure). All data in transit is encrypted via TLS. We use parameterized
              database queries to prevent injection attacks and apply rate limiting to protect
              against abuse.
            </p>
          </section>

          {/* 4 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              4. Your Rights
            </h2>
            <p className="mb-2">
              Under the Digital Personal Data Protection Act 2023 (DPDPA) and applicable laws,
              you have the right to:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Access</strong> — request a copy of all
                personal data we hold about you.
              </li>
              <li>
                <strong className="text-text-primary">Correction</strong> — request correction
                of inaccurate personal data.
              </li>
              <li>
                <strong className="text-text-primary">Erasure</strong> — request deletion of
                your account and all associated data.
              </li>
              <li>
                <strong className="text-text-primary">Portability</strong> — receive your data
                in a structured, machine-readable format.
              </li>
            </ul>
            <p className="mt-2">
              To exercise any of these rights, contact us at{' '}
              <a
                href="mailto:privacy@signalflow.ai"
                className="text-accent-purple hover:underline"
              >
                privacy@signalflow.ai
              </a>
              . We will respond within 30 days.
            </p>
          </section>

          {/* 5 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              5. Data Retention
            </h2>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Market data</strong> — retained
                indefinitely for historical analysis.
              </li>
              <li>
                <strong className="text-text-primary">User account data</strong> — retained
                until you request account deletion.
              </li>
              <li>
                <strong className="text-text-primary">Server logs (IP addresses)</strong> —
                retained for 90 days, then anonymized.
              </li>
              <li>
                <strong className="text-text-primary">Signal history</strong> — retained for 5
                years per record-keeping requirements.
              </li>
            </ul>
          </section>

          {/* 6 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              6. Third-Party Services
            </h2>
            <p className="mb-2">
              SignalFlow AI uses the following third-party services to operate:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>
                <strong className="text-text-primary">Anthropic Claude API</strong> — for AI
                sentiment analysis and signal reasoning. Your personal data is not sent to
                Claude; only market data and news articles are analyzed.
              </li>
              <li>
                <strong className="text-text-primary">Google OAuth</strong> — for
                authentication. Google receives only the data necessary for sign-in.
              </li>
              <li>
                <strong className="text-text-primary">Telegram Bot API</strong> — for
                delivering alerts. Your Telegram chat ID is stored to route messages.
              </li>
              <li>
                <strong className="text-text-primary">Railway</strong> — cloud hosting
                provider for our database and application servers.
              </li>
            </ul>
          </section>

          {/* 7 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              7. Cookies &amp; Local Storage
            </h2>
            <p>
              SignalFlow AI uses a session cookie set by NextAuth.js for authentication. We also
              use browser localStorage to store your display preferences (theme, text size, view
              mode, tier selection). These are not tracking cookies and are not shared with third
              parties.
            </p>
          </section>

          {/* 8 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              8. Grievance Officer
            </h2>
            <p>
              In compliance with the DPDPA 2023, our designated grievance officer can be reached
              at:
            </p>
            <p className="mt-2 p-3 bg-bg-card border border-border-default rounded-lg text-text-primary">
              Email:{' '}
              <a
                href="mailto:privacy@signalflow.ai"
                className="text-accent-purple hover:underline"
              >
                privacy@signalflow.ai
              </a>
              <br />
              Response time: within 30 days of receiving your request.
            </p>
          </section>

          {/* 9 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              9. Changes to This Policy
            </h2>
            <p>
              We may update this Privacy Policy from time to time. Significant changes will be
              notified via email or Telegram alert. Continued use of the platform after changes
              constitutes acceptance of the updated policy.
            </p>
          </section>

          {/* 10 */}
          <section>
            <h2 className="text-lg font-display font-semibold text-text-primary mb-2">
              10. Contact
            </h2>
            <p>
              For questions about this Privacy Policy, contact us at{' '}
              <a
                href="mailto:privacy@signalflow.ai"
                className="text-accent-purple hover:underline"
              >
                privacy@signalflow.ai
              </a>
              .
            </p>
          </section>

          {/* Back + related links */}
          <div className="pt-4 border-t border-border-default flex items-center gap-4 text-xs">
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
