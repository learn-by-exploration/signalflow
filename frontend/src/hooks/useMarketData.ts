'use client';

import { useEffect, useCallback } from 'react';
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
  const { setMarkets, setLoading } = useMarketStore();

  const fetchMarkets = useCallback(async () => {
    try {
      setLoading(true);
      const res = (await api.getMarketOverview()) as MarketApiResponse;
      setMarkets(res.data);
    } catch {
      // Market data is non-critical — fail silently, retry on next poll
      setLoading(false);
    }
  }, [setMarkets, setLoading]);

  useEffect(() => {
    fetchMarkets();
    const interval = setInterval(fetchMarkets, 30000);
    return () => clearInterval(interval);
  }, [fetchMarkets]);

  return { refetch: fetchMarkets };
}
