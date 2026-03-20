/**
 * Zustand store for market overview data.
 */

import { create } from 'zustand';
import type { MarketSnapshot } from '@/lib/types';

interface MarketState {
  stocks: MarketSnapshot[];
  crypto: MarketSnapshot[];
  forex: MarketSnapshot[];
  isLoading: boolean;
  setMarkets: (data: { stocks: MarketSnapshot[]; crypto: MarketSnapshot[]; forex: MarketSnapshot[] }) => void;
  updatePrice: (snapshot: MarketSnapshot) => void;
  setLoading: (loading: boolean) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  stocks: [],
  crypto: [],
  forex: [],
  isLoading: false,
  setMarkets: (data) => set({ ...data, isLoading: false }),
  updatePrice: (snapshot) =>
    set((state) => {
      const key = snapshot.market_type === 'stock' ? 'stocks' : snapshot.market_type;
      const list = [...state[key as keyof Pick<MarketState, 'stocks' | 'crypto' | 'forex'>]];
      const idx = list.findIndex((s) => s.symbol === snapshot.symbol);
      if (idx >= 0) {
        list[idx] = snapshot;
      } else {
        list.push(snapshot);
      }
      return { [key]: list };
    }),
  setLoading: (isLoading) => set({ isLoading }),
}));
