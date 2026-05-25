import { TASK_FEEDBACK_LABELS } from '@/constants/labels';
import type { Task, TaskCreateRequest, TaskRun, TaskRunLog, TaskTypeDefinition, TaskUpdateRequest } from '@/types/task';
import type { PaginatedResponse, TaskListQuery } from '@/types/pagination';
import * as taskApiService from './taskApiService';

export function extractApiErrorMessage(error: unknown): string {
  const responseData =
    typeof error === 'object' && error !== null && 'response' in error
      ? (error as { response?: { data?: unknown } }).response?.data
      : undefined;

  if (typeof responseData === 'object' && responseData !== null) {
    const apiError = (responseData as { error?: unknown }).error;
    if (typeof apiError === 'string' && apiError.trim().length > 0) {
      return apiError;
    }

    const detail = (responseData as { detail?: unknown }).detail;
    if (typeof detail === 'string' && detail.trim().length > 0) {
      return detail;
    }
  }

  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return TASK_FEEDBACK_LABELS.requestFailed;
}

export async function fetchTasks(query: TaskListQuery): Promise<PaginatedResponse<Task>> {
  return taskApiService.fetchTasks(query);
}

export async function fetchTask(taskId: number): Promise<Task> {
  return taskApiService.fetchTask(taskId);
}

export async function fetchTaskTypes(): Promise<TaskTypeDefinition[]> {
  return taskApiService.fetchTaskTypes();
}

export async function createTask(payload: TaskCreateRequest): Promise<Task> {
  return taskApiService.createTask(payload);
}

export async function updateTask(taskId: number, payload: TaskUpdateRequest): Promise<Task> {
  return taskApiService.updateTask(taskId, payload);
}

export async function deleteTask(taskId: number): Promise<void> {
  return taskApiService.deleteTask(taskId);
}

export async function triggerTask(taskId: number): Promise<TaskRun> {
  return taskApiService.triggerTask(taskId);
}

export async function terminateTaskRun(runId: number): Promise<TaskRun> {
  return taskApiService.terminateTaskRun(runId);
}

export async function fetchTaskRuns(
  taskId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<TaskRun>> {
  return taskApiService.fetchTaskRuns(taskId, page, pageSize);
}

export async function fetchTaskRunLogs(runId: number): Promise<TaskRunLog[]> {
  return taskApiService.fetchTaskRunLogs(runId);
}

export async function fetchTaskRunLogsPaginated(
  runId: number,
  page: number = 1,
  pageSize: number = 100
): Promise<PaginatedResponse<TaskRunLog>> {
  return taskApiService.fetchTaskRunLogsPaginated(runId, page, pageSize);
}
