// Shared helpers: content loading, leaf factories, a seeded PRNG, and field-name normalisers
// so the suite does not depend on one engine's internal naming.
import { readFileSync } from 'node:fs';
import path from 'node:path';

export const ENGINE_DIR = process.env.CONF_ENGINE_DIR!;
export const CONTENT_DIR = process.env.CONF_CONTENT_DIR!;
export const LOVABLE_UI_DIR = process.env.CONF_LOVABLE_UI_DIR!;

export const readJson = <T = any>(p: string): T => JSON.parse(readFileSync(p, 'utf-8'));
export const answers: any[] = readJson(path.join(CONTENT_DIR, 'answers.json'));
export const rules: any[] = readJson(path.join(CONTENT_DIR, 'rules.json'));
export const season: any = readJson(path.join(CONTENT_DIR, 'season.json'));
export const answersById = new Map(answers.map((a) => [a.id, a]));

export const LABELS = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'] as const;
export const DISEASES = ['rust', 'cercospora', 'phoma', 'miner'] as const;
export type AnyLabel = (typeof LABELS)[number] | 'unsure';

export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** A consistent LeafResult: 'unsure' leaves are abstained; failed-quality leaves are always 'unsure'. */
export function leaf(label: AnyLabel, confidence = label === 'unsure' ? 0.41 : 0.9, qualityOk = true): any {
  const probs: Record<string, number> = Object.fromEntries(LABELS.map((l) => [l, (1 - confidence) / 5]));
  if (label !== 'unsure') probs[label] = confidence;
  else probs.healthy = confidence;
  return {
    label,
    probs,
    confidence,
    quality: qualityOk ? { ok: true, blur: 120, brightness: 0.55 } : { ok: false, reason: 'blurry', blur: 4, brightness: 0.5 },
    abstained: label === 'unsure',
    modelVersion: 'conformance-fixture',
  };
}

export const leaves = (spec: Partial<Record<AnyLabel, number>>) =>
  (Object.entries(spec) as [AnyLabel, number][]).flatMap(([l, k]) => Array.from({ length: k }, () => leaf(l)));

/** Local noon on a calendar day: robust to engines that read local or UTC date parts. */
export const day = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d, 12, 0, 0);
};

export function makeCheck(over: Partial<any> = {}): any {
  const ls = over.leaves ?? leaves({ rust: 6, miner: 1, unsure: 1, healthy: 2 });
  return {
    id: 'chk-1', createdAt: day('2026-10-04').toISOString(), lang: 'sw',
    leaves: ls, summary: over.summary, window: 'pre_short_rains', answerId: 'rust_high_pre_rains', decision: 'ask',
    memberId: 'OCC0412', plotId: 'P07', consentMain: true, consentPhotos: false, synced: false, ...over,
  };
}

const pick = (o: any, keys: string[]) => {
  for (const k of keys) {
    const parts = k.split('.');
    let v = o;
    for (const p of parts) v = v == null ? undefined : v[p];
    if (v !== undefined) return v;
  }
  return undefined;
};
const toYmd = (v: any): string | undefined => {
  if (v == null) return undefined;
  if (v instanceof Date) return `${v.getFullYear()}${String(v.getMonth() + 1).padStart(2, '0')}${String(v.getDate()).padStart(2, '0')}`;
  const s = String(v);
  if (/^\d{8}$/.test(s)) return s;
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10).replace(/-/g, '');
  return s;
};
const toPct = (v: any): number | undefined => (v == null ? undefined : Number(v) <= 1 && Number(v) > 0 && !Number.isInteger(Number(v)) ? Math.round(Number(v) * 100) : Number(v));
const nullish = (v: any) => (v === undefined || v === null || v === '' || v === '-' ? null : v);

/** Maps a ParsedReferral of any reasonable shape to one canonical record. */
export function normaliseParsed(p: any) {
  if (!p) return p;
  return {
    memberId: nullish(pick(p, ['memberId', 'member_id', 'member', 'M'])),
    plotId: nullish(pick(p, ['plotId', 'plot_id', 'plot', 'P'])),
    date: toYmd(pick(p, ['date', 'checkDate', 'check_date', 'D'])),
    n: Number(pick(p, ['n', 'N', 'leaves']) ?? (p.counts ? Object.values(p.counts).reduce((a: number, b: any) => a + Number(b), 0) + Number(pick(p, ['uncertain', 'unsure', 'U']) ?? 0) : undefined)),
    rust: Number(pick(p, ['rust', 'counts.rust', 'R'])),
    cercospora: Number(pick(p, ['cercospora', 'counts.cercospora', 'C'])),
    phoma: Number(pick(p, ['phoma', 'counts.phoma', 'H'])),
    miner: Number(pick(p, ['miner', 'counts.miner', 'L'])),
    uncertain: Number(pick(p, ['uncertain', 'unsure', 'U'])),
    answerId: nullish(pick(p, ['answerId', 'answer_id', 'answer', 'A'])),
    confidence: toPct(pick(p, ['confidence', 'conf', 'Q'])),
    decision: nullish(pick(p, ['decision', 'X'])),
  };
}

/** GSM 03.38 basic character set, without ESC (0x1B). */
export const GSM7_BASIC = new Set(
  Array.from('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà'),
);

/** JANI1 grammar from CONTRACTS. M, P and X may be '-' (or empty) when unknown; CONTRACTS does not say. */
export const JANI1_RE =
  /^JANI1 M:(?<m>[A-Za-z0-9-]{0,16}) P:(?<p>[A-Za-z0-9-]{0,8}) D:(?<d>\d{8}) N:(?<n>\d{1,3}) R:(?<r>\d{1,3}) C:(?<c>\d{1,3}) H:(?<h>\d{1,3}) L:(?<l>\d{1,3}) U:(?<u>\d{1,3}) A:(?<a>[a-z0-9_]{1,40}) Q:(?<q>\d{1,3}) X:(?<x>act|wait|ask|-)?$/;
