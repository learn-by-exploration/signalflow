/**
 * EntityDrawer — slide-out panel for quick entity details.
 *
 * Opens from the right when clicking an entity in graphs or tables.
 * Shows entity info, top relationships, and quick actions without
 * navigating away from the current page.
 */
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { mkgApi } from '@/lib/mkg-api';
import { useGraphStore } from '@/store/graphStore';
import type { MKGEntity, MKGEdge } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';

interface EntityInfo {
  entity: MKGEntity;
  edges: MKGEdge[];
  neighborCount: number;
}

function entityIcon(type: string): string {
  const icons: Record<string, string> = {
    Company: '🏢', Facility: '🏭', Country: '🌍', Person: '👤',
    Sector: '📊', Product: '📦', Regulation: '⚖️', Event: '⚡',
  };
  return icons[type] || '🔷';
}

function formatRelation(type: string): string {
  return type.replace(/_/g, ' ');
}

export function EntityDrawer() {
  const { drawerEntityId, setDrawerEntityId } = useGraphStore();
  const [info, setInfo] = useState<EntityInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [entityNames, setEntityNames] = useState<Map<string, string>>(new Map());
  const drawerRef = useRef<HTMLDivElement>(null);

  const isOpen = drawerEntityId !== null;

  // Fetch entity data when drawer opens
  useEffect(() => {
    if (!drawerEntityId) {
      setInfo(null);
      return;
    }
    let cancelled = false;
    setIsLoading(true);

    (async () => {
      try {
        const [entity, outEdges, inEdges, neighbors] = await Promise.all([
          mkgApi.getEntity(drawerEntityId),
          mkgApi.listEdges(drawerEntityId, undefined, undefined, 10),
          mkgApi.listEdges(undefined, drawerEntityId, undefined, 10),
          mkgApi.getNeighbors(drawerEntityId),
        ]);
        if (cancelled) return;

        // Dedup edges
        const edgeMap = new Map<string, MKGEdge>();
        for (const e of [...outEdges, ...inEdges]) edgeMap.set(e.id, e);
        // Sort by weight descending
        const edges = Array.from(edgeMap.values()).sort((a, b) => b.weight - a.weight).slice(0, 5);

        // Build name lookup
        const names = new Map<string, string>();
        names.set(entity.id, entity.name);
        for (const n of neighbors) names.set(n.id, n.name);
        setEntityNames(names);

        setInfo({ entity, edges, neighborCount: neighbors.length });
      } catch {
        // ignore
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [drawerEntityId]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerEntityId(null);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, setDrawerEntityId]);

  // Close on backdrop click
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        setDrawerEntityId(null);
      }
    },
    [setDrawerEntityId],
  );

  if (!isOpen) return null;

  const entity = info?.entity;
  const color = entity ? (ENTITY_TYPE_COLORS[entity.entity_type] || '#6B7280') : '#6B7280';

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-label="Entity details"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" />

      {/* Drawer panel */}
      <div
        ref={drawerRef}
        className="relative w-full max-w-md bg-bg-primary border-l border-border-default shadow-2xl
                   overflow-y-auto animate-in slide-in-from-right duration-300"
      >
        {/* Close button */}
        <button
          onClick={() => setDrawerEntityId(null)}
          className="absolute top-4 right-4 text-text-muted hover:text-text-primary z-10"
          aria-label="Close drawer"
        >
          ✕
        </button>

        {isLoading ? (
          <div className="p-6 space-y-4 animate-pulse">
            <div className="flex gap-3">
              <div className="w-10 h-10 rounded-lg bg-white/5" />
              <div>
                <div className="h-5 w-32 bg-white/5 rounded mb-2" />
                <div className="h-4 w-20 bg-white/5 rounded" />
              </div>
            </div>
            <div className="h-4 w-full bg-white/5 rounded" />
            <div className="h-4 w-3/4 bg-white/5 rounded" />
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-12 bg-white/5 rounded-lg" />
              ))}
            </div>
          </div>
        ) : entity ? (
          <div className="p-6">
            {/* Header */}
            <div className="flex items-start gap-3 mb-4 pr-8">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0"
                style={{ backgroundColor: `${color}20`, color }}
              >
                {entityIcon(entity.entity_type)}
              </div>
              <div>
                <h2 className="text-lg font-display font-semibold text-text-primary">
                  {entity.name}
                </h2>
                <span
                  className="px-2 py-0.5 text-xs rounded-full font-mono"
                  style={{ backgroundColor: `${color}20`, color }}
                >
                  {entity.entity_type}
                </span>
                {entity.canonical_name && entity.canonical_name !== entity.name && (
                  <span className="text-xs text-text-muted ml-2">
                    aka {entity.canonical_name}
                  </span>
                )}
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

            {/* Stats */}
            <div className="flex gap-4 text-xs text-text-muted font-mono mb-5">
              <span>{info?.neighborCount ?? 0} connections</span>
              {entity.created_at && (
                <span>Added {new Date(entity.created_at).toLocaleDateString()}</span>
              )}
            </div>

            {/* Quick actions */}
            <div className="flex flex-wrap gap-2 mb-6">
              <Link
                href={`/knowledge-graph/entity/${entity.id}`}
                onClick={() => setDrawerEntityId(null)}
                className="px-3 py-1.5 text-xs rounded-lg bg-accent-purple/10 text-accent-purple
                           hover:bg-accent-purple/20 font-medium transition-colors"
              >
                Open Full Page
              </Link>
              <Link
                href={`/knowledge-graph/simulate?entity=${entity.id}`}
                onClick={() => setDrawerEntityId(null)}
                className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-secondary
                           hover:bg-white/5 font-medium transition-colors"
              >
                ⚡ Run Impact Sim
              </Link>
            </div>

            {/* Top relationships */}
            {info && info.edges.length > 0 && (
              <div>
                <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3">
                  Top Relationships
                </h3>
                <div className="space-y-2">
                  {info.edges.map((edge) => {
                    const isOutgoing = edge.source_id === entity.id;
                    const otherId = isOutgoing ? edge.target_id : edge.source_id;
                    const otherName = entityNames.get(otherId) || otherId.slice(0, 12) + '…';

                    return (
                      <button
                        key={edge.id}
                        onClick={() => setDrawerEntityId(otherId)}
                        className="w-full text-left p-3 rounded-lg border border-border-default bg-bg-secondary
                                   hover:border-border-hover hover:bg-white/[0.04] transition-colors"
                      >
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-text-primary font-medium truncate">
                            {isOutgoing ? entity.name : otherName}
                          </span>
                          <span className="px-1.5 py-0.5 rounded-full bg-accent-purple/10 text-accent-purple font-mono shrink-0">
                            {formatRelation(edge.relation_type)}
                          </span>
                          <span className="text-text-muted">→</span>
                          <span className="text-text-primary font-medium truncate">
                            {isOutgoing ? otherName : entity.name}
                          </span>
                        </div>
                        <div className="flex gap-3 mt-1.5 text-[10px] font-mono text-text-muted">
                          <span>Weight: {Math.round(edge.weight * 100)}%</span>
                          <span>Confidence: {Math.round(edge.confidence * 100)}%</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {info && info.edges.length === 0 && (
              <div className="text-center py-6 text-text-muted text-sm">
                No relationships found.
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center text-text-muted text-sm">
            Entity not found.
          </div>
        )}
      </div>
    </div>
  );
}
