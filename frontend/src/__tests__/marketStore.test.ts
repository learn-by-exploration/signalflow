import { describe, it, expect, beforeEach } from 'vitest';
import { useMarketStore } from '@/store/marketStore';
import type { MarketSnapshot } from '@/lib/types';

function makeSnapshot(overrides: Partial<MarketSnapshot> = {}): MarketSnapshot {
  return {
    symbol: 'HDFCBANK.NS',
    price: '1678.90',
    change_pct: '1.42',
    volume: '5000000',
    market_type: 'stock',
    ...overrides,
  };
}

describe('marketStore', () => {
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
  });

  it('starts with empty defaults', () => {
    const state = useMarketStore.getState();
    expect(state.stocks).toEqual([]);
    expect(state.crypto).toEqual([]);
    expect(state.forex).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.wsStatus).toBe('disconnected');
  });

  it('setMarkets populates all three arrays', () => {
    const stocks = [makeSnapshot({ symbol: 'RELIANCE.NS' })];
    const crypto = [makeSnapshot({ symbol: 'BTCUSDT', market_type: 'crypto', price: '97000' })];
    const forex = [makeSnapshot({ symbol: 'USDINR', market_type: 'forex', price: '83.50' })];

    useMarketStore.getState().setMarkets({ stocks, crypto, forex });

    const state = useMarketStore.getState();
    expect(state.stocks).toHaveLength(1);
    expect(state.crypto).toHaveLength(1);
    expect(state.forex).toHaveLength(1);
    expect(state.isLoading).toBe(false);
    expect(state.lastUpdated).toBeTruthy();
    expect(state.fetchError).toBeNull();
  });

  it('updatePrice upserts an existing stock symbol', () => {
    useMarketStore.getState().setMarkets({
      stocks: [makeSnapshot({ symbol: 'RELIANCE.NS', price: '2500' })],
      crypto: [],
      forex: [],
    });

    useMarketStore.getState().updatePrice(
      makeSnapshot({ symbol: 'RELIANCE.NS', price: '2550', market_type: 'stock' }),
    );

    const { stocks } = useMarketStore.getState();
    expect(stocks).toHaveLength(1);
    expect(stocks[0].price).toBe('2550');
  });

  it('updatePrice adds a new symbol when not found', () => {
    useMarketStore.getState().setMarkets({ stocks: [], crypto: [], forex: [] });

    useMarketStore.getState().updatePrice(
      makeSnapshot({ symbol: 'ETHUSDT', market_type: 'crypto', price: '3200' }),
    );

    const { crypto } = useMarketStore.getState();
    expect(crypto).toHaveLength(1);
    expect(crypto[0].symbol).toBe('ETHUSDT');
  });

  it('updatePrice maps "stock" market_type to "stocks" key', () => {
    useMarketStore.getState().setMarkets({ stocks: [], crypto: [], forex: [] });

    useMarketStore.getState().updatePrice(
      makeSnapshot({ symbol: 'TCS.NS', market_type: 'stock', price: '4000' }),
    );

    expect(useMarketStore.getState().stocks).toHaveLength(1);
    expect(useMarketStore.getState().crypto).toHaveLength(0);
  });

  it('updatePrice sets lastUpdated timestamp', () => {
    useMarketStore.setState({ lastUpdated: null });

    useMarketStore.getState().updatePrice(
      makeSnapshot({ symbol: 'BTCUSDT', market_type: 'crypto', price: '100000' }),
    );

    expect(useMarketStore.getState().lastUpdated).toBeTruthy();
  });

  it('setLoading updates isLoading', () => {
    useMarketStore.getState().setLoading(true);
    expect(useMarketStore.getState().isLoading).toBe(true);
  });

  it('setWsStatus transitions through connection states', () => {
    const { setWsStatus } = useMarketStore.getState();
    setWsStatus('connecting');
    expect(useMarketStore.getState().wsStatus).toBe('connecting');
    setWsStatus('connected');
    expect(useMarketStore.getState().wsStatus).toBe('connected');
    setWsStatus('reconnecting');
    expect(useMarketStore.getState().wsStatus).toBe('reconnecting');
    setWsStatus('disconnected');
    expect(useMarketStore.getState().wsStatus).toBe('disconnected');
  });

  it('setFetchError stores and clears error', () => {
    useMarketStore.getState().setFetchError('API timeout');
    expect(useMarketStore.getState().fetchError).toBe('API timeout');

    useMarketStore.getState().setFetchError(null);
    expect(useMarketStore.getState().fetchError).toBeNull();
  });
});
