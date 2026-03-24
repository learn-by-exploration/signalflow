import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrailingStopSuggestion } from '@/components/signals/TrailingStopSuggestion';
import type { Signal } from '@/lib/types';

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'test-1',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 85,
    current_price: '1700',
    target_price: '1800',
    stop_loss: '1650',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Test',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: new Date().toISOString(),
    expires_at: null,
    ...overrides,
  } as Signal;
}

describe('TrailingStopSuggestion', () => {
  it('renders with title', () => {
    render(<TrailingStopSuggestion signal={makeSignal()} />);
    expect(screen.getByText('Trailing Stop Suggestion')).toBeInTheDocument();
    expect(screen.getByText('📏')).toBeInTheDocument();
  });

  it('shows all four milestone levels', () => {
    render(<TrailingStopSuggestion signal={makeSignal()} />);
    expect(screen.getByText(/Entry/)).toBeInTheDocument();
    expect(screen.getByText(/25% to target/)).toBeInTheDocument();
    expect(screen.getByText(/50% to target/)).toBeInTheDocument();
    expect(screen.getByText(/75% to target/)).toBeInTheDocument();
  });

  it('shows 0% progress at entry price', () => {
    render(<TrailingStopSuggestion signal={makeSignal()} livePrice={1700} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('shows progress when price moved toward target', () => {
    // Entry 1700, target 1800, range 100. Price at 1750 → 50% progress
    render(<TrailingStopSuggestion signal={makeSignal()} livePrice={1750} />);
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('caps progress at 100%', () => {
    render(<TrailingStopSuggestion signal={makeSignal()} livePrice={1900} />);
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });

  it('handles SELL signals', () => {
    render(<TrailingStopSuggestion signal={makeSignal({
      signal_type: 'SELL',
      current_price: '1700',
      target_price: '1600',
      stop_loss: '1750',
    })} livePrice={1650} />);
    // Entry 1700, target 1600, range 100. Price at 1650 → 50%
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('includes trailing stop advice text', () => {
    render(<TrailingStopSuggestion signal={makeSignal()} />);
    expect(screen.getByText(/Move your stop-loss up/)).toBeInTheDocument();
  });

  it('uses forex decimal places for forex pairs', () => {
    render(<TrailingStopSuggestion signal={makeSignal({
      market_type: 'forex',
      symbol: 'EUR/USD',
      current_price: '1.0850',
      target_price: '1.0950',
      stop_loss: '1.0800',
    })} />);
    // Should show 4 decimal places for forex
    expect(screen.getByText(/Stop: 1\.0800/)).toBeInTheDocument();
  });
});
