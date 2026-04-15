import { create } from 'zustand';
import type { SearchParams } from '@/types/search';

export const defaultSearchParams: SearchParams = {
  origin: '',
  destination: '',
  date: '',
  transferCount: 1,
  allowedTrainTypes: [],
  excludedTrainTypes: [],
  allowedTrains: [],
  excludedTrains: [],
  departureTimeStart: '',
  departureTimeEnd: '',
  arrivalDeadline: '',
  minTransferMinutes: 30,
  maxTransferMinutes: '',
  allowedTransferStations: [],
  excludedTransferStations: [],
  enableTicketEnrich: false,
};

interface SearchState {
  params: SearchParams;
  searchId: string | null;
  setOrigin: (origin: string) => void;
  setDestination: (destination: string) => void;
  setDate: (date: string) => void;
  updateParams: (params: Partial<SearchParams>) => void;
  setParams: (params: SearchParams) => void;
  setSearchId: (searchId: string | null) => void;
}

export const useSearchStore = create<SearchState>()((set) => ({
  params: { ...defaultSearchParams },
  searchId: null,
  setOrigin: (origin) => set((s) => ({ params: { ...s.params, origin } })),
  setDestination: (destination) => set((s) => ({ params: { ...s.params, destination } })),
  setDate: (date) => set((s) => ({ params: { ...s.params, date } })),
  updateParams: (params) => set((s) => ({ params: { ...s.params, ...params } })),
  setParams: (params) => set({ params }),
  setSearchId: (searchId) => set({ searchId }),
}));
