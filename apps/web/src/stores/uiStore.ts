import { create } from 'zustand';
import type { Theme } from '@/types/theme';

export interface JourneyViewPrefs {
  excludeDirectTrainCodesInTransferRoutes: boolean;
  displayTrainTypes: string[];
  transferCounts: number[];
  showOnlyAvailableTickets: boolean;
}

export const defaultJourneyViewPrefs: JourneyViewPrefs = {
  excludeDirectTrainCodesInTransferRoutes: false,
  displayTrainTypes: [],
  transferCounts: [],
  showOnlyAvailableTickets: false,
};

interface UiState {
  theme: Theme;
  isTransitioning: boolean;
  isSearchFilterOpen: boolean;
  isJourneyFilterOpen: boolean;
  journeyFilterPrefs: JourneyViewPrefs;
  curtainEl: HTMLElement | null;
  setTheme: (theme: Theme) => void;
  setTransitioning: (v: boolean) => void;
  setSearchFilterOpen: (v: boolean) => void;
  setJourneyFilterOpen: (v: boolean) => void;
  setJourneyFilterPrefs: (prefs: Partial<JourneyViewPrefs>) => void;
  resetJourneyFilterPrefs: () => void;
  setCurtainEl: (el: HTMLElement | null) => void;
}

export const useUiStore = create<UiState>()((set) => ({
  theme: 'dawn',
  isTransitioning: false,
  isSearchFilterOpen: false,
  isJourneyFilterOpen: false,
  journeyFilterPrefs: { ...defaultJourneyViewPrefs },
  curtainEl: null,
  setTheme: (theme) => set({ theme }),
  setTransitioning: (isTransitioning) => set({ isTransitioning }),
  setSearchFilterOpen: (isSearchFilterOpen) => set({ isSearchFilterOpen }),
  setJourneyFilterOpen: (isJourneyFilterOpen) => set({ isJourneyFilterOpen }),
  setJourneyFilterPrefs: (prefs) =>
    set((state) => ({
      journeyFilterPrefs: {
        ...state.journeyFilterPrefs,
        ...prefs,
      },
    })),
  resetJourneyFilterPrefs: () =>
    set({ journeyFilterPrefs: { ...defaultJourneyViewPrefs } }),
  setCurtainEl: (curtainEl) => set({ curtainEl }),
}));
