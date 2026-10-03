import { describe, expect, it } from 'vitest';
import { seasonWindow } from '../../src/engine/decide.ts';

function utc(year: number, month: number, day: number): Date {
  return new Date(Date.UTC(year, month - 1, day));
}

describe('seasonWindow', () => {
  it('places the demo week and the season boundaries', () => {
    expect(seasonWindow(utc(2026, 10, 4))).toBe('pre_short_rains');
    expect(seasonWindow(utc(2026, 10, 15))).toBe('short_rains');
    expect(seasonWindow(utc(2026, 3, 20))).toBe('long_rains');
    expect(seasonWindow(utc(2026, 2, 25))).toBe('pre_long_rains');
    expect(seasonWindow(utc(2026, 7, 1))).toBe('dry');
  });

  it('keeps the inclusive edges', () => {
    expect(seasonWindow(utc(2026, 2, 19))).toBe('dry');
    expect(seasonWindow(utc(2026, 2, 20))).toBe('pre_long_rains');
    expect(seasonWindow(utc(2026, 3, 14))).toBe('pre_long_rains');
    expect(seasonWindow(utc(2026, 3, 15))).toBe('long_rains');
    expect(seasonWindow(utc(2026, 10, 14))).toBe('pre_short_rains');
    expect(seasonWindow(utc(2026, 12, 15))).toBe('short_rains');
    expect(seasonWindow(utc(2026, 12, 16))).toBe('dry');
  });
});
