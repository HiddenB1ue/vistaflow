import { create } from 'zustand';
import type { Task, TaskStatus } from '@/types/task';

interface TaskState {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
}

export const useTaskStore = create<TaskState>()((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, status } : task,
      ),
    })),
}));
