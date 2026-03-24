import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SimpleSignalCard } from '@/components/signals/SimpleSignalCard';
import type { Signal } from '@/lib/types';

const mockSignal: Signal = {
  id: 'test-1',
  symbol: 'HDFCBANK.NS',
  market_type: 'stock',
  signal_type: 'STRONG_BUY',
  confidence: 92,
  current_price: '1678.90',
  target_price: '1780.00',
  stop_loss: '1630.00',
  timeframe: '2-4 weeks',
  ai_reasoning: 'Credit growth accelerating. NIM expansion confirmed by Q3 results.',
  technical_data: {},
  sentiment_data: null,
  is_active: true,
  created_at: '2026-03-20T10:30:00Z',
  expires_at: null,
};

describe('SimpleSignalCard', () => {
  it('renders symbol', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    expect(screen.getByText('HDFCBANK')).toBeInTheDocument();
  });

  it('renders badge with icon', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    expect(screen.getByText('▲▲')).toBeInTheDocument();
    expect(screen.getByText('STRONGLY BULLISH')).toBeInTheDocument();
  });

  it('shows confidence percentage', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('shows plain English action text', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    expect(screen.getByText('Strong bullish momentum detected')).toBeInTheDocument();
  });

  it('shows truncated AI reasoning', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    expect(screen.getByText(/Credit growth accelerating/)).toBeInTheDocument();
  });

  it('links to signal detail page', () => {
    render(<SimpleSignalCard signal={mockSignal} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/signal/test-1');
  });

  it('renders SELL signal with correct action', () => {
    const sellSignal = { ...mockSignal, signal_type: 'SELL' as const };
    render(<SimpleSignalCard signal={sellSignal} />);
    expect(screen.getByText('Bearish momentum detected')).toBeInTheDocument();
    expect(screen.getByText('▼')).toBeInTheDocument();
  });

  it('renders HOLD signal with correct action', () => {
    const holdSignal = { ...mockSignal, signal_type: 'HOLD' as const };
    render(<SimpleSignalCard signal={holdSignal} />);
    expect(screen.getByText('Wait and watch')).toBeInTheDocument();
    expect(screen.getByText('◆')).toBeInTheDocument();
  });
});
