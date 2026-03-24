import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';

vi.mock('@/hooks/useSignals', () => ({
  useSignals: vi.fn(),
}));

vi.mock('@/hooks/useMarketData', () => ({
  useMarketData: vi.fn(),
}));

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(),
}));

vi.mock('@/components/markets/MarketOverview', () => ({
  MarketOverview: () => <div data-testid="market-overview">Market Overview</div>,
}));

vi.mock('@/components/signals/SignalFeed', () => ({
  SignalFeed: ({ signals, isLoading, error }: { signals: unknown[]; isLoading: boolean; error: string | null }) => (
    <div data-testid="signal-feed">{isLoading ? 'Loading...' : error ?? `${signals.length} signals`}</div>
  ),
}));

vi.mock('@/components/signals/WinRateCard', () => ({
  WinRateCard: () => <div data-testid="win-rate">Win Rate</div>,
}));

vi.mock('@/components/signals/AskAI', () => ({
  AskAI: () => <div data-testid="ask-ai">Ask AI</div>,
}));

vi.mock('@/components/shared/WelcomeModal', () => ({
  WelcomeModal: () => <div data-testid="welcome-modal" />,
}));

vi.mock('@/components/shared/GuidedTour', () => ({
  GuidedTour: () => <div data-testid="guided-tour" />,
}));

vi.mock('@/components/shared/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { makeSignal } from './helpers';

beforeEach(() => {
  useSignalStore.setState({
    signals: [],
    isLoading: false,
    error: null,
    total: 0,
    unseenCount: 5,
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

describe('Dashboard Page', () => {
  it('renders market overview section', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('market-overview')).toBeInTheDocument();
  });

  it('renders win rate card', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('win-rate')).toBeInTheDocument();
  });

  it('renders signal feed', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('signal-feed')).toBeInTheDocument();
  });

  it('renders Ask AI section', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('ask-ai')).toBeInTheDocument();
  });

  it('renders welcome modal', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('welcome-modal')).toBeInTheDocument();
  });

  it('renders guided tour', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByTestId('guided-tour')).toBeInTheDocument();
  });

  it('shows inline disclaimer', async () => {
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByText(/AI-generated analysis, not financial advice/)).toBeInTheDocument();
  });

  it('passes signals from store to SignalFeed', async () => {
    useSignalStore.setState({
      signals: [makeSignal({ id: '1' }), makeSignal({ id: '2' })],
      isLoading: false,
      error: null,
    });
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByText('2 signals')).toBeInTheDocument();
  });

  it('passes loading state to SignalFeed', async () => {
    useSignalStore.setState({ isLoading: true });
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('passes error to SignalFeed', async () => {
    useSignalStore.setState({ error: 'Server down' });
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    expect(screen.getByText('Server down')).toBeInTheDocument();
  });

  it('resets unseen count on mount', async () => {
    useSignalStore.setState({ unseenCount: 5 });
    const { default: Dashboard } = await import('@/app/page');
    render(<Dashboard />);
    // After mount, resetUnseen should have been called
    expect(useSignalStore.getState().unseenCount).toBe(0);
  });

  it('has data-tour attributes for guided tour', async () => {
    const { default: Dashboard } = await import('@/app/page');
    const { container } = render(<Dashboard />);
    expect(container.querySelector('[data-tour="market-overview"]')).toBeTruthy();
    expect(container.querySelector('[data-tour="win-rate"]')).toBeTruthy();
    expect(container.querySelector('[data-tour="signal-feed"]')).toBeTruthy();
  });
});
