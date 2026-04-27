import { apiClient } from './api';
import type { Task, TaskCreateRequest, TaskRun, TaskRunLog, TaskTypeDefinition, TaskUpdateRequest } from '@/types/task';
import type { PaginatedResponse, TaskListQuery } from '@/types/pagination';

export async function fetchTasks(query: TaskListQuery): Promise<PaginatedResponse<Task>> {
  const { data } = await apiClient.get<{ data: PaginatedResponse<Task> }>('/admin/tasks', {
    params: {
      page: query.page,
      pageSize: query.pageSize,
      keyword: query.keyword.trim() || undefined,
      status: query.status !== 'all' ? query.status : undefined,
    },
  });
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

export async function updateTask(taskId: number, payload: TaskUpdateRequest): Promise<Task> {
  const { data } = await apiClient.patch<{ data: Task }>(`/admin/tasks/${taskId}`, payload);
  return data.data;
}

export async function deleteTask(taskId: number): Promise<void> {
  await apiClient.delete(`/admin/tasks/${taskId}`);
}

export async function triggerTask(taskId: number): Promise<TaskRun> {
  const { data } = await apiClient.post<{ data: TaskRun }>(`/admin/tasks/${taskId}/runs`);
  return data.data;
}

export async function terminateTaskRun(runId: number): Promise<TaskRun> {
  const { data } = await apiClient.post<{ data: TaskRun }>(`/admin/task-runs/${runId}/terminate`);
  return data.data;
}

export async function fetchTaskRuns(
  taskId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<TaskRun>> {
  const { data } = await apiClient.get<{ data: PaginatedResponse<TaskRun> }>(
    `/admin/tasks/${taskId}/runs`,
    { params: { page, pageSize } }
  );
  return data.data;
}

export async function fetchTaskRunLogs(runId: number): Promise<TaskRunLog[]> {
  const { data } = await apiClient.get<{ data: TaskRunLog[] }>(`/admin/task-runs/${runId}/logs`);
  return data.data;
}

export async function fetchTaskRunLogsPaginated(
  runId: number,
  page: number = 1,
  pageSize: number = 100
): Promise<PaginatedResponse<TaskRunLog>> {
  const { data } = await apiClient.get<{ data: PaginatedResponse<TaskRunLog> }>(
    `/admin/task-runs/${runId}/logs/paginated`,
    { params: { page, pageSize } }
  );
  return data.data;
}
