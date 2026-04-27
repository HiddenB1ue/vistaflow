import { describe, expect, it } from 'vitest';
import { formatTaskSchedule } from './taskSchedule';

describe('formatTaskSchedule', () => {
  it('formats manual tasks', () => {
    expect(formatTaskSchedule({ scheduleMode: 'manual', cron: null, runAt: null, nextRunAt: null })).toBe(
      '手动执行',
    );
  });

  it('formats once tasks with runAt', () => {
    expect(
      formatTaskSchedule({
        scheduleMode: 'once',
        cron: null,
        runAt: '2026-05-01T03:30:00',
        nextRunAt: null,
      }),
    ).toBe('执行一次 · 2026-05-01 03:30');
  });

  it('formats once tasks with nextRunAt fallback', () => {
    expect(
      formatTaskSchedule({
        scheduleMode: 'once',
        cron: null,
        runAt: null,
        nextRunAt: '2026-05-01T03:30:00',
      }),
    ).toBe('执行一次 · 2026-05-01 03:30');
  });

  it('formats cron tasks with expression', () => {
    expect(
      formatTaskSchedule({
        scheduleMode: 'cron',
        cron: '0 3 * * *',
        runAt: null,
        nextRunAt: null,
      }),
    ).toBe('重复执行 · Cron: 0 3 * * *');
  });

  it('treats legacy cron tasks as repeated tasks', () => {
    expect(formatTaskSchedule({ cron: '0 3 * * *', runAt: null, nextRunAt: null })).toBe(
      '重复执行 · Cron: 0 3 * * *',
    );
  });
});
