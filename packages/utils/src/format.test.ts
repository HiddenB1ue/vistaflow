import { describe, it, expect } from 'vitest';
import { formatDuration, formatPrice } from './format';

describe('formatDuration', () => {
  it('returns "0分" for 0 minutes', () => {
    expect(formatDuration(0)).toBe('0分');
  });

  it('returns minutes only when less than 60', () => {
    expect(formatDuration(30)).toBe('30分');
    expect(formatDuration(1)).toBe('1分');
    expect(formatDuration(59)).toBe('59分');
  });

  it('returns hours only for exact multiples of 60', () => {
    expect(formatDuration(60)).toBe('1小时');
    expect(formatDuration(120)).toBe('2小时');
    expect(formatDuration(180)).toBe('3小时');
  });

  it('returns hours and minutes for non-multiples of 60 above 60', () => {
    expect(formatDuration(90)).toBe('1小时30分');
    expect(formatDuration(61)).toBe('1小时1分');
    expect(formatDuration(150)).toBe('2小时30分');
  });
});

describe('formatPrice', () => {
  it('formats simple numbers with ¥ prefix', () => {
    expect(formatPrice(100)).toBe('¥100');
    expect(formatPrice(0)).toBe('¥0');
  });

  it('formats large numbers with locale separators', () => {
    expect(formatPrice(1000)).toBe('¥1,000');
    expect(formatPrice(1000000)).toBe('¥1,000,000');
  });

  it('formats decimal numbers', () => {
    expect(formatPrice(99.5)).toBe('¥99.5');
  });
});
