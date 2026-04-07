/**
 * GraphCanvas — React Flow wrapper that renders MKG subgraphs.
 *
 * Converts MKGSubgraph data into React Flow nodes/edges with
 * force-directed layout positioning.
 */
'use client';

import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { MKGSubgraph, MKGEntity } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';
import { EntityNode } from './EntityNode';
import { RelationEdge } from './RelationEdge';

const nodeTypes = { entity: EntityNode };
const edgeTypes = { relation: RelationEdge };

interface GraphCanvasProps {
  subgraph: MKGSubgraph;
  centerId?: string;
  triggerId?: string;
  impactMap?: Map<string, number>;
  onNodeClick?: (entity: MKGEntity) => void;
  className?: string;
}

/**
 * Simple circular layout — places nodes in a circle around the center.
 * For MVP this is more predictable than force simulation.
 */
function layoutNodes(
  entities: MKGEntity[],
  centerId?: string,
): Node[] {
  const center = entities.find((e) => e.id === centerId) || entities[0];
  const others = entities.filter((e) => e.id !== center?.id);

  const nodes: Node[] = [];

  if (center) {
    nodes.push({
      id: center.id,
      type: 'entity',
      position: { x: 400, y: 300 },
      data: {
        label: center.name,
        entityType: center.entity_type,
        tags: center.tags,
        isCenter: true,
      },
    });
  }

  const radius = Math.max(200, others.length * 28);
  others.forEach((entity, i) => {
    const angle = (2 * Math.PI * i) / others.length - Math.PI / 2;
    nodes.push({
      id: entity.id,
      type: 'entity',
      position: {
        x: 400 + radius * Math.cos(angle),
        y: 300 + radius * Math.sin(angle),
      },
      data: {
        label: entity.name,
        entityType: entity.entity_type,
        tags: entity.tags,
        isCenter: false,
      },
    });
  });

  return nodes;
}

export function GraphCanvas({
  subgraph,
  centerId,
  triggerId,
  impactMap,
  onNodeClick,
  className,
}: GraphCanvasProps) {
  const initialNodes = useMemo(() => {
    const laid = layoutNodes(subgraph.nodes, centerId);
    // Apply impact scores and trigger flag
    if (impactMap || triggerId) {
      for (const node of laid) {
        const d = node.data as Record<string, unknown>;
        if (impactMap) {
          const impact = impactMap.get(node.id);
          if (impact !== undefined) d.impactScore = impact;
        }
        if (triggerId && node.id === triggerId) {
          d.isTrigger = true;
        }
      }
    }
    return laid;
  }, [subgraph.nodes, centerId, impactMap, triggerId]);

  const initialEdges: Edge[] = useMemo(
    () =>
      subgraph.edges.map((e) => ({
        id: e.id,
        source: e.source_id,
        target: e.target_id,
        type: 'relation',
        markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: 'rgba(99,102,241,0.5)' },
        data: {
          relationType: e.relation_type,
          weight: e.weight,
          confidence: e.confidence,
        },
      })),
    [subgraph.edges],
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const entity = subgraph.nodes.find((e) => e.id === node.id);
      if (entity) onNodeClick?.(entity);
    },
    [subgraph.nodes, onNodeClick],
  );

  // Entity lookup for minimap colors
  const entityMap = useMemo(
    () => new Map(subgraph.nodes.map((e) => [e.id, e])),
    [subgraph.nodes],
  );

  return (
    <div className={`w-full h-[500px] rounded-xl border border-border-default bg-bg-primary relative ${className ?? ''}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(255,255,255,0.03)" gap={20} />
        <Controls
          className="!bg-bg-secondary !border-border-default !shadow-none [&>button]:!bg-bg-secondary [&>button]:!border-border-default [&>button]:!text-text-secondary [&>button:hover]:!bg-white/5"
        />
        <MiniMap
          nodeColor={(node) => {
            const entity = entityMap.get(node.id);
            return entity ? ENTITY_TYPE_COLORS[entity.entity_type] || '#6B7280' : '#6B7280';
          }}
          className="!bg-bg-secondary !border-border-default"
          maskColor="rgba(10, 11, 15, 0.7)"
        />
      </ReactFlow>
      {/* Impact legend */}
      {impactMap && impactMap.size > 0 && (
        <div className="absolute bottom-3 left-3 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-secondary/90 border border-border-default text-[10px]">
          <span className="text-text-muted">Impact:</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#6B7280' }} />Low</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#EAB308' }} />Med</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#F97316' }} />High</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#EF4444' }} />Critical</span>
          {triggerId && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full border border-white" style={{ backgroundColor: '#FFF' }} />Trigger</span>}
        </div>
      )}
    </div>
  );
}
