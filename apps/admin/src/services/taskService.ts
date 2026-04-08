import { TASK_FEEDBACK_LABELS } from '@/constants/labels';
import type { Task, TaskCreateRequest, TaskRun, TaskRunLog, TaskTypeDefinition } from '@/types/task';
import * as taskApiService from './taskApiService';
import * as taskMockService from './mock/taskMockService';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const taskServiceImpl = USE_MOCK ? taskMockService : taskApiService;

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

export async function fetchTasks(): Promise<Task[]> {
  return taskServiceImpl.fetchTasks();
}

export async function fetchTask(taskId: number): Promise<Task> {
  return taskServiceImpl.fetchTask(taskId);
}

export async function fetchTaskTypes(): Promise<TaskTypeDefinition[]> {
  return taskServiceImpl.fetchTaskTypes();
}

export async function createTask(payload: TaskCreateRequest): Promise<Task> {
  return taskServiceImpl.createTask(payload);
}

export async function triggerTask(taskId: number): Promise<TaskRun> {
  return taskServiceImpl.triggerTask(taskId);
}

export async function terminateTaskRun(runId: number): Promise<TaskRun> {
  return taskServiceImpl.terminateTaskRun(runId);
}

export async function fetchTaskRuns(taskId: number): Promise<TaskRun[]> {
  return taskServiceImpl.fetchTaskRuns(taskId);
}

export async function fetchTaskRunLogs(runId: number): Promise<TaskRunLog[]> {
  return taskServiceImpl.fetchTaskRunLogs(runId);
}
