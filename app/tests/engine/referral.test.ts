import { describe, expect, it } from 'vitest';
import { buildReferral, checkDate, meanConfidencePercent, parseReferral, smsLink } from '../../src/engine/referral';
import { leaves, makeCheck } from './helpers';
import { summarisePlot } from '../../src/engine/plot';

const GSM7_BASIC = /^[A-Za-z0-9 :_-]*$/;

describe('referral', () => {
  it('matches the CONTRACTS.md format', () => {
    const c = makeCheck({ decision: 'ask' });
    const text = buildReferral(c);
    expect(text).toMatch(
      /^JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:\d{1,3} X:ask$/,
    );
  });

  it('is at most 160 characters and plain GSM-7', () => {
    const text = buildReferral(makeCheck({ decision: 'ask' }));
    expect(text.length).toBeLessThanOrEqual(160);
    expect(GSM7_BASIC.test(text)).toBe(true);
  });

  it('stays under 160 with the longest possible fields', () => {
    const ls = leaves({ rust: 99 });
    const text = buildReferral(
      makeCheck({
        leaves: ls,
        summary: { ...summarisePlot(ls), uncertain: 99, counts: { healthy: 0, rust: 99, cercospora: 99, phoma: 99, miner: 99, not_leaf: 0 } },
        memberId: 'A'.repeat(40),
        plotId: 'B'.repeat(40),
        answerId: 'z'.repeat(200),
        decision: 'wait',
      }),
    );
    expect(text.length).toBeLessThanOrEqual(160);
    expect(GSM7_BASIC.test(text)).toBe(true);
  });

  it('round-trips through parseReferral', () => {
    const c = makeCheck({ decision: 'ask' });
    const p = parseReferral(buildReferral(c))!;
    expect(p).not.toBeNull();
    expect(p.memberId).toBe('OCC0412');
    expect(p.plotId).toBe('2');
    expect(p.date).toBe('2026-10-04');
    expect(p.n).toBe(10);
    expect(p.rust).toBe(6);
    expect(p.miner).toBe(1);
    expect(p.unsure).toBe(1);
    expect(p.other).toBe(2);
    expect(p.answerId).toBe('rust_high_pre_rains');
    expect(p.confidence).toBe(meanConfidencePercent(c));
    expect(p.decision).toBe('ask');
    expect(checkDate(c.createdAt)).toBe(p.date);
  });

  it('parses the example in CONTRACTS.md', () => {
    const p = parseReferral('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask')!;
    expect(p.confidence).toBe(87);
    expect(p.rust).toBe(6);
  });

  it('writes NA for a missing member and defaults the decision to ask', () => {
    const text = buildReferral(makeCheck({ memberId: undefined, plotId: undefined, decision: undefined }));
    expect(text).toContain('M:NA P:NA');
    expect(text.endsWith('X:ask')).toBe(true);
    expect(parseReferral(text)).not.toBeNull();
  });

  it('strips characters that are not safe in an SMS field', () => {
    const text = buildReferral(makeCheck({ memberId: 'occ 04/12 ü', decision: 'ask' }));
    expect(text).toContain('M:OCC0412');
    expect(GSM7_BASIC.test(text)).toBe(true);
  });

  it('is tolerant of case, order and whitespace on parse', () => {
    const p = parseReferral('  jani1  x:act q:50 a:healthy_all u:0 l:0 h:0 c:0 r:0 n:10 d:20261004 p:7 m:occ1 ');
    expect(p?.decision).toBe('act');
    expect(p?.memberId).toBe('OCC1');
  });

  it.each([
    ['empty', ''],
    ['wrong version', 'JANI2 M:A P:1 D:20261004 N:1 R:0 C:0 H:0 L:0 U:0 A:x Q:1 X:ask'],
    ['missing field', 'JANI1 M:A P:1 D:20261004 N:1 R:0 C:0 H:0 L:0 U:0 A:x Q:1'],
    ['bad date', 'JANI1 M:A P:1 D:20261340 N:1 R:0 C:0 H:0 L:0 U:0 A:x Q:1 X:ask'],
    ['counts exceed n', 'JANI1 M:A P:1 D:20261004 N:2 R:2 C:1 H:0 L:0 U:0 A:x Q:1 X:ask'],
    ['confidence over 100', 'JANI1 M:A P:1 D:20261004 N:2 R:0 C:0 H:0 L:0 U:0 A:x Q:101 X:ask'],
    ['bad decision', 'JANI1 M:A P:1 D:20261004 N:2 R:0 C:0 H:0 L:0 U:0 A:x Q:1 X:maybe'],
    ['duplicate field', 'JANI1 M:A M:B P:1 D:20261004 N:2 R:0 C:0 H:0 L:0 U:0 A:x Q:1 X:ask'],
    ['junk token', 'JANI1 hello M:A P:1 D:20261004 N:2 R:0 C:0 H:0 L:0 U:0 A:x Q:1 X:ask'],
    ['not a referral', 'Spray day is Tuesday'],
  ])('rejects %s', (_name, text) => {
    expect(parseReferral(text)).toBeNull();
  });

  it('never throws on odd input', () => {
    expect(() => parseReferral(undefined as unknown as string)).not.toThrow();
    expect(parseReferral(undefined as unknown as string)).toBeNull();
  });

  it('builds an sms link that encodes the body and keeps the number clean', () => {
    const body = 'JANI1 M:A P:1';
    expect(smsLink('+254 700-123 456', body)).toBe('sms:+254700123456?body=JANI1%20M%3AA%20P%3A1');
    expect(smsLink('0700123456', body).startsWith('sms:0700123456?body=')).toBe(true);
  });

  it('mean confidence ignores unsure leaves and is 0 when none were committed', () => {
    expect(meanConfidencePercent(makeCheck({ leaves: leaves({ unsure: 3 }) }))).toBe(0);
    expect(meanConfidencePercent(makeCheck({ leaves: leaves({ rust: 2 }) }))).toBe(90);
  });
});
