import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PipCalculator } from '@/components/signals/PipCalculator';
import type { Signal } from '@/lib/types';

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'test-1',
    symbol: 'EUR/USD',
    market_type: 'forex',
    signal_type: 'BUY',
    confidence: 75,
    current_price: '1.0850',
    target_price: '1.0950',
    stop_loss: '1.0800',
    timeframe: '1-2 weeks',
    ai_reasoning: 'Test reasoning',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: new Date().toISOString(),
    expires_at: null,
    ...overrides,
  } as Signal;
}

describe('PipCalculator', () => {
  it('renders for forex signals', () => {
    render(<PipCalculator signal={makeSignal()} />);
    expect(screen.getByText('Pip Calculator')).toBeInTheDocument();
    expect(screen.getByText('💱')).toBeInTheDocument();
  });

  it('shows pip distances', () => {
    render(<PipCalculator signal={makeSignal()} />);
    // Target = (1.0950 - 1.0850) / 0.0001 = 100 pips
    expect(screen.getByText('100.0 pips')).toBeInTheDocument();
    // Stop = (1.0850 - 1.0800) / 0.0001 = 50 pips
    expect(screen.getByText('50.0 pips')).toBeInTheDocument();
  });

  it('handles JPY pairs with 2-digit pip size', () => {
    render(<PipCalculator signal={makeSignal({
      symbol: 'GBP/JPY',
      current_price: '187.500',
      target_price: '188.500',
      stop_loss: '187.000',
    })} />);
    // Target = (188.5 - 187.5) / 0.01 = 100 pips
    expect(screen.getByText('100.0 pips')).toBeInTheDocument();
  });

  it('shows lot size buttons', () => {
    render(<PipCalculator signal={makeSignal()} />);
    expect(screen.getByText('0.01')).toBeInTheDocument();
    expect(screen.getByText('0.1')).toBeInTheDocument();
    expect(screen.getByText('0.5')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('updates pip value when lot size changes', () => {
    render(<PipCalculator signal={makeSignal()} />);
    // Default lot size is 0.1 → pip value = 0.1 * 10 = $1/pip
    // Click 1.0 lot
    fireEvent.click(screen.getByText('1'));
    // Now pip value should be 10/pip, potential profit = 100 * 10 = $1000
    expect(screen.getByText('$1000.00')).toBeInTheDocument();
  });

  it('shows R:R ratio', () => {
    render(<PipCalculator signal={makeSignal()} />);
    // 100 target pips / 50 stop pips = 1:2.0
    expect(screen.getByText(/R:R = 1:2\.0/)).toBeInTheDocument();
  });

  it('returns null for invalid prices', () => {
    const { container } = render(<PipCalculator signal={makeSignal({
      current_price: '0',
      target_price: '0',
      stop_loss: '0',
    })} />);
    expect(container.innerHTML).toBe('');
  });
});
