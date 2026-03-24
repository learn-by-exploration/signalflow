import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSignals } from '@/hooks/useSignals';
import { useSignalStore } from '@/store/signalStore';

vi.mock('@/lib/api', () => ({
  api: {
    getSignals: vi.fn(),
  },
}));

import { api } from '@/lib/api';

const mockGetSignals = vi.mocked(api.getSignals);

beforeEach(() => {
  useSignalStore.setState({
    signals: [],
    isLoading: false,
    error: null,
    total: 0,
    unseenCount: 0,
  });
  mockGetSignals.mockReset();
});

describe('useSignals', () => {
  it('fetches signals on mount', async () => {
    mockGetSignals.mockResolvedValue({
      data: [{ id: '1', symbol: 'RELIANCE.NS' }],
      meta: { timestamp: '', count: 1, total: 1 },
    });

    renderHook(() => useSignals());
    await waitFor(() => {
      expect(mockGetSignals).toHaveBeenCalledTimes(1);
    });

    expect(useSignalStore.getState().signals).toHaveLength(1);
  });

  it('passes params to API', async () => {
    mockGetSignals.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });

    const params = new URLSearchParams({ market: 'crypto' });
    renderHook(() => useSignals(params));
    await waitFor(() => {
      expect(mockGetSignals).toHaveBeenCalledWith(params);
    });
  });

  it('sets loading state', async () => {
    let resolve: (v: unknown) => void;
    mockGetSignals.mockReturnValue(new Promise((r) => { resolve = r; }));

    renderHook(() => useSignals());

    // Loading should be set to true  
    expect(useSignalStore.getState().isLoading).toBe(true);

    await act(async () => {
      resolve!({ data: [], meta: { timestamp: '', count: 0 } });
    });
  });

  it('sets error on failure', async () => {
    mockGetSignals.mockRejectedValue(new Error('Network failure'));

    renderHook(() => useSignals());
    await waitFor(() => {
      expect(useSignalStore.getState().error).toBe('Network failure');
    });
  });

  it('sets generic error for non-Error throws', async () => {
    mockGetSignals.mockRejectedValue('random error');

    renderHook(() => useSignals());
    await waitFor(() => {
      expect(useSignalStore.getState().error).toBe('Failed to fetch signals');
    });
  });

  it('polls every 30 seconds', async () => {
    vi.useFakeTimers();
    mockGetSignals.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });

    renderHook(() => useSignals());

    // Flush initial call
    await vi.advanceTimersByTimeAsync(0);
    expect(mockGetSignals).toHaveBeenCalledTimes(1);

    // Advance past 30s
    await vi.advanceTimersByTimeAsync(30000);
    expect(mockGetSignals).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('cleans up interval on unmount', async () => {
    vi.useFakeTimers();
    mockGetSignals.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });

    const { unmount } = renderHook(() => useSignals());
    await vi.advanceTimersByTimeAsync(0);
    expect(mockGetSignals).toHaveBeenCalledTimes(1);

    unmount();

    await vi.advanceTimersByTimeAsync(60000);
    // Should not have fetched again after unmount
    expect(mockGetSignals).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it('returns refetch function', async () => {
    mockGetSignals.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });

    const { result } = renderHook(() => useSignals());
    await waitFor(() => expect(mockGetSignals).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.refetch();
    });
    expect(mockGetSignals).toHaveBeenCalledTimes(2);
  });

  it('stores total from meta', async () => {
    mockGetSignals.mockResolvedValue({
      data: [{ id: '1' }],
      meta: { timestamp: '', count: 1, total: 42 },
    });

    renderHook(() => useSignals());
    await waitFor(() => {
      expect(useSignalStore.getState().total).toBe(42);
    });
  });
});
