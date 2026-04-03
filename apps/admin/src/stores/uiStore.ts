import { create } from 'zustand';
import type { Station } from '@/types/station';

export type ToastType = 'success' | 'error' | 'info' | 'warn';

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface UiState {
  taskDrawerOpen: boolean;
  stationDrawerOpen: boolean;
  stationDrawerData: Station | null;
  previewModalOpen: boolean;
  toasts: ToastItem[];
  openTaskDrawer: () => void;
  closeTaskDrawer: () => void;
  openStationDrawer: (station: Station) => void;
  closeStationDrawer: () => void;
  openPreviewModal: () => void;
  closePreviewModal: () => void;
  addToast: (message: string, type: ToastType) => void;
  removeToast: (id: string) => void;
}

let toastCounter = 0;

export const useUiStore = create<UiState>()((set) => ({
  taskDrawerOpen: false,
  stationDrawerOpen: false,
  stationDrawerData: null,
  previewModalOpen: false,
  toasts: [],
  openTaskDrawer: () => set({ taskDrawerOpen: true, stationDrawerOpen: false }),
  closeTaskDrawer: () => set({ taskDrawerOpen: false }),
  openStationDrawer: (station) =>
    set({ stationDrawerOpen: true, stationDrawerData: station, taskDrawerOpen: false }),
  closeStationDrawer: () => set({ stationDrawerOpen: false, stationDrawerData: null }),
  openPreviewModal: () => set({ previewModalOpen: true }),
  closePreviewModal: () => set({ previewModalOpen: false }),
  addToast: (message, type) =>
    set((state) => ({
      toasts: [...state.toasts, { id: `toast-${++toastCounter}`, message, type }],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
