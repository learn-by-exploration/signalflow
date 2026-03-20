/**
 * Zustand store for alert configuration.
 */

import { create } from 'zustand';
import type { AlertConfig } from '@/lib/types';

interface AlertState {
  config: AlertConfig | null;
  isLoading: boolean;
  setConfig: (config: AlertConfig) => void;
  setLoading: (loading: boolean) => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  config: null,
  isLoading: false,
  setConfig: (config) => set({ config, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
}));
