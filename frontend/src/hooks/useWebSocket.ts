'use client';

import { useEffect, useRef, useCallback } from 'react';
import { SignalWebSocket } from '@/lib/websocket';
import type { WSMessage, Signal, MarketSnapshot } from '@/lib/types';
import type { ConnectionStatus } from '@/lib/websocket';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';
import { showSignalNotification } from '@/lib/notifications';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/hooks/useQueries';

const DEFAULT_MARKETS = ['stock', 'crypto', 'forex'];

/**
 * Hook that manages WebSocket connection for real-time signal and market updates.
 * Automatically connects on mount and disconnects on unmount.
 */
export function useWebSocket(markets: string[] = DEFAULT_MARKETS) {
  const addSignal = useSignalStore((s) => s.addSignal);
  const incrementUnseen = useSignalStore((s) => s.incrementUnseen);
  const updatePrice = useMarketStore((s) => s.updatePrice);
  const setWsStatus = useMarketStore((s) => s.setWsStatus);
  const wsRef = useRef<SignalWebSocket | null>(null);
  const marketsKey = JSON.stringify(markets);

  let queryClient: ReturnType<typeof useQueryClient> | null = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    queryClient = useQueryClient();
  } catch {
    // QueryProvider may not be available in all contexts
  }

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.type === 'signal' && msg.data) {
        const signal = msg.data as Signal;
        addSignal(signal);
        showSignalNotification(signal);
        // Invalidate React Query signals cache
        queryClient?.invalidateQueries({ queryKey: queryKeys.signals });
        if (typeof window !== 'undefined' && window.location.pathname !== '/') {
          incrementUnseen();
        }
      } else if (msg.type === 'market_update' && msg.data) {
        updatePrice(msg.data as MarketSnapshot);
        // Invalidate React Query markets cache
        queryClient?.invalidateQueries({ queryKey: queryKeys.marketOverview });
      }
    },
    [addSignal, incrementUnseen, updatePrice, queryClient],
  );

  const handleStatusChange = useCallback(
    (status: ConnectionStatus) => {
      setWsStatus(status);
    },
    [setWsStatus],
  );

  useEffect(() => {
    const ws = new SignalWebSocket(handleMessage, handleStatusChange);
    wsRef.current = ws;
    ws.connect(markets);

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handleMessage, handleStatusChange, marketsKey]);

  return wsRef;
}
