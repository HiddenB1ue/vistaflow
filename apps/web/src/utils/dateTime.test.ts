import { describe, expect, it } from 'vitest';

import { getRouteDayOffset } from './dateTime';

describe('getRouteDayOffset', () => {
  it('returns zero for same-day times', () => {
    expect(getRouteDayOffset('2026-05-03', '2026-05-03')).toBe(0);
  });

  it('returns positive day offsets for later dates', () => {
    expect(getRouteDayOffset('2026-05-04', '2026-05-03')).toBe(1);
    expect(getRouteDayOffset('2026-05-05', '2026-05-03')).toBe(2);
  });

  it('does not show negative offsets for earlier or invalid dates', () => {
    expect(getRouteDayOffset('2026-05-02', '2026-05-03')).toBe(0);
    expect(getRouteDayOffset('', '2026-05-03')).toBe(0);
    expect(getRouteDayOffset('invalid', '2026-05-03')).toBe(0);
  });
});
