import { describe, it, expect, beforeEach } from 'vitest';
import { useTierStore } from '@/store/tierStore';
import { TIER_CONFIG, FEATURE_LABELS } from '@/lib/tiers';

beforeEach(() => {
  useTierStore.setState({ tier: 'free', signalsViewedToday: 0 });
});

describe('Tier Config', () => {
  it('free tier has limited signals per day', () => {
    expect(TIER_CONFIG.free.signalsPerDay).toBe(5);
  });

  it('pro tier has unlimited signals', () => {
    expect(TIER_CONFIG.pro.signalsPerDay).toBeNull();
  });

  it('all feature labels are defined', () => {
    const allFeatures = new Set([
      ...Object.keys(TIER_CONFIG.free.features),
      ...Object.keys(TIER_CONFIG.pro.features),
    ]);
    for (const feat of allFeatures) {
      expect(FEATURE_LABELS[feat]).toBeDefined();
      expect(FEATURE_LABELS[feat].label).toBeTruthy();
    }
  });

  it('pro has all features enabled', () => {
    for (const enabled of Object.values(TIER_CONFIG.pro.features)) {
      expect(enabled).toBe(true);
    }
  });

  it('free has some features disabled', () => {
    const disabledCount = Object.values(TIER_CONFIG.free.features).filter((v) => !v).length;
    expect(disabledCount).toBeGreaterThan(0);
  });
});

describe('useTierStore', () => {
  it('defaults to free tier', () => {
    expect(useTierStore.getState().tier).toBe('free');
  });

  it('setTier changes the tier', () => {
    useTierStore.getState().setTier('pro');
    expect(useTierStore.getState().tier).toBe('pro');
  });

  it('hasFeature returns true for free features', () => {
    expect(useTierStore.getState().hasFeature('viewSignals')).toBe(true);
    expect(useTierStore.getState().hasFeature('watchlist')).toBe(true);
  });

  it('hasFeature returns false for pro-only features on free tier', () => {
    expect(useTierStore.getState().hasFeature('aiQA')).toBe(false);
    expect(useTierStore.getState().hasFeature('backtesting')).toBe(false);
  });

  it('hasFeature returns true for all features on pro tier', () => {
    useTierStore.getState().setTier('pro');
    expect(useTierStore.getState().hasFeature('aiQA')).toBe(true);
    expect(useTierStore.getState().hasFeature('backtesting')).toBe(true);
  });

  it('canViewMoreSignals respects free tier limit', () => {
    const store = useTierStore.getState();
    expect(store.canViewMoreSignals()).toBe(true);

    // View 5 signals
    for (let i = 0; i < 5; i++) {
      useTierStore.getState().incrementSignalsViewed();
    }
    expect(useTierStore.getState().canViewMoreSignals()).toBe(false);
  });

  it('canViewMoreSignals is always true for pro', () => {
    useTierStore.getState().setTier('pro');
    for (let i = 0; i < 100; i++) {
      useTierStore.getState().incrementSignalsViewed();
    }
    expect(useTierStore.getState().canViewMoreSignals()).toBe(true);
  });

  it('resetDailyCount resets the counter', () => {
    useTierStore.getState().incrementSignalsViewed();
    useTierStore.getState().incrementSignalsViewed();
    expect(useTierStore.getState().signalsViewedToday).toBe(2);

    useTierStore.getState().resetDailyCount();
    expect(useTierStore.getState().signalsViewedToday).toBe(0);
  });
});
