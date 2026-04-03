import { create } from 'zustand';
import type { ViewId } from '@/types/view';

interface ViewState {
  activeView: ViewId;
  switchView: (viewId: ViewId) => void;
}

export const useViewStore = create<ViewState>()((set) => ({
  activeView: 'view-overview',
  switchView: (viewId) => set({ activeView: viewId }),
}));
