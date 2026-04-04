import type { Task } from '@/types/task';
import { apiClient } from './api';
import { MOCK_TASKS } from './mock/tasks.mock';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export async function fetchTasks(): Promise<Task[]> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_TASKS;
  }
  const { data } = await apiClient.get<{ data: Task[] }>('/admin/tasks');
  return data.data;
}
