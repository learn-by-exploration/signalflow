/**
 * React Query hooks for SignalFlow API.
 *
 * These hooks replace manual useState/useEffect patterns with
 * automatic caching, deduplication, background refetching, and retry.
 *
 * Migration: existing pages can adopt these hooks one at a time.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Signal, SignalStats, WeeklyTrendItem, SignalHistoryItem } from '@/lib/types';

// ── Query Keys ──
export const queryKeys = {
  signals: ['signals'] as const,
  signal: (id: string) => ['signals', id] as const,
  signalStats: ['signal-stats'] as const,
  accuracyTrend: (weeks: number) => ['accuracy-trend', weeks] as const,
  signalHistory: (params?: string) => ['signal-history', params] as const,
  marketOverview: ['market-overview'] as const,
  watchlist: (chatId: number) => ['watchlist', chatId] as const,
  portfolio: (chatId: number) => ['portfolio', chatId] as const,
  feedback: ['feedback'] as const,
};

// ── Signal Hooks ──

export function useSignalsQuery(params?: URLSearchParams) {
  return useQuery({
    queryKey: [...queryKeys.signals, params?.toString()],
    queryFn: () => api.getSignals(params) as Promise<{ data: Signal[]; meta: { total?: number } }>,
    staleTime: 30_000,
    refetchInterval: 60_000, // Auto-refresh every 60s
  });
}

export function useSignalQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.signal(id),
    queryFn: () => api.getSignal(id) as Promise<{ data: Signal }>,
    enabled: !!id,
  });
}

// ── Stats Hooks ──

export function useSignalStatsQuery() {
  return useQuery({
    queryKey: queryKeys.signalStats,
    queryFn: () => api.getSignalStats() as Promise<SignalStats>,
    staleTime: 60_000,
  });
}

export function useAccuracyTrendQuery(weeks = 8) {
  return useQuery({
    queryKey: queryKeys.accuracyTrend(weeks),
    queryFn: async () => {
      const res = await api.getAccuracyTrend(weeks);
      const items = Array.isArray(res) ? res : (res as { data?: WeeklyTrendItem[] })?.data ?? [];
      return items as WeeklyTrendItem[];
    },
    staleTime: 5 * 60_000,
  });
}

// ── History Hook ──

export function useSignalHistoryQuery(params?: URLSearchParams) {
  return useQuery({
    queryKey: queryKeys.signalHistory(params?.toString()),
    queryFn: () =>
      api.getSignalHistory(params) as Promise<{
        data: (SignalHistoryItem & { signal?: Signal })[];
        meta: { total?: number };
      }>,
  });
}

// ── Market Overview Hook ──

export function useMarketOverviewQuery() {
  return useQuery({
    queryKey: queryKeys.marketOverview,
    queryFn: () => api.getMarketOverview(),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
}

// ── Watchlist Hooks ──

export function useWatchlistQuery(chatId: number) {
  return useQuery({
    queryKey: queryKeys.watchlist(chatId),
    queryFn: () => api.getWatchlist(chatId) as Promise<{ data: { watchlist: string[] } }>,
    enabled: !!chatId,
  });
}

export function useWatchlistMutation(chatId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ symbol, action }: { symbol: string; action: 'add' | 'remove' }) =>
      api.updateWatchlist(chatId, symbol, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.watchlist(chatId) });
    },
  });
}
