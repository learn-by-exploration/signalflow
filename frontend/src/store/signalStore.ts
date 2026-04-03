/**
 * Zustand store for signal state management.
 */

import { create } from 'zustand';
import type { Signal } from '@/lib/types';

const MAX_SIGNALS = 500;

interface SignalState {
  signals: Signal[];
  isLoading: boolean;
  error: string | null;
  total: number | null;
  unseenCount: number;
  setSignals: (signals: Signal[], total?: number | null) => void;
  appendSignals: (signals: Signal[], total?: number | null) => void;
  addSignal: (signal: Signal) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  incrementUnseen: () => void;
  resetUnseen: () => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  isLoading: false,
  error: null,
  total: null,
  unseenCount: 0,
  setSignals: (signals, total) => set({ signals, isLoading: false, total: total ?? null }),
  appendSignals: (newSignals, total) =>
    set((state) => {
      const updated = [...state.signals, ...newSignals];
      return {
        signals: updated.length > MAX_SIGNALS ? updated.slice(0, MAX_SIGNALS) : updated,
        isLoading: false,
        total: total ?? state.total,
      };
    }),
  addSignal: (signal) =>
    set((state) => {
      const updated = [signal, ...state.signals];
      return { signals: updated.length > MAX_SIGNALS ? updated.slice(0, MAX_SIGNALS) : updated };
    }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  incrementUnseen: () => set((state) => ({ unseenCount: state.unseenCount + 1 })),
  resetUnseen: () => set({ unseenCount: 0 }),
}));
