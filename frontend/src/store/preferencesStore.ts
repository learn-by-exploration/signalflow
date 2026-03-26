/**
 * Zustand store for user preferences (persisted to localStorage).
 * Handles: view mode, text size, default market filter.
 */

import { create } from 'zustand';
import type { MarketType } from '@/lib/types';

export type ViewMode = 'standard' | 'simple';
export type TextSize = 'small' | 'medium' | 'large';
export type ThemeMode = 'dark' | 'light';

interface PreferencesState {
  viewMode: ViewMode;
  textSize: TextSize;
  themeMode: ThemeMode;
  defaultMarketFilter: 'all' | MarketType;
  tradingCapital: number;
  maxRiskPct: number;
  setViewMode: (mode: ViewMode) => void;
  setTextSize: (size: TextSize) => void;
  setThemeMode: (mode: ThemeMode) => void;
  setDefaultMarketFilter: (filter: 'all' | MarketType) => void;
  setTradingCapital: (amount: number) => void;
  setMaxRiskPct: (pct: number) => void;
}

function getStored<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const val = localStorage.getItem(key);
    return val ? (JSON.parse(val) as T) : fallback;
  } catch {
    return fallback;
  }
}

function setStored<T>(key: string, value: T) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(key, JSON.stringify(value));
  }
}

export const usePreferencesStore = create<PreferencesState>((set) => ({
  viewMode: getStored<ViewMode>('sf_view_mode', 'standard'),
  textSize: getStored<TextSize>('sf_text_size', 'medium'),
  themeMode: getStored<ThemeMode>('sf_theme_mode', 'dark'),
  defaultMarketFilter: getStored<'all' | MarketType>('sf_market_filter', 'all'),
  tradingCapital: getStored<number>('sf_trading_capital', 0),
  maxRiskPct: getStored<number>('sf_max_risk_pct', 2),

  setViewMode: (mode) => {
    setStored('sf_view_mode', mode);
    set({ viewMode: mode });
  },
  setTextSize: (size) => {
    setStored('sf_text_size', size);
    set({ textSize: size });
  },
  setThemeMode: (mode) => {
    setStored('sf_theme_mode', mode);
    set({ themeMode: mode });
  },
  setDefaultMarketFilter: (filter) => {
    setStored('sf_market_filter', filter);
    set({ defaultMarketFilter: filter });
  },
  setTradingCapital: (amount) => {
    setStored('sf_trading_capital', amount);
    set({ tradingCapital: amount });
  },
  setMaxRiskPct: (pct) => {
    setStored('sf_max_risk_pct', pct);
    set({ maxRiskPct: pct });
  },
}));
