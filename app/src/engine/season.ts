// Season window for a date, from src/content/season.json. First match wins.
// Uses the local calendar date (getMonth/getDate), so the phone's own day counts.
import { SEASON } from './content';
import type { SeasonWindow, SeasonWindowDef } from './types';

function inWindow(w: SeasonWindowDef, monthDay: number): boolean {
  const start = w.start_month * 100 + w.start_day;
  const end = w.end_month * 100 + w.end_day;
  if (w.wraps_year || start > end) return monthDay >= start || monthDay <= end;
  return monthDay >= start && monthDay <= end;
}

export function seasonWindow(date: Date): SeasonWindow {
  const monthDay = (date.getMonth() + 1) * 100 + date.getDate();
  const hit = SEASON.windows.find((w) => inWindow(w, monthDay));
  if (hit) return hit.name;
  console.warn(`seasonWindow: no window covers ${date.getMonth() + 1}/${date.getDate()}, using 'dry'`);
  return 'dry';
}
