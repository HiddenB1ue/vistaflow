import { describe, expect, it } from 'vitest';
import type { TaskTypeDefinition } from '@/types/task';
import { buildTaskCreateRequest, findMissingRequiredParam } from './taskDrawerPayload';

const trainRunType: TaskTypeDefinition = {
  type: 'fetch-train-runs',
  label: '获取某天运行的车次',
  description: '',
  implemented: true,
  supportsCron: true,
  paramSchema: [
    {
      key: 'date',
      label: '日期',
      valueType: 'date',
      required: true,
      placeholder: '',
      description: '',
    },
    {
      key: 'keyword',
      label: '关键字',
      valueType: 'text',
      required: false,
      placeholder: '',
      description: '',
    },
  ],
};

describe('taskDrawerPayload', () => {
  it('builds manual task request without cron or runAt', () => {
    const request = buildTaskCreateRequest({
      name: ' Daily runs ',
      taskType: trainRunType,
      description: '',
      enabled: true,
      scheduleMode: 'manual',
      cronExpr: '0 3 * * *',
      runAt: new Date('2026-05-01T03:00').toISOString(),
      dateMode: 'fixed',
      dateOffsetDays: '9',
      paramValues: { date: '2026-05-02', keyword: ' G ' },
    });

    expect(request.scheduleMode).toBe('manual');
    expect(request.cron).toBeNull();
    expect(request.runAt).toBeNull();
    expect(request.payload).toEqual({
      dateMode: 'fixed',
      date: '2026-05-02',
      keyword: 'G',
    });
  });

  it('builds relative date cron request', () => {
    const request = buildTaskCreateRequest({
      name: 'Daily T+9 runs',
      taskType: trainRunType,
      description: 'sync',
      enabled: true,
      scheduleMode: 'cron',
      cronExpr: ' 0 3 * * * ',
      runAt: '',
      dateMode: 'relative',
      dateOffsetDays: '9',
      paramValues: { date: '2026-05-02', keyword: '' },
    });

    expect(request.scheduleMode).toBe('cron');
    expect(request.cron).toBe('0 3 * * *');
    expect(request.runAt).toBeNull();
    expect(request.payload).toEqual({
      dateMode: 'relative',
      dateOffsetDays: 9,
    });
  });

  it('builds once request with runAt', () => {
    const request = buildTaskCreateRequest({
      name: 'Once',
      taskType: trainRunType,
      description: '',
      enabled: true,
      scheduleMode: 'once',
      cronExpr: '',
      runAt: new Date('2026-05-01T03:00').toISOString(),
      dateMode: 'relative',
      dateOffsetDays: '9',
      paramValues: {},
    });

    expect(request.cron).toBeNull();
    expect(request.runAt).toBe(new Date('2026-05-01T03:00').toISOString());
    expect(request.payload).toEqual({ dateMode: 'relative', dateOffsetDays: 9 });
  });

  it('does not require fixed date when relative mode is selected', () => {
    expect(findMissingRequiredParam(trainRunType, {}, 'relative')).toBeUndefined();
    expect(findMissingRequiredParam(trainRunType, {}, 'fixed')?.key).toBe('date');
  });
});
