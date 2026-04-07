/**
 * EntityCard — rich detail card for a single MKG entity.
 */
'use client';

import Link from 'next/link';
import type { MKGEntity } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';

interface EntityCardProps {
  entity: MKGEntity;
  neighborCount?: number;
  compact?: boolean;
}

export function EntityCard({ entity, neighborCount, compact }: EntityCardProps) {
  const color = ENTITY_TYPE_COLORS[entity.entity_type] || '#6B7280';

  if (compact) {
    return (
      <Link
        href={`/knowledge-graph/entity/${entity.id}`}
        className="block p-3 rounded-lg border border-border-default bg-bg-secondary
                   hover:border-border-hover hover:bg-white/[0.04] transition-colors"
      >
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: color }}
          />
          <span className="text-sm text-text-primary font-medium truncate">
            {entity.name}
          </span>
          <span className="text-xs text-text-muted ml-auto shrink-0">
            {entity.entity_type}
          </span>
        </div>
      </Link>
    );
  }

  return (
    <div className="rounded-xl border border-border-default bg-bg-secondary p-5">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {entityIcon(entity.entity_type)}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-display font-semibold text-text-primary truncate">
            {entity.name}
          </h2>
          <div className="flex items-center gap-2 mt-0.5">
            <span
              className="px-2 py-0.5 text-xs rounded-full font-mono"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {entity.entity_type}
            </span>
            {entity.canonical_name && entity.canonical_name !== entity.name && (
              <span className="text-xs text-text-muted">
                aka {entity.canonical_name}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tags */}
      {entity.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {entity.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-xs rounded-md bg-white/5 text-text-secondary border border-border-default"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-text-muted font-mono">
        {neighborCount !== undefined && (
          <span>{neighborCount} connections</span>
        )}
        {entity.created_at && (
          <span>Added {new Date(entity.created_at).toLocaleDateString()}</span>
        )}
      </div>

      {/* Action */}
      <div className="mt-4 pt-3 border-t border-border-default">
        <Link
          href={`/knowledge-graph/entity/${entity.id}`}
          className="text-sm text-accent-purple hover:text-accent-purple/80 font-medium"
        >
          Explore connections →
        </Link>
      </div>
    </div>
  );
}

function entityIcon(type: string): string {
  const icons: Record<string, string> = {
    Company: '🏢',
    Facility: '🏭',
    Country: '🌍',
    Person: '👤',
    Sector: '📊',
    Product: '📦',
    Regulation: '⚖️',
    Event: '⚡',
  };
  return icons[type] || '🔷';
}
