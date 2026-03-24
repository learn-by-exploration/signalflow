import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BenchmarkComparison } from '@/components/charts/BenchmarkComparison';

// Mock recharts
vi.mock('recharts', () => {
  const MockResponsiveContainer = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockLineChart = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  );
  const MockLine = ({ name }: { name: string }) => (
    <div data-testid={`line-${name}`}>{name}</div>
  );
  const MockXAxis = () => <div data-testid="x-axis" />;
  const MockYAxis = () => <div data-testid="y-axis" />;
  const MockTooltip = () => <div data-testid="tooltip" />;
  const MockLegend = () => <div data-testid="legend" />;

  return {
    ResponsiveContainer: MockResponsiveContainer,
    LineChart: MockLineChart,
    Line: MockLine,
    XAxis: MockXAxis,
    YAxis: MockYAxis,
    Tooltip: MockTooltip,
    Legend: MockLegend,
  };
});

describe('BenchmarkComparison', () => {
  const baseProps = {
    strategyReturns: 15.5,
    benchmarkName: 'Nifty 50',
    benchmarkReturns: 8.2,
    totalSignals: 10,
    startDate: '2026-01-01',
    endDate: '2026-03-31',
  };

  it('renders title with benchmark name', () => {
    render(<BenchmarkComparison {...baseProps} />);
    expect(screen.getByText(/vs Nifty 50/)).toBeInTheDocument();
  });

  it('shows strategy returns', () => {
    render(<BenchmarkComparison {...baseProps} />);
    expect(screen.getByText('+15.50%')).toBeInTheDocument();
  });

  it('shows benchmark returns', () => {
    render(<BenchmarkComparison {...baseProps} />);
    expect(screen.getByText('+8.20%')).toBeInTheDocument();
  });

  it('calculates and shows alpha', () => {
    render(<BenchmarkComparison {...baseProps} />);
    // Alpha = 15.5 - 8.2 = 7.3
    expect(screen.getByText('+7.30%')).toBeInTheDocument();
    expect(screen.getByText('+7.30% alpha')).toBeInTheDocument();
  });

  it('shows negative alpha when underperforming', () => {
    render(<BenchmarkComparison {...baseProps} strategyReturns={5.0} benchmarkReturns={10.0} />);
    expect(screen.getByText('-5.00% alpha')).toBeInTheDocument();
  });

  it('renders chart container', () => {
    render(<BenchmarkComparison {...baseProps} />);
    expect(screen.getByTestId('benchmark-chart')).toBeInTheDocument();
  });

  it('renders both chart lines', () => {
    render(<BenchmarkComparison {...baseProps} />);
    expect(screen.getByTestId('line-Strategy')).toBeInTheDocument();
    expect(screen.getByTestId('line-Nifty 50')).toBeInTheDocument();
  });
});
