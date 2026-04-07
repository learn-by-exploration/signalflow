/**
 * EntityNode — custom React Flow node for MKG entities.
 */
'use client';

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';

interface EntityNodeData {
  label: string;
  entityType: string;
  tags?: string[];
  isCenter?: boolean;
  isTrigger?: boolean;
  impactScore?: number;
  [key: string]: unknown;
}

/** Map impact score to severity color. */
function impactColor(score: number): string {
  if (score >= 0.7) return '#EF4444'; // red / critical
  if (score >= 0.4) return '#F97316'; // orange / high
  if (score >= 0.1) return '#EAB308'; // yellow / medium
  return '#6B7280'; // gray / low
}

function EntityNodeComponent({ data }: NodeProps) {
  const { label, entityType, isCenter, isTrigger, impactScore } = data as EntityNodeData;
  const color = ENTITY_TYPE_COLORS[entityType as string] || '#6B7280';

  const hasImpact = typeof impactScore === 'number' && impactScore > 0;
  const borderColor = isTrigger
    ? '#FFFFFF'
    : hasImpact
      ? impactColor(impactScore!)
      : isCenter
        ? color
        : 'rgba(255,255,255,0.12)';

  // Scale node size based on impact (add padding for high-impact nodes)
  const scale = isTrigger ? 1.15 : hasImpact ? 1 + impactScore! * 0.15 : isCenter ? 1.1 : 1;

  return (
    <>
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-0 !h-0" />
      <div
        className={`px-3 py-2 rounded-lg border-2 bg-bg-secondary min-w-[100px] max-w-[180px] transition-all
                     ${isTrigger ? 'shadow-lg shadow-white/30 ring-1 ring-white/20' : ''}
                     ${isCenter && !isTrigger ? 'shadow-lg shadow-accent-purple/20' : ''}
                     ${!isCenter && !isTrigger ? 'hover:shadow-md' : ''}`}
        style={{ borderColor, transform: `scale(${scale})` }}
      >
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs font-medium text-text-primary truncate">
            {label as string}
          </span>
        </div>
        <div className="flex items-center gap-1 mt-1">
          <span className="text-[10px] text-text-muted">{entityType as string}</span>
          {impactScore != null && impactScore > 0 && (
            <span className="text-[10px] font-mono ml-auto font-semibold" style={{ color: impactColor(impactScore) }}>
              {Math.round(impactScore * 100)}%
            </span>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-0 !h-0" />
    </>
  );
}

export const EntityNode = memo(EntityNodeComponent);
