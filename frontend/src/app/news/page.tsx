'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { NewsEvent, EventEntity, EventCalendar, MarketType } from '@/lib/types';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { EventTimeline } from '@/components/signals/EventTimeline';
import { MARKET_LABELS } from '@/lib/constants';

const MARKET_FILTERS: { value: MarketType | 'all'; label: string }[] = [
  { value: 'all', label: 'All Markets' },
  { value: 'stock', label: 'Stocks' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'forex', label: 'Forex' },
];

const SENTIMENT_CHIPS: { value: string; label: string; color: string }[] = [
  { value: 'all', label: 'All', color: 'text-text-secondary' },
  { value: 'bullish', label: '📈 Bullish', color: 'text-signal-buy' },
  { value: 'bearish', label: '📉 Bearish', color: 'text-signal-sell' },
  { value: 'neutral', label: '➡️ Neutral', color: 'text-text-muted' },
];

interface NewsListResponse {
  data: NewsEvent[];
  meta: { count: number; total: number };
}

interface EventListResponse {
  data: EventEntity[];
  meta: { count: number };
}

interface CalendarResponse {
  data: EventCalendar[];
  meta: { count: number };
}

type TabKey = 'headlines' | 'events' | 'calendar';

export default function NewsPage() {
  const [tab, setTab] = useState<TabKey>('headlines');
  const [marketFilter, setMarketFilter] = useState<MarketType | 'all'>('all');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  // Data
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [events, setEvents] = useState<EventEntity[]>([]);
  const [calendar, setCalendar] = useState<EventCalendar[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === 'headlines') {
        const params = new URLSearchParams();
        if (marketFilter !== 'all') params.set('market', marketFilter);
        if (sentimentFilter !== 'all') params.set('sentiment', sentimentFilter);
        params.set('limit', '50');
        const res = (await api.getNews(params)) as NewsListResponse;
        setNews(res.data ?? []);
      } else if (tab === 'events') {
        const params = new URLSearchParams();
        if (marketFilter !== 'all') params.set('market', marketFilter);
        params.set('limit', '30');
        const res = (await api.getEvents(params)) as EventListResponse;
        setEvents(res.data ?? []);
      } else if (tab === 'calendar') {
        const params = new URLSearchParams();
        params.set('days', '30');
        const res = (await api.getEventCalendar(params)) as CalendarResponse;
        setCalendar(res.data ?? []);
      }
    } catch {
      // Silently handle — empty state shown
    } finally {
      setLoading(false);
    }
  }, [tab, marketFilter, sentimentFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-display font-bold text-text-primary">News Intelligence</h1>
          <p className="text-sm text-text-muted mt-1">
            Real-time news tracking, event extraction, and causal chain analysis across all markets.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-border-default">
          {(['headlines', 'events', 'calendar'] as TabKey[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-display capitalize transition-colors border-b-2 -mb-px ${
                tab === t
                  ? 'text-accent-purple border-accent-purple'
                  : 'text-text-muted border-transparent hover:text-text-secondary'
              }`}
            >
              {t === 'headlines' ? '📰 Headlines' : t === 'events' ? '🔗 Events' : '📅 Calendar'}
            </button>
          ))}
        </div>

        {/* Filters */}
        {tab !== 'calendar' && (
          <div className="flex flex-wrap items-center gap-3">
            {/* Market filter */}
            <div className="flex items-center gap-1">
              {MARKET_FILTERS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setMarketFilter(m.value)}
                  className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                    marketFilter === m.value
                      ? 'bg-accent-purple/15 text-accent-purple'
                      : 'bg-white/[0.04] text-text-muted hover:text-text-secondary'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {/* Sentiment filter (headlines only) */}
            {tab === 'headlines' && (
              <div className="flex items-center gap-1">
                {SENTIMENT_CHIPS.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setSentimentFilter(s.value)}
                    className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                      sentimentFilter === s.value
                        ? 'bg-white/[0.08] text-text-primary'
                        : 'bg-white/[0.02] text-text-muted hover:text-text-secondary'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <>
            {/* Headlines Tab */}
            {tab === 'headlines' && (
              <div className="space-y-2">
                {news.length === 0 ? (
                  <div className="text-center py-12 text-text-muted">
                    <p className="text-3xl mb-2">📰</p>
                    <p className="text-sm">No news articles found. News will appear as markets generate signals.</p>
                  </div>
                ) : (
                  news.map((item) => (
                    <div
                      key={item.id}
                      className="bg-bg-card border border-border-default rounded-lg p-3 hover:border-border-hover transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-sm ${
                              item.sentiment_direction === 'bullish' ? 'text-signal-buy' :
                              item.sentiment_direction === 'bearish' ? 'text-signal-sell' :
                              'text-text-muted'
                            }`}>
                              {item.sentiment_direction === 'bullish' ? '📈' :
                               item.sentiment_direction === 'bearish' ? '📉' : '➡️'}
                            </span>
                            <h3 className="text-sm text-text-primary truncate">
                              {item.headline}
                            </h3>
                          </div>
                          <div className="flex items-center gap-3 text-[10px] text-text-muted">
                            {item.source && <span>{item.source}</span>}
                            <span className="font-mono">{item.symbol}</span>
                            <span>{MARKET_LABELS[item.market_type]}</span>
                            {item.event_category && (
                              <span className="px-1.5 py-0.5 rounded bg-accent-purple/10 text-accent-purple">
                                {item.event_category}
                              </span>
                            )}
                            {item.published_at && (
                              <span>{new Date(item.published_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                        {item.impact_magnitude != null && (
                          <span className="shrink-0 text-[10px] font-mono text-text-muted">
                            Impact {item.impact_magnitude}/5
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Events Tab */}
            {tab === 'events' && (
              <EventTimeline events={events} />
            )}

            {/* Calendar Tab */}
            {tab === 'calendar' && (
              <div className="space-y-2">
                {calendar.length === 0 ? (
                  <div className="text-center py-12 text-text-muted">
                    <p className="text-3xl mb-2">📅</p>
                    <p className="text-sm">No upcoming events on the calendar.</p>
                  </div>
                ) : (
                  calendar.map((item) => {
                    const scheduled = new Date(item.scheduled_at);
                    const isPast = scheduled.getTime() < Date.now();
                    return (
                      <div
                        key={item.id}
                        className={`bg-bg-card border border-border-default rounded-lg p-3 ${
                          isPast ? 'opacity-60' : ''
                        } hover:border-border-hover transition-colors`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm">{item.is_completed ? '✅' : isPast ? '⏰' : '📅'}</span>
                              <h3 className="text-sm font-display text-text-primary">{item.title}</h3>
                            </div>
                            <div className="flex items-center gap-3 text-[10px] text-text-muted">
                              <span className="px-1.5 py-0.5 rounded bg-accent-purple/10 text-accent-purple">
                                {item.event_type}
                              </span>
                              <span>{scheduled.toLocaleDateString()} {scheduled.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                              <span>Impact {item.impact_magnitude}/5</span>
                              {item.is_recurring && <span>🔄 Recurring</span>}
                            </div>
                            {item.affected_symbols.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1.5">
                                {item.affected_symbols.map((sym) => (
                                  <span key={sym} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.04] text-text-secondary">
                                    {sym}
                                  </span>
                                ))}
                              </div>
                            )}
                            {item.outcome && (
                              <p className="text-xs text-text-secondary mt-1">{item.outcome}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
