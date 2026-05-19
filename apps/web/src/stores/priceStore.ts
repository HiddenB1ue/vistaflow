import { create } from 'zustand';

export interface PriceSeatEntry {
  seat_type: string;
  status: string;
  price: number | null;
  available: boolean;
}

export interface PriceCacheEntry {
  min_price: number | null;
  seats: PriceSeatEntry[];
  matched_by: string;
  failed: boolean;
}

interface PriceState {
  /** key: "trainNo:fromStation:toStation" → price entry */
  priceMap: Record<string, PriceCacheEntry>;
  /** Whether a price stream is currently active */
  isStreaming: boolean;
  /** Total unique legs to fetch */
  totalLegs: number;
  /** How many legs have been fetched so far */
  fetchedLegs: number;
  /** Merge a batch of price entries into the map */
  mergePrices: (batch: Record<string, PriceCacheEntry>) => void;
  /** Mark streaming as started */
  startStream: (totalLegs: number) => void;
  /** Mark streaming as finished */
  endStream: () => void;
  /** Reset to initial state */
  reset: () => void;
}

const initialState = {
  priceMap: {} as Record<string, PriceCacheEntry>,
  isStreaming: false,
  totalLegs: 0,
  fetchedLegs: 0,
};

export const usePriceStore = create<PriceState>()((set) => ({
  ...initialState,

  mergePrices: (batch) =>
    set((state) => ({
      priceMap: { ...state.priceMap, ...batch },
    })),

  startStream: (totalLegs) =>
    set({
      isStreaming: true,
      totalLegs,
      fetchedLegs: 0,
    }),

  endStream: () =>
    set({
      isStreaming: false,
    }),

  reset: () => set({ ...initialState }),
}));
