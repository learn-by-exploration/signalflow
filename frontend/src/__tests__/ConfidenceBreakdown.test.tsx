import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBreakdown } from '@/components/signals/ConfidenceBreakdown';

describe('ConfidenceBreakdown', () => {
  it('renders technical and sentiment bars', () => {
    render(<ConfidenceBreakdown technicalScore={85} sentimentScore={72} signalType="BUY" />);
    expect(screen.getByText('Confidence Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Technical')).toBeInTheDocument();
    expect(screen.getByText('Sentiment')).toBeInTheDocument();
  });

  it('shows correct percentage values', () => {
    render(<ConfidenceBreakdown technicalScore={85} sentimentScore={72} signalType="BUY" />);
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('72%')).toBeInTheDocument();
  });

  it('shows formula explanation', () => {
    render(<ConfidenceBreakdown technicalScore={60} sentimentScore={40} signalType="HOLD" />);
    expect(screen.getByText(/Technical × 60% \+ Sentiment × 40%/)).toBeInTheDocument();
  });

  it('renders with SELL signal type', () => {
    render(<ConfidenceBreakdown technicalScore={30} sentimentScore={20} signalType="SELL" />);
    expect(screen.getByText('30%')).toBeInTheDocument();
    expect(screen.getByText('20%')).toBeInTheDocument();
  });
});
