'use client';

import { useEffect, useRef, useCallback } from 'react';
import { SignalWebSocket } from '@/lib/websocket';
import type { WSMessage, Signal, MarketSnapshot } from '@/lib/types';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';

/**
 * Hook that manages WebSocket connection for real-time signal and market updates.
 * Automatically connects on mount and disconnects on unmount.
 */
export function useWebSocket(markets: string[] = ['stock', 'crypto', 'forex']) {
  const addSignal = useSignalStore((s) => s.addSignal);
  const updatePrice = useMarketStore((s) => s.updatePrice);
  const wsRef = useRef<SignalWebSocket | null>(null);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.type === 'signal' && msg.data) {
        addSignal(msg.data as Signal);
      } else if (msg.type === 'market_update' && msg.data) {
        updatePrice(msg.data as MarketSnapshot);
      }
    },
    [addSignal, updatePrice],
  );

  useEffect(() => {
    const ws = new SignalWebSocket(handleMessage);
    wsRef.current = ws;
    ws.connect(markets);

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [handleMessage, markets]);

  return wsRef;
}
