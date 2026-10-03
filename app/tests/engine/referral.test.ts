import { describe, expect, it } from 'vitest';
import { buildReferral, parseReferral, smsLink } from '../../src/engine/referral.ts';
import type { Check, LeafResult } from '../../src/engine/types.ts';

function leaf(confidence: number, abstained: boolean): LeafResult {
  return {
    label: abstained ? 'unsure' : 'rust',
    probs: { healthy: 0, rust: abstained ? 0 : confidence, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 },
    confidence,
    quality: { ok: !abstained, blur: 100, brightness: 128, ...(abstained ? { reason: 'blurry' as const } : {}) },
    abstained,
    modelVersion: 'mock',
  };
}

function check(): Check {
  return {
    id: 'check-1',
    createdAt: '2026-10-04T08:00:00.000Z',
    lang: 'sw',
    leaves: [leaf(0.87, false), leaf(0, true)],
    summary: {
      n: 10,
      counts: { healthy: 2, rust: 6, cercospora: 0, phoma: 0, miner: 1, not_leaf: 0 },
      uncertain: 1,
      dominant: 'rust',
      affected: 7,
      distinctProblems: 2,
    },
    window: 'pre_short_rains',
    answerId: 'rust_high_pre_rains',
    decision: 'ask',
    memberId: 'OCC0412',
    plotId: '2',
    consentMain: true,
    consentPhotos: false,
    synced: false,
  };
}

describe('referral', () => {
  it('round-trips a GSM-7 string of at most 160 characters', () => {
    const text = buildReferral(check());
    expect(text.length).toBeLessThanOrEqual(160);
    expect(text).toBe('JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask');
    expect(parseReferral(text)).toEqual({
      memberId: 'OCC0412',
      plotId: '2',
      date: '20261004',
      n: 10,
      rust: 6,
      cercospora: 0,
      phoma: 0,
      miner: 1,
      unsure: 1,
      answerId: 'rust_high_pre_rains',
      confidence: 87,
      decision: 'ask',
    });
  });

  it('uses NA and none when member, plot, or decision are missing', () => {
    const source = check();
    delete source.memberId;
    delete source.plotId;
    delete source.decision;
    const text = buildReferral(source);
    expect(text.startsWith('JANI1 M:NA P:NA ')).toBe(true);
    expect(text.endsWith(' X:none')).toBe(true);
    expect(parseReferral(text)?.decision).toBe('none');
  });

  it('returns null when the text is not a JANI1 referral', () => {
    expect(parseReferral('hello officer')).toBeNull();
    expect(parseReferral('JANI1 M:only')).toBeNull();
  });

  it('builds an sms link with digits and an encoded body', () => {
    expect(smsLink('+254 712 345 678', 'JANI1 M:NA')).toBe('sms:+254712345678?body=JANI1%20M%3ANA');
  });

  it('throws when the referral would pass 160 characters', () => {
    const source = check();
    source.memberId = 'M'.repeat(180);
    expect(() => buildReferral(source)).toThrow(/160/);
  });
});
