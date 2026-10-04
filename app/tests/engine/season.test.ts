import { describe, expect, it, vi } from 'vitest';
import { seasonWindow } from '../../src/engine/season';
import { SEASON } from '../../src/engine/content';
import type { SeasonWindow } from '../../src/engine/types';

// Local calendar dates at noon, so no time zone can shift the day.
const d = (y: number, m: number, day: number) => new Date(y, m - 1, day, 12);

describe('seasonWindow', () => {
  const cases: [number, number, SeasonWindow][] = [
    [10, 1, 'pre_short_rains'],
    [11, 5, 'pre_short_rains'],
    [11, 6, 'short_rains'],
    [12, 15, 'short_rains'],
    [12, 16, 'dry'],
    [12, 31, 'dry'],
    [1, 1, 'dry'],
    [2, 19, 'dry'],
    [2, 20, 'pre_long_rains'],
    [3, 31, 'pre_long_rains'],
    [4, 1, 'long_rains'],
    [5, 31, 'long_rains'],
    [6, 1, 'dry'],
    [9, 30, 'dry'],
  ];
  it.each(cases)('%i/%i -> %s', (m, day, want) => {
    expect(seasonWindow(d(2026, m, day))).toBe(want);
  });

  it('uses local time at the edges of the day', () => {
    expect(seasonWindow(new Date(2026, 10, 5, 23, 59))).toBe('pre_short_rains');
    expect(seasonWindow(new Date(2026, 10, 6, 0, 0))).toBe('short_rains');
  });

  it('leap day falls in dry-to-pre-long-rains correctly', () => {
    expect(seasonWindow(d(2028, 2, 29))).toBe('pre_long_rains');
  });

  it.each([2026, 2028])('every day of %i maps to a window without warning', (year) => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const names = new Set(SEASON.windows.map((w) => w.name));
    const days = year % 4 === 0 ? 366 : 365;
    for (let i = 0; i < days; i++) {
      const w = seasonWindow(new Date(year, 0, 1 + i, 12));
      expect(names.has(w)).toBe(true);
    }
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });
});
