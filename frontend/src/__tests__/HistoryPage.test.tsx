import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getSignalHistory: vi.fn(),
  },
}));

vi.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

import { api } from '@/lib/api';
import { makeHistoryItem, makeSignal } from './helpers';

const mockGetHistory = vi.mocked(api.getSignalHistory);

beforeEach(() => {
  mockGetHistory.mockReset();
});

describe('HistoryPage', () => {
  it('shows loading state initially', async () => {
    mockGetHistory.mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders Signal History heading', async () => {
    mockGetHistory.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('Signal History')).toBeInTheDocument();
    });
  });

  it('renders outcome filter buttons', async () => {
    const items = [makeHistoryItem()];
    mockGetHistory.mockResolvedValue({ data: items, meta: { timestamp: '', count: 1, total: 1 } });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      // Filter buttons include emojis, so use regex
      expect(screen.getAllByText(/All/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Target Hit/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Stop Hit/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Expired/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Pending/).length).toBeGreaterThan(0);
    });
  });

  it('renders market filter buttons', async () => {
    const items = [makeHistoryItem()];
    mockGetHistory.mockResolvedValue({ data: items, meta: { timestamp: '', count: 1, total: 1 } });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('All Markets')).toBeInTheDocument();
    });
  });

  it('renders history items', async () => {
    const items = [
      makeHistoryItem({
        id: 'h1',
        outcome: 'hit_target',
        return_pct: '5.50',
        signal: makeSignal({ symbol: 'RELIANCE.NS', signal_type: 'BUY' }),
      }),
    ];
    mockGetHistory.mockResolvedValue({
      data: items,
      meta: { timestamp: '', count: 1, total: 1 },
    });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getAllByText('RELIANCE').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when no history', async () => {
    mockGetHistory.mockResolvedValue({ data: [], meta: { timestamp: '', count: 0 } });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/No signal history/i)).toBeInTheDocument();
    });
  });

  it('shows win rate stats', async () => {
    const items = [
      makeHistoryItem({ outcome: 'hit_target', return_pct: '5.0' }),
      makeHistoryItem({ id: 'h2', outcome: 'hit_stop', return_pct: '-2.0', signal: makeSignal({ id: '2' }) }),
    ];
    mockGetHistory.mockResolvedValue({
      data: items,
      meta: { timestamp: '', count: 2, total: 2 },
    });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      // Win rate should be displayed somewhere
      expect(screen.getByText(/Win Rate/i)).toBeInTheDocument();
    });
  });

  it('has Load More button when hasMore', async () => {
    const items = Array.from({ length: 5 }, (_, i) =>
      makeHistoryItem({ id: `h${i}`, signal: makeSignal({ id: `s${i}`, symbol: `SYM${i}.NS` }) }),
    );
    mockGetHistory.mockResolvedValue({
      data: items,
      meta: { timestamp: '', count: 5, total: 50 },
    });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Load More/)).toBeInTheDocument();
    });
  });

  it('has export buttons', async () => {
    const items = [makeHistoryItem()];
    mockGetHistory.mockResolvedValue({
      data: items,
      meta: { timestamp: '', count: 1, total: 1 },
    });
    const { default: Page } = await import('@/app/history/page');
    render(<Page />);
    await waitFor(() => {
      // Export section
      expect(screen.getByText(/CSV/i)).toBeInTheDocument();
    });
  });
});
