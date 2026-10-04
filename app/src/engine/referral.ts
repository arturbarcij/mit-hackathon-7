// Referral SMS: the single implementation of both writing and reading the referral.
// Format (kb/CONTRACTS.md), at most 160 GSM-7 characters, no names:
//   JANI1 M:<member> P:<plot> D:<yyyymmdd> N:<n> R:<rust> C:<cerco> H:<phoma> L:<miner> U:<unsure> A:<answerId> Q:<conf%> X:<decision>
// parseReferral also reads the older Lovable short form:
//   JANI <member> <plot> <YYYY-MM-DD> <label> <affected>/<n> unsure <u> <ACT|WAIT|ASK>
// Nothing here sends anything: smsLink only builds the link the farmer taps herself.
// SSR-safe: navigator is only read inside smsLink.
import { DISEASES, LABELS } from './types';
import type { Check, Decision, Label, LeafResult, ParsedReferral, ReferralCheck, ReferralOptions } from './types';

export const SMS_MAX = 160;
const ID_MAX = 12;

// GSM 03.38 basic character set (no escape, no extension table).
const GSM7_BASIC =
  '@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?' +
  '¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà';
const GSM7_SET = new Set(Array.from(GSM7_BASIC));

/** Replaces every character outside the GSM 03.38 basic set with '?'. */
export function toGsm7(text: string): string {
  return Array.from(String(text ?? ''))
    .map((ch) => (GSM7_SET.has(ch) ? ch : '?'))
    .join('');
}

export function isGsm7(text: string): boolean {
  return Array.from(text).every((ch) => GSM7_SET.has(ch));
}

/** Uppercase, keep A-Z 0-9 and '-', cut to max chars. Empty or missing gives '-'. */
export function cleanId(value: string | undefined | null, max = ID_MAX): string {
  const v = String(value ?? '')
    .toUpperCase()
    .replace(/[^A-Z0-9-]/g, '')
    .slice(0, max);
  return v || '-';
}

function cleanAnswerId(value: string | undefined | null): string {
  const v = String(value ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, '');
  return v || '-';
}

function localYmd(d: Date): string {
  if (!(d instanceof Date) || isNaN(d.getTime())) return '-';
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
}

/** Rounded mean calibrated confidence of accepted leaves (not unsure, not not_leaf, not abstained), whole percent; '0' when none. */
function confidencePct(leaves: LeafResult[] | undefined): string {
  const sure = (leaves ?? []).filter((l) => l.label !== 'unsure' && l.label !== 'not_leaf' && !l.abstained);
  if (sure.length === 0) return '0';
  const mean = sure.reduce((s, l) => s + (Number.isFinite(l.confidence) ? l.confidence : 0), 0) / sure.length;
  return String(Math.round(Math.min(1, Math.max(0, mean)) * 100));
}

function isFullCheck(c: Check | ReferralCheck): c is Check {
  return typeof (c as Check).answerId === 'string';
}

/** Builds the JANI1 referral body. Always GSM-7 and at most 160 characters. */
export function buildReferral(check: Check | ReferralCheck, opts?: ReferralOptions): string {
  const full = isFullCheck(check);
  const answerId = full ? check.answerId : check.answer?.id;
  const date = full ? new Date(check.createdAt) : check.date;
  const s = check.summary;
  const c = (l: Label) => Math.max(0, Math.trunc(s?.counts?.[l] ?? 0));
  const fields = (idMax: number, answer: string) =>
    [
      'JANI1',
      `M:${cleanId(check.memberId ?? opts?.memberId, idMax)}`,
      `P:${cleanId(check.plotId ?? opts?.plotId, idMax)}`,
      `D:${localYmd(date)}`,
      `N:${Math.max(0, Math.trunc(s?.n ?? 0))}`,
      `R:${c('rust')}`,
      `C:${c('cercospora')}`,
      `H:${c('phoma')}`,
      `L:${c('miner')}`,
      `U:${Math.max(0, Math.trunc(s?.uncertain ?? 0))}`,
      `A:${answer}`,
      `Q:${confidencePct(check.leaves)}`,
      `X:${check.decision ?? '-'}`,
    ].join(' ');

  const answer = cleanAnswerId(answerId);
  let out = toGsm7(fields(ID_MAX, answer));
  // Shorten member and plot first, then the answer id, until it fits.
  for (let max = ID_MAX - 1; out.length > SMS_MAX && max >= 4; max--) out = toGsm7(fields(max, answer));
  if (out.length > SMS_MAX) out = toGsm7(fields(4, answer.slice(0, Math.max(1, answer.length - (out.length - SMS_MAX)))));
  if (out.length > SMS_MAX || !isGsm7(out)) throw new Error('Jani referral does not fit one GSM-7 SMS');
  return out;
}

/** sms: link for the composer. The farmer presses send herself. */
export function smsLink(number: string, body: string): string {
  const n = String(number ?? '').replace(/[^+\d]/g, '');
  const ua = typeof navigator !== 'undefined' && navigator ? navigator.userAgent || '' : '';
  const sep = /iPad|iPhone|iPod/.test(ua) ? '&' : '?';
  return `sms:${n}${sep}body=${encodeURIComponent(body ?? '')}`;
}

function emptyCounts(): Record<Label, number> {
  return Object.fromEntries(LABELS.map((l) => [l, 0])) as Record<Label, number>;
}

function validIsoDate(y: number, m: number, d: number): string | null {
  if (!(y >= 2000 && y <= 2100 && m >= 1 && m <= 12 && d >= 1 && d <= 31)) return null;
  const t = new Date(Date.UTC(y, m - 1, d));
  if (t.getUTCFullYear() !== y || t.getUTCMonth() !== m - 1 || t.getUTCDate() !== d) return null;
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}

const INT = /^\d{1,4}$/;
const DECISIONS: readonly Decision[] = ['act', 'wait', 'ask'];

function toDecision(v: string | undefined): Decision | null {
  const d = (v ?? '').toLowerCase() as Decision;
  return DECISIONS.includes(d) ? d : null;
}

function cleanParsedId(v: string | undefined): string {
  if (!v || v === '-') return '';
  const id = cleanId(v, 32);
  return id === '-' ? '' : id;
}

function parseJani1(tokens: string[]): ParsedReferral | null {
  const f: Record<string, string> = {};
  for (const t of tokens.slice(1)) {
    const i = t.indexOf(':');
    if (i < 1) continue; // stray words are ignored
    const v = t.slice(i + 1);
    if (v !== '-' && v !== '') f[t.slice(0, i).toUpperCase()] = v;
  }
  const dm = /^(\d{4})(\d{2})(\d{2})$/.exec(f.D ?? '');
  const date = dm ? validIsoDate(+dm[1], +dm[2], +dm[3]) : null;
  if (!date) return null;
  const nums: Record<string, number> = {};
  for (const k of ['N', 'R', 'C', 'H', 'L', 'U']) {
    if (f[k] === undefined) {
      if (k === 'N') return null;
      nums[k] = 0;
      continue;
    }
    if (!INT.test(f[k])) return null;
    nums[k] = parseInt(f[k], 10);
  }
  const n = nums.N;
  const sum = nums.R + nums.C + nums.H + nums.L + nums.U;
  // N:0 is a valid referral with no photos (the engine writes it).
  if (n > 50 || sum > n) return null;
  // Q:- (legacy, before Q:0) was dropped above as missing, so it parses as confidence null.
  let confidence: number | null = null;
  if (f.Q !== undefined) {
    if (!INT.test(f.Q) || parseInt(f.Q, 10) > 100) return null;
    confidence = parseInt(f.Q, 10) / 100;
  }
  const counts = emptyCounts();
  counts.rust = nums.R;
  counts.cercospora = nums.C;
  counts.phoma = nums.H;
  counts.miner = nums.L;
  counts.healthy = n - sum;
  const answer = f.A ? cleanAnswerId(f.A) : '-';
  return {
    member_id: cleanParsedId(f.M),
    plot_id: cleanParsedId(f.P),
    check_date: date,
    counts,
    uncertain: nums.U,
    answer_id: answer === '-' ? null : answer,
    confidence,
    decision: toDecision(f.X),
    format: 'JANI1',
  };
}

// Lovable short form: JANI <member> <plot> <YYYY-MM-DD> <label> <affected>/<n> unsure <u> <ACT|WAIT|ASK>
function parseShort(tokens: string[]): ParsedReferral | null {
  const di = tokens.findIndex((t, i) => i > 0 && /^\d{4}-\d{2}-\d{2}$/.test(t));
  if (di < 1 || di > 3) return null;
  const ids = tokens.slice(1, di);
  const rest = tokens.slice(di + 1);
  if (rest.length !== 5 || rest[2].toLowerCase() !== 'unsure') return null;
  const [y, m, d] = tokens[di].split('-').map(Number);
  const date = validIsoDate(y, m, d);
  if (!date) return null;
  const label = rest[0].toLowerCase();
  const isDisease = (DISEASES as readonly string[]).includes(label);
  if (!isDisease && !['affected', 'healthy', 'none'].includes(label)) return null;
  const frac = /^(\d{1,4})\/(\d{1,4})$/.exec(rest[1]);
  if (!frac || !INT.test(rest[3])) return null;
  const affected = parseInt(frac[1], 10);
  const n = parseInt(frac[2], 10);
  const u = parseInt(rest[3], 10);
  if (n < 1 || n > 50 || affected + u > n) return null;
  const decision = toDecision(rest[4]);
  if (!decision) return null;
  const counts = emptyCounts();
  if (isDisease) counts[label as Label] = affected;
  counts.healthy = Math.max(0, n - affected - u);
  return {
    member_id: cleanParsedId(ids[0]),
    plot_id: cleanParsedId(ids[1]),
    check_date: date,
    counts,
    uncertain: u,
    answer_id: null,
    confidence: null,
    decision,
    format: 'JANI',
  };
}

/** Reads a referral SMS (JANI1 or the Lovable short form). Returns null for anything else. Never throws. */
export function parseReferral(text: string): ParsedReferral | null {
  try {
    if (typeof text !== 'string' || text.length > 1000) return null;
    const tokens = text.trim().split(/\s+/);
    const head = (tokens[0] ?? '').toUpperCase();
    if (head === 'JANI1') return parseJani1(tokens);
    if (head === 'JANI') return parseShort(tokens);
    return null;
  } catch {
    return null;
  }
}
