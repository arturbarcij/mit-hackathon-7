import seasonFile from '../content/season.json' with { type: 'json' }
import type { SeasonWindow } from './types.ts'

interface SeasonWindowSpec {
  name: string
  start_month: number
  start_day: number
  end_month: number
  end_day: number
  wraps_year?: boolean
}

const windows = seasonFile.windows as SeasonWindowSpec[]

/**
 * Map the research calendar onto the five decision windows.
 * Spray windows win over the rain windows they overlap, because the decision
 * is whether to spray before the rains (S03).
 * A date within 14 days before a spray window is included. season.json says
 * to treat window edges as plus or minus two weeks. That lead-in is an
 * assumption so the week before mid-October is the spray decision, not a dry
 * week. 3 Oct 2026 is inside that lead-in.
 */
const EDGE_LEAD_DAYS = 14

export function seasonWindow(date: Date): SeasonWindow {
  const shortSpray = spec('spray_before_short_rains')
  const longSpray = spec('spray_before_long_rains')

  if (contains(date, shortSpray) || daysBeforeStart(date, shortSpray) <= EDGE_LEAD_DAYS) {
    return 'pre_short_rains'
  }
  if (
    (contains(date, longSpray) && !contains(date, spec('long_rains'))) ||
    daysBeforeStart(date, longSpray) <= EDGE_LEAD_DAYS
  ) {
    return 'pre_long_rains'
  }
  if (contains(date, spec('short_rains'))) return 'short_rains'
  if (contains(date, spec('long_rains'))) return 'long_rains'
  return 'dry'
}

function spec(name: string): SeasonWindowSpec {
  const found = windows.find((item) => item.name === name)
  if (!found) throw new Error(`Missing season window ${name}`)
  return found
}

function monthDay(date: Date): number {
  return (date.getMonth() + 1) * 100 + date.getDate()
}

function contains(date: Date, window: SeasonWindowSpec): boolean {
  const cur = monthDay(date)
  const start = window.start_month * 100 + window.start_day
  const end = window.end_month * 100 + window.end_day
  if (window.wraps_year || start > end) return cur >= start || cur <= end
  return cur >= start && cur <= end
}

function daysBeforeStart(date: Date, window: SeasonWindowSpec): number {
  const start = new Date(date.getFullYear(), window.start_month - 1, window.start_day)
  const from = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate())
  const to = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate())
  const days = Math.round((to - from) / 86_400_000)
  if (days <= 0) return Number.POSITIVE_INFINITY
  return days
}
