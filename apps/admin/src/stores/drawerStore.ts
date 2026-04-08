import { create } from 'zustand';
import type { Station } from '@/types/station';

interface DrawerState {
  taskDrawerOpen: boolean;
  taskDetailDrawerOpen: boolean;
  taskDetailDrawerTaskId: number | null;
  stationDrawerOpen: boolean;
  stationDrawerData: Station | null;
  openTaskDrawer: () => void;
  closeTaskDrawer: () => void;
  openTaskDetailDrawer: (taskId: number) => void;
  closeTaskDetailDrawer: () => void;
  openStationDrawer: (station: Station) => void;
  closeStationDrawer: () => void;
}

export const useDrawerStore = create<DrawerState>()((set) => ({
  taskDrawerOpen: false,
  taskDetailDrawerOpen: false,
  taskDetailDrawerTaskId: null,
  stationDrawerOpen: false,
  stationDrawerData: null,
  openTaskDrawer: () =>
    set({ taskDrawerOpen: true, taskDetailDrawerOpen: false, stationDrawerOpen: false }),
  closeTaskDrawer: () => set({ taskDrawerOpen: false }),
  openTaskDetailDrawer: (taskId) =>
    set({
      taskDetailDrawerOpen: true,
      taskDetailDrawerTaskId: taskId,
      taskDrawerOpen: false,
      stationDrawerOpen: false,
    }),
  closeTaskDetailDrawer: () =>
    set({ taskDetailDrawerOpen: false, taskDetailDrawerTaskId: null }),
  openStationDrawer: (station) =>
    set({
      stationDrawerOpen: true,
      stationDrawerData: station,
      taskDrawerOpen: false,
      taskDetailDrawerOpen: false,
    }),
  closeStationDrawer: () => set({ stationDrawerOpen: false, stationDrawerData: null }),
}));
