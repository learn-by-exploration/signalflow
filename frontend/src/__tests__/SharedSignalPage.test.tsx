import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'share-abc-123' }),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getSharedSignal: vi.fn(),
  },
}));

import { api } from '@/lib/api';

beforeEach(() => {
  vi.mocked(api.getSharedSignal).mockReset();
});

describe('SharedSignalPage', () => {
  it('shows loading state initially', async () => {
    vi.mocked(api.getSharedSignal).mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    expect(screen.getByText('Loading signal...')).toBeInTheDocument();
  });

  it('shows error when signal not found', async () => {
    vi.mocked(api.getSharedSignal).mockRejectedValue(new Error('not found'));
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Signal not found or link has expired/)).toBeInTheDocument();
    });
  });

  it('has link to dashboard on error', async () => {
    vi.mocked(api.getSharedSignal).mockRejectedValue(new Error('not found'));
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Go to SignalFlow Dashboard/)).toBeInTheDocument();
    });
  });

  it('renders shared signal data', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'RELIANCE.NS',
        market_type: 'stock',
        signal_type: 'STRONG_BUY',
        confidence: 92,
        current_price: '2450.00',
        target_price: '2600.00',
        stop_loss: '2350.00',
        timeframe: '2-4 weeks',
        ai_reasoning: 'Strong bullish momentum.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('RELIANCE')).toBeInTheDocument();
      expect(screen.getByText('STRONG BUY')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
    });
  });

  it('shows confidence as main number', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'BTCUSDT',
        market_type: 'crypto',
        signal_type: 'BUY',
        confidence: 78,
        current_price: '97000',
        target_price: '102000',
        stop_loss: '94000',
        timeframe: null,
        ai_reasoning: 'Breaking resistance.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('78%')).toBeInTheDocument();
      expect(screen.getByText('confidence')).toBeInTheDocument();
    });
  });

  it('renders AI reasoning', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'ETHUSDT',
        market_type: 'crypto',
        signal_type: 'BUY',
        confidence: 70,
        current_price: '3200',
        target_price: '3500',
        stop_loss: '3000',
        timeframe: '1-2 weeks',
        ai_reasoning: 'ETH showing bullish divergence on MACD.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('ETH showing bullish divergence on MACD.')).toBeInTheDocument();
    });
  });

  it('shows timeframe when present', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'TCS.NS',
        market_type: 'stock',
        signal_type: 'BUY',
        confidence: 65,
        current_price: '3890',
        target_price: '4100',
        stop_loss: '3750',
        timeframe: '3-6 months',
        ai_reasoning: 'Long-term growth trend.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/3-6 months/)).toBeInTheDocument();
    });
  });

  it('shows disclaimer', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'RELIANCE.NS',
        market_type: 'stock',
        signal_type: 'BUY',
        confidence: 70,
        current_price: '2450',
        target_price: '2600',
        stop_loss: '2350',
        timeframe: null,
        ai_reasoning: 'Test.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/not financial advice/i)).toBeInTheDocument();
    });
  });

  it('has Try SignalFlow link', async () => {
    vi.mocked(api.getSharedSignal).mockResolvedValue({
      data: {
        symbol: 'RELIANCE.NS',
        market_type: 'stock',
        signal_type: 'BUY',
        confidence: 70,
        current_price: '2450',
        target_price: '2600',
        stop_loss: '2350',
        timeframe: null,
        ai_reasoning: 'Test.',
        created_at: '2026-03-20T10:00:00Z',
      },
    });
    const { default: Page } = await import('@/app/shared/[id]/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Try SignalFlow AI/)).toBeInTheDocument();
    });
  });
});
