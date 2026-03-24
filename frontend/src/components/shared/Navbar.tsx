'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { useSignalStore } from '@/store/signalStore';

const PRIMARY_LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/news', label: 'News' },
  { href: '/track-record', label: 'Track Record' },
  { href: '/alerts', label: 'Alerts' },
];

const MORE_LINKS = [
  { href: '/watchlist', label: 'Watchlist' },
  { href: '/calendar', label: 'Calendar' },
  { href: '/history', label: 'Signal History' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/backtest', label: 'Backtest' },
  { href: '/brief', label: 'Daily Brief' },
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/settings', label: 'Settings' },
];

// Grouped navigation for mobile drawer
const MOBILE_NAV_GROUPS = [
  {
    title: 'Markets',
    icon: '📊',
    links: [
      { href: '/', label: 'Dashboard' },
      { href: '/news', label: 'News' },
      { href: '/calendar', label: 'Calendar' },
    ],
  },
  {
    title: 'Analysis',
    icon: '📈',
    links: [
      { href: '/track-record', label: 'Track Record' },
      { href: '/history', label: 'Signal History' },
      { href: '/backtest', label: 'Backtest' },
      { href: '/brief', label: 'Daily Brief' },
    ],
  },
  {
    title: 'Account',
    icon: '👤',
    links: [
      { href: '/portfolio', label: 'Portfolio' },
      { href: '/alerts', label: 'Alerts' },
      { href: '/watchlist', label: 'Watchlist' },
      { href: '/settings', label: 'Settings' },
    ],
  },
];

const PUBLIC_LINKS = [
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/pricing', label: 'Pricing' },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  const unseenCount = useSignalStore((s) => s.unseenCount);
  const { data: session, status } = useSession();
  const isAuth = status === 'authenticated';

  // Close More dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    if (moreOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [moreOpen]);

  // Close menus on route change
  useEffect(() => {
    setMoreOpen(false);
    setMobileOpen(false);
  }, [pathname]);

  return (
    <nav className="sticky top-0 z-50 bg-bg-secondary/95 backdrop-blur-md border-b border-border-default">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-12">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <span className="text-lg font-display font-bold text-accent-purple">SignalFlow</span>
            <span className="text-xs font-mono text-text-muted bg-accent-purple/10 px-1.5 py-0.5 rounded">AI</span>
          </Link>

          {/* Desktop nav — authenticated */}
          {isAuth ? (
            <div className="hidden md:flex items-center gap-0.5">
              {/* Top-level links: most used pages */}
              {[
                { href: '/', label: 'Dashboard' },
                { href: '/news', label: 'News' },
                { href: '/track-record', label: 'Track Record' },
                { href: '/alerts', label: 'Alerts' },
                { href: '/history', label: 'History' },
                { href: '/portfolio', label: 'Portfolio' },
              ].map((link) => {
                const isActive = pathname === link.href;
                const showBadge = link.href === '/' && unseenCount > 0 && !isActive;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    aria-current={isActive ? 'page' : undefined}
                    className={`relative px-2.5 py-1.5 text-sm rounded-lg transition-colors ${
                      isActive
                        ? 'text-accent-purple bg-accent-purple/10'
                        : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                    }`}
                  >
                    {link.label}
                    {showBadge && (
                      <span className="absolute -top-1 -right-1 min-w-[20px] h-5 flex items-center justify-center bg-signal-sell text-white text-xs font-mono font-bold rounded-full px-1">
                        {unseenCount > 9 ? '9+' : unseenCount}
                      </span>
                    )}
                  </Link>
                );
              })}

              {/* More dropdown — remaining pages */}
              <div className="relative" ref={moreRef}>
                <button
                  onClick={() => setMoreOpen(!moreOpen)}
                  className="px-2.5 py-1.5 text-sm text-text-secondary hover:text-text-primary hover:bg-white/[0.03] rounded-lg transition-colors"
                >
                  More ▾
                </button>
                {moreOpen && (
                  <div
                    className="absolute right-0 mt-1 bg-bg-secondary border border-border-default rounded-lg shadow-lg py-1 min-w-[180px] z-50"
                    onMouseLeave={() => setMoreOpen(false)}
                  >
                    <p className="px-4 py-1 text-xs text-text-muted uppercase tracking-wider">Tools</p>
                    {[
                      { href: '/backtest', label: 'Backtest' },
                      { href: '/watchlist', label: 'Watchlist' },
                      { href: '/calendar', label: 'Calendar' },
                      { href: '/brief', label: 'Daily Brief' },
                    ].map((link) => (
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
                    <div className="border-t border-border-default my-1" />
                    <p className="px-4 py-1 text-xs text-text-muted uppercase tracking-wider">Help</p>
                    {[
                      { href: '/how-it-works', label: 'How It Works' },
                      { href: '/settings', label: 'Settings' },
                    ].map((link) => (
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
          ) : (
            /* Desktop nav — unauthenticated (minimal) */
            <div className="hidden md:flex items-center gap-1">
              {PUBLIC_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    pathname === link.href
                      ? 'text-accent-purple bg-accent-purple/10'
                      : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          )}

          {/* Auth + Settings + Mobile hamburger */}
          <div className="flex items-center gap-1">
            {isAuth ? (
              <>
                <button
                  onClick={() => signOut()}
                  className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-white/[0.03]"
                  title={session.user?.email ?? undefined}
                >
                  <span className="w-5 h-5 rounded-full bg-accent-purple/20 text-accent-purple flex items-center justify-center text-xs font-bold">
                    {(session.user?.name?.[0] ?? session.user?.email?.[0] ?? '?').toUpperCase()}
                  </span>
                  <span className="max-w-[80px] truncate">{session.user?.name ?? 'User'}</span>
                </button>
                <Link
                  href="/settings"
                  className="p-2 text-text-secondary hover:text-text-primary transition-colors"
                  aria-label="Settings"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </Link>
              </>
            ) : (
              <Link
                href="/auth/signin"
                className="hidden md:block px-4 py-1.5 text-sm font-medium text-white bg-accent-purple rounded-lg hover:bg-accent-purple/90 transition-colors"
              >
                Sign In
              </Link>
            )}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-3 text-text-secondary hover:text-text-primary touch-target"
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
        <div className="md:hidden border-t border-border-default bg-bg-secondary max-h-[80vh] overflow-y-auto">
          {isAuth ? (
            MOBILE_NAV_GROUPS.map((group) => (
              <div key={group.title}>
                <p className="px-4 pt-3 pb-1 text-xs text-text-muted uppercase tracking-wider font-display">
                  {group.icon} {group.title}
                </p>
                {group.links.map((link) => {
                  const isActive = pathname === link.href;
                  const showBadge = link.href === '/' && unseenCount > 0 && !isActive;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center justify-between px-4 py-3 text-sm border-b border-border-default transition-colors ${
                        isActive
                          ? 'text-accent-purple bg-accent-purple/5'
                          : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.02]'
                      }`}
                    >
                      {link.label}
                      {showBadge && (
                        <span className="min-w-[20px] h-5 flex items-center justify-center bg-signal-sell text-white text-xs font-mono font-bold rounded-full px-1">
                          {unseenCount > 9 ? '9+' : unseenCount}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            ))
          ) : (
            [...PUBLIC_LINKS, { href: '/auth/signin', label: 'Sign In' }].map((link) => {
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
                  {link.label}
                </Link>
              );
            })
          )}
          {isAuth && (
            <div className="px-4 py-3">
              <Link
                href="/how-it-works"
                onClick={() => setMobileOpen(false)}
                className="text-xs text-text-muted hover:text-text-secondary transition-colors"
              >
                How It Works
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
