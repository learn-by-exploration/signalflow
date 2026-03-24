import Link from 'next/link';

export function SebiDisclaimer() {
  return (
    <footer
      className="mt-auto border-t border-border-default bg-bg-secondary/50 py-4 px-4"
      role="contentinfo"
      aria-label="Legal disclaimer"
    >
      <p className="text-center text-xs leading-relaxed text-text-secondary max-w-3xl mx-auto">
        <span className="text-signal-hold font-semibold">⚠ Important Disclaimer:</span>{' '}
        SignalFlow AI is{' '}
        <strong className="text-text-primary">NOT registered with SEBI</strong> or any
        financial regulatory authority. All analysis is AI-generated and for{' '}
        <strong className="text-text-primary">
          educational and informational purposes only
        </strong>{' '}
        — it does not constitute investment advice or a recommendation to buy or sell any
        security. Past performance does not guarantee future results. Trading involves
        substantial risk of loss. Always consult a SEBI-registered investment advisor before
        making investment decisions.
      </p>
      <p className="text-center text-[10px] text-text-muted mt-2">
        <Link href="/privacy" className="hover:text-text-secondary underline">
          Privacy Policy
        </Link>
        {' · '}
        <Link href="/terms" className="hover:text-text-secondary underline">
          Terms of Service
        </Link>
        {' · '}
        <Link href="/contact" className="hover:text-text-secondary underline">
          Contact &amp; Grievance
        </Link>
      </p>
    </footer>
  );
}
