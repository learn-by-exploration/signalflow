/**
 * Zustand store for user preferences (persisted to localStorage).
 * Handles: view mode, text size, default market filter.
 */

import { create } from 'zustand';
import type { MarketType } from '@/lib/types';

export type ViewMode = 'standard' | 'simple';
export type TextSize = 'small' | 'medium' | 'large';

interface PreferencesState {
  viewMode: ViewMode;
  textSize: TextSize;
  defaultMarketFilter: 'all' | MarketType;
  setViewMode: (mode: ViewMode) => void;
  setTextSize: (size: TextSize) => void;
  setDefaultMarketFilter: (filter: 'all' | MarketType) => void;
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
  defaultMarketFilter: getStored<'all' | MarketType>('sf_market_filter', 'all'),

  setViewMode: (mode) => {
    setStored('sf_view_mode', mode);
    set({ viewMode: mode });
  },
  setTextSize: (size) => {
    setStored('sf_text_size', size);
    set({ textSize: size });
  },
  setDefaultMarketFilter: (filter) => {
    setStored('sf_market_filter', filter);
    set({ defaultMarketFilter: filter });
  },
}));
