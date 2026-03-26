import { create } from 'zustand';
import type { SearchParams } from '@/types/search';

interface SearchState {
  params: SearchParams;
  setOrigin: (origin: string) => void;
  setDestination: (destination: string) => void;
  setDate: (date: string) => void;
  setParams: (params: SearchParams) => void;
}

export const useSearchStore = create<SearchState>()((set) => ({
  params: {
    origin: '',
    destination: '',
    date: '',
  },
  setOrigin: (origin) => set((s) => ({ params: { ...s.params, origin } })),
  setDestination: (destination) => set((s) => ({ params: { ...s.params, destination } })),
  setDate: (date) => set((s) => ({ params: { ...s.params, date } })),
  setParams: (params) => set({ params }),
}));
