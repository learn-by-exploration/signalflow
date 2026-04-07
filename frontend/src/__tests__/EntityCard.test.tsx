/**
 * Tests for EntityCard component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EntityCard } from '@/components/graph/EntityCard';
import type { MKGEntity } from '@/lib/mkg-types';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function makeEntity(overrides: Partial<MKGEntity> = {}): MKGEntity {
  return {
    id: 'e-test',
    entity_type: 'Company',
    name: 'TSMC',
    canonical_name: 'tsmc',
    tags: ['semiconductor', 'foundry'],
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-06-01T00:00:00Z',
    ...overrides,
  };
}

describe('EntityCard', () => {
  it('renders entity name', () => {
    render(<EntityCard entity={makeEntity()} />);
    expect(screen.getByText('TSMC')).toBeInTheDocument();
  });

  it('renders entity type badge', () => {
    render(<EntityCard entity={makeEntity()} />);
    expect(screen.getByText('Company')).toBeInTheDocument();
  });

  it('renders tags', () => {
    render(<EntityCard entity={makeEntity()} />);
    expect(screen.getByText('semiconductor')).toBeInTheDocument();
    expect(screen.getByText('foundry')).toBeInTheDocument();
  });

  it('renders explore link', () => {
    render(<EntityCard entity={makeEntity()} />);
    const link = screen.getByText('Explore connections →');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-test');
  });

  it('renders neighbor count when provided', () => {
    render(<EntityCard entity={makeEntity()} neighborCount={12} />);
    expect(screen.getByText('12 connections')).toBeInTheDocument();
  });

  it('renders compact variant', () => {
    render(<EntityCard entity={makeEntity()} compact />);
    expect(screen.getByText('TSMC')).toBeInTheDocument();
    // Compact variant should be a link
    expect(screen.getByText('TSMC').closest('a')).toHaveAttribute(
      'href',
      '/knowledge-graph/entity/e-test',
    );
  });

  it('shows canonical name when different from name', () => {
    render(<EntityCard entity={makeEntity({ canonical_name: 'taiwan_semiconductor' })} />);
    expect(screen.getByText(/aka taiwan_semiconductor/)).toBeInTheDocument();
  });

  it('does not show canonical name when same as name', () => {
    render(<EntityCard entity={makeEntity({ canonical_name: 'TSMC' })} />);
    expect(screen.queryByText(/aka/)).not.toBeInTheDocument();
  });

  it('renders different entity type icons', () => {
    render(<EntityCard entity={makeEntity({ entity_type: 'Facility' })} />);
    expect(screen.getByText('Facility')).toBeInTheDocument();
  });

  it('handles empty tags array', () => {
    render(<EntityCard entity={makeEntity({ tags: [] })} />);
    expect(screen.queryByText('semiconductor')).not.toBeInTheDocument();
  });

  it('renders created date', () => {
    render(<EntityCard entity={makeEntity()} />);
    // Should show date from created_at
    expect(screen.getByText(/Added/)).toBeInTheDocument();
  });
});
