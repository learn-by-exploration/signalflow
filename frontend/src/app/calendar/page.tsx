'use client';

import { useState, useMemo } from 'react';

interface EconomicEvent {
  id: string;
  date: string;
  time: string;
  country: string;
  flag: string;
  event: string;
  impact: 'high' | 'medium' | 'low';
  previous?: string;
  forecast?: string;
  actual?: string;
  markets: string[];
}

// Static calendar of key recurring events (will be replaced by live API in future)
const UPCOMING_EVENTS: EconomicEvent[] = [
  {
    id: '1',
    date: getNextWeekday(1),
    time: '14:00',
    country: 'IN',
    flag: '🇮🇳',
    event: 'RBI Monetary Policy Decision',
    impact: 'high',
    markets: ['stock', 'forex'],
    previous: '6.50%',
    forecast: '6.50%',
  },
  {
    id: '2',
    date: getNextWeekday(2),
    time: '18:30',
    country: 'US',
    flag: '🇺🇸',
    event: 'US CPI (Monthly)',
    impact: 'high',
    markets: ['forex', 'crypto'],
    previous: '0.4%',
    forecast: '0.3%',
  },
  {
    id: '3',
    date: getNextWeekday(3),
    time: '20:00',
    country: 'US',
    flag: '🇺🇸',
    event: 'FOMC Interest Rate Decision',
    impact: 'high',
    markets: ['forex', 'crypto', 'stock'],
    previous: '5.50%',
    forecast: '5.50%',
  },
  {
    id: '4',
    date: getNextWeekday(3),
    time: '14:30',
    country: 'US',
    flag: '🇺🇸',
    event: 'US Retail Sales',
    impact: 'medium',
    markets: ['forex'],
    previous: '0.6%',
    forecast: '0.4%',
  },
  {
    id: '5',
    date: getNextWeekday(4),
    time: '15:30',
    country: 'EU',
    flag: '🇪🇺',
    event: 'ECB Interest Rate Decision',
    impact: 'high',
    markets: ['forex'],
    previous: '4.50%',
    forecast: '4.50%',
  },
  {
    id: '6',
    date: getNextWeekday(5),
    time: '18:30',
    country: 'US',
    flag: '🇺🇸',
    event: 'Non-Farm Payrolls',
    impact: 'high',
    markets: ['forex', 'crypto', 'stock'],
    previous: '275K',
    forecast: '200K',
  },
  {
    id: '7',
    date: getNextWeekday(1),
    time: '11:30',
    country: 'IN',
    flag: '🇮🇳',
    event: 'India GDP (Quarterly)',
    impact: 'high',
    markets: ['stock'],
    previous: '8.4%',
    forecast: '7.0%',
  },
  {
    id: '8',
    date: getNextWeekday(2),
    time: '07:30',
    country: 'JP',
    flag: '🇯🇵',
    event: 'BoJ Interest Rate Decision',
    impact: 'medium',
    markets: ['forex'],
    previous: '0.10%',
    forecast: '0.10%',
  },
  {
    id: '9',
    date: getNextWeekday(4),
    time: '14:30',
    country: 'US',
    flag: '🇺🇸',
    event: 'US Jobless Claims (Weekly)',
    impact: 'low',
    markets: ['forex'],
    previous: '210K',
    forecast: '215K',
  },
  {
    id: '10',
    date: getNextWeekday(5),
    time: '15:00',
    country: 'EU',
    flag: '🇪🇺',
    event: 'EU PMI Manufacturing',
    impact: 'medium',
    markets: ['forex'],
    previous: '46.5',
    forecast: '47.0',
  },
];

function getNextWeekday(daysFromNow: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysFromNow);
  return d.toISOString().split('T')[0];
}

type MarketFilter = 'all' | 'stock' | 'crypto' | 'forex';
type ImpactFilter = 'all' | 'high' | 'medium' | 'low';

const IMPACT_CONFIG = {
  high: { label: 'High', color: 'text-signal-sell', bg: 'bg-signal-sell/15', dots: '●●●' },
  medium: { label: 'Medium', color: 'text-signal-hold', bg: 'bg-signal-hold/15', dots: '●●○' },
  low: { label: 'Low', color: 'text-text-muted', bg: 'bg-bg-secondary', dots: '●○○' },
};

export default function EconomicCalendarPage() {
  const [marketFilter, setMarketFilter] = useState<MarketFilter>('all');
  const [impactFilter, setImpactFilter] = useState<ImpactFilter>('all');

  const filtered = useMemo(() => {
    return UPCOMING_EVENTS
      .filter((e) => marketFilter === 'all' || e.markets.includes(marketFilter))
      .filter((e) => impactFilter === 'all' || e.impact === impactFilter)
      .sort((a, b) => {
        const dateA = `${a.date}T${a.time}`;
        const dateB = `${b.date}T${b.time}`;
        return dateA.localeCompare(dateB);
      });
  }, [marketFilter, impactFilter]);

  // Group by date
  const grouped = useMemo(() => {
    const groups: Record<string, EconomicEvent[]> = {};
    for (const event of filtered) {
      if (!groups[event.date]) groups[event.date] = [];
      groups[event.date].push(event);
    }
    return groups;
  }, [filtered]);

  function formatDateLabel(dateStr: string): string {
    const d = new Date(dateStr + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = Math.floor((d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    const dayName = d.toLocaleDateString('en-US', { weekday: 'long' });
    const dateLabel = d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });

    if (diff === 0) return `Today — ${dateLabel}`;
    if (diff === 1) return `Tomorrow — ${dateLabel}`;
    return `${dayName} — ${dateLabel}`;
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-display font-semibold">Economic Calendar</h1>
          <p className="text-sm text-text-secondary">
            Key economic events that move markets. High-impact events can cause significant
            volatility — plan your trades around them.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Market:</span>
            {(['all', 'stock', 'crypto', 'forex'] as MarketFilter[]).map((m) => (
              <button
                key={m}
                onClick={() => setMarketFilter(m)}
                className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                  marketFilter === m
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-muted hover:border-border-hover'
                }`}
              >
                {m === 'all' ? 'All' : m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">Impact:</span>
            {(['all', 'high', 'medium', 'low'] as ImpactFilter[]).map((i) => (
              <button
                key={i}
                onClick={() => setImpactFilter(i)}
                className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                  impactFilter === i
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-muted hover:border-border-hover'
                }`}
              >
                {i === 'all' ? 'All' : i.charAt(0).toUpperCase() + i.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Events by date */}
        {Object.entries(grouped).length > 0 ? (
          <div className="space-y-6">
            {Object.entries(grouped).map(([date, events]) => (
              <section key={date}>
                <h2 className="text-sm font-display font-semibold text-text-secondary mb-3">
                  {formatDateLabel(date)}
                </h2>
                <div className="space-y-2">
                  {events.map((event) => {
                    const impact = IMPACT_CONFIG[event.impact];
                    return (
                      <div
                        key={event.id}
                        className="bg-bg-card border border-border-default rounded-xl p-4 hover:border-border-hover transition-colors"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3">
                            <span className="text-lg">{event.flag}</span>
                            <div>
                              <p className="text-sm font-medium">{event.event}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-text-muted font-mono">{event.time} IST</span>
                                <span className={`text-xs px-1.5 py-0.5 rounded ${impact.bg} ${impact.color}`}>
                                  {impact.dots} {impact.label}
                                </span>
                                {event.markets.map((m) => (
                                  <span key={m} className="text-xs text-text-muted bg-bg-secondary px-1.5 py-0.5 rounded">
                                    {m}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                          {/* Data columns */}
                          <div className="flex items-center gap-4 text-right shrink-0">
                            {event.previous && (
                              <div>
                                <p className="text-xs text-text-muted">Previous</p>
                                <p className="text-xs font-mono">{event.previous}</p>
                              </div>
                            )}
                            {event.forecast && (
                              <div>
                                <p className="text-xs text-text-muted">Forecast</p>
                                <p className="text-xs font-mono text-accent-purple">{event.forecast}</p>
                              </div>
                            )}
                            {event.actual && (
                              <div>
                                <p className="text-xs text-text-muted">Actual</p>
                                <p className="text-xs font-mono font-bold">{event.actual}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <div className="bg-bg-card border border-border-default rounded-xl p-8 text-center space-y-3">
            <p className="text-3xl">📅</p>
            <p className="text-text-secondary text-sm">No events match your filters.</p>
            <p className="text-text-muted text-xs">
              Try selecting &ldquo;All&rdquo; for market and impact to see all upcoming events.
            </p>
          </div>
        )}

        {/* Info note */}
        <div className="bg-bg-secondary/30 border border-border-default rounded-xl p-4 text-center">
          <p className="text-xs text-text-muted max-w-xl mx-auto leading-relaxed">
            💡 <strong className="text-text-secondary">Trading tip:</strong> Avoid entering new
            positions 30 minutes before high-impact events. Wait for the initial volatility to
            settle before acting on signals. Times shown in IST.
          </p>
        </div>
      </div>
    </main>
  );
}
