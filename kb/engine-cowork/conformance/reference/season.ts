// seasonWindow(date) from content/season.json. One window per date, first match
// wins, windows cover the whole year. A window with wraps_year spans New Year.
// Only the calendar month and day matter; the year and the time of day do not.
import seasonJson from '../content/season.json';
import type { SeasonWindow } from './types';

interface WindowDef {
  name: SeasonWindow;
  start_month: number; start_day: number;
  end_month: number; end_day: number;
  wraps_year?: boolean;
}

const WINDOWS = (seasonJson as { windows: WindowDef[] }).windows;

/** Month and day as a single comparable number, e.g. 4 Oct -> 1004. */
function monthDay(month: number, day: number): number {
  return month * 100 + day;
}

export function seasonWindowFor(month: number, day: number): SeasonWindow {
  const md = monthDay(month, day);
  for (const w of WINDOWS) {
    const start = monthDay(w.start_month, w.start_day);
    const end = monthDay(w.end_month, w.end_day);
    const inside = w.wraps_year || start > end
      ? md >= start || md <= end
      : md >= start && md <= end;
    if (inside) return w.name;
  }
  // season.json promises full coverage. If it is edited and leaves a gap, fail loudly
  // rather than guess a season; decide() still falls through to ask_officer because
  // no window rule can match.
  throw new Error(`season.json has no window for month ${month} day ${day}`);
}

/**
 * Uses the local calendar date of the device. The farmer checks leaves where she
 * stands, so local date is the right reading; a UTC reading would be a day off
 * for a few hours each night in Kenya (UTC+3).
 */
export function seasonWindow(date: Date): SeasonWindow {
  return seasonWindowFor(date.getMonth() + 1, date.getDate());
}
