// Helpers shared by the tests: content fixtures and LeafResult builders.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Check, Label, LeafResult, PlotSummary, SeasonWindow } from '../reference/types';

const here = path.dirname(fileURLToPath(import.meta.url));
export const CONTENT_DIR = path.resolve(here, '../content');

export function readJson<T>(name: string): T {
  return JSON.parse(readFileSync(path.join(CONTENT_DIR, name), 'utf8')) as T;
}

export interface AnswerEntry {
  id: string; kind?: string; severity: string;
  text: Record<string, string>; not_sure?: Record<string, string>;
  sources?: string[]; assumption?: boolean;
}
export interface Rule { if: Record<string, string | number>; then: string; }
export interface SeasonFile {
  windows: { name: SeasonWindow; start_month: number; start_day: number; end_month: number; end_day: number; wraps_year?: boolean }[];
}

export const answers = readJson<AnswerEntry[]>('answers.json');
export const rules = readJson<Rule[]>('rules.json');
export const season = readJson<SeasonFile>('season.json');
export const answerIds = new Set(answers.map((a) => a.id));
export const answersById = new Map(answers.map((a) => [a.id, a]));

export const LABELS: Label[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];
export const DISEASES: Label[] = ['rust', 'cercospora', 'phoma', 'miner'];
export const WINDOWS: SeasonWindow[] = ['pre_short_rains', 'short_rains', 'pre_long_rains', 'long_rains', 'dry'];

export function emptyCounts(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 };
}

export function leaf(label: Label | 'unsure', confidence = 0.9): LeafResult {
  const probs = emptyCounts();
  if (label === 'unsure') {
    for (const l of LABELS) probs[l] = 1 / LABELS.length;
  } else {
    const rest = (1 - confidence) / (LABELS.length - 1);
    for (const l of LABELS) probs[l] = l === label ? confidence : rest;
  }
  return {
    label,
    probs,
    confidence: label === 'unsure' ? Math.min(confidence, 0.5) : confidence,
    quality: { ok: label !== 'unsure' || confidence > 0.3, blur: 0.8, brightness: 0.5 },
    abstained: label === 'unsure',
    modelVersion: 'fixture',
  };
}

/** Build leaves from a count map, e.g. { rust: 6, healthy: 4 }. Order: as given. */
export function leavesFrom(counts: Partial<Record<Label | 'unsure', number>>): LeafResult[] {
  const out: LeafResult[] = [];
  for (const [label, n] of Object.entries(counts)) {
    for (let i = 0; i < (n ?? 0); i++) out.push(leaf(label as Label | 'unsure'));
  }
  return out;
}

/** A representative date inside each window (2026). */
export const DATE_IN_WINDOW: Record<SeasonWindow, Date> = {
  pre_short_rains: new Date(2026, 9, 4),   // Sun 4 Oct 2026
  short_rains: new Date(2026, 10, 20),     // 20 Nov
  dry: new Date(2026, 0, 15),              // 15 Jan
  pre_long_rains: new Date(2026, 2, 10),   // 10 Mar
  long_rains: new Date(2026, 3, 20),       // 20 Apr
};

/** Abstract summary in the shape decision_matrix.py enumerates. counts are filled best-effort. */
export function abstractSummary(dominant: Label | 'none', affected: number, uncertain: number, distinct: number, n = 10): PlotSummary {
  const counts = emptyCounts();
  if (affected > 0 && dominant !== 'healthy' && dominant !== 'none') {
    // dominant label gets the bulk, the other (distinct - 1) disease labels get one each
    const others = DISEASES.filter((d) => d !== dominant).slice(0, Math.max(0, distinct - 1));
    for (const o of others) counts[o] = 1;
    const lead = dominant === 'not_leaf' ? 'rust' : dominant;
    counts[lead] += affected - others.length;
  }
  if (dominant === 'not_leaf') counts.not_leaf = Math.min(uncertain, n);
  counts.healthy = Math.max(0, n - affected - uncertain);
  return { n, counts, uncertain, dominant, affected, distinctProblems: distinct };
}

export function checkFrom(partial: Partial<Check> & { leaves: LeafResult[]; summary: PlotSummary }): Check {
  return {
    id: 'chk_test',
    createdAt: '2026-10-04T09:30:00.000Z',
    lang: 'sw',
    window: 'pre_short_rains',
    answerId: 'ask_officer',
    decision: 'ask',
    memberId: 'OCC0412',
    plotId: '2',
    consentMain: true,
    consentPhotos: false,
    synced: false,
    ...partial,
  };
}

/** Small deterministic PRNG (mulberry32) so random tests are reproducible. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
