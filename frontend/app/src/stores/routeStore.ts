import { create } from 'zustand';
import type { Route, RouteList } from '@/types/route';

interface RouteState {
  routes: RouteList;
  selectedRoute: Route | null;
  setRoutes: (routes: RouteList) => void;
  selectRoute: (route: Route | null) => void;
}

export const useRouteStore = create<RouteState>()((set) => ({
  routes: [],
  selectedRoute: null,
  setRoutes: (routes) => set({ routes }),
  selectRoute: (selectedRoute) => set({ selectedRoute }),
}));
