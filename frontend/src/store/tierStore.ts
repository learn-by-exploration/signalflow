import { create } from 'zustand';
import type { UserTier } from '@/lib/tiers';
import { TIER_CONFIG } from '@/lib/tiers';

interface TierState {
  tier: UserTier;
  setTier: (tier: UserTier) => void;
  hasFeature: (feature: string) => boolean;
  signalsViewedToday: number;
  incrementSignalsViewed: () => void;
  resetDailyCount: () => void;
  canViewMoreSignals: () => boolean;
}

export const useTierStore = create<TierState>()(
  (set, get) => ({
    tier: 'free',
    signalsViewedToday: 0,

    setTier: (tier) => set({ tier }),

    hasFeature: (feature) => {
      const config = TIER_CONFIG[get().tier];
      return config.features[feature] ?? false;
    },

    incrementSignalsViewed: () =>
      set((state) => ({ signalsViewedToday: state.signalsViewedToday + 1 })),

    resetDailyCount: () => set({ signalsViewedToday: 0 }),

    canViewMoreSignals: () => {
      const { tier, signalsViewedToday } = get();
      const config = TIER_CONFIG[tier];
      if (config.signalsPerDay === null) return true;
      return signalsViewedToday < config.signalsPerDay;
    },
  }),
);
