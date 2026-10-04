import { afterEach, describe, expect, it, vi } from 'vitest';
import { buildReferral, isGsm7, parseReferral, smsLink, toGsm7 } from '../../src/engine/referral';
import type { AnswerCard, Check, Label, LeafResult, PlotSummary, ReferralCheck } from '../../src/engine/types';

const counts = (c: Partial<Record<Label, number>>): Record<Label, number> => ({
  healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0, ...c,
});

const summary: PlotSummary = {
  n: 10,
  counts: counts({ healthy: 2, rust: 6, miner: 1 }),
  uncertain: 1,
  dominant: 'rust',
  affected: 7,
  distinctProblems: 2,
};

const leaf = (label: LeafResult['label'], confidence: number): LeafResult => ({
  label,
  probs: counts({}),
  confidence,
  quality: { ok: true, blur: 100, brightness: 120 },
  abstained: label === 'unsure',
  modelVersion: 'mock',
});

const leaves: LeafResult[] = [
  ...Array.from({ length: 6 }, () => leaf('rust', 0.9)),
  leaf('miner', 0.8),
  leaf('healthy', 0.8),
  leaf('healthy', 0.9),
  leaf('unsure', 0.3),
];

const check: Check = {
  id: 'x',
  createdAt: new Date(2026, 9, 4, 9, 30).toISOString(),
  lang: 'sw',
  leaves,
  summary,
  window: 'pre_short_rains',
  answerId: 'rust_high_pre_rains',
  decision: 'ask',
  memberId: 'occ0412',
  plotId: 'p07',
  consentMain: true,
  consentPhotos: false,
  synced: false,
};

const card: AnswerCard = { id: 'rust_high_pre_rains', severity: 'act', text: {}, audio: {}, sources: [], assumption: false };

describe('buildReferral', () => {
  it('builds JANI1 from a Check', () => {
    const s = buildReferral(check);
    // mean of 6x0.9, 0.8, 0.8, 0.9 = 0.8778 -> 88
    expect(s).toBe('JANI1 M:OCC0412 P:P07 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:88 X:ask');
    expect(s.length).toBeLessThanOrEqual(160);
    expect(isGsm7(s)).toBe(true);
  });

  it('builds JANI1 from a Lovable ReferralCheck, member/plot from opts, Q:0 without leaves', () => {
    const rc: ReferralCheck = { summary, answer: card, decision: 'wait', date: new Date(2026, 9, 4) };
    expect(buildReferral(rc, { memberId: 'OCC 0412', plotId: 'Plot#2' })).toBe(
      'JANI1 M:OCC0412 P:PLOT2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:0 X:wait',
    );
  });

  it('marks missing member and plot with "-" and keeps ids short and clean', () => {
    const { memberId, plotId, ...rest } = check;
    void memberId; void plotId;
    expect(buildReferral(rest as Check)).toContain('M:- P:- ');
    const long = buildReferral({ ...check, memberId: 'Wanjiru Kamau 123456789', plotId: 'ñ€ü' });
    expect(long).toContain('M:WANJIRUKAMAU P:- ');
    expect(isGsm7(long)).toBe(true);
  });

  it('stays within 160 GSM-7 characters with a very long answer id', () => {
    const s = buildReferral({ ...check, answerId: 'a_'.repeat(80), memberId: 'M'.repeat(30), plotId: 'P'.repeat(30) });
    expect(s.length).toBeLessThanOrEqual(160);
    expect(isGsm7(s)).toBe(true);
  });

  it('Q ignores unsure and not_leaf leaves; all unsure gives 0', () => {
    expect(buildReferral({ ...check, leaves: [leaf('rust', 0.7), leaf('not_leaf', 0.99), leaf('unsure', 0.2)] })).toContain('Q:70 ');
    expect(buildReferral({ ...check, leaves: [leaf('unsure', 0.2)] })).toContain('Q:0 ');
    expect(buildReferral({ ...check, decision: undefined })).toMatch(/ X:-$/);
  });
});

describe('parseReferral', () => {
  it('round-trips build -> parse', () => {
    const p = parseReferral(buildReferral(check));
    expect(p).toEqual({
      member_id: 'OCC0412',
      plot_id: 'P07',
      check_date: '2026-10-04',
      counts: counts({ healthy: 2, rust: 6, miner: 1 }),
      uncertain: 1,
      answer_id: 'rust_high_pre_rains',
      confidence: 0.88,
      decision: 'ask',
      format: 'JANI1',
    });
  });

  it('reads the contract example with keys in any order and any case', () => {
    const p = parseReferral('jani1 x:ACT q:87 a:rust_high_pre_rains u:1 l:1 h:0 c:0 r:6 n:10 d:20261004 p:2 m:OCC0412');
    expect(p?.member_id).toBe('OCC0412');
    expect(p?.plot_id).toBe('2');
    expect(p?.decision).toBe('act');
    expect(p?.counts.healthy).toBe(2);
    expect(p?.confidence).toBe(0.87);
  });

  it('treats "-" as missing', () => {
    const p = parseReferral('JANI1 M:- P:- D:20261004 N:3 R:1 C:0 H:0 L:0 U:2 A:- Q:- X:-');
    expect(p).toMatchObject({ member_id: '', plot_id: '', answer_id: null, confidence: null, decision: null });
    expect(p?.counts.healthy).toBe(0);
  });

  it('parses the Lovable short form', () => {
    expect(parseReferral('JANI OCC0412 P07 2026-10-04 rust 6/10 unsure 1 ASK')).toEqual({
      member_id: 'OCC0412',
      plot_id: 'P07',
      check_date: '2026-10-04',
      counts: counts({ rust: 6, healthy: 3 }),
      uncertain: 1,
      answer_id: null,
      confidence: null,
      decision: 'ask',
      format: 'JANI',
    });
    const a = parseReferral('JANI - - 2026-10-04 affected 4/10 unsure 0 WAIT');
    expect(a).toMatchObject({ member_id: '', plot_id: '', decision: 'wait' });
    expect(a?.counts).toEqual(counts({ healthy: 6 }));
  });

  it('rejects garbage, bad dates and counts above N', () => {
    for (const bad of [
      '',
      'hello there',
      'JANI1',
      'JANI1 M:A P:B',
      'JANI1 D:20261304 N:10',
      'JANI1 D:20260230 N:10',
      'JANI1 D:2026104 N:10',
      'JANI1 D:20261004 N:51',
      'JANI1 D:20261004 N:10 R:6 C:3 U:2',
      'JANI1 D:20261004 N:10 R:-1',
      'JANI1 D:20261004 N:10 R:2.5',
      'JANI1 D:20261004 N:10 Q:101',
      'JANI OCC0412 P07 2026-02-30 rust 6/10 unsure 1 ASK',
      'JANI OCC0412 P07 2026-10-04 rust 9/10 unsure 2 ASK',
      'JANI OCC0412 P07 2026-10-04 banana 6/10 unsure 1 ASK',
      'JANI OCC0412 P07 2026-10-04 rust 6/10 unsure 1 MAYBE',
    ]) {
      expect(parseReferral(bad), bad).toBeNull();
    }
    expect(parseReferral(null as unknown as string)).toBeNull();
    expect(parseReferral(42 as unknown as string)).toBeNull();
  });
});

describe('toGsm7', () => {
  it('replaces characters outside the basic set', () => {
    expect(toGsm7('Kahawa ñ é €[]{} \u{1F33F}')).toBe('Kahawa ñ é ????? ?');
  });
});

describe('smsLink', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('cleans the number and encodes the body with ?body=', () => {
    vi.stubGlobal('navigator', { userAgent: 'Mozilla/5.0 (Linux; Android 10)' });
    expect(smsLink('+254 712-345 678', 'JANI1 M:A X:ask&q=1')).toBe('sms:+254712345678?body=JANI1%20M%3AA%20X%3Aask%26q%3D1');
  });

  it('uses &body= on iOS', () => {
    vi.stubGlobal('navigator', { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)' });
    expect(smsLink('0712 345678', 'hi')).toBe('sms:0712345678&body=hi');
  });

  it('works without navigator (SSR)', () => {
    vi.stubGlobal('navigator', undefined);
    expect(smsLink('123', 'a b')).toBe('sms:123?body=a%20b');
  });
});

describe('referral Q and N edge cases (contract suite fixes)', () => {
  it('writes Q:0 and N:0 with no leaves, and parses its own output', () => {
    const empty: Check = { ...check, leaves: [], summary: { ...summary, n: 0, uncertain: 0, affected: 0, distinctProblems: 0, dominant: 'none', counts: counts({}) }, answerId: 'ask_officer' };
    const sms = buildReferral(empty);
    expect(sms).toContain(' N:0 ');
    expect(sms).toContain(' Q:0 ');
    expect(sms).not.toContain('Q:-');
    const p = parseReferral(sms);
    expect(p).not.toBeNull();
    expect(p?.confidence).toBe(0);
    expect(p?.counts).toEqual(counts({}));
  });

  it('all unsure gives Q:0 and round-trips', () => {
    const allUnsure: Check = { ...check, leaves: Array.from({ length: 10 }, () => leaf('unsure', 0.3)), summary: { ...summary, uncertain: 10, affected: 0, distinctProblems: 0, dominant: 'none', counts: counts({}) }, answerId: 'too_many_unsure' };
    const sms = buildReferral(allUnsure);
    expect(sms).toContain(' U:10 A:too_many_unsure Q:0 ');
    expect(parseReferral(sms)).toMatchObject({ uncertain: 10, confidence: 0, answer_id: 'too_many_unsure' });
  });

  it('still reads legacy Q:- (confidence null)', () => {
    const p = parseReferral('JANI1 M:OCC0412 P:P07 D:20261004 N:0 R:0 C:0 H:0 L:0 U:0 A:ask_officer Q:- X:ask');
    expect(p).toMatchObject({ member_id: 'OCC0412', answer_id: 'ask_officer', confidence: null, decision: 'ask' });
    expect(parseReferral('JANI1 D:20261004 N:10 R:6 U:1 Q:- X:wait')?.confidence).toBeNull();
  });
});
