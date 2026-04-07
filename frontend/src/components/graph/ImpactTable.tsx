/**
 * ImpactTable — ranked table of propagation results.
 *
 * Columns: Rank, Entity, Type, Impact, Depth, Severity.
 * Sortable, accessible, with severity color coding.
 */
'use client';

import { useMemo, useState } from 'react';
import type { ImpactTableRow } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS, SEVERITY_COLORS } from '@/lib/mkg-types';
import { useGraphStore } from '@/store/graphStore';

interface ImpactTableProps {
  rows: ImpactTableRow[];
  trigger?: string | null;
}

type SortCol = 'rank' | 'impact' | 'depth';
type SortDir = 'asc' | 'desc';

function severity(impact: number): keyof typeof SEVERITY_COLORS {
  if (impact >= 0.8) return 'critical';
  if (impact >= 0.6) return 'high';
  if (impact >= 0.3) return 'medium';
  return 'low';
}

function severityLabel(s: keyof typeof SEVERITY_COLORS): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function ImpactTable({ rows, trigger }: ImpactTableProps) {
  const [sortCol, setSortCol] = useState<SortCol>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const setDrawerEntityId = useGraphStore((s) => s.setDrawerEntityId);

  const sorted = useMemo(() => {
    const items = [...rows];
    items.sort((a, b) => {
      let cmp = 0;
      if (sortCol === 'rank') cmp = a.rank - b.rank;
      else if (sortCol === 'impact') cmp = a.impact_score - b.impact_score;
      else if (sortCol === 'depth') cmp = a.depth - b.depth;
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return items;
  }, [rows, sortCol, sortDir]);

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortCol(col);
      setSortDir(col === 'rank' ? 'asc' : 'desc');
    }
  }

  const arrow = (col: SortCol) =>
    sortCol === col ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '';

  if (rows.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted text-sm">
        No affected entities found.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border-default overflow-hidden">
      {trigger && (
        <div className="px-4 py-2 bg-bg-secondary border-b border-border-default text-xs text-text-muted">
          Triggered by: <span className="text-text-primary font-medium">{trigger}</span>
          <span className="ml-3">{rows.length} entities affected</span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table">
          <thead>
            <tr className="bg-bg-secondary text-text-muted text-xs uppercase tracking-wider">
              <th
                className="px-4 py-3 text-left cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('rank')}
              >
                #{arrow('rank')}
              </th>
              <th className="px-4 py-3 text-left">Entity</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th
                className="px-4 py-3 text-right cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('impact')}
              >
                Impact{arrow('impact')}
              </th>
              <th
                className="px-4 py-3 text-center cursor-pointer hover:text-text-secondary select-none"
                onClick={() => toggleSort('depth')}
              >
                Hops{arrow('depth')}
              </th>
              <th className="px-4 py-3 text-center">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {sorted.map((row) => {
              const sev = severity(row.impact_score);
              const sevColor = SEVERITY_COLORS[sev];
              const typeColor = ENTITY_TYPE_COLORS[row.entity_type] || '#6B7280';
              return (
                <tr
                  key={row.entity_id}
                  className="hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-3 text-text-muted font-mono text-xs">
                    {row.rank}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setDrawerEntityId(row.entity_id)}
                      className="text-text-primary hover:text-accent-purple font-medium text-left"
                    >
                      {row.entity_name}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="px-2 py-0.5 text-xs rounded-full font-mono"
                      style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
                    >
                      {row.entity_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono" style={{ color: sevColor }}>
                    {Math.round(row.impact_score * 100)}%
                  </td>
                  <td className="px-4 py-3 text-center text-text-muted font-mono text-xs">
                    {row.depth}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className="px-2 py-0.5 text-xs rounded-full font-mono"
                      style={{ backgroundColor: `${sevColor}20`, color: sevColor }}
                    >
                      {severityLabel(sev)}
                    </span>
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
