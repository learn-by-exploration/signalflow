import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import TrackRecordPage from '@/app/track-record/page';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  api: {
    getSignalStats: vi.fn(),
    getAccuracyTrend: vi.fn(),
    getSignalHistory: vi.fn(),
  },
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  ReferenceLine: () => null,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  Cell: () => null,
}));

const mockStats = {
  total_signals: 100,
  hit_target: 62,
  hit_stop: 25,
  expired: 10,
  pending: 3,
  win_rate: 71.3,
  avg_return_pct: 2.45,
  last_updated: '2026-03-24T10:00:00Z',
};

const mockTrend = [
  { week: 'W1', start_date: '2026-02-01', total: 20, hit_target: 14, win_rate: 70 },
  { week: 'W2', start_date: '2026-02-08', total: 18, hit_target: 13, win_rate: 72.2 },
];

const mockHistory = {
  data: [
    {
      id: '1',
      signal_id: 's1',
      outcome: 'hit_target',
      exit_price: '1800',
      return_pct: '3.50',
      resolved_at: '2026-03-20T10:00:00Z',
      created_at: '2026-03-15T10:00:00Z',
      signal: {
        id: 's1',
        symbol: 'HDFCBANK.NS',
        market_type: 'stock',
        signal_type: 'STRONG_BUY',
        confidence: 92,
        current_price: '1670',
        target_price: '1800',
        stop_loss: '1620',
        ai_reasoning: 'Test',
        technical_data: {},
        is_active: false,
        created_at: '2026-03-15T10:00:00Z',
      },
    },
  ],
  meta: { total: 1 },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('TrackRecordPage', () => {
  it('renders loading state initially', () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));

    const { container } = render(<TrackRecordPage />);
    // Should show a loading spinner while data loads
    expect(container.querySelector('[class*="animate"]')).toBeTruthy();
  });

  it('renders stats after loading', async () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockResolvedValue(mockStats);
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockResolvedValue(mockTrend);
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockResolvedValue(mockHistory);

    render(<TrackRecordPage />);
    await waitFor(() => {
      expect(screen.getByText('71.3%')).toBeInTheDocument();
    });
    expect(screen.getByText('+2.45%')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders empty state when no signals', async () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockStats,
      total_signals: 0,
    });
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [], meta: {} });

    render(<TrackRecordPage />);
    await waitFor(() => {
      expect(screen.getByText('No signals resolved yet')).toBeInTheDocument();
    });
  });

  it('renders methodology section', async () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockResolvedValue(mockStats);
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockResolvedValue(mockTrend);
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockResolvedValue(mockHistory);

    render(<TrackRecordPage />);
    await waitFor(() => {
      expect(screen.getByText('How We Track')).toBeInTheDocument();
    });
  });

  it('renders recent signals with outcomes', async () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockResolvedValue(mockStats);
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockResolvedValue(mockTrend);
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockResolvedValue(mockHistory);

    render(<TrackRecordPage />);
    await waitFor(() => {
      expect(screen.getByText('HDFCBANK')).toBeInTheDocument();
    });
    expect(screen.getByText('+3.50%')).toBeInTheDocument();
    expect(screen.getByText('🎯 Hit Target')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    (api.getSignalStats as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));
    (api.getAccuracyTrend as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));
    (api.getSignalHistory as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));

    render(<TrackRecordPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load track record data')).toBeInTheDocument();
    });
    expect(screen.getByText('Try again')).toBeInTheDocument();
  });
});
