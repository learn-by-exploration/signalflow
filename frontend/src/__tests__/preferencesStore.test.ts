import { describe, it, expect, beforeEach } from 'vitest';
import { usePreferencesStore } from '@/store/preferencesStore';

// Mock localStorage
const store: Record<string, string> = {};
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  },
  writable: true,
});

describe('preferencesStore', () => {
  beforeEach(() => {
    Object.keys(store).forEach((k) => delete store[k]);
  });

  it('defaults to standard view mode', () => {
    const { viewMode } = usePreferencesStore.getState();
    expect(viewMode).toBe('standard');
  });

  it('defaults to medium text size', () => {
    const { textSize } = usePreferencesStore.getState();
    expect(textSize).toBe('medium');
  });

  it('defaults to all market filter', () => {
    const { defaultMarketFilter } = usePreferencesStore.getState();
    expect(defaultMarketFilter).toBe('all');
  });

  it('persists view mode to localStorage', () => {
    usePreferencesStore.getState().setViewMode('simple');
    expect(usePreferencesStore.getState().viewMode).toBe('simple');
    expect(store['sf_view_mode']).toBe('"simple"');
  });

  it('persists text size to localStorage', () => {
    usePreferencesStore.getState().setTextSize('large');
    expect(usePreferencesStore.getState().textSize).toBe('large');
    expect(store['sf_text_size']).toBe('"large"');
  });

  it('persists market filter to localStorage', () => {
    usePreferencesStore.getState().setDefaultMarketFilter('crypto');
    expect(usePreferencesStore.getState().defaultMarketFilter).toBe('crypto');
    expect(store['sf_market_filter']).toBe('"crypto"');
  });
});
