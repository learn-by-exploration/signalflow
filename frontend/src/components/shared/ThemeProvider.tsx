'use client';

import { useEffect } from 'react';
import { usePreferencesStore } from '@/store/preferencesStore';

/**
 * Applies the current theme mode (dark/light) to the document root.
 * Sets data-theme attribute and CSS class for tailwind dark mode overrides.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const themeMode = usePreferencesStore((s) => s.themeMode);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', themeMode);
    if (themeMode === 'light') {
      root.classList.add('theme-light');
      root.classList.remove('theme-dark');
    } else {
      root.classList.add('theme-dark');
      root.classList.remove('theme-light');
    }
  }, [themeMode]);

  return <>{children}</>;
}
