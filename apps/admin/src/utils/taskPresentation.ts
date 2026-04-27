import { TASK_STATE_LABELS, TASK_STATUS_LABELS } from '@/constants/labels';
import type { Task } from '@/types/task';

export type TaskStatusDotVariant = 'running' | 'pending' | 'idle' | 'error';
export type TaskBadgeVariant = 'green' | 'yellow' | 'blue' | 'red';

export interface TaskDisplayStatus {
  label: string;
  dotVariant: TaskStatusDotVariant;
  badgeVariant: TaskBadgeVariant;
}

export function isRecurringTask(task: Pick<Task, 'scheduleMode' | 'cron'>): boolean {
  return task.scheduleMode === 'cron' || Boolean(task.cron);
}

export function canToggleTaskEnabled(task: Pick<Task, 'scheduleMode' | 'cron' | 'runAt' | 'nextRunAt'>): boolean {
  if (isRecurringTask(task)) {
    return true;
  }
  return task.scheduleMode === 'once' && Boolean(task.runAt ?? task.nextRunAt);
}

export function getTaskDisplayStatus(task: Pick<Task, 'status' | 'enabled' | 'scheduleMode' | 'cron'>): TaskDisplayStatus {
  if (!task.enabled && isRecurringTask(task)) {
    return {
      label: TASK_STATE_LABELS.disabled,
      dotVariant: 'idle',
      badgeVariant: 'red',
    };
  }

  if (task.enabled && isRecurringTask(task) && task.status !== 'pending' && task.status !== 'running') {
    return {
      label: '等待下次',
      dotVariant: 'idle',
      badgeVariant: 'blue',
    };
  }

  switch (task.status) {
    case 'running':
      return { label: TASK_STATUS_LABELS.running, dotVariant: 'running', badgeVariant: 'green' };
    case 'pending':
      return { label: TASK_STATUS_LABELS.pending, dotVariant: 'pending', badgeVariant: 'yellow' };
    case 'completed':
      return { label: TASK_STATUS_LABELS.completed, dotVariant: 'idle', badgeVariant: 'blue' };
    case 'error':
      return { label: TASK_STATUS_LABELS.error, dotVariant: 'error', badgeVariant: 'red' };
    case 'terminated':
      return { label: TASK_STATUS_LABELS.terminated, dotVariant: 'error', badgeVariant: 'red' };
    default:
      return { label: TASK_STATUS_LABELS.idle, dotVariant: 'idle', badgeVariant: 'blue' };
  }
}
