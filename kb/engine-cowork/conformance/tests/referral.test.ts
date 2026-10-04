// Referral SMS conformance: JANI1 format, 160 GSM-7 limit, round trip, parser strictness, sms: link.
import { describe, expect, it } from 'vitest';
import { need } from './engine-under-test';
import { answers, checkFrom, DISEASES, LABELS, leavesFrom, rng, WINDOWS } from './fixtures';
import { gsm7Length, isGsm7 } from '../reference/gsm7';
import { summarisePlot as refSummarise } from '../reference/plot';
import type { Check, Decision, Label } from '../reference/types';

const JANI1 = /^JANI1 M:(\S+) P:(\S+) D:(\d{8}) N:(\d+) R:(\d+) C:(\d+) H:(\d+) L:(\d+) U:(\d+) A:([a-z0-9_]+) Q:(\d+) X:(act|wait|ask)$/;
const CONTRACTS_EXAMPLE = 'JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask';

const resultIds = answers.filter((a) => a.kind === 'result').map((a) => a.id);
const decisions: Decision[] = ['act', 'wait', 'ask'];

function randomCheck(next: () => number, i: number): Check {
  const n = 1 + Math.floor(next() * 10);
  const counts: Partial<Record<Label | 'unsure', number>> = {};
  const pool: (Label | 'unsure')[] = [...LABELS, 'unsure'];
  for (let k = 0; k < n; k++) { const l = pool[Math.floor(next() * pool.length)]; counts[l] = (counts[l] ?? 0) + 1; }
  const leaves = leavesFrom(counts).map((l) => ({ ...l, confidence: l.label === 'unsure' ? 0.3 + next() * 0.2 : 0.55 + next() * 0.45 }));
  const summary = refSummarise(leaves);
  const memberStyles = ['OCC0412', 'KM12', 'ABCD123456', `M${1000 + i}`, 'NY0007'];
  const plotStyles = ['2', 'P07', '1', 'P123', '12'];
  const y = 2026, m = 1 + Math.floor(next() * 12), d = 1 + Math.floor(next() * 28);
  return checkFrom({
    id: `chk_${i}`,
    createdAt: new Date(Date.UTC(y, m - 1, d, 6 + Math.floor(next() * 12))).toISOString(),
    leaves,
    summary,
    window: WINDOWS[Math.floor(next() * WINDOWS.length)],
    answerId: resultIds[Math.floor(next() * resultIds.length)],
    decision: decisions[Math.floor(next() * 3)],
    memberId: memberStyles[Math.floor(next() * memberStyles.length)],
    plotId: plotStyles[Math.floor(next() * plotStyles.length)],
  });
}

describe('buildReferral', () => {
  const buildReferral = need('buildReferral');

  const base = checkFrom({
    leaves: leavesFrom({ rust: 6, miner: 1, healthy: 2, unsure: 1 }).map((l) => ({ ...l, confidence: l.label === 'unsure' ? 0.4 : 0.87 })),
    summary: refSummarise(leavesFrom({ rust: 6, miner: 1, healthy: 2, unsure: 1 })),
    createdAt: '2026-10-04T09:30:00.000Z',
    answerId: 'rust_high_pre_rains',
    decision: 'ask',
    memberId: 'OCC0412',
    plotId: '2',
  });

  it('reproduces the CONTRACTS example line', () => {
    expect(buildReferral(base)).toBe(CONTRACTS_EXAMPLE);
  });

  it('matches the JANI1 grammar and is at most 160 GSM-7 characters', () => {
    const line = buildReferral(base);
    expect(line).toMatch(JANI1);
    expect(isGsm7(line)).toBe(true);
    expect(gsm7Length(line)).toBeLessThanOrEqual(160);
  });

  it('carries member id, plot id, date and counts from the check (no names, no free text)', () => {
    const m = buildReferral(base).match(JANI1)!;
    expect(m[1]).toBe('OCC0412');
    expect(m[2]).toBe('2');
    expect(m[3]).toBe('20261004');
    expect(Number(m[4])).toBe(10);
    expect([m[5], m[6], m[7], m[8], m[9]].map(Number)).toEqual([6, 0, 0, 1, 1]);
    expect(m[10]).toBe('rust_high_pre_rains');
    expect(m[12]).toBe('ask');
  });

  it('accepts a P07 style plot id too', () => {
    const line = buildReferral({ ...base, plotId: 'P07' });
    expect(line).toContain(' P:P07 ');
  });

  it('stays within 160 GSM-7 characters for 200 random checks', () => {
    const next = rng(42);
    for (let i = 0; i < 200; i++) {
      const line = buildReferral(randomCheck(next, i));
      expect(isGsm7(line), line).toBe(true);
      expect(gsm7Length(line), line).toBeLessThanOrEqual(160);
      expect(line).toMatch(JANI1);
    }
  });

  it('stays within 160 GSM-7 characters with hostile inputs (long ids, non GSM characters)', () => {
    const hostile = { ...base, memberId: 'Ω'.repeat(50) + 'A'.repeat(300), plotId: 'P' + '9'.repeat(200), answerId: 'x'.repeat(500) };
    const line = buildReferral(hostile);
    expect(isGsm7(line)).toBe(true);
    expect(gsm7Length(line)).toBeLessThanOrEqual(160);
  });

  it('confidence Q is a whole number between 0 and 100', () => {
    const next = rng(7);
    for (let i = 0; i < 50; i++) {
      const q = Number(buildReferral(randomCheck(next, i)).match(JANI1)![11]);
      expect(Number.isInteger(q)).toBe(true);
      expect(q).toBeGreaterThanOrEqual(0);
      expect(q).toBeLessThanOrEqual(100);
    }
  });
});

describe('parseReferral', () => {
  const parseReferral = need('parseReferral');
  const buildReferral = need('buildReferral');

  it('parses the CONTRACTS example (plot id "2")', () => {
    const p = parseReferral(CONTRACTS_EXAMPLE);
    expect(p).not.toBeNull();
    expect(p!.memberId).toBe('OCC0412');
    expect(p!.plotId).toBe('2');
    expect(p!.date).toBe('20261004');
    expect(p!.n).toBe(10);
    expect(p!.counts).toEqual({ rust: 6, cercospora: 0, phoma: 0, miner: 1 });
    expect(p!.uncertain).toBe(1);
    expect(p!.answerId).toBe('rust_high_pre_rains');
    expect(p!.confidence).toBe(87);
    expect(p!.decision).toBe('ask');
  });

  it('parses a P07 style plot id (Lovable parser convention)', () => {
    const p = parseReferral(CONTRACTS_EXAMPLE.replace('P:2', 'P:P07'));
    expect(p?.plotId).toBe('P07');
  });

  it('round-trips build -> parse for 200 random checks', () => {
    const next = rng(2026);
    for (let i = 0; i < 200; i++) {
      const c = randomCheck(next, i);
      const line = buildReferral(c);
      const p = parseReferral(line);
      expect(p, line).not.toBeNull();
      expect(p!.memberId).toBe(c.memberId);
      expect(p!.plotId).toBe(c.plotId);
      expect(p!.date).toBe(c.createdAt.slice(0, 10).replace(/-/g, ''));
      expect(p!.n).toBe(c.summary.n);
      expect(p!.counts.rust).toBe(c.summary.counts.rust);
      expect(p!.counts.cercospora).toBe(c.summary.counts.cercospora);
      expect(p!.counts.phoma).toBe(c.summary.counts.phoma);
      expect(p!.counts.miner).toBe(c.summary.counts.miner);
      expect(p!.uncertain).toBe(c.summary.uncertain);
      expect(p!.answerId).toBe(c.answerId);
      expect(p!.decision).toBe(c.decision);
      expect(p!.confidence).toBeGreaterThanOrEqual(0);
      expect(p!.confidence).toBeLessThanOrEqual(100);
    }
  });

  it('tolerates surrounding whitespace and repeated spaces', () => {
    expect(parseReferral(`  ${CONTRACTS_EXAMPLE.replace(/ /g, '  ')}\n`)).not.toBeNull();
  });

  it.each([
    ['empty string', ''],
    ['plain text', 'hello officer please come'],
    ['wrong version', CONTRACTS_EXAMPLE.replace('JANI1', 'JANI2')],
    ['lowercase version', CONTRACTS_EXAMPLE.replace('JANI1', 'jani1')],
    ['missing version', CONTRACTS_EXAMPLE.replace('JANI1 ', '')],
    ['missing field', CONTRACTS_EXAMPLE.replace(' U:1', '')],
    ['bad decision', CONTRACTS_EXAMPLE.replace('X:ask', 'X:maybe')],
    ['confidence over 100', CONTRACTS_EXAMPLE.replace('Q:87', 'Q:187')],
    ['non numeric count', CONTRACTS_EXAMPLE.replace('R:6', 'R:six')],
    ['bad date length', CONTRACTS_EXAMPLE.replace('D:20261004', 'D:2026104')],
    ['bad month', CONTRACTS_EXAMPLE.replace('D:20261004', 'D:20261304')],
    ['Lovable free text referral', 'Jani check: 10 leaves, 6 affected, 1 not sure. Main result: rust. Farmer chose: ask. Please advise.'],
    ['json', '{"version":"JANI1"}'],
  ])('rejects %s', (_name, text) => {
    expect(parseReferral(text)).toBeNull();
  });

  it('does not throw on odd input', () => {
    for (const bad of ['JANI1', 'JANI1 M:', 'JANI1 ::::', 'JANI1 M:a P:b D:c N:d R:e C:f H:g L:h U:i A:j Q:k X:l']) {
      expect(() => parseReferral(bad)).not.toThrow();
      expect(parseReferral(bad)).toBeNull();
    }
  });
});

describe('smsLink', () => {
  const smsLink = need('smsLink');

  it('builds sms:<number> with the body URL-encoded, using ? (Android) or & (iOS)', () => {
    const link = smsLink('+254700000000', CONTRACTS_EXAMPLE);
    expect(link).toMatch(/^sms:\+254700000000[?&]body=/);
    const body = decodeURIComponent(link.split('body=')[1]);
    expect(body).toBe(CONTRACTS_EXAMPLE);
  });

  it('encodes spaces and colons so the SMS app receives the exact text', () => {
    const link = smsLink('0700000000', 'a b:c&d');
    expect(link).not.toContain(' ');
    expect(decodeURIComponent(link.split('body=')[1])).toBe('a b:c&d');
  });

  it('does nothing automatic: the result is a string, not a navigation', () => {
    expect(typeof smsLink('0700', 'x')).toBe('string');
  });
});
