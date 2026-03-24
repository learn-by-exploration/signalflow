'use client';

import type { EventEntity, CausalLink } from '@/lib/types';

const DIRECTION_COLORS: Record<string, string> = {
  bullish: 'text-signal-buy',
  bearish: 'text-signal-sell',
  neutral: 'text-text-muted',
  mixed: 'text-signal-hold',
};

const DIRECTION_ICONS: Record<string, string> = {
  bullish: '📈',
  bearish: '📉',
  neutral: '➡️',
  mixed: '↔️',
};

const CATEGORY_BADGES: Record<string, string> = {
  macro_policy: 'Macro',
  earnings: 'Earnings',
  regulatory: 'Regulatory',
  geopolitical: 'Geopolitical',
  sector: 'Sector',
  commodity: 'Commodity',
  technical: 'Technical',
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  causes: '→ causes',
  amplifies: '⬆ amplifies',
  dampens: '⬇ dampens',
  contradicts: '⚡ contradicts',
  precedes: '⏩ precedes',
};

interface EventTimelineProps {
  events: EventEntity[];
  links?: CausalLink[];
  compact?: boolean;
}

export function EventTimeline({ events, links = [], compact = false }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-6 text-text-muted text-sm">
        No events tracked yet.
      </div>
    );
  }

  // Sort events by occurred_at descending
  const sorted = [...events].sort((a, b) => {
    const ta = a.occurred_at ? new Date(a.occurred_at).getTime() : new Date(a.created_at).getTime();
    const tb = b.occurred_at ? new Date(b.occurred_at).getTime() : new Date(b.created_at).getTime();
    return tb - ta;
  });

  // Build quick lookup for causal links: event_id → outgoing links
  const linksBySource = new Map<string, CausalLink[]>();
  for (const link of links) {
    const existing = linksBySource.get(link.source_event_id) ?? [];
    existing.push(link);
    linksBySource.set(link.source_event_id, existing);
  }

  return (
    <div className="relative">
      {/* Vertical timeline line */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-border-default" />

      <div className="space-y-4">
        {sorted.map((event) => {
          const outgoing = linksBySource.get(event.id) ?? [];
          const dirColor = DIRECTION_COLORS[event.sentiment_direction] ?? 'text-text-muted';
          const dirIcon = DIRECTION_ICONS[event.sentiment_direction] ?? '➡️';
          const categoryLabel = CATEGORY_BADGES[event.event_category] ?? event.event_category;

          return (
            <div key={event.id} className="relative pl-8">
              {/* Timeline dot */}
              <div className={`absolute left-1.5 top-2 w-3 h-3 rounded-full border-2 border-bg-secondary ${
                event.sentiment_direction === 'bullish' ? 'bg-signal-buy' :
                event.sentiment_direction === 'bearish' ? 'bg-signal-sell' :
                'bg-text-muted'
              }`} />

              <div className="bg-bg-card border border-border-default rounded-lg p-3 hover:border-border-hover transition-colors">
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="text-sm font-display font-medium text-text-primary leading-snug">
                    {dirIcon} {event.title}
                  </h4>
                  <span className="shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-purple/10 text-accent-purple">
                    {categoryLabel}
                  </span>
                </div>

                {/* Description */}
                {!compact && event.description && (
                  <p className="text-xs text-text-secondary mb-2 leading-relaxed">
                    {event.description}
                  </p>
                )}

                {/* Meta row */}
                <div className="flex items-center gap-3 text-[10px] text-text-muted">
                  <span className={dirColor}>
                    Impact {event.impact_magnitude}/5
                  </span>
                  <span>Confidence {event.confidence}%</span>
                  {event.article_count > 1 && (
                    <span>{event.article_count} articles</span>
                  )}
                  {event.occurred_at && (
                    <span>{new Date(event.occurred_at).toLocaleDateString()}</span>
                  )}
                </div>

                {/* Affected symbols */}
                {!compact && event.affected_symbols.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {event.affected_symbols.map((sym) => (
                      <span key={sym} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.04] text-text-secondary">
                        {sym}
                      </span>
                    ))}
                  </div>
                )}

                {/* Outgoing causal links */}
                {!compact && outgoing.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-border-default space-y-1">
                    {outgoing.map((link) => {
                      const targetEvent = events.find((e) => e.id === link.target_event_id);
                      const relLabel = RELATIONSHIP_LABELS[link.relationship_type] ?? link.relationship_type;
                      return (
                        <div key={link.id} className="flex items-center gap-2 text-[10px]">
                          <span className="text-accent-purple">{relLabel}</span>
                          <span className="text-text-secondary truncate">
                            {targetEvent?.title ?? 'Unknown event'}
                          </span>
                          {link.propagation_delay && (
                            <span className="text-text-muted">({link.propagation_delay})</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
