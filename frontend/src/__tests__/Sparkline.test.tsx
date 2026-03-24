import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Sparkline } from '@/components/markets/Sparkline';

describe('Sparkline', () => {
  const sampleData = [100, 102, 101, 105, 103, 108, 110];

  it('renders SVG element with role="img"', () => {
    const { container } = render(<Sparkline data={sampleData} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute('role', 'img');
  });

  it('has default aria-label with trend description', () => {
    const { container } = render(<Sparkline data={sampleData} positive={true} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('aria-label', expect.stringContaining('trending upward'));
  });

  it('uses custom label when provided', () => {
    const { container } = render(
      <Sparkline data={sampleData} label="BTC price over 7 days" />
    );
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('aria-label', 'BTC price over 7 days');
  });

  it('renders polyline for data', () => {
    const { container } = render(<Sparkline data={sampleData} />);
    expect(container.querySelector('polyline')).toBeInTheDocument();
  });

  it('renders target line when target is provided', () => {
    const { container } = render(
      <Sparkline data={sampleData} target={112} />
    );
    const lines = container.querySelectorAll('line');
    expect(lines.length).toBeGreaterThanOrEqual(1);
  });

  it('renders stop-loss line when provided', () => {
    const { container } = render(
      <Sparkline data={sampleData} stopLoss={98} />
    );
    const lines = container.querySelectorAll('line');
    expect(lines.length).toBeGreaterThanOrEqual(1);
  });

  it('returns null for less than 2 data points', () => {
    const { container } = render(<Sparkline data={[100]} />);
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });

  it('uses green stroke for positive trend', () => {
    const { container } = render(<Sparkline data={sampleData} positive={true} />);
    const polyline = container.querySelector('polyline');
    expect(polyline).toHaveAttribute('stroke', '#00E676');
  });

  it('uses red stroke for negative trend', () => {
    const { container } = render(<Sparkline data={sampleData} positive={false} />);
    const polyline = container.querySelector('polyline');
    expect(polyline).toHaveAttribute('stroke', '#FF5252');
  });
});
