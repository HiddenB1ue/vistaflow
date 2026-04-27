import { describe, expect, it } from 'vitest';
import {
  appendNumberWheelInput,
  getNumberWheelDirection,
  getNumberWheelItems,
  getNumberWheelValue,
  normalizeNumberWheelInput,
} from './NumberWheel';

describe('NumberWheel helpers', () => {
  it('returns previous current and next values', () => {
    expect(getNumberWheelItems(12, { min: 0, max: 23 })).toEqual([11, 12, 13]);
  });

  it('wraps across range boundaries by default', () => {
    expect(getNumberWheelItems(0, { min: 0, max: 23 })).toEqual([23, 0, 1]);
    expect(getNumberWheelItems(23, { min: 0, max: 23 })).toEqual([22, 23, 0]);
  });

  it('supports stepped minute ranges', () => {
    expect(getNumberWheelItems(55, { min: 0, max: 55, step: 5 })).toEqual([50, 55, 0]);
    expect(getNumberWheelValue(0, -1, { min: 0, max: 55, step: 5 })).toBe(55);
  });

  it('can clamp instead of wrapping', () => {
    expect(getNumberWheelItems(0, { min: 0, max: 23, wrap: false })).toEqual([0, 0, 1]);
  });

  it('maps wheel delta to value direction', () => {
    expect(getNumberWheelDirection(100)).toBe(1);
    expect(getNumberWheelDirection(-100)).toBe(-1);
    expect(getNumberWheelDirection(0)).toBe(0);
  });

  it('normalizes keyboard numeric input by range and step', () => {
    expect(normalizeNumberWheelInput('23', { min: 0, max: 23 })).toBe(23);
    expect(normalizeNumberWheelInput('24', { min: 0, max: 23 })).toBeNull();
    expect(normalizeNumberWheelInput('15', { min: 0, max: 55, step: 5 })).toBe(15);
    expect(normalizeNumberWheelInput('17', { min: 0, max: 55, step: 5 })).toBeNull();
  });

  it('buffers numeric keyboard input until pad length is reached', () => {
    expect(appendNumberWheelInput('', '3', { padLength: 2 })).toBe('3');
    expect(appendNumberWheelInput('3', '1', { padLength: 2 })).toBe('31');
    expect(appendNumberWheelInput('31', '2', { padLength: 2 })).toBe('12');
  });
});
