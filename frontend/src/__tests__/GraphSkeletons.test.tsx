/**
 * Tests for GraphSkeletons components + dummy data fixtures.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  EntityCardSkeleton,
  EntityCardCompactSkeleton,
  GraphCanvasSkeleton,
  RelationshipTableSkeleton,
  StatCardSkeleton,
  ImpactTableSkeleton,
} from '@/components/graph/GraphSkeletons';
import {
  DUMMY_ENTITIES,
  DUMMY_EDGES,
  DUMMY_ALERTS,
  DUMMY_SUBGRAPH,
  DUMMY_GRAPH_HEALTH,
  DUMMY_PROPAGATION_RESULT,
  DUMMY_IMPACT_TABLE_ROWS,
  DUMMY_CAUSAL_CHAINS,
  dummyEntity,
  dummyEdge,
  dummyAlert,
  dummyEntities,
  dummyEdges,
  dummySubgraph,
} from '@/lib/mkg-dummy-data';

// ── Skeleton rendering tests ──

describe('GraphSkeletons', () => {
  it('renders EntityCardSkeleton', () => {
    const { container } = render(<EntityCardSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders EntityCardCompactSkeleton', () => {
    const { container } = render(<EntityCardCompactSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders GraphCanvasSkeleton with simulated nodes', () => {
    const { container } = render(<GraphCanvasSkeleton />);
    // Should have the skeleton container
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders RelationshipTableSkeleton with default 5 rows', () => {
    const { container } = render(<RelationshipTableSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    // Should have the heading placeholder + 5 row placeholders
    const rows = container.querySelectorAll('.divide-y > div');
    expect(rows.length).toBe(5);
  });

  it('renders RelationshipTableSkeleton with custom row count', () => {
    const { container } = render(<RelationshipTableSkeleton rows={3} />);
    const rows = container.querySelectorAll('.divide-y > div');
    expect(rows.length).toBe(3);
  });

  it('renders StatCardSkeleton with default 3 cards', () => {
    const { container } = render(<StatCardSkeleton />);
    // 3 skeleton cards rendered
    const cards = container.querySelectorAll('.animate-pulse');
    expect(cards.length).toBe(3);
  });

  it('renders StatCardSkeleton with custom count', () => {
    const { container } = render(<StatCardSkeleton count={5} />);
    const cards = container.querySelectorAll('.animate-pulse');
    expect(cards.length).toBe(5);
  });

  it('renders ImpactTableSkeleton', () => {
    const { container } = render(<ImpactTableSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});

// ── Dummy data integrity tests ──

describe('Dummy Data Fixtures', () => {
  describe('DUMMY_ENTITIES', () => {
    it('contains expected number of entities', () => {
      expect(DUMMY_ENTITIES.length).toBe(8);
    });

    it('has all required fields on every entity', () => {
      for (const e of DUMMY_ENTITIES) {
        expect(e.id).toBeTruthy();
        expect(e.entity_type).toBeTruthy();
        expect(e.name).toBeTruthy();
        expect(e.canonical_name).toBeTruthy();
        expect(Array.isArray(e.tags)).toBe(true);
        expect(e.tags.length).toBeGreaterThan(0);
      }
    });

    it('covers multiple entity types', () => {
      const types = new Set(DUMMY_ENTITIES.map((e) => e.entity_type));
      expect(types.has('company')).toBe(true);
      expect(types.has('sector')).toBe(true);
      expect(types.has('regulator')).toBe(true);
      expect(types.has('crypto')).toBe(true);
      expect(types.has('commodity')).toBe(true);
    });

    it('has unique IDs', () => {
      const ids = DUMMY_ENTITIES.map((e) => e.id);
      expect(new Set(ids).size).toBe(ids.length);
    });
  });

  describe('DUMMY_EDGES', () => {
    it('contains expected number of edges', () => {
      expect(DUMMY_EDGES.length).toBe(6);
    });

    it('has all required fields on every edge', () => {
      for (const e of DUMMY_EDGES) {
        expect(e.id).toBeTruthy();
        expect(e.source_id).toBeTruthy();
        expect(e.target_id).toBeTruthy();
        expect(e.relation_type).toBeTruthy();
        expect(typeof e.weight).toBe('number');
        expect(typeof e.confidence).toBe('number');
        expect(e.weight).toBeGreaterThanOrEqual(0);
        expect(e.weight).toBeLessThanOrEqual(1);
        expect(e.confidence).toBeGreaterThanOrEqual(0);
        expect(e.confidence).toBeLessThanOrEqual(1);
      }
    });

    it('references valid entity IDs', () => {
      const entityIds = new Set(DUMMY_ENTITIES.map((e) => e.id));
      for (const edge of DUMMY_EDGES) {
        expect(entityIds.has(edge.source_id)).toBe(true);
        expect(entityIds.has(edge.target_id)).toBe(true);
      }
    });

    it('covers multiple provenance sources', () => {
      const sources = DUMMY_EDGES.map((e) => e.source);
      expect(sources).toContain(null); // seed
      expect(sources.some((s) => typeof s === 'string' && s.includes('claude'))).toBe(true); // AI
      expect(sources.some((s) => typeof s === 'string' && s.includes('reuters'))).toBe(true); // news
    });

    it('covers multiple relation types', () => {
      const types = new Set(DUMMY_EDGES.map((e) => e.relation_type));
      expect(types.size).toBeGreaterThanOrEqual(4);
    });
  });

  describe('DUMMY_ALERTS', () => {
    it('contains all severity levels', () => {
      const severities = new Set(DUMMY_ALERTS.map((a) => a.severity));
      expect(severities).toEqual(new Set(['critical', 'high', 'medium', 'low']));
    });

    it('has valid causal chains', () => {
      for (const alert of DUMMY_ALERTS) {
        expect(alert.source_chain.trigger_name).toBeTruthy();
        expect(alert.source_chain.affected_name).toBeTruthy();
        expect(alert.source_chain.narrative).toBeTruthy();
        expect(alert.source_chain.hops).toBeGreaterThanOrEqual(1);
      }
    });

    it('has impact scores between 0 and 1', () => {
      for (const alert of DUMMY_ALERTS) {
        expect(alert.impact_score).toBeGreaterThanOrEqual(0);
        expect(alert.impact_score).toBeLessThanOrEqual(1);
      }
    });
  });

  describe('DUMMY_PROPAGATION_RESULT', () => {
    it('has consistent trigger across chains', () => {
      for (const chain of DUMMY_CAUSAL_CHAINS) {
        expect(chain.trigger).toBe('00000000-0000-0000-0000-000000000001');
        expect(chain.trigger_name).toBe('TSMC');
      }
    });

    it('has impact table rows sorted by rank', () => {
      for (let i = 1; i < DUMMY_IMPACT_TABLE_ROWS.length; i++) {
        expect(DUMMY_IMPACT_TABLE_ROWS[i].rank).toBeGreaterThan(
          DUMMY_IMPACT_TABLE_ROWS[i - 1].rank,
        );
      }
    });

    it('has decreasing impact scores in impact table', () => {
      for (let i = 1; i < DUMMY_IMPACT_TABLE_ROWS.length; i++) {
        expect(DUMMY_IMPACT_TABLE_ROWS[i].impact_score).toBeLessThanOrEqual(
          DUMMY_IMPACT_TABLE_ROWS[i - 1].impact_score,
        );
      }
    });

    it('has matching impact_pct = impact_score * 100', () => {
      for (const row of DUMMY_IMPACT_TABLE_ROWS) {
        expect(row.impact_pct).toBe(Math.round(row.impact_score * 100));
      }
    });
  });

  describe('DUMMY_SUBGRAPH', () => {
    it('has nodes and edges', () => {
      expect(DUMMY_SUBGRAPH.nodes.length).toBe(5);
      expect(DUMMY_SUBGRAPH.edges.length).toBe(4);
    });
  });

  describe('DUMMY_GRAPH_HEALTH', () => {
    it('reports healthy status', () => {
      expect(DUMMY_GRAPH_HEALTH.status).toBe('healthy');
      expect(DUMMY_GRAPH_HEALTH.backend).toBe('postgresql');
      expect(DUMMY_GRAPH_HEALTH.entity_count).toBe(48);
      expect(DUMMY_GRAPH_HEALTH.edge_count).toBe(49);
    });
  });

  describe('helper functions', () => {
    it('dummyEntity returns entity by index', () => {
      expect(dummyEntity(0).name).toBe('TSMC');
      expect(dummyEntity(1).name).toBe('Samsung Electronics');
    });

    it('dummyEntity wraps around', () => {
      expect(dummyEntity(8).name).toBe(dummyEntity(0).name);
      expect(dummyEntity(10).name).toBe(dummyEntity(2).name);
    });

    it('dummyEdge returns edge by index', () => {
      expect(dummyEdge(0).relation_type).toBe('competes_with');
    });

    it('dummyEdge wraps around', () => {
      expect(dummyEdge(6)).toEqual(dummyEdge(0));
    });

    it('dummyAlert returns alert by index', () => {
      expect(dummyAlert(0).severity).toBe('critical');
      expect(dummyAlert(3).severity).toBe('low');
    });

    it('dummyEntities returns N entities', () => {
      const entities = dummyEntities(3);
      expect(entities.length).toBe(3);
      expect(entities[0].name).toBe('TSMC');
      expect(entities[2].name).toBe('Reliance Industries');
    });

    it('dummyEntities supports offset', () => {
      const entities = dummyEntities(2, 5);
      expect(entities[0].name).toBe('BTC');
      expect(entities[1].name).toBe('Infosys');
    });

    it('dummyEdges returns N edges', () => {
      const edges = dummyEdges(4);
      expect(edges.length).toBe(4);
    });

    it('dummySubgraph builds custom-sized subgraph', () => {
      const sg = dummySubgraph(3, 2);
      expect(sg.nodes.length).toBe(3);
      expect(sg.edges.length).toBe(2);
    });
  });
});
