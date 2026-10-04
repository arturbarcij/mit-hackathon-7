// Referral SMS: buildReferral(check), parseReferral(text), smsLink(number, body).
// Format (kb/CONTRACTS.md "Referral SMS format"):
//   JANI1 M:<member> P:<plot> D:<yyyymmdd> N:<n> R:<rust> C:<cerco> H:<phoma> L:<miner>
//         U:<unsure> A:<answerId> Q:<conf%> X:<decision>
// Example: JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask
import { gsm7Length, SMS_GSM7_MAX, stripNonGsm7 } from './gsm7';
import type { Check, Decision, ParsedReferral } from './types';

export const REFERRAL_VERSION = 'JANI1';

// Field limits. They keep the line under 160 septets even with long inputs:
// fixed text 51 + member 16 + plot 8 + answer 40 + numbers (2+2+2+2+2+2+3) = 130 worst case.
const MEMBER_MAX = 16;
const PLOT_MAX = 8;
const ANSWER_MAX = 40;
const MISSING = '-';

// Token character classes. Member and plot: letters, digits, underscore, hyphen.
// CONTRACTS shows P:2 (a bare number). Lovable's parser requires P07 style. The
// reference accepts both, see RESULTS.md.
const MEMBER_RE = /^[A-Za-z0-9_-]{1,16}$/;
const PLOT_RE = /^[A-Za-z0-9_-]{1,8}$/;
const ANSWER_RE = /^[a-z0-9_]{1,40}$/;
const DATE_RE = /^\d{8}$/;
const INT_RE = /^\d{1,3}$/;
const DECISIONS: readonly Decision[] = ['act', 'wait', 'ask'];

/** Keep only safe token characters and cap the length. Empty becomes '-'. */
function token(value: string | undefined, max: number): string {
  const cleaned = stripNonGsm7(value ?? '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, max);
  return cleaned.length > 0 ? cleaned : MISSING;
}

/** yyyymmdd from an ISO timestamp, read in UTC so the output does not depend on the machine's zone. */
export function yyyymmdd(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '00000000';
  const y = d.getUTCFullYear().toString().padStart(4, '0');
  const m = (d.getUTCMonth() + 1).toString().padStart(2, '0');
  const day = d.getUTCDate().toString().padStart(2, '0');
  return `${y}${m}${day}`;
}

/**
 * Q: whole-number percent, 0 to 100. CONTRACTS does not say which confidence.
 * Reference: mean confidence of the accepted (non-unsure) leaves; 0 when none.
 */
export function confidencePercent(check: Check): number {
  const accepted = check.leaves.filter((l) => l.label !== 'unsure');
  if (accepted.length === 0) return 0;
  const mean = accepted.reduce((s, l) => s + l.confidence, 0) / accepted.length;
  return Math.max(0, Math.min(100, Math.round(mean * 100)));
}

export function buildReferral(c: Check): string {
  const s = c.summary;
  const clamp = (v: number) => Math.max(0, Math.min(999, Math.round(v || 0)));
  // X: is required by the format. A check saved before the farmer chose defaults to 'ask'.
  const decision: Decision = c.decision ?? 'ask';
  const parts = [
    REFERRAL_VERSION,
    `M:${token(c.memberId, MEMBER_MAX)}`,
    `P:${token(c.plotId, PLOT_MAX)}`,
    `D:${yyyymmdd(c.createdAt)}`,
    `N:${clamp(s.n)}`,
    `R:${clamp(s.counts.rust)}`,
    `C:${clamp(s.counts.cercospora)}`,
    `H:${clamp(s.counts.phoma)}`,
    `L:${clamp(s.counts.miner)}`,
    `U:${clamp(s.uncertain)}`,
    `A:${token(c.answerId, ANSWER_MAX).toLowerCase()}`,
    `Q:${confidencePercent(c)}`,
    `X:${decision}`,
  ];
  const line = parts.join(' ');
  if (gsm7Length(line) > SMS_GSM7_MAX) {
    // Cannot happen with the caps above; guard anyway rather than send a split SMS.
    throw new Error(`referral exceeds ${SMS_GSM7_MAX} GSM-7 characters`);
  }
  return line;
}

export function parseReferral(text: string): ParsedReferral | null {
  if (typeof text !== 'string') return null;
  const tokens = text.trim().split(/\s+/);
  if (tokens.length === 0 || tokens[0] !== REFERRAL_VERSION) return null;
  const fields = new Map<string, string>();
  for (const t of tokens.slice(1)) {
    const i = t.indexOf(':');
    if (i !== 1) return null; // every field is a single-letter key
    const key = t[0];
    if (fields.has(key)) return null; // duplicate field
    fields.set(key, t.slice(2));
  }
  const need = ['M', 'P', 'D', 'N', 'R', 'C', 'H', 'L', 'U', 'A', 'Q', 'X'];
  for (const k of need) if (!fields.has(k)) return null;

  const member = fields.get('M')!;
  const plot = fields.get('P')!;
  const date = fields.get('D')!;
  const answer = fields.get('A')!;
  const decision = fields.get('X')!;
  if (!MEMBER_RE.test(member) || !PLOT_RE.test(plot) || !DATE_RE.test(date) || !ANSWER_RE.test(answer)) return null;
  if (!DECISIONS.includes(decision as Decision)) return null;

  const ints: Record<string, number> = {};
  for (const k of ['N', 'R', 'C', 'H', 'L', 'U', 'Q']) {
    const v = fields.get(k)!;
    if (!INT_RE.test(v)) return null;
    ints[k] = Number.parseInt(v, 10);
  }
  if (ints.Q > 100) return null;
  const month = Number.parseInt(date.slice(4, 6), 10);
  const day = Number.parseInt(date.slice(6, 8), 10);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;

  return {
    version: 'JANI1',
    memberId: member,
    plotId: plot,
    date,
    n: ints.N,
    counts: { rust: ints.R, cercospora: ints.C, phoma: ints.H, miner: ints.L },
    uncertain: ints.U,
    answerId: answer,
    confidence: ints.Q,
    decision: decision as Decision,
  };
}

/**
 * sms: link that opens the phone's SMS app pre-filled. Android and the RFC 5724
 * form use '?body='. iOS needs '&body=' (Safari ignores '?'). Same approach as
 * Lovable's mock: sniff the user agent when a navigator exists; default to '?'.
 */
export function smsLinkFor(number: string, body: string, ios: boolean): string {
  const sep = ios ? '&' : '?';
  return `sms:${number.replace(/\s+/g, '')}${sep}body=${encodeURIComponent(body)}`;
}

export function smsLink(number: string, body: string): string {
  const ua = typeof navigator === 'undefined' ? '' : navigator.userAgent ?? '';
  return smsLinkFor(number, body, /iPhone|iPad|iPod/i.test(ua));
}
