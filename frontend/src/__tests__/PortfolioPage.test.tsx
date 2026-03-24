import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getPortfolioSummary: vi.fn(),
    getTrades: vi.fn(),
    logTrade: vi.fn(),
  },
}));

vi.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock('@/components/shared/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('@/components/charts/EquityCurve', () => ({
  EquityCurve: () => <div data-testid="equity-curve" />,
}));

vi.mock('@/components/charts/AllocationPieChart', () => ({
  AllocationPieChart: () => <div data-testid="allocation-pie" />,
}));

vi.mock('@/store/userStore', () => ({
  useUserStore: (selector: (s: { chatId: number }) => unknown) => selector({ chatId: 123 }),
}));

import { api } from '@/lib/api';
import { makePortfolioSummary, makeTrade } from './helpers';

beforeEach(() => {
  vi.mocked(api.getPortfolioSummary).mockReset();
  vi.mocked(api.getTrades).mockReset();
});

describe('PortfolioPage', () => {
  it('shows loading state initially', async () => {
    vi.mocked(api.getPortfolioSummary).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getTrades).mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/portfolio/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders portfolio heading', async () => {
    vi.mocked(api.getPortfolioSummary).mockResolvedValue({ data: makePortfolioSummary() });
    vi.mocked(api.getTrades).mockResolvedValue({ data: [makeTrade()] });
    const { default: Page } = await import('@/app/portfolio/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Portfolio/i)).toBeInTheDocument();
    });
  });

  it('renders portfolio summary values', async () => {
    vi.mocked(api.getPortfolioSummary).mockResolvedValue({
      data: makePortfolioSummary({
        total_invested: '50000.00',
        current_value: '52500.00',
        total_pnl: '2500.00',
        total_pnl_pct: 5.0,
      }),
    });
    vi.mocked(api.getTrades).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/portfolio/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getAllByText(/P&L/i).length).toBeGreaterThan(0);
    });
  });

  it('shows error state', async () => {
    vi.mocked(api.getPortfolioSummary).mockRejectedValue(new Error('fail'));
    vi.mocked(api.getTrades).mockRejectedValue(new Error('fail'));
    const { default: Page } = await import('@/app/portfolio/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
    });
  });

  it('renders trade log section', async () => {
    vi.mocked(api.getPortfolioSummary).mockResolvedValue({ data: makePortfolioSummary() });
    vi.mocked(api.getTrades).mockResolvedValue({ data: [makeTrade()] });
    const { default: Page } = await import('@/app/portfolio/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getAllByText(/HDFCBANK/).length).toBeGreaterThan(0);
    });
  });
});
