import { describe, it, expect, beforeEach } from 'vitest';
import { useSignalStore } from '@/store/signalStore';
import type { Signal } from '@/lib/types';

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'sig-1',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 72,
    current_price: '1678.90',
    target_price: '1780.00',
    stop_loss: '1630.00',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Credit growth accelerating.',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: '2026-03-20T10:30:00Z',
    expires_at: null,
    ...overrides,
  };
}

describe('signalStore', () => {
  beforeEach(() => {
    useSignalStore.setState({
      signals: [],
      isLoading: false,
      error: null,
      total: null,
      unseenCount: 0,
    });
  });

  it('starts with empty defaults', () => {
    const state = useSignalStore.getState();
    expect(state.signals).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.total).toBeNull();
    expect(state.unseenCount).toBe(0);
  });

  it('setSignals replaces signals and sets total', () => {
    const signals = [makeSignal({ id: 'a' }), makeSignal({ id: 'b' })];
    useSignalStore.getState().setSignals(signals, 42);

    const state = useSignalStore.getState();
    expect(state.signals).toHaveLength(2);
    expect(state.signals[0].id).toBe('a');
    expect(state.total).toBe(42);
    expect(state.isLoading).toBe(false);
  });

  it('setSignals without total sets it to null', () => {
    useSignalStore.getState().setSignals([makeSignal()]);
    expect(useSignalStore.getState().total).toBeNull();
  });

  it('appendSignals adds to existing list', () => {
    useSignalStore.getState().setSignals([makeSignal({ id: 'a' })], 5);
    useSignalStore.getState().appendSignals([makeSignal({ id: 'b' })], 10);

    const state = useSignalStore.getState();
    expect(state.signals).toHaveLength(2);
    expect(state.signals[0].id).toBe('a');
    expect(state.signals[1].id).toBe('b');
    expect(state.total).toBe(10);
  });

  it('appendSignals preserves existing total when none provided', () => {
    useSignalStore.getState().setSignals([], 99);
    useSignalStore.getState().appendSignals([makeSignal({ id: 'c' })]);
    expect(useSignalStore.getState().total).toBe(99);
  });

  it('addSignal prepends to the list', () => {
    useSignalStore.getState().setSignals([makeSignal({ id: 'old' })]);
    useSignalStore.getState().addSignal(makeSignal({ id: 'new' }));

    const { signals } = useSignalStore.getState();
    expect(signals).toHaveLength(2);
    expect(signals[0].id).toBe('new');
    expect(signals[1].id).toBe('old');
  });

  it('setLoading updates isLoading', () => {
    useSignalStore.getState().setLoading(true);
    expect(useSignalStore.getState().isLoading).toBe(true);
    useSignalStore.getState().setLoading(false);
    expect(useSignalStore.getState().isLoading).toBe(false);
  });

  it('setError sets error and clears loading', () => {
    useSignalStore.getState().setLoading(true);
    useSignalStore.getState().setError('Network failure');

    const state = useSignalStore.getState();
    expect(state.error).toBe('Network failure');
    expect(state.isLoading).toBe(false);
  });

  it('setError with null clears the error', () => {
    useSignalStore.getState().setError('fail');
    useSignalStore.getState().setError(null);
    expect(useSignalStore.getState().error).toBeNull();
  });

  it('incrementUnseen increments the counter', () => {
    useSignalStore.getState().incrementUnseen();
    useSignalStore.getState().incrementUnseen();
    useSignalStore.getState().incrementUnseen();
    expect(useSignalStore.getState().unseenCount).toBe(3);
  });

  it('resetUnseen resets the counter to zero', () => {
    useSignalStore.getState().incrementUnseen();
    useSignalStore.getState().incrementUnseen();
    useSignalStore.getState().resetUnseen();
    expect(useSignalStore.getState().unseenCount).toBe(0);
  });
});
