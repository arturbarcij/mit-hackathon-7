import placeholderAnswers from './placeholders/answers.json';
import placeholderRules from './placeholders/rules.json';
import placeholderSeason from './placeholders/season.json';

/*
 * The content-voice agent owns src/content/{answers,rules,season}.json. Until a file lands there
 * the engine falls back to the placeholders in ./placeholders. The glob returns an empty object
 * when a file is missing, so the build never breaks on absent content.
 */
const answersFiles = import.meta.glob('../content/answers.json', { eager: true, import: 'default' });
const rulesFiles = import.meta.glob('../content/rules.json', { eager: true, import: 'default' });
const seasonFiles = import.meta.glob('../content/season.json', { eager: true, import: 'default' });

export interface ContentBundle {
  answers: unknown;
  rules: unknown;
  season: unknown;
  usingPlaceholders: { answers: boolean; rules: boolean; season: boolean };
}

function pick(files: Record<string, unknown>, fallback: unknown): { value: unknown; placeholder: boolean } {
  const first = Object.values(files)[0];
  return first === undefined ? { value: fallback, placeholder: true } : { value: first, placeholder: false };
}

export function loadContent(): ContentBundle {
  const a = pick(answersFiles, placeholderAnswers);
  const r = pick(rulesFiles, placeholderRules);
  const s = pick(seasonFiles, placeholderSeason);
  return {
    answers: a.value,
    rules: r.value,
    season: s.value,
    usingPlaceholders: { answers: a.placeholder, rules: r.placeholder, season: s.placeholder },
  };
}

interface AnswerRow {
  id: string;
  text: { en?: string; sw?: string; kik?: string };
}

interface RuleRow {
  if: Record<string, unknown>;
  then: string;
}

/**
 * Backward-compatible helper used by legacy tests.
 * Returns answers as an array regardless of source shape (object keyed by id or array).
 */
export function listAnswers(): AnswerRow[] {
  const raw = loadContent().answers as unknown;
  const entries = Array.isArray(raw)
    ? raw
    : raw && typeof raw === 'object'
      ? Array.isArray((raw as { answers?: unknown }).answers)
        ? ((raw as { answers: unknown[] }).answers ?? [])
        : Object.values(raw as Record<string, unknown>)
      : [];
  const out: AnswerRow[] = [];
  for (const item of entries) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    if (typeof row.id !== 'string') continue;
    const text = (row.text && typeof row.text === 'object' ? row.text : {}) as Record<string, unknown>;
    out.push({
      id: row.id,
      text: {
        en: typeof text.en === 'string' ? text.en : undefined,
        sw: typeof text.sw === 'string' ? text.sw : undefined,
        kik: typeof text.kik === 'string' ? text.kik : undefined,
      },
    });
  }
  return out;
}

export function getAnswer(id: string): AnswerRow | undefined {
  return listAnswers().find((row) => row.id === id);
}

export function textFor(record: { text: { en?: string; sw?: string; kik?: string } }, lang: 'sw' | 'kik' | 'en'): string {
  return record.text[lang] ?? record.text.sw ?? record.text.en ?? '';
}

/** Backward-compatible helper used by legacy tests. */
export function getRules(): RuleRow[] {
  const raw = loadContent().rules as unknown;
  const list = Array.isArray(raw)
    ? raw
    : raw && typeof raw === 'object' && Array.isArray((raw as { rules?: unknown }).rules)
      ? ((raw as { rules: unknown[] }).rules ?? [])
      : [];
  const out: RuleRow[] = [];
  for (const item of list) {
    if (!item || typeof item !== 'object') continue;
    const row = item as Record<string, unknown>;
    if (!row.if || typeof row.if !== 'object' || typeof row.then !== 'string') continue;
    out.push({ if: row.if as Record<string, unknown>, then: row.then });
  }
  return out;
}
