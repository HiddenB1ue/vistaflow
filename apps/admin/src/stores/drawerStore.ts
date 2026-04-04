import { create } from 'zustand';
import type { Station } from '@/types/station';

interface DrawerState {
  taskDrawerOpen: boolean;
  stationDrawerOpen: boolean;
  stationDrawerData: Station | null;
  openTaskDrawer: () => void;
  closeTaskDrawer: () => void;
  openStationDrawer: (station: Station) => void;
  closeStationDrawer: () => void;
}

export const useDrawerStore = create<DrawerState>()((set) => ({
  taskDrawerOpen: false,
  stationDrawerOpen: false,
  stationDrawerData: null,
  openTaskDrawer: () => set({ taskDrawerOpen: true, stationDrawerOpen: false }),
  closeTaskDrawer: () => set({ taskDrawerOpen: false }),
  openStationDrawer: (station) =>
    set({ stationDrawerOpen: true, stationDrawerData: station, taskDrawerOpen: false }),
  closeStationDrawer: () => set({ stationDrawerOpen: false, stationDrawerData: null }),
}));
