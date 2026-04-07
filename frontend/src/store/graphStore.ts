/**
 * Zustand store for MKG graph state.
 */

import { create } from 'zustand';
import type {
  MKGEntity,
  MKGSubgraph,
  PropagationResult,
  MKGAlert,
  GraphFilters,
} from '@/lib/mkg-types';

interface GraphState {
  // Selected entity
  selectedEntityId: string | null;
  selectedEntity: MKGEntity | null;

  // Subgraph around selected entity
  subgraph: MKGSubgraph | null;
  subgraphLoading: boolean;

  // Search
  searchQuery: string;
  searchResults: MKGEntity[];
  searchLoading: boolean;

  // Impact simulation
  simulationResult: PropagationResult | null;
  isSimulating: boolean;

  // Alerts
  alerts: MKGAlert[];

  // Filters
  filters: GraphFilters;

  // Breadcrumb trail
  breadcrumbs: { id: string; name: string }[];

  // Entity drawer (T1.2)
  drawerEntityId: string | null;

  // Impact overlay (T1.3)
  impactOverlay: Map<string, number> | null;
  showImpactOverlay: boolean;

  // Actions
  setSelectedEntity: (entity: MKGEntity | null) => void;
  setSubgraph: (sg: MKGSubgraph | null) => void;
  setSubgraphLoading: (loading: boolean) => void;
  setSearchQuery: (q: string) => void;
  setSearchResults: (results: MKGEntity[]) => void;
  setSearchLoading: (loading: boolean) => void;
  setSimulationResult: (result: PropagationResult | null) => void;
  setIsSimulating: (s: boolean) => void;
  setAlerts: (alerts: MKGAlert[]) => void;
  setFilters: (filters: Partial<GraphFilters>) => void;
  resetFilters: () => void;
  pushBreadcrumb: (entry: { id: string; name: string }) => void;
  popBreadcrumb: () => void;
  resetBreadcrumbs: () => void;
  setDrawerEntityId: (id: string | null) => void;
  setImpactOverlay: (overlay: Map<string, number> | null) => void;
  setShowImpactOverlay: (show: boolean) => void;
  reset: () => void;
}

const DEFAULT_FILTERS: GraphFilters = {
  entityTypes: [],
  relationTypes: [],
  confidenceRange: [0, 1],
  tags: [],
};

export const useGraphStore = create<GraphState>((set) => ({
  selectedEntityId: null,
  selectedEntity: null,
  subgraph: null,
  subgraphLoading: false,
  searchQuery: '',
  searchResults: [],
  searchLoading: false,
  simulationResult: null,
  isSimulating: false,
  alerts: [],
  filters: { ...DEFAULT_FILTERS },
  breadcrumbs: [],
  drawerEntityId: null,
  impactOverlay: null,
  showImpactOverlay: true,

  setSelectedEntity: (entity) =>
    set({ selectedEntity: entity, selectedEntityId: entity?.id ?? null }),

  setSubgraph: (sg) => set({ subgraph: sg }),
  setSubgraphLoading: (loading) => set({ subgraphLoading: loading }),

  setSearchQuery: (q) => set({ searchQuery: q }),
  setSearchResults: (results) => set({ searchResults: results }),
  setSearchLoading: (loading) => set({ searchLoading: loading }),

  setSimulationResult: (result) => set({ simulationResult: result }),
  setIsSimulating: (s) => set({ isSimulating: s }),

  setAlerts: (alerts) => set({ alerts }),

  setFilters: (partial) =>
    set((state) => ({ filters: { ...state.filters, ...partial } })),

  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),

  pushBreadcrumb: (entry) =>
    set((state) => {
      const existing = state.breadcrumbs.findIndex((b) => b.id === entry.id);
      if (existing >= 0) {
        return { breadcrumbs: state.breadcrumbs.slice(0, existing + 1) };
      }
      return { breadcrumbs: [...state.breadcrumbs, entry] };
    }),

  popBreadcrumb: () =>
    set((state) => ({
      breadcrumbs: state.breadcrumbs.slice(0, -1),
    })),

  resetBreadcrumbs: () => set({ breadcrumbs: [] }),

  setDrawerEntityId: (id) => set({ drawerEntityId: id }),

  setImpactOverlay: (overlay) => set({ impactOverlay: overlay }),
  setShowImpactOverlay: (show) => set({ showImpactOverlay: show }),

  reset: () =>
    set({
      selectedEntityId: null,
      selectedEntity: null,
      subgraph: null,
      subgraphLoading: false,
      searchQuery: '',
      searchResults: [],
      searchLoading: false,
      simulationResult: null,
      isSimulating: false,
      filters: { ...DEFAULT_FILTERS },
      breadcrumbs: [],
      drawerEntityId: null,
      impactOverlay: null,
      showImpactOverlay: true,
    }),
}));
