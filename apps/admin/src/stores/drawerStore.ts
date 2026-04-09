import { create } from 'zustand';

interface DrawerState {
  taskDrawerOpen: boolean;
  taskDetailDrawerOpen: boolean;
  taskDetailDrawerTaskId: number | null;
  openTaskDrawer: () => void;
  closeTaskDrawer: () => void;
  openTaskDetailDrawer: (taskId: number) => void;
  closeTaskDetailDrawer: () => void;
}

export const useDrawerStore = create<DrawerState>()((set) => ({
  taskDrawerOpen: false,
  taskDetailDrawerOpen: false,
  taskDetailDrawerTaskId: null,
  openTaskDrawer: () =>
    set({ taskDrawerOpen: true, taskDetailDrawerOpen: false }),
  closeTaskDrawer: () => set({ taskDrawerOpen: false }),
  openTaskDetailDrawer: (taskId) =>
    set({
      taskDetailDrawerOpen: true,
      taskDetailDrawerTaskId: taskId,
      taskDrawerOpen: false,
    }),
  closeTaskDetailDrawer: () =>
    set({ taskDetailDrawerOpen: false, taskDetailDrawerTaskId: null }),
}));
