'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useSignalStore } from '@/store/signalStore';
import { NAV_MOBILE_TABS } from '@/lib/constants';
import { MobileMenuSheet } from './MobileMenuSheet';

const TAB_ICONS: Record<string, { active: React.ReactNode; inactive: React.ReactNode }> = {
  home: {
    active: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 12l9-8 9 8v8a2 2 0 01-2 2h-4v-6H9v6H5a2 2 0 01-2-2v-8z" />
      </svg>
    ),
    inactive: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l9-8 9 8M5 10v10h4v-6h6v6h4V10" />
      </svg>
    ),
  },
  watchlist: {
    active: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17a5 5 0 110-10 5 5 0 010 10zm0-8a3 3 0 100 6 3 3 0 000-6z" />
      </svg>
    ),
    inactive: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  brief: {
    active: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zM7 7h10v2H7V7zm0 4h10v2H7v-2zm0 4h7v2H7v-2z" />
      </svg>
    ),
    inactive: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <line x1="7" y1="7" x2="17" y2="7" />
        <line x1="7" y1="11" x2="17" y2="11" />
        <line x1="7" y1="15" x2="14" y2="15" />
      </svg>
    ),
  },
  portfolio: {
    active: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 7h-4V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2H4a2 2 0 00-2 2v11a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM10 5h4v2h-4V5z" />
      </svg>
    ),
    inactive: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <rect x="2" y="7" width="20" height="13" rx="2" />
        <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
      </svg>
    ),
  },
  menu: {
    active: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    inactive: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    ),
  },
};

export function BottomNav() {
  const pathname = usePathname();
  const { status } = useSession();
  const isAuth = status === 'authenticated';
  const unseenCount = useSignalStore((s) => s.unseenCount);
  const [menuOpen, setMenuOpen] = useState(false);

  if (!isAuth) return null;

  return (
    <>
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-bg-secondary/95 backdrop-blur-md border-t border-border-default"
        role="navigation"
        aria-label="Main navigation"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <div className="grid grid-cols-5 h-14">
          {NAV_MOBILE_TABS.map((tab) => {
            const isMenu = tab.id === 'menu';
            const isActive = isMenu ? menuOpen : pathname === tab.href;
            const showBadge = tab.id === 'home' && unseenCount > 0 && pathname !== '/';
            const icons = TAB_ICONS[tab.id];

            if (isMenu) {
              return (
                <button
                  key={tab.id}
                  onClick={() => setMenuOpen(!menuOpen)}
                  className={`flex flex-col items-center justify-center gap-0.5 text-xs transition-colors ${
                    isActive ? 'text-accent-purple' : 'text-text-muted'
                  }`}
                  aria-label="Menu"
                  aria-expanded={menuOpen}
                >
                  {isActive ? icons.active : icons.inactive}
                  <span>{tab.label}</span>
                </button>
              );
            }

            return (
              <Link
                key={tab.id}
                href={tab.href!}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => setMenuOpen(false)}
                className={`relative flex flex-col items-center justify-center gap-0.5 text-xs transition-colors ${
                  isActive ? 'text-accent-purple' : 'text-text-muted'
                }`}
              >
                {isActive ? icons.active : icons.inactive}
                <span>{tab.label}</span>
                {showBadge && (
                  <span className="absolute top-1 right-1/4 min-w-[16px] h-4 flex items-center justify-center bg-signal-sell text-white text-[10px] font-mono font-bold rounded-full px-0.5">
                    {unseenCount > 9 ? '9+' : unseenCount}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      <MobileMenuSheet isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
    </>
  );
}
