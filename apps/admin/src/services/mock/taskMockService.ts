import { TASK_STATUS_LABELS } from '@/constants/labels';
import type { Task, TaskCreateRequest, TaskRun, TaskRunLog, TaskTypeDefinition } from '@/types/task';
import type { PaginatedResponse, TaskListQuery } from '@/types/pagination';
import { MOCK_TASKS, MOCK_TASK_TYPES } from './tasks.mock';

let mockTasksState: Task[] = MOCK_TASKS.map((task) => ({
  ...task,
  payload: { ...task.payload },
  latestRun: task.latestRun ? { ...task.latestRun } : null,
}));
let mockTaskIdSeed = Math.max(...mockTasksState.map((task) => task.id), 0);
let mockRunIdSeed = Math.max(...mockTasksState.map((task) => task.latestRun?.id ?? 0), 100);

function cloneTask(task: Task): Task {
  return {
    ...task,
    payload: { ...task.payload },
    latestRun: task.latestRun ? { ...task.latestRun } : null,
  };
}

function cloneTaskType(taskType: TaskTypeDefinition): TaskTypeDefinition {
  return {
    ...taskType,
    paramSchema: taskType.paramSchema.map((param) => ({ ...param })),
  };
}

function findTaskType(taskType: string): TaskTypeDefinition | undefined {
  return MOCK_TASK_TYPES.find((candidate) => candidate.type === taskType);
}

function buildMockRun(task: Task): TaskRun | null {
  if (!task.latestRun) {
    return null;
  }

  return {
    id: task.latestRun.id,
    taskId: task.id,
    taskName: task.name,
    taskType: task.type,
    triggerMode: 'manual',
    status: task.latestRun.status,
    requestedBy: 'admin',
    summary: task.errorMessage ?? task.description ?? null,
    resultLevel: task.latestRun.resultLevel ?? null,
    metricsValue: task.metrics.value,
    progressSnapshot: null,
    errorMessage: task.latestRun.errorMessage ?? task.errorMessage ?? null,
    terminationReason: task.status === 'terminated' ? '管理员终止执行' : null,
    startedAt: task.latestRun.startedAt ?? null,
    finishedAt: task.latestRun.finishedAt ?? null,
    createdAt: task.latestRun.startedAt ?? new Date().toISOString(),
    updatedAt: task.latestRun.finishedAt ?? task.latestRun.startedAt ?? new Date().toISOString(),
  };
}

function buildMockLogs(run: TaskRun): TaskRunLog[] {
  const createdAt = run.createdAt;
  const logs: TaskRunLog[] = [
    {
      id: run.id * 10 + 1,
      runId: run.id,
      severity: 'SYSTEM',
      message: `任务 ${run.taskName} 已入队`,
      createdAt,
    },
  ];

  if (run.status === 'running' || run.status === 'completed') {
    logs.push({
      id: run.id * 10 + 2,
      runId: run.id,
      severity: 'INFO',
      message: `任务 ${run.taskName} 开始执行`,
      createdAt: run.startedAt ?? createdAt,
    });
  }

  if (run.status === 'completed') {
    logs.push({
      id: run.id * 10 + 3,
      runId: run.id,
      severity: 'SUCCESS',
      message: `任务 ${run.taskName} 执行完成`,
      createdAt: run.finishedAt ?? createdAt,
    });
  }

  if (run.status === 'error' || run.status === 'terminated') {
    logs.push({
      id: run.id * 10 + 3,
      runId: run.id,
      severity: 'ERROR',
      message: run.errorMessage || run.terminationReason || `任务 ${run.taskName} 执行失败`,
      createdAt: run.finishedAt ?? createdAt,
    });
  }

  if (run.status === 'pending') {
    logs.push({
      id: run.id * 10 + 2,
      runId: run.id,
      severity: 'INFO',
      message: `任务 ${run.taskName} 正在等待 worker 执行`,
      createdAt,
    });
  }

  return logs;
}

async function sleep(timeoutMs: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, timeoutMs));
}

export async function fetchTasks(query: TaskListQuery): Promise<PaginatedResponse<Task>> {
  await sleep(300);
  
  // Filter tasks based on query
  let filtered = mockTasksState;
  
  // Apply keyword search
  if (query.keyword.trim()) {
    const keyword = query.keyword.trim().toLowerCase();
    filtered = filtered.filter((task) => {
      const searchableFields = [task.name, task.typeLabel, task.description ?? '', task.type];
      return searchableFields.some((field) => field.toLowerCase().includes(keyword));
    });
  }
  
  // Apply status filter
  if (query.status !== 'all') {
    filtered = filtered.filter((task) => task.status === query.status);
  }
  
  // Calculate pagination
  const total = filtered.length;
  const totalPages = Math.ceil(total / query.pageSize) || 0;
  const offset = (query.page - 1) * query.pageSize;
  const items = filtered.slice(offset, offset + query.pageSize).map(cloneTask);
  
  return {
    items,
    page: query.page,
    pageSize: query.pageSize,
    total,
    totalPages,
  };
}

export async function fetchTask(taskId: number): Promise<Task> {
  await sleep(150);
  const task = mockTasksState.find((candidate) => candidate.id === taskId);
  if (!task) {
    throw new Error('任务不存在');
  }

  return cloneTask(task);
}

export async function fetchTaskTypes(): Promise<TaskTypeDefinition[]> {
  await sleep(150);
  return MOCK_TASK_TYPES.map(cloneTaskType);
}

export async function createTask(payload: TaskCreateRequest): Promise<Task> {
  await sleep(200);
  const taskType = findTaskType(payload.type);
  const createdTask: Task = {
    id: ++mockTaskIdSeed,
    name: payload.name,
    type: payload.type,
    typeLabel: taskType?.label ?? payload.type,
    status: 'idle',
    description: payload.description ?? null,
    enabled: payload.enabled ?? true,
    scheduleMode: payload.scheduleMode ?? (payload.cron ? 'cron' : 'manual'),
    cron: payload.cron ?? null,
    runAt: payload.runAt ?? null,
    nextRunAt: payload.scheduleMode === 'once' ? payload.runAt ?? null : null,
    payload: { ...(payload.payload ?? {}) },
    metrics: { label: '最近结果', value: '-' },
    timing: { label: '最近耗时', value: '-' },
    errorMessage: null,
    latestRun: null,
  };
  mockTasksState = [createdTask, ...mockTasksState];
  return cloneTask(createdTask);
}

export async function triggerTask(taskId: number): Promise<TaskRun> {
  await sleep(200);
  const task = mockTasksState.find((candidate) => candidate.id === taskId);
  if (!task) {
    throw new Error('任务不存在');
  }
  if (!task.enabled) {
    throw new Error('任务已停用，无法执行');
  }

  const now = new Date().toISOString();
  const run: TaskRun = {
    id: ++mockRunIdSeed,
    taskId: task.id,
    taskName: task.name,
    taskType: task.type,
    triggerMode: 'manual',
    status: 'pending',
    requestedBy: 'admin',
    summary: null,
    resultLevel: null,
    metricsValue: '',
    progressSnapshot: null,
    errorMessage: null,
    terminationReason: null,
    startedAt: null,
    finishedAt: null,
    createdAt: now,
    updatedAt: now,
  };

  mockTasksState = mockTasksState.map((candidate) =>
    candidate.id === taskId
      ? {
          ...candidate,
          status: 'pending',
          errorMessage: null,
          metrics: { ...candidate.metrics, value: TASK_STATUS_LABELS.pending },
          latestRun: {
            id: run.id,
            status: run.status,
            resultLevel: run.resultLevel,
            startedAt: run.startedAt,
            finishedAt: run.finishedAt,
            errorMessage: null,
          },
        }
      : candidate,
  );

  return run;
}

export async function terminateTaskRun(runId: number): Promise<TaskRun> {
  await sleep(200);
  const task = mockTasksState.find((candidate) => candidate.latestRun?.id === runId);
  if (!task || !task.latestRun) {
    throw new Error('执行记录不存在');
  }

  const now = new Date().toISOString();
  const terminatedRun: TaskRun = {
    id: task.latestRun.id,
    taskId: task.id,
    taskName: task.name,
    taskType: task.type,
    triggerMode: 'manual',
    status: 'terminated',
    requestedBy: 'admin',
    summary: null,
    resultLevel: 'error',
    metricsValue: '',
    progressSnapshot: null,
    errorMessage: '执行已被管理员终止',
    terminationReason: '管理员终止执行',
    startedAt: task.latestRun.startedAt ?? null,
    finishedAt: now,
    createdAt: now,
    updatedAt: now,
  };

  mockTasksState = mockTasksState.map((candidate) =>
    candidate.latestRun?.id === runId
      ? {
          ...candidate,
          status: 'terminated',
          errorMessage: terminatedRun.errorMessage,
          latestRun: {
            ...candidate.latestRun,
            status: 'terminated',
            resultLevel: 'error',
            finishedAt: terminatedRun.finishedAt,
            errorMessage: terminatedRun.errorMessage,
          },
        }
      : candidate,
  );

  return terminatedRun;
}

export async function fetchTaskRuns(
  taskId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<TaskRun>> {
  await sleep(150);
  const task = mockTasksState.find((candidate) => candidate.id === taskId);
  const run = task ? buildMockRun(task) : null;
  const allRuns = run ? [run] : [];
  
  // Calculate pagination
  const total = allRuns.length;
  const totalPages = Math.ceil(total / pageSize) || 0;
  const offset = (page - 1) * pageSize;
  const items = allRuns.slice(offset, offset + pageSize);
  
  return {
    items,
    page,
    pageSize,
    total,
    totalPages,
  };
}

export async function fetchTaskRunLogs(runId: number): Promise<TaskRunLog[]> {
  await sleep(150);
  const task = mockTasksState.find((candidate) => candidate.latestRun?.id === runId);
  const run = task ? buildMockRun(task) : null;
  return run ? buildMockLogs(run) : [];
}

export async function fetchTaskRunLogsPaginated(
  runId: number,
  page: number = 1,
  pageSize: number = 100
): Promise<PaginatedResponse<TaskRunLog>> {
  await sleep(150);
  const allLogs = await fetchTaskRunLogs(runId);
  const total = allLogs.length;
  const totalPages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const items = allLogs.slice(start, end);

  return {
    items,
    page,
    pageSize,
    total,
    totalPages,
  };
}
