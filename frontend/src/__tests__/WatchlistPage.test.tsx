import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getWatchlist: vi.fn(),
    updateWatchlist: vi.fn(),
    getSignals: vi.fn(),
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
  vi.mocked(api.getWatchlist).mockReset();
  vi.mocked(api.getSignals).mockReset();
});

describe('WatchlistPage', () => {
  it('shows loading state initially', async () => {
    vi.mocked(api.getWatchlist).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/watchlist/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders Watchlist heading', async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: ['RELIANCE.NS'] } });
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/watchlist/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Watchlist');
    });
  });

  it('shows watchlist items', async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({
      data: { watchlist: ['RELIANCE.NS', 'TCS.NS'] },
    });
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/watchlist/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getAllByText(/RELIANCE/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/TCS/).length).toBeGreaterThan(0);
    });
  });

  it('shows empty state with no watched symbols', async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: [] } });
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/watchlist/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/no symbols|Add symbols|empty/i)).toBeInTheDocument();
    });
  });

  it('has add symbol input', async () => {
    vi.mocked(api.getWatchlist).mockResolvedValue({ data: { watchlist: [] } });
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/watchlist/page');
    render(<Page />);
    await waitFor(() => {
      const input = document.querySelector('input');
      expect(input).toBeTruthy();
    });
  });
});
