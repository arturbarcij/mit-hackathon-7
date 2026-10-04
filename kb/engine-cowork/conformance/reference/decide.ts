// decide(summary, date): evaluate content/rules.json in order, first match wins,
// and return an AnswerCard built from content/answers.json. Pure, no randomness,
// never composes text.
import rulesJson from '../content/rules.json';
import answersJson from '../content/answers.json';
import { seasonWindow } from './season';
import type { AnswerCard, Lang, PlotSummary, SeasonWindow } from './types';

export interface RuleCondition {
  dominant?: string;
  affected_gte?: number;
  affected_lte?: number;
  uncertain_gte?: number;
  distinct_problems_gte?: number;
  window?: SeasonWindow;
}
export interface Rule { if: RuleCondition; then: string; }

// Shape of one entry in answers.json (content-voice owns the file).
export interface AnswerEntry {
  id: string;
  kind?: string;
  severity: AnswerCard['severity'];
  text: Partial<Record<Lang, string>>;
  not_sure?: Partial<Record<Lang, string>>;
  sources?: string[];
  assumption?: boolean;
}

export const RULES = rulesJson as Rule[];
export const ANSWERS = answersJson as AnswerEntry[];
const ANSWERS_BY_ID = new Map(ANSWERS.map((a) => [a.id, a]));
export const CATCH_ALL = 'ask_officer';
const LANGS: Lang[] = ['sw', 'kik', 'en'];

export function matches(cond: RuleCondition, s: PlotSummary, window: SeasonWindow): boolean {
  if (cond.dominant !== undefined && s.dominant !== cond.dominant) return false;
  if (cond.affected_gte !== undefined && !(s.affected >= cond.affected_gte)) return false;
  if (cond.affected_lte !== undefined && !(s.affected <= cond.affected_lte)) return false;
  if (cond.uncertain_gte !== undefined && !(s.uncertain >= cond.uncertain_gte)) return false;
  if (cond.distinct_problems_gte !== undefined && !(s.distinctProblems >= cond.distinct_problems_gte)) return false;
  if (cond.window !== undefined && window !== cond.window) return false;
  return true;
}

/** The answer id a summary resolves to in a given window. Exposed for tests. */
export function decideId(s: PlotSummary, window: SeasonWindow): string {
  for (const r of RULES) {
    if (matches(r.if ?? {}, s, window)) return r.then ?? CATCH_ALL;
  }
  return CATCH_ALL;
}

/** Build the AnswerCard for an id. Throws if the id is not in answers.json. */
export function answerCard(id: string): AnswerCard {
  const a = ANSWERS_BY_ID.get(id);
  if (!a) throw new Error(`answers.json has no entry '${id}'`);
  const text: Partial<Record<Lang, string>> = {};
  const audio: Partial<Record<Lang, string>> = {};
  for (const lang of LANGS) {
    const t = a.text?.[lang];
    if (typeof t === 'string' && t.length > 0) {
      text[lang] = t;
      audio[lang] = `/audio/${lang}/${a.id}.mp3`;
    }
  }
  const card: AnswerCard = {
    id: a.id,
    severity: a.severity,
    text,
    audio,
    sources: Array.isArray(a.sources) ? [...a.sources] : [],
    assumption: a.assumption === true,
  };
  if (a.not_sure && Object.keys(a.not_sure).length > 0) card.notSure = { ...a.not_sure };
  return card;
}

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  const window = seasonWindow(date);
  const id = decideId(summary, window);
  return answerCard(ANSWERS_BY_ID.has(id) ? id : CATCH_ALL);
}
