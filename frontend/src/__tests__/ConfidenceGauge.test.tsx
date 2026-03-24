import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceGauge } from '@/components/signals/ConfidenceGauge';

describe('ConfidenceGauge', () => {
  it('renders confidence percentage text', () => {
    render(<ConfidenceGauge confidence={92} signalType="STRONG_BUY" />);
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('has accessible aria-label with confidence and signal type', () => {
    render(<ConfidenceGauge confidence={75} signalType="BUY" />);
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', 'Confidence: 75 percent, Buy');
  });

  it('shows Strong Buy label for STRONG_BUY', () => {
    render(<ConfidenceGauge confidence={85} signalType="STRONG_BUY" />);
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', 'Confidence: 85 percent, Strong Buy');
  });

  it('shows Sell label for SELL', () => {
    render(<ConfidenceGauge confidence={30} signalType="SELL" />);
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', 'Confidence: 30 percent, Sell');
  });

  it('renders SVG with correct size', () => {
    const { container } = render(<ConfidenceGauge confidence={50} signalType="HOLD" size={72} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '72');
    expect(svg).toHaveAttribute('height', '72');
  });

  it('renders two circles (background track + progress arc)', () => {
    const { container } = render(<ConfidenceGauge confidence={60} signalType="BUY" />);
    const circles = container.querySelectorAll('circle');
    expect(circles).toHaveLength(2);
  });
});
