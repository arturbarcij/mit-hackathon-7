import type { Check, Decision, ParsedReferral } from './types';

export const REFERRAL_VERSION = 'JANI1';
export const SMS_MAX = 160;

const MEMBER_MAX = 14;
const PLOT_MAX = 8;
const ANSWER_MAX = 40;

/*
 * Field caps keep the longest possible message at 130 characters, well under 160:
 * "JANI1 M:" + 14 + " P:" + 8 + " D:20261004 N:99 R:99 C:99 H:99 L:99 U:99 A:" + 40 + " Q:100 X:wait".
 * All characters are in the GSM-7 basic set (letters, digits, space, colon, underscore, hyphen).
 */

function clean(value: string | undefined, max: number, fallback: string): string {
  const s = (value ?? '').toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, max);
  return s === '' ? fallback : s;
}

function cleanAnswer(id: string): string {
  const s = id.toLowerCase().replace(/[^a-z0-9_]/g, '').slice(0, ANSWER_MAX);
  return s === '' ? 'ask_officer' : s;
}

function two(n: number): string {
  return String(n).padStart(2, '0');
}

function yyyymmdd(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '00000000';
  return `${d.getFullYear()}${two(d.getMonth() + 1)}${two(d.getDate())}`;
}

/** Local calendar date of the check as yyyy-mm-dd, matching the D field of the SMS. */
export function checkDate(iso: string): string {
  const s = yyyymmdd(iso);
  return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
}

function count(n: number): number {
  return Math.max(0, Math.min(99, Math.round(n)));
}

/** Mean calibrated confidence over leaves the model committed to, as a whole percentage. */
export function meanConfidencePercent(check: Check): number {
  const committed = check.leaves.filter((l) => !l.abstained && l.label !== 'unsure');
  if (committed.length === 0) return 0;
  const mean = committed.reduce((s, l) => s + l.confidence, 0) / committed.length;
  return Math.max(0, Math.min(100, Math.round(mean * 100)));
}

/**
 * Builds the SMS body. A referral exists to ask a person, so a check with no decision yet is written as `ask`.
 * Missing member or plot numbers are written as NA; the officer then asks the cooperative.
 */
export function buildReferral(check: Check): string {
  const s = check.summary;
  const decision: Decision = check.decision ?? 'ask';
  const parts = [
    REFERRAL_VERSION,
    `M:${clean(check.memberId, MEMBER_MAX, 'NA')}`,
    `P:${clean(check.plotId, PLOT_MAX, 'NA')}`,
    `D:${yyyymmdd(check.createdAt)}`,
    `N:${count(s.n)}`,
    `R:${count(s.counts.rust)}`,
    `C:${count(s.counts.cercospora)}`,
    `H:${count(s.counts.phoma)}`,
    `L:${count(s.counts.miner)}`,
    `U:${count(s.uncertain)}`,
    `A:${cleanAnswer(check.answerId)}`,
    `Q:${meanConfidencePercent(check)}`,
    `X:${decision}`,
  ];
  return parts.join(' ');
}

/** Opens the phone's SMS composer with the body filled in. The farmer presses send. */
export function smsLink(number: string, body: string): string {
  const cleaned = number.trim().replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '');
  return `sms:${cleaned}?body=${encodeURIComponent(body)}`;
}

function intField(v: string | undefined, max = 99): number | null {
  if (v === undefined || !/^\d{1,3}$/.test(v)) return null;
  const n = Number(v);
  return n <= max ? n : null;
}

/** Returns null for anything that is not a well-formed JANI1 message. Never throws. */
export function parseReferral(text: string): ParsedReferral | null {
  if (typeof text !== 'string') return null;
  const tokens = text.trim().split(/\s+/);
  if (tokens[0]?.toUpperCase() !== REFERRAL_VERSION) return null;

  const f: Record<string, string> = {};
  for (const t of tokens.slice(1)) {
    const m = /^([A-Za-z]):(.+)$/.exec(t);
    if (!m) return null;
    const key = m[1].toUpperCase();
    if (key in f) return null;
    f[key] = m[2];
  }

  const member = f.M?.toUpperCase();
  const plot = f.P?.toUpperCase();
  const answer = f.A?.toLowerCase();
  const dateMatch = /^(\d{4})(\d{2})(\d{2})$/.exec(f.D ?? '');
  const n = intField(f.N);
  const rust = intField(f.R);
  const cerco = intField(f.C);
  const phoma = intField(f.H);
  const miner = intField(f.L);
  const unsure = intField(f.U);
  const conf = intField(f.Q, 100);
  const decision = f.X?.toLowerCase();

  if (!member || !/^[A-Z0-9-]+$/.test(member)) return null;
  if (!plot || !/^[A-Z0-9-]+$/.test(plot)) return null;
  if (!answer || !/^[a-z0-9_]+$/.test(answer)) return null;
  if (!dateMatch) return null;
  if ([n, rust, cerco, phoma, miner, unsure, conf].some((v) => v === null)) return null;
  if (decision !== 'act' && decision !== 'wait' && decision !== 'ask') return null;

  const year = Number(dateMatch[1]);
  const month = Number(dateMatch[2]);
  const day = Number(dateMatch[3]);
  const probe = new Date(Date.UTC(year, month - 1, day));
  if (probe.getUTCFullYear() !== year || probe.getUTCMonth() !== month - 1 || probe.getUTCDate() !== day) return null;

  const total = (n as number);
  const problems = (rust as number) + (cerco as number) + (phoma as number) + (miner as number);
  if (problems + (unsure as number) > total) return null;

  return {
    version: 1,
    memberId: member,
    plotId: plot,
    date: `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`,
    n: total,
    rust: rust as number,
    cercospora: cerco as number,
    phoma: phoma as number,
    miner: miner as number,
    unsure: unsure as number,
    uncertain: unsure as number,
    other: total - problems - (unsure as number),
    answerId: answer,
    confidence: conf as number,
    decision,
  } as ParsedReferral & { uncertain: number };
}
