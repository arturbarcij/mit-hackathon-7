import { getAnswer, getRules, toCard, type RuleIf } from './content.ts'
import type { AnswerCard, PlotSummary } from './types.ts'
import { seasonWindow } from './season.ts'

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  const window = seasonWindow(date)
  for (const rule of getRules()) {
    if (matches(rule.if, summary, window)) {
      const record = getAnswer(rule.then) ?? getAnswer('ask_officer')
      if (!record) throw new Error('ask_officer is missing from the answer bank')
      return toCard(record, Boolean(rule.assumption))
    }
  }
  const fallback = getAnswer('ask_officer')
  if (!fallback) throw new Error('ask_officer is missing from the answer bank')
  return toCard(fallback, false)
}

function matches(condition: RuleIf, summary: PlotSummary, window: string): boolean {
  if (condition.uncertain_gte != null && summary.uncertain < condition.uncertain_gte) return false
  if (condition.dominant != null && summary.dominant !== condition.dominant) return false
  if (condition.affected_gte != null && summary.affected < condition.affected_gte) return false
  if (condition.affected_lte != null && summary.affected > condition.affected_lte) return false
  if (condition.distinct_problems_gte != null && summary.distinctProblems < condition.distinct_problems_gte) return false
  if (condition.window != null && condition.window !== window) return false
  return true
}
