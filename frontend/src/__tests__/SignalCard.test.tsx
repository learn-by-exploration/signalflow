import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SignalCard } from '@/components/signals/SignalCard';
import { useMarketStore } from '@/store/marketStore';
import type { Signal } from '@/lib/types';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'sig-test',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 72,
    current_price: '1678.90',
    target_price: '1780.00',
    stop_loss: '1630.00',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Credit growth is accelerating.',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: new Date().toISOString(),
    expires_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  useMarketStore.setState({
    stocks: [],
    crypto: [],
    forex: [],
    isLoading: false,
    lastUpdated: null,
    wsStatus: 'disconnected',
    fetchError: null,
  });
});

describe('SignalCard', () => {
  it('renders symbol name in collapsed state', () => {
    render(<SignalCard signal={makeSignal()} />);
    expect(screen.getByText('HDFCBANK')).toBeInTheDocument();
  });

  it('renders signal badge with confidence', () => {
    render(<SignalCard signal={makeSignal()} />);
    expect(screen.getByText(/BULLISH · 72%/)).toBeInTheDocument();
  });

  it('renders price and timeframe', () => {
    render(<SignalCard signal={makeSignal()} />);
    expect(screen.getByText('2-4 weeks')).toBeInTheDocument();
  });

  it('starts collapsed (aria-expanded=false)', () => {
    render(<SignalCard signal={makeSignal()} />);
    const card = screen.getByRole('button');
    expect(card).toHaveAttribute('aria-expanded', 'false');
  });

  it('expands on click', () => {
    render(<SignalCard signal={makeSignal()} />);
    const card = screen.getByRole('button');
    fireEvent.click(card);
    expect(card).toHaveAttribute('aria-expanded', 'true');
  });

  it('toggles expand on Enter key', () => {
    render(<SignalCard signal={makeSignal()} />);
    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(card).toHaveAttribute('aria-expanded', 'true');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(card).toHaveAttribute('aria-expanded', 'false');
  });

  it('toggles expand on Space key', () => {
    render(<SignalCard signal={makeSignal()} />);
    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: ' ' });
    expect(card).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows "View full analysis" link when expanded', () => {
    render(<SignalCard signal={makeSignal()} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText('View full analysis →')).toBeInTheDocument();
    expect(screen.getByText('View full analysis →').closest('a')).toHaveAttribute('href', '/signal/sig-test');
  });

  it('shows age warning for signals older than 48 hours', () => {
    const old = new Date(Date.now() - 72 * 3600000).toISOString();
    render(<SignalCard signal={makeSignal({ created_at: old })} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText(/check conditions/)).toBeInTheDocument();
  });

  it('shows stronger age warning for signals older than 5 days', () => {
    const veryOld = new Date(Date.now() - 6 * 24 * 3600000).toISOString();
    render(<SignalCard signal={makeSignal({ created_at: veryOld })} />);
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText(/verify before acting/)).toBeInTheDocument();
  });

  it('renders STRONG_BUY badge icon', () => {
    render(<SignalCard signal={makeSignal({ signal_type: 'STRONG_BUY', confidence: 90 })} />);
    expect(screen.getByText(/STRONGLY BULLISH · 90%/)).toBeInTheDocument();
  });

  it('renders SELL badge icon', () => {
    render(<SignalCard signal={makeSignal({ signal_type: 'SELL', confidence: 30 })} />);
    expect(screen.getByText(/BEARISH · 30%/)).toBeInTheDocument();
  });
});
