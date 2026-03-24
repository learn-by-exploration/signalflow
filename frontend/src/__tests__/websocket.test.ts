import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SignalWebSocket } from '@/lib/websocket';
import type { ConnectionStatus } from '@/lib/websocket';

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;

  sent: string[] = [];

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  // Test helpers
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.onclose?.();
  }

  simulateError() {
    this.onerror?.();
  }
}

let mockWsInstance: MockWebSocket;

beforeEach(() => {
  vi.useFakeTimers();
  mockWsInstance = new MockWebSocket();
  // Use a proper constructor function so `new WebSocket(...)` works
  const MockWsCtor = function () { return mockWsInstance; } as unknown as typeof WebSocket;
  MockWsCtor.OPEN = 1;
  MockWsCtor.CLOSED = 3;
  MockWsCtor.CLOSING = 2;
  MockWsCtor.CONNECTING = 0;
  MockWsCtor.prototype = MockWebSocket.prototype;
  globalThis.WebSocket = MockWsCtor;
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('SignalWebSocket', () => {
  it('sends "connecting" status on connect', () => {
    const statuses: ConnectionStatus[] = [];
    const ws = new SignalWebSocket(vi.fn(), (s) => statuses.push(s));
    ws.connect();
    expect(statuses).toContain('connecting');
  });

  it('sends "connected" status after onopen', () => {
    const statuses: ConnectionStatus[] = [];
    const ws = new SignalWebSocket(vi.fn(), (s) => statuses.push(s));
    ws.connect();
    mockWsInstance.simulateOpen();
    expect(statuses).toContain('connected');
  });

  it('sends subscribe message on open with default markets', () => {
    const ws = new SignalWebSocket(vi.fn());
    ws.connect();
    mockWsInstance.simulateOpen();

    expect(mockWsInstance.sent).toHaveLength(1);
    const msg = JSON.parse(mockWsInstance.sent[0]);
    expect(msg.type).toBe('subscribe');
    expect(msg.markets).toEqual(['stock', 'crypto', 'forex']);
  });

  it('sends subscribe with custom markets', () => {
    const ws = new SignalWebSocket(vi.fn());
    ws.connect(['crypto']);
    mockWsInstance.simulateOpen();

    const msg = JSON.parse(mockWsInstance.sent[0]);
    expect(msg.markets).toEqual(['crypto']);
  });

  it('forwards non-ping messages to onMessage callback', () => {
    const onMessage = vi.fn();
    const ws = new SignalWebSocket(onMessage);
    ws.connect();
    mockWsInstance.simulateOpen();

    mockWsInstance.simulateMessage({ type: 'signal', data: { id: 'test-signal' } });
    expect(onMessage).toHaveBeenCalledWith({ type: 'signal', data: { id: 'test-signal' } });
  });

  it('responds to ping with pong', () => {
    const ws = new SignalWebSocket(vi.fn());
    ws.connect();
    mockWsInstance.simulateOpen();
    mockWsInstance.sent = []; // clear subscribe message

    mockWsInstance.simulateMessage({ type: 'ping' });

    expect(mockWsInstance.sent).toHaveLength(1);
    const msg = JSON.parse(mockWsInstance.sent[0]);
    expect(msg.type).toBe('pong');
  });

  it('does not forward ping messages to onMessage', () => {
    const onMessage = vi.fn();
    const ws = new SignalWebSocket(onMessage);
    ws.connect();
    mockWsInstance.simulateOpen();

    mockWsInstance.simulateMessage({ type: 'ping' });
    expect(onMessage).not.toHaveBeenCalled();
  });

  it('sends "disconnected" on disconnect()', () => {
    const statuses: ConnectionStatus[] = [];
    const ws = new SignalWebSocket(vi.fn(), (s) => statuses.push(s));
    ws.connect();
    mockWsInstance.simulateOpen();
    ws.disconnect();

    expect(statuses[statuses.length - 1]).toBe('disconnected');
  });

  it('prevents reconnect after disconnect()', () => {
    let constructorCallCount = 0;
    const CountingWsCtor = function () { constructorCallCount++; return mockWsInstance; } as unknown as typeof WebSocket;
    CountingWsCtor.OPEN = 1;
    CountingWsCtor.CLOSED = 3;
    CountingWsCtor.CLOSING = 2;
    CountingWsCtor.CONNECTING = 0;
    globalThis.WebSocket = CountingWsCtor;

    const ws = new SignalWebSocket(vi.fn());
    ws.connect();
    mockWsInstance.simulateOpen();
    ws.disconnect();

    const countAfterDisconnect = constructorCallCount;
    vi.advanceTimersByTime(30000); // well past reconnect delay
    expect(constructorCallCount).toBe(countAfterDisconnect);
  });

  it('does not connect if already open', () => {
    let constructorCallCount = 0;
    const CountingWsCtor = function () { constructorCallCount++; return mockWsInstance; } as unknown as typeof WebSocket;
    CountingWsCtor.OPEN = 1;
    CountingWsCtor.CLOSED = 3;
    CountingWsCtor.CLOSING = 2;
    CountingWsCtor.CONNECTING = 0;
    globalThis.WebSocket = CountingWsCtor;

    const ws = new SignalWebSocket(vi.fn());
    ws.connect();
    mockWsInstance.simulateOpen();
    mockWsInstance.readyState = 1; // OPEN

    ws.connect(); // should noop
    expect(constructorCallCount).toBe(1);
  });

  it('ignores malformed messages without crashing', () => {
    const onMessage = vi.fn();
    const ws = new SignalWebSocket(onMessage);
    ws.connect();
    mockWsInstance.simulateOpen();

    // Send malformed JSON directly
    mockWsInstance.onmessage?.({ data: 'not-json{{{' });
    expect(onMessage).not.toHaveBeenCalled();
  });
});
