import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-signal-id' }),
}));

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getSignal: vi.fn(),
    getSymbolTrackRecord: vi.fn(),
  },
}));

vi.mock('@/components/signals/ConfidenceGauge', () => ({
  ConfidenceGauge: ({ confidence }: { confidence: number }) => <div data-testid="gauge">{confidence}%</div>,
}));

vi.mock('@/components/signals/SignalBadge', () => ({
  SignalBadge: ({ type }: { type: string }) => <div data-testid="badge">{type}</div>,
}));

vi.mock('@/components/signals/TargetProgressBar', () => ({
  TargetProgressBar: () => <div data-testid="progress-bar" />,
}));

vi.mock('@/components/signals/RiskCalculator', () => ({
  RiskCalculator: () => <div data-testid="risk-calc" />,
}));

vi.mock('@/components/signals/ShareButton', () => ({
  ShareButton: () => <div data-testid="share-btn" />,
}));

vi.mock('@/components/signals/ConfidenceBreakdown', () => ({
  ConfidenceBreakdown: () => <div data-testid="confidence-breakdown" />,
}));

vi.mock('@/components/signals/PipCalculator', () => ({
  PipCalculator: () => <div data-testid="pip-calc" />,
}));

vi.mock('@/components/signals/TrailingStopSuggestion', () => ({
  TrailingStopSuggestion: () => <div data-testid="trailing-stop" />,
}));

vi.mock('@/components/markets/Sparkline', () => ({
  Sparkline: () => <div data-testid="sparkline" />,
}));

vi.mock('@/components/charts/CandlestickChart', () => ({
  CandlestickChart: () => <div data-testid="candlestick-chart" />,
}));

vi.mock('@/components/shared/IndicatorTooltip', () => ({
  IndicatorTooltip: ({ name, value }: { name: string; value: string }) => <div>{name}: {value}</div>,
}));

vi.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

import { api } from '@/lib/api';
import { useMarketStore } from '@/store/marketStore';
import { makeSignal } from './helpers';

const mockGetSignal = vi.mocked(api.getSignal);
const mockGetTrackRecord = vi.mocked(api.getSymbolTrackRecord);

beforeEach(() => {
  mockGetSignal.mockReset();
  mockGetTrackRecord.mockReset();
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

describe('SignalDetailPage', () => {
  it('shows loading spinner initially', async () => {
    mockGetSignal.mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows error state when signal not found', async () => {
    mockGetSignal.mockRejectedValue(new Error('not found'));
    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('Signal not found.')).toBeInTheDocument();
    });
    expect(screen.getByText('← Back to Dashboard')).toBeInTheDocument();
  });

  it('renders signal detail with symbol name', async () => {
    const signal = makeSignal({ symbol: 'RELIANCE.NS', signal_type: 'STRONG_BUY', confidence: 92 });
    mockGetSignal.mockResolvedValue({ data: signal });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    });
  });

  it('renders confidence gauge', async () => {
    const signal = makeSignal({ confidence: 85 });
    mockGetSignal.mockResolvedValue({ data: signal });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByTestId('gauge')).toBeInTheDocument();
    });
  });

  it('renders AI reasoning', async () => {
    const signal = makeSignal({ ai_reasoning: 'Strong technical setup with bullish MACD crossover.' });
    mockGetSignal.mockResolvedValue({ data: signal });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Strong technical setup/)).toBeInTheDocument();
    });
  });

  it('renders target and stop-loss prices', async () => {
    const signal = makeSignal({
      current_price: '1678.90',
      target_price: '1780.00',
      stop_loss: '1630.00',
    });
    mockGetSignal.mockResolvedValue({ data: signal });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
    });
  });

  it('renders Risk Calculator', async () => {
    mockGetSignal.mockResolvedValue({ data: makeSignal() });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByTestId('risk-calc')).toBeInTheDocument();
    });
  });

  it('has back to dashboard link', async () => {
    mockGetSignal.mockResolvedValue({ data: makeSignal() });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      const links = screen.getAllByText('← Back to Dashboard');
      expect(links.length).toBeGreaterThan(0);
      expect(links[0].closest('a')).toHaveAttribute('href', '/');
    });
  });

  it('renders timeframe', async () => {
    const signal = makeSignal({ timeframe: '2-4 weeks' });
    mockGetSignal.mockResolvedValue({ data: signal });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/2-4 weeks/)).toBeInTheDocument();
    });
  });

  it('shows disclaimer', async () => {
    mockGetSignal.mockResolvedValue({ data: makeSignal() });
    mockGetTrackRecord.mockRejectedValue(new Error('no data'));

    const { default: Page } = await import('@/app/signal/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/not financial advice/i)).toBeInTheDocument();
    });
  });
});
