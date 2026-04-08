import { apiClient } from './api';
import type { Task, TaskCreateRequest, TaskRun, TaskRunLog, TaskTypeDefinition } from '@/types/task';

export async function fetchTasks(): Promise<Task[]> {
  const { data } = await apiClient.get<{ data: Task[] }>('/admin/tasks');
  return data.data;
}

export async function fetchTask(taskId: number): Promise<Task> {
  const { data } = await apiClient.get<{ data: Task }>(`/admin/tasks/${taskId}`);
  return data.data;
}

export async function fetchTaskTypes(): Promise<TaskTypeDefinition[]> {
  const { data } = await apiClient.get<{ data: TaskTypeDefinition[] }>('/admin/tasks/types');
  return data.data;
}

export async function createTask(payload: TaskCreateRequest): Promise<Task> {
  const { data } = await apiClient.post<{ data: Task }>('/admin/tasks', payload);
  return data.data;
}

export async function triggerTask(taskId: number): Promise<TaskRun> {
  const { data } = await apiClient.post<{ data: TaskRun }>(`/admin/tasks/${taskId}/runs`);
  return data.data;
}

export async function terminateTaskRun(runId: number): Promise<TaskRun> {
  const { data } = await apiClient.post<{ data: TaskRun }>(`/admin/task-runs/${runId}/terminate`);
  return data.data;
}

export async function fetchTaskRuns(taskId: number): Promise<TaskRun[]> {
  const { data } = await apiClient.get<{ data: TaskRun[] }>(`/admin/tasks/${taskId}/runs`);
  return data.data;
}

export async function fetchTaskRunLogs(runId: number): Promise<TaskRunLog[]> {
  const { data } = await apiClient.get<{ data: TaskRunLog[] }>(`/admin/task-runs/${runId}/logs`);
  return data.data;
}
