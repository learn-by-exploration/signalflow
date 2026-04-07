/**
 * Tests for EntityDrawer component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EntityDrawer } from '@/components/graph/EntityDrawer';
import { useGraphStore } from '@/store/graphStore';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    getEntity: vi.fn(),
    listEdges: vi.fn(),
    getNeighbors: vi.fn(),
  },
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: () => void }) => (
    <a href={href} onClick={onClick}>{children}</a>
  ),
}));

import { mkgApi } from '@/lib/mkg-api';

const mockEntity = {
  id: 'e-tsmc',
  entity_type: 'Company',
  name: 'TSMC',
  canonical_name: 'Taiwan Semiconductor',
  tags: ['semiconductor', 'foundry'],
  created_at: '2024-01-15T00:00:00Z',
  updated_at: null,
};

const mockEdge = {
  id: 'edge-1',
  source_id: 'e-tsmc',
  target_id: 'e-apple',
  relation_type: 'supplies_to',
  weight: 0.9,
  confidence: 0.85,
  direction: 'outgoing',
  tags: [],
  valid_from: null,
  valid_until: null,
  created_at: '2024-01-15T00:00:00Z',
  updated_at: null,
};

const mockNeighbor = {
  id: 'e-apple',
  entity_type: 'Company',
  name: 'Apple',
  canonical_name: 'Apple Inc.',
  tags: ['tech'],
  created_at: '2024-01-15T00:00:00Z',
  updated_at: null,
};

function setupMocks() {
  (mkgApi.getEntity as ReturnType<typeof vi.fn>).mockResolvedValue(mockEntity);
  (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue([mockEdge]);
  (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue([mockNeighbor]);
}

describe('EntityDrawer', () => {
  beforeEach(() => {
    useGraphStore.getState().reset();
    vi.clearAllMocks();
  });

  it('renders nothing when drawer is closed', () => {
    const { container } = render(<EntityDrawer />);
    expect(container.querySelector('[role="dialog"]')).toBeNull();
  });

  it('renders entity details when open', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getAllByText('TSMC').length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getByText('Company')).toBeInTheDocument();
    expect(screen.getByText(/aka Taiwan Semiconductor/)).toBeInTheDocument();
    expect(screen.getByText('semiconductor')).toBeInTheDocument();
    expect(screen.getByText('foundry')).toBeInTheDocument();
  });

  it('shows loading state initially', async () => {
    // Set up a delayed mock
    (mkgApi.getEntity as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockEntity), 100)),
    );
    (mkgApi.listEdges as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);
    // Should show loading skeleton
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('shows top relationships', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getByText('Top Relationships')).toBeInTheDocument();
    });

    expect(screen.getByText('supplies to')).toBeInTheDocument();
    expect(screen.getByText('Weight: 90%')).toBeInTheDocument();
  });

  it('closes on close button click', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getAllByText('TSMC').length).toBeGreaterThanOrEqual(1);
    });

    const closeButtons = screen.getAllByLabelText('Close drawer');
    await userEvent.click(closeButtons[0]);

    expect(useGraphStore.getState().drawerEntityId).toBeNull();
  });

  it('closes on escape key', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getAllByText('TSMC').length).toBeGreaterThanOrEqual(1);
    });

    await userEvent.keyboard('{Escape}');

    expect(useGraphStore.getState().drawerEntityId).toBeNull();
  });

  it('shows link to full entity page', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getByText('Open Full Page')).toBeInTheDocument();
    });

    const link = screen.getByText('Open Full Page');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-tsmc');
  });

  it('shows connection count', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getByText('1 connections')).toBeInTheDocument();
    });
  });

  it('navigates to different entity when clicking relationship', async () => {
    setupMocks();
    act(() => {
      useGraphStore.getState().setDrawerEntityId('e-tsmc');
    });

    render(<EntityDrawer />);

    await waitFor(() => {
      expect(screen.getByText('Top Relationships')).toBeInTheDocument();
    });

    // Click on the neighbor entity in relationships
    const appleButton = screen.getByText('Apple');
    await userEvent.click(appleButton);

    expect(useGraphStore.getState().drawerEntityId).toBe('e-apple');
  });
});
