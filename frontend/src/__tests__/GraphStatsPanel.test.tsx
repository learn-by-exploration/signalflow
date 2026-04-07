/**
 * Tests for GraphStatsPanel component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { GraphStatsPanel } from '@/components/graph/GraphStatsPanel';
import { useGraphStore } from '@/store/graphStore';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    getGraphHealth: vi.fn(),
    listEntities: vi.fn(),
    listEdges: vi.fn(),
  },
}));

import { mkgApi } from '@/lib/mkg-api';

const mockHealth = {
  status: 'healthy',
  backend: 'sqlite',
  entity_count: 48,
  edge_count: 49,
};

const mockEntities = [
  { id: 'e-1', entity_type: 'Company', name: 'TSMC', canonical_name: 'TSMC', tags: [], created_at: null, updated_at: null },
  { id: 'e-2', entity_type: 'Company', name: 'Apple', canonical_name: 'Apple', tags: [], created_at: null, updated_at: null },
  { id: 'e-3', entity_type: 'Sector', name: 'Indian IT', canonical_name: 'Indian IT', tags: [], created_at: null, updated_at: null },
  { id: 'e-4', entity_type: 'Country', name: 'India', canonical_name: 'India', tags: [], created_at: null, updated_at: null },
];

const mockEdges = [
  { id: 'edge-1', source_id: 'e-1', target_id: 'e-2', relation_type: 'supplies_to', weight: 0.9, confidence: 0.85, direction: 'outgoing', tags: [], valid_from: null, valid_until: null, created_at: null, updated_at: null },
  { id: 'edge-2', source_id: 'e-2', target_id: 'e-3', relation_type: 'belongs_to', weight: 0.7, confidence: 0.95, direction: 'outgoing', tags: [], valid_from: null, valid_until: null, created_at: null, updated_at: null },
  { id: 'edge-3', source_id: 'e-3', target_id: 'e-4', relation_type: 'headquartered_in', weight: 0.8, confidence: 0.9, direction: 'outgoing', tags: [], valid_from: null, valid_until: null, created_at: null, updated_at: null },
];

describe('GraphStatsPanel', () => {
  beforeEach(() => {
    useGraphStore.getState().reset();
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}),
    );
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}),
    );
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}),
    );

    const { container } = render(<GraphStatsPanel />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('displays overview stat cards', async () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealth);
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockEntities,
      meta: { count: 4 },
    });
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdges);

    render(<GraphStatsPanel />);

    await waitFor(() => {
      expect(screen.getByText('48')).toBeInTheDocument();
    });

    expect(screen.getByText('49')).toBeInTheDocument();
    expect(screen.getByText('Entities')).toBeInTheDocument();
    expect(screen.getByText('Connections')).toBeInTheDocument();
    expect(screen.getByText('Avg Confidence')).toBeInTheDocument();
    expect(screen.getByText('Avg Weight')).toBeInTheDocument();
  });

  it('displays entity type breakdown', async () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealth);
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockEntities,
      meta: { count: 4 },
    });
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdges);

    render(<GraphStatsPanel />);

    await waitFor(() => {
      expect(screen.getByText('Entity Types')).toBeInTheDocument();
    });

    expect(screen.getByText('Company')).toBeInTheDocument();
    expect(screen.getByText('Sector')).toBeInTheDocument();
    expect(screen.getByText('Country')).toBeInTheDocument();
  });

  it('displays relation type breakdown', async () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealth);
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockEntities,
      meta: { count: 4 },
    });
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdges);

    render(<GraphStatsPanel />);

    await waitFor(() => {
      expect(screen.getByText('Relation Types')).toBeInTheDocument();
    });

    expect(screen.getByText('supplies to')).toBeInTheDocument();
    expect(screen.getByText('belongs to')).toBeInTheDocument();
    expect(screen.getByText('headquartered in')).toBeInTheDocument();
  });

  it('displays most connected entities', async () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealth);
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockEntities,
      meta: { count: 4 },
    });
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue(mockEdges);

    render(<GraphStatsPanel />);

    await waitFor(() => {
      expect(screen.getByText('Most Connected')).toBeInTheDocument();
    });

    // All entities connected: e-2 (Apple) has 2 edges (edge-1 target, edge-2 source), e-3 has 2 edges
    expect(screen.getByText('TSMC')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('handles API failure gracefully', async () => {
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));
    (mkgApi.listEntities as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('fail'));

    render(<GraphStatsPanel />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load graph stats.')).toBeInTheDocument();
    });
  });
});
