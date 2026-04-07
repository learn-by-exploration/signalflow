/**
 * Tests for CausalNarratives component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CausalNarratives } from '@/components/graph/CausalNarratives';
import type { CausalChainItem } from '@/lib/mkg-types';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

function makeChain(overrides: Partial<CausalChainItem> = {}): CausalChainItem {
  return {
    trigger: 'e-tsmc',
    trigger_name: 'TSMC',
    trigger_event: 'Factory shutdown',
    affected_entity: 'e-apple',
    affected_name: 'Apple',
    impact_score: 0.72,
    hops: 2,
    path: ['TSMC', 'Foxconn', 'Apple'],
    edge_labels: ['SUPPLIES_TO', 'SUPPLIES_TO'],
    narrative: 'TSMC factory shutdown disrupts chip supply to Foxconn, which impacts Apple iPhone production.',
    ...overrides,
  };
}

describe('CausalNarratives', () => {
  it('shows empty message when no chains', () => {
    render(<CausalNarratives chains={[]} />);
    expect(screen.getByText('No causal chains generated.')).toBeInTheDocument();
  });

  it('renders narrative text', () => {
    render(<CausalNarratives chains={[makeChain()]} />);
    expect(
      screen.getByText(/TSMC factory shutdown disrupts chip supply/),
    ).toBeInTheDocument();
  });

  it('renders path breadcrumb with entity names', () => {
    render(<CausalNarratives chains={[makeChain()]} />);
    expect(screen.getByText('TSMC')).toBeInTheDocument();
    expect(screen.getByText('Foxconn')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('renders edge labels in path', () => {
    render(<CausalNarratives chains={[makeChain()]} />);
    // edge labels are rendered with underscores replaced by spaces
    const labels = screen.getAllByText(/SUPPLIES TO/);
    expect(labels.length).toBeGreaterThanOrEqual(1);
  });

  it('renders impact percentage', () => {
    render(<CausalNarratives chains={[makeChain({ impact_score: 0.72 })]} />);
    expect(screen.getByText(/Impact: 72%/)).toBeInTheDocument();
  });

  it('renders hop count', () => {
    render(<CausalNarratives chains={[makeChain({ hops: 2 })]} />);
    expect(screen.getByText(/2 hops/)).toBeInTheDocument();
  });

  it('renders singular hop label for 1 hop', () => {
    render(<CausalNarratives chains={[makeChain({ hops: 1 })]} />);
    expect(screen.getByText(/1 hop\b/)).toBeInTheDocument();
  });

  it('renders view entity link', () => {
    render(<CausalNarratives chains={[makeChain()]} />);
    const link = screen.getByText(/View Apple →/);
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-apple');
  });

  it('renders multiple chains', () => {
    const chains = [
      makeChain({ affected_entity: 'e-apple', affected_name: 'Apple' }),
      makeChain({
        affected_entity: 'e-samsung',
        affected_name: 'Samsung',
        narrative: 'Samsung affected via competitor supply chain.',
        impact_score: 0.45,
      }),
    ];
    render(<CausalNarratives chains={chains} />);
    expect(screen.getByText(/View Apple →/)).toBeInTheDocument();
    expect(screen.getByText(/View Samsung →/)).toBeInTheDocument();
  });
});
