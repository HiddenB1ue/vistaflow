import { TASK_DRAWER_LABELS, TASK_STATE_LABELS } from '@/constants/labels';
import type { Task } from '@/types/task';

type TaskScheduleFields = Pick<Task, 'scheduleMode' | 'cron' | 'runAt' | 'nextRunAt'>;

function padDatePart(value: number): string {
  return String(value).padStart(2, '0');
}

export function formatScheduleDateTime(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return [
    date.getFullYear(),
    padDatePart(date.getMonth() + 1),
    padDatePart(date.getDate()),
  ].join('-') + ` ${padDatePart(date.getHours())}:${padDatePart(date.getMinutes())}`;
}

export function formatTaskSchedule(task: TaskScheduleFields): string {
  const scheduleMode = task.scheduleMode ?? (task.cron ? 'cron' : 'manual');
  const cron = task.cron?.trim();

  if (scheduleMode === 'cron') {
    return cron ? `${TASK_DRAWER_LABELS.scheduleCron} · Cron: ${cron}` : TASK_DRAWER_LABELS.scheduleCron;
  }

  if (scheduleMode === 'once') {
    const runTime = formatScheduleDateTime(task.runAt ?? task.nextRunAt);
    return runTime ? `${TASK_DRAWER_LABELS.scheduleOnce} · ${runTime}` : TASK_DRAWER_LABELS.scheduleOnce;
  }

  return TASK_DRAWER_LABELS.scheduleManual ?? TASK_STATE_LABELS.manualTrigger;
}
