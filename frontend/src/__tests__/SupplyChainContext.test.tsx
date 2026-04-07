/**
 * Tests for SupplyChainContext component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SupplyChainContext } from '@/components/graph/SupplyChainContext';
import { useGraphStore } from '@/store/graphStore';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    searchEntities: vi.fn(),
    getNeighbors: vi.fn(),
  },
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock EntityDrawer
vi.mock('@/components/graph/EntityDrawer', () => ({
  EntityDrawer: () => <div data-testid="entity-drawer" />,
}));

import { mkgApi } from '@/lib/mkg-api';

const mockEntity = {
  id: 'e-tcs',
  entity_type: 'Company',
  name: 'TCS',
  canonical_name: 'Tata Consultancy Services',
  tags: ['IT', 'services'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

const mockNeighbors = [
  { id: 'e-infosys', entity_type: 'Company', name: 'Infosys', canonical_name: 'Infosys', tags: [], created_at: null, updated_at: null },
  { id: 'e-wipro', entity_type: 'Company', name: 'Wipro', canonical_name: 'Wipro', tags: [], created_at: null, updated_at: null },
];

describe('SupplyChainContext', () => {
  beforeEach(() => {
    useGraphStore.getState().reset();
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    render(<SupplyChainContext symbol="TCS" />);

    // Should show loading skeleton
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('shows matched entity and neighbors', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue(mockNeighbors);

    render(<SupplyChainContext symbol="TCS" />);

    await waitFor(() => {
      expect(screen.getByText('TCS')).toBeInTheDocument();
    });

    expect(screen.getAllByText('Company').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Infosys')).toBeInTheDocument();
    expect(screen.getByText('Wipro')).toBeInTheDocument();
    expect(screen.getByText('2 connections')).toBeInTheDocument();
  });

  it('shows not found when no entity matches', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    render(<SupplyChainContext symbol="UNKNOWN" />);

    await waitFor(() => {
      expect(screen.getByText(/No supply chain data found for UNKNOWN/)).toBeInTheDocument();
    });
  });

  it('normalizes .NS suffix for Indian stocks', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    render(<SupplyChainContext symbol="TCS.NS" />);

    await waitFor(() => {
      expect(mkgApi.searchEntities).toHaveBeenCalledWith('TCS', undefined, 5);
    });
  });

  it('normalizes USDT suffix for crypto', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    render(<SupplyChainContext symbol="BTCUSDT" marketType="crypto" />);

    await waitFor(() => {
      expect(mkgApi.searchEntities).toHaveBeenCalledWith('BTC', undefined, 5);
    });
  });

  it('shows full graph link', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue(mockNeighbors);

    render(<SupplyChainContext symbol="TCS" />);

    await waitFor(() => {
      expect(screen.getByText('View Full Graph →')).toBeInTheDocument();
    });

    const link = screen.getByText('View Full Graph →');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph/entity/e-tcs');
  });

  it('shows impact sim link', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue(mockNeighbors);

    render(<SupplyChainContext symbol="TCS" />);

    await waitFor(() => {
      expect(screen.getByText('⚡ Run Impact Sim')).toBeInTheDocument();
    });
  });

  it('opens drawer when clicking a neighbor', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.getNeighbors as ReturnType<typeof vi.fn>).mockResolvedValue(mockNeighbors);

    render(<SupplyChainContext symbol="TCS" />);

    await waitFor(() => {
      expect(screen.getByText('Infosys')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Infosys'));

    expect(useGraphStore.getState().drawerEntityId).toBe('e-infosys');
  });
});
