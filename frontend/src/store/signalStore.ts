/**
 * Zustand store for signal state management.
 */

import { create } from 'zustand';
import type { Signal } from '@/lib/types';

interface SignalState {
  signals: Signal[];
  isLoading: boolean;
  error: string | null;
  setSignals: (signals: Signal[]) => void;
  addSignal: (signal: Signal) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  isLoading: false,
  error: null,
  setSignals: (signals) => set({ signals, isLoading: false }),
  addSignal: (signal) =>
    set((state) => ({ signals: [signal, ...state.signals] })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
}));
