/**
 * Tests for useMKGQueries hooks.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { mkgKeys, useEntity, useEntitySearch, useGraphHealth, useAlerts, useEntityLineage } from '@/hooks/useMKGQueries';
import type { ReactNode } from 'react';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    getEntity: vi.fn(),
    listEntities: vi.fn(),
    searchEntities: vi.fn(),
    listEdges: vi.fn(),
    getNeighbors: vi.fn(),
    getSubgraph: vi.fn(),
    getGraphHealth: vi.fn(),
    runPropagation: vi.fn(),
    listAlerts: vi.fn(),
    getEntityLineage: vi.fn(),
  },
}));

import { mkgApi } from '@/lib/mkg-api';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('mkgKeys', () => {
  it('generates correct key hierarchy', () => {
    expect(mkgKeys.all).toEqual(['mkg']);
    expect(mkgKeys.entities()).toEqual(['mkg', 'entities']);
    expect(mkgKeys.entityDetail('e-1')).toEqual(['mkg', 'entities', 'e-1']);
    expect(mkgKeys.health()).toEqual(['mkg', 'graph', 'health']);
    expect(mkgKeys.subgraph('e-1', 2)).toEqual(['mkg', 'graph', 'subgraph', 'e-1', 2]);
    expect(mkgKeys.alerts(10)).toEqual(['mkg', 'alerts', { limit: 10 }]);
    expect(mkgKeys.lineage('e-1')).toEqual(['mkg', 'lineage', 'e-1']);
  });
});

describe('useEntity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches entity by ID', async () => {
    const mockEntity = { id: 'e-1', name: 'TSMC', entity_type: 'Company' };
    (mkgApi.getEntity as ReturnType<typeof vi.fn>).mockResolvedValue(mockEntity);

    const { result } = renderHook(() => useEntity('e-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEntity);
    expect(mkgApi.getEntity).toHaveBeenCalledWith('e-1');
  });

  it('does not fetch when entityId is empty', () => {
    renderHook(() => useEntity(''), {
      wrapper: createWrapper(),
    });

    expect(mkgApi.getEntity).not.toHaveBeenCalled();
  });
});

describe('useEntitySearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('searches when query length >= 2', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { result } = renderHook(() => useEntitySearch('TS'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mkgApi.searchEntities).toHaveBeenCalledWith('TS', undefined);
  });

  it('does not search when query too short', () => {
    renderHook(() => useEntitySearch('T'), {
      wrapper: createWrapper(),
    });

    expect(mkgApi.searchEntities).not.toHaveBeenCalled();
  });
});

describe('useGraphHealth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches health data', async () => {
    const mockHealth = { status: 'healthy', entity_count: 48, edge_count: 49, backend: 'sqlite' };
    (mkgApi.getGraphHealth as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealth);

    const { result } = renderHook(() => useGraphHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockHealth);
  });
});

describe('useAlerts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches alerts with default limit', async () => {
    (mkgApi.listAlerts as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { result } = renderHook(() => useAlerts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mkgApi.listAlerts).toHaveBeenCalledWith(10);
  });

  it('fetches alerts with custom limit', async () => {
    (mkgApi.listAlerts as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { result } = renderHook(() => useAlerts(50), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mkgApi.listAlerts).toHaveBeenCalledWith(50);
  });
});

describe('useEntityLineage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches lineage data', async () => {
    const mockLineage = {
      entity_id: 'e-1',
      source_articles: ['art-1'],
      highest_confidence: 0.9,
      extraction_tiers_used: ['tier_1'],
      data_sources: [],
    };
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue(mockLineage);

    const { result } = renderHook(() => useEntityLineage('e-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockLineage);
  });
});
