import { create } from 'zustand';

interface ModalState {
  previewModalOpen: boolean;
  openPreviewModal: () => void;
  closePreviewModal: () => void;
}

export const useModalStore = create<ModalState>()((set) => ({
  previewModalOpen: false,
  openPreviewModal: () => set({ previewModalOpen: true }),
  closePreviewModal: () => set({ previewModalOpen: false }),
}));
