import { create } from 'zustand';
import type {
  JourneyAvailableFacets,
  JourneyDisplaySortMode,
  JourneyViewResult,
} from '@/services/routeService';
import type { Route, RouteList } from '@/types/route';
import { sortRoutesForDisplay } from '@/pages/JourneyPage/routeList.helpers';

interface RouteState {
  routes: RouteList;
  selectedRoute: Route | null;
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  sortMode: JourneyDisplaySortMode;
  appliedView: JourneyViewResult['appliedView'] | null;
  availableFacets: JourneyAvailableFacets;
  sessionSearchId: string | null;
  setViewResult: (searchId: string, result: JourneyViewResult) => void;
  selectRoute: (route: Route | null) => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setSortMode: (sortMode: JourneyDisplaySortMode) => void;
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
      const displaySortMode = state.sortMode;
      // For "price" sort, trust backend ordering; for others, sort locally
      const sortedRoutes =
        displaySortMode === 'price'
          ? result.items
          : sortRoutesForDisplay(result.items, displaySortMode);
      const matchedSelectedRoute =
        sortedRoutes.find((route) => route.id === state.selectedRoute?.id) ?? null;
      return {
        sessionSearchId,
        routes: sortedRoutes,
        selectedRoute: matchedSelectedRoute ?? sortedRoutes[0] ?? null,
        total: result.total,
        page: result.page,
        pageSize: result.pageSize,
        totalPages: result.totalPages,
        sortMode: displaySortMode,
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
  setSortMode: (sortMode) =>
    set((state) => {
      // For "price" sort, don't re-sort locally — the backend handles it.
      // The component will trigger a new get_view call with sort_by="price".
      if (sortMode === 'price') {
        return { sortMode };
      }
      const sortedRoutes = sortRoutesForDisplay(state.routes, sortMode);
      const matchedSelectedRoute =
        sortedRoutes.find((route) => route.id === state.selectedRoute?.id) ?? null;
      return {
        sortMode,
        routes: sortedRoutes,
        selectedRoute: matchedSelectedRoute ?? sortedRoutes[0] ?? null,
      };
    }),
}));

