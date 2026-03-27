'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

interface ShortcutCallbacks {
  onFilterChange?: (filter: 'all' | 'stock' | 'crypto' | 'forex') => void;
  onFocusSearch?: () => void;
  onNavigate?: (path: string) => void;
}

const NAV_KEYS: Record<string, string> = {
  h: '/',
  w: '/watchlist',
  p: '/portfolio',
  b: '/brief',
  t: '/track-record',
  n: '/news',
};

/**
 * Global keyboard shortcuts for the dashboard.
 * 1/2/3/4 — Switch filter (All/Stocks/Crypto/Forex)
 * / — Focus search input
 * ? — Toggle shortcuts help modal
 * Escape — Close any modal/expanded card
 * G then H/W/P/B/T/N — Navigate to page
 */
export function useKeyboardShortcuts(callbacks?: ShortcutCallbacks) {
  const [showHelp, setShowHelp] = useState(false);
  const pendingNav = useRef(false);
  const navTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      // Don't capture when user is typing in an input/textarea
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
        if (e.key === 'Escape') {
          (e.target as HTMLElement).blur();
        }
        return;
      }

      // G-then-letter navigation
      if (pendingNav.current) {
        pendingNav.current = false;
        if (navTimeout.current) {
          clearTimeout(navTimeout.current);
          navTimeout.current = null;
        }
        const path = NAV_KEYS[e.key.toLowerCase()];
        if (path && callbacks?.onNavigate) {
          e.preventDefault();
          callbacks.onNavigate(path);
          return;
        }
      }

      if (e.key === 'g' || e.key === 'G') {
        pendingNav.current = true;
        navTimeout.current = setTimeout(() => {
          pendingNav.current = false;
          navTimeout.current = null;
        }, 1000);
        return;
      }

      switch (e.key) {
        case '1':
          callbacks?.onFilterChange?.('all');
          break;
        case '2':
          callbacks?.onFilterChange?.('stock');
          break;
        case '3':
          callbacks?.onFilterChange?.('crypto');
          break;
        case '4':
          callbacks?.onFilterChange?.('forex');
          break;
        case '/':
          e.preventDefault();
          callbacks?.onFocusSearch?.();
          break;
        case '?':
          setShowHelp((prev) => !prev);
          break;
        case 'Escape':
          setShowHelp(false);
          pendingNav.current = false;
          if (navTimeout.current) {
            clearTimeout(navTimeout.current);
            navTimeout.current = null;
          }
          break;
      }
    },
    [callbacks],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (navTimeout.current) {
        clearTimeout(navTimeout.current);
      }
    };
  }, [handleKeyDown]);

  return { showHelp, setShowHelp };
}

export const KEYBOARD_SHORTCUTS = [
  { key: '1', description: 'Show all signals' },
  { key: '2', description: 'Filter: Stocks' },
  { key: '3', description: 'Filter: Crypto' },
  { key: '4', description: 'Filter: Forex' },
  { key: '/', description: 'Focus search' },
  { key: '?', description: 'Toggle this help' },
  { key: 'Esc', description: 'Close modal / blur input' },
  { key: 'G H', description: 'Go to Home' },
  { key: 'G W', description: 'Go to Watchlist' },
  { key: 'G P', description: 'Go to Portfolio' },
  { key: 'G B', description: 'Go to Brief' },
  { key: 'G T', description: 'Go to Track Record' },
  { key: 'G N', description: 'Go to News' },
] as const;
