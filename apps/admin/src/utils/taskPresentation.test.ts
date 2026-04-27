import { describe, expect, it } from 'vitest';
import { canToggleTaskEnabled, getTaskDisplayStatus, isRecurringTask } from './taskPresentation';

describe('taskPresentation', () => {
  it('detects recurring tasks from schedule mode or legacy cron', () => {
    expect(isRecurringTask({ scheduleMode: 'cron', cron: null })).toBe(true);
    expect(isRecurringTask({ scheduleMode: 'once', cron: null })).toBe(false);
    expect(isRecurringTask({ scheduleMode: 'manual', cron: '0 3 * * *' })).toBe(true);
    expect(isRecurringTask({ scheduleMode: 'manual', cron: null })).toBe(false);
  });

  it('allows toggling recurring tasks and pending once tasks', () => {
    expect(canToggleTaskEnabled({ scheduleMode: 'cron', cron: null, runAt: null, nextRunAt: null })).toBe(true);
    expect(canToggleTaskEnabled({ scheduleMode: 'once', cron: null, runAt: null, nextRunAt: '2026-05-01T03:00:00' })).toBe(true);
    expect(canToggleTaskEnabled({ scheduleMode: 'once', cron: null, runAt: null, nextRunAt: null })).toBe(false);
  });

  it('shows enabled automatic idle tasks as waiting for next run', () => {
    expect(
      getTaskDisplayStatus({
        status: 'completed',
        enabled: true,
        scheduleMode: 'cron',
        cron: '0 3 * * *',
      }),
    ).toEqual({
      label: '等待下次',
      dotVariant: 'idle',
      badgeVariant: 'blue',
    });
  });

  it('shows disabled automatic tasks as disabled', () => {
    expect(
      getTaskDisplayStatus({
        status: 'completed',
        enabled: false,
        scheduleMode: 'cron',
        cron: '0 3 * * *',
      }),
    ).toEqual({
      label: '已停用',
      dotVariant: 'idle',
      badgeVariant: 'red',
    });
  });

  it('keeps active run statuses for automatic tasks', () => {
    expect(
      getTaskDisplayStatus({
        status: 'running',
        enabled: true,
        scheduleMode: 'cron',
        cron: '0 3 * * *',
      }),
    ).toEqual({
      label: '运行中',
      dotVariant: 'running',
      badgeVariant: 'green',
    });
  });
});
