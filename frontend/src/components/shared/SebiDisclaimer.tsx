export function SebiDisclaimer() {
  return (
    <footer className="mt-auto border-t border-border-default bg-bg-secondary/50 py-3 px-4">
      <p className="text-center text-[10px] leading-relaxed text-text-muted max-w-3xl mx-auto">
        <span className="text-signal-hold/70 font-semibold">⚠ Disclaimer:</span>{' '}
        SignalFlow AI is <strong className="text-text-secondary">not registered with SEBI</strong> or
        any financial regulatory authority. Signals are AI-generated analysis and{' '}
        <strong className="text-text-secondary">not investment advice</strong>. Past performance does
        not guarantee future results. Always do your own research and consult a SEBI-registered
        advisor before making investment decisions. Trade at your own risk.
      </p>
    </footer>
  );
}
