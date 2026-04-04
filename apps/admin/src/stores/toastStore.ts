import { create } from 'zustand';
import type { ToastType, ToastItem } from '@vistaflow/ui';

let toastCounter = 0;

interface ToastState {
  toasts: ToastItem[];
  addToast: (message: string, type: ToastType) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastState>()((set) => ({
  toasts: [],
  addToast: (message, type) =>
    set((state) => ({
      toasts: [...state.toasts, { id: `toast-${++toastCounter}`, message, type }],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
