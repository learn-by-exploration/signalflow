import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EquityCurve } from '@/components/charts/EquityCurve';

// Mock recharts to avoid canvas rendering issues in jsdom
vi.mock('recharts', () => ({
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  XAxis: () => <div data-testid="xaxis" />,
  YAxis: () => <div data-testid="yaxis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ReferenceLine: () => <div data-testid="refline" />,
}));

describe('EquityCurve', () => {
  const sampleData = [
    { date: 'Jan 1', value: 10000 },
    { date: 'Jan 8', value: 10500 },
    { date: 'Jan 15', value: 10200 },
    { date: 'Jan 22', value: 11000 },
    { date: 'Jan 29', value: 11500 },
  ];

  it('renders with label', () => {
    render(<EquityCurve data={sampleData} label="Test Curve" />);
    expect(screen.getByText('Test Curve')).toBeInTheDocument();
  });

  it('renders charts when enough data', () => {
    render(<EquityCurve data={sampleData} />);
    expect(screen.getByTestId('area-chart')).toBeInTheDocument();
  });

  it('shows message with insufficient data', () => {
    render(<EquityCurve data={[{ date: 'Jan 1', value: 100 }]} />);
    expect(screen.getByText('Not enough data for equity curve')).toBeInTheDocument();
  });

  it('defaults label to Portfolio Value', () => {
    render(<EquityCurve data={sampleData} />);
    expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
  });
});
