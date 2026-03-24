import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { useSignalStore } from '@/store/signalStore';
import { usePreferencesStore } from '@/store/preferencesStore';
import { makeSignal } from './helpers';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: { getSignals: vi.fn() },
}));

vi.mock('@/hooks/useKeyboardShortcuts', () => ({
  useKeyboardShortcuts: () => ({ showHelp: false, setShowHelp: vi.fn() }),
  KEYBOARD_SHORTCUTS: [],
}));

beforeEach(() => {
  useSignalStore.setState({
    signals: [],
    isLoading: false,
    error: null,
    total: 0,
    unseenCount: 0,
  });
  usePreferencesStore.setState({
    viewMode: 'detailed',
    defaultMarketFilter: 'all',
  });
});

describe('SignalFeed', () => {
  it('renders header', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);
    expect(screen.getByText('Active Signals')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading', () => {
    render(<SignalFeed signals={[]} isLoading={true} error={null} />);
    // Skeleton renders elements with animate-pulse
    const container = document.querySelector('.animate-pulse');
    expect(container).toBeTruthy();
  });

  it('shows error message', () => {
    render(<SignalFeed signals={[]} isLoading={false} error="Connection failed" />);
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });

  it('shows empty state when no signals', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);
    expect(screen.getByText(/No.*signals right now/)).toBeInTheDocument();
  });

  it('renders signal cards', () => {
    const signals = [
      makeSignal({ id: '1', symbol: 'RELIANCE.NS', confidence: 80 }),
      makeSignal({ id: '2', symbol: 'TCS.NS', confidence: 70 }),
    ];
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);
    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText('TCS')).toBeInTheDocument();
  });

  it('sorts signals by confidence (highest first)', () => {
    const signals = [
      makeSignal({ id: '1', symbol: 'LOW.NS', confidence: 50 }),
      makeSignal({ id: '2', symbol: 'HIGH.NS', confidence: 90 }),
    ];
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);
    const cards = screen.getAllByRole('button');
    // HIGH should appear before LOW
    const highIndex = cards.findIndex((c) => c.textContent?.includes('HIGH'));
    const lowIndex = cards.findIndex((c) => c.textContent?.includes('LOW'));
    expect(highIndex).toBeLessThan(lowIndex);
  });

  it('has market filter buttons', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.getByText('Crypto')).toBeInTheDocument();
    expect(screen.getByText('Forex')).toBeInTheDocument();
  });

  it('filters by market type', () => {
    const signals = [
      makeSignal({ id: '1', symbol: 'RELIANCE.NS', market_type: 'stock' }),
      makeSignal({ id: '2', symbol: 'BTCUSDT', market_type: 'crypto' }),
    ];
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);

    fireEvent.click(screen.getByText('Crypto'));
    expect(screen.queryByText('RELIANCE')).not.toBeInTheDocument();
    expect(screen.getByText('BTC')).toBeInTheDocument();
  });

  it('has timeframe filter options', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);
    expect(screen.getByText('Any')).toBeInTheDocument();
    expect(screen.getByText('Short')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Long')).toBeInTheDocument();
  });

  it('toggles search input', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);

    const searchBtn = screen.getByLabelText('Search symbols');
    fireEvent.click(searchBtn);
    expect(screen.getByPlaceholderText('Search symbol...')).toBeInTheDocument();

    // Toggle off
    fireEvent.click(searchBtn);
    expect(screen.queryByPlaceholderText('Search symbol...')).not.toBeInTheDocument();
  });

  it('filters signals by search term', () => {
    const signals = [
      makeSignal({ id: '1', symbol: 'RELIANCE.NS' }),
      makeSignal({ id: '2', symbol: 'HDFCBANK.NS' }),
    ];
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);

    fireEvent.click(screen.getByLabelText('Search symbols'));
    fireEvent.change(screen.getByPlaceholderText('Search symbol...'), { target: { value: 'HDFC' } });

    expect(screen.queryByText('RELIANCE')).not.toBeInTheDocument();
    expect(screen.getByText('HDFCBANK')).toBeInTheDocument();
  });

  it('shows search result count', () => {
    const signals = [makeSignal({ id: '1', symbol: 'RELIANCE.NS' })];
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);

    fireEvent.click(screen.getByLabelText('Search symbols'));
    fireEvent.change(screen.getByPlaceholderText('Search symbol...'), { target: { value: 'REL' } });

    expect(screen.getByText(/1 result/)).toBeInTheDocument();
  });

  it('shows pagination info when total is set', () => {
    useSignalStore.setState({ total: 50 });
    const signals = Array.from({ length: 5 }, (_, i) =>
      makeSignal({ id: String(i), symbol: `SYM${i}.NS` }),
    );
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);
    expect(screen.getByText(/Showing 5 of 50/)).toBeInTheDocument();
  });

  it('shows Load More button when hasMore', () => {
    useSignalStore.setState({ total: 50 });
    const signals = Array.from({ length: 5 }, (_, i) =>
      makeSignal({ id: String(i), symbol: `SYM${i}.NS` }),
    );
    render(<SignalFeed signals={signals} isLoading={false} error={null} />);
    expect(screen.getByText('Load More')).toBeInTheDocument();
  });

  it('shows stock empty state message for stock filter', () => {
    render(<SignalFeed signals={[]} isLoading={false} error={null} />);
    fireEvent.click(screen.getByText('Stocks'));
    expect(screen.getByText(/NSE market hours/)).toBeInTheDocument();
  });
});
