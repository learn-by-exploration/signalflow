'use client';

import { useEffect, useState, useCallback } from 'react';

interface ShortcutCallbacks {
  onFilterChange?: (filter: 'all' | 'stock' | 'crypto' | 'forex') => void;
  onFocusSearch?: () => void;
}

/**
 * Global keyboard shortcuts for the dashboard.
 * 1/2/3/4 — Switch filter (All/Stocks/Crypto/Forex)
 * / — Focus search input
 * ? — Toggle shortcuts help modal
 * Escape — Close any modal/expanded card
 */
export function useKeyboardShortcuts(callbacks?: ShortcutCallbacks) {
  const [showHelp, setShowHelp] = useState(false);

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
          break;
      }
    },
    [callbacks],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
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
] as const;
