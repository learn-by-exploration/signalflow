/**
 * RelationshipTable — browsable, sortable table of MKG edges.
 *
 * Shows source → relation → target with weight, confidence, and dates.
 * Resolves entity names from a provided entity map or displays IDs as fallback.
 */
'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import type { MKGEdge } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';
import { ProvenanceBadge } from './ProvenanceBadge';

interface EntityInfo {
  id: string;
  name: string;
  entity_type: string;
}

interface RelationshipTableProps {
  edges: MKGEdge[];
  /** Map of entity ID → name + type for display. */
  entityMap?: Map<string, EntityInfo>;
  /** Title displayed above table. */
  title?: string;
  /** If true, hide the source column (used on entity detail page). */
  hideSource?: boolean;
  /** If true, hide the target column. */
  hideTarget?: boolean;
}

type SortCol = 'relation' | 'weight' | 'confidence';
type SortDir = 'asc' | 'desc';

function confidenceColor(c: number): string {
  if (c >= 0.8) return '#00E676';
  if (c >= 0.6) return '#FFD740';
  if (c >= 0.4) return '#FF9800';
  return '#FF5252';
}

function formatRelation(type: string): string {
  return type.replace(/_/g, ' ');
}

/** Compute edge freshness from updated_at / created_at. */
function edgeAge(edge: MKGEdge): { label: string; color: string; days: number } {
  const dateStr = (edge.updated_at || edge.created_at) as string | null;
  if (!dateStr) return { label: 'Unknown', color: '#6B7280', days: Infinity };
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24));
  if (days <= 7) return { label: `${days}d ago`, color: '#00E676', days };
  if (days <= 30) return { label: `${days}d ago`, color: '#FFD740', days };
  if (days <= 90) return { label: `${Math.round(days / 7)}w ago`, color: '#FF9800', days };
  if (days <= 365) return { label: `${Math.round(days / 30)}mo ago`, color: '#FF5252', days };
  return { label: `${Math.round(days / 365)}y ago`, color: '#FF5252', days };
}

export function RelationshipTable({
  edges,
  entityMap,
  title,
  hideSource,
  hideTarget,
}: RelationshipTableProps) {
  const [sortCol, setSortCol] = useState<SortCol>('weight');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [filterRelation, setFilterRelation] = useState<string>('');

  // Collect unique relation types for filter dropdown
  const relationTypes = useMemo(
    () => [...new Set(edges.map((e) => e.relation_type))].sort(),
    [edges],
  );

  // Filter and sort
  const displayed = useMemo(() => {
    let items = [...edges];
    if (filterRelation) {
      items = items.filter((e) => e.relation_type === filterRelation);
    }
    items.sort((a, b) => {
      let cmp = 0;
      if (sortCol === 'relation') cmp = a.relation_type.localeCompare(b.relation_type);
      else if (sortCol === 'weight') cmp = a.weight - b.weight;
      else if (sortCol === 'confidence') cmp = a.confidence - b.confidence;
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return items;
  }, [edges, filterRelation, sortCol, sortDir]);

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortCol(col);
      setSortDir('desc');
    }
  }

  const arrow = (col: SortCol) =>
    sortCol === col ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  function entityLabel(id: string): { name: string; type?: string } {
    const info = entityMap?.get(id);
    if (info) return { name: info.name, type: info.entity_type };
    // Fallback: show truncated ID
    return { name: id.length > 16 ? `${id.slice(0, 16)}…` : id };
  }

  if (edges.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted text-sm">
        No relationships found.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border-default overflow-hidden">
      {/* Header bar */}
      <div className="px-4 py-3 bg-bg-secondary border-b border-border-default flex items-center gap-3 flex-wrap">
        {title && (
          <span className="text-sm font-display font-semibold text-text-primary">{title}</span>
        )}
        <span className="text-xs text-text-muted">
          {displayed.length} of {edges.length} relationships
        </span>
        <select
          value={filterRelation}
          onChange={(e) => setFilterRelation(e.target.value)}
          className="ml-auto px-2 py-1 text-xs rounded bg-bg-primary border border-border-default
                     text-text-primary"
        >
          <option value="">All types</option>
          {relationTypes.map((rt) => (
            <option key={rt} value={rt}>
              {formatRelation(rt)}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table">
          <thead>
            <tr className="bg-bg-secondary text-text-muted text-xs uppercase tracking-wider">
              {!hideSource && (
                <th className="px-4 py-3 text-left">Source</th>
              )}
              <th
                className="px-4 py-3 text-left cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('relation')}
              >
                Relationship{arrow('relation')}
              </th>
              {!hideTarget && (
                <th className="px-4 py-3 text-left">Target</th>
              )}
              <th
                className="px-4 py-3 text-right cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('weight')}
              >
                Weight{arrow('weight')}
              </th>
              <th
                className="px-4 py-3 text-right cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('confidence')}
              >
                Confidence{arrow('confidence')}
              </th>
              <th className="px-4 py-3 text-left">Provenance</th>
              <th className="px-4 py-3 text-center">Freshness</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {displayed.map((edge) => {
              const src = entityLabel(edge.source_id);
              const tgt = entityLabel(edge.target_id);
              const srcColor = src.type ? (ENTITY_TYPE_COLORS[src.type] || '#6B7280') : '#6B7280';
              const tgtColor = tgt.type ? (ENTITY_TYPE_COLORS[tgt.type] || '#6B7280') : '#6B7280';

              return (
                <tr
                  key={edge.id}
                  className="hover:bg-white/[0.02] transition-colors"
                >
                  {!hideSource && (
                    <td className="px-4 py-3">
                      <Link
                        href={`/knowledge-graph/entity/${edge.source_id}`}
                        className="text-text-primary hover:text-accent-purple font-medium"
                      >
                        <span className="flex items-center gap-1.5">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: srcColor }}
                          />
                          {src.name}
                        </span>
                      </Link>
                      {src.type && (
                        <span className="text-xs text-text-muted">{src.type}</span>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 text-xs rounded-full bg-accent-purple/10 text-accent-purple font-mono">
                      {formatRelation(edge.relation_type)}
                    </span>
                    <span className="text-text-muted text-xs ml-1.5">→</span>
                  </td>
                  {!hideTarget && (
                    <td className="px-4 py-3">
                      <Link
                        href={`/knowledge-graph/entity/${edge.target_id}`}
                        className="text-text-primary hover:text-accent-purple font-medium"
                      >
                        <span className="flex items-center gap-1.5">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: tgtColor }}
                          />
                          {tgt.name}
                        </span>
                      </Link>
                      {tgt.type && (
                        <span className="text-xs text-text-muted">{tgt.type}</span>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">
                    {(edge.weight * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span style={{ color: confidenceColor(edge.confidence) }}>
                      {(edge.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-text-muted">
                    <ProvenanceBadge source={edge.source as string | undefined} showLabel />
                  </td>
                  <td className="px-4 py-3 text-center">
                    {(() => {
                      const age = edgeAge(edge);
                      return (
                        <span className="text-xs font-mono" style={{ color: age.color }}>
                          {age.label}
                        </span>
                      );
                    })()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
