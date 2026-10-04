// seasonWindow for every day of a normal and a leap year, against season.json semantics:
// windows are month/day ranges, inclusive at both ends; a range whose start is after its end
// (wraps_year) runs over New Year; the first window that contains the day wins.
import { describe, expect, it } from 'vitest';
import * as engine from '@engine';
import { season } from './helpers';

const seasonWindow = (engine as any).seasonWindow as (d: Date) => string;
const WINDOWS = ['pre_short_rains', 'short_rains', 'pre_long_rains', 'long_rains', 'dry'];

function oracle(m: number, d: number): string | undefined {
  const md = m * 100 + d;
  for (const w of season.windows) {
    const s = w.start_month * 100 + w.start_day, e = w.end_month * 100 + w.end_day;
    if (s <= e ? md >= s && md <= e : md >= s || md <= e) return w.name;
  }
  return undefined;
}

describe('season.json itself', () => {
  it('uses only the five SeasonWindow names', () => {
    for (const w of season.windows) expect(WINDOWS).toContain(w.name);
  });
  it('covers every day of a leap year', () => {
    const gaps: string[] = [];
    for (let t = new Date(2028, 0, 1, 12); t.getFullYear() === 2028; t = new Date(t.getFullYear(), t.getMonth(), t.getDate() + 1, 12))
      if (!oracle(t.getMonth() + 1, t.getDate())) gaps.push(`${t.getMonth() + 1}/${t.getDate()}`);
    expect(gaps).toEqual([]);
  });
  it('marks every window that runs over New Year with wraps_year', () => {
    for (const w of season.windows) {
      const wraps = w.start_month * 100 + w.start_day > w.end_month * 100 + w.end_day;
      expect(Boolean(w.wraps_year), w.name).toBe(wraps);
    }
  });
});

describe('seasonWindow', () => {
  it('is exported', () => expect(typeof seasonWindow).toBe('function'));

  for (const year of [2026, 2028]) {
    it(`matches season.json on every day of ${year} (local noon)`, () => {
      const bad: string[] = [];
      for (let t = new Date(year, 0, 1, 12); t.getFullYear() === year; t = new Date(t.getFullYear(), t.getMonth(), t.getDate() + 1, 12)) {
        const want = oracle(t.getMonth() + 1, t.getDate());
        let got: string;
        try { got = seasonWindow(t); } catch (e) { got = `threw ${(e as Error).message}`; }
        if (got !== want) bad.push(`${t.getMonth() + 1}/${t.getDate()}: got ${got}, want ${want}`);
      }
      expect(bad.slice(0, 8), `${bad.length} days wrong`).toEqual([]);
    });
  }

  const edges: [string, string][] = [
    ['2026-09-30', 'dry'], ['2026-10-01', 'pre_short_rains'], ['2026-10-04', 'pre_short_rains'], ['2026-11-05', 'pre_short_rains'],
    ['2026-11-06', 'short_rains'], ['2026-12-15', 'short_rains'], ['2026-12-16', 'dry'], ['2026-12-31', 'dry'],
    ['2027-01-01', 'dry'], ['2027-02-19', 'dry'], ['2027-02-20', 'pre_long_rains'], ['2028-02-29', 'pre_long_rains'],
    ['2027-03-31', 'pre_long_rains'], ['2027-04-01', 'long_rains'], ['2027-05-31', 'long_rains'], ['2027-06-01', 'dry'],
  ];
  it.each(edges)('%s is %s', (iso, want) => {
    const [y, m, d] = iso.split('-').map(Number);
    expect(seasonWindow(new Date(y, m - 1, d, 12))).toBe(want);
  });

  it('uses the local calendar day in Kenya (00:30 on 1 Oct is already pre_short_rains)', () => {
    expect(process.env.TZ).toBeTruthy();
    expect(seasonWindow(new Date(2026, 9, 1, 0, 30))).toBe('pre_short_rains');
    expect(seasonWindow(new Date(2026, 8, 30, 23, 30))).toBe('dry');
  });
});
