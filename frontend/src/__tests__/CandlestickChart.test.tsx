import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CandlestickChart } from '@/components/charts/CandlestickChart';

// Mock lightweight-charts since it needs a canvas context
vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => ({
    addCandlestickSeries: vi.fn(() => ({
      setData: vi.fn(),
      createPriceLine: vi.fn(),
    })),
    timeScale: vi.fn(() => ({ fitContent: vi.fn() })),
    applyOptions: vi.fn(),
    remove: vi.fn(),
  })),
  ColorType: { Solid: 'solid' },
}));

describe('CandlestickChart', () => {
  const sampleData = [
    { time: '2026-01-01', open: 100, high: 105, low: 98, close: 103 },
    { time: '2026-01-02', open: 103, high: 108, low: 101, close: 106 },
    { time: '2026-01-03', open: 106, high: 110, low: 104, close: 108 },
  ];

  it('renders container div', () => {
    const { container } = render(<CandlestickChart data={sampleData} />);
    expect(container.querySelector('div')).toBeInTheDocument();
  });

  it('shows message with insufficient data (< 2 points)', () => {
    render(<CandlestickChart data={[sampleData[0]]} />);
    expect(screen.getByText('Not enough data for candlestick chart')).toBeInTheDocument();
  });

  it('renders without errors when given target and stop loss', () => {
    const { container } = render(
      <CandlestickChart data={sampleData} targetPrice={112} stopLoss={96} />
    );
    expect(container.querySelector('div')).toBeInTheDocument();
  });
});
