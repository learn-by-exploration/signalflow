import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AllocationPieChart } from '@/components/charts/AllocationPieChart';
import type { PortfolioPosition } from '@/lib/types';

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock('recharts', () => {
  const MockResponsiveContainer = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockPieChart = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  );
  const MockPie = ({ children, data }: { children: React.ReactNode; data: { name: string }[] }) => (
    <div data-testid="pie">
      {data.map((d: { name: string }) => (
        <span key={d.name} data-testid={`slice-${d.name}`}>{d.name}</span>
      ))}
      {children}
    </div>
  );
  const MockCell = () => <div data-testid="cell" />;
  const MockTooltip = () => <div data-testid="tooltip" />;
  const MockLegend = () => <div data-testid="legend" />;

  return {
    ResponsiveContainer: MockResponsiveContainer,
    PieChart: MockPieChart,
    Pie: MockPie,
    Cell: MockCell,
    Tooltip: MockTooltip,
    Legend: MockLegend,
  };
});

function makePosition(overrides: Partial<PortfolioPosition> = {}): PortfolioPosition {
  return {
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    quantity: '10',
    avg_price: '1600',
    current_price: '1700',
    value: '17000',
    pnl: '1000',
    pnl_pct: 6.25,
    ...overrides,
  };
}

describe('AllocationPieChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chart with positions', () => {
    const positions = [
      makePosition({ symbol: 'HDFCBANK.NS', market_type: 'stock', value: '17000' }),
      makePosition({ symbol: 'BTCUSDT', market_type: 'crypto', value: '8000' }),
    ];
    render(<AllocationPieChart positions={positions} totalValue={25000} />);
    expect(screen.getByText('Market Allocation')).toBeInTheDocument();
    expect(screen.getByTestId('allocation-pie-chart')).toBeInTheDocument();
  });

  it('aggregates positions by market type', () => {
    const positions = [
      makePosition({ symbol: 'HDFCBANK.NS', market_type: 'stock', value: '10000' }),
      makePosition({ symbol: 'RELIANCE.NS', market_type: 'stock', value: '5000' }),
      makePosition({ symbol: 'BTCUSDT', market_type: 'crypto', value: '8000' }),
    ];
    render(<AllocationPieChart positions={positions} totalValue={23000} />);
    expect(screen.getByTestId('slice-Stocks')).toBeInTheDocument();
    expect(screen.getByTestId('slice-Crypto')).toBeInTheDocument();
  });

  it('returns null for empty positions', () => {
    const { container } = render(<AllocationPieChart positions={[]} totalValue={0} />);
    expect(container.innerHTML).toBe('');
  });

  it('returns null for zero total value', () => {
    const positions = [makePosition({ value: '10000' })];
    const { container } = render(<AllocationPieChart positions={positions} totalValue={0} />);
    expect(container.innerHTML).toBe('');
  });

  it('handles all three market types', () => {
    const positions = [
      makePosition({ symbol: 'HDFCBANK.NS', market_type: 'stock', value: '10000' }),
      makePosition({ symbol: 'BTCUSDT', market_type: 'crypto', value: '5000' }),
      makePosition({ symbol: 'EUR/USD', market_type: 'forex', value: '3000' }),
    ];
    render(<AllocationPieChart positions={positions} totalValue={18000} />);
    expect(screen.getByTestId('slice-Stocks')).toBeInTheDocument();
    expect(screen.getByTestId('slice-Crypto')).toBeInTheDocument();
    expect(screen.getByTestId('slice-Forex')).toBeInTheDocument();
  });
});
