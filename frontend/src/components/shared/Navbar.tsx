'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { useSignalStore } from '@/store/signalStore';
import { SettingsPanel } from './SettingsPanel';

const PRIMARY_LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/track-record', label: 'Track Record' },
  { href: '/alerts', label: 'Alerts' },
];

const MORE_LINKS = [
  { href: '/watchlist', label: 'Watchlist', icon: '⭐' },
  { href: '/calendar', label: 'Calendar', icon: '📅' },
  { href: '/history', label: 'Signal History', icon: '📋' },
  { href: '/portfolio', label: 'Portfolio', icon: '💼' },
  { href: '/backtest', label: 'Backtest', icon: '🧪' },
  { href: '/brief', label: 'Daily Brief', icon: '📰' },
  { href: '/how-it-works', label: 'How It Works', icon: '💡' },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const unseenCount = useSignalStore((s) => s.unseenCount);
  const { data: session, status } = useSession();

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
            {PRIMARY_LINKS.map((link) => {
              const isActive = pathname === link.href;
              const showBadge = link.href === '/' && unseenCount > 0 && !isActive;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`relative px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    isActive
                      ? 'text-accent-purple bg-accent-purple/10'
                      : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                  }`}
                >
                  {link.label}
                  {showBadge && (
                    <span className="absolute -top-1 -right-1 min-w-[16px] h-4 flex items-center justify-center bg-signal-sell text-white text-[9px] font-mono font-bold rounded-full px-1">
                      {unseenCount > 9 ? '9+' : unseenCount}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* More dropdown */}
            <div className="relative">
              <button
                onClick={() => setMoreOpen(!moreOpen)}
                className="px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary hover:bg-white/[0.03] rounded-lg transition-colors"
              >
                More
              </button>
              {moreOpen && (
                <div className="absolute right-0 mt-1 bg-bg-secondary border border-border-default rounded-lg shadow-lg py-1 min-w-[160px] z-50">
                  {MORE_LINKS.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMoreOpen(false)}
                      className={`block px-4 py-2 text-sm transition-colors ${
                        pathname === link.href
                          ? 'text-accent-purple bg-accent-purple/5'
                          : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                      }`}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Auth + Settings + Mobile hamburger */}
          <div className="flex items-center gap-1">
            {status === 'authenticated' ? (
              <button
                onClick={() => signOut()}
                className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-white/[0.03]"
                title={session.user?.email ?? undefined}
              >
                <span className="w-5 h-5 rounded-full bg-accent-purple/20 text-accent-purple flex items-center justify-center text-[10px] font-bold">
                  {(session.user?.name?.[0] ?? session.user?.email?.[0] ?? '?').toUpperCase()}
                </span>
                <span className="max-w-[80px] truncate">{session.user?.name ?? 'User'}</span>
              </button>
            ) : status === 'unauthenticated' ? (
              <Link
                href="/auth/signin"
                className="hidden md:block px-3 py-1.5 text-xs text-accent-purple border border-accent-purple/30 rounded-lg hover:bg-accent-purple/10 transition-colors"
              >
                Sign In
              </Link>
            ) : null}
            <button
              onClick={() => setSettingsOpen(true)}
              className="p-2 text-text-secondary hover:text-text-primary transition-colors"
              aria-label="Settings"
            >
              <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
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
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border-default bg-bg-secondary">
          {[...PRIMARY_LINKS, ...MORE_LINKS].map((link) => {
            const isActive = pathname === link.href;
            const showBadge = link.href === '/' && unseenCount > 0 && !isActive;
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
                {link.label}
                {showBadge && (
                  <span className="ml-2 inline-flex items-center justify-center min-w-[16px] h-4 bg-signal-sell text-white text-[9px] font-mono font-bold rounded-full px-1">
                    {unseenCount > 9 ? '9+' : unseenCount}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      )}
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </nav>
  );
}
