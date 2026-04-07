/**
 * Tests for RelationshipTable component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RelationshipTable } from '@/components/graph/RelationshipTable';
import type { MKGEdge } from '@/lib/mkg-types';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function makeEdge(overrides: Partial<MKGEdge> = {}): MKGEdge {
  return {
    id: 'edge-1',
    source_id: 'e-tsmc',
    target_id: 'e-apple',
    relation_type: 'SUPPLIES_TO',
    weight: 0.85,
    confidence: 0.92,
    direction: 'downstream',
    tags: [],
    valid_from: null,
    valid_until: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-06-01T00:00:00Z',
    source: 'Annual Report 2024',
    ...overrides,
  };
}

function makeEntityMap() {
  return new Map([
    ['e-tsmc', { id: 'e-tsmc', name: 'TSMC', entity_type: 'Company' }],
    ['e-apple', { id: 'e-apple', name: 'Apple', entity_type: 'Company' }],
    ['e-samsung', { id: 'e-samsung', name: 'Samsung', entity_type: 'Company' }],
  ]);
}

describe('RelationshipTable', () => {
  it('shows empty message when no edges', () => {
    render(<RelationshipTable edges={[]} />);
    expect(screen.getByText('No relationships found.')).toBeInTheDocument();
  });

  it('renders entity names from entity map', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} />);
    expect(screen.getByText('TSMC')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('renders relation type with spaces', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} />);
    // Appears in both table cell and filter dropdown
    const matches = screen.getAllByText('SUPPLIES TO');
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('renders weight percentage', () => {
    render(<RelationshipTable edges={[makeEdge({ weight: 0.85 })]} entityMap={makeEntityMap()} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders confidence percentage', () => {
    render(<RelationshipTable edges={[makeEdge({ confidence: 0.92 })]} entityMap={makeEntityMap()} />);
    expect(screen.getByText('92%')).toBeInTheDocument();
  });

  it('renders provenance badge', () => {
    render(<RelationshipTable edges={[makeEdge({ source: 'reuters-article-123' })]} entityMap={makeEntityMap()} />);
    // Provenance badge should render for news-sourced data
    expect(screen.getByText('News-Sourced')).toBeInTheDocument();
  });

  it('renders source entity link', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} />);
    const link = screen.getByText('TSMC');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-tsmc');
  });

  it('renders target entity link', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} />);
    const link = screen.getByText('Apple');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-apple');
  });

  it('renders title when provided', () => {
    render(<RelationshipTable edges={[makeEdge()]} title="My Relationships" />);
    expect(screen.getByText('My Relationships')).toBeInTheDocument();
  });

  it('shows edge count', () => {
    render(<RelationshipTable edges={[makeEdge()]} />);
    expect(screen.getByText(/1 of 1 relationships/)).toBeInTheDocument();
  });

  it('renders relation type filter dropdown', () => {
    const edges = [
      makeEdge({ id: 'e1', relation_type: 'SUPPLIES_TO' }),
      makeEdge({ id: 'e2', relation_type: 'COMPETES_WITH' }),
    ];
    render(<RelationshipTable edges={edges} />);
    expect(screen.getByText('All types')).toBeInTheDocument();
  });

  it('filters by relation type', async () => {
    const user = userEvent.setup();
    const edges = [
      makeEdge({ id: 'e1', relation_type: 'SUPPLIES_TO', source_id: 'e-tsmc', target_id: 'e-apple' }),
      makeEdge({ id: 'e2', relation_type: 'COMPETES_WITH', source_id: 'e-apple', target_id: 'e-samsung' }),
    ];
    render(<RelationshipTable edges={edges} entityMap={makeEntityMap()} />);

    // Initially shows both
    expect(screen.getByText(/2 of 2/)).toBeInTheDocument();

    // Select SUPPLIES_TO filter
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'SUPPLIES_TO');

    // Should show 1 of 2
    expect(screen.getByText(/1 of 2/)).toBeInTheDocument();
  });

  it('sorts by weight when header clicked', async () => {
    const user = userEvent.setup();
    const edges = [
      makeEdge({ id: 'e1', weight: 0.3, source_id: 'e-tsmc' }),
      makeEdge({ id: 'e2', weight: 0.9, source_id: 'e-apple' }),
    ];
    render(<RelationshipTable edges={edges} entityMap={makeEntityMap()} />);

    // Default sort is weight desc, so first data row should be 90%
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('90%');

    // Click weight header to flip to asc
    const weightHeader = screen.getByText(/Weight/);
    await user.click(weightHeader);

    const rowsAfter = screen.getAllByRole('row');
    // Now first data row should be 30%
    expect(rowsAfter[1]).toHaveTextContent('30%');
  });

  it('has accessible table role', () => {
    render(<RelationshipTable edges={[makeEdge()]} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('falls back to truncated ID when entity not in map', () => {
    render(<RelationshipTable edges={[makeEdge({ source_id: 'very-long-entity-id-here' })]} />);
    expect(screen.getByText('very-long-entity…')).toBeInTheDocument();
  });

  it('shows curated badge for missing source info', () => {
    render(<RelationshipTable edges={[makeEdge({ source: undefined })]} />);
    // Provenance badge should render as Curated for seed data
    expect(screen.getByText('Curated')).toBeInTheDocument();
  });

  it('hides source column when hideSource is true', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} hideSource />);
    // Source header should not be present
    expect(screen.queryByText('Source')).not.toBeInTheDocument();
    // But target should still be there
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('hides target column when hideTarget is true', () => {
    render(<RelationshipTable edges={[makeEdge()]} entityMap={makeEntityMap()} hideTarget />);
    // Target header should not be present
    expect(screen.queryByText('Target')).not.toBeInTheDocument();
    // But source should still be there
    expect(screen.getByText('TSMC')).toBeInTheDocument();
  });

  it('renders multiple edges', () => {
    const edges = [
      makeEdge({ id: 'e1', source_id: 'e-tsmc', target_id: 'e-apple', relation_type: 'SUPPLIES_TO' }),
      makeEdge({ id: 'e2', source_id: 'e-apple', target_id: 'e-samsung', relation_type: 'COMPETES_WITH' }),
    ];
    render(<RelationshipTable edges={edges} entityMap={makeEntityMap()} />);
    // Each relation type appears in table cell + dropdown option
    const suppliesTo = screen.getAllByText('SUPPLIES TO');
    const competesWith = screen.getAllByText('COMPETES WITH');
    expect(suppliesTo.length).toBeGreaterThanOrEqual(1);
    expect(competesWith.length).toBeGreaterThanOrEqual(1);
  });
});
