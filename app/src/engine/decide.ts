// Rule-based decision. Pure: no randomness, no clock. Every word the farmer sees
// comes from answers.json; this module only picks an id. Fail safe to ask_officer.
import { RULES, answerById } from './content';
import { seasonWindow } from './season';
import { LABELS } from './types';
import type { AnswerCard, Lang, PlotSummary, RuleCondition, SeasonWindow } from './types';

export const FALLBACK_ID = 'ask_officer';

/**
 * A plot check needs this many classified leaves (MASTER_PROMPT section 4: 10 leaves).
 * The rule thresholds in rules.json (for example 3 of 10 for rust) assume n = 10, so
 * a smaller plot never gets a rule answer: it gets TOO_FEW_ID (an "ask" card).
 * Kept in code, not in rules.json, so the Python mirrors in qa/ and the conformance
 * fixture generator (which enumerate n = 10 only) stay valid.
 */
export const MIN_LEAVES = 10;
export const TOO_FEW_ID = 'too_few_leaves';

/** True when every condition holds. An unknown key makes the rule not match. */
export function ruleMatches(cond: RuleCondition, s: PlotSummary, window: SeasonWindow): boolean {
  for (const [key, value] of Object.entries(cond) as [string, unknown][]) {
    // A non-numeric threshold gives NaN, and every comparison with NaN fails.
    const num = typeof value === 'number' ? value : Number.NaN;
    switch (key) {
      case 'dominant':
        if (s.dominant !== value) return false;
        break;
      case 'affected_gte':
        if (!(s.affected >= num)) return false;
        break;
      case 'affected_lte':
        if (!(s.affected <= num)) return false;
        break;
      case 'uncertain_gte':
        if (!(s.uncertain >= num)) return false;
        break;
      case 'n_lt':
        if (!(s.n < num)) return false;
        break;
      case 'distinct_problems_gte':
        if (!(s.distinctProblems >= num)) return false;
        break;
      case 'window':
        if (window !== value) return false;
        break;
      default:
        return false;
    }
  }
  return true;
}

export function getAnswer(id: string): AnswerCard {
  const entry = answerById(id) ?? answerById(FALLBACK_ID);
  if (!entry) {
    // Only reachable if answers.json lost ask_officer; the content tests guard this.
    return { id: FALLBACK_ID, severity: 'ask', text: {}, audio: {}, sources: [], assumption: true };
  }
  const audio: Partial<Record<Lang, string>> = {};
  for (const lang of Object.keys(entry.text) as Lang[]) audio[lang] = `/audio/${lang}/${entry.id}.mp3`;
  return {
    id: entry.id,
    severity: entry.severity,
    text: entry.text,
    notSure: entry.not_sure,
    audio,
    sources: entry.sources ?? [],
    assumption: entry.assumption,
    kind: entry.kind,
    reviewStatus: entry.review_status,
  };
}

const WINDOWS: readonly SeasonWindow[] = ['pre_short_rains', 'short_rains', 'pre_long_rains', 'long_rains', 'dry'];

const isCount = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v >= 0;

/**
 * True when the summary is safe to run through the rules: every number a finite,
 * non-negative integer, a known dominant label, and no part larger than the whole.
 * Deliberately not stricter (the QA matrix has unrealisable but well-formed rows).
 */
export function isValidSummary(s: unknown): s is PlotSummary {
  if (!s || typeof s !== 'object') return false;
  const x = s as Record<string, unknown>;
  const { n, uncertain, affected, distinctProblems, dominant, counts } = x;
  if (!isCount(n) || !isCount(uncertain) || !isCount(affected) || !isCount(distinctProblems)) return false;
  if (dominant !== 'none' && !(LABELS as readonly unknown[]).includes(dominant)) return false;
  if (!counts || typeof counts !== 'object') return false;
  let sum = 0;
  for (const l of LABELS) {
    const c = (counts as Record<string, unknown>)[l];
    if (!isCount(c) || c > n) return false;
    sum += c;
  }
  if (sum > n || affected + uncertain > n || distinctProblems > 4) return false;
  return true;
}

function isValidDate(d: unknown): d is Date {
  return d instanceof Date && Number.isFinite(d.getTime());
}

/** Never throws. Bad summary or unknown window gives the ask_officer card. */
export function decideForWindow(summary: PlotSummary, window: SeasonWindow): AnswerCard {
  try {
    if (!isValidSummary(summary) || !WINDOWS.includes(window)) return getAnswer(FALLBACK_ID);
    if (summary.n < MIN_LEAVES) return getAnswer(TOO_FEW_ID);
    const rule = RULES.find((r) => ruleMatches(r.if ?? {}, summary, window));
    return getAnswer(rule?.then ?? FALLBACK_ID);
  } catch {
    return getAnswer(FALLBACK_ID);
  }
}

/** Never throws. Bad summary or invalid date gives the ask_officer card. */
export function decide(summary: PlotSummary, date: Date): AnswerCard {
  try {
    if (!isValidSummary(summary) || !isValidDate(date)) return getAnswer(FALLBACK_ID);
    return decideForWindow(summary, seasonWindow(date));
  } catch {
    return getAnswer(FALLBACK_ID);
  }
}
