import Link from 'next/link';

export const metadata = {
  title: 'Contact & Grievance — SignalFlow AI',
};

export default function ContactPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-3xl font-display font-bold mb-2">Contact Us</h1>
          <p className="text-sm text-text-secondary">
            Have questions, feedback, or a complaint? We&apos;re here to help.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* General contact */}
          <div className="bg-bg-card border border-border-default rounded-xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-full bg-accent-purple/10 flex items-center justify-center">
              <span className="text-accent-purple text-lg">📧</span>
            </div>
            <h2 className="text-lg font-display font-semibold">General Inquiries</h2>
            <p className="text-sm text-text-secondary">
              For questions about the platform, features, or feedback.
            </p>
            <a
              href="mailto:support@signalflow.ai"
              className="text-accent-purple text-sm hover:underline"
            >
              support@signalflow.ai
            </a>
          </div>

          {/* Privacy / Data */}
          <div className="bg-bg-card border border-border-default rounded-xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-full bg-accent-purple/10 flex items-center justify-center">
              <span className="text-accent-purple text-lg">🔒</span>
            </div>
            <h2 className="text-lg font-display font-semibold">Privacy &amp; Data Rights</h2>
            <p className="text-sm text-text-secondary">
              To request data access, correction, deletion, or portability under DPDPA 2023.
            </p>
            <a
              href="mailto:privacy@signalflow.ai"
              className="text-accent-purple text-sm hover:underline"
            >
              privacy@signalflow.ai
            </a>
          </div>
        </div>

        {/* Grievance Officer — DPDPA §8(10) */}
        <section className="bg-bg-card border border-border-default rounded-xl p-6 space-y-3">
          <h2 className="text-lg font-display font-semibold">
            Grievance Officer{' '}
            <span className="text-xs text-text-muted font-normal">(DPDPA 2023 §8(10))</span>
          </h2>
          <p className="text-sm text-text-secondary">
            In compliance with the Digital Personal Data Protection Act 2023, we have designated
            a Grievance Officer to address your concerns related to data processing, privacy, or
            any grievance with our services.
          </p>
          <div className="p-4 bg-bg-secondary rounded-lg text-sm space-y-1">
            <p className="text-text-primary">
              <strong>Email:</strong>{' '}
              <a
                href="mailto:privacy@signalflow.ai"
                className="text-accent-purple hover:underline"
              >
                privacy@signalflow.ai
              </a>
            </p>
            <p className="text-text-secondary">
              Response time: within 30 days of receiving your request.
            </p>
          </div>
        </section>

        {/* Complaint Process */}
        <section className="space-y-3">
          <h2 className="text-lg font-display font-semibold">How We Handle Complaints</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-text-secondary ml-2">
            <li>
              <strong className="text-text-primary">Submit your complaint</strong> via email to
              the relevant address above. Include as much detail as possible.
            </li>
            <li>
              <strong className="text-text-primary">Acknowledgment</strong> — we will
              acknowledge receipt within 48 hours.
            </li>
            <li>
              <strong className="text-text-primary">Investigation</strong> — we will investigate
              and provide a resolution within 30 days.
            </li>
            <li>
              <strong className="text-text-primary">Escalation</strong> — if unsatisfied with our
              response, you may escalate to the Data Protection Board of India as per DPDPA 2023.
            </li>
          </ol>
        </section>

        <div className="pt-4 border-t border-border-default flex items-center gap-4 text-xs">
          <Link href="/privacy" className="text-accent-purple hover:underline">
            Privacy Policy
          </Link>
          <Link href="/terms" className="text-accent-purple hover:underline">
            Terms of Service
          </Link>
          <Link href="/" className="text-text-muted hover:text-text-primary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
