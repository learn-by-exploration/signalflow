import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';

// vi.hoisted returns values that are available inside vi.mock factories
const { mockConnect, mockDisconnect } = vi.hoisted(() => ({
  mockConnect: vi.fn(),
  mockDisconnect: vi.fn(),
}));

vi.mock('@/lib/websocket', () => ({
  SignalWebSocket: class MockSignalWebSocket {
    constructor(onMessage: (msg: unknown) => void, onStatus: (status: string) => void) {
      (globalThis as any).__ws_onMessage = onMessage;
      (globalThis as any).__ws_onStatus = onStatus;
    }
    connect = mockConnect;
    disconnect = mockDisconnect;
  },
}));

vi.mock('@/lib/notifications', () => ({
  showSignalNotification: vi.fn(),
}));

import { useWebSocket } from '@/hooks/useWebSocket';
import { showSignalNotification } from '@/lib/notifications';

function capturedOnMessage(): ((msg: unknown) => void) | undefined {
  return (globalThis as any).__ws_onMessage;
}
function capturedOnStatus(): ((status: string) => void) | undefined {
  return (globalThis as any).__ws_onStatus;
}

beforeEach(() => {
  mockConnect.mockReset();
  mockDisconnect.mockReset();
  delete (globalThis as any).__ws_onMessage;
  delete (globalThis as any).__ws_onStatus;
  vi.mocked(showSignalNotification).mockReset();
  useSignalStore.setState({
    signals: [],
    isLoading: false,
    error: null,
    total: 0,
    unseenCount: 0,
  });
  useMarketStore.setState({
    stocks: [],
    crypto: [],
    forex: [],
    isLoading: false,
    lastUpdated: null,
    wsStatus: 'disconnected',
    fetchError: null,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useWebSocket', () => {
  it('connects on mount with default markets', () => {
    renderHook(() => useWebSocket());
    expect(mockConnect).toHaveBeenCalledWith(['stock', 'crypto', 'forex']);
  });

  it('connects with custom markets', () => {
    renderHook(() => useWebSocket(['crypto']));
    expect(mockConnect).toHaveBeenCalledWith(['crypto']);
  });

  it('disconnects on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());
    unmount();
    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('adds signal to store on signal message', () => {
    renderHook(() => useWebSocket());

    const signal = {
      id: 'ws-sig-1',
      symbol: 'RELIANCE.NS',
      signal_type: 'BUY',
      confidence: 80,
      market_type: 'stock',
    };

    capturedOnMessage()?.({ type: 'signal', data: signal });
    expect(useSignalStore.getState().signals).toHaveLength(1);
    expect(useSignalStore.getState().signals[0].id).toBe('ws-sig-1');
  });

  it('shows notification for high-confidence signals', () => {
    renderHook(() => useWebSocket());

    const signal = { id: 'ws-sig-2', symbol: 'BTC', confidence: 90 };
    capturedOnMessage()?.({ type: 'signal', data: signal });
    expect(showSignalNotification).toHaveBeenCalled();
  });

  it('updates market price on market_update message', () => {
    renderHook(() => useWebSocket());

    const snapshot = { symbol: 'BTCUSDT', price: '100000', change_pct: '5.0', market_type: 'crypto' };
    capturedOnMessage()?.({ type: 'market_update', data: snapshot });

    const state = useMarketStore.getState();
    expect(state.crypto).toHaveLength(1);
    expect(state.crypto[0].symbol).toBe('BTCUSDT');
  });

  it('updates ws status on status change', () => {
    renderHook(() => useWebSocket());

    capturedOnStatus()?.('connected');
    expect(useMarketStore.getState().wsStatus).toBe('connected');
  });

  it('increments unseen count when not on dashboard', () => {
    Object.defineProperty(window, 'location', {
      value: { pathname: '/history' },
      writable: true,
    });

    renderHook(() => useWebSocket());

    capturedOnMessage()?.({ type: 'signal', data: { id: 'ws-sig-3' } });
    expect(useSignalStore.getState().unseenCount).toBe(1);
  });

  it('ignores messages without data', () => {
    renderHook(() => useWebSocket());

    capturedOnMessage()?.({ type: 'signal' });
    expect(useSignalStore.getState().signals).toHaveLength(0);

    capturedOnMessage()?.({ type: 'market_update' });
    // No crash, no update
  });

  it('ignores ping messages', () => {
    renderHook(() => useWebSocket());
    capturedOnMessage()?.({ type: 'ping' });
    expect(useSignalStore.getState().signals).toHaveLength(0);
  });
});
