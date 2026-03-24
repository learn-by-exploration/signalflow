import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MarketHeatmap } from '@/components/markets/MarketHeatmap';
import { useMarketStore } from '@/store/marketStore';
import { makeStockSnapshots, makeCryptoSnapshots, makeForexSnapshots } from './helpers';

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

describe('MarketHeatmap', () => {
  it('returns null when no data', () => {
    const { container } = render(<MarketHeatmap />);
    expect(container.innerHTML).toBe('');
  });

  it('renders Market Pulse heading with data', () => {
    useMarketStore.setState({ stocks: makeStockSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('Market Pulse')).toBeInTheDocument();
  });

  it('renders stock section', () => {
    useMarketStore.setState({ stocks: makeStockSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('Stocks')).toBeInTheDocument();
  });

  it('renders crypto section', () => {
    useMarketStore.setState({ crypto: makeCryptoSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('Crypto')).toBeInTheDocument();
  });

  it('renders forex section', () => {
    useMarketStore.setState({ forex: makeForexSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('Forex')).toBeInTheDocument();
  });

  it('renders symbol names', () => {
    useMarketStore.setState({ stocks: makeStockSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText('HDFCBANK')).toBeInTheDocument();
  });

  it('shows percentage changes', () => {
    useMarketStore.setState({
      stocks: makeStockSnapshots(),
      crypto: makeCryptoSnapshots(),
    });
    render(<MarketHeatmap />);
    // Positive and negative percentages both displayed
    expect(screen.getByText('+1.25%')).toBeInTheDocument();
    expect(screen.getByText('-0.50%')).toBeInTheDocument();
  });

  it('only shows sections with data', () => {
    useMarketStore.setState({ stocks: makeStockSnapshots() });
    render(<MarketHeatmap />);
    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.queryByText('Crypto')).not.toBeInTheDocument();
    expect(screen.queryByText('Forex')).not.toBeInTheDocument();
  });

  it('colors positive changes green and negative red', () => {
    useMarketStore.setState({
      crypto: makeCryptoSnapshots(),
    });
    render(<MarketHeatmap />);
    // BTC is +3.87 → green, ETH is -1.20 → red
    const btcPct = screen.getByText('+3.87%');
    expect(btcPct.className).toContain('signal-buy');
    const ethPct = screen.getByText('-1.20%');
    expect(ethPct.className).toContain('signal-sell');
  });
});
