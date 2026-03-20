'use client';

import { useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useSignalStore } from '@/store/signalStore';
import type { Signal } from '@/lib/types';

interface SignalApiResponse {
  data: Signal[];
  meta: { timestamp: string; count: number };
}

/**
 * Hook that fetches signals from the REST API and polls every 30 seconds.
 */
export function useSignals(params?: URLSearchParams) {
  const { setSignals, setLoading, setError } = useSignalStore();

  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      const res = (await api.getSignals(params)) as SignalApiResponse;
      setSignals(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals');
    }
  }, [params, setSignals, setLoading, setError]);

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  return { refetch: fetchSignals };
}
