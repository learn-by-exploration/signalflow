import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AccuracyChart } from '@/components/signals/AccuracyChart';

vi.mock('@/lib/api', () => ({
  api: {
    getAccuracyTrend: vi.fn(),
  },
}));

// Mock Recharts to avoid canvas/SVG issues in JSDOM
vi.mock('recharts', () => ({
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  ReferenceLine: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { api } from '@/lib/api';

beforeEach(() => {
  vi.mocked(api.getAccuracyTrend).mockReset();
});

describe('AccuracyChart', () => {
  it('shows loading state initially', () => {
    vi.mocked(api.getAccuracyTrend).mockReturnValue(new Promise(() => {}));
    render(<AccuracyChart />);
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('shows Accuracy Trend heading', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue([
      { week: 'W1', start_date: '2025-01-01', total: 10, hit_target: 6, win_rate: 60 },
    ]);
    render(<AccuracyChart />);
    await waitFor(() => {
      expect(screen.getByText(/Accuracy Trend/)).toBeInTheDocument();
    });
  });

  it('renders chart with data', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue([
      { week: 'W1', start_date: '2025-01-01', total: 10, hit_target: 6, win_rate: 60 },
      { week: 'W2', start_date: '2025-01-08', total: 12, hit_target: 8, win_rate: 67 },
    ]);
    render(<AccuracyChart />);
    await waitFor(() => {
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });

  it('shows error message on API failure', async () => {
    vi.mocked(api.getAccuracyTrend).mockRejectedValue(new Error('fail'));
    render(<AccuracyChart />);
    await waitFor(() => {
      expect(screen.getByText('Could not load trend data.')).toBeInTheDocument();
    });
  });

  it('shows empty state when no data', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue([]);
    render(<AccuracyChart />);
    await waitFor(() => {
      expect(screen.getByText(/Not enough resolved signals/)).toBeInTheDocument();
    });
  });

  it('handles { data: [...] } response format', async () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue({
      data: [{ week: 'W1', start_date: '2025-01-01', total: 10, hit_target: 6, win_rate: 60 }],
    });
    render(<AccuracyChart />);
    await waitFor(() => {
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });

  it('calls API with 8 weeks', () => {
    vi.mocked(api.getAccuracyTrend).mockResolvedValue([]);
    render(<AccuracyChart />);
    expect(api.getAccuracyTrend).toHaveBeenCalledWith(8);
  });
});
