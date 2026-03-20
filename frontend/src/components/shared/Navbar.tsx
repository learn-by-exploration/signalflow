'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_LINKS = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/history', label: 'History', icon: '📜' },
  { href: '/portfolio', label: 'Portfolio', icon: '💼' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
  { href: '/backtest', label: 'Backtest', icon: '🧪' },
  { href: '/how-it-works', label: 'How It Works', icon: '💡' },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-bg-secondary/95 backdrop-blur-md border-b border-border-default">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-12">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <span className="text-lg font-display font-bold text-accent-purple">SignalFlow</span>
            <span className="text-[10px] font-mono text-text-muted bg-accent-purple/10 px-1.5 py-0.5 rounded">AI</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    isActive
                      ? 'text-accent-purple bg-accent-purple/10'
                      : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-text-secondary hover:text-text-primary"
            aria-label="Toggle menu"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border-default bg-bg-secondary">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={`block px-4 py-3 text-sm border-b border-border-default transition-colors ${
                  isActive
                    ? 'text-accent-purple bg-accent-purple/5'
                    : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.02]'
                }`}
              >
                <span className="mr-2">{link.icon}</span>
                {link.label}
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
}
