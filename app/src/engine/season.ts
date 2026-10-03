import { loadContent } from './content';
import type { SeasonWindow } from './types';

export const SEASON_WINDOWS: readonly SeasonWindow[] = [
  'pre_short_rains',
  'short_rains',
  'pre_long_rains',
  'long_rains',
  'dry',
];

export interface SeasonRange {
  name: SeasonWindow;
  startMonth: number;
  startDay: number;
  endMonth: number;
  endDay: number;
}

function isWindowName(x: unknown): x is SeasonWindow {
  return typeof x === 'string' && (SEASON_WINDOWS as readonly string[]).includes(x);
}

function validDayOfMonth(m: unknown, d: unknown): boolean {
  return Number.isInteger(m) && Number.isInteger(d) && (m as number) >= 1 && (m as number) <= 12 && (d as number) >= 1 && (d as number) <= 31;
}

/** Accepts the research format `{ windows: [{ name, start_month, start_day, end_month, end_day }] }`. */
export function normaliseSeason(raw: unknown): SeasonRange[] {
  const list = Array.isArray(raw) ? raw : (raw as { windows?: unknown } | null)?.windows;
  if (!Array.isArray(list)) return [];
  const out: SeasonRange[] = [];
  for (const w of list) {
    if (!w || typeof w !== 'object') continue;
    const r = w as Record<string, unknown>;
    if (!isWindowName(r.name)) continue;
    if (!validDayOfMonth(r.start_month, r.start_day) || !validDayOfMonth(r.end_month, r.end_day)) continue;
    out.push({
      name: r.name,
      startMonth: r.start_month as number,
      startDay: r.start_day as number,
      endMonth: r.end_month as number,
      endDay: r.end_day as number,
    });
  }
  return out;
}

function ordinal(month: number, day: number): number {
  return month * 100 + day;
}

function inRange(range: SeasonRange, month: number, day: number): boolean {
  const start = ordinal(range.startMonth, range.startDay);
  const end = ordinal(range.endMonth, range.endDay);
  const now = ordinal(month, day);
  return start <= end ? now >= start && now <= end : now >= start || now <= end;
}

/** First listed window that contains the date wins. Anything uncovered is `dry`. */
export function seasonWindowFrom(ranges: SeasonRange[], date: Date): SeasonWindow {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  for (const r of ranges) {
    if (inRange(r, month, day)) return r.name;
  }
  return 'dry';
}

let cached: SeasonRange[] | null = null;

export function seasonWindow(date: Date): SeasonWindow {
  cached ??= normaliseSeason(loadContent().season);
  return seasonWindowFrom(cached, date);
}
