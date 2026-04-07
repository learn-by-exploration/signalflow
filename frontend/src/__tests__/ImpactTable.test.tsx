/**
 * Tests for ImpactTable component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImpactTable } from '@/components/graph/ImpactTable';
import type { ImpactTableRow } from '@/lib/mkg-types';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function makeRow(overrides: Partial<ImpactTableRow> = {}): ImpactTableRow {
  return {
    rank: 1,
    entity_id: 'e-1',
    entity_name: 'Samsung',
    entity_type: 'Company',
    impact_score: 0.85,
    impact_pct: 85,
    depth: 1,
    path: ['TSMC', 'Samsung'],
    ...overrides,
  };
}

describe('ImpactTable', () => {
  it('shows empty message when no rows', () => {
    render(<ImpactTable rows={[]} />);
    expect(screen.getByText('No affected entities found.')).toBeInTheDocument();
  });

  it('renders rows with entity names', () => {
    const rows = [
      makeRow({ rank: 1, entity_name: 'Samsung', entity_id: 'e-1' }),
      makeRow({ rank: 2, entity_name: 'Apple', entity_id: 'e-2', impact_score: 0.45 }),
    ];
    render(<ImpactTable rows={rows} />);
    expect(screen.getByText('Samsung')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('renders entity type badges', () => {
    render(<ImpactTable rows={[makeRow({ entity_type: 'Facility' })]} />);
    expect(screen.getByText('Facility')).toBeInTheDocument();
  });

  it('renders impact percentage', () => {
    render(<ImpactTable rows={[makeRow({ impact_score: 0.85 })]} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders severity badges', () => {
    const rows = [
      makeRow({ rank: 1, entity_id: 'e-1', impact_score: 0.85 }),
      makeRow({ rank: 2, entity_id: 'e-2', impact_score: 0.65 }),
      makeRow({ rank: 3, entity_id: 'e-3', impact_score: 0.35 }),
      makeRow({ rank: 4, entity_id: 'e-4', impact_score: 0.15 }),
    ];
    render(<ImpactTable rows={rows} />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('renders entity links to detail page', () => {
    render(<ImpactTable rows={[makeRow()]} />);
    const button = screen.getByText('Samsung');
    expect(button.tagName).toBe('BUTTON');
  });

  it('shows trigger info when provided', () => {
    render(<ImpactTable rows={[makeRow()]} trigger="TSMC" />);
    expect(screen.getByText('TSMC')).toBeInTheDocument();
    expect(screen.getByText(/1 entities affected/)).toBeInTheDocument();
  });

  it('renders depth column', () => {
    render(<ImpactTable rows={[makeRow({ depth: 3 })]} />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('sorts by impact when column header clicked', async () => {
    const user = userEvent.setup();
    const rows = [
      makeRow({ rank: 1, entity_id: 'e-1', entity_name: 'Low', impact_score: 0.2 }),
      makeRow({ rank: 2, entity_id: 'e-2', entity_name: 'High', impact_score: 0.9 }),
    ];
    render(<ImpactTable rows={rows} />);

    // Click Impact header to sort desc
    const impactHeader = screen.getByText(/Impact/);
    await user.click(impactHeader);

    const tableRows = screen.getAllByRole('row');
    // First data row (index 1) should be the high-impact entity
    expect(tableRows[1]).toHaveTextContent('High');
  });

  it('has accessible table role', () => {
    render(<ImpactTable rows={[makeRow()]} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
});
