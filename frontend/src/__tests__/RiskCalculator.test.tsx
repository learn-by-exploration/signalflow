import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RiskCalculator } from '@/components/signals/RiskCalculator';
import type { Signal } from '@/lib/types';

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'sig-1',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 72,
    current_price: '1000.00',
    target_price: '1200.00',
    stop_loss: '900.00',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Test reasoning.',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: '2026-03-20T10:30:00Z',
    expires_at: null,
    ...overrides,
  };
}

describe('RiskCalculator', () => {
  it('returns null when price is zero', () => {
    const { container } = render(
      <RiskCalculator signal={makeSignal({ current_price: '0' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('returns null when target is missing', () => {
    const { container } = render(
      <RiskCalculator signal={makeSignal({ target_price: '0' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('returns null when stop_loss is missing', () => {
    const { container } = render(
      <RiskCalculator signal={makeSignal({ stop_loss: '0' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('calculates max gain correctly for BUY (default 10K)', () => {
    // BUY: price=1000, target=1200 → gain = ((1200-1000)/1000)*10000 = 2000
    render(<RiskCalculator signal={makeSignal()} />);
    expect(screen.getByText('+₹2000')).toBeInTheDocument();
  });

  it('calculates max loss correctly for BUY (default 10K)', () => {
    // BUY: price=1000, stop=900 → loss = ((1000-900)/1000)*10000 = 1000
    render(<RiskCalculator signal={makeSignal()} />);
    expect(screen.getByText('-₹1000')).toBeInTheDocument();
  });

  it('calculates risk-reward ratio for BUY', () => {
    // gain=2000, loss=1000 → R:R = 1:2.0
    render(<RiskCalculator signal={makeSignal()} />);
    expect(screen.getByText('1:2.0')).toBeInTheDocument();
  });

  it('calculates max gain correctly for SELL signal', () => {
    // SELL: price=1000, target=800 → gain = ((1000-800)/1000)*10000 = 2000
    render(
      <RiskCalculator
        signal={makeSignal({ signal_type: 'SELL', target_price: '800.00', stop_loss: '1100.00' })}
      />,
    );
    expect(screen.getByText('+₹2000')).toBeInTheDocument();
  });

  it('calculates max loss correctly for SELL signal', () => {
    // SELL: price=1000, stop=1100 → loss = ((1100-1000)/1000)*10000 = 1000
    render(
      <RiskCalculator
        signal={makeSignal({ signal_type: 'SELL', target_price: '800.00', stop_loss: '1100.00' })}
      />,
    );
    expect(screen.getByText('-₹1000')).toBeInTheDocument();
  });

  it('shows ₹ currency for stock signals', () => {
    render(<RiskCalculator signal={makeSignal({ market_type: 'stock' })} />);
    expect(screen.getByText('+₹2000')).toBeInTheDocument();
  });

  it('shows $ currency for crypto signals', () => {
    render(<RiskCalculator signal={makeSignal({ market_type: 'crypto' })} />);
    expect(screen.getByText('+$2000')).toBeInTheDocument();
  });

  it('shows no currency prefix for forex signals', () => {
    render(<RiskCalculator signal={makeSignal({ market_type: 'forex' })} />);
    expect(screen.getByText('+2000')).toBeInTheDocument();
  });

  it('shows gain/loss percentages', () => {
    // gain%  = (2000/10000)*100 = 20.0%
    // loss%  = (1000/10000)*100 = 10.0%
    render(<RiskCalculator signal={makeSignal()} />);
    expect(screen.getByText('Max Gain (20.0%)')).toBeInTheDocument();
    expect(screen.getByText('Max Loss (10.0%)')).toBeInTheDocument();
  });

  it('updates calculation when a preset amount is clicked', () => {
    render(<RiskCalculator signal={makeSignal()} />);
    // Click 25K preset → gain = ((1200-1000)/1000)*25000 = 5000
    fireEvent.click(screen.getByText('₹25K'));
    expect(screen.getByText('+₹5000')).toBeInTheDocument();
  });

  it('renders preset buttons for four amounts', () => {
    render(<RiskCalculator signal={makeSignal()} />);
    expect(screen.getByText('₹10K')).toBeInTheDocument();
    expect(screen.getByText('₹25K')).toBeInTheDocument();
    expect(screen.getByText('₹50K')).toBeInTheDocument();
    expect(screen.getByText('₹100K')).toBeInTheDocument();
  });

  it('handles STRONG_BUY same as BUY direction', () => {
    render(<RiskCalculator signal={makeSignal({ signal_type: 'STRONG_BUY' })} />);
    expect(screen.getByText('+₹2000')).toBeInTheDocument();
  });

  it('handles STRONG_SELL same as SELL direction', () => {
    render(
      <RiskCalculator
        signal={makeSignal({ signal_type: 'STRONG_SELL', target_price: '800.00', stop_loss: '1100.00' })}
      />,
    );
    expect(screen.getByText('+₹2000')).toBeInTheDocument();
  });
});
