'use client';

import Link from 'next/link';
import { NAV_PRIMARY_LINKS, NAV_RESEARCH_LINKS, NAV_LEGAL_LINKS } from '@/lib/constants';

export function SiteFooter() {
  return (
    <footer
      className="border-t border-border-default bg-bg-secondary/50 pt-8 pb-20 md:pb-8 px-4"
      role="contentinfo"
      aria-label="Site footer"
    >
      <div className="max-w-7xl mx-auto">
        {/* Column grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Product */}
          <div>
            <h3 className="text-xs font-display font-semibold text-text-muted uppercase tracking-wider mb-3">
              Product
            </h3>
            <ul className="space-y-2">
              {NAV_PRIMARY_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Research */}
          <div>
            <h3 className="text-xs font-display font-semibold text-text-muted uppercase tracking-wider mb-3">
              Research
            </h3>
            <ul className="space-y-2">
              {NAV_RESEARCH_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-xs font-display font-semibold text-text-muted uppercase tracking-wider mb-3">
              Legal
            </h3>
            <ul className="space-y-2">
              {NAV_LEGAL_LINKS.filter((l) => l.href !== '/contact').map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-xs font-display font-semibold text-text-muted uppercase tracking-wider mb-3">
              Support
            </h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/contact"
                  className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  Contact &amp; Grievance
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* SEBI Disclaimer */}
        <div className="border-t border-border-default pt-6">
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
          <p className="text-center text-xs text-text-muted mt-3">
            &copy; {new Date().getFullYear()} SignalFlow AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
