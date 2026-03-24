import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EventTimeline } from '@/components/signals/EventTimeline';
import type { EventEntity, CausalLink } from '@/lib/types';

const mockEvents: EventEntity[] = [
  {
    id: 'evt-1',
    title: 'RBI keeps repo rate unchanged',
    description: 'Central bank maintained status quo at 6.5%',
    event_category: 'macro_policy',
    affected_symbols: ['HDFCBANK.NS', 'SBIN.NS'],
    affected_sectors: ['banking'],
    impact_magnitude: 4,
    sentiment_direction: 'bullish',
    confidence: 85,
    article_count: 3,
    occurred_at: '2026-03-20T10:00:00Z',
    expires_at: '2026-05-01T10:00:00Z',
    created_at: '2026-03-20T10:05:00Z',
  },
  {
    id: 'evt-2',
    title: 'Bitcoin ETF sees record inflows',
    description: 'Institutional investors pile into spot BTC ETFs',
    event_category: 'sector',
    affected_symbols: ['BTCUSDT', 'ETHUSDT'],
    affected_sectors: ['crypto_major'],
    impact_magnitude: 3,
    sentiment_direction: 'bullish',
    confidence: 70,
    article_count: 5,
    occurred_at: '2026-03-19T14:00:00Z',
    expires_at: '2026-04-02T14:00:00Z',
    created_at: '2026-03-19T14:05:00Z',
  },
  {
    id: 'evt-3',
    title: 'Fed signals potential rate cuts',
    description: null,
    event_category: 'macro_policy',
    affected_symbols: ['EUR/USD', 'GBP/USD'],
    affected_sectors: ['forex_major'],
    impact_magnitude: 5,
    sentiment_direction: 'bearish',
    confidence: 90,
    article_count: 8,
    occurred_at: '2026-03-18T18:00:00Z',
    expires_at: '2026-04-29T18:00:00Z',
    created_at: '2026-03-18T18:05:00Z',
  },
];

const mockLinks: CausalLink[] = [
  {
    id: 'link-1',
    source_event_id: 'evt-1',
    target_event_id: 'evt-2',
    relationship_type: 'causes',
    propagation_delay: '2-3 days',
    impact_decay: 0.8,
    confidence: 70,
    reasoning: 'Rate stability encourages risk-on behavior',
  },
];

describe('EventTimeline', () => {
  it('renders empty state when no events', () => {
    render(<EventTimeline events={[]} />);
    expect(screen.getByText('No events tracked yet.')).toBeInTheDocument();
  });

  it('renders event titles', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText(/RBI keeps repo rate unchanged/)).toBeInTheDocument();
    expect(screen.getByText(/Bitcoin ETF sees record inflows/)).toBeInTheDocument();
    expect(screen.getByText(/Fed signals potential rate cuts/)).toBeInTheDocument();
  });

  it('renders event descriptions when not compact', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText('Central bank maintained status quo at 6.5%')).toBeInTheDocument();
    expect(screen.getByText('Institutional investors pile into spot BTC ETFs')).toBeInTheDocument();
  });

  it('hides descriptions in compact mode', () => {
    render(<EventTimeline events={mockEvents} compact />);
    expect(screen.queryByText('Central bank maintained status quo at 6.5%')).not.toBeInTheDocument();
  });

  it('shows impact magnitude', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText('Impact 4/5')).toBeInTheDocument();
    expect(screen.getByText('Impact 3/5')).toBeInTheDocument();
    expect(screen.getByText('Impact 5/5')).toBeInTheDocument();
  });

  it('shows confidence percentages', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText('Confidence 85%')).toBeInTheDocument();
    expect(screen.getByText('Confidence 70%')).toBeInTheDocument();
    expect(screen.getByText('Confidence 90%')).toBeInTheDocument();
  });

  it('shows article count for multi-article events', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText('3 articles')).toBeInTheDocument();
    expect(screen.getByText('5 articles')).toBeInTheDocument();
    expect(screen.getByText('8 articles')).toBeInTheDocument();
  });

  it('shows category badges', () => {
    render(<EventTimeline events={mockEvents} />);
    const macros = screen.getAllByText('Macro');
    expect(macros.length).toBe(2); // Two macro_policy events
    expect(screen.getByText('Sector')).toBeInTheDocument();
  });

  it('shows affected symbols', () => {
    render(<EventTimeline events={mockEvents} />);
    expect(screen.getByText('HDFCBANK.NS')).toBeInTheDocument();
    expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
    expect(screen.getByText('EUR/USD')).toBeInTheDocument();
  });

  it('renders causal links when provided', () => {
    render(<EventTimeline events={mockEvents} links={mockLinks} />);
    expect(screen.getByText('→ causes')).toBeInTheDocument();
    expect(screen.getByText('(2-3 days)')).toBeInTheDocument();
  });

  it('hides causal links in compact mode', () => {
    render(<EventTimeline events={mockEvents} links={mockLinks} compact />);
    expect(screen.queryByText('→ causes')).not.toBeInTheDocument();
  });
});
