import { create } from 'zustand';

export type SearchPhase =
  | 'idle'
  | 'planning'
  | 'pricing'
  | 'building_view'
  | 'complete'
  | 'error';

export interface PlanReadyEntry {
  transferCount: number;
  candidateCount: number;
}

export interface SearchProgress {
  phase: SearchPhase;
  /** Which transfer count is currently being planned */
  currentTransferCount: number | null;
  /** Plans that have completed */
  plansReady: PlanReadyEntry[];
  /** Total candidates across all plans */
  totalCandidates: number | null;
  /** Total unique legs (cached + uncached) */
  totalLegs: number | null;
  /** Legs already cached in Redis */
  cachedLegs: number | null;
  /** Legs that need to be fetched from 12306 */
  legsToFetch: number | null;
  /** How many legs have been fetched so far */
  fetchedLegs: number;
  /** Error message if phase === 'error' */
  errorMessage: string | null;
}

interface SearchProgressState extends SearchProgress {
  /** Whether a search stream is currently active */
  isActive: boolean;
  /** Reset to idle state before starting a new search */
  reset: () => void;
  /** Start a new search (set phase to planning) */
  start: () => void;
  /** Apply a single SSE event to the store */
  applyEvent: (event: Record<string, unknown>) => void;
}

const initialProgress: SearchProgress = {
  phase: 'idle',
  currentTransferCount: null,
  plansReady: [],
  totalCandidates: null,
  totalLegs: null,
  cachedLegs: null,
  legsToFetch: null,
  fetchedLegs: 0,
  errorMessage: null,
};

export const useSearchProgressStore = create<SearchProgressState>()((set) => ({
  ...initialProgress,
  isActive: false,

  reset: () => set({ ...initialProgress, isActive: false }),

  start: () =>
    set({
      ...initialProgress,
      isActive: true,
      phase: 'planning',
    }),

  applyEvent: (event) => {
    const type = event.type as string;

    switch (type) {
      case 'phase':
        set((s) => ({
          phase:
            event.phase === 'planning'
              ? 'planning'
              : event.phase === 'building_view'
                ? 'building_view'
                : s.phase,
          currentTransferCount:
            event.phase === 'planning'
              ? (event.transferCount as number)
              : s.currentTransferCount,
        }));
        break;

      case 'plan_ready':
        set((s) => ({
          plansReady: [
            ...s.plansReady,
            {
              transferCount: event.transferCount as number,
              candidateCount: event.candidateCount as number,
            },
          ],
        }));
        break;

      case 'candidates_counted':
        set({
          totalCandidates: event.totalCandidates as number,
        });
        break;

      case 'pricing_started':
        set({
          phase: 'pricing',
          totalLegs: event.totalLegs as number,
          cachedLegs: event.cachedLegs as number,
          legsToFetch: event.legsToFetch as number,
          fetchedLegs: 0,
        });
        break;

      case 'leg_fetched':
        set({
          fetchedLegs: event.completed as number,
        });
        break;

      case 'complete':
        set({
          phase: 'complete',
          isActive: false,
        });
        break;

      case 'error':
        set({
          phase: 'error',
          isActive: false,
          errorMessage: (event.message as string) ?? '搜索失败，请稍后重试',
        });
        break;
    }
  },
}));
