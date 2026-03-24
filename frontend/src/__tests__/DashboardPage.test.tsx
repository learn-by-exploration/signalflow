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

vi.mock('@/hooks/useQueries', () => ({
  useSignalsQuery: () => ({
    data: { data: useSignalStore.getState().signals, meta: { total: useSignalStore.getState().total } },
    isLoading: useSignalStore.getState().isLoading,
    error: useSignalStore.getState().error ? new Error(useSignalStore.getState().error!) : null,
    dataUpdatedAt: Date.now(),
  }),
  useMarketOverviewQuery: () => ({
    data: {
      data: {
        stocks: useMarketStore.getState().stocks,
        crypto: useMarketStore.getState().crypto,
        forex: useMarketStore.getState().forex,
      },
    },
    isLoading: useMarketStore.getState().isLoading,
    error: null,
    dataUpdatedAt: useMarketStore.getState().lastUpdated ? new Date(useMarketStore.getState().lastUpdated!).getTime() : 0,
  }),
  queryKeys: {
    signals: ['signals'],
    marketOverview: ['market-overview'],
  },
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
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('market-overview')).toBeInTheDocument();
  });

  it('renders win rate card', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('win-rate')).toBeInTheDocument();
  });

  it('renders signal feed', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('signal-feed')).toBeInTheDocument();
  });

  it('renders Ask AI section', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('ask-ai')).toBeInTheDocument();
  });

  it('renders welcome modal', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('welcome-modal')).toBeInTheDocument();
  });

  it('renders guided tour', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByTestId('guided-tour')).toBeInTheDocument();
  });

  it('shows inline disclaimer', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByText(/AI-generated analysis, not financial advice/)).toBeInTheDocument();
  });

  it('passes signals from store to SignalFeed', async () => {
    useSignalStore.setState({
      signals: [makeSignal({ id: '1' }), makeSignal({ id: '2' })],
      isLoading: false,
      error: null,
    });
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByText('2 signals')).toBeInTheDocument();
  });

  it('passes loading state to SignalFeed', async () => {
    useSignalStore.setState({ isLoading: true });
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('passes error to SignalFeed', async () => {
    useSignalStore.setState({ error: 'Server down' });
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(screen.getByText('Server down')).toBeInTheDocument();
  });

  it('resets unseen count on mount', async () => {
    useSignalStore.setState({ unseenCount: 5 });
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    render(<DashboardContent />);
    expect(useSignalStore.getState().unseenCount).toBe(0);
  });

  it('has data-tour attributes for guided tour', async () => {
    const { default: DashboardContent } = await import('@/components/dashboard/DashboardContent');
    const { container } = render(<DashboardContent />);
    expect(container.querySelector('[data-tour="market-overview"]')).toBeTruthy();
    expect(container.querySelector('[data-tour="win-rate"]')).toBeTruthy();
    expect(container.querySelector('[data-tour="signal-feed"]')).toBeTruthy();
  });
});
