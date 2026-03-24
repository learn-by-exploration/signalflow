import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getAlertConfig: vi.fn(),
    getPriceAlerts: vi.fn(),
    getWatchlist: vi.fn(),
    createAlertConfig: vi.fn(),
    updateAlertConfig: vi.fn(),
    createPriceAlert: vi.fn(),
    deletePriceAlert: vi.fn(),
    updateWatchlist: vi.fn(),
  },
}));

vi.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock('@/components/shared/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('@/store/userStore', () => ({
  useUserStore: (selector: (s: { chatId: number }) => unknown) => selector({ chatId: 123 }),
}));

import { api } from '@/lib/api';

beforeEach(() => {
  vi.mocked(api.getAlertConfig).mockReset();
  vi.mocked(api.getPriceAlerts).mockReset();
  vi.mocked(api.getWatchlist).mockReset();
});

describe('AlertsPage', () => {
  it('shows loading state initially', async () => {
    vi.mocked(api.getAlertConfig).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getPriceAlerts).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getWatchlist).mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/alerts/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders Alerts & Settings heading', async () => {
    vi.mocked(api.getAlertConfig).mockResolvedValue({
      data: {
        id: 'cfg-1',
        markets: ['stock', 'crypto', 'forex'],
        min_confidence: 60,
        signal_types: ['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL'],
      },
    });
    vi.mocked(api.getPriceAlerts).mockResolvedValue({ data: [] });
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: [] } });
    const { default: Page } = await import('@/app/alerts/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('Alerts & Settings')).toBeInTheDocument();
    });
  });

  it('renders market toggle options', async () => {
    vi.mocked(api.getAlertConfig).mockResolvedValue({
      data: {
        id: 'cfg-1',
        markets: ['stock', 'crypto'],
        min_confidence: 60,
        signal_types: [],
      },
    });
    vi.mocked(api.getPriceAlerts).mockResolvedValue({ data: [] });
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: [] } });
    const { default: Page } = await import('@/app/alerts/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getAllByText(/Stocks/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Crypto/).length).toBeGreaterThan(0);
    });
  });

  it('renders confidence slider', async () => {
    vi.mocked(api.getAlertConfig).mockResolvedValue({
      data: {
        id: 'cfg-1',
        markets: ['stock'],
        min_confidence: 75,
        signal_types: [],
      },
    });
    vi.mocked(api.getPriceAlerts).mockResolvedValue({ data: [] });
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: [] } });
    const { default: Page } = await import('@/app/alerts/page');
    render(<Page />);
    await waitFor(() => {
      const slider = document.querySelector('input[type="range"]');
      expect(slider).toBeTruthy();
    });
  });

  it('renders watchlist section', async () => {
    vi.mocked(api.getAlertConfig).mockResolvedValue({
      data: { id: 'cfg-1', markets: [], min_confidence: 60, signal_types: [] },
    });
    vi.mocked(api.getPriceAlerts).mockResolvedValue({ data: [] });
    vi.mocked(api.getWatchlist).mockResolvedValue({
      data: { watchlist: ['RELIANCE.NS', 'TCS.NS'] },
    });
    const { default: Page } = await import('@/app/alerts/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Watchlist/i)).toBeInTheDocument();
    });
  });
});
