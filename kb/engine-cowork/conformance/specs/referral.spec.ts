// buildReferral and parseReferral against the JANI1 format in kb/CONTRACTS.md, plus the officer
// The officer dashboard's own parser is checked in specs/ui-compat/lovable-parse.spec.ts.
import { describe, expect, it } from 'vitest';
import * as engine from '@engine';
import { day, GSM7_BASIC, JANI1_RE, leaf, leaves, makeCheck, mulberry32, normaliseParsed } from './helpers';

const e = engine as any;
const summarise = (ls: any[]) => e.summarisePlot(ls);
const build = (c: any) => e.buildReferral(c, c.memberId) as string; // second arg covers buildReferral(check, memberId)
const check = (over: any = {}) => {
  const c = makeCheck(over);
  c.summary = over.summary ?? summarise(c.leaves);
  return c;
};
const gsmBad = (s: string) => Array.from(s).filter((ch) => !GSM7_BASIC.has(ch));

describe('buildReferral: JANI1 grammar', () => {
  it('is exported', () => expect(typeof e.buildReferral).toBe('function'));

  it('the CONTRACTS example check gives exactly the CONTRACTS example fields', () => {
    const c = check({ plotId: '2', leaves: [...leaves({ rust: 6, miner: 1, unsure: 1, healthy: 2 })], answerId: 'rust_high_pre_rains', decision: 'ask' });
    const sms = build(c);
    const m = sms.match(JANI1_RE);
    expect(m, sms).not.toBeNull();
    expect(sms.replace(/ Q:\d{1,3}/, ' Q:87')).toBe('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask');
  });

  it('at most 160 characters, GSM-7 basic charset only, one line', () => {
    const sms = build(check());
    expect(sms.length).toBeLessThanOrEqual(160);
    expect(gsmBad(sms)).toEqual([]);
    expect(sms).not.toMatch(/[\r\n]/);
  });

  it('Q is a whole percent from 0 to 100', () => {
    const q = Number(build(check()).match(JANI1_RE)!.groups!.q);
    expect(Number.isInteger(q) && q >= 0 && q <= 100).toBe(true);
  });

  it('carries no names, even when the check object has name-like extra fields', () => {
    const sms = build(check({ farmerName: 'Noor Wanjiku', name: 'Noor Wanjiku', ownerName: 'Wanjiku' }));
    expect(sms).not.toMatch(/noor|wanjiku/i);
    expect(sms).toMatch(JANI1_RE);
  });

  it('a member id typed with spaces and lower case still gives a parseable SMS', () => {
    const sms = build(check({ memberId: ' occ 0412 ', plotId: ' p07 ' }));
    expect(sms, sms).toMatch(JANI1_RE);
  });

  it('a very long member id still fits in 160 characters', () => {
    const sms = build(check({ memberId: 'OCC'.padEnd(200, '9') }));
    expect(sms.length).toBeLessThanOrEqual(160);
    expect(sms).toMatch(JANI1_RE);
  });

  it('non-GSM characters in member or plot never reach the SMS', () => {
    const sms = build(check({ memberId: 'OCC0412\u2014\u00f8\u20ac', plotId: 'P\u00b707' }));
    expect(gsmBad(sms)).toEqual([]);
  });
});

describe('buildReferral: edge cases', () => {
  it('n = 0 (no photos) still gives a valid JANI1 string', () => {
    const sms = build(check({ leaves: [], answerId: 'ask_officer' }));
    expect(sms, sms).toMatch(JANI1_RE);
    expect(sms).toContain(' N:0 ');
  });

  it('all unsure gives U = N and zero disease counts', () => {
    const sms = build(check({ leaves: leaves({ unsure: 10 }), answerId: 'too_many_unsure' }));
    const g = sms.match(JANI1_RE)!.groups!;
    expect([g.n, g.r, g.c, g.h, g.l, g.u]).toEqual(['10', '0', '0', '0', '0', '10']);
  });

  it('U is summary.uncertain, so it includes not_leaf leaves and N = healthy + R + C + H + L + U', () => {
    const sms = build(check({ leaves: leaves({ not_leaf: 2, unsure: 1, rust: 3, healthy: 4 }) }));
    const g = sms.match(JANI1_RE)!.groups!;
    expect(g.u).toBe('3');
  });

  it('missing member or plot still gives a valid JANI1 string', () => {
    for (const over of [{ memberId: undefined }, { plotId: undefined }, { memberId: undefined, plotId: undefined }, { memberId: '', plotId: '' }]) {
      const sms = build(check(over));
      expect(sms, JSON.stringify(over) + ' -> ' + sms).toMatch(JANI1_RE);
    }
  });

  it('missing decision still gives a valid JANI1 string', () => {
    const sms = build(check({ decision: undefined }));
    expect(sms, sms).toMatch(JANI1_RE);
  });
});

describe('parseReferral: round trip', () => {
  it('is exported by the engine', () => expect(typeof e.parseReferral).toBe('function'));

  it('round-trips every field of the CONTRACTS example', () => {
    const p = normaliseParsed(e.parseReferral('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask'));
    expect(p).toEqual({ memberId: 'OCC0412', plotId: '2', date: '20261004', n: 10, rust: 6, cercospora: 0, phoma: 0, miner: 1, uncertain: 1, answerId: 'rust_high_pre_rains', confidence: 87, decision: 'ask' });
  });

  it('round-trips buildReferral output for 300 random checks', () => {
    const rnd = mulberry32(160);
    const pool = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf', 'unsure'] as const;
    const ids = ['healthy_all', 'rust_low', 'rust_high_pre_rains', 'mixed_problems', 'too_many_unsure', 'ask_officer', 'not_a_leaf'];
    const bad: string[] = [];
    for (let i = 0; i < 300; i++) {
      const ls = Array.from({ length: Math.floor(rnd() * 13) }, () => leaf(pool[Math.floor(rnd() * pool.length)] as any, 0.35 + rnd() * 0.65));
      const c = check({ leaves: ls, memberId: `OCC${String(Math.floor(rnd() * 9999)).padStart(4, '0')}`, plotId: `P${1 + Math.floor(rnd() * 30)}`,
        answerId: ids[Math.floor(rnd() * ids.length)], decision: (['act', 'wait', 'ask'] as const)[Math.floor(rnd() * 3)],
        createdAt: day(`2026-${String(1 + Math.floor(rnd() * 12)).padStart(2, '0')}-${String(1 + Math.floor(rnd() * 28)).padStart(2, '0')}`).toISOString() });
      const sms = build(c);
      const g = sms.match(JANI1_RE)?.groups;
      const p = normaliseParsed(e.parseReferral(sms));
      const s = c.summary;
      const want = g && { memberId: c.memberId, plotId: c.plotId, date: g.d, n: s.n, rust: s.counts.rust, cercospora: s.counts.cercospora, phoma: s.counts.phoma, miner: s.counts.miner, uncertain: s.uncertain, answerId: c.answerId, confidence: Number(g.q), decision: c.decision };
      if (!g || sms.length > 160 || JSON.stringify(p) !== JSON.stringify(want)) bad.push(`${sms} -> ${JSON.stringify(p)}`);
    }
    expect(bad.slice(0, 4), `${bad.length} of 300 failed`).toEqual([]);
  });

  it('D is the local calendar day of createdAt', () => {
    const sms = build(check({ createdAt: new Date(2026, 9, 4, 0, 30).toISOString() }));
    expect(sms.match(JANI1_RE)?.groups?.d).toBe('20261004');
  });

  it('rejects text that is not a JANI1 referral', () => {
    for (const t of ['hello', '', 'JANI2 M:OCC0412', 'JANI1', 'JANI1 M:OCC0412 P:2 D:2026 N:x']) expect(e.parseReferral(t), t).toBeNull();
  });
});
