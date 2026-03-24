import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useMarketData } from '@/hooks/useMarketData';
import { useMarketStore } from '@/store/marketStore';

vi.mock('@/lib/api', () => ({
  api: {
    getMarketOverview: vi.fn(),
  },
}));

import { api } from '@/lib/api';

const mockGetMarkets = vi.mocked(api.getMarketOverview);

beforeEach(() => {
  useMarketStore.setState({
    stocks: [],
    crypto: [],
    forex: [],
    isLoading: false,
    lastUpdated: null,
    wsStatus: 'disconnected',
    fetchError: null,
  });
  mockGetMarkets.mockReset();
});

describe('useMarketData', () => {
  it('fetches market data on mount', async () => {
    mockGetMarkets.mockResolvedValue({
      data: { stocks: [{ symbol: 'RELIANCE.NS' }], crypto: [], forex: [] },
    });

    renderHook(() => useMarketData());
    await waitFor(() => {
      expect(mockGetMarkets).toHaveBeenCalledTimes(1);
    });
  });

  it('stores market data in store', async () => {
    mockGetMarkets.mockResolvedValue({
      data: {
        stocks: [{ symbol: 'RELIANCE.NS', price: '2450', change_pct: '1.2', volume: '100', market_type: 'stock' }],
        crypto: [],
        forex: [],
      },
    });

    renderHook(() => useMarketData());
    await waitFor(() => {
      expect(useMarketStore.getState().stocks).toHaveLength(1);
    });
  });

  it('sets loading state', async () => {
    let resolve: (v: unknown) => void;
    mockGetMarkets.mockReturnValue(new Promise((r) => { resolve = r; }));

    renderHook(() => useMarketData());
    expect(useMarketStore.getState().isLoading).toBe(true);

    await act(async () => {
      resolve!({ data: { stocks: [], crypto: [], forex: [] } });
    });
  });

  it('shows error after 3 consecutive failures', async () => {
    vi.useFakeTimers();
    mockGetMarkets.mockRejectedValue(new Error('fail'));

    renderHook(() => useMarketData());
    await vi.advanceTimersByTimeAsync(0);

    // After first failure, no error message yet
    expect(useMarketStore.getState().fetchError).toBeNull();

    // Trigger 2 more failures via polling
    await vi.advanceTimersByTimeAsync(30000);
    await vi.advanceTimersByTimeAsync(30000);

    expect(useMarketStore.getState().fetchError).toContain('trouble reaching');
    vi.useRealTimers();
  });

  it('resets failure count on success', async () => {
    vi.useFakeTimers();
    // First call fails
    mockGetMarkets.mockRejectedValueOnce(new Error('fail'));
    // Second call succeeds
    mockGetMarkets.mockResolvedValueOnce({
      data: { stocks: [], crypto: [], forex: [] },
    });

    renderHook(() => useMarketData());
    await vi.advanceTimersByTimeAsync(0);

    await vi.advanceTimersByTimeAsync(30000);

    // Now fail twice more — should NOT trigger error since count was reset
    mockGetMarkets.mockRejectedValueOnce(new Error('fail'));
    mockGetMarkets.mockRejectedValueOnce(new Error('fail'));

    await vi.advanceTimersByTimeAsync(30000);
    await vi.advanceTimersByTimeAsync(30000);

    expect(useMarketStore.getState().fetchError).toBeNull();
    vi.useRealTimers();
  });

  it('polls every 30 seconds', async () => {
    vi.useFakeTimers();
    mockGetMarkets.mockResolvedValue({ data: { stocks: [], crypto: [], forex: [] } });

    renderHook(() => useMarketData());
    await vi.advanceTimersByTimeAsync(0);
    expect(mockGetMarkets).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(30000);
    expect(mockGetMarkets).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('cleans up interval on unmount', async () => {
    vi.useFakeTimers();
    mockGetMarkets.mockResolvedValue({ data: { stocks: [], crypto: [], forex: [] } });

    const { unmount } = renderHook(() => useMarketData());
    await vi.advanceTimersByTimeAsync(0);
    expect(mockGetMarkets).toHaveBeenCalledTimes(1);

    unmount();
    await vi.advanceTimersByTimeAsync(60000);
    expect(mockGetMarkets).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it('returns refetch function', async () => {
    mockGetMarkets.mockResolvedValue({ data: { stocks: [], crypto: [], forex: [] } });

    const { result } = renderHook(() => useMarketData());
    await waitFor(() => expect(mockGetMarkets).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.refetch();
    });
    expect(mockGetMarkets).toHaveBeenCalledTimes(2);
  });
});
