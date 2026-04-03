import { create } from 'zustand';
import type { Task, TaskStatus } from '@/types/task';
import { MOCK_TASKS } from '@/services/mock/tasks.mock';

interface TaskState {
  tasks: Task[];
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
}

export const useTaskStore = create<TaskState>()((set) => ({
  tasks: [...MOCK_TASKS],
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, status } : t
      ),
    })),
}));
