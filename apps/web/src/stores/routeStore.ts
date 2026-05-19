import { create } from 'zustand';
import type {
  JourneyAvailableFacets,
  JourneyDisplaySortMode,
  JourneyViewResult,
} from '@/services/routeService';
import type { Route, RouteList, SeatClass, TrainSegment } from '@/types/route';
import { isTransfer } from '@/types/route';
import { sortRoutesForDisplay } from '@/pages/JourneyPage/routeList.helpers';
import type { PriceCacheEntry } from '@/stores/priceStore';

const SEAT_LABELS: Record<string, string> = {
  swz: '商务座',
  tz: '特等座',
  zy: '一等座',
  ze: '二等座',
  gr: '高级软卧',
  rw: '软卧',
  yw: '硬卧',
  yz: '硬座',
  wz: '无座',
  gg: '其他',
};

function priceMapKey(trainNo: string, fromStation: string, toStation: string): string {
  return `${trainNo}:${fromStation}:${toStation}`;
}

function buildSeats(entry: PriceCacheEntry): SeatClass[] {
  return entry.seats.map((s) => ({
    type: s.seat_type,
    label: SEAT_LABELS[s.seat_type.toLowerCase()] ?? s.seat_type.toUpperCase(),
    price: s.price,
    available: s.available,
    availabilityText: s.status || undefined,
  }));
}

function applyPricesToRoute(
  route: Route,
  priceMap: Record<string, PriceCacheEntry>,
): Route {
  const updatedSegs = route.segs.map((seg) => {
    if (isTransfer(seg)) return seg;
    const trainSeg = seg as TrainSegment;
    const key = priceMapKey(trainSeg.trainNo, trainSeg.origin.name, trainSeg.destination.name);
    const entry = priceMap[key];
    if (!entry) return trainSeg; // no update, keep current state
    if (entry.failed) {
      return { ...trainSeg, ticketStatus: 'unavailable' as const, seats: [] };
    }
    return {
      ...trainSeg,
      ticketStatus: 'ready' as const,
      seats: buildSeats(entry),
    };
  });

  // Derive route-level ticketStatus from segments
  const segStatuses = updatedSegs
    .filter((s) => !isTransfer(s))
    .map((s) => (s as TrainSegment).ticketStatus ?? 'loading');

  let routeStatus: Route['ticketStatus'];
  const unique = new Set(segStatuses);
  if (unique.size === 1 && unique.has('ready')) {
    routeStatus = 'ready';
  } else if (unique.size === 1 && unique.has('loading')) {
    routeStatus = 'loading';
  } else if (unique.has('ready') || unique.has('loading')) {
    routeStatus = 'partial';
  } else if (unique.size === 1 && unique.has('disabled')) {
    routeStatus = 'disabled';
  } else {
    routeStatus = 'unavailable';
  }

  return { ...route, segs: updatedSegs, ticketStatus: routeStatus };
}

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
  updateRoutesPrices: (priceMap: Record<string, PriceCacheEntry>) => void;
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
  updateRoutesPrices: (priceMap) =>
    set((state) => {
      const updatedRoutes = state.routes.map((route) =>
        applyPricesToRoute(route, priceMap),
      );
      const updatedSelected = state.selectedRoute
        ? updatedRoutes.find((r) => r.id === state.selectedRoute?.id) ?? null
        : null;
      return {
        routes: updatedRoutes,
        selectedRoute: updatedSelected,
      };
    }),
}));
