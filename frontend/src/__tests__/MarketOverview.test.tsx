import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MarketOverview } from '@/components/markets/MarketOverview';
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

beforeEach(() => {
  useMarketStore.setState({
    stocks: [],
    crypto: [],
    forex: [],
    isLoading: false,
    lastUpdated: null,
    wsStatus: 'connected',
    fetchError: null,
  });
});

describe('MarketOverview', () => {
  it('shows "Loading markets..." when loading with no data', () => {
    render(
      <MarketOverview stocks={[]} crypto={[]} forex={[]} isLoading={true} lastUpdated={null} />,
    );
    expect(screen.getByText('Loading markets...')).toBeInTheDocument();
  });

  it('shows stock symbols (top 3)', () => {
    const stocks = [
      makeSnapshot({ symbol: 'RELIANCE.NS', price: '2500', change_pct: '0.5' }),
      makeSnapshot({ symbol: 'TCS.NS', price: '4000', change_pct: '-0.3' }),
      makeSnapshot({ symbol: 'INFY.NS', price: '1500', change_pct: '1.2' }),
      makeSnapshot({ symbol: 'WIPRO.NS', price: '500', change_pct: '-0.1' }),
    ];
    render(
      <MarketOverview stocks={stocks} crypto={[]} forex={[]} isLoading={false} lastUpdated={new Date().toISOString()} />,
    );
    // Only top 3
    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText('TCS')).toBeInTheDocument();
    expect(screen.getByText('INFY')).toBeInTheDocument();
    expect(screen.queryByText('WIPRO')).not.toBeInTheDocument();
  });

  it('shows market section labels', () => {
    const stocks = [makeSnapshot()];
    const crypto = [makeSnapshot({ symbol: 'BTCUSDT', market_type: 'crypto' })];
    const forex = [makeSnapshot({ symbol: 'USDINR', market_type: 'forex' })];
    render(
      <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={false} lastUpdated={new Date().toISOString()} />,
    );
    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.getByText('Crypto')).toBeInTheDocument();
    expect(screen.getByText('Forex')).toBeInTheDocument();
  });

  it('shows stale data warning when lastUpdated is > 5 min old', () => {
    const staleTime = new Date(Date.now() - 6 * 60 * 1000).toISOString();
    render(
      <MarketOverview
        stocks={[makeSnapshot()]}
        crypto={[]}
        forex={[]}
        isLoading={false}
        lastUpdated={staleTime}
      />,
    );
    expect(screen.getByText(/⚠/)).toBeInTheDocument();
  });

  it('does not show stale warning when data is fresh', () => {
    render(
      <MarketOverview
        stocks={[makeSnapshot()]}
        crypto={[]}
        forex={[]}
        isLoading={false}
        lastUpdated={new Date().toISOString()}
      />,
    );
    expect(screen.queryByText(/⚠/)).not.toBeInTheDocument();
  });

  it('shows connection status from market store', () => {
    useMarketStore.setState({ wsStatus: 'connected' });
    render(
      <MarketOverview stocks={[]} crypto={[]} forex={[]} isLoading={false} lastUpdated={null} />,
    );
    // Connected dot should be present with title="Live"
    expect(screen.getByTitle('Live')).toBeInTheDocument();
  });

  it('shows fetchError message when set', () => {
    useMarketStore.setState({ fetchError: 'API timeout' });
    render(
      <MarketOverview stocks={[]} crypto={[]} forex={[]} isLoading={false} lastUpdated={null} />,
    );
    expect(screen.getByText('API timeout')).toBeInTheDocument();
  });

  it('renders price and change for each ticker', () => {
    const stocks = [makeSnapshot({ symbol: 'RELIANCE.NS', price: '2500.50', change_pct: '1.42' })];
    render(
      <MarketOverview stocks={stocks} crypto={[]} forex={[]} isLoading={false} lastUpdated={new Date().toISOString()} />,
    );
    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
  });
});
