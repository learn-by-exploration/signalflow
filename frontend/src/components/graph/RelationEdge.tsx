/**
 * RelationEdge — custom React Flow edge for MKG relationships.
 */
'use client';

import { memo } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
} from '@xyflow/react';
import type { EdgeProps } from '@xyflow/react';

interface RelationEdgeData {
  relationType: string;
  weight: number;
  confidence: number;
  [key: string]: unknown;
}

function RelationEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps) {
  const { relationType, weight, confidence } = (data || {}) as RelationEdgeData;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Opacity based on confidence (0.3 – 1.0 range)
  const opacity = 0.3 + (confidence ?? 0.5) * 0.7;
  // Width based on weight (1px – 4px range)
  const strokeWidth = 1 + (weight ?? 0.5) * 3;
  // Stroke style: solid > 0.8, dashed 0.5-0.8, dotted < 0.5
  const conf = confidence ?? 1;
  const strokeDasharray =
    conf < 0.5 ? '2,4' : conf <= 0.8 ? '8,4' : undefined;

  // Format label for display
  const label = relationType
    ? relationType.replace(/_/g, ' ')
    : '';
  // Confidence percentage for badge
  const confPct = conf < 1 ? `${Math.round(conf * 100)}%` : '';

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: `rgba(99, 102, 241, ${opacity})`,
          strokeWidth,
          strokeDasharray,
        }}
      />
      {label && (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan pointer-events-auto"
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            <span className="px-1.5 py-0.5 text-[9px] font-mono text-text-muted bg-bg-primary/90 rounded border border-border-default">
              {label}{confPct && <span className="ml-1 text-text-secondary">· {confPct}</span>}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const RelationEdge = memo(RelationEdgeComponent);
