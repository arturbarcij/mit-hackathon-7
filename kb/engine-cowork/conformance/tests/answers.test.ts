// Content integrity: answers.json and rules.json as the engine consumes them.
// Word lists mirror app/qa/checks/content.py so both harnesses agree.
import { describe, expect, it } from 'vitest';
import { answers, answerIds, answersById, rules, season } from './fixtures';

// From content.py KIK_CORE (content-voice.md section 3 lists the same 8).
const KIK_CORE = ['how_to_pick_leaves', 'healthy_all', 'rust_high_pre_rains', 'too_many_unsure',
  'ask_officer', 'decision_act', 'decision_wait', 'decision_ask'];
const REQUIRED_IDS = [
  'how_to_pick_leaves', 'how_to_photograph', 'retake_blurry', 'retake_dark', 'not_a_leaf',
  'healthy_all', 'rust_low', 'rust_high_pre_rains', 'rust_high_in_rains', 'rust_high_dry',
  'cercospora', 'phoma', 'miner', 'mixed_problems', 'too_many_unsure', 'ask_officer',
  'berries_out_of_scope', 'other_crop',
  'consent_main', 'consent_photos', 'decision_act', 'decision_wait', 'decision_ask',
  'referral_ready', 'language_name',
];
const ALLOWED_CONDITIONS = new Set(['dominant', 'affected_gte', 'affected_lte', 'uncertain_gte', 'distinct_problems_gte', 'window']);
const ALLOWED_WINDOWS = new Set(['pre_short_rains', 'short_rains', 'pre_long_rains', 'long_rains', 'dry']);
const ALLOWED_SEVERITY = new Set(['ok', 'watch', 'act', 'ask']);
// content.py BANNED_WORDS, verbatim.
const BANNED_WORDS = ['mancozeb', 'chlorothalonil', 'copper oxychloride 50', 'ml per', 'g per litre',
  'grams per', 'litres per', 'revolutionise', 'empower', 'seamless', 'cutting-edge'];
// Extra dose patterns: a number followed by a dose unit. Not in content.py; reported, kept strict.
const DOSE_PATTERN = /\b\d+(\.\d+)?\s?(ml|l|g|kg|mg)\s?(\/|per)\s?(l|litre|liter|ha|acre|tree|pump|knapsack)\b/i;

describe('answers.json', () => {
  it('is a non-empty list with unique ids', () => {
    expect(Array.isArray(answers)).toBe(true);
    expect(answers.length).toBeGreaterThan(0);
    expect(answerIds.size).toBe(answers.length);
  });

  it('contains every required id', () => {
    const missing = REQUIRED_IDS.filter((id) => !answerIds.has(id));
    expect(missing).toEqual([]);
  });

  it('every answer has en and sw text', () => {
    for (const a of answers) {
      expect(a.text?.en, `${a.id}.text.en`).toBeTruthy();
      expect(a.text?.sw, `${a.id}.text.sw`).toBeTruthy();
    }
  });

  it('the 8 core ids have kik text', () => {
    for (const id of KIK_CORE) expect(answersById.get(id)?.text?.kik, `${id}.text.kik`).toBeTruthy();
  });

  it('severity is in the allowed set', () => {
    for (const a of answers) expect(ALLOWED_SEVERITY.has(a.severity), `${a.id}: ${a.severity}`).toBe(true);
  });

  it('no text contains a pesticide brand, a dose, or a marketing word', () => {
    const hits: string[] = [];
    for (const a of answers) {
      const blob = Object.values(a.text ?? {}).concat(Object.values(a.not_sure ?? {})).join(' ').toLowerCase();
      for (const w of BANNED_WORDS) if (blob.includes(w)) hits.push(`${a.id}: '${w}'`);
      if (DOSE_PATTERN.test(blob)) hits.push(`${a.id}: dose pattern`);
    }
    expect(hits).toEqual([]);
  });

  it('every result card has sources or an assumption flag', () => {
    for (const a of answers) {
      if ((a.kind ?? 'result') !== 'result') continue;
      expect((a.sources?.length ?? 0) > 0 || a.assumption === true, a.id).toBe(true);
    }
  });

  it('act and watch result cards carry a not_sure line', () => {
    for (const a of answers) {
      if ((a.kind ?? 'result') !== 'result') continue;
      if (a.severity === 'act' || a.severity === 'watch') expect(a.not_sure, a.id).toBeTruthy();
    }
  });

  it('no em dashes in any text', () => {
    for (const a of answers) {
      const blob = Object.values(a.text ?? {}).concat(Object.values(a.not_sure ?? {})).join(' ');
      expect(blob.includes('—'), a.id).toBe(false);
    }
  });
});

describe('rules.json', () => {
  it("every rule 'then' exists in answers.json", () => {
    for (const [i, r] of rules.entries()) expect(answerIds.has(r.then), `rule ${i} -> ${r.then}`).toBe(true);
  });

  it('only allowed condition keys and window names', () => {
    for (const [i, r] of rules.entries()) {
      for (const k of Object.keys(r.if ?? {})) expect(ALLOWED_CONDITIONS.has(k), `rule ${i}: ${k}`).toBe(true);
      if (r.if?.window !== undefined) expect(ALLOWED_WINDOWS.has(String(r.if.window)), `rule ${i}`).toBe(true);
    }
  });

  it('the last rule is the empty catch-all to ask_officer, and no earlier rule is empty', () => {
    const last = rules[rules.length - 1];
    expect(Object.keys(last.if ?? {})).toEqual([]);
    expect(last.then).toBe('ask_officer');
    for (const r of rules.slice(0, -1)) expect(Object.keys(r.if ?? {}).length).toBeGreaterThan(0);
  });

  it('numeric thresholds carry sources or an assumption flag', () => {
    for (const [i, r] of rules.entries()) {
      const numeric = Object.values(r.if ?? {}).some((v) => typeof v === 'number');
      const rr = r as Rule & { assumption?: boolean; sources?: string[] };
      if (numeric) expect(rr.assumption === true || (rr.sources?.length ?? 0) > 0, `rule ${i}`).toBe(true);
    }
  });
});

describe('season.json', () => {
  it('uses only the five window names and lists a source', () => {
    for (const w of season.windows) expect(ALLOWED_WINDOWS.has(w.name), w.name).toBe(true);
    const s = season as unknown as { source?: unknown; sources?: unknown };
    expect(Boolean(s.source || s.sources)).toBe(true);
  });
});

type Rule = (typeof rules)[number];
