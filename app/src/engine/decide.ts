import { loadContent } from './content';
import { seasonWindow } from './season';
import type { AnswerCard, Lang, PlotSummary, SeasonWindow } from './types';

export const FALLBACK_ID = 'ask_officer';
const LANGS: readonly Lang[] = ['sw', 'kik', 'en'];
const SEVERITIES = ['ok', 'watch', 'act', 'ask'] as const;

export interface RuleCondition {
  dominant?: string | string[];
  affected_gte?: number;
  affected_lte?: number;
  uncertain_gte?: number;
  uncertain_lte?: number;
  distinct_problems_gte?: number;
  window?: string | string[];
}

export interface Rule { if: RuleCondition; then: string }

const KNOWN_KEYS = new Set([
  'dominant',
  'affected_gte',
  'affected_lte',
  'uncertain_gte',
  'uncertain_lte',
  'distinct_problems_gte',
  'window',
]);

/** Used only if answers.json has no `ask_officer` entry at all. Never shown with real content. */
const LAST_RESORT: AnswerCard = {
  id: FALLBACK_ID,
  severity: 'ask',
  text: { en: 'Not sure. Ask the extension officer.' },
  notSure: { en: 'The tool does not have enough to give an answer.' },
  audio: {},
  sources: [],
  assumption: true,
};

export function normaliseRules(raw: unknown): Rule[] {
  const list = Array.isArray(raw) ? raw : (raw as { rules?: unknown } | null)?.rules;
  if (!Array.isArray(list)) return [];
  const out: Rule[] = [];
  for (const r of list) {
    if (!r || typeof r !== 'object') continue;
    const rec = r as Record<string, unknown>;
    if (typeof rec.then !== 'string' || typeof rec.if !== 'object' || rec.if === null) continue;
    out.push({ if: rec.if as RuleCondition, then: rec.then });
  }
  return out;
}

function asList(v: string | string[]): string[] {
  return Array.isArray(v) ? v : [v];
}

/** An unknown key or a malformed value makes the rule fail to match, so the table falls through to ask_officer. */
export function ruleMatches(cond: RuleCondition, summary: PlotSummary, window: SeasonWindow): boolean {
  for (const [key, value] of Object.entries(cond)) {
    if (!KNOWN_KEYS.has(key)) return false;
    switch (key) {
      case 'dominant':
        if (!asList(value as string | string[]).includes(summary.dominant)) return false;
        break;
      case 'window':
        if (!asList(value as string | string[]).includes(window)) return false;
        break;
      case 'affected_gte':
        if (typeof value !== 'number' || !(summary.affected >= value)) return false;
        break;
      case 'affected_lte':
        if (typeof value !== 'number' || !(summary.affected <= value)) return false;
        break;
      case 'uncertain_gte':
        if (typeof value !== 'number' || !(summary.uncertain >= value)) return false;
        break;
      case 'uncertain_lte':
        if (typeof value !== 'number' || !(summary.uncertain <= value)) return false;
        break;
      case 'distinct_problems_gte':
        if (typeof value !== 'number' || !(summary.distinctProblems >= value)) return false;
        break;
    }
  }
  return true;
}

export function pickAnswerId(rules: Rule[], summary: PlotSummary, window: SeasonWindow): string {
  for (const rule of rules) {
    if (ruleMatches(rule.if, summary, window)) return rule.then;
  }
  return FALLBACK_ID;
}

type AnswerBank = Map<string, AnswerCard>;

function textMap(v: unknown): Partial<Record<Lang, string>> {
  const out: Partial<Record<Lang, string>> = {};
  if (v && typeof v === 'object') {
    for (const lang of LANGS) {
      const s = (v as Record<string, unknown>)[lang];
      if (typeof s === 'string' && s.trim() !== '') out[lang] = s;
    }
  }
  return out;
}

/** Accepts an array of entries with `id`, or an object keyed by id. */
export function normaliseAnswers(raw: unknown): AnswerBank {
  const bank: AnswerBank = new Map();
  let entries: [string | undefined, unknown][] = [];
  if (Array.isArray(raw)) {
    entries = raw.map((e) => [(e as { id?: string } | null)?.id, e]);
  } else if (raw && typeof raw === 'object') {
    const obj = raw as Record<string, unknown>;
    const inner = Array.isArray(obj.answers) ? obj.answers : null;
    entries = inner ? inner.map((e) => [(e as { id?: string } | null)?.id, e]) : Object.entries(obj);
  }
  for (const [keyOrId, value] of entries) {
    if (!value || typeof value !== 'object') continue;
    const e = value as Record<string, unknown>;
    const id = typeof e.id === 'string' ? e.id : keyOrId;
    if (!id) continue;
    const text = textMap(e.text);
    const notSure = textMap(e.not_sure ?? e.notSure);
    const audio: Partial<Record<Lang, string>> = {};
    for (const lang of Object.keys(text) as Lang[]) audio[lang] = `/audio/${lang}/${id}.mp3`;
    const severity = (SEVERITIES as readonly unknown[]).includes(e.severity)
      ? (e.severity as AnswerCard['severity'])
      : 'ask';
    bank.set(id, {
      id,
      severity,
      text,
      ...(Object.keys(notSure).length > 0 ? { notSure } : {}),
      audio,
      sources: Array.isArray(e.sources) ? e.sources.filter((s): s is string => typeof s === 'string') : [],
      assumption: e.assumption === true,
    });
  }
  return bank;
}

export function cardFor(bank: AnswerBank, id: string): AnswerCard {
  return bank.get(id) ?? bank.get(FALLBACK_ID) ?? LAST_RESORT;
}

export interface DecideContent { rules: Rule[]; answers: AnswerBank; window: SeasonWindow }

/** Pure: same summary and content always give the same card. Never composes text. */
export function decideWith(summary: PlotSummary, content: DecideContent): AnswerCard {
  if (summary.n <= 0) return cardFor(content.answers, FALLBACK_ID);
  const id = pickAnswerId(content.rules, summary, content.window);
  return cardFor(content.answers, id);
}

let cache: { rules: Rule[]; answers: AnswerBank } | null = null;

function bundled() {
  if (!cache) {
    const c = loadContent();
    cache = { rules: normaliseRules(c.rules), answers: normaliseAnswers(c.answers) };
  }
  return cache;
}

export function decide(summary: PlotSummary, date: Date): AnswerCard {
  const { rules, answers } = bundled();
  return decideWith(summary, { rules, answers, window: seasonWindow(date) });
}

/** Every answer id the bundled rule table can return, plus the fallback. Used by tests. */
export function bundledRuleTargets(): string[] {
  const ids = new Set(bundled().rules.map((r) => r.then));
  ids.add(FALLBACK_ID);
  return [...ids];
}

export function bundledAnswerIds(): string[] {
  return [...bundled().answers.keys()];
}

export function answerById(id: string): AnswerCard | undefined {
  return bundled().answers.get(id);
}
