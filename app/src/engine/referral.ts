import type { Check, LeafResult, ParsedReferral } from './types.ts';

const REFERRAL =
  /^JANI1 M:(\S+) P:(\S+) D:(\d{8}) N:(\d+) R:(\d+) C:(\d+) H:(\d+) L:(\d+) U:(\d+) A:(\S+) Q:(\d+) X:(\S+)$/;

function yyyymmdd(createdAt: string): string {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return '00000000';
  const year = date.getUTCFullYear().toString().padStart(4, '0');
  const month = (date.getUTCMonth() + 1).toString().padStart(2, '0');
  const day = date.getUTCDate().toString().padStart(2, '0');
  return `${year}${month}${day}`;
}

function confidencePercent(leaves: LeafResult[]): number {
  const used = leaves.filter((leaf) => !leaf.abstained);
  if (used.length === 0) return 0;
  const mean = used.reduce((sum, leaf) => sum + leaf.confidence, 0) / used.length;
  return Math.round(mean * 100);
}

export function buildReferral(check: Check): string {
  const member = check.memberId || 'NA';
  const plot = check.plotId || 'NA';
  const decision = check.decision ?? 'none';
  const summary = check.summary;
  const text = `JANI1 M:${member} P:${plot} D:${yyyymmdd(check.createdAt)} N:${summary.n} R:${summary.counts.rust} C:${summary.counts.cercospora} H:${summary.counts.phoma} L:${summary.counts.miner} U:${summary.uncertain} A:${check.answerId} Q:${confidencePercent(check.leaves)} X:${decision}`;
  if (text.length > 160) {
    throw new Error(`Referral is ${text.length} characters, which is over the 160 character GSM-7 limit.`);
  }
  return text;
}

export function smsLink(number: string, body: string): string {
  const compact = number.replace(/[^\d+]/g, '');
  const lead = compact.startsWith('+') ? '+' : '';
  const digits = compact.replace(/\D/g, '');
  return `sms:${lead}${digits}?body=${encodeURIComponent(body)}`;
}

export function parseReferral(text: string): ParsedReferral | null {
  const trimmed = text.trim();
  if (!trimmed.startsWith('JANI1')) return null;
  const match = REFERRAL.exec(trimmed);
  if (!match) return null;
  return {
    memberId: match[1],
    plotId: match[2],
    date: match[3],
    n: Number(match[4]),
    rust: Number(match[5]),
    cercospora: Number(match[6]),
    phoma: Number(match[7]),
    miner: Number(match[8]),
    unsure: Number(match[9]),
    answerId: match[10],
    confidence: Number(match[11]),
    decision: match[12],
  };
}
