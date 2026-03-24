import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { WinRateCard } from '@/components/signals/WinRateCard';
import type { SignalStats } from '@/lib/types';

// Mock api
vi.mock('@/lib/api', () => ({
  api: {
    getSignalStats: vi.fn(),
    getAccuracyTrend: vi.fn(),
  },
}));

// Mock Sparkline to simplify
vi.mock('@/components/markets/Sparkline', () => ({
  Sparkline: ({ label }: { label: string }) => <div data-testid="sparkline">{label}</div>,
}));

// Mock skeleton
vi.mock('@/components/shared/Skeleton', () => ({
  WinRateCardSkeleton: () => <div data-testid="skeleton">Loading...</div>,
}));

import { api } from '@/lib/api';

const mockGetStats = api.getSignalStats as ReturnType<typeof vi.fn>;
const mockGetTrend = api.getAccuracyTrend as ReturnType<typeof vi.fn>;

function makeStats(overrides: Partial<SignalStats> = {}): SignalStats {
  return {
    total_signals: 50,
    hit_target: 30,
    hit_stop: 15,
    expired: 5,
    pending: 0,
    win_rate: 66.7,
    avg_return_pct: 2.35,
    last_updated: '2026-03-20T10:30:00Z',
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('WinRateCard', () => {
  it('shows skeleton while loading', () => {
    // Never resolve to keep loading
    mockGetStats.mockReturnValue(new Promise(() => {}));
    mockGetTrend.mockReturnValue(new Promise(() => {}));
    render(<WinRateCard />);
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('returns null when total_signals is 0', async () => {
    mockGetStats.mockResolvedValue(makeStats({ total_signals: 0 }));
    mockGetTrend.mockResolvedValue([]);
    const { container } = render(<WinRateCard />);
    await waitFor(() => {
      expect(container.innerHTML).toBe('');
    });
  });

  it('shows win rate percentage', async () => {
    mockGetStats.mockResolvedValue(makeStats({ win_rate: 66.7 }));
    mockGetTrend.mockResolvedValue([]);
    render(<WinRateCard />);
    await waitFor(() => {
      expect(screen.getByText('66.7%')).toBeInTheDocument();
    });
  });

  it('shows average return percentage', async () => {
    mockGetStats.mockResolvedValue(makeStats({ avg_return_pct: 2.35 }));
    mockGetTrend.mockResolvedValue([]);
    render(<WinRateCard />);
    await waitFor(() => {
      expect(screen.getByText('+2.35%')).toBeInTheDocument();
    });
  });

  it('shows negative avg return with no + prefix', async () => {
    mockGetStats.mockResolvedValue(makeStats({ avg_return_pct: -1.5 }));
    mockGetTrend.mockResolvedValue([]);
    render(<WinRateCard />);
    await waitFor(() => {
      expect(screen.getByText('-1.50%')).toBeInTheDocument();
    });
  });

  it('shows total signals with link to history', async () => {
    mockGetStats.mockResolvedValue(makeStats({ total_signals: 50 }));
    mockGetTrend.mockResolvedValue([]);
    render(<WinRateCard />);
    await waitFor(() => {
      const link = screen.getByText('50 signals →');
      expect(link).toBeInTheDocument();
      expect(link.closest('a')).toHaveAttribute('href', '/history');
    });
  });

  it('renders sparkline when trend has 2+ data points', async () => {
    mockGetStats.mockResolvedValue(makeStats());
    mockGetTrend.mockResolvedValue({ data: [
      { week: '1', start_date: '2026-03-01', total: 10, hit_target: 7, win_rate: 70 },
      { week: '2', start_date: '2026-03-08', total: 10, hit_target: 6, win_rate: 60 },
    ]});
    render(<WinRateCard />);
    await waitFor(() => {
      expect(screen.getByTestId('sparkline')).toBeInTheDocument();
    });
  });

  it('does not render sparkline if trend has fewer than 2 points', async () => {
    mockGetStats.mockResolvedValue(makeStats());
    mockGetTrend.mockResolvedValue({ data: [
      { week: '1', start_date: '2026-03-01', total: 10, hit_target: 7, win_rate: 70 },
    ]});
    render(<WinRateCard />);
    await waitFor(() => {
      expect(screen.getByText('66.7%')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('sparkline')).not.toBeInTheDocument();
  });

  it('returns null on API error', async () => {
    mockGetStats.mockRejectedValue(new Error('fail'));
    mockGetTrend.mockResolvedValue([]);
    const { container } = render(<WinRateCard />);
    await waitFor(() => {
      // After error, it should show nothing (total_signals would be 0 in stats=null case)
      // Actually with error, stats is null, so it returns null
      expect(container.querySelector('[class*="bg-bg-card"]')).toBeNull();
    });
  });
});
