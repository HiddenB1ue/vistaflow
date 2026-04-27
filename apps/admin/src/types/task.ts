export type TaskStatus = 'idle' | 'pending' | 'running' | 'completed' | 'error' | 'terminated';
export type TaskRunStatus = 'pending' | 'running' | 'completed' | 'error' | 'terminated';
export type TaskResultLevel = 'success' | 'warning' | 'error';
export type TaskValueType = 'date' | 'text';
export type TaskScheduleMode = 'manual' | 'once' | 'cron';
export type TaskDateMode = 'fixed' | 'relative';

export interface TaskMetrics {
  label: string;
  value: string;
}

export interface TaskTiming {
  label: string;
  value: string;
}

export interface TaskLatestRun {
  id: number;
  status: TaskRunStatus;
  resultLevel?: TaskResultLevel | null;
  startedAt?: string | null;
  finishedAt?: string | null;
  errorMessage?: string | null;
}

export interface Task {
  id: number;
  name: string;
  type: string;
  typeLabel: string;
  status: TaskStatus;
  description?: string | null;
  enabled: boolean;
  scheduleMode?: TaskScheduleMode;
  cron?: string | null;
  runAt?: string | null;
  nextRunAt?: string | null;
  payload: Record<string, unknown>;
  metrics: TaskMetrics;
  timing: TaskTiming;
  errorMessage?: string | null;
  latestRun?: TaskLatestRun | null;
}

export interface TaskParamDefinition {
  key: string;
  label: string;
  valueType: TaskValueType;
  required: boolean;
  placeholder: string;
  description: string;
}

export interface TaskTypeDefinition {
  type: string;
  label: string;
  description: string;
  implemented: boolean;
  supportsCron: boolean;
  paramSchema: TaskParamDefinition[];
}

export interface TaskCreateRequest {
  name: string;
  type: string;
  description?: string;
  enabled?: boolean;
  scheduleMode?: TaskScheduleMode;
  cron?: string | null;
  runAt?: string | null;
  payload?: Record<string, unknown>;
}

export interface TaskRun {
  id: number;
  taskId: number;
  taskName: string;
  taskType: string;
  triggerMode: string;
  status: TaskRunStatus;
  requestedBy: string;
  summary?: string | null;
  resultLevel?: TaskResultLevel | null;
  metricsValue: string;
  progressSnapshot?: Record<string, unknown> | null;
  errorMessage?: string | null;
  terminationReason?: string | null;
  startedAt?: string | null;
  finishedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TaskRunLog {
  id: number;
  runId: number;
  severity: 'SUCCESS' | 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';
  message: string;
  createdAt: string;
}
