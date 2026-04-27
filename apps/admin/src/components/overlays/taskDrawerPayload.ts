import type {
  TaskCreateRequest,
  TaskDateMode,
  TaskParamDefinition,
  TaskScheduleMode,
  TaskTypeDefinition,
} from '@/types/task';

const DATE_TASK_TYPES = new Set(['fetch-trains', 'fetch-train-stops', 'fetch-train-runs']);

export const DEFAULT_CRON_EXPRESSION = '0 3 * * *';
export const DEFAULT_DATE_OFFSET_DAYS = 9;

export interface BuildTaskCreateInput {
  name: string;
  taskType: TaskTypeDefinition;
  description: string;
  enabled: boolean;
  scheduleMode: TaskScheduleMode;
  cronExpr: string;
  runAt: string;
  dateMode: TaskDateMode;
  dateOffsetDays: string;
  paramValues: Record<string, string>;
}

export function taskTypeSupportsDateMode(taskType: TaskTypeDefinition | undefined): boolean {
  return taskType ? DATE_TASK_TYPES.has(taskType.type) : false;
}

function buildPayload(
  taskType: TaskTypeDefinition,
  paramValues: Record<string, string>,
  dateMode: TaskDateMode,
  dateOffsetDays: string,
): Record<string, unknown> {
  const supportsDateMode = taskTypeSupportsDateMode(taskType);
  const payloadEntries = taskType.paramSchema.flatMap((param) => {
    if (supportsDateMode && param.key === 'date') {
      return [];
    }
    const value = (paramValues[param.key] ?? '').trim();
    return value ? [[param.key, value] as const] : [];
  });
  const payload: Record<string, unknown> = Object.fromEntries(payloadEntries);
  if (!supportsDateMode) {
    return payload;
  }
  payload.dateMode = dateMode;
  if (dateMode === 'fixed') {
    const date = (paramValues.date ?? '').trim();
    if (date) {
      payload.date = date;
    }
    return payload;
  }
  payload.dateOffsetDays = Number.parseInt(dateOffsetDays, 10);
  return payload;
}

export function findMissingRequiredParam(
  taskType: TaskTypeDefinition,
  paramValues: Record<string, string>,
  dateMode: TaskDateMode,
): TaskParamDefinition | undefined {
  const supportsDateMode = taskTypeSupportsDateMode(taskType);
  return taskType.paramSchema.find((param) => {
    if (!param.required) {
      return false;
    }
    if (supportsDateMode && param.key === 'date' && dateMode === 'relative') {
      return false;
    }
    return (paramValues[param.key] ?? '').trim().length === 0;
  });
}

export function buildTaskCreateRequest(input: BuildTaskCreateInput): TaskCreateRequest {
  const payload = buildPayload(
    input.taskType,
    input.paramValues,
    input.dateMode,
    input.dateOffsetDays,
  );
  return {
    name: input.name.trim(),
    type: input.taskType.type,
    description: input.description.trim() || undefined,
    enabled: input.enabled,
    scheduleMode: input.scheduleMode,
    cron: input.scheduleMode === 'cron' ? input.cronExpr.trim() : null,
    runAt:
      input.scheduleMode === 'once'
        ? input.runAt.trim()
        : null,
    payload,
  };
}
