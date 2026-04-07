/**
 * Tests for MKG graph store (Zustand).
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useGraphStore } from '@/store/graphStore';

describe('graphStore', () => {
  beforeEach(() => {
    useGraphStore.getState().reset();
  });

  it('starts with null selected entity', () => {
    const state = useGraphStore.getState();
    expect(state.selectedEntityId).toBeNull();
    expect(state.selectedEntity).toBeNull();
  });

  it('sets selected entity', () => {
    const entity = {
      id: 'e1',
      entity_type: 'Company',
      name: 'TSMC',
      canonical_name: 'tsmc',
      tags: ['semiconductor'],
      created_at: null,
      updated_at: null,
    };
    useGraphStore.getState().setSelectedEntity(entity);
    const state = useGraphStore.getState();
    expect(state.selectedEntityId).toBe('e1');
    expect(state.selectedEntity?.name).toBe('TSMC');
  });

  it('clears selected entity with null', () => {
    useGraphStore.getState().setSelectedEntity({
      id: 'e1', entity_type: 'Company', name: 'X',
      canonical_name: 'x', tags: [], created_at: null, updated_at: null,
    });
    useGraphStore.getState().setSelectedEntity(null);
    expect(useGraphStore.getState().selectedEntityId).toBeNull();
  });

  it('manages search state', () => {
    useGraphStore.getState().setSearchQuery('TSMC');
    expect(useGraphStore.getState().searchQuery).toBe('TSMC');

    useGraphStore.getState().setSearchLoading(true);
    expect(useGraphStore.getState().searchLoading).toBe(true);

    useGraphStore.getState().setSearchResults([]);
    expect(useGraphStore.getState().searchResults).toEqual([]);
  });

  it('manages simulation state', () => {
    expect(useGraphStore.getState().isSimulating).toBe(false);
    useGraphStore.getState().setIsSimulating(true);
    expect(useGraphStore.getState().isSimulating).toBe(true);
  });

  it('manages filters with partial updates', () => {
    useGraphStore.getState().setFilters({ entityTypes: ['Company'] });
    expect(useGraphStore.getState().filters.entityTypes).toEqual(['Company']);
    expect(useGraphStore.getState().filters.confidenceRange).toEqual([0, 1]);

    useGraphStore.getState().setFilters({ confidenceRange: [0.5, 1] });
    expect(useGraphStore.getState().filters.entityTypes).toEqual(['Company']);
    expect(useGraphStore.getState().filters.confidenceRange).toEqual([0.5, 1]);
  });

  it('resets filters to defaults', () => {
    useGraphStore.getState().setFilters({ entityTypes: ['Company', 'Facility'] });
    useGraphStore.getState().resetFilters();
    expect(useGraphStore.getState().filters.entityTypes).toEqual([]);
    expect(useGraphStore.getState().filters.confidenceRange).toEqual([0, 1]);
  });

  it('manages breadcrumbs push and pop', () => {
    useGraphStore.getState().pushBreadcrumb({ id: 'e1', name: 'TSMC' });
    useGraphStore.getState().pushBreadcrumb({ id: 'e2', name: 'Apple' });
    expect(useGraphStore.getState().breadcrumbs).toHaveLength(2);
    expect(useGraphStore.getState().breadcrumbs[1].name).toBe('Apple');

    useGraphStore.getState().popBreadcrumb();
    expect(useGraphStore.getState().breadcrumbs).toHaveLength(1);
    expect(useGraphStore.getState().breadcrumbs[0].name).toBe('TSMC');
  });

  it('truncates breadcrumbs on revisiting earlier node', () => {
    useGraphStore.getState().pushBreadcrumb({ id: 'e1', name: 'TSMC' });
    useGraphStore.getState().pushBreadcrumb({ id: 'e2', name: 'Apple' });
    useGraphStore.getState().pushBreadcrumb({ id: 'e3', name: 'Foxconn' });
    // Go back to Apple — truncate Foxconn
    useGraphStore.getState().pushBreadcrumb({ id: 'e2', name: 'Apple' });
    expect(useGraphStore.getState().breadcrumbs).toHaveLength(2);
    expect(useGraphStore.getState().breadcrumbs[1].name).toBe('Apple');
  });

  it('resets all state', () => {
    useGraphStore.getState().setSearchQuery('test');
    useGraphStore.getState().setIsSimulating(true);
    useGraphStore.getState().pushBreadcrumb({ id: 'e1', name: 'X' });
    useGraphStore.getState().setFilters({ entityTypes: ['Company'] });
    useGraphStore.getState().setDrawerEntityId('e2');
    useGraphStore.getState().setImpactOverlay(new Map([['e1', 0.5]]));
    useGraphStore.getState().setShowImpactOverlay(false);

    useGraphStore.getState().reset();

    const state = useGraphStore.getState();
    expect(state.searchQuery).toBe('');
    expect(state.isSimulating).toBe(false);
    expect(state.breadcrumbs).toEqual([]);
    expect(state.filters.entityTypes).toEqual([]);
    expect(state.selectedEntity).toBeNull();
    expect(state.drawerEntityId).toBeNull();
    expect(state.impactOverlay).toBeNull();
    expect(state.showImpactOverlay).toBe(true);
  });

  it('manages drawer entity state', () => {
    expect(useGraphStore.getState().drawerEntityId).toBeNull();

    useGraphStore.getState().setDrawerEntityId('e1');
    expect(useGraphStore.getState().drawerEntityId).toBe('e1');

    useGraphStore.getState().setDrawerEntityId(null);
    expect(useGraphStore.getState().drawerEntityId).toBeNull();
  });

  it('manages impact overlay state', () => {
    expect(useGraphStore.getState().impactOverlay).toBeNull();
    expect(useGraphStore.getState().showImpactOverlay).toBe(true);

    const overlay = new Map([['e1', 0.8], ['e2', 0.3]]);
    useGraphStore.getState().setImpactOverlay(overlay);
    expect(useGraphStore.getState().impactOverlay).toEqual(overlay);

    useGraphStore.getState().setShowImpactOverlay(false);
    expect(useGraphStore.getState().showImpactOverlay).toBe(false);

    useGraphStore.getState().setImpactOverlay(null);
    expect(useGraphStore.getState().impactOverlay).toBeNull();
  });
});
