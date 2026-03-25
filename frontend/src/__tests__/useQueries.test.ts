import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('@/lib/api', () => ({
  api: {
    getSignals: vi.fn(),
    getSignal: vi.fn(),
    getSignalStats: vi.fn(),
    getAccuracyTrend: vi.fn(),
    getSignalHistory: vi.fn(),
    getMarketOverview: vi.fn(),
    getWatchlist: vi.fn(),
    updateWatchlist: vi.fn(),
  },
}));

import { api } from '@/lib/api';
import {
  useSignalsQuery,
  useSignalQuery,
  useSignalStatsQuery,
  useAccuracyTrendQuery,
  useSignalHistoryQuery,
  useMarketOverviewQuery,
  useWatchlistQuery,
  useWatchlistMutation,
  queryKeys,
} from '@/hooks/useQueries';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

beforeEach(() => {
  vi.mocked(api.getSignals).mockReset();
  vi.mocked(api.getSignal).mockReset();
  vi.mocked(api.getSignalStats).mockReset();
  vi.mocked(api.getAccuracyTrend).mockReset();
  vi.mocked(api.getSignalHistory).mockReset();
  vi.mocked(api.getMarketOverview).mockReset();
  vi.mocked(api.getWatchlist).mockReset();
  vi.mocked(api.updateWatchlist).mockReset();
});

describe('queryKeys', () => {
  it('returns stable signal keys', () => {
    expect(queryKeys.signals).toEqual(['signals']);
    expect(queryKeys.signal('abc')).toEqual(['signals', 'abc']);
    expect(queryKeys.signalStats).toEqual(['signal-stats']);
  });

  it('returns watchlist keys', () => {
    expect(queryKeys.watchlist).toEqual(['watchlist']);
  });
});

describe('useSignalsQuery', () => {
  it('fetches signals', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({
      data: [{ id: '1', symbol: 'BTC' }],
      meta: { total: 1 },
    });

    const { result } = renderHook(() => useSignalsQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.data).toHaveLength(1);
  });

  it('passes params to API', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({ data: [], meta: {} });
    const params = new URLSearchParams({ market: 'forex' });

    renderHook(() => useSignalsQuery(params), { wrapper: createWrapper() });
    await waitFor(() => expect(api.getSignals).toHaveBeenCalledWith(params));
  });
});

describe('useSignalQuery', () => {
  it('fetches single signal', async () => {
    vi.mocked(api.getSignal).mockResolvedValue({ data: { id: 'abc', symbol: 'ETH' } });

    const { result } = renderHook(() => useSignalQuery('abc'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.data.id).toBe('abc');
  });

  it('is disabled with empty id', () => {
    const { result } = renderHook(() => useSignalQuery(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useSignalStatsQuery', () => {
  it('fetches stats', async () => {
    vi.mocked(api.getSignalStats).mockResolvedValue({ total_signals: 100, win_rate: 65 });

    const { result } = renderHook(() => useSignalStatsQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({ total_signals: 100, win_rate: 65 });
  });
});

describe('useAccuracyTrendQuery', () => {
  it('handles array response', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue([
      { week: 'W1', start_date: '2025-01-01', total: 10, hit_target: 6, win_rate: 60 },
    ]);

    const { result } = renderHook(() => useAccuracyTrendQuery(8), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
  });

  it('handles { data: [...] } response', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue({
      data: [{ week: 'W1', start_date: '2025-01-01', total: 10, hit_target: 6, win_rate: 60 }],
    });

    const { result } = renderHook(() => useAccuracyTrendQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
  });
});

describe('useSignalHistoryQuery', () => {
  it('fetches history', async () => {
    vi.mocked(api.getSignalHistory).mockResolvedValue({ data: [], meta: { total: 0 } });

    const { result } = renderHook(() => useSignalHistoryQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useMarketOverviewQuery', () => {
  it('fetches market overview', async () => {
    vi.mocked(api.getMarketOverview).mockResolvedValue({
      data: { stocks: [], crypto: [], forex: [] },
    });

    const { result } = renderHook(() => useMarketOverviewQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useWatchlistQuery', () => {
  it('fetches watchlist', async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: ['RELIANCE.NS'] } });

    const { result } = renderHook(() => useWatchlistQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.data.watchlist).toContain('RELIANCE.NS');
  });
});

describe('useWatchlistMutation', () => {
  it('calls updateWatchlist on mutate', async () => {
    vi.mocked(api.updateWatchlist).mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useWatchlistMutation(), { wrapper: createWrapper() });

    result.current.mutate({ symbol: 'RELIANCE.NS', action: 'add' });
    await waitFor(() => expect(api.updateWatchlist).toHaveBeenCalledWith('RELIANCE.NS', 'add'));
  });
});
