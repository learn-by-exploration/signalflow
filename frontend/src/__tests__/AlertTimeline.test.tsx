import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AlertTimeline } from '@/components/alerts/AlertTimeline';
import { makeSignal } from './helpers';

describe('AlertTimeline', () => {
  it('shows empty state when no signals', () => {
    render(<AlertTimeline signals={[]} />);
    expect(screen.getByText('Recent Alerts')).toBeInTheDocument();
    expect(screen.getByText(/Alerts will appear here/)).toBeInTheDocument();
  });

  it('renders signals in timeline', () => {
    const signals = [
      makeSignal({ id: '1', symbol: 'RELIANCE.NS', signal_type: 'BUY', confidence: 75 }),
      makeSignal({ id: '2', symbol: 'TCS.NS', signal_type: 'SELL', confidence: 30 }),
    ];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    expect(screen.getByText('TCS')).toBeInTheDocument();
  });

  it('shows signal type', () => {
    const signals = [makeSignal({ signal_type: 'STRONG_BUY' })];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('STRONG BUY')).toBeInTheDocument();
  });

  it('shows emoji for buy signals', () => {
    const signals = [makeSignal({ signal_type: 'BUY' })];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('🟢')).toBeInTheDocument();
  });

  it('shows emoji for sell signals', () => {
    const signals = [makeSignal({ signal_type: 'SELL' })];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('🔴')).toBeInTheDocument();
  });

  it('shows emoji for hold signals', () => {
    const signals = [makeSignal({ signal_type: 'HOLD', confidence: 50 })];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('🟡')).toBeInTheDocument();
  });

  it('shows confidence percentage', () => {
    const signals = [makeSignal({ confidence: 92 })];
    render(<AlertTimeline signals={signals} />);
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('limits to 10 signals', () => {
    const signals = Array.from({ length: 15 }, (_, i) =>
      makeSignal({ id: String(i), symbol: `SYM${i}.NS` }),
    );
    render(<AlertTimeline signals={signals} />);
    // Should only show first 10
    const cards = document.querySelectorAll('.bg-bg-card');
    expect(cards.length).toBe(10);
  });
});
