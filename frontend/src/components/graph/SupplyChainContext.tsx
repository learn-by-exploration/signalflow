/**
 * SupplyChainContext — shows MKG supply chain context for a signal.
 *
 * Searches for the signal's symbol in the knowledge graph, and if found,
 * displays a mini graph of neighbors + link to full entity page.
 */
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import type { MKGEntity } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';
import { useGraphStore } from '@/store/graphStore';
import { EntityDrawer } from './EntityDrawer';

interface SupplyChainContextProps {
  symbol: string;
  marketType?: string;
}

function normalizeSymbol(symbol: string, marketType?: string): string {
  // Strip .NS suffix for Indian stocks
  let s = symbol.replace(/\.NS$/i, '');
  // Strip USDT suffix for crypto
  if (marketType === 'crypto') {
    s = s.replace(/USDT$/i, '');
  }
  return s;
}

function entityIcon(type: string): string {
  const icons: Record<string, string> = {
    Company: '🏢', Facility: '🏭', Country: '🌍', Sector: '📊',
  };
  return icons[type] || '🔷';
}

export function SupplyChainContext({ symbol, marketType }: SupplyChainContextProps) {
  const [matchedEntity, setMatchedEntity] = useState<MKGEntity | null>(null);
  const [neighbors, setNeighbors] = useState<MKGEntity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const setDrawerEntityId = useGraphStore((s) => s.setDrawerEntityId);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setNotFound(false);

    (async () => {
      try {
        const searchName = normalizeSymbol(symbol, marketType);
        const results = await mkgApi.searchEntities(searchName, undefined, 5);
        if (cancelled) return;

        if (results.length === 0) {
          setNotFound(true);
          return;
        }

        const entity = results[0];
        setMatchedEntity(entity);

        // Fetch neighbors
        const nb = await mkgApi.getNeighbors(entity.id);
        if (!cancelled) {
          setNeighbors(nb.slice(0, 6));
        }
      } catch {
        setNotFound(true);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [symbol, marketType]);

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-4 w-40 bg-white/5 rounded" />
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-white/5 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (notFound || !matchedEntity) {
    return (
      <div className="text-center py-4">
        <p className="text-xs text-text-muted">
          No supply chain data found for {symbol}.
        </p>
      </div>
    );
  }

  const color = ENTITY_TYPE_COLORS[matchedEntity.entity_type] || '#6B7280';

  return (
    <div className="space-y-3">
      {/* Matched entity */}
      <div className="flex items-center gap-2">
        <span className="text-sm">{entityIcon(matchedEntity.entity_type)}</span>
        <button
          onClick={() => setDrawerEntityId(matchedEntity.id)}
          className="text-sm font-medium text-text-primary hover:text-accent-purple"
        >
          {matchedEntity.name}
        </button>
        <span
          className="px-1.5 py-0.5 text-[10px] rounded-full font-mono"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {matchedEntity.entity_type}
        </span>
        <span className="text-xs text-text-muted ml-auto">
          {neighbors.length} connection{neighbors.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Neighbor grid */}
      {neighbors.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {neighbors.map((n) => {
            const nColor = ENTITY_TYPE_COLORS[n.entity_type] || '#6B7280';
            return (
              <button
                key={n.id}
                onClick={() => setDrawerEntityId(n.id)}
                className="text-left p-2.5 rounded-lg border border-border-default bg-bg-secondary
                           hover:border-border-hover hover:bg-white/[0.04] transition-colors"
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: nColor }}
                  />
                  <span className="text-xs text-text-primary font-medium truncate">
                    {n.name}
                  </span>
                </div>
                <span className="text-[10px] text-text-muted">{n.entity_type}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <Link
          href={`/knowledge-graph/entity/${matchedEntity.id}`}
          className="text-xs text-accent-purple hover:underline"
        >
          View Full Graph →
        </Link>
        <Link
          href={`/knowledge-graph/simulate?entity=${matchedEntity.id}`}
          className="text-xs text-text-muted hover:text-text-secondary"
        >
          ⚡ Run Impact Sim
        </Link>
      </div>

      <EntityDrawer />
    </div>
  );
}
