// seasonWindow conformance against content/season.json.
import { describe, expect, it } from 'vitest';
import { need } from './engine-under-test';
import { season, WINDOWS } from './fixtures';
import type { SeasonWindow } from '../reference/types';

/** Independent oracle built from season.json, written differently from the reference. */
function oracle(month: number, day: number): SeasonWindow {
  const md = month * 100 + day;
  for (const w of season.windows) {
    const s = w.start_month * 100 + w.start_day;
    const e = w.end_month * 100 + w.end_day;
    const hit = w.wraps_year ? md >= s || md <= e : md >= s && md <= e;
    if (hit) return w.name;
  }
  throw new Error(`no window for ${month}/${day}`);
}

function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

function* daysOfYear(year: number): Generator<Date> {
  for (let d = new Date(year, 0, 1); d.getFullYear() === year; d = addDays(d, 1)) yield d;
}

describe('seasonWindow', () => {
  const seasonWindow = need('seasonWindow');

  it('season.json itself has only the five allowed window names and covers the year', () => {
    for (const w of season.windows) expect(WINDOWS).toContain(w.name);
    for (const d of daysOfYear(2026)) expect(() => oracle(d.getMonth() + 1, d.getDate())).not.toThrow();
  });

  it('Sun 4 Oct 2026 is pre_short_rains', () => {
    expect(seasonWindow(new Date(2026, 9, 4))).toBe('pre_short_rains');
    expect(seasonWindow(new Date(2026, 9, 4, 23, 59, 59))).toBe('pre_short_rains');
  });

  for (const year of [2026, 2028]) {
    const kind = year % 4 === 0 ? 'leap' : 'non-leap';
    describe(`${year} (${kind} year)`, () => {
      for (const w of season.windows) {
        const start = new Date(year, w.start_month - 1, w.start_day);
        const end = new Date(year, w.end_month - 1, w.end_day);
        const label = `${w.name} ${w.start_month}/${w.start_day} to ${w.end_month}/${w.end_day}`;

        it(`${label}: start day is inside`, () => expect(seasonWindow(start)).toBe(w.name));
        it(`${label}: end day is inside`, () => expect(seasonWindow(end)).toBe(w.name));
        it(`${label}: day before start belongs to another window (and matches season.json)`, () => {
          const d = addDays(start, -1);
          const got = seasonWindow(d);
          expect(got).toBe(oracle(d.getMonth() + 1, d.getDate()));
          // Both 'dry' windows share a name, so only assert a change when the name differs.
          if (oracle(d.getMonth() + 1, d.getDate()) !== w.name) expect(got).not.toBe(w.name);
        });
        it(`${label}: day after end belongs to another window (and matches season.json)`, () => {
          const d = addDays(end, 1);
          const got = seasonWindow(d);
          expect(got).toBe(oracle(d.getMonth() + 1, d.getDate()));
          if (oracle(d.getMonth() + 1, d.getDate()) !== w.name) expect(got).not.toBe(w.name);
        });
      }

      it('every day of the year maps to exactly one window and agrees with season.json', () => {
        const seen = new Map<SeasonWindow, number>();
        let days = 0;
        for (const d of daysOfYear(year)) {
          days++;
          const got = seasonWindow(d);
          expect(WINDOWS, d.toDateString()).toContain(got);
          expect(got, d.toDateString()).toBe(oracle(d.getMonth() + 1, d.getDate()));
          seen.set(got, (seen.get(got) ?? 0) + 1);
        }
        expect(days).toBe(year % 4 === 0 ? 366 : 365);
        expect([...seen.values()].reduce((a, b) => a + b, 0)).toBe(days);
        for (const w of WINDOWS) expect(seen.get(w), w).toBeGreaterThan(0);
      });
    });
  }

  it('29 Feb 2028 is pre_long_rains (the leap day falls inside 20 Feb to 31 Mar)', () => {
    expect(seasonWindow(new Date(2028, 1, 29))).toBe('pre_long_rains');
  });

  it('the wrapping dry window covers both 31 Dec and 1 Jan', () => {
    expect(seasonWindow(new Date(2026, 11, 31))).toBe('dry');
    expect(seasonWindow(new Date(2027, 0, 1))).toBe('dry');
  });

  it('ignores the year: same calendar day in different years gives the same window', () => {
    for (const y of [2000, 2026, 2027, 2100]) expect(seasonWindow(new Date(y, 6, 15))).toBe('dry');
  });
});
