import { create } from 'zustand';
import type { Theme } from '@/types/theme';

interface FilterPrefs {
  directOnly: boolean;
  business: boolean;
  first: boolean;
  second: boolean;
}

const defaultFilterPrefs: FilterPrefs = {
  directOnly: false,
  business: true,
  first: true,
  second: true,
};

interface UiState {
  theme: Theme;
  isTransitioning: boolean;
  isSearchFilterOpen: boolean;
  isJourneyFilterOpen: boolean;
  searchFilterPrefs: FilterPrefs;
  journeyFilterPrefs: FilterPrefs;
  curtainEl: HTMLElement | null;
  setTheme: (theme: Theme) => void;
  setTransitioning: (v: boolean) => void;
  setSearchFilterOpen: (v: boolean) => void;
  setJourneyFilterOpen: (v: boolean) => void;
  setSearchFilterPrefs: (prefs: Partial<FilterPrefs>) => void;
  setJourneyFilterPrefs: (prefs: Partial<FilterPrefs>) => void;
  setCurtainEl: (el: HTMLElement | null) => void;
}

export const useUiStore = create<UiState>()((set) => ({
  theme: 'dawn',
  isTransitioning: false,
  isSearchFilterOpen: false,
  isJourneyFilterOpen: false,
  searchFilterPrefs: { ...defaultFilterPrefs },
  journeyFilterPrefs: { ...defaultFilterPrefs },
  curtainEl: null,
  setTheme: (theme) => set({ theme }),
  setTransitioning: (isTransitioning) => set({ isTransitioning }),
  setSearchFilterOpen: (isSearchFilterOpen) => set({ isSearchFilterOpen }),
  setJourneyFilterOpen: (isJourneyFilterOpen) => set({ isJourneyFilterOpen }),
  setSearchFilterPrefs: (prefs) =>
    set((s) => ({ searchFilterPrefs: { ...s.searchFilterPrefs, ...prefs } })),
  setJourneyFilterPrefs: (prefs) =>
    set((s) => ({ journeyFilterPrefs: { ...s.journeyFilterPrefs, ...prefs } })),
  setCurtainEl: (curtainEl) => set({ curtainEl }),
}));

export type { FilterPrefs };
