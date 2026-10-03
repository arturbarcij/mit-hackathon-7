import answersJson from '../content/answers.json' with { type: 'json' };
import rulesJson from '../content/rules.json' with { type: 'json' };
import type { AnswerCard, Lang, PlotSummary, SeasonWindow } from './types.ts';

// Season windows are an assumption aligned to kb/research/season.json.
// Research marks long rains from 15 Mar and short rains from 15 Oct, with a
// drier spell from 1 Jun. pre_long_rains (20 Feb to 14 Mar) and
// pre_short_rains (1 Oct to 14 Oct) fill the gaps before those onsets.
// The demo week of 4 Oct 2026 sits in pre_short_rains, before the 15 Oct
// short-rain onset. Comparisons use UTC month and day so tests do not drift.

const LANGS: readonly Lang[] = ['sw', 'kik', 'en'];
const SEVERITIES = new Set<AnswerCard['severity']>(['ok', 'watch', 'act', 'ask']);

interface RuleIf {
  dominant?: string;
  affected_gte?: number;
  affected_lte?: number;
  uncertain_gte?: number;
  distinct_problems_gte?: number;
  window?: string;
}

interface Rule {
  if?: RuleIf;
  then: string;
}

interface AnswerEntry {
  id?: string;
  severity?: string;
  text?: Partial<Record<Lang, string | null>>;
  not_sure?: Partial<Record<Lang, string | null>>;
  sources?: string[];
  assumption?: boolean;
}

function asRules(value: unknown): Rule[] {
  if (Array.isArray(value)) return value as Rule[];
  if (value && typeof value === 'object' && Array.isArray((value as { rules?: unknown }).rules)) {
    return (value as { rules: Rule[] }).rules;
  }
  return [];
}

function asAnswers(value: unknown): AnswerEntry[] {
  if (Array.isArray(value)) return value as AnswerEntry[];
  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, AnswerEntry>).map(([id, entry]) => ({
      ...entry,
      id: entry?.id ?? id,
    }));
  }
  return [];
}

const rules = asRules(rulesJson);
const answers = asAnswers(answersJson);

export function seasonWindow(date: Date): SeasonWindow {
  const key = (date.getUTCMonth() + 1) * 100 + date.getUTCDate();
  if (key >= 220 && key <= 314) return 'pre_long_rains';
  if (key >= 315 && key <= 531) return 'long_rains';
  if (key >= 601 && key <= 930) return 'dry';
  if (key >= 1001 && key <= 1014) return 'pre_short_rains';
  if (key >= 1015 && key <= 1215) return 'short_rains';
  return 'dry';
}

function textMap(raw: Partial<Record<Lang, string | null>> | undefined): Partial<Record<Lang, string>> {
  const out: Partial<Record<Lang, string>> = {};
  if (!raw) return out;
  for (const lang of LANGS) {
    const value = raw[lang];
    if (typeof value === 'string' && value.length > 0) out[lang] = value;
  }
  return out;
}

function findAnswer(id: string): AnswerEntry | undefined {
  return answers.find((entry) => entry.id === id);
}

function cardFrom(entry: AnswerEntry, id: string): AnswerCard {
  const text = textMap(entry.text);
  const audio: Partial<Record<Lang, string>> = {};
  for (const lang of LANGS) {
    if (text[lang]) audio[lang] = `/audio/${lang}/${id}.mp3`;
  }
  const notSure = textMap(entry.not_sure);
  const severity = SEVERITIES.has(entry.severity as AnswerCard['severity'])
    ? (entry.severity as AnswerCard['severity'])
    : 'ask';
  const card: AnswerCard = {
    id,
    severity,
    text,
    audio,
    sources: Array.isArray(entry.sources) ? entry.sources.filter((source) => typeof source === 'string') : [],
    assumption: entry.assumption === true,
  };
  if (Object.keys(notSure).length > 0) card.notSure = notSure;
  return card;
}

function askOfficerCard(): AnswerCard {
  const entry = findAnswer('ask_officer');
  if (entry) return cardFrom(entry, 'ask_officer');
  return {
    id: 'ask_officer',
    severity: 'ask',
    text: {},
    audio: {},
    sources: [],
    assumption: true,
  };
}

function cardFor(id: string): AnswerCard {
  const entry = findAnswer(id);
  if (!entry) return askOfficerCard();
  return cardFrom(entry, id);
}

function matches(condition: RuleIf, summary: PlotSummary, window: SeasonWindow): boolean {
  if (condition.dominant !== undefined && condition.dominant !== summary.dominant) return false;
  if (condition.affected_gte !== undefined && summary.affected < condition.affected_gte) return false;
  if (condition.affected_lte !== undefined && summary.affected > condition.affected_lte) return false;
  if (condition.uncertain_gte !== undefined && summary.uncertain < condition.uncertain_gte) return false;
  if (condition.distinct_problems_gte !== undefined && summary.distinctProblems < condition.distinct_problems_gte) {
    return false;
  }
  if (condition.window !== undefined && condition.window !== window) return false;
  return true;
}

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  const window = seasonWindow(date);
  for (const rule of rules) {
    if (matches(rule.if ?? {}, summary, window)) return cardFor(rule.then);
  }
  return askOfficerCard();
}
