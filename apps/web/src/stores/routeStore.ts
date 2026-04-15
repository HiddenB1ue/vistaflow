import { create } from 'zustand';
import type {
  JourneyAvailableFacets,
  JourneySortMode,
  JourneyViewResult,
} from '@/services/routeService';
import type { Route, RouteList } from '@/types/route';

interface RouteState {
  routes: RouteList;
  selectedRoute: Route | null;
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  sortMode: JourneySortMode;
  appliedView: JourneyViewResult['appliedView'] | null;
  availableFacets: JourneyAvailableFacets;
  sessionSearchId: string | null;
  setViewResult: (searchId: string, result: JourneyViewResult) => void;
  selectRoute: (route: Route | null) => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setSortMode: (sortMode: JourneySortMode) => void;
}

const defaultAvailableFacets: JourneyAvailableFacets = {
  transferCounts: [],
  trainTypes: [],
};

export const useRouteStore = create<RouteState>()((set) => ({
  routes: [],
  selectedRoute: null,
  total: 0,
  page: 1,
  pageSize: 20,
  totalPages: 0,
  sortMode: 'duration',
  appliedView: null,
  availableFacets: { ...defaultAvailableFacets },
  sessionSearchId: null,
  setViewResult: (sessionSearchId, result) =>
    set((state) => {
      const matchedSelectedRoute =
        result.items.find((route) => route.id === state.selectedRoute?.id) ?? null;
      return {
        sessionSearchId,
        routes: result.items,
        selectedRoute: matchedSelectedRoute ?? result.items[0] ?? null,
        total: result.total,
        page: result.page,
        pageSize: result.pageSize,
        totalPages: result.totalPages,
        sortMode: result.appliedView.sortBy,
        availableFacets: {
          transferCounts: [...result.availableFacets.transferCounts],
          trainTypes: [...result.availableFacets.trainTypes],
        },
        appliedView: {
          ...result.appliedView,
          displayTrainTypes: [...result.appliedView.displayTrainTypes],
          transferCounts: [...result.appliedView.transferCounts],
        },
      };
    }),
  selectRoute: (selectedRoute) => set({ selectedRoute }),
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setSortMode: (sortMode) => set({ sortMode, page: 1 }),
}));
