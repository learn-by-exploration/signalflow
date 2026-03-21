/**
 * Zustand store for market overview data.
 */

import { create } from 'zustand';
import type { MarketSnapshot } from '@/lib/types';
import type { ConnectionStatus } from '@/lib/websocket';

interface MarketState {
  stocks: MarketSnapshot[];
  crypto: MarketSnapshot[];
  forex: MarketSnapshot[];
  isLoading: boolean;
  lastUpdated: string | null;
  wsStatus: ConnectionStatus;
  fetchError: string | null;
  setMarkets: (data: { stocks: MarketSnapshot[]; crypto: MarketSnapshot[]; forex: MarketSnapshot[] }) => void;
  updatePrice: (snapshot: MarketSnapshot) => void;
  setLoading: (loading: boolean) => void;
  setWsStatus: (status: ConnectionStatus) => void;
  setFetchError: (error: string | null) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  stocks: [],
  crypto: [],
  forex: [],
  isLoading: false,
  lastUpdated: null,
  wsStatus: 'disconnected' as ConnectionStatus,
  fetchError: null,
  setMarkets: (data) => set({ ...data, isLoading: false, lastUpdated: new Date().toISOString(), fetchError: null }),
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
      return { [key]: list, lastUpdated: new Date().toISOString() };
    }),
  setLoading: (isLoading) => set({ isLoading }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setFetchError: (fetchError) => set({ fetchError }),
}));
