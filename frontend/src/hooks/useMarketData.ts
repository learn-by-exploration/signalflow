'use client';

import { useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useMarketStore } from '@/store/marketStore';
import type { MarketSnapshot } from '@/lib/types';

interface MarketApiResponse {
  data: {
    stocks: MarketSnapshot[];
    crypto: MarketSnapshot[];
    forex: MarketSnapshot[];
  };
}

/**
 * Hook that fetches market overview data and polls every 30 seconds.
 */
export function useMarketData() {
  const { setMarkets, setLoading, setFetchError } = useMarketStore();
  const failureCount = useRef(0);

  const fetchMarkets = useCallback(async () => {
    try {
      setLoading(true);
      const res = (await api.getMarketOverview()) as MarketApiResponse;
      setMarkets(res.data);
      failureCount.current = 0;
    } catch {
      failureCount.current += 1;
      setLoading(false);
      if (failureCount.current >= 3) {
        setFetchError('Having trouble reaching the server. Data shown may not be current.');
      }
    }
  }, [setMarkets, setLoading, setFetchError]);

  useEffect(() => {
    fetchMarkets();
    const interval = setInterval(fetchMarkets, 30000);
    return () => clearInterval(interval);
  }, [fetchMarkets]);

  return { refetch: fetchMarkets };
}
