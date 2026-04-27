import { describe, expect, it } from 'vitest';
import { buildDateTimeISOString, parseDateTimeValue } from './DateTimePicker';

describe('DateTimePicker helpers', () => {
  it('parses an ISO value into local date and time parts', () => {
    const value = new Date(2026, 4, 1, 3, 17, 0).toISOString();

    expect(parseDateTimeValue(value)).toEqual({
      date: '2026-05-01',
      hour: '03',
      minute: '17',
    });
  });

  it('uses fallback when value is empty', () => {
    const fallback = new Date(2026, 4, 1, 9, 31, 0);

    expect(parseDateTimeValue('', { fallback, minuteStep: 10 })).toEqual({
      date: '2026-05-01',
      hour: '09',
      minute: '30',
    });
  });

  it('builds an ISO string from local parts', () => {
    const result = buildDateTimeISOString({
      date: '2026-05-01',
      hour: '03',
      minute: '15',
    });

    expect(result).toBe(new Date(2026, 4, 1, 3, 15, 0).toISOString());
  });
});
