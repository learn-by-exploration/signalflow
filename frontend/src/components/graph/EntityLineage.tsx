/**
 * EntityLineage — shows the data provenance trail for an entity.
 *
 * Displays source articles, confidence, extraction tiers, and data sources
 * that contributed to this entity's presence in the knowledge graph.
 */
'use client';

import { useState, useEffect } from 'react';
import { mkgApi } from '@/lib/mkg-api';
import type { EntityLineage as EntityLineageData } from '@/lib/mkg-api';

interface EntityLineageProps {
  entityId: string;
}

const TIER_LABELS: Record<string, { label: string; emoji: string; color: string }> = {
  tier_1: { label: 'Rule-Based', emoji: '⚙️', color: '#6B7280' },
  tier_2: { label: 'NLP Pipeline', emoji: '🔬', color: '#3B82F6' },
  tier_3: { label: 'LLM Extraction', emoji: '🤖', color: '#8B5CF6' },
};

export function EntityLineage({ entityId }: EntityLineageProps) {
  const [lineage, setLineage] = useState<EntityLineageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(false);

    (async () => {
      try {
        const data = await mkgApi.getEntityLineage(entityId);
        if (!cancelled) setLineage(data);
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [entityId]);

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        <div className="h-4 w-48 bg-white/5 rounded" />
        <div className="h-20 bg-white/5 rounded-lg" />
      </div>
    );
  }

  if (error || !lineage) {
    return (
      <div className="text-center py-4 text-text-muted text-xs">
        Lineage data unavailable. The entity may have been seeded directly.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary row */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="px-3 py-2 rounded-lg border border-border-default bg-bg-secondary text-center">
          <div className="text-sm font-mono text-text-primary">
            {lineage.source_articles.length}
          </div>
          <div className="text-[10px] text-text-muted">Sources</div>
        </div>
        <div className="px-3 py-2 rounded-lg border border-border-default bg-bg-secondary text-center">
          <div className="text-sm font-mono text-text-primary">
            {Math.round(lineage.highest_confidence * 100)}%
          </div>
          <div className="text-[10px] text-text-muted">Max Confidence</div>
        </div>
        <div className="flex gap-1.5">
          {lineage.extraction_tiers_used.map((tier) => {
            const cfg = TIER_LABELS[tier] || {
              label: tier,
              emoji: '📄',
              color: '#6B7280',
            };
            return (
              <span
                key={tier}
                className="px-2 py-1 text-[10px] rounded-full font-mono"
                style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}
                title={`Extraction: ${cfg.label}`}
              >
                {cfg.emoji} {cfg.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Data sources list */}
      {lineage.data_sources.length > 0 && (
        <div>
          <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">
            Data Sources
          </h4>
          <div className="space-y-1.5">
            {lineage.data_sources.map((ds, i) => (
              <div
                key={i}
                className="flex items-center gap-2 p-2.5 rounded-lg border border-border-default bg-bg-secondary text-xs"
              >
                <span className="text-text-secondary">📰</span>
                <span className="text-text-primary font-medium flex-1 truncate">
                  {ds.source}
                </span>
                <span className="text-text-muted font-mono text-[10px] truncate max-w-[120px]">
                  {ds.article_id}
                </span>
                {ds.url && (
                  <a
                    href={ds.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent-purple hover:underline shrink-0"
                  >
                    Open →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {lineage.source_articles.length === 0 && lineage.data_sources.length === 0 && (
        <div className="text-center py-4 text-text-muted text-xs">
          This entity was added as seed data — no extraction trail available.
        </div>
      )}
    </div>
  );
}
